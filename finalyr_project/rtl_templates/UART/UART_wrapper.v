`timescale 1ns / 1ps
//CLS_PER_BIT = 87 for 115200 baud with 10MHz clock just default if not specified this is chosen
module uart #(
    parameter CLKS_PER_BIT = 87
)(
    input        reset,
    input        txclk,
    input        ld_tx_data,
    input  [7:0] tx_data,
    input        rxclk,
    input        rx_in,
    output       tx_out,
    output       tx_empty,
    output [7:0] rx_data,
    output       rx_empty
);

    // Transmitter instance
    transmitter #(
        .CLKS_PER_BIT(CLKS_PER_BIT)
    ) uart_tx (
        .i_Clock(txclk),
        .i_Tx_DV(ld_tx_data),
        .i_Tx_Byte(tx_data),
        .o_Tx_Active(),
        .o_Tx_Serial(tx_out),
        .o_Tx_Done(tx_empty)
    );

    // Receiver instance
    receiver #(
        .CLKS_PER_BIT(CLKS_PER_BIT)
    ) uart_rx (
        .i_Clock(rxclk),
        .i_Rx_Serial(rx_in),
        .o_Rx_DV(rx_empty),
        .o_Rx_Byte(rx_data)
    );

endmodule
