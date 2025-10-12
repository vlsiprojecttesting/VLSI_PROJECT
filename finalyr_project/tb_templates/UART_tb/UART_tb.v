`timescale 1ns / 1ps

module tb_uart;

    // Signals
    reg txclk;
    reg rxclk;
    reg ld_tx_data;
    reg [7:0] tx_data;
    reg rx_in;
    wire tx_out;
    wire tx_empty;
    wire [7:0] rx_data;
    wire rx_empty;

    // Instantiate UART
    uart uut (
        .reset(1'b0),        // Not used in this wrapper
        .txclk(txclk),
        .ld_tx_data(ld_tx_data),
        .tx_data(tx_data),
        .rxclk(rxclk),
        .rx_in(rx_in),
        .tx_out(tx_out),
        .tx_empty(tx_empty),
        .rx_data(rx_data),
        .rx_empty(rx_empty)
    );
   always @(*) begin
    rx_in = tx_out;
    end

    // Clock generation
    always #5 txclk = ~txclk; // 100 MHz
    always #5 rxclk = ~rxclk; // 71.4 MHz

    // Initialize
    initial begin
        txclk = 0;
        rxclk = 0;
        ld_tx_data = 0;
        tx_data = 8'h00;
        rx_in = 1; // idle high for UART RX

        #10;

        // -------------------------
        // Test Case 1: Send 'A'
        // -------------------------
        tx_data = 8'h41;
        ld_tx_data = 1;
        #10 ld_tx_data = 0;

        wait(tx_empty); // wait until TX is done
        #50; // small delay for RX
        $display("Test Case 1: Sent 'A', Received: %h", rx_data);

        // -------------------------
        // Test Case 2: Send 'Hello'
        // -------------------------
        send_byte(8'h48); // 'H'
        send_byte(8'h65); // 'e'
        send_byte(8'h6C); // 'l'
        send_byte(8'h6C); // 'l'
        send_byte(8'h6F); // 'o'

        #200;
        $display("Test Case 2 Finished. Last received: %h", rx_data);

        $display("UART Testbench finished");
        $finish;
    end

    // Task to send a single byte
    task send_byte(input [7:0] data);
        begin
            tx_data = data;
            ld_tx_data = 1;
            #10 ld_tx_data = 0;
            wait(tx_empty);
            #20; // small delay to allow RX to catch up
        end
    endtask

endmodule
