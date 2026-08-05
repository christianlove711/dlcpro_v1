`timescale 1ps/1ps

module tb_rgmii_ddr_mapping;
  reg raw_rxc = 1'b0;
  reg resetn = 1'b0;
  wire shifted_clk;
  wire mmcm_locked;

  reg map_clk = 1'b0;
  reg [3:0] rgmii_rxd = 4'h0;
  reg rgmii_rx_ctl = 1'b0;
  wire gmii_rx_clk;
  wire gmii_rx_dv;
  wire [7:0] gmii_rxd;

  reg gmii_tx_en = 1'b0;
  reg [7:0] gmii_txd = 8'h00;
  wire rgmii_txc;
  wire rgmii_tx_ctl;
  wire [3:0] rgmii_txd;

  integer errors = 0;
  integer timeout_cycles;
  time raw_edge_time;
  time shifted_edge_time;
  time phase_delta;

  always #4000 raw_rxc = ~raw_rxc;
  always #4000 map_clk = ~map_clk;

  pl_rgmii_clock clock_dut (
      .rgmii_rxc(raw_rxc),
      .resetn(resetn),
      .gmii_clk_125m(shifted_clk),
      .locked(mmcm_locked)
  );

  rgmii_rx rx_dut (
      .rgmii_rxc(map_clk),
      .rgmii_rx_ctl(rgmii_rx_ctl),
      .rgmii_rxd(rgmii_rxd),
      .gmii_rx_clk(gmii_rx_clk),
      .gmii_rx_dv(gmii_rx_dv),
      .gmii_rxd(gmii_rxd)
  );

  rgmii_tx tx_dut (
      .gmii_tx_clk(map_clk),
      .gmii_tx_en(gmii_tx_en),
      .gmii_txd(gmii_txd),
      .rgmii_txc(rgmii_txc),
      .rgmii_tx_ctl(rgmii_tx_ctl),
      .rgmii_txd(rgmii_txd)
  );

  task automatic check_cond(input bit condition, input string message);
    begin
      if (!condition) begin
        $display("ERROR: %s at %0t ps", message, $time);
        errors = errors + 1;
      end
    end
  endtask

  task automatic rx_byte(input [7:0] expected, input bit valid);
    begin
      // rgmii_rx intentionally maps its C0 sample to the high nibble and its
      // C1 sample to the low nibble.  DDR_ALIGNMENT="C0" presents the C1
      // sample together with the following C0 sample, so drive low on C1,
      // high on the next C0, then inspect the aligned byte.
      @(posedge map_clk);
      #1000;
      rgmii_rxd = expected[3:0];
      rgmii_rx_ctl = valid;
      @(negedge map_clk);
      #1000;
      rgmii_rxd = expected[7:4];
      rgmii_rx_ctl = valid;
      @(posedge map_clk);
      #100;
      check_cond(gmii_rxd === expected, $sformatf("RX byte mismatch: expected %02x got %02x", expected, gmii_rxd));
      check_cond(gmii_rx_dv === valid, "RX_CTL/DV mapping mismatch");
    end
  endtask

  task automatic tx_byte(input [7:0] value, input bit enable);
    begin
      @(negedge map_clk);
      #1000;
      gmii_txd = value;
      gmii_tx_en = enable;
      @(posedge map_clk);
      #100;
      check_cond(rgmii_txd === value[3:0], "TX rising-edge low nibble mismatch");
      check_cond(rgmii_tx_ctl === enable, "TX_CTL rising-edge mismatch");
      @(negedge map_clk);
      #100;
      check_cond(rgmii_txd === value[7:4], "TX falling-edge high nibble mismatch");
      check_cond(rgmii_tx_ctl === enable, "TX_CTL falling-edge mismatch");
    end
  endtask

  initial begin
    #20000;
    resetn = 1'b1;

    timeout_cycles = 0;
    while (!mmcm_locked && timeout_cycles < 2000) begin
      @(posedge raw_rxc);
      timeout_cycles = timeout_cycles + 1;
    end
    check_cond(mmcm_locked, "MMCM did not lock");

    // Measure one stable pair of corresponding rising edges.  The modulo-one-
    // period value must match the production 208.125-degree phase (4.625 ns).
    @(posedge raw_rxc);
    raw_edge_time = $time;
    @(posedge shifted_clk);
    shifted_edge_time = $time;
    phase_delta = (shifted_edge_time - raw_edge_time) % 8000;
    check_cond((phase_delta >= 4500) && (phase_delta <= 4750),
           $sformatf("MMCM phase expected 4625 ps, measured %0t ps", phase_delta));

    // Known Ethernet preamble/SFD values catch a silent nibble-order change.
    rx_byte(8'h55, 1'b1);
    rx_byte(8'h55, 1'b1);
    rx_byte(8'hD5, 1'b1);
    rx_byte(8'h00, 1'b0);
    tx_byte(8'h55, 1'b1);
    tx_byte(8'hD5, 1'b1);
    tx_byte(8'h00, 1'b0);

    // A reset must remove lock, then recover.  Keeping RX_CTL low for two DDR
    // edges proves that the receive bridge cannot report a stale valid frame.
    resetn = 1'b0;
    rgmii_rx_ctl = 1'b0;
    rgmii_rxd = 4'h0;
    repeat (4) @(posedge raw_rxc);
    check_cond(!mmcm_locked, "MMCM lock remained asserted during reset");
    repeat (2) @(posedge map_clk);
    #100;
    check_cond(!gmii_rx_dv, "RX_DV remained asserted after reset-idle edges");

    resetn = 1'b1;
    timeout_cycles = 0;
    while (!mmcm_locked && timeout_cycles < 2000) begin
      @(posedge raw_rxc);
      timeout_cycles = timeout_cycles + 1;
    end
    check_cond(mmcm_locked, "MMCM did not relock");

    if (errors == 0)
      $display("PASS: RGMII DDR nibble mapping, phase, RX_CTL and MMCM recovery");
    else
      $fatal(1, "RGMII DDR mapping test failed with %0d errors", errors);
    $finish;
  end

  initial begin
    #50000000;
    $fatal(1, "Timeout waiting for RGMII DDR mapping test");
  end
endmodule
