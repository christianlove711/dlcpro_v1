# Program the Zynq PL over JTAG without opening the Vivado GUI.
# Usage: vivado -mode batch -source program_fpga_bit.tcl -tclargs design.bit

proc progress {value message_id} {
    # Keep the machine-readable protocol ASCII-only. Python translates these
    # IDs for the Chinese GUI, avoiding Vivado/Tcl console encoding ambiguity.
    puts "FPGA_PROGRAM_PROGRESS:${value}:${message_id}"
    flush stdout
}

if {$argc != 1} {
    puts stderr "FPGA_PROGRAM_ERROR:INVALID_ARGUMENT_COUNT"
    exit 2
}

set bit_file [file normalize [lindex $argv 0]]
if {![file exists $bit_file] || ![file isfile $bit_file]} {
    puts stderr "FPGA_PROGRAM_ERROR:BITSTREAM_NOT_FOUND:$bit_file"
    exit 2
}
if {![string equal -nocase [file extension $bit_file] ".bit"]} {
    puts stderr "FPGA_PROGRAM_ERROR:NOT_A_BITSTREAM:$bit_file"
    exit 2
}

set manager_open 0
set target_open 0
if {[catch {
    progress 10 "STARTING_HW_SERVER"
    open_hw_manager
    set manager_open 1
    if {[catch {
        connect_hw_server -url localhost:3121 -allow_non_jtag
    } server_message]} {
        error "HW_SERVER_CONNECT_FAILED:$server_message"
    }

    progress 25 "SCANNING_JTAG"
    if {[catch {open_hw_target} target_message]} {
        error "JTAG_TARGET_OPEN_FAILED:$target_message"
    }
    set target_open 1
    set zynq_devices {}
    foreach device [get_hw_devices -quiet] {
        set part [get_property PART $device]
        if {[string match -nocase "xc7z*" $part]} {
            lappend zynq_devices $device
        }
    }
    if {[llength $zynq_devices] == 0} {
        error "NO_ZYNQ_DEVICE"
    }
    if {[llength $zynq_devices] > 1} {
        error "MULTIPLE_ZYNQ_DEVICES:$zynq_devices"
    }

    set device [lindex $zynq_devices 0]
    current_hw_device $device
    refresh_hw_device -update_hw_probes false $device
    set_property PROGRAM.FILE $bit_file $device

    set ltx_file "[file rootname $bit_file].ltx"
    if {[file exists $ltx_file]} {
        set_property PROBES.FILE $ltx_file $device
        set_property FULL_PROBES.FILE $ltx_file $device
        progress 45 "LOADED_PROBES"
    } else {
        set_property PROBES.FILE {} $device
        set_property FULL_PROBES.FILE {} $device
        progress 45 "READY_BITSTREAM"
    }

    progress 60 "PROGRAMMING_FPGA"
    program_hw_devices $device
    refresh_hw_device -update_hw_probes false $device
    progress 100 "PROGRAM_COMPLETE"
} message options]} {
    puts stderr "FPGA_PROGRAM_ERROR:$message"
    if {$target_open} { catch {close_hw_target} }
    catch {disconnect_hw_server}
    if {$manager_open} { catch {close_hw_manager} }
    exit 1
}

if {$target_open} { catch {close_hw_target} }
catch {disconnect_hw_server}
if {$manager_open} { catch {close_hw_manager} }
exit 0
