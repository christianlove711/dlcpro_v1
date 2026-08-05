`timescale 1ns / 1ps

// Release the external Ethernet PHY independently of the PHY-generated RXC.
// This prevents a reset deadlock where the PHY cannot generate RXC until its
// reset is released, while the FPGA waits for an RXC-based MMCM to lock.
module phy_reset_sequencer #(
    parameter integer HOLD_CYCLES = 1_000_000
) (
    input  wire clk,
    input  wire resetn,
    input  wire ready,
    output reg  phy_reset_n
);
    localparam integer COUNTER_WIDTH =
        (HOLD_CYCLES <= 1) ? 1 : $clog2(HOLD_CYCLES);

    reg [COUNTER_WIDTH-1:0] hold_count;

    always @(posedge clk or negedge resetn) begin
        if (!resetn) begin
            hold_count  <= {COUNTER_WIDTH{1'b0}};
            phy_reset_n <= 1'b0;
        end else if (!ready) begin
            hold_count  <= {COUNTER_WIDTH{1'b0}};
            phy_reset_n <= 1'b0;
        end else if (!phy_reset_n) begin
            if (HOLD_CYCLES <= 1 || hold_count == HOLD_CYCLES - 1) begin
                phy_reset_n <= 1'b1;
            end else begin
                hold_count <= hold_count + {{(COUNTER_WIDTH-1){1'b0}}, 1'b1};
            end
        end
    end
endmodule
