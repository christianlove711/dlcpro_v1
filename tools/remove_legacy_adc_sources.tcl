set project_dir {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
open_project [file join $project_dir AXI_DMA.xpr]

set legacy_files [list \
  [file join $project_dir AXI_DMA.srcs sources_1 new ad9280_input_frontend.v] \
  [file join $project_dir AXI_DMA.srcs sources_1 new dual_adc_ingress.v] \
  [file join $project_dir AXI_DMA.srcs sources_1 new dac_sine_rom.v] \
  [file join $project_dir AXI_DMA.srcs sources_1 new dac_wave_generator.v] \
  [file join $project_dir AXI_DMA.srcs sources_1 new dac_test_source.v] \
  [file join $project_dir AXI_DMA.srcs sources_1 new adc_input_frontend.v] \
  [file join $project_dir AXI_DMA.srcs sources_1 new adc_clock_generator.v] \
  [file join $project_dir AXI_DMA.srcs sources_1 new ad9269_clock_forwarder.v] \
  [file join $project_dir AXI_DMA.srcs sources_1 new daq_control_regs.v] \
  [file join $project_dir AXI_DMA.srcs sources_1 new daq_control_regs_v2.v] \
  [file join $project_dir trigger_unit.v] \
  [file join $project_dir sim tb_dac_test_source.sv] \
  [file join $project_dir sim tb_dac_adc_loopback.sv] \
  [file join $project_dir sim tb_adc_input_frontend.sv] \
  [file join $project_dir AXI_DMA.srcs sim_1 new tb_ad9280_frontend.sv] \
  [file join $project_dir AXI_DMA.srcs sim_1 new tb_dual_adc_ingress.sv] \
  [file join $project_dir AXI_DMA.srcs sim_1 new tb_ad9280_udp_end_to_end.sv] \
  [file join $project_dir AXI_DMA.srcs sim_1 new tb_adc_clock_generator.sv] \
  [file join $project_dir AXI_DMA.srcs sim_1 new tb_ad9269_frontend.sv]]

foreach path $legacy_files {
  set f [get_files -quiet $path]
  if {[llength $f]} {
    remove_files $f
    puts "REMOVED_FROM_PROJECT=$path"
  }
}
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
close_project
exit 0
