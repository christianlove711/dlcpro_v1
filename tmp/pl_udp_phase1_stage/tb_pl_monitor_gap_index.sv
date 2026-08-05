`timescale 1ns/1ps

module tb_pl_monitor_gap_index;
  reg core_clk=0, gmii_clk=0, resetn=0, clear_stream=0;
  reg monitor_enable=1, jumbo_enable=0, adc_model=1, sample_valid=0;
  reg [31:0] sample_rate_hz=20_000_000, stream_id=21, sample_pair=0;
  reg [7:0] sample_u8=0; reg [1:0] sample_otr=0;
  reg [63:0] sample_index=0;
  reg status_toggle=0; reg [2:0] acquisition_state=3;
  reg [7:0] last_error=0; reg [31:0] measured_rate_hz=20_000_000;
  reg [14:0] active_fifo_level=0; reg [31:0] active_overflow_count=0;
  reg [31:0] event_count=0, dropped_event_count=0;
  reg [31:0] suppressed_event_count=0, transaction_id=0;
  reg event_path_enable=0; reg [63:0] interval_mean_q16=0;
  reg tx_done=0, tx_req=0;
  wire tx_start_en; wire [31:0] tx_data; wire [15:0] tx_byte_num;
  wire [15:0] tx_src_port,tx_dst_port; wire [14:0] monitor_fifo_level;
  wire monitor_fifo_full; wire [31:0] monitor_drop_count,packet_count;
  reg [31:0] packet[0:361];
  integer i;

  always #5 core_clk=~core_clk;
  always #4 gmii_clk=~gmii_clk;

  pl_raw_udp_streamer #(.FIFO_DEPTH(64),.SIM_ASSERT_CHK(0)) dut (.*);

  function automatic [31:0] payload_word(input [15:0] a, input [15:0] b);
    payload_word={a[7:0],a[15:8],b[7:0],b[15:8]};
  endfunction

  task automatic push_dual(
      input integer count, input [63:0] first_index,
      input [15:0] first_a);
    integer k;
    begin
      for(k=0;k<count;k=k+1) begin
        @(negedge core_clk);
        sample_valid=1;
        sample_index=first_index+k;
        sample_pair={16'h8000+k[15:0],first_a+k[15:0]};
      end
      @(negedge core_clk); sample_valid=0;
    end
  endtask

  task automatic collect_packet(input integer words);
    integer k;
    begin
      wait(dut.busy);
      for(k=0;k<words;k=k+1) begin
        @(negedge gmii_clk); tx_req=1;
        @(posedge gmii_clk); #1 packet[k]=tx_data;
      end
      @(negedge gmii_clk); tx_req=0; tx_done=1;
      @(negedge gmii_clk); tx_done=0;
      repeat(5) @(posedge gmii_clk);
    end
  endtask

  task automatic pulse_clear;
    begin
      @(negedge core_clk); clear_stream=1;
      repeat(4) @(negedge core_clk);
      clear_stream=0;
      repeat(100) @(posedge core_clk);
    end
  endtask

  initial begin
    repeat(8) @(posedge core_clk); resetn=1;
    repeat(100) @(posedge core_clk);

    // Hold a status transfer open so the 64-word monitor FIFO must overflow.
    status_toggle=1;
    wait(dut.busy && dut.sending_status);
    push_dual(128,64'd0,16'h0000);
    if(monitor_drop_count==0)
      $fatal(1,"FIFO overflow was not created");
    collect_packet(20);
    wait(monitor_fifo_level==0);
    repeat(10) @(posedge gmii_clk);

    // The accepted prefix is partial.  Index 128 exposes the gap, so that
    // unsent prefix must be discarded and the next DAQD packet starts at 128.
    push_dual(352,64'd128,16'h1000);
    collect_packet(362);
    if(packet[0]!==32'h44415144 || {packet[5],packet[6]}!==64'd128 ||
       packet[7]!==352)
      $fatal(1,"post-overflow packet did not expose exact gap");
    for(i=0;i<352;i=i+1)
      if(packet[10+i]!==payload_word(16'h1000+i,16'h8000+i))
        $fatal(1,"post-gap packet is not internally continuous at %0d",i);

    // A real 64-bit index crossing low-32 wrap must remain continuous.
    pulse_clear(); stream_id=22;
    push_dual(352,64'h0000_0000_ffff_ff80,16'h2000);
    collect_packet(362);
    if({packet[5],packet[6]}!==64'h0000_0000_ffff_ff80)
      $fatal(1,"first wrap packet index mismatch");
    push_dual(352,64'h0000_0001_0000_00e0,16'h3000);
    collect_packet(362);
    if({packet[5],packet[6]}!==64'h0000_0001_0000_00e0)
      $fatal(1,"64-bit low-word wrap was treated as a gap");

    // STOP/START clear discards an old partial packet; a new stream starts
    // from its real first index and packet sequence zero.
    push_dual(100,64'd10_000,16'h4000);
    pulse_clear(); stream_id=23;
    push_dual(352,64'd20_000,16'h5000);
    collect_packet(362);
    if(packet[2]!==23 || packet[3]!==0 ||
       {packet[5],packet[6]}!==64'd20_000)
      $fatal(1,"STOP/START retained an old partial packet");

    $display("PASS: FIFO-full gap position, packet continuity, 64-bit wrap, and STOP/START flush");
    $finish;
  end

  initial begin
    #3_000_000;
    $fatal(1,"tb_pl_monitor_gap_index timeout busy=%b stage=%0d fifo=%0d drops=%0d",
           dut.busy,dut.stage_count,monitor_fifo_level,monitor_drop_count);
  end
endmodule
