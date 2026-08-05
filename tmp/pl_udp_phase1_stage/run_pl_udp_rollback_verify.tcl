set root [file dirname [file normalize [info script]]]
set out_dir [file join $root reports pl_udp_pc_v2 rollback_verify]
file mkdir $out_dir

open_project [file join $root AXI_DMA.xpr]

# Restore the production fileset configuration.  The baseline clock source has
# a literal 208.125-degree phase and does not use the phase-sweep macro.
set_property verilog_define {} [get_filesets sources_1]
update_compile_order -fileset sources_1

reset_run synth_1
launch_runs synth_1 -jobs 6
wait_on_run synth_1
set synth_status [get_property STATUS [get_runs synth_1]]
if {[string first "Complete" $synth_status] < 0} {
  error "synth_1 failed: $synth_status"
}

reset_run impl_1
launch_runs impl_1 -to_step write_bitstream -jobs 6
wait_on_run impl_1
set impl_status [get_property STATUS [get_runs impl_1]]
if {[string first "Complete" $impl_status] < 0} {
  error "impl_1 failed: $impl_status"
}

open_run impl_1
report_timing_summary -delay_type min_max -report_unconstrained \
    -check_timing_verbose \
    -file [file join $out_dir post_route_timing_summary.rpt]
report_drc -file [file join $out_dir post_route_drc.rpt]
report_methodology -file [file join $out_dir post_route_methodology.rpt]
report_utilization -hierarchical \
    -file [file join $out_dir post_route_utilization.rpt]
report_power -file [file join $out_dir post_route_power.rpt]

set summary [open [file join $out_dir run_summary.txt] w]
puts $summary "synth_status=$synth_status"
puts $summary "impl_status=$impl_status"
puts $summary "wns=[get_property STATS.WNS [get_runs impl_1]]"
puts $summary "tns=[get_property STATS.TNS [get_runs impl_1]]"
puts $summary "whs=[get_property STATS.WHS [get_runs impl_1]]"
puts $summary "ths=[get_property STATS.THS [get_runs impl_1]]"
close $summary

set impl_dir [get_property DIRECTORY [get_runs impl_1]]
set bit_path [file join $impl_dir top.bit]
if {![file exists $bit_path]} {
  error "Expected rollback verification bitstream not found: $bit_path"
}
file copy -force $bit_path \
    [file join $out_dir top_pl_udp_v2_rollback_verify.bit]

set ltx_candidates [glob -nocomplain -directory $impl_dir *.ltx]
if {[llength $ltx_candidates]} {
  file copy -force [lindex $ltx_candidates 0] \
      [file join $out_dir top_pl_udp_v2_rollback_verify.ltx]
}

close_project
puts "PL_UDP_ROLLBACK_VERIFY_COMPLETE=$out_dir"
exit
