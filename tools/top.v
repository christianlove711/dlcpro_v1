`timescale 1ns / 1ps

module top (
    inout  wire [14:0] DDR_addr,
    inout  wire [2:0]  DDR_ba,
    inout  wire        DDR_cas_n,
    inout  wire        DDR_ck_n,
    inout  wire        DDR_ck_p,
    inout  wire        DDR_cke,
    inout  wire        DDR_cs_n,
    inout  wire [3:0]  DDR_dm,
    inout  wire [31:0] DDR_dq,
    inout  wire [3:0]  DDR_dqs_n,
    inout  wire [3:0]  DDR_dqs_p,
    inout  wire        DDR_odt,
    inout  wire        DDR_ras_n,
    inout  wire        DDR_reset_n,
    inout  wire        DDR_we_n,
    inout  wire        FIXED_IO_ddr_vrn,
    inout  wire        FIXED_IO_ddr_vrp,
    inout  wire [53:0] FIXED_IO_mio,
    inout  wire        FIXED_IO_ps_clk,
    inout  wire        FIXED_IO_ps_porb,
    inout  wire        FIXED_IO_ps_srstb,

    input  wire        sys_clk,
    input  wire        sys_rst_n,

    input  wire [15:0] ad9269_data,
    input  wire        ad9269_dco,
    input  wire        ad9269_otr,
    output wire        ad9269_clk,
    output wire        ad9269_pdwn,
    output wire        ad9269_oeb,
    output wire        ad9269_csb,
    output wire        ad9269_sclk,
    inout  wire        ad9269_sdio,

    input  wire        eth_rxc,
    input  wire        eth_rx_ctl,
    input  wire [3:0]  eth_rxd,
    output wire        eth_rst_n,
    output wire        eth_txc,
    output wire        eth_tx_ctl,
    output wire [3:0]  eth_txd
);

    localparam [31:0] BOARD_IP = {8'd192, 8'd168, 8'd20, 8'd2};
    localparam [47:0] BOARD_MAC = 48'h00_0A_35_02_1E_01;
    localparam [31:0] HOST_IP = {8'd192, 8'd168, 8'd20, 8'd1};
    localparam [47:0] HOST_MAC = 48'hFF_FF_FF_FF_FF_FF;

    wire clk_100m;
    wire clk_50m;
    wire system_clock_locked;

    pl_system_clock system_clock_inst (
        .clk_50m_in(sys_clk),
        .resetn(sys_rst_n),
        .clk_100m(clk_100m),
        .clk_50m(clk_50m),
        .locked(system_clock_locked)
    );

    // Only the board reset reaches asynchronous clear pins.  The MMCM lock
    // indication is sampled in the 100 MHz domain and controls synchronous
    // reset assertion/release, so it cannot create a LUT-driven reset glitch.
    reg [2:0] core_reset_sync;
    always @(posedge clk_100m or negedge sys_rst_n) begin
        if (!sys_rst_n)
            core_reset_sync <= 3'b000;
        else if (!system_clock_locked)
            core_reset_sync <= 3'b000;
        else
            core_reset_sync <= {core_reset_sync[1:0], 1'b1};
    end
    wire core_resetn = core_reset_sync[2];

    // The PHY reset must not depend on eth_rxc or its MMCM lock: a PHY held in
    // reset cannot generate the receive clock needed to obtain that lock.
    wire phy_reset_done;
    phy_reset_sequencer #(
        .HOLD_CYCLES(1_000_000) // 20 ms at 50 MHz
    ) phy_reset_inst (
        .clk(clk_50m),
        .resetn(sys_rst_n),
        .ready(system_clock_locked),
        .phy_reset_n(phy_reset_done)
    );
    assign eth_rst_n = phy_reset_done;

    wire gmii_clk_125m;
    wire rgmii_clock_locked;
    pl_rgmii_clock rgmii_clock_inst (
        .rgmii_rxc(eth_rxc),
        // RXC is absent while the PHY is held in reset.  The MMCM can safely
        // remain out of lock until RXC appears; its reset pin therefore needs
        // only the direct, glitch-free board reset.
        .resetn(sys_rst_n),
        .gmii_clk_125m(gmii_clk_125m),
        .locked(rgmii_clock_locked)
    );

    // Only the board reset is allowed onto asynchronous reset pins.  MMCM
    // lock/status terms are evaluated synchronously so a LUT cannot glitch an
    // asynchronous clear.  If RXC disappears, the network state is quiescent;
    // when it returns, reset is held until all prerequisites are valid for
    // three consecutive GMII clock edges.
    reg [2:0] net_reset_sync;
    always @(posedge gmii_clk_125m or negedge sys_rst_n) begin
        if (!sys_rst_n)
            net_reset_sync <= 3'b000;
        else if (!core_resetn || !phy_reset_done || !rgmii_clock_locked)
            net_reset_sync <= 3'b000;
        else
            net_reset_sync <= {net_reset_sync[1:0], 1'b1};
    end
    wire net_resetn = net_reset_sync[2];

    wire gmii_rx_clk;
    wire gmii_rx_dv;
    wire [7:0] gmii_rxd;
    wire gmii_tx_clk;
    wire gmii_tx_en;
    wire [7:0] gmii_txd;

    gmii_to_rgmii eth_bridge_inst (
        .gmii_rx_clk(gmii_rx_clk),
        .gmii_rx_dv(gmii_rx_dv),
        .gmii_rxd(gmii_rxd),
        .gmii_tx_clk(gmii_tx_clk),
        .gmii_tx_en(gmii_tx_en),
        .gmii_txd(gmii_txd),
        .rgmii_rxc(gmii_clk_125m),
        .rgmii_rx_ctl(eth_rx_ctl),
        .rgmii_rxd(eth_rxd),
        .rgmii_txc(eth_txc),
        .rgmii_tx_ctl(eth_tx_ctl),
        .rgmii_txd(eth_txd)
    );

    wire udp_rec_pkt_done;
    wire udp_rec_en;
    wire [31:0] udp_rec_data;
    wire [15:0] udp_rec_byte_num;
    wire udp_tx_start;
    wire [31:0] udp_tx_data;
    wire [15:0] udp_tx_byte_num;
    wire [15:0] udp_tx_src_port;
    wire [15:0] udp_tx_dst_port;
    wire udp_tx_done;
    wire udp_tx_req;

    udp #(
        .BOARD_MAC(BOARD_MAC),
        .BOARD_IP(BOARD_IP),
        .DES_MAC(HOST_MAC),
        .DES_IP(HOST_IP)
    ) udp_stack_inst (
        .rst_n(net_resetn),
        .gmii_rx_clk(gmii_rx_clk),
        .gmii_rx_dv(gmii_rx_dv),
        .gmii_rxd(gmii_rxd),
        .gmii_tx_clk(gmii_tx_clk),
        .gmii_tx_en(gmii_tx_en),
        .gmii_txd(gmii_txd),
        .rec_pkt_done(udp_rec_pkt_done),
        .rec_en(udp_rec_en),
        .rec_data(udp_rec_data),
        .rec_byte_num(udp_rec_byte_num),
        .tx_start_en(udp_tx_start),
        .tx_data(udp_tx_data),
        .tx_byte_num(udp_tx_byte_num),
        .tx_src_port(udp_tx_src_port),
        .tx_dst_port(udp_tx_dst_port),
        .tx_done(udp_tx_done),
        .tx_req(udp_tx_req)
    );

    wire requested_adc_select;
    wire [2:0] requested_rate_sel;
    wire [2:0] requested_test_mode;
    wire requested_channel_swap;
    wire requested_jumbo;
    wire requested_capture;
    wire requested_monitor;
    wire config_toggle;
    wire start_toggle;
    wire stop_toggle;
    wire clear_toggle;
    wire status_toggle;
    wire [31:0] transaction_id;
    wire [31:0] command_count;
    wire [31:0] bad_command_count;

    pl_daq_control control_parser_inst (
        .clk(gmii_rx_clk),
        .resetn(net_resetn),
        .rec_en(udp_rec_en),
        .rec_data(udp_rec_data),
        .rec_pkt_done(udp_rec_pkt_done),
        .rec_byte_num(udp_rec_byte_num),
        .adc_select(requested_adc_select),
        .rate_sel(requested_rate_sel),
        .adc_test_mode(requested_test_mode),
        .channel_swap(requested_channel_swap),
        .jumbo_enable(requested_jumbo),
        .capture_requested(requested_capture),
        .monitor_requested(requested_monitor),
        .config_toggle(config_toggle),
        .start_toggle(start_toggle),
        .stop_toggle(stop_toggle),
        .clear_toggle(clear_toggle),
        .status_toggle(status_toggle),
        .transaction_id(transaction_id),
        .command_count(command_count),
        .bad_command_count(bad_command_count)
    );

    wire ctrl_adc_select;
    wire [2:0] ctrl_rate_sel;
    wire [2:0] ctrl_test_mode;
    wire ctrl_channel_swap;
    wire ctrl_jumbo;
    wire ctrl_capture;
    wire ctrl_monitor;
    wire config_pulse;
    wire start_pulse;
    wire stop_pulse;
    wire clear_pulse;

    pl_daq_control_cdc control_cdc_inst (
        .clk(clk_100m),
        .resetn(core_resetn),
        .async_adc_select(requested_adc_select),
        .async_rate_sel(requested_rate_sel),
        .async_test_mode(requested_test_mode),
        .async_channel_swap(requested_channel_swap),
        .async_jumbo_enable(requested_jumbo),
        .async_capture_requested(requested_capture),
        .async_monitor_requested(requested_monitor),
        .async_config_toggle(config_toggle),
        .async_start_toggle(start_toggle),
        .async_stop_toggle(stop_toggle),
        .async_clear_toggle(clear_toggle),
        .adc_select(ctrl_adc_select),
        .rate_sel(ctrl_rate_sel),
        .test_mode(ctrl_test_mode),
        .channel_swap(ctrl_channel_swap),
        .jumbo_enable(ctrl_jumbo),
        .capture_requested(ctrl_capture),
        .monitor_requested(ctrl_monitor),
        .config_pulse(config_pulse),
        .start_pulse(start_pulse),
        .stop_pulse(stop_pulse),
        .clear_pulse(clear_pulse)
    );

    wire ps_adc_select_async;
    wire ps_jumbo_async;
    wire ps_monitor_async;
    wire ps_config_toggle_async;
    wire ps_start_toggle_async;
    wire ps_stop_toggle_async;
    wire ps_clear_toggle_async;
    wire ps_event_enable_async;
    wire ps_acq_mode_async;
    wire ps_scope_armed_async;
    wire ps_scope_abort_toggle_async;
    wire ps_scope_clear_toggle_async;
    wire [3:0] ps_scope_decimation_async;
    wire [1:0] ps_scope_trigger_mode_async;
    wire ps_scope_trigger_channel_async;
    wire signed [15:0] ps_scope_trigger_level_async;
    wire ps_scope_fps_20_async;
    wire ps_adc_select_core;
    wire [2:0] ps_rate_sel_core;
    wire [2:0] ps_test_mode_core;
    wire ps_channel_swap_core;
    wire [2:0] ps_rate_sel;
    wire [2:0] ps_test_mode;
    wire ps_channel_swap;
    wire ps_jumbo_core;
    wire ps_monitor_core;
    wire ps_config_pulse_core;
    wire ps_start_pulse_core;
    wire ps_stop_pulse_core;
    wire ps_clear_pulse_core;
    (* ASYNC_REG = "TRUE" *) reg [1:0] ps_event_enable_sync = 2'b00;
    wire ps_event_enable_core = ps_event_enable_sync[1];

    always @(posedge clk_100m or negedge core_resetn) begin
        if (!core_resetn)
            ps_event_enable_sync <= 2'b00;
        else
            ps_event_enable_sync <= {ps_event_enable_sync[0],
                                     ps_event_enable_async};
    end

    pl_daq_control_cdc ps_control_cdc_inst (
        .clk(clk_100m), .resetn(core_resetn),
        .async_adc_select(ps_adc_select_async),
        .async_rate_sel(ps_rate_sel),
        .async_test_mode(ps_test_mode),
        .async_channel_swap(ps_channel_swap),
        .async_jumbo_enable(ps_jumbo_async),
        .async_capture_requested(1'b0),
        .async_monitor_requested(ps_monitor_async),
        .async_config_toggle(ps_config_toggle_async),
        .async_start_toggle(ps_start_toggle_async),
        .async_stop_toggle(ps_stop_toggle_async),
        .async_clear_toggle(ps_clear_toggle_async),
        .adc_select(ps_adc_select_core), .rate_sel(ps_rate_sel_core),
        .test_mode(ps_test_mode_core), .channel_swap(ps_channel_swap_core),
        .jumbo_enable(ps_jumbo_core), .capture_requested(),
        .monitor_requested(ps_monitor_core),
        .config_pulse(ps_config_pulse_core), .start_pulse(ps_start_pulse_core),
        .stop_pulse(ps_stop_pulse_core), .clear_pulse(ps_clear_pulse_core)
    );

    wire active_adc_select;
    wire [2:0] active_rate_sel;
    wire [2:0] active_test_mode;
    wire active_channel_swap;
    wire active_jumbo;
    wire adc_clock_enable;
    wire capture_enable;
    wire monitor_enable;
    wire feature_enable;
    wire clear_fifos;
    wire clear_stats;
    wire [31:0] stream_id;
    wire [2:0] acquisition_state;
    wire [7:0] last_error;
    wire active_acq_mode;
    wire active_fifo_full;
    wire [31:0] active_overflow_count;
    wire selected_adc_clk;
    wire adc_clock_locked;
    wire [31:0] configured_rate_hz;
    wire spi_done;
    wire spi_error;

    daq_acq_manager acquisition_manager_inst (
        .clk(clk_100m),
        .resetn(core_resetn),
        .udp_adc_select(ctrl_adc_select), .udp_rate_sel(ctrl_rate_sel),
        .udp_test_mode(ctrl_test_mode), .udp_channel_swap(ctrl_channel_swap),
        .udp_jumbo(ctrl_jumbo), .udp_monitor(ctrl_monitor),
        .udp_config_pulse(config_pulse), .udp_start_pulse(start_pulse),
        .udp_stop_pulse(stop_pulse), .udp_clear_pulse(clear_pulse),
        .ps_adc_select(ps_adc_select_core), .ps_rate_sel(ps_rate_sel_core),
        .ps_test_mode(ps_test_mode_core), .ps_channel_swap(ps_channel_swap_core),
        .ps_jumbo(ps_jumbo_core), .ps_monitor(ps_monitor_core),
        .ps_config_pulse(ps_config_pulse_core), .ps_start_pulse(ps_start_pulse_core),
        .ps_stop_pulse(ps_stop_pulse_core), .ps_clear_pulse(ps_clear_pulse_core),
        .ps_acq_mode(ps_acq_mode_async),
        .clock_locked(adc_clock_locked),
        .spi_done(spi_done),
        .spi_error(spi_error),
        .active_fifo_full(active_fifo_full),
        .active_overflow_count(active_overflow_count),
        .adc_select(active_adc_select),
        .rate_sel(active_rate_sel),
        .test_mode(active_test_mode),
        .channel_swap(active_channel_swap),
        .jumbo_enable(active_jumbo),
        .clock_enable(adc_clock_enable),
        .capture_enable(capture_enable),
        .monitor_enable(monitor_enable),
        .feature_enable(feature_enable),
        .clear_fifos(clear_fifos),
        .clear_stats(clear_stats),
        .stream_id(stream_id),
        .state(acquisition_state),
        .last_error(last_error),
        .acq_mode(active_acq_mode)
    );

    adc_rate_clock_gen adc_clock_generator_inst (
        .clk_100m(clk_100m),
        .resetn(core_resetn),
        .clock_enable(adc_clock_enable),
        .rate_sel(active_rate_sel),
        .sample_clk(selected_adc_clk),
        .ad9269_clk_pin(ad9269_clk),
        .locked(adc_clock_locked),
        .configured_rate_hz(configured_rate_hz)
    );

    wire ad9269_sample_clk;
    wire [31:0] ad9269_sample_pair;
    wire [1:0] ad9269_otr_pair;
    ad9269_input_frontend adc_frontend (
        .adc_dco_pin(ad9269_dco),
        .adc_data_pins(ad9269_data),
        .adc_otr_pin(ad9269_otr),
        .channel_swap(active_channel_swap),
        .sample_clk(ad9269_sample_clk),
        .sample_pair(ad9269_sample_pair),
        .otr_pair(ad9269_otr_pair),
        .debug_dco_ibuf(),
        .debug_data_rise()
    );

    reg local_spi_reinit_toggle;
    wire ps_spi_reinit_toggle;
    always @(posedge clk_100m or negedge core_resetn) begin
        if (!core_resetn)
            local_spi_reinit_toggle <= 1'b0;
        else if (config_pulse || ps_config_pulse_core)
            local_spi_reinit_toggle <= ~local_spi_reinit_toggle;
    end

    wire spi_sdio_o;
    wire spi_sdio_oe;
    wire spi_sdio_i;
    wire spi_busy;
    wire [7:0] spi_chip_id;
    wire [7:0] spi_chip_grade;
    wire [7:0] spi_readback_14;
    wire [7:0] spi_readback_17;
    wire [7:0] spi_readback_0d;
    wire [31:0] spi_error_detail;
    ad9269_spi_init adc_spi_init_inst (
        .clk(clk_50m),
        .resetn(core_resetn),
        .reinit_toggle(local_spi_reinit_toggle ^ ps_spi_reinit_toggle),
        .test_mode(active_test_mode),
        .sdio_i(spi_sdio_i),
        .acquisition_stopped(acquisition_state == 3'd0 ||
                             acquisition_state == 3'd1),
        .csb(ad9269_csb),
        .sclk(ad9269_sclk),
        .sdio_o(spi_sdio_o),
        .sdio_oe(spi_sdio_oe),
        .busy(spi_busy),
        .done(spi_done),
        .error(spi_error),
        .chip_id(spi_chip_id), .chip_grade(spi_chip_grade),
        .readback_14(spi_readback_14), .readback_17(spi_readback_17),
        .readback_0d(spi_readback_0d), .error_detail(spi_error_detail)
    );
    IOBUF ad9269_sdio_iobuf (
        .I(spi_sdio_o), .O(spi_sdio_i), .T(!spi_sdio_oe), .IO(ad9269_sdio)
    );
    assign ad9269_pdwn = 1'b0;
    assign ad9269_oeb = 1'b0;

    wire ingress_valid;
    wire [31:0] ingress_pair;
    wire [1:0] ingress_otr;
    wire [63:0] ingress_index;
    wire [14:0] ad9269_fifo_level;
    wire ad9269_fifo_full;
    wire [31:0] ad9269_overflow_count;

    assign active_fifo_full = ad9269_fifo_full;
    assign active_overflow_count = ad9269_overflow_count;
    wire [14:0] active_fifo_level = ad9269_fifo_level;

    ad9269_ingress ingress_inst (
        .clk_100m(clk_100m),
        .resetn(core_resetn),
        .clear_fifo(clear_fifos),
        .capture_enable(capture_enable),
        .sample_clk(ad9269_sample_clk),
        .sample_pair_in(ad9269_sample_pair),
        .sample_otr_in(ad9269_otr_pair),
        .sample_ready(1'b1),
        .sample_valid(ingress_valid),
        .sample_pair(ingress_pair),
        .sample_otr(ingress_otr),
        .sample_index(ingress_index),
        .fifo_level(ad9269_fifo_level),
        .fifo_full(ad9269_fifo_full),
        .overflow_count(ad9269_overflow_count)
    );

    wire event_valid;
    wire [31:0] event_data;
    wire event_ready;
    wire event_last;
    wire event_busy;
    wire [31:0] event_count;
    wire [31:0] dropped_event_count;
    wire [31:0] suppressed_event_count;
    wire [63:0] last_event_index;
    wire [63:0] interval_mean_q16;
    wire [63:0] interval_variance_q16;

    peak_feature_engine feature_engine_inst (
        .clk(clk_100m),
        .resetn(core_resetn),
        .clear_stats(clear_stats),
        .enable(feature_enable),
        .event_path_enable(ps_event_enable_core),
        .adc_model(1'b1),
        .sample_rate_hz(configured_rate_hz),
        .sample_valid(ingress_valid),
        .sample_pair(ingress_pair),
        .sample_otr(ingress_otr),
        .sample_index(ingress_index),
        .peak_polarity(2'd0),
        .min_threshold(16'd512),
        .noise_multiplier(8'd6),
        .hysteresis_shift(8'd2),
        .min_peak_width(16'd3),
        .max_peak_width(16'hffff),
        .dead_samples(32'd1000),
        .sample_ready(),
        .event_data(event_data),
        .event_valid(event_valid),
        .event_ready(event_ready),
        .event_last(event_last),
        .event_busy(event_busy),
        .event_count(event_count),
        .dropped_event_count(dropped_event_count),
        .suppressed_event_count(suppressed_event_count),
        .last_event_index(last_event_index),
        .interval_mean_q16(interval_mean_q16),
        .interval_variance_q16(interval_variance_q16)
    );

    (* ASYNC_REG = "TRUE" *) reg [1:0] scope_armed_sync = 2'b00;
    (* ASYNC_REG = "TRUE" *) reg [3:0] scope_decim_s1 = 4'd0;
    (* ASYNC_REG = "TRUE" *) reg [3:0] scope_decim_s2 = 4'd0;
    (* ASYNC_REG = "TRUE" *) reg [1:0] scope_trig_mode_s1 = 2'd0;
    (* ASYNC_REG = "TRUE" *) reg [1:0] scope_trig_mode_s2 = 2'd0;
    (* ASYNC_REG = "TRUE" *) reg scope_trig_ch_s1 = 1'b0;
    (* ASYNC_REG = "TRUE" *) reg scope_trig_ch_s2 = 1'b0;
    (* ASYNC_REG = "TRUE" *) reg signed [15:0] scope_level_s1 = 16'sd0;
    (* ASYNC_REG = "TRUE" *) reg signed [15:0] scope_level_s2 = 16'sd0;
    (* ASYNC_REG = "TRUE" *) reg [1:0] scope_fps_sync = 2'b00;
    (* ASYNC_REG = "TRUE" *) reg [1:0] scope_abort_sync = 2'b00;
    (* ASYNC_REG = "TRUE" *) reg [1:0] scope_clear_sync = 2'b00;
    reg scope_abort_seen = 1'b0;
    reg scope_clear_seen = 1'b0;
    wire scope_abort_pulse = scope_abort_sync[1] ^ scope_abort_seen;
    wire scope_clear_pulse = scope_clear_sync[1] ^ scope_clear_seen;
    always @(posedge clk_100m or negedge core_resetn) begin
      if (!core_resetn) begin
        scope_armed_sync <= 0; scope_decim_s1 <= 0; scope_decim_s2 <= 0;
        scope_trig_mode_s1 <= 0; scope_trig_mode_s2 <= 0;
        scope_trig_ch_s1 <= 0; scope_trig_ch_s2 <= 0;
        scope_level_s1 <= 0; scope_level_s2 <= 0; scope_fps_sync <= 0;
        scope_abort_sync <= 0; scope_clear_sync <= 0;
        scope_abort_seen <= 0; scope_clear_seen <= 0;
      end else begin
        scope_armed_sync <= {scope_armed_sync[0],ps_scope_armed_async};
        scope_decim_s1 <= ps_scope_decimation_async;
        scope_decim_s2 <= scope_decim_s1;
        scope_trig_mode_s1 <= ps_scope_trigger_mode_async;
        scope_trig_mode_s2 <= scope_trig_mode_s1;
        scope_trig_ch_s1 <= ps_scope_trigger_channel_async;
        scope_trig_ch_s2 <= scope_trig_ch_s1;
        scope_level_s1 <= ps_scope_trigger_level_async;
        scope_level_s2 <= scope_level_s1;
        scope_fps_sync <= {scope_fps_sync[0],ps_scope_fps_20_async};
        scope_abort_sync <= {scope_abort_sync[0],ps_scope_abort_toggle_async};
        scope_clear_sync <= {scope_clear_sync[0],ps_scope_clear_toggle_async};
        scope_abort_seen <= scope_abort_sync[1];
        scope_clear_seen <= scope_clear_sync[1];
      end
    end

    wire [31:0] scope_data;
    wire scope_valid;
    wire scope_ready;
    wire scope_last;
    wire scope_busy;
    wire scope_triggered;
    wire scope_overflow;
    wire [31:0] scope_frame_count;
    wire [31:0] scope_suppressed_count;
    wire [31:0] scope_dropped_count;
    ad9269_scope_capture scope_capture_inst (
      .clk(clk_100m), .resetn(core_resetn),
      .clear(clear_stats || scope_clear_pulse),
      .mode_scope(!active_acq_mode && acquisition_state == 3'd3),
      .armed(scope_armed_sync[1]), .abort(scope_abort_pulse),
      .decimation_log2(scope_decim_s2),
      .trigger_mode(scope_trig_mode_s2),
      .trigger_channel(scope_trig_ch_s2),
      .trigger_level(scope_level_s2), .fps_20(scope_fps_sync[1]),
      .stream_id(stream_id), .sample_rate_hz(configured_rate_hz),
      .sample_valid(ingress_valid), .sample_pair(ingress_pair),
      .sample_otr(ingress_otr), .sample_index(ingress_index),
      .scope_data(scope_data), .scope_valid(scope_valid),
      .scope_ready(scope_ready), .scope_last(scope_last),
      .busy(scope_busy), .triggered(scope_triggered),
      .overflow(scope_overflow), .frame_count(scope_frame_count),
      .suppressed_count(scope_suppressed_count),
      .dropped_count(scope_dropped_count)
    );

    wire [31:0] ad9269_measured_hz;
    wire ad9269_clock_active;
    adc_activity_meter ad9269_meter_inst (
        .ref_clk(clk_100m), .resetn(core_resetn), .sample_clk(ad9269_sample_clk),
        .measured_hz(ad9269_measured_hz), .active(ad9269_clock_active)
    );
    wire [31:0] active_measured_hz = ad9269_measured_hz;

    wire status_toggle_core;
    reg [1:0] status_toggle_sync;
    always @(posedge clk_100m or negedge core_resetn) begin
        if (!core_resetn)
            status_toggle_sync <= 2'b00;
        else
            status_toggle_sync <= {status_toggle_sync[0], status_toggle};
    end
    assign status_toggle_core = status_toggle_sync[1];

    wire [14:0] monitor_fifo_level;
    wire monitor_fifo_full;
    wire [31:0] monitor_drop_count;
    wire [31:0] monitor_packet_count;
    pl_raw_udp_streamer raw_streamer_inst (
        .core_clk(clk_100m),
        .gmii_clk(gmii_tx_clk),
        .resetn(net_resetn),
        .clear_stream(clear_stats),
        .monitor_enable(monitor_enable),
        .jumbo_enable(active_jumbo),
        .adc_model(1'b1),
        .sample_rate_hz(configured_rate_hz),
        .stream_id(stream_id),
        .sample_valid(ingress_valid),
        .sample_pair(ingress_pair),
        .sample_u8(8'd0),
        .sample_otr(ingress_otr),
        .status_toggle(status_toggle_core),
        .acquisition_state(acquisition_state),
        .last_error(last_error),
        .measured_rate_hz(active_measured_hz),
        .active_fifo_level(active_fifo_level),
        .active_overflow_count(active_overflow_count),
        .event_count(event_count),
        .dropped_event_count(dropped_event_count),
        .suppressed_event_count(suppressed_event_count),
        .event_path_enable(ps_event_enable_core),
        .interval_mean_q16(interval_mean_q16),
        .transaction_id(transaction_id),
        .tx_start_en(udp_tx_start),
        .tx_data(udp_tx_data),
        .tx_byte_num(udp_tx_byte_num),
        .tx_src_port(udp_tx_src_port),
        .tx_dst_port(udp_tx_dst_port),
        .tx_done(udp_tx_done),
        .tx_req(udp_tx_req),
        .monitor_fifo_level(monitor_fifo_level),
        .monitor_fifo_full(monitor_fifo_full),
        .monitor_drop_count(monitor_drop_count),
        .packet_count(monitor_packet_count)
    );

    System_wrapper zynq_u (
        .DDR_addr(DDR_addr), .DDR_ba(DDR_ba), .DDR_cas_n(DDR_cas_n),
        .DDR_ck_n(DDR_ck_n), .DDR_ck_p(DDR_ck_p), .DDR_cke(DDR_cke),
        .DDR_cs_n(DDR_cs_n), .DDR_dm(DDR_dm), .DDR_dq(DDR_dq),
        .DDR_dqs_n(DDR_dqs_n), .DDR_dqs_p(DDR_dqs_p), .DDR_odt(DDR_odt),
        .DDR_ras_n(DDR_ras_n), .DDR_reset_n(DDR_reset_n), .DDR_we_n(DDR_we_n),
        .FIXED_IO_ddr_vrn(FIXED_IO_ddr_vrn), .FIXED_IO_ddr_vrp(FIXED_IO_ddr_vrp),
        .FIXED_IO_mio(FIXED_IO_mio), .FIXED_IO_ps_clk(FIXED_IO_ps_clk),
        .FIXED_IO_ps_porb(FIXED_IO_ps_porb), .FIXED_IO_ps_srstb(FIXED_IO_ps_srstb),
        .adc_rate_sel_0(ps_rate_sel),
        .adc_test_mode_0(ps_test_mode), .channel_swap_0(ps_channel_swap),
        .ps_adc_select_0(ps_adc_select_async),
        .ps_jumbo_enable_0(ps_jumbo_async),
        .ps_monitor_requested_0(ps_monitor_async),
        .ps_config_toggle_0(ps_config_toggle_async),
        .ps_start_toggle_0(ps_start_toggle_async),
        .ps_stop_toggle_0(ps_stop_toggle_async),
        .ps_clear_toggle_0(ps_clear_toggle_async),
        .ps_event_enable_0(ps_event_enable_async),
        .ps_acq_mode_0(ps_acq_mode_async),
        .ps_scope_armed_0(ps_scope_armed_async),
        .ps_scope_abort_toggle_0(ps_scope_abort_toggle_async),
        .ps_scope_clear_toggle_0(ps_scope_clear_toggle_async),
        .ps_scope_decimation_0(ps_scope_decimation_async),
        .ps_scope_trigger_mode_0(ps_scope_trigger_mode_async),
        .ps_scope_trigger_channel_0(ps_scope_trigger_channel_async),
        .ps_scope_trigger_level_0(ps_scope_trigger_level_async),
        .ps_scope_fps_20_0(ps_scope_fps_20_async),
        .manager_state_0(acquisition_state),
        .manager_adc_select_0(active_adc_select),
        .manager_rate_sel_0(active_rate_sel),
        .manager_test_mode_0(active_test_mode),
        .manager_channel_swap_0(active_channel_swap),
        .manager_jumbo_enable_0(active_jumbo),
        .manager_monitor_enable_0(monitor_enable),
        .manager_stream_id_0(stream_id),
        .manager_last_error_0(last_error),
        .manager_measured_rate_hz_0(active_measured_hz),
        .manager_event_count_0(event_count),
        .manager_dropped_event_count_0(dropped_event_count),
        .manager_suppressed_event_count_0(suppressed_event_count),
        .event_data_0(event_data), .event_valid_0(event_valid),
        .event_ready_0(event_ready), .event_reset_0(clear_fifos),
        .scope_axis_0_tdata(scope_data), .scope_axis_0_tvalid(scope_valid),
        .scope_axis_0_tready(scope_ready), .scope_axis_0_tlast(scope_last),
        .scope_axis_0_tkeep(4'hf),
        .scope_resetn_0(core_resetn),
        .scope_busy_0(scope_busy), .scope_triggered_0(scope_triggered),
        .scope_overflow_0(scope_overflow),
        .scope_frame_count_0(scope_frame_count),
        .scope_suppressed_count_0(scope_suppressed_count),
        .scope_dropped_count_0(scope_dropped_count),
        .otr_pair_0(ingress_otr),
        .sample_clk(clk_100m), .sample_pair_1(ingress_pair),
        .spi_busy_0(spi_busy), .spi_done_0(spi_done),
        .spi_error_0(spi_error), .spi_reinit_toggle_0(ps_spi_reinit_toggle),
        .spi_chip_id_0(spi_chip_id), .spi_chip_grade_0(spi_chip_grade),
        .spi_readback_14_0(spi_readback_14),
        .spi_readback_17_0(spi_readback_17),
        .spi_readback_0d_0(spi_readback_0d),
        .spi_error_detail_0(spi_error_detail)
    );

endmodule
