`timescale 1ns / 1ps

// AD9269-only clock generator.
//
// A single 80 MHz global clock tree avoids cascading BUFGMUX/BUFH resources.
// The AD9269 clock pin is always driven by one ODDR:
//   - 80 MSPS uses the native DDR 1/0 pattern.
//   - 40/20/10/5 MSPS use a divider level captured on the rising edge and
//     presented identically on both ODDR halves for a clean full-cycle level.
// rate_sel 1/2/3/4/5 = 5/10/20/40/80 MSPS.
module adc_rate_clock_gen (
    input  wire        clk_100m,
    input  wire        resetn,
    input  wire        clock_enable,
    input  wire [2:0]  rate_sel,
    output wire        sample_clk,
    output wire        ad9269_clk_pin,
    output wire        locked,
    output reg  [31:0] configured_rate_hz
);
  wire clkfb_raw;
  wire clkfb;
  wire clk80_raw;
  wire clk80;
  (* ASYNC_REG = "TRUE" *) reg [1:0] enable_sync = 2'b00;
  (* ASYNC_REG = "TRUE" *) reg [2:0] rate_sel_sync1 = 3'd1;
  (* ASYNC_REG = "TRUE" *) reg [2:0] rate_sel_sync2 = 3'd1;
  reg [3:0] divider_counter = 4'd0;
  reg divider_level = 1'b0;

  MMCME2_BASE #(
      .BANDWIDTH("OPTIMIZED"),
      .CLKIN1_PERIOD(10.000),
      .DIVCLK_DIVIDE(1),
      .CLKFBOUT_MULT_F(6.000),
      .CLKOUT0_DIVIDE_F(7.500),
      .STARTUP_WAIT("FALSE")
  ) rate_mmcm (
      .CLKIN1(clk_100m),
      .CLKFBIN(clkfb),
      .RST(!resetn),
      .PWRDWN(1'b0),
      .CLKFBOUT(clkfb_raw),
      .CLKOUT0(clk80_raw),
      .CLKOUT1(),
      .CLKOUT2(),
      .CLKOUT3(),
      .CLKOUT4(),
      .CLKOUT5(),
      .CLKOUT6(),
      .CLKOUT0B(),
      .CLKOUT1B(),
      .CLKOUT2B(),
      .CLKOUT3B(),
      .LOCKED(locked)
  );

  BUFG feedback_buffer (.I(clkfb_raw), .O(clkfb));
  BUFG output_buffer (.I(clk80_raw), .O(clk80));
  assign sample_clk = clk80;

  always @(posedge clk80 or negedge resetn) begin
    if (!resetn) begin
      enable_sync <= 2'b00;
      rate_sel_sync1 <= 3'd1;
      rate_sel_sync2 <= 3'd1;
      divider_counter <= 4'd0;
      divider_level <= 1'b0;
    end else begin
      enable_sync <= {enable_sync[0], clock_enable && locked};
      rate_sel_sync1 <= rate_sel;
      rate_sel_sync2 <= rate_sel_sync1;
      if (!clock_enable || !locked) begin
        divider_counter <= 4'd0;
        divider_level <= 1'b0;
      end else begin
        // divider_level is captured by the SAME_EDGE ODDR before this
        // nonblocking update, so D1 and D2 remain equal for the whole cycle.
        case (rate_sel_sync2)
          3'd1: divider_level <= divider_counter[3]; // 80 / 16 = 5
          3'd2: divider_level <= divider_counter[2]; // 80 / 8  = 10
          3'd3: divider_level <= divider_counter[1]; // 80 / 4  = 20
          3'd4: divider_level <= divider_counter[0]; // 80 / 2  = 40
          default: divider_level <= 1'b0;
        endcase
        divider_counter <= divider_counter + 1'b1;
      end
    end
  end

  ODDR #(
      .DDR_CLK_EDGE("SAME_EDGE"),
      .INIT(1'b0),
      .SRTYPE("ASYNC")
  ) ad9269_clock_oddr (
      .Q(ad9269_clk_pin),
      .C(clk80),
      .CE(enable_sync[1]),
      .D1(rate_sel_sync2 == 3'd5 ? 1'b1 : divider_level),
      .D2(rate_sel_sync2 == 3'd5 ? 1'b0 : divider_level),
      .R(!enable_sync[1]),
      .S(1'b0)
  );

  always @* begin
    case (rate_sel)
      3'd1: configured_rate_hz = 32'd5000000;
      3'd2: configured_rate_hz = 32'd10000000;
      3'd3: configured_rate_hz = 32'd20000000;
      3'd4: configured_rate_hz = 32'd40000000;
      3'd5: configured_rate_hz = 32'd80000000;
      default: configured_rate_hz = 32'd0;
    endcase
  end
endmodule
