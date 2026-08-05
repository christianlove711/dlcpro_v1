`timescale 1ns / 1ps

`ifndef PL_RGMII_CLKOUT0_PHASE
`define PL_RGMII_CLKOUT0_PHASE 208.125
`endif

// The board PHY's receive clock is the timing reference for both GMII sides.
// 208.125 degrees is the nearest legal MMCM phase step for this divide-by-8
// output (5.625-degree granularity), while retaining the intended RGMII
// sampling-edge centering.  The macro keeps 208.125 degrees as the production
// default while allowing sweep_rgmii_phase.tcl to build isolated candidates
// without changing the checked-in source between runs.
module pl_rgmii_clock (
    input  wire rgmii_rxc,
    input  wire resetn,
    output wire gmii_clk_125m,
    output wire locked
);
  wire clkfb_raw;
  wire clkfb;
  wire shifted_raw;

  MMCME2_BASE #(
      .BANDWIDTH("OPTIMIZED"),
      .CLKIN1_PERIOD(8.000),
      .DIVCLK_DIVIDE(1),
      .CLKFBOUT_MULT_F(8.000),
      .CLKOUT0_DIVIDE_F(8.000),
      .CLKOUT0_PHASE(`PL_RGMII_CLKOUT0_PHASE),
      .STARTUP_WAIT("FALSE")
  ) rgmii_mmcm (
      .CLKIN1(rgmii_rxc),
      .CLKFBIN(clkfb),
      .RST(!resetn),
      .PWRDWN(1'b0),
      .CLKFBOUT(clkfb_raw),
      .CLKOUT0(shifted_raw),
      .CLKOUT0B(), .CLKOUT1(), .CLKOUT1B(), .CLKOUT2(), .CLKOUT2B(),
      .CLKOUT3(), .CLKOUT3B(), .CLKOUT4(), .CLKOUT5(), .CLKOUT6(),
      .LOCKED(locked)
  );

  BUFG rgmii_feedback_buffer (.I(clkfb_raw), .O(clkfb));
  BUFG rgmii_receive_buffer (.I(shifted_raw), .O(gmii_clk_125m));
endmodule
