set ltx_file {C:/Users/chris/Desktop/2/02_/top.ltx}
set csv_file {C:/Users/chris/dlcpro_v1/daq_pc/captures/ad9280_ff_trigger.csv}
file mkdir [file dirname $csv_file]

catch {open_hw_manager}
connect_hw_server -url localhost:3121 -allow_non_jtag
open_hw_target
set device [lindex [get_hw_devices -filter {PART =~ "xc7z020*"}] 0]
current_hw_device $device
set_property PROBES.FILE $ltx_file $device
set_property FULL_PROBES.FILE $ltx_file $device
refresh_hw_device $device

set ila [lindex [get_hw_ilas -of_objects $device] 0]
set debug_probe [get_hw_probes zynq_u/System_i/Controller/ad9280_debug_0_2 \
    -of_objects $ila]
# probe0[15:8] is the AD9280 registered sample. Other probe bits are don't-care.
set_property TRIGGER_COMPARE_VALUE \
    "eq51'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx11111111xxxxxxxx" \
    $debug_probe
set_property CONTROL.TRIGGER_POSITION 512 $ila
run_hw_ila $ila
# Stop after five seconds if no full-scale code is observed.
after 5000 [list stop_hw_ila $ila]
wait_on_hw_ila $ila
upload_hw_ila_data $ila
set data [lindex [get_hw_ila_data -of_objects $ila] 0]
write_hw_ila_data -force -csv_file $csv_file $data
puts "CSV=$csv_file"
close_hw_manager
