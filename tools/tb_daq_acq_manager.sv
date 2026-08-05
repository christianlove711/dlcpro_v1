`timescale 1ns/1ps

module tb_daq_acq_manager;
  reg clk = 0;
  reg resetn = 0;
  always #5 clk = ~clk;

  reg udp_adc = 0, udp_swap = 0, udp_jumbo = 0, udp_monitor = 0;
  reg [2:0] udp_rate = 1, udp_test = 0;
  reg udp_cfg = 0, udp_start = 0, udp_stop = 0, udp_clear = 0;
  reg ps_adc = 0, ps_swap = 0, ps_jumbo = 0, ps_monitor = 0;
  reg ps_acq_mode = 1;
  reg [2:0] ps_rate = 1, ps_test = 0;
  reg ps_cfg = 0, ps_start = 0, ps_stop = 0, ps_clear = 0;
  reg clock_locked = 1;
  reg spi_done = 1;
  reg spi_error = 0;
  reg fifo_full = 0;
  reg [31:0] overflow_count = 0;

  wire adc_select, clock_enable, capture_enable, monitor_enable, feature_enable;
  wire channel_swap, jumbo_enable, clear_fifos, clear_stats;
  wire [2:0] rate_sel, test_mode, state;
  wire [31:0] stream_id;
  wire [7:0] last_error;
  wire acq_mode;

  daq_acq_manager #(
    .ARM_DELAY_CYCLES(8),
    .FIFO_RESET_CYCLES(4)
  ) dut (
    .clk(clk), .resetn(resetn),
    .udp_adc_select(udp_adc), .udp_rate_sel(udp_rate), .udp_test_mode(udp_test),
    .udp_channel_swap(udp_swap), .udp_jumbo(udp_jumbo), .udp_monitor(udp_monitor),
    .udp_config_pulse(udp_cfg), .udp_start_pulse(udp_start),
    .udp_stop_pulse(udp_stop), .udp_clear_pulse(udp_clear),
    .ps_adc_select(ps_adc), .ps_rate_sel(ps_rate), .ps_test_mode(ps_test),
    .ps_channel_swap(ps_swap), .ps_jumbo(ps_jumbo), .ps_monitor(ps_monitor),
    .ps_config_pulse(ps_cfg), .ps_start_pulse(ps_start),
    .ps_stop_pulse(ps_stop), .ps_clear_pulse(ps_clear),
    .ps_acq_mode(ps_acq_mode),
    .clock_locked(clock_locked), .active_fifo_full(fifo_full),
    .spi_done(spi_done), .spi_error(spi_error),
    .active_overflow_count(overflow_count),
    .adc_select(adc_select), .rate_sel(rate_sel), .test_mode(test_mode),
    .channel_swap(channel_swap), .jumbo_enable(jumbo_enable),
    .clock_enable(clock_enable), .capture_enable(capture_enable),
    .monitor_enable(monitor_enable), .feature_enable(feature_enable),
    .clear_fifos(clear_fifos), .clear_stats(clear_stats),
    .stream_id(stream_id), .state(state), .last_error(last_error),
    .acq_mode(acq_mode)
  );

  task pulse_ps_start_stop;
    begin
      @(negedge clk); ps_start = 1;
      @(negedge clk); ps_start = 0;
      wait (state == 3'd3);
      @(negedge clk); udp_stop = 1;
      @(negedge clk); udp_stop = 0;
      @(posedge clk);
      if (state != 3'd0 || capture_enable) $fatal(1, "UDP STOP did not stop PS start");
    end
  endtask

  integer i;
  initial begin
    repeat (4) @(posedge clk);
    resetn = 1;

    // Simultaneous commits: PS configuration must win.  START in the same
    // cycle must apply that configuration before entering ARMING.
    @(negedge clk);
    udp_adc = 0; udp_rate = 2; udp_cfg = 1; udp_start = 1;
    ps_adc = 1; ps_rate = 3; ps_test = 5; ps_swap = 1; ps_jumbo = 1;
    ps_cfg = 1; ps_start = 1; ps_monitor = 1;
    @(negedge clk);
    udp_cfg = 0; udp_start = 0; ps_cfg = 0; ps_start = 0;
    if (adc_select !== 1 || rate_sel !== 3 || test_mode !== 5 || !channel_swap || !jumbo_enable)
      $fatal(1, "PS simultaneous CONFIG priority failed");
    wait (state == 3'd3);
    if (!capture_enable || !feature_enable || !monitor_enable || !acq_mode)
      $fatal(1, "CONFIG+START did not enter RUNNING");
    if (clear_fifos)
      $fatal(1, "FIFO reset was still asserted when capture started");

    // A running commit is rejected and must not alter the active settings.
    @(negedge clk); udp_rate = 1; udp_cfg = 1;
    @(negedge clk); udp_cfg = 0;
    if (rate_sel !== 3 || last_error !== 8'd4)
      $fatal(1, "running CONFIG was not rejected");

    // Any control plane STOP has highest priority.
    @(negedge clk); ps_stop = 1; udp_start = 1;
    @(negedge clk); ps_stop = 0; udp_start = 0;
    if (state !== 3'd0 || capture_enable) $fatal(1, "STOP priority failed");

    // Repeated START/STOP must not accumulate state or ignore cross-plane STOP.
    for (i = 0; i < 100; i = i + 1)
      pulse_ps_start_stop();

    $display("PASS: dual control arbitration and 100 START/STOP cycles");
    $finish;
  end

  initial begin
    #200000;
    $fatal(1, "tb_daq_acq_manager timeout");
  end
endmodule
