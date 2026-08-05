`timescale 1ns/1ps

module tb_ad9269_scope_capture;
  localparam integer SAMPLES = 64;
  localparam integer HEADER = 16;
  reg clk = 0;
  always #5 clk = ~clk;

  reg resetn = 0;
  reg clear = 0;
  reg mode_scope = 1;
  reg armed = 0;
  reg abort = 0;
  reg [3:0] decimation_log2 = 0;
  reg [1:0] trigger_mode = 0;
  reg trigger_channel = 0;
  reg signed [15:0] trigger_level = 0;
  reg fps_20 = 1;
  reg [31:0] stream_id = 32'h12345678;
  reg [31:0] sample_rate_hz = 32'd80000000;
  reg sample_valid = 1;
  reg [31:0] sample_pair = 0;
  reg [1:0] sample_otr = 0;
  reg [63:0] sample_index = 0;
  wire [31:0] scope_data;
  wire scope_valid;
  reg scope_ready = 0;
  wire scope_last;
  wire busy;
  wire triggered;
  wire overflow;
  wire [31:0] frame_count;
  wire [31:0] suppressed_count;
  wire [31:0] dropped_count;

  integer cycle = 0;
  integer words = 0;
  integer failures = 0;
  reg [31:0] held_data;
  reg held_last;
  reg was_stalled = 0;

  ad9269_scope_capture #(
      .SAMPLES_PER_FRAME(SAMPLES),
      .HEADER_WORDS(HEADER),
      .CORE_HZ(20000)
  ) dut (
      .clk(clk), .resetn(resetn), .clear(clear), .mode_scope(mode_scope),
      .armed(armed), .abort(abort), .decimation_log2(decimation_log2),
      .trigger_mode(trigger_mode), .trigger_channel(trigger_channel),
      .trigger_level(trigger_level), .fps_20(fps_20),
      .stream_id(stream_id), .sample_rate_hz(sample_rate_hz),
      .sample_valid(sample_valid), .sample_pair(sample_pair),
      .sample_otr(sample_otr), .sample_index(sample_index),
      .scope_data(scope_data), .scope_valid(scope_valid),
      .scope_ready(scope_ready), .scope_last(scope_last), .busy(busy),
      .triggered(triggered), .overflow(overflow),
      .frame_count(frame_count), .suppressed_count(suppressed_count),
      .dropped_count(dropped_count)
  );

  always @(negedge clk) begin
    cycle = cycle + 1;
    sample_pair = {sample_index[15:0] + 16'h4000, sample_index[15:0]};
    sample_index = sample_index + 1;
    // Repeatedly exercise AXIS backpressure.
    scope_ready = ((cycle % 5) != 0) && ((cycle % 7) != 0);
  end

  always @(posedge clk) begin
    if (scope_valid && !scope_ready) begin
      if (was_stalled &&
          (scope_data !== held_data || scope_last !== held_last)) begin
        $display("FAIL: AXIS output changed during backpressure");
        failures = failures + 1;
      end
      held_data = scope_data;
      held_last = scope_last;
      was_stalled = 1;
    end else begin
      was_stalled = 0;
    end

    if (scope_valid && scope_ready) begin
      if (words == 0 && scope_data !== 32'h504f4353) begin
        $display("FAIL: SCOP magic %08x", scope_data);
        failures = failures + 1;
      end
      if (words == 2 && scope_data !== stream_id) begin
        $display("FAIL: stream id %08x", scope_data);
        failures = failures + 1;
      end
      if (words == 4 && scope_data !== sample_rate_hz) begin
        $display("FAIL: sample rate %0d", scope_data);
        failures = failures + 1;
      end
      if (words == 14 && scope_data !== SAMPLES) begin
        $display("FAIL: sample count %0d", scope_data);
        failures = failures + 1;
      end
      if (words == 15 && scope_data !== HEADER*4) begin
        $display("FAIL: header bytes %0d", scope_data);
        failures = failures + 1;
      end
      if (scope_last !== (words == HEADER + SAMPLES - 1)) begin
        $display("FAIL: TLAST at word %0d", words);
        failures = failures + 1;
      end
      words = words + 1;
    end
  end

  initial begin
    repeat (5) @(posedge clk);
    resetn = 1;
    armed = 1;
    fork
      begin
        wait (words == HEADER + SAMPLES);
        repeat (4) @(posedge clk);
        if (frame_count < 1) begin
          $display("FAIL: frame_count=%0d", frame_count);
          failures = failures + 1;
        end
        if (overflow || dropped_count != 0) begin
          $display("FAIL: overflow=%0d dropped=%0d",
                   overflow, dropped_count);
          failures = failures + 1;
        end
        if (failures == 0)
          $display("PASS: AD9269 Scope frame, BRAM latency, TLAST and backpressure");
        else
          $fatal(1, "Scope capture failures=%0d", failures);
        $finish;
      end
      begin
        repeat (20000) @(posedge clk);
        $fatal(1, "TIMEOUT: Scope capture");
      end
    join_any
  end
endmodule
