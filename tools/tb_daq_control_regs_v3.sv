`timescale 1ns/1ps
module tb_daq_control_regs_v3;
  reg sample_clk=0,s_axi_aclk=0,s_axi_aresetn=0;
  reg [31:0] sample_pair=0; reg [1:0] otr_pair=0;
  reg hardtrigger=0,fifo_full=0,block_complete=0;
  reg [13:0] fifo_level=14'h123;
  reg spi_busy=0,spi_done=1,spi_error=0;
  wire capture_enable,fifo_reset,trigger_event,channel_swap,spi_reinit_toggle;
  wire [2:0] adc_test_mode,adc_rate_sel; wire adc_divide_by_two;
  wire ps_adc_select,ps_jumbo_enable,ps_monitor_requested;
  wire ps_config_toggle,ps_start_toggle,ps_stop_toggle,ps_clear_toggle;
  wire ps_event_enable;
  wire ps_acq_mode,ps_scope_armed,ps_scope_abort_toggle,ps_scope_clear_toggle;
  wire [3:0] ps_scope_decimation;
  wire [1:0] ps_scope_trigger_mode;
  wire ps_scope_trigger_channel,ps_scope_fps_20;
  wire signed [15:0] ps_scope_trigger_level;
  reg [2:0] manager_state=0,manager_rate_sel=1,manager_test_mode=0;
  reg manager_adc_select=0,manager_channel_swap=0,manager_jumbo_enable=0;
  reg manager_monitor_enable=0;
  reg [31:0] manager_stream_id=32'h11223344,manager_measured_rate_hz=20_000_000;
  reg [31:0] manager_event_count=77,manager_dropped_event_count=3;
  reg [31:0] manager_suppressed_event_count=11;
  reg [7:0] manager_last_error=0;
  reg scope_busy=0,scope_triggered=0,scope_overflow=0;
  reg [31:0] scope_frame_count=0,scope_suppressed_count=0;
  reg [31:0] scope_dropped_count=0;
  reg [7:0] spi_chip_id=8'h75,spi_chip_grade=8'h20;
  reg [7:0] spi_readback_14=8'h21,spi_readback_17=8'h27;
  reg [7:0] spi_readback_0d=8'h00;
  reg [31:0] spi_error_detail=0;
  reg [7:0] s_axi_awaddr=0,s_axi_araddr=0; reg [2:0] s_axi_awprot=0,s_axi_arprot=0;
  reg s_axi_awvalid=0,s_axi_wvalid=0,s_axi_bready=0,s_axi_arvalid=0,s_axi_rready=0;
  reg [31:0] s_axi_wdata=0; reg [3:0] s_axi_wstrb=4'hf;
  wire s_axi_awready,s_axi_wready,s_axi_bvalid,s_axi_arready,s_axi_rvalid;
  wire [1:0] s_axi_bresp,s_axi_rresp; wire [31:0] s_axi_rdata;
  reg [31:0] read_value;
  always #5 sample_clk=~sample_clk;
  always #5 s_axi_aclk=~s_axi_aclk;
  daq_control_regs_v3 dut (.*);

  task automatic axi_write(input [7:0] address,input [31:0] value);
    begin
      @(negedge s_axi_aclk); s_axi_awaddr=address; s_axi_wdata=value;
      s_axi_awvalid=1; s_axi_wvalid=1; s_axi_wstrb=4'hf;
      @(negedge s_axi_aclk); s_axi_awvalid=0; s_axi_wvalid=0;
      wait(s_axi_bvalid); @(negedge s_axi_aclk); s_axi_bready=1;
      @(negedge s_axi_aclk); s_axi_bready=0;
    end
  endtask
  task automatic axi_read(input [7:0] address);
    begin
      @(negedge s_axi_aclk); s_axi_araddr=address; s_axi_arvalid=1;
      @(posedge s_axi_aclk); #1 read_value=s_axi_rdata;
      @(negedge s_axi_aclk); s_axi_arvalid=0; s_axi_rready=1;
      @(negedge s_axi_aclk); s_axi_rready=0;
    end
  endtask

  initial begin
    repeat(5) @(posedge s_axi_aclk); s_axi_aresetn=1;
    repeat(3) @(posedge s_axi_aclk);
    axi_read(8'h00); if(read_value!==32'h44415132) $fatal(1,"ID");
    axi_read(8'h04); if(read_value!==32'h00040100) $fatal(1,"VERSION");
    axi_write(8'h38,32'h00030571);
    if(!ps_adc_select || !ps_jumbo_enable || !channel_swap ||
       adc_rate_sel!=5 || adc_test_mode!=7) $fatal(1,"ADC_CONFIG fields");
    axi_write(8'h08,32'h04); if(!ps_config_toggle) $fatal(1,"CONFIG W1P");
    axi_write(8'h08,32'h01); if(!ps_start_toggle) $fatal(1,"START W1P");
    axi_write(8'h08,32'h10); if(!ps_monitor_requested) $fatal(1,"MONITOR_START");
    axi_write(8'h08,32'h20); if(ps_monitor_requested) $fatal(1,"MONITOR_STOP");
    axi_write(8'h08,32'h08); if(!ps_clear_toggle) $fatal(1,"CLEAR W1P");
    axi_write(8'h08,32'h02); if(!ps_stop_toggle) $fatal(1,"STOP W1P");
    axi_write(8'h68,32'h01); if(!ps_event_enable) $fatal(1,"EVENT_ENABLE arm");
    axi_read(8'h68); if(read_value!==1) $fatal(1,"EVENT_CONTROL readback");
    axi_write(8'h70,32'h01); if(!ps_acq_mode) $fatal(1,"ACQ_MODE");
    axi_write(8'h74,32'h07);
    if(!ps_scope_armed || !ps_scope_abort_toggle || !ps_scope_clear_toggle)
      $fatal(1,"SCOPE_CONTROL");
    axi_write(8'h78,32'h123400f5);
    if(ps_scope_decimation!==5 || ps_scope_trigger_mode!==3 ||
       !ps_scope_trigger_channel || !ps_scope_fps_20 ||
       ps_scope_trigger_level!==16'h1234) $fatal(1,"SCOPE_CONFIG");

    manager_state=3; manager_monitor_enable=1; manager_last_error=8'ha5;
    manager_adc_select=1; manager_rate_sel=3; manager_test_mode=5;
    manager_channel_swap=1; manager_jumbo_enable=1;
    repeat(4) @(posedge s_axi_aclk);
    axi_read(8'h0c); if(read_value!==32'h00a5000b) $fatal(1,"STATUS %08x",read_value);
    axi_read(8'h54); if(read_value!==32'h11223344) $fatal(1,"STREAM_ID");
    axi_read(8'h58); if(read_value!==20_000_000) $fatal(1,"MEASURED_RATE");
    axi_read(8'h5c); if(read_value!==77) $fatal(1,"EVENT_COUNT");
    axi_read(8'h60); if(read_value!==3) $fatal(1,"DROPPED_EVENTS");
    axi_read(8'h64); if(read_value!==32'h000000a5) $fatal(1,"LAST_ERROR");
    axi_read(8'h6c); if(read_value!==11) $fatal(1,"SUPPRESSED_EVENTS");
    scope_busy=1; scope_triggered=1; scope_overflow=1;
    scope_frame_count=9; scope_suppressed_count=10; scope_dropped_count=2;
    spi_readback_0d=8'h05; spi_error_detail=32'h01020304;
    repeat(4) @(posedge s_axi_aclk);
    axi_read(8'h7c); if(read_value!==32'h0000001f) $fatal(1,"SCOPE_STATUS");
    axi_read(8'h80); if(read_value!==9) $fatal(1,"SCOPE_FRAME_COUNT");
    axi_read(8'h84); if(read_value!==32'h00002075) $fatal(1,"SPI_ID_GRADE");
    axi_read(8'h88); if(read_value!==32'h00052721) $fatal(1,"SPI_READBACK");
    axi_read(8'h90); if(read_value!==32'h01020304) $fatal(1,"SPI_ERROR_DETAIL");
    axi_read(8'h94); if(read_value!==32'h00000001) $fatal(1,"EVENT_DMA_STATUS");
    axi_read(8'h98); if(read_value!==10) $fatal(1,"SCOPE_SUPPRESSED");
    axi_read(8'h9c); if(read_value!==2) $fatal(1,"SCOPE_DROPPED");
    axi_write(8'h68,32'h00); if(ps_event_enable) $fatal(1,"EVENT_ENABLE disarm");
    $display("PASS: AXI-Lite control, DMA arm and separated event status map");
    $finish;
  end
  initial begin #10000; $fatal(1,"tb_daq_control_regs_v3 timeout"); end
endmodule
