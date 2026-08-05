`timescale 1ns / 1ps

// Copies the selected ADC stream into a monitor-only asynchronous FIFO and
// emits self-describing UDP payloads. A full monitor FIFO drops only the PC
// copy; it never applies backpressure to the feature/DMA path.
module pl_raw_udp_streamer #(
    parameter FIFO_DEPTH = 4096,
    parameter SIM_ASSERT_CHK = 1
) (
    input  wire        core_clk,
    input  wire        gmii_clk,
    input  wire        resetn,
    input  wire        clear_stream,
    input  wire        monitor_enable,
    input  wire        jumbo_enable,
    input  wire        adc_model,       // 0: AD9280, 1: AD9269
    input  wire [31:0] sample_rate_hz,
    input  wire [31:0] stream_id,
    input  wire        sample_valid,
    input  wire [31:0] sample_pair,
    input  wire [7:0]  sample_u8,
    input  wire [1:0]  sample_otr,
    input  wire [63:0] sample_index,

    input  wire        status_toggle,
    input  wire [2:0]  acquisition_state,
    input  wire [7:0]  last_error,
    input  wire [31:0] measured_rate_hz,
    input  wire [14:0] active_fifo_level,
    input  wire [31:0] active_overflow_count,
    input  wire [31:0] event_count,
    input  wire [31:0] dropped_event_count,
    input  wire [31:0] suppressed_event_count,
    input  wire        event_path_enable,
    input  wire [63:0] interval_mean_q16,
    input  wire [31:0] transaction_id,

    output reg         tx_start_en = 1'b0,
    output reg  [31:0] tx_data = 32'd0,
    output reg  [15:0] tx_byte_num = 16'd0,
    output reg  [15:0] tx_src_port = 16'd5001,
    output reg  [15:0] tx_dst_port = 16'd5001,
    input  wire        tx_done,
    input  wire        tx_req,

    output wire [14:0] monitor_fifo_level,
    output wire        monitor_fifo_full,
    output reg  [31:0] monitor_drop_count = 32'd0,
    output reg  [31:0] packet_count = 32'd0
);
  localparam DATA_MAGIC = 32'h44415144;   // DAQD
  localparam STATUS_MAGIC = 32'h44415153; // DAQS
  localparam HEADER_BYTES = 16'd40;
  localparam STD_PAYLOAD_BYTES = 16'd1408;
  localparam JUMBO_PAYLOAD_BYTES = 16'd8192;
  localparam STD_PAYLOAD_WORDS = 15'd352;
  localparam JUMBO_PAYLOAD_WORDS = 15'd2048;
  localparam integer FIFO_COUNT_WIDTH = $clog2(FIFO_DEPTH) + 1;

  reg [5:0] reset_hold = 6'h3f;
  always @(posedge core_clk) begin
    if (!resetn || clear_stream)
      reset_hold <= 6'h3f;
    else if (reset_hold != 0)
      reset_hold <= reset_hold - 1'b1;
  end
  wire fifo_reset = !resetn || (reset_hold != 0);

  reg [95:0] fifo_din = 96'd0;
  reg fifo_wr_en = 1'b0;
  reg [31:0] mono_pack = 32'd0;
  reg [1:0] mono_count = 2'd0;
  reg [31:0] otr_a_count = 32'd0;
  reg [31:0] otr_b_count = 32'd0;
  wire [95:0] fifo_dout;
  wire fifo_empty;
  wire fifo_rd_rst_busy;
  wire fifo_rd_en;
  wire [FIFO_COUNT_WIDTH-1:0] monitor_level_narrow;

  always @(posedge core_clk) begin
    fifo_wr_en <= 1'b0;
    if (!resetn || clear_stream) begin
      mono_pack <= 0;
      mono_count <= 0;
      monitor_drop_count <= 0;
      otr_a_count <= 0;
      otr_b_count <= 0;
    end else if (sample_valid && monitor_enable) begin
      if (sample_otr[0] && otr_a_count != 32'hffff_ffff)
        otr_a_count <= otr_a_count + 1'b1;
      if (sample_otr[1] && otr_b_count != 32'hffff_ffff)
        otr_b_count <= otr_b_count + 1'b1;
      if (adc_model) begin
        if (!monitor_fifo_full) begin
          // Network byte order contains A_L, A_H, B_L, B_H.
          fifo_din <= {sample_index,
                       sample_pair[7:0], sample_pair[15:8],
                       sample_pair[23:16], sample_pair[31:24]};
          fifo_wr_en <= 1'b1;
        end else if (monitor_drop_count != 32'hffff_ffff) begin
          monitor_drop_count <= monitor_drop_count + 1'b1;
        end
      end else begin
        mono_pack <= {mono_pack[23:0], sample_u8};
        mono_count <= mono_count + 1'b1;
        if (mono_count == 2'd3) begin
          mono_count <= 0;
          if (!monitor_fifo_full) begin
            fifo_din <= {sample_index - 64'd3,
                         mono_pack[23:0], sample_u8};
            fifo_wr_en <= 1'b1;
          end else if (monitor_drop_count <= 32'hffff_fffb) begin
            monitor_drop_count <= monitor_drop_count + 3'd4;
          end
        end
      end
    end
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
      .RD_DATA_COUNT_WIDTH(FIFO_COUNT_WIDTH),
      .READ_DATA_WIDTH(96),
      .READ_MODE("fwft"),
      .RELATED_CLOCKS(0),
      .SIM_ASSERT_CHK(SIM_ASSERT_CHK),
      .USE_ADV_FEATURES("0707"),
      .WAKEUP_TIME(0),
      .WRITE_DATA_WIDTH(96),
      .WR_DATA_COUNT_WIDTH(FIFO_COUNT_WIDTH)
  ) monitor_fifo (
      .rst(fifo_reset),
      .wr_clk(core_clk), .wr_en(fifo_wr_en), .din(fifo_din),
      .full(monitor_fifo_full), .overflow(), .wr_data_count(),
      .prog_full(), .almost_full(), .wr_ack(), .wr_rst_busy(),
      .rd_clk(gmii_clk), .rd_en(fifo_rd_en), .dout(fifo_dout),
      .empty(fifo_empty), .underflow(), .rd_data_count(monitor_level_narrow),
      .prog_empty(), .almost_empty(), .data_valid(), .rd_rst_busy(fifo_rd_rst_busy),
      .sleep(1'b0), .injectsbiterr(1'b0), .injectdbiterr(1'b0),
      .sbiterr(), .dbiterr()
  );
  assign monitor_fifo_level =
      {{(15-FIFO_COUNT_WIDTH){1'b0}}, monitor_level_narrow};

  // Configuration changes only in STOPPED state and is stable before START,
  // so two-stage sampling is sufficient for these control/status buses.
  reg [31:0] stream_sync1 = 0, stream_sync2 = 0;
  reg [31:0] rate_sync1 = 0, rate_sync2 = 0;
  reg [31:0] measured_sync1 = 0, measured_sync2 = 0;
  reg [31:0] overflow_sync1 = 0, overflow_sync2 = 0;
  reg [31:0] event_sync1 = 0, event_sync2 = 0;
  reg [31:0] event_drop_sync1 = 0, event_drop_sync2 = 0;
  reg [31:0] event_suppressed_sync1 = 0, event_suppressed_sync2 = 0;
  reg [31:0] transaction_sync1 = 0, transaction_sync2 = 0;
  reg [31:0] monitor_drop_sync1 = 0, monitor_drop_sync2 = 0;
  reg [31:0] otr_a_sync1 = 0, otr_a_sync2 = 0;
  reg [31:0] otr_b_sync1 = 0, otr_b_sync2 = 0;
  reg [63:0] interval_sync1 = 0, interval_sync2 = 0;
  reg [14:0] ingress_level_sync1 = 0, ingress_level_sync2 = 0;
  reg [2:0] state_sync1 = 0, state_sync2 = 0;
  reg [7:0] error_sync1 = 0, error_sync2 = 0;
  reg [1:0] model_sync = 0, jumbo_sync = 0, monitor_sync = 0;
  reg [1:0] event_path_sync = 0;
  reg [1:0] status_sync = 0;
  reg status_seen = 0;
  reg status_request_pulse = 0;
  reg status_pending = 0;

  always @(posedge gmii_clk) begin
    status_request_pulse <= 1'b0;
    stream_sync1 <= stream_id; stream_sync2 <= stream_sync1;
    rate_sync1 <= sample_rate_hz; rate_sync2 <= rate_sync1;
    measured_sync1 <= measured_rate_hz; measured_sync2 <= measured_sync1;
    overflow_sync1 <= active_overflow_count; overflow_sync2 <= overflow_sync1;
    event_sync1 <= event_count; event_sync2 <= event_sync1;
    event_drop_sync1 <= dropped_event_count; event_drop_sync2 <= event_drop_sync1;
    event_suppressed_sync1 <= suppressed_event_count;
    event_suppressed_sync2 <= event_suppressed_sync1;
    transaction_sync1 <= transaction_id; transaction_sync2 <= transaction_sync1;
    monitor_drop_sync1 <= monitor_drop_count; monitor_drop_sync2 <= monitor_drop_sync1;
    otr_a_sync1 <= otr_a_count; otr_a_sync2 <= otr_a_sync1;
    otr_b_sync1 <= otr_b_count; otr_b_sync2 <= otr_b_sync1;
    interval_sync1 <= interval_mean_q16; interval_sync2 <= interval_sync1;
    ingress_level_sync1 <= active_fifo_level; ingress_level_sync2 <= ingress_level_sync1;
    state_sync1 <= acquisition_state; state_sync2 <= state_sync1;
    error_sync1 <= last_error; error_sync2 <= error_sync1;
    model_sync <= {model_sync[0], adc_model};
    jumbo_sync <= {jumbo_sync[0], jumbo_enable};
    monitor_sync <= {monitor_sync[0], monitor_enable};
    event_path_sync <= {event_path_sync[0], event_path_enable};
    status_sync <= {status_sync[0], status_toggle};
    if (status_sync[1] != status_seen) begin
      status_seen <= status_sync[1];
      status_request_pulse <= 1'b1;
    end
  end

  // A complete packet is staged before tx_start_en.  The 64-bit index carried
  // with every FIFO word is checked while filling this RAM.  A discontinuity
  // discards only the unsent partial packet and restarts at the new real index,
  // so a transmitted DAQD payload can never contain an unmarked hole.
  wire [31:0] packet_rd_data;
  reg [11:0] stage_count = 12'd0;
  reg [14:0] stage_target_words = STD_PAYLOAD_WORDS;
  reg [63:0] stage_first_index = 64'd0;
  reg [63:0] stage_expected_index = 64'd0;
  reg [31:0] stage_stream_id = 32'd0;
  reg [31:0] stage_rate_hz = 32'd0;
  reg stage_model = 1'b0;
  reg stage_jumbo = 1'b0;
  reg packet_ready = 1'b0;
  reg [31:0] assembly_discard_count = 32'd0;

  reg busy = 1'b0;
  reg sending_status = 1'b0;
  reg [11:0] word_index = 12'd0;
  reg [31:0] packet_sequence = 32'd0;
  reg [63:0] first_sample_index = 64'd0;
  reg [31:0] active_stream_id = 32'd0;
  reg [31:0] active_rate_hz = 32'd0;
  reg active_model = 1'b0;
  reg active_jumbo = 1'b0;
  reg [15:0] active_payload_bytes = STD_PAYLOAD_BYTES;
  reg [14:0] active_payload_words = STD_PAYLOAD_WORDS;
  reg [31:0] active_sample_count = 32'd0;

  wire [63:0] fifo_sample_index = fifo_dout[95:32];
  wire [31:0] fifo_payload_word = fifo_dout[31:0];
  wire [14:0] requested_words = jumbo_sync[1] ?
      JUMBO_PAYLOAD_WORDS : STD_PAYLOAD_WORDS;
  wire [63:0] requested_index_step = model_sync[1] ? 64'd1 : 64'd4;
  wire stream_changed = stream_sync2 != active_stream_id;
  wire stage_allowed = !busy && !packet_ready && !stream_changed &&
      monitor_sync[1] && !status_pending && !status_request_pulse;
  wire [31:0] staged_discard_samples = stage_model ?
      {20'd0, stage_count} : {18'd0, stage_count, 2'b00};
  wire [32:0] total_monitor_drop =
      {1'b0, monitor_drop_sync2} + {1'b0, assembly_discard_count};
  wire packet_wr_en = fifo_rd_en;
  wire [10:0] packet_wr_addr =
      (stage_count == 0 || fifo_sample_index != stage_expected_index) ?
      11'd0 : stage_count[10:0];
  wire [31:0] packet_wr_data = fifo_payload_word;
  wire packet_rd_en = busy && !sending_status && tx_req &&
      (word_index >= 12'd9);
  wire [10:0] packet_rd_addr =
      (word_index >= 12'd9) ? word_index[10:0] - 11'd9 : 11'd0;

  // Use an explicit synchronous simple-dual-port XPM so the 8 KiB packet
  // buffer is guaranteed to map to BRAM rather than thousands of flip-flops.
  // Address zero is prefetched while header word 9 is accepted; READ_LATENCY=1
  // then presents each payload word on the following tx_req cycle.
  xpm_memory_sdpram #(
      .ADDR_WIDTH_A(11),
      .ADDR_WIDTH_B(11),
      .AUTO_SLEEP_TIME(0),
      .BYTE_WRITE_WIDTH_A(32),
      .CLOCKING_MODE("common_clock"),
      .ECC_MODE("no_ecc"),
      .MEMORY_INIT_FILE("none"),
      .MEMORY_INIT_PARAM(""),
      .MEMORY_OPTIMIZATION("true"),
      .MEMORY_PRIMITIVE("block"),
      .MEMORY_SIZE(65536),
      .MESSAGE_CONTROL(0),
      .READ_DATA_WIDTH_B(32),
      .READ_LATENCY_B(1),
      .READ_RESET_VALUE_B("0"),
      .RST_MODE_A("SYNC"),
      .RST_MODE_B("SYNC"),
      .SIM_ASSERT_CHK(SIM_ASSERT_CHK),
      .USE_MEM_INIT(0),
      .WAKEUP_TIME("disable_sleep"),
      .WRITE_DATA_WIDTH_A(32),
      .WRITE_MODE_B("read_first")
  ) packet_buffer (
      .sleep(1'b0),
      .clka(gmii_clk),
      .ena(packet_wr_en),
      .wea(packet_wr_en),
      .addra(packet_wr_addr),
      .dina(packet_wr_data),
      .injectsbiterra(1'b0),
      .injectdbiterra(1'b0),
      .clkb(gmii_clk),
      // Contents are protected by packet_ready/stage_count and never need
      // clearing.  Keeping the BRAM reset inactive also avoids an asynchronous
      // control path into the RAM primitive.
      .rstb(1'b0),
      .enb(packet_rd_en),
      .regceb(1'b1),
      .addrb(packet_rd_addr),
      .doutb(packet_rd_data),
      .sbiterrb(),
      .dbiterrb()
  );

  function [31:0] data_header_word;
    input [3:0] index;
    begin
      case (index)
        4'd0: data_header_word = DATA_MAGIC;
        4'd1: data_header_word = {8'd1, active_model ? 8'd2 : 8'd1,
                                  active_model ? 8'd2 : 8'd1,
                                  active_model ? 8'd2 : 8'd1};
        4'd2: data_header_word = active_stream_id;
        4'd3: data_header_word = packet_sequence;
        4'd4: data_header_word = active_rate_hz;
        4'd5: data_header_word = first_sample_index[63:32];
        4'd6: data_header_word = first_sample_index[31:0];
        4'd7: data_header_word = active_sample_count;
        4'd8: data_header_word = {29'd0, active_jumbo, active_model, 1'b0};
        4'd9: data_header_word = {HEADER_BYTES, active_payload_bytes};
        default: data_header_word = 32'd0;
      endcase
    end
  endfunction

  function [31:0] status_word;
    input [4:0] index;
    begin
      case (index)
        4'd0: status_word = STATUS_MAGIC;
        4'd1: status_word = {8'd1, 4'd0, state_sync2, model_sync[1],
                             8'd0, error_sync2};
        4'd2: status_word = active_stream_id;
        4'd3: status_word = rate_sync2;
        4'd4: status_word = measured_sync2;
        4'd5: status_word = {17'd0, ingress_level_sync2};
        4'd6: status_word = overflow_sync2;
        4'd7: status_word = total_monitor_drop[32] ?
            32'hffff_ffff : total_monitor_drop[31:0];
        4'd8: status_word = packet_count;
        4'd9: status_word = event_sync2;
        4'd10: status_word = event_drop_sync2;
        4'd11: status_word = {29'd0, jumbo_sync[1], monitor_sync[1], model_sync[1]};
        4'd12: status_word = 32'h0001_0000; // hardware/protocol revision
        4'd13: status_word = transaction_sync2;
        5'd14: status_word = otr_a_sync2;
        5'd15: status_word = otr_b_sync2;
        5'd16: status_word = interval_sync2[31:0];
        5'd17: status_word = interval_sync2[63:32];
        5'd18: status_word = event_suppressed_sync2;
        5'd19: status_word = {31'd0, event_path_sync[1]};
        default: status_word = 32'd0;
      endcase
    end
  endfunction

  // The FWFT word is consumed only after it has been copied into packet_mem.
  // No monitor FIFO read is tied directly to the UDP transmitter anymore.
  assign fifo_rd_en = stage_allowed && !fifo_empty;

  always @(posedge gmii_clk) begin
    tx_start_en <= 1'b0;
    if (!resetn || fifo_rd_rst_busy) begin
      busy <= 1'b0;
      sending_status <= 1'b0;
      word_index <= 0;
      packet_sequence <= 0;
      first_sample_index <= 0;
      active_stream_id <= 0;
      active_rate_hz <= 0;
      packet_count <= 0;
      stage_count <= 0;
      stage_target_words <= STD_PAYLOAD_WORDS;
      stage_first_index <= 0;
      stage_expected_index <= 0;
      stage_stream_id <= 0;
      stage_rate_hz <= 0;
      stage_model <= 0;
      stage_jumbo <= 0;
      packet_ready <= 0;
      assembly_discard_count <= 0;
      tx_byte_num <= 0;
      tx_data <= 0;
      tx_src_port <= 16'd5001;
      tx_dst_port <= 16'd5001;
      status_pending <= 1'b0;
    end else begin
      if (status_request_pulse)
        status_pending <= 1'b1;

      if (!busy && stream_sync2 != active_stream_id) begin
        active_stream_id <= stream_sync2;
        packet_sequence <= 0;
        first_sample_index <= 0;
        stage_count <= 0;
        packet_ready <= 1'b0;
        assembly_discard_count <= 0;
      end

      if (fifo_rd_en) begin
        if (stage_count == 0) begin
          stage_count <= 12'd1;
          stage_target_words <= requested_words;
          stage_first_index <= fifo_sample_index;
          stage_expected_index <= fifo_sample_index + requested_index_step;
          stage_stream_id <= stream_sync2;
          stage_rate_hz <= rate_sync2;
          stage_model <= model_sync[1];
          stage_jumbo <= jumbo_sync[1];
          if (requested_words == 1)
            packet_ready <= 1'b1;
        end else if (fifo_sample_index == stage_expected_index) begin
          stage_count <= stage_count + 1'b1;
          stage_expected_index <= stage_expected_index +
              (stage_model ? 64'd1 : 64'd4);
          if (stage_count + 1'b1 == stage_target_words)
            packet_ready <= 1'b1;
        end else begin
          // The partial payload has never been exposed to the MAC.  Count it
          // as monitor-only loss and restart at the first post-gap sample.
          if (assembly_discard_count >
              32'hffff_ffff - staged_discard_samples)
            assembly_discard_count <= 32'hffff_ffff;
          else
            assembly_discard_count <= assembly_discard_count +
                staged_discard_samples;
          stage_count <= 12'd1;
          stage_target_words <= requested_words;
          stage_first_index <= fifo_sample_index;
          stage_expected_index <= fifo_sample_index + requested_index_step;
          stage_stream_id <= stream_sync2;
          stage_rate_hz <= rate_sync2;
          stage_model <= model_sync[1];
          stage_jumbo <= jumbo_sync[1];
          packet_ready <= (requested_words == 1);
        end
      end

      if (!busy) begin
        word_index <= 0;
        if (status_pending || status_request_pulse) begin
          status_pending <= 1'b0;
          sending_status <= 1'b1;
          busy <= 1'b1;
          tx_src_port <= 16'd5000;
          tx_dst_port <= 16'd5000;
          tx_byte_num <= 16'd80;
          tx_start_en <= 1'b1;
        end else if (monitor_sync[1] && packet_ready) begin
          active_model <= stage_model;
          active_jumbo <= stage_jumbo;
          active_rate_hz <= stage_rate_hz;
          active_stream_id <= stage_stream_id;
          first_sample_index <= stage_first_index;
          active_payload_bytes <= stage_jumbo ?
              JUMBO_PAYLOAD_BYTES : STD_PAYLOAD_BYTES;
          active_payload_words <= stage_jumbo ?
              JUMBO_PAYLOAD_WORDS : STD_PAYLOAD_WORDS;
          active_sample_count <= stage_model ? stage_target_words :
              {15'd0, stage_target_words, 2'b00};
          sending_status <= 1'b0;
          busy <= 1'b1;
          tx_src_port <= 16'd5001;
          tx_dst_port <= 16'd5001;
          tx_byte_num <= HEADER_BYTES +
              (stage_jumbo ? JUMBO_PAYLOAD_BYTES : STD_PAYLOAD_BYTES);
          tx_start_en <= 1'b1;
        end
      end else if (tx_req) begin
        if (sending_status) begin
          tx_data <= status_word(word_index[4:0]);
        end else if (word_index < 12'd10) begin
          tx_data <= data_header_word(word_index[3:0]);
        end else begin
          tx_data <= packet_rd_data;
        end
        word_index <= word_index + 1'b1;
      end

      if (busy && tx_done) begin
        busy <= 1'b0;
        if (!sending_status) begin
          packet_sequence <= packet_sequence + 1'b1;
          packet_count <= packet_count + 1'b1;
          packet_ready <= 1'b0;
          stage_count <= 0;
        end
      end
    end
  end
endmodule
