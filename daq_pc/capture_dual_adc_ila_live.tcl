set ltx_file {C:/Users/chris/Desktop/2/02_/top.ltx}
set csv_file {C:/Users/chris/dlcpro_v1/daq_pc/captures/dual_adc_ila_live.csv}
file mkdir [file dirname $csv_file]

catch {open_hw_manager}
connect_hw_server -url localhost:3121 -allow_non_jtag
open_hw_target
set device [lindex [get_hw_devices -filter {PART =~ "xc7z020*"}] 0]
if {![llength $device]} {
  error "No xc7z020 device found"
}
current_hw_device $device
set_property PROBES.FILE $ltx_file $device
set_property FULL_PROBES.FILE $ltx_file $device
refresh_hw_device $device

set ila [lindex [get_hw_ilas -of_objects $device] 0]
if {![llength $ila]} {
  error "No ILA core found"
}
set_property CONTROL.TRIGGER_POSITION 512 $ila
run_hw_ila $ila
wait_on_hw_ila $ila
upload_hw_ila_data $ila
set data [lindex [get_hw_ila_data -of_objects $ila] 0]
write_hw_ila_data -force -csv_file $csv_file $data
puts "ILA=$ila"
puts "PROBES=[get_hw_probes -of_objects $ila]"
puts "CSV=$csv_file"
close_hw_manager
