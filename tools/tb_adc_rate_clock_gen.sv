`timescale 1ns/1ps

module tb_adc_rate_clock_gen;
  reg clk_100m = 0;
  always #5 clk_100m = ~clk_100m;
  reg resetn = 0;
  reg clock_enable = 0;
  reg [2:0] rate_sel = 1;
  wire sample_clk;
  wire adc_clk;
  wire locked;
  wire [31:0] configured_rate_hz;
  integer failures = 0;
  realtime t0;
  realtime t1;
  realtime measured;

  adc_rate_clock_gen dut (
      .clk_100m(clk_100m), .resetn(resetn),
      .clock_enable(clock_enable), .rate_sel(rate_sel),
      .sample_clk(sample_clk), .ad9269_clk_pin(adc_clk),
      .locked(locked), .configured_rate_hz(configured_rate_hz)
  );

  task check_rate;
    input [2:0] selector;
    input integer expected_hz;
    input realtime expected_period_ns;
    begin
      clock_enable = 0;
      repeat (8) @(posedge clk_100m);
      rate_sel = selector;
      repeat (4) @(posedge clk_100m);
      if (configured_rate_hz !== expected_hz) begin
        $display("FAIL: selector %0d rate register %0d",
                 selector, configured_rate_hz);
        failures = failures + 1;
      end
      clock_enable = 1;
      repeat (3) @(posedge adc_clk);
      t0 = $realtime;
      @(posedge adc_clk);
      t1 = $realtime;
      measured = t1 - t0;
      if (measured < expected_period_ns - 0.2 ||
          measured > expected_period_ns + 0.2) begin
        $display("FAIL: selector %0d period=%0.3f expected=%0.3f",
                 selector, measured, expected_period_ns);
        failures = failures + 1;
      end
    end
  endtask

  initial begin
    repeat (5) @(posedge clk_100m);
    resetn = 1;
    fork
      begin
        wait (locked);
        check_rate(3'd1, 5000000, 200.0);
        check_rate(3'd2, 10000000, 100.0);
        check_rate(3'd3, 20000000, 50.0);
        check_rate(3'd4, 40000000, 25.0);
        check_rate(3'd5, 80000000, 12.5);
        clock_enable = 0;
        repeat (6) @(posedge clk_100m);
        if (adc_clk !== 1'b0) begin
          $display("FAIL: forwarded clock did not stop low");
          failures = failures + 1;
        end
        if (failures == 0)
          $display("PASS: AD9269 5/10/20/40/80 MHz single-BUFG clock");
        else
          $fatal(1, "Clock generator failures=%0d", failures);
        $finish;
      end
      begin
        #100000;
        $fatal(1, "TIMEOUT: clock generator");
      end
    join_any
  end
endmodule
