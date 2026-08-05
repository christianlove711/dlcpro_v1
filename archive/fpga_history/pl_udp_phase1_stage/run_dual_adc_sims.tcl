set root [file dirname [file normalize [info script]]]
open_project [file join $root AXI_DMA.xpr]
# Remove stale simulation-only references left by earlier diagnostics.  Missing
# sources otherwise produce confusing warnings in later synthesis runs.
foreach stale_file [get_files -quiet *tb_rgmii_rx_bytes.sv] {
  if {![file exists $stale_file]} {
    remove_files $stale_file
  }
}
set summary_path [file join $root reports_dual_adc_simulation.txt]
set summary [open $summary_path w]
puts $summary "Dual ADC RTL self-check summary"
puts $summary "Generated: [clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]"
set phy_reset_rtl [file join $root AXI_DMA.srcs sources_1 new phy_reset_sequencer.v]
if {![llength [get_files -quiet $phy_reset_rtl]]} {
  add_files -fileset sources_1 -norecurse $phy_reset_rtl
}
foreach sim_file [list \
    [file join $root AXI_DMA.srcs sim_1 new tb_phy_reset_sequencer.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_pl_daq_control.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_pl_daq_control_cdc.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_peak_feature_engine.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_iterative_math.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_daq_acq_manager.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_daq_control_regs_v3.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_udp_rx.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_udp_tx_sync_reset.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_udp_control_integration.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_rgmii_ddr_mapping.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_pl_raw_udp_streamer.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_ad9280_frontend.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_ad9280_udp_end_to_end.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_dual_adc_ingress.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_peak_scenarios.sv]] {
  if {[file exists $sim_file] && ![llength [get_files -quiet $sim_file]]} {
    add_files -fileset sim_1 -norecurse $sim_file
  }
}
set tests {tb_phy_reset_sequencer tb_ad9269_spi tb_ad9269_frontend_t9 tb_native_fifo_to_axis_fwft tb_adc_fifo_axis tb_pl_daq_control tb_pl_daq_control_cdc tb_iterative_math tb_peak_feature_engine tb_peak_scenarios tb_daq_acq_manager tb_daq_control_regs_v3 tb_udp_rx tb_udp_tx_sync_reset tb_udp_control_integration tb_rgmii_ddr_mapping tb_pl_raw_udp_streamer}
if {[info exists ::env(DAQ_ONLY_TEST)] && $::env(DAQ_ONLY_TEST) ne ""} {
  set tests [list $::env(DAQ_ONLY_TEST)]
}
if {$argc > 0} {
  set tests [list [lindex $argv 0]]
}
foreach test $tests {
  set_property top $test [get_filesets sim_1]
  # Let launch_simulation run until the self-checking testbench calls $finish.
  # Issuing another `run all` after a test that finished inside the default
  # launch runtime can hang XSim 2020.2.
  set_property xsim.simulate.runtime all [get_filesets sim_1]
  launch_simulation -mode behavioral
  close_sim
  set log_path [file join $root AXI_DMA.sim sim_1 behav xsim simulate.log]
  set log_handle [open $log_path r]
  set log_text [read $log_handle]
  close $log_handle
  if {[string first "Fatal:" $log_text] >= 0 ||
      [string first "PASS:" $log_text] < 0} {
    puts $summary "FAIL $test"
    close $summary
    error "Simulation failed or did not report PASS: $test (see $log_path)"
  }
  puts $summary "PASS $test"
  puts "VERIFIED PASS: $test"
}
close $summary
close_project
