set project_dir {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
set report_dir [file join $project_dir reports ad9269_single_dualdma simulations]
set external_dir {C:/Users/chris/dlcpro_v1/tools}
set sim_dir [file join $project_dir AXI_DMA.srcs sim_1 new]
file mkdir $report_dir

open_project [file join $project_dir AXI_DMA.xpr]
foreach path [list \
    [file join $external_dir tb_ad9269_scope_capture.sv] \
    [file join $external_dir tb_adc_rate_clock_gen.sv]] {
  if {![llength [get_files -quiet $path]]} {
    add_files -fileset sim_1 -norecurse $path
  }
}
foreach path [list \
    [file join $sim_dir tb_native_fifo_to_axis_fwft.sv] \
    [file join $sim_dir tb_ad9269_spi.sv] \
    [file join $sim_dir tb_ad9269_frontend_t9.sv]] {
  if {![llength [get_files -quiet $path]]} {
    add_files -fileset sim_1 -norecurse $path
  }
}
update_compile_order -fileset sim_1

set failures {}
foreach sim_top {
  tb_adc_rate_clock_gen
  tb_ad9269_scope_capture
  tb_native_fifo_to_axis_fwft
  tb_ad9269_spi
  tb_ad9269_frontend_t9
  tb_iterative_math
  tb_peak_feature_engine
  tb_peak_scenarios
  tb_daq_acq_manager
  tb_pl_daq_control
  tb_pl_daq_control_cdc
  tb_udp_control_integration
  tb_daq_control_regs_v3
} {
  puts "AD9269_SIM_START=$sim_top"
  set_property top $sim_top [get_filesets sim_1]
  set_property xsim.simulate.runtime all [get_filesets sim_1]
  if {[catch {
    launch_simulation -simset sim_1 -mode behavioral
  } detail]} {
    lappend failures "$sim_top launch: $detail"
    catch {close_sim}
    continue
  }
  close_sim
  set log_path [file join $project_dir AXI_DMA.sim sim_1 behav xsim simulate.log]
  set log_handle [open $log_path r]
  set log_text [read $log_handle]
  close $log_handle
  set dst [file join $report_dir "${sim_top}.log"]
  file copy -force $log_path $dst
  if {[string first "Fatal:" $log_text] >= 0 ||
      [string first "PASS:" $log_text] < 0} {
    lappend failures "$sim_top missing PASS or reported Fatal"
  } else {
    puts "AD9269_SIM_PASS=$sim_top"
  }
}

set summary [open [file join $report_dir summary.txt] w]
if {[llength $failures]} {
  puts $summary "FAIL"
  foreach failure $failures {puts $summary $failure}
  close $summary
  close_project
  exit 1
}
puts $summary "PASS"
puts $summary "All AD9269 final simulations passed."
close $summary
close_project
exit 0
