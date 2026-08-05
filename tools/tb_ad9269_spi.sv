`timescale 1ns / 1ps

module tb_ad9269_spi;
  reg clk = 1'b0;
  reg resetn = 1'b0;
  reg reinit_toggle = 1'b0;
  reg [2:0] test_mode = 3'd3;
  reg acquisition_stopped = 1'b1;
  reg force_first_bad_id = 1'b0;
  reg force_all_bad_id = 1'b0;
  wire csb, sclk, sdio_o, sdio_oe;
  wire busy, done, error;
  wire [7:0] chip_id, chip_grade;
  wire [7:0] rb14, rb17, rb0d;
  wire [31:0] error_detail;
  reg [23:0] driven_shift = 24'd0;
  integer driven_bits = 0;
  integer frame_count = 0;
  reg [7:0] response;

  always #10 clk = ~clk;

  always @* begin
    case (dut.command_index)
      4: response = (force_all_bad_id ||
                     (force_first_bad_id && dut.attempt == 0)) ?
                    8'h00 : 8'h75;
      5: response = 8'hA0;
      6: response = 8'h21;
      7: response = 8'h27;
      8: response = {5'd0, test_mode};
      default: response = 8'h00;
    endcase
  end

  wire sdio_i = (dut.edge_count >= 16 && dut.edge_count <= 23) ?
                response[23-dut.edge_count] : 1'b0;

  ad9269_spi_init #(
      .STARTUP_CYCLES(4),
      .HALF_PERIOD_CYCLES(2)
  ) dut (
      .clk(clk), .resetn(resetn),
      .reinit_toggle(reinit_toggle), .test_mode(test_mode),
      .sdio_i(sdio_i), .acquisition_stopped(acquisition_stopped),
      .csb(csb), .sclk(sclk), .sdio_o(sdio_o), .sdio_oe(sdio_oe),
      .busy(busy), .done(done), .error(error),
      .chip_id(chip_id), .chip_grade(chip_grade),
      .readback_14(rb14), .readback_17(rb17), .readback_0d(rb0d),
      .error_detail(error_detail)
  );

  function [23:0] expected_command;
    input integer index;
    begin
      case (index)
        0: expected_command = 24'h001421;
        1: expected_command = 24'h001727;
        2: expected_command = {16'h000D,5'd0,test_mode};
        3: expected_command = 24'h00FF01;
        4: expected_command = 24'h800100;
        5: expected_command = 24'h800200;
        6: expected_command = 24'h801400;
        7: expected_command = 24'h801700;
        default: expected_command = 24'h800D00;
      endcase
    end
  endfunction

  always @(posedge sclk) begin
    if (!csb && sdio_oe) begin
      driven_shift = {driven_shift[22:0], sdio_o};
      driven_bits = driven_bits + 1;
    end
  end

  always @(posedge csb) begin
    integer index;
    reg [23:0] expected;
    if (driven_bits != 0) begin
      index = frame_count % 9;
      expected = expected_command(index);
      if (index < 4) begin
        if (driven_bits != 24 || driven_shift !== expected)
          $fatal(1, "write frame %0d mismatch bits=%0d got=%06x exp=%06x",
                 index, driven_bits, driven_shift, expected);
      end else begin
        if (driven_bits != 16 || driven_shift[15:0] !== expected[23:8])
          $fatal(1, "read instruction %0d mismatch bits=%0d got=%04x exp=%04x",
                 index, driven_bits, driven_shift[15:0], expected[23:8]);
      end
      frame_count = frame_count + 1;
      driven_bits = 0;
      driven_shift = 24'd0;
    end
  end

  initial begin
    repeat (3) @(posedge clk);
    resetn = 1'b1;

    wait (done && frame_count >= 9);
    if (busy || error || chip_id != 8'h75 || chip_grade != 8'hA0 ||
        rb14 != 8'h21 || rb17 != 8'h27 || rb0d != 8'h03)
      $fatal(1, "normal readback verification failed");

    force_first_bad_id = 1'b1;
    test_mode = 3'd5;
    reinit_toggle = ~reinit_toggle;
    wait (done && frame_count >= 27);
    if (error || dut.attempt != 1 || rb0d != 8'h05)
      $fatal(1, "retry-after-ID-mismatch failed");

    force_first_bad_id = 1'b0;
    force_all_bad_id = 1'b1;
    test_mode = 3'd6;
    reinit_toggle = ~reinit_toggle;
    wait (error && frame_count >= 54);
    if (done || error_detail == 0)
      $fatal(1, "three-attempt failure was not reported");

    force_all_bad_id = 1'b0;
    reinit_toggle = ~reinit_toggle;
    wait (done && frame_count >= 63);
    if (error || chip_id != 8'h75 || rb0d != 8'h06)
      $fatal(1, "recovery after failed verification failed");

    $display("PASS: AD9269 SPI readback, retry, failure and recovery");
    $finish;
  end

  initial begin
    #3000000;
    $fatal(1, "SPI test timeout");
  end
endmodule
