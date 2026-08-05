catch {open_hw_manager}
connect_hw_server -url localhost:3121 -allow_non_jtag
open_hw_target
set devices [get_hw_devices -filter {PART =~ "xc7z020*"}]
puts "DEVICES=$devices"
if {[llength $devices]} {
  current_hw_device [lindex $devices 0]
  refresh_hw_device [lindex $devices 0]
  puts "ILAS=[get_hw_ilas -of_objects [lindex $devices 0]]"
  foreach ila [get_hw_ilas -of_objects [lindex $devices 0]] {
    puts "ILA=$ila"
    puts "PROBES=[get_hw_probes -of_objects $ila]"
  }
}
close_hw_manager
