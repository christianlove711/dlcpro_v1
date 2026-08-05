set project_dir {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
set report_dir [file join $project_dir reports ad9269_single_dualdma]
set output_dir [file join $project_dir deliverables ad9269_single_dualdma_final]
file mkdir $report_dir
file mkdir $output_dir

open_project [file join $project_dir AXI_DMA.xpr]
set_property top top [current_fileset]
update_compile_order -fileset sources_1

# Vivado 2020.2 can leave a stale OOC XCI for an RTL Module Reference after
# its port list changes.  Synthesize the BD hierarchy with the top-level run
# so daq_control_regs_v3 is resolved directly from sources_1.  Vendor IP DCPs
# remain available and the implemented hardware hierarchy is unchanged.
set system_bd [get_files -quiet *System.bd]
if {[llength $system_bd]} {
    set_property SYNTH_CHECKPOINT_MODE None $system_bd
}

# The legacy project had impl_1 pinned to xc7z010 even though the project and
# synthesis run target the actual xc7z020-2 device.  Keep every run on the
# project part before implementation.
set project_part [get_property PART [current_project]]
set_property PART $project_part [get_runs synth_1]
set_property PART $project_part [get_runs impl_1]
# The design contains two SG DMA fabrics and two 32-bit capture memories.
# Explore placement/physical optimization so the final timing sign-off does
# not depend on the legacy default strategy's seed.
set_property strategy Performance_Explore [get_runs impl_1]

# This file constrained the deleted dual-ADC clock mux (including 3 MSPS).
# Preserve it on disk for history but exclude it from the final active set.
set obsolete_clock_xdc [file join $project_dir AXI_DMA.srcs constrs_1 new \
    dual_adc_impl_clocks.xdc]
set obsolete_file [get_files -quiet $obsolete_clock_xdc]
if {[llength $obsolete_file]} {
    remove_files -fileset constrs_1 $obsolete_file
}

reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
set synth_status [get_property STATUS [get_runs synth_1]]
puts "AD9269_FINAL_SYNTH_STATUS=$synth_status"
if {![string match "*Complete*" $synth_status]} {
    close_project
    exit 1
}

reset_run impl_1
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
set impl_status [get_property STATUS [get_runs impl_1]]
puts "AD9269_IMPL_STATUS=$impl_status"
if {![string match "*Complete*" $impl_status]} {
    close_project
    exit 1
}

open_run impl_1
report_utilization -hierarchical \
    -file [file join $report_dir post_route_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained \
    -check_timing_verbose \
    -file [file join $report_dir post_route_timing_summary.rpt]
report_bus_skew -file [file join $report_dir post_route_bus_skew.rpt]
report_drc -file [file join $report_dir post_route_drc.rpt]
report_methodology -file [file join $report_dir post_route_methodology.rpt]
report_clock_utilization \
    -file [file join $report_dir post_route_clock_utilization.rpt]
report_power -file [file join $report_dir post_route_power.rpt]
write_checkpoint -force [file join $report_dir post_route.dcp]

set setup_path [get_timing_paths -delay_type max -max_paths 1 -nworst 1]
set hold_path [get_timing_paths -delay_type min -max_paths 1 -nworst 1]
set wns [expr {[llength $setup_path] ? [get_property SLACK $setup_path] : 0.0}]
set whs [expr {[llength $hold_path] ? [get_property SLACK $hold_path] : 0.0}]
set drc_errors [get_drc_violations -quiet -filter {SEVERITY == Error}]
set methodology_critical [get_methodology_violations -quiet \
    -filter {SEVERITY == "Critical Warning"}]
set unconstrained [check_timing -quiet -override_defaults no_clock]

puts "AD9269_WNS=$wns"
puts "AD9269_WHS=$whs"
puts "AD9269_DRC_ERROR_COUNT=[llength $drc_errors]"
puts "AD9269_METHODOLOGY_CRITICAL_COUNT=[llength $methodology_critical]"
puts "AD9269_NO_CLOCK_CHECK=$unconstrained"

if {$wns < 0.0 || $whs < 0.0 || [llength $drc_errors] != 0 ||
    [llength $methodology_critical] != 0} {
    puts "AD9269_DELIVERY_REJECTED=timing_or_drc"
    close_project
    exit 2
}

write_bitstream -force [file join $output_dir top.bit]
write_hw_platform -fixed -force \
    -file [file join $output_dir ad9269_single_dualdma.xsa]

set hwh_candidates [glob -nocomplain \
    [file join $project_dir AXI_DMA.gen sources_1 bd System hw_handoff *.hwh] \
    [file join $project_dir AXI_DMA.srcs sources_1 bd System hw_handoff *.hwh]]
if {[llength $hwh_candidates] > 0} {
    file copy -force [lindex $hwh_candidates 0] \
        [file join $output_dir System.hwh]
}

puts "AD9269_DELIVERY_DIR=$output_dir"
close_project
exit 0
