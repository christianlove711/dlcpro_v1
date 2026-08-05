set project_dir {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
set xdc [file join $project_dir AXI_DMA.srcs constrs_1 new \
    ad9269_clock_domains.xdc]
open_project [file join $project_dir AXI_DMA.xpr]
if {![llength [get_files -quiet $xdc]]} {
  add_files -fileset constrs_1 -norecurse $xdc
}
set_property USED_IN_SYNTHESIS false [get_files $xdc]
set_property USED_IN_IMPLEMENTATION true [get_files $xdc]
close_project
exit 0
