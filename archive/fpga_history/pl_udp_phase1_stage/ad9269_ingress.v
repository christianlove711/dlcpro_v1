`timescale 1ns / 1ps

// AD9269-only clock-domain crossing.  The source-synchronous A/B pair and
// both OTR flags remain in one FIFO word so their sample indices cannot skew.
module ad9269_ingress #(
    parameter FIFO_DEPTH = 16384,
    parameter SIM_ASSERT_CHK = 1
) (
    input  wire        clk_100m,
    input  wire        resetn,
    input  wire        clear_fifo,
    input  wire        capture_enable,
    input  wire        sample_clk,
    input  wire [31:0] sample_pair_in,
    input  wire [1:0]  sample_otr_in,
    input  wire        sample_ready,
    output wire        sample_valid,
    output wire [31:0] sample_pair,
    output wire [1:0]  sample_otr,
    output reg  [63:0] sample_index = 64'd0,
    output wire [14:0] fifo_level,
    output wire        fifo_full,
    output reg  [31:0] overflow_count = 32'd0
);
  localparam integer COUNT_WIDTH = $clog2(FIFO_DEPTH) + 1;
  wire fifo_reset = !resetn || clear_fifo;
  (* ASYNC_REG = "TRUE" *) reg [1:0] capture_sync = 2'b00;
  wire [33:0] fifo_dout;
  wire fifo_empty;
  wire fifo_overflow;
  wire wr_rst_busy;
  wire rd_rst_busy;
  wire [COUNT_WIDTH-1:0] level_narrow;

  always @(posedge sample_clk) begin
    if (!resetn)
      capture_sync <= 2'b00;
    else
      capture_sync <= {capture_sync[0], capture_enable};
  end

  xpm_fifo_async #(
      .CDC_SYNC_STAGES(2),
      .DOUT_RESET_VALUE("0"),
      .ECC_MODE("no_ecc"),
      .FIFO_MEMORY_TYPE("block"),
      .FIFO_READ_LATENCY(0),
      .FIFO_WRITE_DEPTH(FIFO_DEPTH),
      .FULL_RESET_VALUE(0),
      .PROG_EMPTY_THRESH(16),
      .PROG_FULL_THRESH(FIFO_DEPTH - 16),
      .RD_DATA_COUNT_WIDTH(COUNT_WIDTH),
      .READ_DATA_WIDTH(34),
      .READ_MODE("fwft"),
      .RELATED_CLOCKS(0),
      .SIM_ASSERT_CHK(SIM_ASSERT_CHK),
      .USE_ADV_FEATURES("0707"),
      .WAKEUP_TIME(0),
      .WRITE_DATA_WIDTH(34),
      .WR_DATA_COUNT_WIDTH(COUNT_WIDTH)
  ) sample_fifo (
      .rst(fifo_reset),
      .wr_clk(sample_clk),
      .wr_en(capture_sync[1] && !wr_rst_busy),
      .din({sample_otr_in, sample_pair_in}),
      .full(fifo_full),
      .overflow(fifo_overflow),
      .wr_data_count(), .prog_full(), .almost_full(), .wr_ack(),
      .wr_rst_busy(wr_rst_busy),
      .rd_clk(clk_100m),
      .rd_en(sample_valid && sample_ready),
      .dout(fifo_dout),
      .empty(fifo_empty),
      .underflow(),
      .rd_data_count(level_narrow),
      .prog_empty(), .almost_empty(), .data_valid(),
      .rd_rst_busy(rd_rst_busy),
      .sleep(1'b0),
      .injectsbiterr(1'b0), .injectdbiterr(1'b0),
      .sbiterr(), .dbiterr()
  );

  assign sample_valid = capture_enable && !fifo_empty && !rd_rst_busy;
  assign sample_pair = fifo_dout[31:0];
  assign sample_otr = fifo_dout[33:32];
  assign fifo_level = {{(15-COUNT_WIDTH){1'b0}}, level_narrow};

  always @(posedge clk_100m) begin
    if (!resetn || clear_fifo)
      sample_index <= 64'd0;
    else if (sample_valid && sample_ready)
      sample_index <= sample_index + 1'b1;
  end

  always @(posedge sample_clk) begin
    if (!resetn || clear_fifo)
      overflow_count <= 32'd0;
    else if (fifo_overflow && overflow_count != 32'hffff_ffff)
      overflow_count <= overflow_count + 1'b1;
  end
endmodule
