set project_dir {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
set bd_path [file join $project_dir AXI_DMA.srcs sources_1 bd System System.bd]

open_project [file join $project_dir AXI_DMA.xpr]
open_bd_design $bd_path

# The final release has no ILA.  The former 50-bit ADC debug core consumed
# roughly 2.7k LUTs and 15 BRAM36s and is not part of either DMA data path.
set ila_cell [get_bd_cells -quiet /Controller/ila_0]
if {[llength $ila_cell]} {
  delete_bd_objs $ila_cell
}

# Remove both possible representations (top-level port or hierarchy pin)
# used by older revisions of the block design.
foreach name {/ad9269_debug_0 /ila_sample_clk} {
  set obj [concat [get_bd_ports -quiet $name] [get_bd_pins -quiet $name]]
  if {[llength $obj]} {
    delete_bd_objs $obj
  }
}
foreach name {/Controller/ad9269_debug_0 /Controller/ila_sample_clk} {
  set obj [get_bd_pins -quiet $name]
  if {[llength $obj]} {
    delete_bd_objs $obj
  }
}

validate_bd_design
save_bd_design
generate_target all [get_files $bd_path]
make_wrapper -files [get_files $bd_path] -top -force

set wrapper [file join $project_dir AXI_DMA.gen sources_1 bd System hdl System_wrapper.v]
if {[file exists $wrapper] && ![llength [get_files -quiet $wrapper]]} {
  add_files -norecurse $wrapper
}
update_compile_order -fileset sources_1
close_project
exit 0
