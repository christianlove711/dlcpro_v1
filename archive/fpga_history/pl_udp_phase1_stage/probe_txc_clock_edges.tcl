set root {C:/Users/chris/FPGA_Projects/A-high-speed-data-acquisition-framework-main}
open_project [file join $root AXI_DMA.xpr]
open_run impl_1

puts "TXC_SOURCE_PIN=[get_pins -quiet eth_bridge_inst/u_rgmii_tx/txc_oddr/C0]"
puts "TXC_OUTPUT_PORT=[get_ports -quiet eth_txc]"

create_generated_clock -name pl_eth_txc_probe \
    -source [get_pins eth_bridge_inst/u_rgmii_tx/txc_oddr/C0] \
    -master_clock [get_clocks shifted_raw] \
    -edges {1 2 3} -add [get_ports eth_txc]
set tx_ports [get_ports {eth_txd[0] eth_txd[1] eth_txd[2] eth_txd[3] eth_tx_ctl}]
set_output_delay -clock [get_clocks pl_eth_txc_probe] -max -0.500 $tx_ports
set_output_delay -clock [get_clocks pl_eth_txc_probe] -min -3.100 -add_delay $tx_ports
set_output_delay -clock [get_clocks pl_eth_txc_probe] -clock_fall -max -0.500 $tx_ports
set_output_delay -clock [get_clocks pl_eth_txc_probe] -clock_fall -min \
    -3.100 $tx_ports
update_timing

puts "TX_SETUP_AFTER_EDGE_MAP"
report_timing -delay_type max \
    -to [get_ports {eth_txd[0] eth_txd[1] eth_txd[2] eth_txd[3] eth_tx_ctl}] \
    -group pl_eth_txc_probe -max_paths 1 -nworst 1
puts "TX_HOLD_AFTER_EDGE_MAP"
report_timing -delay_type min \
    -to [get_ports {eth_txd[0] eth_txd[1] eth_txd[2] eth_txd[3] eth_tx_ctl}] \
    -group pl_eth_txc_probe -max_paths 1 -nworst 1
close_project
exit
