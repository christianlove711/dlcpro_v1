set root [file dirname [file normalize [info script]]]
set report_root [file join $root reports pl_udp_pc_v2]
set out_dir [file join $report_root baseline]
file mkdir $out_dir

open_project [file join $root AXI_DMA.xpr]

set manifest [open [file join $out_dir vivado_active_files.tsv] w]
puts $manifest "fileset\tfile_type\tused_in\tpath"
foreach fs_name {sources_1 constrs_1 sim_1} {
  set fs [get_filesets -quiet $fs_name]
  if {![llength $fs]} { continue }
  foreach f [lsort [get_files -quiet -of_objects $fs]] {
    set file_type ""
    set used_in ""
    catch {set file_type [get_property FILE_TYPE $f]}
    catch {set used_in [join [get_property USED_IN $f] ,]}
    puts $manifest "$fs_name\t$file_type\t$used_in\t[file normalize $f]"
  }
}
close $manifest

set project_info [open [file join $out_dir vivado_project_properties.txt] w]
foreach prop {NAME PART TARGET_LANGUAGE DEFAULT_LIB SIMULATOR_LANGUAGE} {
  set value ""
  catch {set value [get_property $prop [current_project]]}
  puts $project_info "$prop=$value"
}
puts $project_info "TOP_SOURCES=[get_property TOP [get_filesets sources_1]]"
puts $project_info "TOP_SIM=[get_property TOP [get_filesets sim_1]]"
close $project_info
close_project

set old_report_dir [file join $root reports ad9269_single_dualdma]
foreach name {
  post_route_timing_summary.rpt
  post_route_drc.rpt
  post_route_methodology.rpt
  post_route_utilization.rpt
  post_route_power.rpt
  final_sims_console.log
  final_impl_console.log
} {
  set src [file join $old_report_dir $name]
  if {[file exists $src]} {
    file copy -force $src [file join $out_dir $name]
  }
}
set sim_src [file join $old_report_dir simulations]
if {[file isdirectory $sim_src]} {
  file copy -force $sim_src [file join $out_dir simulations]
}
puts "PL_UDP_BASELINE_FROZEN=$out_dir"
exit
