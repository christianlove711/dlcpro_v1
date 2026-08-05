# Run only when the default 208.125-degree candidate has a negative RGMII
# setup/hold slack.  Each phase is a separate synthesis/implementation run.
set root [file dirname [file normalize [info script]]]
set out_dir [file join $root reports pl_udp_pc_v2 phase_sweep]
file mkdir $out_dir

proc worst_slack {delay_type direction ports} {
  if {$direction eq "-from"} {
    set paths [get_timing_paths -delay_type $delay_type -from $ports \
        -max_paths 1 -nworst 1]
  } else {
    set paths [get_timing_paths -delay_type $delay_type -to $ports \
        -max_paths 1 -nworst 1]
  }
  if {![llength $paths]} {
    return "NO_PATH"
  }
  return [get_property SLACK [lindex $paths 0]]
}

set phases {}
for {set p 0.0} {$p < 360.0} {set p [expr {$p + 5.625}]} {
  lappend phases [format %.3f $p]
}
if {[info exists ::env(RGMII_PHASE_LIST)] && $::env(RGMII_PHASE_LIST) ne ""} {
  set phases [split $::env(RGMII_PHASE_LIST) ,]
}

open_project [file join $root AXI_DMA.xpr]
set csv [open [file join $out_dir phase_sweep.csv] w]
puts $csv "phase_deg,rx_setup,rx_hold,tx_setup,tx_hold,min_rgmii_slack,global_wns,global_whs,ddr_mapping,status"
set best_phase ""
set best_score -1000000.0

foreach phase $phases {
  puts "RGMII_PHASE_SWEEP_BEGIN=$phase"
  set_property verilog_define [list "PL_RGMII_CLKOUT0_PHASE=$phase"] \
      [get_filesets sources_1]

  # A phase is never eligible unless the behavioral checker confirms the
  # rising/falling nibble order, RX_CTL encoding, preamble/SFD and recovery.
  set mapping_status PASS
  set_property top tb_rgmii_ddr_mapping [get_filesets sim_1]
  set_property xsim.simulate.runtime all [get_filesets sim_1]
  if {[catch {launch_simulation -simset sim_1 -mode behavioral} sim_detail]} {
    set mapping_status "LAUNCH_FAILED"
    catch {close_sim}
  } else {
    close_sim
    set sim_log [file join $root AXI_DMA.sim sim_1 behav xsim simulate.log]
    set h [open $sim_log r]
    set sim_text [read $h]
    close $h
    if {[string first "PASS: RGMII DDR nibble mapping" $sim_text] < 0 ||
        [string first "Fatal:" $sim_text] >= 0} {
      set mapping_status FAIL
    }
  }
  if {$mapping_status ne "PASS"} {
    puts $csv "$phase,,,,,,,,${mapping_status},DDR_MAPPING_FAILED"
    flush $csv
    continue
  }

  reset_run synth_1
  launch_runs synth_1 -jobs 6
  wait_on_run synth_1
  if {[string first "Complete" [get_property STATUS [get_runs synth_1]]] < 0} {
    puts $csv "$phase,,,,,,,,PASS,SYNTH_FAILED"
    flush $csv
    continue
  }
  reset_run impl_1
  launch_runs impl_1 -to_step route_design -jobs 6
  wait_on_run impl_1
  if {[string first "Complete" [get_property STATUS [get_runs impl_1]]] < 0} {
    puts $csv "$phase,,,,,,,,PASS,IMPL_FAILED"
    flush $csv
    continue
  }
  open_run impl_1
  set wns [get_property STATS.WNS [get_runs impl_1]]
  set whs [get_property STATS.WHS [get_runs impl_1]]
  set rx_ports [get_ports {eth_rxd[0] eth_rxd[1] eth_rxd[2] eth_rxd[3] eth_rx_ctl}]
  set tx_ports [get_ports {eth_txd[0] eth_txd[1] eth_txd[2] eth_txd[3] eth_tx_ctl}]
  set rx_setup [worst_slack max -from $rx_ports]
  set rx_hold  [worst_slack min -from $rx_ports]
  set tx_setup [worst_slack max -to $tx_ports]
  set tx_hold  [worst_slack min -to $tx_ports]
  set rgmii_values [list $rx_setup $rx_hold $tx_setup $tx_hold]
  set numeric 1
  foreach value $rgmii_values {
    if {![string is double -strict $value]} {set numeric 0}
  }
  set score "NO_PATH"
  set status ROUTED
  if {$numeric} {
    set score [lindex $rgmii_values 0]
    foreach value [lrange $rgmii_values 1 end] {
      if {$value < $score} {set score $value}
    }
    if {$score > $best_score} {
      set best_score $score
      set best_phase $phase
    }
    if {$score >= 0.0} {set status RGMII_TIMING_MET}
  }
  report_timing_summary -delay_type min_max -report_unconstrained \
      -check_timing_verbose \
      -file [file join $out_dir [format "timing_phase_%s.rpt" $phase]]
  puts $csv "$phase,$rx_setup,$rx_hold,$tx_setup,$tx_hold,$score,$wns,$whs,PASS,$status"
  flush $csv
  close_design
}

# Restore the production default in project metadata.  Selection of a new
# default is permitted only after the DDR mapping test and board validation.
set_property verilog_define {PL_RGMII_CLKOUT0_PHASE=208.125} \
    [get_filesets sources_1]
close $csv
set selection [open [file join $out_dir selected_phase.txt] w]
if {$best_phase eq ""} {
  puts $selection "NO_ROUTED_PHASE"
} elseif {$best_score < 0.0} {
  puts $selection "NO_PASSING_PHASE"
  puts $selection "best_phase_deg=$best_phase"
  puts $selection "best_min_rgmii_slack_ns=$best_score"
  puts $selection "Candidate must not be promoted or used for board test."
} else {
  puts $selection "SELECTED_PHASE_DEG=$best_phase"
  puts $selection "MIN_RGMII_SLACK_NS=$best_score"
  puts $selection "Board validation is still required before promotion."
}
close $selection
close_project
puts "RGMII_PHASE_SWEEP_COMPLETE=$out_dir"
exit
