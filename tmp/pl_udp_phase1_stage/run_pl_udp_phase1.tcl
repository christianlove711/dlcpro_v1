set root [file dirname [file normalize [info script]]]
set out_dir [file join $root reports pl_udp_pc_v2 phase1]
file mkdir $out_dir

open_project [file join $root AXI_DMA.xpr]
set_property verilog_define {PL_RGMII_CLKOUT0_PHASE=208.125} [get_filesets sources_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1

reset_run synth_1
launch_runs synth_1 -jobs 6
wait_on_run synth_1
set synth_status [get_property STATUS [get_runs synth_1]]
if {[string first "Complete" $synth_status] < 0} {
  error "synth_1 failed: $synth_status"
}

reset_run impl_1
launch_runs impl_1 -to_step write_bitstream -jobs 6
wait_on_run impl_1
set impl_status [get_property STATUS [get_runs impl_1]]
if {[string first "Complete" $impl_status] < 0} {
  error "impl_1 failed: $impl_status"
}

open_run impl_1
report_timing_summary -delay_type min_max -report_unconstrained \
    -check_timing_verbose -file [file join $out_dir post_route_timing_summary.rpt]
report_timing -delay_type max -from \
    [get_ports {eth_rxd[0] eth_rxd[1] eth_rxd[2] eth_rxd[3] eth_rx_ctl}] \
    -max_paths 100 -file [file join $out_dir rgmii_rx_setup.rpt]
report_timing -delay_type min -from \
    [get_ports {eth_rxd[0] eth_rxd[1] eth_rxd[2] eth_rxd[3] eth_rx_ctl}] \
    -max_paths 100 -file [file join $out_dir rgmii_rx_hold.rpt]
report_timing -delay_type max -to \
    [get_ports {eth_txd[0] eth_txd[1] eth_txd[2] eth_txd[3] eth_tx_ctl}] \
    -max_paths 100 -file [file join $out_dir rgmii_tx_setup.rpt]
report_timing -delay_type min -to \
    [get_ports {eth_txd[0] eth_txd[1] eth_txd[2] eth_txd[3] eth_tx_ctl}] \
    -max_paths 100 -file [file join $out_dir rgmii_tx_hold.rpt]
report_drc -file [file join $out_dir post_route_drc.rpt]
report_methodology -file [file join $out_dir post_route_methodology.rpt]
report_utilization -hierarchical -file [file join $out_dir post_route_utilization.rpt]
report_power -file [file join $out_dir post_route_power.rpt]
report_clock_interaction -file [file join $out_dir post_route_clock_interaction.rpt]

set slacks [open [file join $out_dir rgmii_slack_summary.tsv] w]
puts $slacks "class\tslack_ns\tstartpoint\tendpoint"
foreach spec {
  {rx_setup max -from}
  {rx_hold min -from}
  {tx_setup max -to}
  {tx_hold min -to}
} {
  lassign $spec label delay_type direction
  if {[string match "rx_*" $label]} {
    set ports [get_ports {eth_rxd[0] eth_rxd[1] eth_rxd[2] eth_rxd[3] eth_rx_ctl}]
  } else {
    set ports [get_ports {eth_txd[0] eth_txd[1] eth_txd[2] eth_txd[3] eth_tx_ctl}]
  }
  if {$direction eq "-from"} {
    set paths [get_timing_paths -delay_type $delay_type -from $ports -max_paths 1 -nworst 1]
  } else {
    set paths [get_timing_paths -delay_type $delay_type -to $ports -max_paths 1 -nworst 1]
  }
  if {![llength $paths]} {
    puts $slacks "$label\tNO_PATH\t\t"
    continue
  }
  set p [lindex $paths 0]
  puts $slacks "$label\t[get_property SLACK $p]\t[get_property STARTPOINT_PIN $p]\t[get_property ENDPOINT_PIN $p]"
}
close $slacks

set impl_dir [get_property DIRECTORY [get_runs impl_1]]
set bit_path [file join $impl_dir top.bit]
if {![file exists $bit_path]} {
  error "Expected bitstream not found: $bit_path"
}
file copy -force $bit_path [file join $out_dir top_pl_udp_v2_test.bit]
set ltx_candidates [glob -nocomplain -directory $impl_dir *.ltx]
if {[llength $ltx_candidates]} {
  file copy -force [lindex $ltx_candidates 0] \
      [file join $out_dir top_pl_udp_v2_test.ltx]
}
close_project
puts "PL_UDP_PHASE1_COMPLETE=$out_dir"
exit
