set project_dir {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
open_project [file join $project_dir AXI_DMA.xpr]
set_property top tb_ad9269_spi [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
launch_simulation -simset sim_1 -mode behavioral
close_sim
close_project
exit 0
