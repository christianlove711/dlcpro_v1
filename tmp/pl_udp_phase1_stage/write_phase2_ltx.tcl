set root {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
set out_dir [file join $root reports pl_udp_pc_v2 phase2]
open_project [file join $root AXI_DMA.xpr]
open_run impl_1
write_debug_probes -force \
    [file join $out_dir top_pl_udp_v2_phase2_test.ltx]
close_project
exit
