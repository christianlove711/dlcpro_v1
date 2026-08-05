set project_dir {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
set output_dir [file join $project_dir deliverables ad9269_single_dualdma_final]
file mkdir $output_dir
open_project [file join $project_dir AXI_DMA.xpr]
puts "IMPL_STATUS=[get_property STATUS [get_runs impl_1]]"
open_run impl_1
write_hw_platform -fixed -force \
    -file [file join $output_dir ad9269_single_dualdma.xsa]
set hwh [file join $project_dir AXI_DMA.srcs sources_1 bd System \
    hw_handoff System.hwh]
if {![file exists $hwh]} {
  puts "ERROR: missing $hwh"
  close_project
  exit 1
}
file copy -force $hwh [file join $output_dir System.hwh]
puts "AD9269_HW_EXPORT_PASS=$output_dir"
close_project
exit 0
