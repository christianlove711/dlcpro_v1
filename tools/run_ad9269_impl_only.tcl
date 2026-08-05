set project_dir {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
set report_dir [file join $project_dir reports ad9269_single_dualdma]
set output_dir [file join $project_dir deliverables ad9269_single_dualdma_final]
file mkdir $report_dir
file mkdir $output_dir

open_project [file join $project_dir AXI_DMA.xpr]
set_property PART [get_property PART [current_project]] [get_runs impl_1]
set_property strategy Performance_Explore [get_runs impl_1]
set obsolete [get_files -quiet *dual_adc_impl_clocks.xdc]
if {[llength $obsolete]} {remove_files -fileset constrs_1 $obsolete}

reset_run impl_1
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
set status [get_property STATUS [get_runs impl_1]]
puts "AD9269_IMPL_STATUS=$status"
if {![string match "*Complete*" $status]} {
  close_project
  exit 1
}

open_run impl_1
report_utilization -hierarchical -file [file join $report_dir post_route_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained \
    -check_timing_verbose -file [file join $report_dir post_route_timing_summary.rpt]
report_bus_skew -file [file join $report_dir post_route_bus_skew.rpt]
report_drc -file [file join $report_dir post_route_drc.rpt]
report_methodology -file [file join $report_dir post_route_methodology.rpt]
report_clock_utilization -file [file join $report_dir post_route_clock_utilization.rpt]
report_power -file [file join $report_dir post_route_power.rpt]
write_checkpoint -force [file join $report_dir post_route.dcp]

set setup_path [get_timing_paths -delay_type max -max_paths 1 -nworst 1]
set hold_path [get_timing_paths -delay_type min -max_paths 1 -nworst 1]
set wns [get_property SLACK $setup_path]
set whs [get_property SLACK $hold_path]
set drc_errors [get_drc_violations -quiet -filter {SEVERITY == Error}]
set methodology_critical [get_methodology_violations -quiet \
    -filter {SEVERITY == "Critical Warning"}]
puts "AD9269_WNS=$wns"
puts "AD9269_WHS=$whs"
puts "AD9269_DRC_ERROR_COUNT=[llength $drc_errors]"
puts "AD9269_METHODOLOGY_CRITICAL_COUNT=[llength $methodology_critical]"
if {$wns < 0.0 || $whs < 0.0 || [llength $drc_errors] != 0 ||
    [llength $methodology_critical] != 0} {
  puts "AD9269_DELIVERY_REJECTED=timing_drc_or_methodology"
  close_project
  exit 2
}

write_bitstream -force [file join $output_dir top.bit]
write_hw_platform -fixed -force \
    -file [file join $output_dir ad9269_single_dualdma.xsa]
set hwh [file join $project_dir AXI_DMA.srcs sources_1 bd System hw_handoff System.hwh]
file copy -force $hwh [file join $output_dir System.hwh]
puts "AD9269_DELIVERY_DIR=$output_dir"
close_project
exit 0
