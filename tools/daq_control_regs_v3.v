`timescale 1ns / 1ps

module daq_control_regs_v3 #(
    parameter integer C_S_AXI_DATA_WIDTH = 32,
    parameter integer C_S_AXI_ADDR_WIDTH = 8,
    parameter integer BLOCK_BYTES = 262144
)(
    input wire sample_clk,
    input wire [31:0] sample_pair,
    input wire [1:0] otr_pair,
    // Compatibility-only BD pin. It is tied low and has no trigger logic or
    // package-pin assignment in the AD9269-only release.
    input wire hardtrigger,
    input wire fifo_full,
    input wire [13:0] fifo_level,
    input wire block_complete,
    input wire spi_busy,
    input wire spi_done,
    input wire spi_error,
    output wire capture_enable,
    output wire fifo_reset,
    output wire trigger_event,
    output wire channel_swap,
    output wire spi_reinit_toggle,
    output wire [2:0] adc_test_mode,
    output wire [2:0] adc_rate_sel,
    output wire adc_divide_by_two,
    output wire ps_adc_select,
    output wire ps_jumbo_enable,
    output wire ps_monitor_requested,
    output wire ps_config_toggle,
    output wire ps_start_toggle,
    output wire ps_stop_toggle,
    output wire ps_clear_toggle,
    output wire ps_event_enable,
    output wire ps_acq_mode,
    output wire ps_scope_armed,
    output wire ps_scope_abort_toggle,
    output wire ps_scope_clear_toggle,
    output wire [3:0] ps_scope_decimation,
    output wire [1:0] ps_scope_trigger_mode,
    output wire ps_scope_trigger_channel,
    output wire signed [15:0] ps_scope_trigger_level,
    output wire ps_scope_fps_20,
    input wire [2:0] manager_state,
    input wire manager_adc_select,
    input wire [2:0] manager_rate_sel,
    input wire [2:0] manager_test_mode,
    input wire manager_channel_swap,
    input wire manager_jumbo_enable,
    input wire manager_monitor_enable,
    input wire [31:0] manager_stream_id,
    input wire [7:0] manager_last_error,
    input wire [31:0] manager_measured_rate_hz,
    input wire [31:0] manager_event_count,
    input wire [31:0] manager_dropped_event_count,
    input wire [31:0] manager_suppressed_event_count,
    input wire scope_busy,
    input wire scope_triggered,
    input wire scope_overflow,
    input wire [31:0] scope_frame_count,
    input wire [31:0] scope_suppressed_count,
    input wire [31:0] scope_dropped_count,
    input wire [7:0] spi_chip_id,
    input wire [7:0] spi_chip_grade,
    input wire [7:0] spi_readback_14,
    input wire [7:0] spi_readback_17,
    input wire [7:0] spi_readback_0d,
    input wire [31:0] spi_error_detail,

    (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME S_AXI, PROTOCOL AXI4LITE, DATA_WIDTH 32, ADDR_WIDTH 8" *)
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWADDR" *)
    input wire [C_S_AXI_ADDR_WIDTH-1:0] s_axi_awaddr,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWPROT" *)
    input wire [2:0] s_axi_awprot,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWVALID" *)
    input wire s_axi_awvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWREADY" *)
    output wire s_axi_awready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WDATA" *)
    input wire [C_S_AXI_DATA_WIDTH-1:0] s_axi_wdata,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WSTRB" *)
    input wire [(C_S_AXI_DATA_WIDTH/8)-1:0] s_axi_wstrb,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WVALID" *)
    input wire s_axi_wvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WREADY" *)
    output wire s_axi_wready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI BRESP" *)
    output wire [1:0] s_axi_bresp,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI BVALID" *)
    output wire s_axi_bvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI BREADY" *)
    input wire s_axi_bready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARADDR" *)
    input wire [C_S_AXI_ADDR_WIDTH-1:0] s_axi_araddr,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARPROT" *)
    input wire [2:0] s_axi_arprot,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARVALID" *)
    input wire s_axi_arvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARREADY" *)
    output wire s_axi_arready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RDATA" *)
    output wire [C_S_AXI_DATA_WIDTH-1:0] s_axi_rdata,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RRESP" *)
    output wire [1:0] s_axi_rresp,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RVALID" *)
    output wire s_axi_rvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RREADY" *)
    input wire s_axi_rready,
    (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME S_AXI_CLK, ASSOCIATED_BUSIF S_AXI, ASSOCIATED_RESET s_axi_aresetn" *)
    (* X_INTERFACE_INFO = "xilinx.com:signal:clock:1.0 S_AXI_CLK CLK" *)
    input wire s_axi_aclk,
    (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME S_AXI_RST, POLARITY ACTIVE_LOW" *)
    (* X_INTERFACE_INFO = "xilinx.com:signal:reset:1.0 S_AXI_RST RST" *)
    input wire s_axi_aresetn
);
  localparam [7:0] REG_ID             = 8'h00;
  localparam [7:0] REG_VERSION        = 8'h04;
  localparam [7:0] REG_CONTROL        = 8'h08;
  localparam [7:0] REG_STATUS         = 8'h0C;
  localparam [7:0] REG_BLOCK_BYTES    = 8'h10;
  localparam [7:0] REG_FIFO_LEVEL     = 8'h14;
  localparam [7:0] REG_OVERFLOW_COUNT = 8'h18;
  localparam [7:0] REG_SAMPLE_LO      = 8'h1C;
  localparam [7:0] REG_SAMPLE_HI      = 8'h20;
  localparam [7:0] REG_TRIGGER_CFG    = 8'h24;
  localparam [7:0] REG_TRIGGER_LO     = 8'h28;
  localparam [7:0] REG_TRIGGER_HI     = 8'h2C;
  localparam [7:0] REG_TRIGGER_COUNT  = 8'h30;
  localparam [7:0] REG_BLOCK_COUNT    = 8'h34;
  localparam [7:0] REG_ADC_CONFIG     = 8'h38;
  localparam [7:0] REG_ADC_STATUS     = 8'h3C;
  localparam [7:0] REG_OTR_A_COUNT    = 8'h40;
  localparam [7:0] REG_OTR_B_COUNT    = 8'h44;
  localparam [7:0] REG_DCO_ACTIVITY   = 8'h48;
  localparam [7:0] REG_DATA_FORMAT    = 8'h4C;
  localparam [7:0] REG_DCO_FREQUENCY = 8'h50;
  localparam [7:0] REG_STREAM_ID      = 8'h54;
  localparam [7:0] REG_MEASURED_RATE  = 8'h58;
  localparam [7:0] REG_EVENT_COUNT    = 8'h5C;
  localparam [7:0] REG_DROPPED_EVENTS = 8'h60;
  localparam [7:0] REG_LAST_ERROR     = 8'h64;
  localparam [7:0] REG_EVENT_CONTROL  = 8'h68;
  localparam [7:0] REG_SUPPRESSED_EVENTS = 8'h6C;
  localparam [7:0] REG_ACQ_MODE         = 8'h70;
  localparam [7:0] REG_SCOPE_CONTROL    = 8'h74;
  localparam [7:0] REG_SCOPE_CONFIG     = 8'h78;
  localparam [7:0] REG_SCOPE_STATUS     = 8'h7C;
  localparam [7:0] REG_SCOPE_FRAMES     = 8'h80;
  localparam [7:0] REG_SPI_ID_GRADE     = 8'h84;
  localparam [7:0] REG_SPI_READBACK_0   = 8'h88;
  localparam [7:0] REG_SPI_READBACK_1   = 8'h8C;
  localparam [7:0] REG_SPI_ERROR_DETAIL = 8'h90;
  localparam [7:0] REG_EVENT_DMA_STATUS = 8'h94;
  localparam [7:0] REG_SCOPE_SUPPRESSED = 8'h98;
  localparam [7:0] REG_SCOPE_DROPPED    = 8'h9C;

  localparam integer DCO_GATE_CYCLES = 10000000;

  localparam [31:0] DATA_FORMAT_DUAL_S16_AB = 32'h03100204;

  reg [31:0] control_reg;
  reg [31:0] trigger_cfg_reg;
  reg [31:0] adc_config_reg;
  reg adc_divide_by_two_reg;
  reg reinit_toggle_reg;
  reg clear_stats_toggle;
  reg ps_config_toggle_reg;
  reg ps_start_toggle_reg;
  reg ps_stop_toggle_reg;
  reg ps_clear_toggle_reg;
  reg ps_monitor_requested_reg;
  reg ps_event_enable_reg;
  reg ps_acq_mode_reg;
  reg ps_scope_armed_reg;
  reg ps_scope_abort_toggle_reg;
  reg ps_scope_clear_toggle_reg;
  reg [31:0] scope_config_reg;
  reg [7:0] reset_hold;
  reg fifo_reset_reg;

  // The AXI reset may assert while DCO is stopped. Assert the sample-domain
  // reset asynchronously, then release it only on sample-clock edges.
  (* ASYNC_REG = "TRUE" *) reg [2:0] sample_reset_pipe;
  wire sample_reset = sample_reset_pipe[2];

  reg aw_hold;
  reg [C_S_AXI_ADDR_WIDTH-1:0] awaddr_hold;
  reg w_hold;
  reg [C_S_AXI_DATA_WIDTH-1:0] wdata_hold;
  reg [(C_S_AXI_DATA_WIDTH/8)-1:0] wstrb_hold;
  reg bvalid_reg;
  reg rvalid_reg;
  reg [C_S_AXI_DATA_WIDTH-1:0] rdata_reg;

  (* ASYNC_REG = "TRUE" *) reg capture_sync1;
  (* ASYNC_REG = "TRUE" *) reg capture_sync2;
  (* ASYNC_REG = "TRUE" *) reg [19:0] trigger_cfg_sync1;
  (* ASYNC_REG = "TRUE" *) reg [19:0] trigger_cfg_sync2;
  (* ASYNC_REG = "TRUE" *) reg clear_sync1;
  (* ASYNC_REG = "TRUE" *) reg clear_sync2;
  reg clear_sync_d;
  reg trigger_latched;
  reg trigger_event_sample;
  reg trigger_event_toggle;
  reg [63:0] sample_pair_count;
  reg [31:0] overflow_count;
  reg [63:0] last_trigger_pair;
  reg [31:0] trigger_count;
  reg [31:0] otr_a_count;
  reg [31:0] otr_b_count;
  reg otr_a_sticky;
  reg otr_b_sticky;
  reg [31:0] dco_activity_count;

  // Register every Gray code in its source domain. This removes combinational
  // logic before the synchronizers and guarantees only stable Gray vectors
  // enter the AXI clock domain.
  reg [63:0] sample_gray_source;
  reg [31:0] overflow_gray_source;
  reg [31:0] otr_a_gray_source;
  reg [31:0] otr_b_gray_source;
  reg [31:0] dco_gray_source;
  reg [63:0] trigger_pair_gray_source;
  reg [31:0] trigger_count_gray_source;
  (* ASYNC_REG = "TRUE" *) reg [63:0] sample_gray_sync1;
  (* ASYNC_REG = "TRUE" *) reg [63:0] sample_gray_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] overflow_gray_sync1;
  (* ASYNC_REG = "TRUE" *) reg [31:0] overflow_gray_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] otr_a_gray_sync1;
  (* ASYNC_REG = "TRUE" *) reg [31:0] otr_a_gray_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] otr_b_gray_sync1;
  (* ASYNC_REG = "TRUE" *) reg [31:0] otr_b_gray_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] dco_gray_sync1;
  (* ASYNC_REG = "TRUE" *) reg [31:0] dco_gray_sync2;
  reg [31:0] dco_gray_previous;
  reg [10:0] dco_idle_count;
  reg [23:0] dco_measure_window;
  reg [31:0] dco_count_snapshot;
  reg [31:0] dco_frequency_hz;
  (* ASYNC_REG = "TRUE" *) reg [63:0] trigger_pair_gray_sync1;
  (* ASYNC_REG = "TRUE" *) reg [63:0] trigger_pair_gray_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] trigger_count_gray_sync1;
  (* ASYNC_REG = "TRUE" *) reg [31:0] trigger_count_gray_sync2;
  (* ASYNC_REG = "TRUE" *) reg capture_status_sync1;
  (* ASYNC_REG = "TRUE" *) reg capture_status_sync2;
  (* ASYNC_REG = "TRUE" *) reg fifo_full_sync1;
  (* ASYNC_REG = "TRUE" *) reg fifo_full_sync2;
  (* ASYNC_REG = "TRUE" *) reg otr_a_sticky_sync1;
  (* ASYNC_REG = "TRUE" *) reg otr_a_sticky_sync2;
  (* ASYNC_REG = "TRUE" *) reg otr_b_sticky_sync1;
  (* ASYNC_REG = "TRUE" *) reg otr_b_sticky_sync2;
  (* ASYNC_REG = "TRUE" *) reg spi_busy_sync1;
  (* ASYNC_REG = "TRUE" *) reg spi_busy_sync2;
  (* ASYNC_REG = "TRUE" *) reg spi_done_sync1;
  (* ASYNC_REG = "TRUE" *) reg spi_done_sync2;
  (* ASYNC_REG = "TRUE" *) reg spi_error_sync1;
  (* ASYNC_REG = "TRUE" *) reg spi_error_sync2;
  (* ASYNC_REG = "TRUE" *) reg trigger_event_sync1;
  (* ASYNC_REG = "TRUE" *) reg trigger_event_sync2;
  reg trigger_event_sync_d;
  reg trigger_event_axi;
  reg [31:0] block_count;
  (* ASYNC_REG = "TRUE" *) reg [2:0] manager_state_sync1, manager_state_sync2;
  (* ASYNC_REG = "TRUE" *) reg manager_adc_sync1, manager_adc_sync2;
  (* ASYNC_REG = "TRUE" *) reg [2:0] manager_rate_sync1, manager_rate_sync2;
  (* ASYNC_REG = "TRUE" *) reg [2:0] manager_test_sync1, manager_test_sync2;
  (* ASYNC_REG = "TRUE" *) reg manager_swap_sync1, manager_swap_sync2;
  (* ASYNC_REG = "TRUE" *) reg manager_jumbo_sync1, manager_jumbo_sync2;
  (* ASYNC_REG = "TRUE" *) reg manager_monitor_sync1, manager_monitor_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] manager_stream_sync1, manager_stream_sync2;
  (* ASYNC_REG = "TRUE" *) reg [7:0] manager_error_sync1, manager_error_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] manager_rate_hz_sync1, manager_rate_hz_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] manager_events_sync1, manager_events_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] manager_drops_sync1, manager_drops_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] manager_suppressed_sync1, manager_suppressed_sync2;
  (* ASYNC_REG = "TRUE" *) reg scope_busy_sync1, scope_busy_sync2;
  (* ASYNC_REG = "TRUE" *) reg scope_triggered_sync1, scope_triggered_sync2;
  (* ASYNC_REG = "TRUE" *) reg scope_overflow_sync1, scope_overflow_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] scope_frames_sync1, scope_frames_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] scope_suppressed_sync1, scope_suppressed_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] scope_dropped_sync1, scope_dropped_sync2;
  (* ASYNC_REG = "TRUE" *) reg [7:0] spi_id_sync1, spi_id_sync2;
  (* ASYNC_REG = "TRUE" *) reg [7:0] spi_grade_sync1, spi_grade_sync2;
  (* ASYNC_REG = "TRUE" *) reg [7:0] spi_rb14_sync1, spi_rb14_sync2;
  (* ASYNC_REG = "TRUE" *) reg [7:0] spi_rb17_sync1, spi_rb17_sync2;
  (* ASYNC_REG = "TRUE" *) reg [7:0] spi_rb0d_sync1, spi_rb0d_sync2;
  (* ASYNC_REG = "TRUE" *) reg [31:0] spi_detail_sync1, spi_detail_sync2;

  integer byte_index;
  reg [31:0] merged_data;

  function [63:0] gray_to_bin64;
    input [63:0] gray;
    reg [63:0] p1, p2, p4, p8, p16;
    begin
      // Parallel-prefix Gray decode.  The former serial XOR chain placed up
      // to 15 LUT levels between the synchronizer and AXI read data.
      p1  = gray ^ (gray >> 1);
      p2  = p1   ^ (p1   >> 2);
      p4  = p2   ^ (p2   >> 4);
      p8  = p4   ^ (p4   >> 8);
      p16 = p8   ^ (p8   >> 16);
      gray_to_bin64 = p16 ^ (p16 >> 32);
    end
  endfunction

  function [31:0] gray_to_bin32;
    input [31:0] gray;
    reg [31:0] p1, p2, p4, p8;
    begin
      p1 = gray ^ (gray >> 1);
      p2 = p1   ^ (p1   >> 2);
      p4 = p2   ^ (p2   >> 4);
      p8 = p4   ^ (p4   >> 8);
      gray_to_bin32 = p8 ^ (p8 >> 16);
    end
  endfunction

  wire [63:0] sample_count_axi = gray_to_bin64(sample_gray_sync2);
  wire [31:0] overflow_count_axi = gray_to_bin32(overflow_gray_sync2);
  wire [31:0] otr_a_count_axi = gray_to_bin32(otr_a_gray_sync2);
  wire [31:0] otr_b_count_axi = gray_to_bin32(otr_b_gray_sync2);
  wire [31:0] dco_count_axi = gray_to_bin32(dco_gray_sync2);
  wire [63:0] trigger_pair_axi = gray_to_bin64(trigger_pair_gray_sync2);
  wire [31:0] trigger_count_axi = gray_to_bin32(trigger_count_gray_sync2);
  wire clear_stats_sample = clear_sync2 ^ clear_sync_d;
  wire [2:0] trigger_mode = trigger_cfg_sync2[2:0];
  wire trigger_channel_b = trigger_cfg_sync2[3];
  wire signed [15:0] trigger_threshold = trigger_cfg_sync2[19:4];
  wire signed [15:0] selected_sample = trigger_channel_b ?
      $signed(sample_pair[31:16]) : $signed(sample_pair[15:0]);
  wire trigger_match =
      (trigger_mode == 3'd1 && selected_sample > trigger_threshold) ||
      (trigger_mode == 3'd2 && selected_sample < trigger_threshold) ||
      (trigger_mode == 3'd3);
  wire dco_alive = (dco_idle_count != 11'h7FF);

  assign capture_enable = capture_sync2;
  assign fifo_reset = fifo_reset_reg;
  assign trigger_event = trigger_event_sample;
  assign channel_swap = adc_config_reg[0];
  assign spi_reinit_toggle = reinit_toggle_reg;
  assign adc_test_mode = adc_config_reg[6:4];
  assign adc_rate_sel = adc_config_reg[10:8];
  assign adc_divide_by_two = adc_divide_by_two_reg;
  assign ps_adc_select = adc_config_reg[16];
  assign ps_jumbo_enable = adc_config_reg[17];
  assign ps_monitor_requested = ps_monitor_requested_reg;
  assign ps_config_toggle = ps_config_toggle_reg;
  assign ps_start_toggle = ps_start_toggle_reg;
  assign ps_stop_toggle = ps_stop_toggle_reg;
  assign ps_clear_toggle = ps_clear_toggle_reg;
  assign ps_event_enable = ps_event_enable_reg;
  assign ps_acq_mode = ps_acq_mode_reg;
  assign ps_scope_armed = ps_scope_armed_reg;
  assign ps_scope_abort_toggle = ps_scope_abort_toggle_reg;
  assign ps_scope_clear_toggle = ps_scope_clear_toggle_reg;
  assign ps_scope_decimation = scope_config_reg[3:0];
  assign ps_scope_trigger_mode = scope_config_reg[5:4];
  assign ps_scope_trigger_channel = scope_config_reg[6];
  assign ps_scope_fps_20 = scope_config_reg[7];
  assign ps_scope_trigger_level = scope_config_reg[31:16];

  assign s_axi_awready = !aw_hold;
  assign s_axi_wready = !w_hold;
  assign s_axi_bresp = 2'b00;
  assign s_axi_bvalid = bvalid_reg;
  assign s_axi_arready = !rvalid_reg;
  assign s_axi_rdata = rdata_reg;
  assign s_axi_rresp = 2'b00;
  assign s_axi_rvalid = rvalid_reg;

  always @(posedge sample_clk or negedge s_axi_aresetn) begin
    if (!s_axi_aresetn)
      sample_reset_pipe <= 3'b111;
    else
      sample_reset_pipe <= {sample_reset_pipe[1:0], 1'b0};
  end

  always @(posedge sample_clk) begin
    if (sample_reset) begin
      capture_sync1 <= 1'b0;
      capture_sync2 <= 1'b0;
      trigger_cfg_sync1 <= 20'd0;
      trigger_cfg_sync2 <= 20'd0;
      clear_sync1 <= 1'b0;
      clear_sync2 <= 1'b0;
      clear_sync_d <= 1'b0;
      trigger_latched <= 1'b0;
      trigger_event_sample <= 1'b0;
      trigger_event_toggle <= 1'b0;
      sample_pair_count <= 64'd0;
      overflow_count <= 32'd0;
      last_trigger_pair <= 64'd0;
      trigger_count <= 32'd0;
      otr_a_count <= 32'd0;
      otr_b_count <= 32'd0;
      otr_a_sticky <= 1'b0;
      otr_b_sticky <= 1'b0;
      dco_activity_count <= 32'd0;
      sample_gray_source <= 64'd0;
      overflow_gray_source <= 32'd0;
      otr_a_gray_source <= 32'd0;
      otr_b_gray_source <= 32'd0;
      dco_gray_source <= 32'd0;
      trigger_pair_gray_source <= 64'd0;
      trigger_count_gray_source <= 32'd0;
    end else begin
      trigger_event_sample <= 1'b0;
      capture_sync1 <= control_reg[0];
      capture_sync2 <= capture_sync1;
      trigger_cfg_sync1 <= {trigger_cfg_reg[31:16], trigger_cfg_reg[3:0]};
      trigger_cfg_sync2 <= trigger_cfg_sync1;
      clear_sync1 <= clear_stats_toggle;
      clear_sync2 <= clear_sync1;
      clear_sync_d <= clear_sync2;
      dco_activity_count <= dco_activity_count + 1'b1;

      sample_gray_source <= sample_pair_count ^ (sample_pair_count >> 1);
      overflow_gray_source <= overflow_count ^ (overflow_count >> 1);
      otr_a_gray_source <= otr_a_count ^ (otr_a_count >> 1);
      otr_b_gray_source <= otr_b_count ^ (otr_b_count >> 1);
      dco_gray_source <= dco_activity_count ^ (dco_activity_count >> 1);
      trigger_pair_gray_source <= last_trigger_pair ^ (last_trigger_pair >> 1);
      trigger_count_gray_source <= trigger_count ^ (trigger_count >> 1);

      if (clear_stats_sample) begin
        sample_pair_count <= 64'd0;
        overflow_count <= 32'd0;
        last_trigger_pair <= 64'd0;
        trigger_count <= 32'd0;
        otr_a_count <= 32'd0;
        otr_b_count <= 32'd0;
        otr_a_sticky <= 1'b0;
        otr_b_sticky <= 1'b0;
        trigger_latched <= 1'b0;
      end else if (!capture_sync2) begin
        trigger_latched <= 1'b0;
      end else begin
        sample_pair_count <= sample_pair_count + 1'b1;
        if (fifo_full)
          overflow_count <= overflow_count + 1'b1;
        if (otr_pair[0]) begin
          otr_a_count <= otr_a_count + 1'b1;
          otr_a_sticky <= 1'b1;
        end
        if (otr_pair[1]) begin
          otr_b_count <= otr_b_count + 1'b1;
          otr_b_sticky <= 1'b1;
        end
        if (!trigger_latched && trigger_match) begin
          trigger_latched <= 1'b1;
          trigger_event_sample <= 1'b1;
          trigger_event_toggle <= ~trigger_event_toggle;
          last_trigger_pair <= sample_pair_count;
          trigger_count <= trigger_count + 1'b1;
        end
      end
    end
  end

  always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
      control_reg <= 32'd0;
      trigger_cfg_reg <= 32'd0;
      // Rate selector 1 is the normal 5 MSPS power-up setting. Selector 0
      // configures the Clock Wizard to 6 MHz and enables exact /2 forwarding.
      // AD9269-only: model bit 16 is fixed high, selector 1 = 5 MSPS.
      adc_config_reg <= 32'h00010100;
      adc_divide_by_two_reg <= 1'b0;
      reinit_toggle_reg <= 1'b0;
      clear_stats_toggle <= 1'b0;
      ps_config_toggle_reg <= 1'b0;
      ps_start_toggle_reg <= 1'b0;
      ps_stop_toggle_reg <= 1'b0;
      ps_clear_toggle_reg <= 1'b0;
      ps_monitor_requested_reg <= 1'b0;
      ps_event_enable_reg <= 1'b0;
      ps_acq_mode_reg <= 1'b0;
      ps_scope_armed_reg <= 1'b0;
      ps_scope_abort_toggle_reg <= 1'b0;
      ps_scope_clear_toggle_reg <= 1'b0;
      scope_config_reg <= 32'd0;
      reset_hold <= 8'hFF;
      fifo_reset_reg <= 1'b1;
      aw_hold <= 1'b0;
      w_hold <= 1'b0;
      bvalid_reg <= 1'b0;
      rvalid_reg <= 1'b0;
      rdata_reg <= 32'd0;
      sample_gray_sync1 <= 64'd0;
      sample_gray_sync2 <= 64'd0;
      overflow_gray_sync1 <= 32'd0;
      overflow_gray_sync2 <= 32'd0;
      otr_a_gray_sync1 <= 32'd0;
      otr_a_gray_sync2 <= 32'd0;
      otr_b_gray_sync1 <= 32'd0;
      otr_b_gray_sync2 <= 32'd0;
      dco_gray_sync1 <= 32'd0;
      dco_gray_sync2 <= 32'd0;
      dco_gray_previous <= 32'd0;
      dco_idle_count <= 11'h7FF;
      dco_measure_window <= 24'd0;
      dco_count_snapshot <= 32'd0;
      dco_frequency_hz <= 32'd0;
      trigger_pair_gray_sync1 <= 64'd0;
      trigger_pair_gray_sync2 <= 64'd0;
      trigger_count_gray_sync1 <= 32'd0;
      trigger_count_gray_sync2 <= 32'd0;
      capture_status_sync1 <= 1'b0;
      capture_status_sync2 <= 1'b0;
      fifo_full_sync1 <= 1'b0;
      fifo_full_sync2 <= 1'b0;
      otr_a_sticky_sync1 <= 1'b0;
      otr_a_sticky_sync2 <= 1'b0;
      otr_b_sticky_sync1 <= 1'b0;
      otr_b_sticky_sync2 <= 1'b0;
      spi_busy_sync1 <= 1'b0;
      spi_busy_sync2 <= 1'b0;
      spi_done_sync1 <= 1'b0;
      spi_done_sync2 <= 1'b0;
      spi_error_sync1 <= 1'b0;
      spi_error_sync2 <= 1'b0;
      trigger_event_sync1 <= 1'b0;
      trigger_event_sync2 <= 1'b0;
      trigger_event_sync_d <= 1'b0;
      trigger_event_axi <= 1'b0;
      block_count <= 32'd0;
      manager_state_sync1 <= 0; manager_state_sync2 <= 0;
      manager_adc_sync1 <= 0; manager_adc_sync2 <= 0;
      manager_rate_sync1 <= 0; manager_rate_sync2 <= 0;
      manager_test_sync1 <= 0; manager_test_sync2 <= 0;
      manager_swap_sync1 <= 0; manager_swap_sync2 <= 0;
      manager_jumbo_sync1 <= 0; manager_jumbo_sync2 <= 0;
      manager_monitor_sync1 <= 0; manager_monitor_sync2 <= 0;
      manager_stream_sync1 <= 0; manager_stream_sync2 <= 0;
      manager_error_sync1 <= 0; manager_error_sync2 <= 0;
      manager_rate_hz_sync1 <= 0; manager_rate_hz_sync2 <= 0;
      manager_events_sync1 <= 0; manager_events_sync2 <= 0;
      manager_drops_sync1 <= 0; manager_drops_sync2 <= 0;
      manager_suppressed_sync1 <= 0; manager_suppressed_sync2 <= 0;
      scope_busy_sync1 <= 0; scope_busy_sync2 <= 0;
      scope_triggered_sync1 <= 0; scope_triggered_sync2 <= 0;
      scope_overflow_sync1 <= 0; scope_overflow_sync2 <= 0;
      scope_frames_sync1 <= 0; scope_frames_sync2 <= 0;
      scope_suppressed_sync1 <= 0; scope_suppressed_sync2 <= 0;
      scope_dropped_sync1 <= 0; scope_dropped_sync2 <= 0;
      spi_id_sync1 <= 0; spi_id_sync2 <= 0;
      spi_grade_sync1 <= 0; spi_grade_sync2 <= 0;
      spi_rb14_sync1 <= 0; spi_rb14_sync2 <= 0;
      spi_rb17_sync1 <= 0; spi_rb17_sync2 <= 0;
      spi_rb0d_sync1 <= 0; spi_rb0d_sync2 <= 0;
      spi_detail_sync1 <= 0; spi_detail_sync2 <= 0;
    end else begin
      // Register the rate decode before it enters the ref_clk synchronizer.
      adc_divide_by_two_reg <= (adc_config_reg[10:8] == 3'd0);
      fifo_reset_reg <= (reset_hold != 0);
      if (reset_hold != 0)
        reset_hold <= reset_hold - 1'b1;

      sample_gray_sync1 <= sample_gray_source;
      sample_gray_sync2 <= sample_gray_sync1;
      overflow_gray_sync1 <= overflow_gray_source;
      overflow_gray_sync2 <= overflow_gray_sync1;
      otr_a_gray_sync1 <= otr_a_gray_source;
      otr_a_gray_sync2 <= otr_a_gray_sync1;
      otr_b_gray_sync1 <= otr_b_gray_source;
      otr_b_gray_sync2 <= otr_b_gray_sync1;
      dco_gray_sync1 <= dco_gray_source;
      dco_gray_sync2 <= dco_gray_sync1;
      dco_gray_previous <= dco_gray_sync2;
      if (dco_gray_sync2 != dco_gray_previous)
        dco_idle_count <= 11'd0;
      else if (dco_idle_count != 11'h7FF)
        dco_idle_count <= dco_idle_count + 1'b1;

      // Count DCO/sample-pair edges for exactly 100 ms using the 100 MHz AXI
      // clock. Multiplying the delta by ten reports the measured frequency in
      // hertz and keeps network throughput out of the rate calculation.
      if (dco_measure_window == DCO_GATE_CYCLES - 1) begin
        dco_measure_window <= 24'd0;
        dco_frequency_hz <= (dco_count_axi - dco_count_snapshot) * 10;
        dco_count_snapshot <= dco_count_axi;
      end else begin
        dco_measure_window <= dco_measure_window + 1'b1;
      end
      trigger_pair_gray_sync1 <= trigger_pair_gray_source;
      trigger_pair_gray_sync2 <= trigger_pair_gray_sync1;
      trigger_count_gray_sync1 <= trigger_count_gray_source;
      trigger_count_gray_sync2 <= trigger_count_gray_sync1;
      capture_status_sync1 <= capture_sync2;
      capture_status_sync2 <= capture_status_sync1;
      fifo_full_sync1 <= fifo_full;
      fifo_full_sync2 <= fifo_full_sync1;
      otr_a_sticky_sync1 <= otr_a_sticky;
      otr_a_sticky_sync2 <= otr_a_sticky_sync1;
      otr_b_sticky_sync1 <= otr_b_sticky;
      otr_b_sticky_sync2 <= otr_b_sticky_sync1;
      spi_busy_sync1 <= spi_busy;
      spi_busy_sync2 <= spi_busy_sync1;
      spi_done_sync1 <= spi_done;
      spi_done_sync2 <= spi_done_sync1;
      spi_error_sync1 <= spi_error;
      spi_error_sync2 <= spi_error_sync1;
      trigger_event_sync1 <= trigger_event_toggle;
      trigger_event_sync2 <= trigger_event_sync1;
      trigger_event_sync_d <= trigger_event_sync2;
      trigger_event_axi <= trigger_event_sync2 ^ trigger_event_sync_d;
      manager_state_sync1 <= manager_state; manager_state_sync2 <= manager_state_sync1;
      manager_adc_sync1 <= manager_adc_select; manager_adc_sync2 <= manager_adc_sync1;
      manager_rate_sync1 <= manager_rate_sel; manager_rate_sync2 <= manager_rate_sync1;
      manager_test_sync1 <= manager_test_mode; manager_test_sync2 <= manager_test_sync1;
      manager_swap_sync1 <= manager_channel_swap; manager_swap_sync2 <= manager_swap_sync1;
      manager_jumbo_sync1 <= manager_jumbo_enable; manager_jumbo_sync2 <= manager_jumbo_sync1;
      manager_monitor_sync1 <= manager_monitor_enable; manager_monitor_sync2 <= manager_monitor_sync1;
      manager_stream_sync1 <= manager_stream_id; manager_stream_sync2 <= manager_stream_sync1;
      manager_error_sync1 <= manager_last_error; manager_error_sync2 <= manager_error_sync1;
      manager_rate_hz_sync1 <= manager_measured_rate_hz; manager_rate_hz_sync2 <= manager_rate_hz_sync1;
      manager_events_sync1 <= manager_event_count; manager_events_sync2 <= manager_events_sync1;
      manager_drops_sync1 <= manager_dropped_event_count; manager_drops_sync2 <= manager_drops_sync1;
      manager_suppressed_sync1 <= manager_suppressed_event_count;
      manager_suppressed_sync2 <= manager_suppressed_sync1;
      scope_busy_sync1 <= scope_busy; scope_busy_sync2 <= scope_busy_sync1;
      scope_triggered_sync1 <= scope_triggered;
      scope_triggered_sync2 <= scope_triggered_sync1;
      scope_overflow_sync1 <= scope_overflow;
      scope_overflow_sync2 <= scope_overflow_sync1;
      scope_frames_sync1 <= scope_frame_count;
      scope_frames_sync2 <= scope_frames_sync1;
      scope_suppressed_sync1 <= scope_suppressed_count;
      scope_suppressed_sync2 <= scope_suppressed_sync1;
      scope_dropped_sync1 <= scope_dropped_count;
      scope_dropped_sync2 <= scope_dropped_sync1;
      spi_id_sync1 <= spi_chip_id; spi_id_sync2 <= spi_id_sync1;
      spi_grade_sync1 <= spi_chip_grade; spi_grade_sync2 <= spi_grade_sync1;
      spi_rb14_sync1 <= spi_readback_14; spi_rb14_sync2 <= spi_rb14_sync1;
      spi_rb17_sync1 <= spi_readback_17; spi_rb17_sync2 <= spi_rb17_sync1;
      spi_rb0d_sync1 <= spi_readback_0d; spi_rb0d_sync2 <= spi_rb0d_sync1;
      spi_detail_sync1 <= spi_error_detail;
      spi_detail_sync2 <= spi_detail_sync1;

      if (block_complete)
        block_count <= block_count + 1'b1;

      if (s_axi_awvalid && s_axi_awready) begin
        aw_hold <= 1'b1;
        awaddr_hold <= s_axi_awaddr;
      end
      if (s_axi_wvalid && s_axi_wready) begin
        w_hold <= 1'b1;
        wdata_hold <= s_axi_wdata;
        wstrb_hold <= s_axi_wstrb;
      end

      if (aw_hold && w_hold && !bvalid_reg) begin
        if (awaddr_hold[7:0] == REG_CONTROL) begin
          // W1P command bits: START, STOP, CONFIG_COMMIT, CLEAR_STATS,
          // MONITOR_START and MONITOR_STOP.  Commands are exported as
          // toggles so no pulse can be lost at the PS-to-core CDC boundary.
          merged_data = 32'd0;
          for (byte_index = 0; byte_index < 4; byte_index = byte_index + 1)
            if (wstrb_hold[byte_index])
              merged_data[byte_index*8 +: 8] = wdata_hold[byte_index*8 +: 8];
          if (merged_data[0]) ps_start_toggle_reg <= ~ps_start_toggle_reg;
          if (merged_data[1]) ps_stop_toggle_reg <= ~ps_stop_toggle_reg;
          if (merged_data[2]) ps_config_toggle_reg <= ~ps_config_toggle_reg;
          if (merged_data[3]) begin
            clear_stats_toggle <= ~clear_stats_toggle;
            ps_clear_toggle_reg <= ~ps_clear_toggle_reg;
            block_count <= 32'd0;
          end
          if (merged_data[4]) ps_monitor_requested_reg <= 1'b1;
          if (merged_data[5]) ps_monitor_requested_reg <= 1'b0;
        end else if (awaddr_hold[7:0] == REG_TRIGGER_CFG) begin
          merged_data = trigger_cfg_reg;
          for (byte_index = 0; byte_index < 4; byte_index = byte_index + 1)
            if (wstrb_hold[byte_index])
              merged_data[byte_index*8 +: 8] = wdata_hold[byte_index*8 +: 8];
          trigger_cfg_reg <= merged_data;
        end else if (awaddr_hold[7:0] == REG_ADC_CONFIG) begin
          merged_data = adc_config_reg;
          for (byte_index = 0; byte_index < 4; byte_index = byte_index + 1)
            if (wstrb_hold[byte_index])
              merged_data[byte_index*8 +: 8] = wdata_hold[byte_index*8 +: 8];
          adc_config_reg <= merged_data & 32'h00030771;
          if (merged_data[1])
            reinit_toggle_reg <= ~reinit_toggle_reg;
        end else if (awaddr_hold[7:0] == REG_EVENT_CONTROL) begin
          // Level control: software sets this only after every SG descriptor
          // is submitted and issued. Clearing it prevents new event frames
          // from entering the DMA FIFO before the channel is terminated.
          if (wstrb_hold[0])
            ps_event_enable_reg <= wdata_hold[0];
        end else if (awaddr_hold[7:0] == REG_ACQ_MODE) begin
          // Software must commit this only while the manager is stopped.
          if (wstrb_hold[0] && manager_state_sync2 == 3'd0)
            ps_acq_mode_reg <= wdata_hold[0];
        end else if (awaddr_hold[7:0] == REG_SCOPE_CONTROL) begin
          if (wstrb_hold[0]) begin
            ps_scope_armed_reg <= wdata_hold[0];
            if (wdata_hold[1])
              ps_scope_abort_toggle_reg <= ~ps_scope_abort_toggle_reg;
            if (wdata_hold[2])
              ps_scope_clear_toggle_reg <= ~ps_scope_clear_toggle_reg;
          end
        end else if (awaddr_hold[7:0] == REG_SCOPE_CONFIG) begin
          merged_data = scope_config_reg;
          for (byte_index = 0; byte_index < 4; byte_index = byte_index + 1)
            if (wstrb_hold[byte_index])
              merged_data[byte_index*8 +: 8] =
                  wdata_hold[byte_index*8 +: 8];
          scope_config_reg <= merged_data & 32'hffff00ff;
        end
        aw_hold <= 1'b0;
        w_hold <= 1'b0;
        bvalid_reg <= 1'b1;
      end
      if (bvalid_reg && s_axi_bready)
        bvalid_reg <= 1'b0;

      if (s_axi_arvalid && s_axi_arready) begin
        case (s_axi_araddr[7:0])
          REG_ID:             rdata_reg <= 32'h44415132;
          REG_VERSION:        rdata_reg <= 32'h00040100;
          REG_CONTROL:        rdata_reg <= 32'd0;
          REG_STATUS:         rdata_reg <= {8'd0, manager_error_sync2,
              12'd0, manager_monitor_sync2, manager_state_sync2};
          REG_BLOCK_BYTES:    rdata_reg <= BLOCK_BYTES;
          REG_FIFO_LEVEL:     rdata_reg <= {18'd0, fifo_level};
          REG_OVERFLOW_COUNT: rdata_reg <= overflow_count_axi;
          REG_SAMPLE_LO:      rdata_reg <= sample_count_axi[31:0];
          REG_SAMPLE_HI:      rdata_reg <= sample_count_axi[63:32];
          REG_TRIGGER_CFG:    rdata_reg <= trigger_cfg_reg;
          REG_TRIGGER_LO:     rdata_reg <= trigger_pair_axi[31:0];
          REG_TRIGGER_HI:     rdata_reg <= trigger_pair_axi[63:32];
          REG_TRIGGER_COUNT:  rdata_reg <= trigger_count_axi;
          REG_BLOCK_COUNT:    rdata_reg <= block_count;
          REG_ADC_CONFIG:     rdata_reg <= adc_config_reg & 32'h00030771;
          REG_ADC_STATUS:     rdata_reg <= {8'd0, manager_error_sync2,
              2'd0, manager_jumbo_sync2, manager_swap_sync2,
              manager_test_sync2, manager_rate_sync2, manager_adc_sync2,
              otr_b_sticky_sync2, otr_a_sticky_sync2, dco_alive,
              spi_error_sync2, spi_done_sync2, spi_busy_sync2};
          REG_OTR_A_COUNT:    rdata_reg <= otr_a_count_axi;
          REG_OTR_B_COUNT:    rdata_reg <= otr_b_count_axi;
          REG_DCO_ACTIVITY:   rdata_reg <= dco_count_axi;
          REG_DATA_FORMAT:    rdata_reg <= DATA_FORMAT_DUAL_S16_AB;
          REG_DCO_FREQUENCY:  rdata_reg <= dco_frequency_hz;
          REG_STREAM_ID:      rdata_reg <= manager_stream_sync2;
          REG_MEASURED_RATE:  rdata_reg <= manager_rate_hz_sync2;
          REG_EVENT_COUNT:    rdata_reg <= manager_events_sync2;
          REG_DROPPED_EVENTS: rdata_reg <= manager_drops_sync2;
          REG_LAST_ERROR:     rdata_reg <= {24'd0, manager_error_sync2};
          REG_EVENT_CONTROL:  rdata_reg <= {31'd0, ps_event_enable_reg};
          REG_SUPPRESSED_EVENTS: rdata_reg <= manager_suppressed_sync2;
          REG_ACQ_MODE:         rdata_reg <= {31'd0, ps_acq_mode_reg};
          REG_SCOPE_CONTROL:    rdata_reg <= {31'd0, ps_scope_armed_reg};
          REG_SCOPE_CONFIG:     rdata_reg <= scope_config_reg;
          REG_SCOPE_STATUS:     rdata_reg <= {27'd0, ps_scope_armed_reg,
              ps_scope_armed_reg, scope_overflow_sync2,
              scope_triggered_sync2, scope_busy_sync2};
          REG_SCOPE_FRAMES:     rdata_reg <= scope_frames_sync2;
          REG_SPI_ID_GRADE:     rdata_reg <=
              {16'd0,spi_grade_sync2,spi_id_sync2};
          REG_SPI_READBACK_0:   rdata_reg <=
              {8'd0,spi_rb0d_sync2,spi_rb17_sync2,spi_rb14_sync2};
          REG_SPI_READBACK_1:   rdata_reg <=
              {8'd0,manager_test_sync2,5'd0,8'h27,8'h21};
          REG_SPI_ERROR_DETAIL: rdata_reg <= spi_detail_sync2;
          REG_EVENT_DMA_STATUS: rdata_reg <=
              {29'd0,spi_error_sync2,manager_state_sync2==3'd4,
               ps_event_enable_reg};
          REG_SCOPE_SUPPRESSED: rdata_reg <= scope_suppressed_sync2;
          REG_SCOPE_DROPPED:    rdata_reg <= scope_dropped_sync2;
          default:            rdata_reg <= 32'd0;
        endcase
        rvalid_reg <= 1'b1;
      end else if (rvalid_reg && s_axi_rready) begin
        rvalid_reg <= 1'b0;
      end
    end
  end

  wire unused = &{1'b0, s_axi_awprot, s_axi_arprot};
endmodule
