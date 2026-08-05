`timescale 1ns/1ps
module tb_pl_raw_udp_streamer;
  reg core_clk=0, gmii_clk=0, resetn=0, clear_stream=0;
  reg monitor_enable=0, jumbo_enable=0, adc_model=0, sample_valid=0;
  reg [31:0] sample_rate_hz=3_000_000, stream_id=1, sample_pair=0;
  reg [7:0] sample_u8=0; reg [1:0] sample_otr=0;
  reg status_toggle=0; reg [2:0] acquisition_state=3;
  reg [7:0] last_error=0; reg [31:0] measured_rate_hz=3_000_000;
  reg [14:0] active_fifo_level=7; reg [31:0] active_overflow_count=0;
  reg [31:0] event_count=9, dropped_event_count=2;
  reg [31:0] suppressed_event_count=17, transaction_id=32'h1234;
  reg event_path_enable=1;
  reg [63:0] interval_mean_q16=64'h0000_0001_8000_0000;
  reg tx_done=0, tx_req=0;
  wire tx_start_en; wire [31:0] tx_data; wire [15:0] tx_byte_num;
  wire [15:0] tx_src_port,tx_dst_port; wire [14:0] monitor_fifo_level;
  wire monitor_fifo_full; wire [31:0] monitor_drop_count,packet_count;
  reg [31:0] packet[0:2057];
  integer i;
  always #5 core_clk=~core_clk;
  always #4 gmii_clk=~gmii_clk;

  pl_raw_udp_streamer #(.SIM_ASSERT_CHK(0)) dut (.*);

  task automatic push_mono(input integer count, input [7:0] first);
    begin
      for(i=0;i<count;i=i+1) begin
        @(negedge core_clk); sample_valid=1; sample_u8=first+i;
      end
      @(negedge core_clk); sample_valid=0;
    end
  endtask

  task automatic push_dual(input integer count, input [15:0] first_a);
    begin
      for(i=0;i<count;i=i+1) begin
        @(negedge core_clk); sample_valid=1;
        sample_pair={16'h8000+i[15:0],first_a+i[15:0]};
        sample_otr=(i==3)?2'b01:2'b00;
      end
      @(negedge core_clk); sample_valid=0; sample_otr=0;
    end
  endtask

  task automatic collect_packet(input integer words, input integer bytes);
    begin
      $display("WAIT packet bytes=%0d time=%0t fifo=%0d stream=%0d",bytes,$time,monitor_fifo_level,stream_id);
      wait(tx_start_en);
      $display("GOT packet bytes=%0d time=%0t fifo=%0d",tx_byte_num,$time,monitor_fifo_level);
      if(tx_byte_num!==bytes || tx_src_port!==tx_dst_port)
        $fatal(1,"packet metadata bytes=%0d ports=%0d/%0d",tx_byte_num,tx_src_port,tx_dst_port);
      for(i=0;i<words;i=i+1) begin
        @(negedge gmii_clk); tx_req=1;
        @(posedge gmii_clk); #1 packet[i]=tx_data;
      end
      @(negedge gmii_clk); tx_req=0; tx_done=1;
      @(negedge gmii_clk); tx_done=0;
      repeat(3) @(posedge gmii_clk);
    end
  endtask

  task automatic pulse_clear;
    begin
      @(negedge core_clk); clear_stream=1;
      repeat(4) @(negedge core_clk);
      clear_stream=0;
      repeat(80) @(posedge core_clk);
    end
  endtask

  initial begin
    repeat(8) @(posedge core_clk); resetn=1;
    repeat(80) @(posedge core_clk);

    status_toggle=1;
    collect_packet(20,80);
    if(packet[0]!==32'h44415153 || packet[2]!==1 || packet[3]!==3_000_000 ||
       packet[9]!==9 || packet[10]!==2 || packet[13]!==32'h1234 ||
       packet[16]!==32'h8000_0000 || packet[17]!==1 ||
       packet[18]!==17 || packet[19]!==1)
      $fatal(1,"DAQS base/extension mismatch");

    monitor_enable=1;
    push_mono(1408,8'h10);
    $display("mono pushed time=%0t fifo=%0d",$time,monitor_fifo_level);
    collect_packet(362,1448);
    if(packet[0]!==32'h44415144 || packet[1]!==32'h01010101 || packet[2]!==1 ||
       packet[3]!==0 || packet[5]!==0 || packet[6]!==0 ||
       packet[9]!=={16'd40,16'd1408}) $fatal(1,"AD9280 header mismatch");
    if(packet[10]!==32'h10111213 || packet[11]!==32'h14151617 ||
       packet[361]!==32'h8c8d8e8f) $fatal(1,"AD9280 payload order");

    repeat(20) @(posedge core_clk);
    adc_model=1; stream_id=2;
    sample_rate_hz=20_000_000; measured_rate_hz=20_000_000;
    push_dual(352,16'h0100);
    $display("dual pushed time=%0t fifo=%0d",$time,monitor_fifo_level);
    collect_packet(362,1448);
    if(packet[1]!==32'h01020202 || packet[2]!==2 || packet[3]!==0 ||
       packet[4]!==20_000_000 || packet[9]!=={16'd40,16'd1408})
      $fatal(1,"AD9269 standard header mismatch");
    if(packet[10]!==32'h00010080 || packet[11]!==32'h01010180 ||
       packet[361]!==32'h5f025f81) $fatal(1,"AD9269 little-endian payload order");

    repeat(20) @(posedge core_clk);
    jumbo_enable=1; stream_id=3;
    push_dual(2048,16'h1000);
    $display("jumbo pushed time=%0t fifo=%0d",$time,monitor_fifo_level);
    collect_packet(2058,8232);
    if(packet[2]!==3 || packet[3]!==0 || packet[9]!=={16'd40,16'd8192} ||
       packet[10]!==32'h00100080 || packet[2057]!==32'hff17ff87)
      $fatal(1,"AD9269 jumbo/stream reset mismatch");
    $display("PASS: DAQS extension, U8/S16 payload order, standard/jumbo MTU, stream and sequence");
    $finish;
  end
  initial begin
    #2_000_000;
    $display("DEBUG timeout busy=%b fifo=%0d enough=%b monitor=%b rd_busy=%b requested=%0d stream_sync=%0d active_stream=%0d",
             dut.busy,monitor_fifo_level,dut.enough_data,dut.monitor_sync[1],
             dut.fifo_rd_rst_busy,dut.requested_words,dut.stream_sync2,dut.active_stream_id);
    $fatal(1,"tb_pl_raw_udp_streamer timeout");
  end
endmodule
