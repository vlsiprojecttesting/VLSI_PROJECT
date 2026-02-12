`timescale 1ns/1ps
module fft_accel (
    input  wire        clk,
    input  wire        resetn,
    input  wire        valid,
    input  wire [31:0] mem_addr,
    input  wire [3:0]  wstrb,
    input  wire [31:0] wdata,
    output reg  [31:0] rdata,
    output reg         ready,
    output reg         irq_out
);

    // Address map
    localparam OFFSET_CTRL   = 12'h000;
    localparam OFFSET_STATUS = 12'h004;
    localparam OFFSET_IN     = 12'h008;
    localparam OFFSET_OUT    = 12'h108;

    // FFT size
    localparam N = 64;

    // Buffers
    reg signed [15:0] in_re_buf  [0:N-1];
    reg signed [15:0] in_im_buf  [0:N-1];
    reg signed [15:0] out_re_buf [0:N-1];
    reg signed [15:0] out_im_buf [0:N-1];

    // counters widened to avoid overflow when counting up to N
    reg [6:0] feed_index;   // can represent 0..64 safely
    reg [6:0] out_index;    // can represent 0..64 safely
    reg [9:0] wait_count;   // pipeline wait / timeout counter
    reg [2:0] state;        // 0=IDLE,1=FEED,2=WAIT,3=CAPTURE

    reg start_flag;
    reg done_flag;

    // FFT I/O
    reg [0:0] di_en;
    reg [15:0] di_re;
    reg [15:0] di_im;
    wire do_en;
    wire [15:0] do_re;
    wire [15:0] do_im;

    // FFT Instance (assumes your FFT module uses these ports)
    FFT FFT_inst (
        .clock(clk),
        .reset(~resetn),
        .di_en(di_en),
        .di_re(di_re),
        .di_im(di_im),
        .do_en(do_en),
        .do_re(do_re),
        .do_im(do_im)
    );

    wire [11:0] local_addr = mem_addr[11:0];
    wire in_region  = (local_addr >= OFFSET_IN)  && (local_addr < (OFFSET_IN + 12'h100));
    wire out_region = (local_addr >= OFFSET_OUT) && (local_addr < (OFFSET_OUT + 12'h100));

    integer i;
    always @(posedge clk or negedge resetn) begin
        if (!resetn) begin
            ready      <= 0;
            irq_out    <= 0;
            start_flag <= 0;
            done_flag  <= 0;
            feed_index <= 0;
            out_index  <= 0;
            wait_count <= 0;
            di_en      <= 0;
            di_re      <= 0;
            di_im      <= 0;
            state      <= 0;
            for (i = 0; i < N; i = i + 1) begin
                in_re_buf[i]  <= 0;
                in_im_buf[i]  <= 0;
                out_re_buf[i] <= 0;
                out_im_buf[i] <= 0;
            end
        end else begin
            // default each cycle
            ready <= 0;
            di_en <= 0; // assert only in FEED cycle

            // --- Memory write handling ---
            if (valid && |wstrb) begin
                ready <= 1;
                if (local_addr == OFFSET_CTRL) begin
                    if (wdata[0]) begin
                        start_flag <= 1;
                        done_flag <= 0;
                        irq_out <= 0;
                        feed_index <= 0;
                        out_index <= 0;
                        wait_count <= 0;
                        state <= 1;
                       // $display("[%0t] CONTROL: START Triggered", $time);
                    end
                    if (wdata[1]) begin
                        done_flag <= 0;
                        irq_out <= 0;
                       // $display("[%0t] CONTROL: CLEAR Flags", $time);
                    end
                end else if (in_region) begin
                    integer idx;
                    idx = (local_addr - OFFSET_IN) >> 2;
                    in_re_buf[idx] <= wdata[15:0];
                    in_im_buf[idx] <= wdata[31:16];
                  //  $display("[%0t] WRITE INPUT[%0d] = Re:%0d Im:%0d", $time, idx,
                            //$signed(wdata[15:0]), $signed(wdata[31:16]));
                end
            end

            // --- Memory read handling ---
            if (valid && !(|wstrb)) begin
                ready <= 1;
                if (local_addr == OFFSET_STATUS)
                    rdata <= {30'd0, done_flag, (state != 0)};
                else if (in_region) begin
                    integer idx;
                    idx = (local_addr - OFFSET_IN) >> 2;
                    rdata <= {in_im_buf[idx], in_re_buf[idx]};
                end else if (out_region) begin
                    integer idx;
                    idx = (local_addr - OFFSET_OUT) >> 2;
                    rdata <= {out_im_buf[idx], out_re_buf[idx]};
                end else
                    rdata <= 0;
            end

            // -------------------
            // STATE MACHINE
            // -------------------
            case (state)
                0: begin // IDLE
                    if (start_flag) begin
                        $display("[%0t] STATE -> FEED", $time);
                        state <= 1;
                    end
                end

                1: begin // FEED
                    // feed_index ranges 0..63, stop when it reaches N
                    if (feed_index < N) begin
                        di_en <= 1'b1;
                        di_re <= in_re_buf[feed_index];
                        di_im <= in_im_buf[feed_index];
                   //     $display("[%0t] FEED[%0d] -> Re:%0d Im:%0d", $time, feed_index, $signed(di_re), $signed(di_im));
                        feed_index <= feed_index + 1;
                    end else begin
                        // finished feeding exactly N samples
                        di_en <= 1'b0;
                        state <= 2;
                        wait_count <= 10'd120; // adjust for pipeline latency
                  //      $display("[%0t] FEED COMPLETE — STATE -> WAIT (flush %0d cycles)", $time, wait_count);
                    end
                end

                2: begin // WAIT for pipeline to produce outputs
                    if (wait_count > 0) begin
                        wait_count <= wait_count - 1;
                       
                        // if (wait_count % 20 == 0)
                        // $display("[%0t] WAIT: %0d cycles remaining", $time, wait_count);
                        // end else begin
                        state <= 3;
                        out_index <= 0;
                        wait_count <= 0; // reuse as capture timeout counter
                  //      $display("[%0t] WAIT COMPLETE — STATE -> CAPTURE OUTPUTS", $time);
                   end
                end

                3: begin // CAPTURE outputs
                    // debug line each cycle to see do_en changes
                //    $display("[%0t] CAPTURE: out_index=%0d do_en=%b do_re=%0d do_im=%0d",
                     //        $time, out_index, do_en, $signed(do_re), $signed(do_im));

                    if (do_en) begin
                        // store output
                        out_re_buf[out_index] <= do_re;
                        out_im_buf[out_index] <= do_im;
                        $display("OUT[%0d]: Re=%0d Im=%0d", out_index, $signed(do_re), $signed(do_im));
                        out_index <= out_index + 1;
                        wait_count <= 0; // reset capture timeout when data arrives

                        if (out_index == (N-1)) begin
                            done_flag <= 1;
                            irq_out <= 1;
                            start_flag <= 0;
                            state <= 0;
                     $display("[%0t] FFT DONE — All outputs captured", $time);
                        end
                    end else begin
                        // No do_en this cycle — increment timeout guard
                        if (wait_count < 10'd1023)
                            wait_count <= wait_count + 1;
                        else begin
                    //        $display("[%0t] ERROR: No FFT output (do_en stayed low) — aborting capture", $time);
                            done_flag <= 1;
                            state <= 0;
                        end
                    end
                end

                default: state <= 0;
            endcase
        end
    end
endmodule
