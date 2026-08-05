set root {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
set out_dir [file join $root reports pl_udp_pc_v2 phase2]
file mkdir $out_dir
open_project [file join $root AXI_DMA.xpr]
foreach sim_file [list \
    [file join $root AXI_DMA.srcs sim_1 new tb_pl_monitor_packetizer.sv] \
    [file join $root AXI_DMA.srcs sim_1 new tb_pl_monitor_gap_index.sv]] {
  if {![llength [get_files -quiet $sim_file]]} {
    add_files -fileset sim_1 -norecurse $sim_file
  }
}
update_compile_order -fileset sim_1
set tests {
  tb_phy_reset_sequencer tb_ad9269_spi tb_ad9269_frontend_t9
  tb_native_fifo_to_axis_fwft tb_adc_fifo_axis tb_pl_daq_control
  tb_pl_daq_control_cdc tb_iterative_math tb_peak_feature_engine
  tb_peak_scenarios tb_daq_acq_manager tb_daq_control_regs_v3
  tb_udp_rx tb_udp_tx_sync_reset tb_udp_control_integration
  tb_rgmii_ddr_mapping tb_pl_raw_udp_streamer
  tb_pl_monitor_packetizer tb_pl_monitor_gap_index
}
set summary [open [file join $out_dir rtl_simulation_summary.txt] w]
puts $summary "Phase 2 RTL self-check summary"
puts $summary "Generated: [clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]"
foreach test $tests {
  set_property top $test [get_filesets sim_1]
  set_property xsim.simulate.runtime all [get_filesets sim_1]
  launch_simulation -mode behavioral
  close_sim
  set log_path [file join $root AXI_DMA.sim sim_1 behav xsim simulate.log]
  set handle [open $log_path r]
  set text [read $handle]
  close $handle
  if {[string first "Fatal:" $text] >= 0 ||
      [string first "PASS:" $text] < 0} {
    puts $summary "FAIL $test"
    close $summary
    error "Simulation failed or did not report PASS: $test"
  }
  puts $summary "PASS $test"
  puts "VERIFIED PASS: $test"
}
close $summary
close_project
puts "PL_UDP_PHASE2_SIMS_COMPLETE=$out_dir"
exit
