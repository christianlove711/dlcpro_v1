set project_dir {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
cd {C:/baidunetdiskdownload/Vivado2020_2/Vivado/2020.2/scripts/ipintegrator}
set rc [catch {open_project [file join $project_dir AXI_DMA.xpr]} detail]
puts "OPEN_RC=$rc"
puts "OPEN_DETAIL=$detail"
puts "CURRENT_PROJECT=[current_project -quiet]"
if {[llength [current_project -quiet]]} {
  puts "DAQ_FILE=[get_files -quiet *daq_control_regs_v3.v]"
  puts "DAQ_FILE_USED_SYNTH=[get_property USED_IN_SYNTHESIS [get_files -quiet *daq_control_regs_v3.v]]"
  catch {update_compile_order -fileset sources_1} update_detail
  puts "UPDATE_DETAIL=$update_detail"
  puts "BD_FILES=[get_files -quiet *System.bd]"
  catch {open_bd_design [get_files *System.bd]} bd_detail
  puts "BD_OPEN_DETAIL=$bd_detail"
  puts "DAQ_CELL=[get_bd_cells -quiet daq_control_0]"
  catch {update_module_reference [get_bd_cells -quiet daq_control_0]} ref_detail
  puts "REF_DETAIL=$ref_detail"
  catch {validate_bd_design} validate_detail
  puts "VALIDATE_DETAIL=$validate_detail"
  catch {save_bd_design} save_detail
  puts "SAVE_DETAIL=$save_detail"
  close_project
}
exit 0
