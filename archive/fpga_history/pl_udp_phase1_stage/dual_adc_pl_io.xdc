# System clock and reset used by the pure-PL acquisition/network plane.
set_property -dict {PACKAGE_PIN N18 IOSTANDARD LVCMOS33} [get_ports sys_clk]
set_property -dict {PACKAGE_PIN G19 IOSTANDARD LVCMOS33 PULLUP true} [get_ports sys_rst_n]
create_clock -name pl_sys_clk -period 20.000 [get_ports sys_clk]

# J25 is intentionally unconstrained and completely free for the display.

# PL-side RGMII PHY. This link is dedicated to ADC monitoring/control from PC.
set_property -dict {PACKAGE_PIN J15 IOSTANDARD LVCMOS33} [get_ports eth_rst_n]
set_property -dict {PACKAGE_PIN K17 IOSTANDARD LVCMOS33} [get_ports eth_rxc]
set_property -dict {PACKAGE_PIN F17 IOSTANDARD LVCMOS33} [get_ports eth_rx_ctl]
set_property -dict {PACKAGE_PIN E17 IOSTANDARD LVCMOS33} [get_ports {eth_rxd[0]}]
set_property -dict {PACKAGE_PIN D18 IOSTANDARD LVCMOS33} [get_ports {eth_rxd[1]}]
set_property -dict {PACKAGE_PIN F19 IOSTANDARD LVCMOS33} [get_ports {eth_rxd[2]}]
set_property -dict {PACKAGE_PIN F20 IOSTANDARD LVCMOS33} [get_ports {eth_rxd[3]}]
set_property -dict {PACKAGE_PIN K18 IOSTANDARD LVCMOS33 SLEW FAST DRIVE 8} [get_ports eth_txc]
set_property -dict {PACKAGE_PIN F16 IOSTANDARD LVCMOS33 SLEW FAST DRIVE 8} [get_ports eth_tx_ctl]
set_property -dict {PACKAGE_PIN E18 IOSTANDARD LVCMOS33 SLEW FAST DRIVE 8} [get_ports {eth_txd[0]}]
set_property -dict {PACKAGE_PIN E19 IOSTANDARD LVCMOS33 SLEW FAST DRIVE 8} [get_ports {eth_txd[1]}]
set_property -dict {PACKAGE_PIN G17 IOSTANDARD LVCMOS33 SLEW FAST DRIVE 8} [get_ports {eth_txd[2]}]
set_property -dict {PACKAGE_PIN G18 IOSTANDARD LVCMOS33 SLEW FAST DRIVE 8} [get_ports {eth_txd[3]}]
create_clock -name pl_eth_rxc -period 8.000 [get_ports eth_rxc]

# RTL8211E-VB RGMII-ID timing model.
#
# Board straps enable the PHY's 2 ns RXC and TXC internal delays.  The exact
# PCB trace-length report is not available, so the limits below include a
# provisional +/-0.5 ns clock-to-data PCB skew budget.  Replace only the
# *_PCB_SKEW_NS value when measured or layout-derived skew becomes available,
# then regenerate every phase-1 timing report.
#
# RX (PHY -> FPGA):
#   RTL8211E transmitter-integrated-delay setup/hold window: [-2.8, -1.2] ns
#   Provisional window after PCB skew:                    [-3.3, -0.7] ns
# TX (FPGA -> PHY):
#   RTL8211E receiver-integrated-delay window:             [-2.6, -1.0] ns
#   Provisional window after PCB skew:                     [-3.1, -0.5] ns
#
# Negative values are intentional: in RGMII-ID the forwarded clock reaches
# the receiver after the associated data transition.  Both DDR edges must be
# constrained; do not replace these paths with false-path exceptions.
set RGMII_PCB_SKEW_NS 0.500
set RGMII_RX_INPUT_MAX_NS [expr {-1.200 + $RGMII_PCB_SKEW_NS}]
set RGMII_RX_INPUT_MIN_NS [expr {-2.800 - $RGMII_PCB_SKEW_NS}]
set RGMII_TX_OUTPUT_MAX_NS [expr {-1.000 + $RGMII_PCB_SKEW_NS}]
set RGMII_TX_OUTPUT_MIN_NS [expr {-2.600 - $RGMII_PCB_SKEW_NS}]

set RGMII_RX_INPUTS [get_ports {eth_rxd[0] eth_rxd[1] eth_rxd[2] eth_rxd[3] eth_rx_ctl}]
set_input_delay -clock [get_clocks pl_eth_rxc] -max $RGMII_RX_INPUT_MAX_NS $RGMII_RX_INPUTS
set_input_delay -clock [get_clocks pl_eth_rxc] -min $RGMII_RX_INPUT_MIN_NS $RGMII_RX_INPUTS
set_input_delay -clock [get_clocks pl_eth_rxc] -clock_fall -max \
    $RGMII_RX_INPUT_MAX_NS -add_delay $RGMII_RX_INPUTS
set_input_delay -clock [get_clocks pl_eth_rxc] -clock_fall -min \
    $RGMII_RX_INPUT_MIN_NS -add_delay $RGMII_RX_INPUTS

# eth_txc is a forwarded copy of the MMCM output used by the TX DDR registers.
# Naming it explicitly prevents output delays from being referenced to an
# unrelated or auto-selected clock.
create_generated_clock -name pl_eth_txc \
    -source [get_pins rgmii_clock_inst/rgmii_mmcm/CLKOUT0] \
    -divide_by 1 [get_ports eth_txc]

set RGMII_TX_OUTPUTS [get_ports {eth_txd[0] eth_txd[1] eth_txd[2] eth_txd[3] eth_tx_ctl}]
set_output_delay -clock [get_clocks pl_eth_txc] -max $RGMII_TX_OUTPUT_MAX_NS $RGMII_TX_OUTPUTS
set_output_delay -clock [get_clocks pl_eth_txc] -min $RGMII_TX_OUTPUT_MIN_NS $RGMII_TX_OUTPUTS
set_output_delay -clock [get_clocks pl_eth_txc] -clock_fall -max \
    $RGMII_TX_OUTPUT_MAX_NS -add_delay $RGMII_TX_OUTPUTS
set_output_delay -clock [get_clocks pl_eth_txc] -clock_fall -min \
    $RGMII_TX_OUTPUT_MIN_NS -add_delay $RGMII_TX_OUTPUTS

# The ADC, PS and RGMII domains cross only through explicit asynchronous FIFOs.
set_clock_groups -asynchronous \
    -group [get_clocks -include_generated_clocks pl_sys_clk] \
    -group [get_clocks -include_generated_clocks pl_eth_rxc]
