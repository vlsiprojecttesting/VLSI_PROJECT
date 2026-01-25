/*
 * Auto-generated SoC Top-Level
 * DO NOT EDIT MANUALLY
 */

`ifndef PICORV32_REGS
`ifdef PICORV32_V
`error "picogen.v must be read before picorv32.v!"
`endif

`define PICORV32_REGS picosoc_regs
`endif

`ifndef PICOSOC_MEM
`define PICOSOC_MEM picosoc_mem
`endif

`define PICOSOC_V

module picogen (
	input clk,
	input resetn,

	output        iomem_valid,//cpu requests a transaction
	input         iomem_ready,//peripeheral signal completion
	output [ 3:0] iomem_wstrb,//byte enable signals
	output [31:0] iomem_addr,//address of memory mapped peripheral
	output [31:0] iomem_wdata,//date to write to peripheral
	input  [31:0] iomem_rdata,//data read from peripheral

    input uart_irq,
    input irq_5,
    input irq_6,
    input irq_7,
    input fft_irq,
    
    output flash_csb,
    output flash_clk,
    output flash_io0_oe,
    output flash_io1_oe,
    output flash_io2_oe,
    output flash_io3_oe,
    output flash_io0_do,
    output flash_io1_do,
    output flash_io2_do,
    output flash_io3_do,
    input flash_io0_di,
    input flash_io1_di,
    input flash_io2_di,
    input flash_io3_di,
    output ser_tx,
    input ser_rx,
    output irq,
    );
        // -------------------------------------------------
    // PicoRV32 Core Parameters
    // -------------------------------------------------

    // -------- CPU feature enables --------
    parameter [0:0] BARREL_SHIFTER    = 1;
    parameter [0:0] ENABLE_MUL        = 1;
    parameter [0:0] ENABLE_DIV        = 1;
    parameter [0:0] ENABLE_FAST_MUL   = 0;
    parameter [0:0] ENABLE_COMPRESSED = 1;
    parameter [0:0] ENABLE_COUNTERS   = 1;
    parameter [0:0] ENABLE_IRQ_QREGS  = 0;

    // -------- Memory configuration --------
    parameter integer MEM_WORDS = 256;

    // -------- Address parameters --------
    parameter [31:0] STACKADDR      = (4*MEM_WORDS);  // end of memory
    parameter [31:0] PROGADDR_RESET = 32'h00100000;
    parameter [31:0] PROGADDR_IRQ   = 32'h00000000;

    reg [31:0] irq;
    wire irq_stall = 0;

    always @* begin
        irq = 0;
        irq[3] = irq_stall;
        irq[4] = uart_irq;
        irq[5] = irq_5;
        irq[6] = irq_6;
        irq[7] = irq_7;
        irq[8] = fft_irq;
        end

    wire mem_valid;
	wire mem_instr;
	wire mem_ready;
	wire [31:0] mem_addr;
	wire [31:0] mem_wdata;
	wire [3:0] mem_wstrb;
	wire [31:0] mem_rdata;

    assign iomem_valid = mem_valid && (mem_addr[31:24] > 8'h 01);
	assign iomem_wstrb = mem_wstrb;
	assign iomem_addr = mem_addr;
	assign iomem_wdata = mem_wdata;

    wire spimem_ready;
    wire [31:0] spimem_rdata;
    wire spimemio_cfgreg_sel = mem_valid && (mem_addr == 32'h02000000);
    wire [31:0] spimemio_cfgreg_do;
    spimemio spimemio (
    .clk        (clk),
    .resetn     (resetn),

    .flash_csb  (flash_csb),
    .flash_clk  (flash_clk),

    .flash_io0_oe (flash_io0_oe),
    .flash_io1_oe (flash_io1_oe),
    .flash_io2_oe (flash_io2_oe),
    .flash_io3_oe (flash_io3_oe),

    .flash_io0_do (flash_io0_do),
    .flash_io1_do (flash_io1_do),
    .flash_io2_do (flash_io2_do),
    .flash_io3_do (flash_io3_do),

    .flash_io0_di (flash_io0_di),
    .flash_io1_di (flash_io1_di),
    .flash_io2_di (flash_io2_di),
    .flash_io3_di (flash_io3_di),

    .cfgreg_sel  (spimemio_cfgreg_sel),
    .cfgreg_do   (spimemio_cfgreg_do)
);    
    wire uart0_reg_div_sel = mem_valid && (mem_addr == 32'h02000004);
    wire [31:0] uart0_reg_div_do;
    wire uart0_reg_dat_sel = mem_valid && (mem_addr == 32'h02000008);
    wire [31:0] uart0_reg_dat_do;
    wire uart0_reg_dat_wait;

    simpleuart uart0 (
    .clk(clk),
    .resetn(resetn),

    .ser_tx(ser_tx),
    .ser_rx(ser_rx),

    .reg_div_we(uart0_reg_div_sel ? mem_wstrb : 4'b0),
    .reg_div_di(mem_wdata),
    .reg_div_do(uart0_reg_div_do),

    .reg_dat_we(uart0_reg_dat_sel ? mem_wstrb[0] : 1'b0),
    .reg_dat_re(uart0_reg_dat_sel && !mem_wstrb),
    .reg_dat_di(mem_wdata),
    .reg_dat_do(uart0_reg_dat_do),
    .reg_dat_wait(uart0_reg_dat_wait)
);    
    wire fft_ready;
    wire [31:0] fft_rdata;
    wire fft0_sel = mem_valid && 
                        (mem_addr >= 32'h03000000 &&
                         mem_addr < 32'h03000200);

    fft_accel fft0 (
    .clk     (clk),
    .resetn  (resetn),
    .valid   (fft0_sel),
    .mem_addr(mem_addr),
    .wstrb   (mem_wstrb),
    .wdata   (mem_wdata),
    .rdata   (fft_rdata),
    .ready   (fft_ready),
    
    .irq_out (fft_irq)
    
);

assign mem_ready =
    (iomem_valid && iomem_ready)
    || spimem_ready
    || fft_ready
    || spimemio_cfgreg_sel
    || uart0_reg_div_sel
    || (uart0_reg_dat_sel && !uart0_reg_dat_wait)
    || fft0_fft_sel
    || ram_ready;


assign mem_rdata =
    (iomem_valid && iomem_ready) ? iomem_rdata
    : spimem_ready ? spimem_rdata
    : fft_ready ? fft_rdata
    : ram_ready ? ram_rdata
    : spimemio_cfgreg_sel ? spimemio_cfgreg_do
    : uart0_reg_div_sel ? uart0_reg_div_do
    : uart0_reg_dat_sel ? uart0_reg_dat_do
    : fft0_fft_sel ? fft0_fft_do
    : 32'h0000_0000;

    picorv32 #(
    .STACKADDR        (STACKADDR),
    .PROGADDR_RESET   (PROGADDR_RESET),
    .PROGADDR_IRQ     (PROGADDR_IRQ),

    .BARREL_SHIFTER   (BARREL_SHIFTER),
    .COMPRESSED_ISA   (ENABLE_COMPRESSED),
    .ENABLE_COUNTERS  (ENABLE_COUNTERS),
    .ENABLE_MUL       (ENABLE_MUL),
    .ENABLE_DIV       (ENABLE_DIV),
    .ENABLE_FAST_MUL  (ENABLE_FAST_MUL),
    .ENABLE_IRQ       (1),
    .ENABLE_IRQ_QREGS (ENABLE_IRQ_QREGS)
) cpu (
    .clk        (clk),
    .resetn     (resetn),

    .mem_valid  (mem_valid),
    .mem_instr  (mem_instr),
    .mem_ready  (mem_ready),
    .mem_addr   (mem_addr),
    .mem_wdata  (mem_wdata),
    .mem_wstrb  (mem_wstrb),
    .mem_rdata  (mem_rdata),

    .irq        (irq)
);

    always @(posedge clk)
    ram_ready <= mem_valid && !mem_ready && mem_addr < 4*256;

    `PICOSOC_MEM #(
        .WORDS(256)
    ) memory (
        .clk(clk),
        .wen((mem_valid && !mem_ready && mem_addr < 4*MEM_WORDS) ? mem_wstrb : 4'b0),
        .addr(mem_addr[23:2]),
        .wdata(mem_wdata),
        .rdata(ram_rdata)
    );
endmodule
    module picosoc_regs (
        input clk, wen,
        input [5:0] waddr,
        input [5:0] raddr1,
        input [5:0] raddr2,
        input [31:0] wdata,
        output [31:0] rdata1,
        output [31:0] rdata2
    );
        reg [31:0] regs [0:31];

        always @(posedge clk)
            if (wen) regs[waddr[4:0]] <= wdata;

        assign rdata1 = regs[raddr1[4:0]];
        assign rdata2 = regs[raddr2[4:0]];
    endmodule

    module picosoc_mem #(
        parameter integer WORDS = 256
    ) (
        input clk,
        input [3:0] wen,
        input [21:0] addr,
        input [31:0] wdata,
        output reg [31:0] rdata
    );
        reg [31:0] mem [0:WORDS-1];

        always @(posedge clk) begin
            rdata <= mem[addr];
            if (wen[0]) mem[addr][ 7: 0] <= wdata[ 7: 0];
            if (wen[1]) mem[addr][15: 8] <= wdata[15: 8];
            if (wen[2]) mem[addr][23:16] <= wdata[23:16];
            if (wen[3]) mem[addr][31:24] <= wdata[31:24];
        end
    endmodule
