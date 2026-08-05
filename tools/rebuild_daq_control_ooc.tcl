set project_dir {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
cd {C:/baidunetdiskdownload/Vivado2020_2/Vivado/2020.2/scripts/ipintegrator}
open_project [file join $project_dir AXI_DMA.xpr]
set run_name System_daq_control_0_15_synth_1
if {![llength [get_runs -quiet $run_name]]} {
  puts "ERROR: missing $run_name"
  close_project
  exit 1
}
reset_run $run_name
launch_runs $run_name -jobs 1
wait_on_run $run_name
set status [get_property STATUS [get_runs $run_name]]
puts "DAQ_CONTROL_OOC_STATUS=$status"
close_project
if {![string match "*Complete*" $status]} {
  exit 2
}
exit 0
