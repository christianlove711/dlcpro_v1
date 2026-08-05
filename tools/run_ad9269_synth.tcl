set project_dir {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
set report_dir [file join $project_dir reports ad9269_single_dualdma]
file mkdir $report_dir

open_project [file join $project_dir AXI_DMA.xpr]
set_property top top [current_fileset]
update_compile_order -fileset sources_1

reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1

set synth_status [get_property STATUS [get_runs synth_1]]
puts "AD9269_SYNTH_STATUS=$synth_status"
if {![string match "*Complete*" $synth_status]} {
    close_project
    exit 1
}

open_run synth_1
report_utilization -hierarchical -file [file join $report_dir post_synth_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose \
    -file [file join $report_dir post_synth_timing_summary.rpt]
report_drc -file [file join $report_dir post_synth_drc.rpt]
write_checkpoint -force [file join $report_dir post_synth.dcp]

puts "AD9269_TOP=[get_property top [current_fileset]]"
puts "AD9269_PART=[get_property PART [current_project]]"
puts "AD9269_REPORT_DIR=$report_dir"
close_project
exit 0
