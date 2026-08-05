# PS FCLK and the PL board-oscillator MMCM clocks have unrelated physical
# sources.  All crossings between them use explicit synchronizers, AXI clock
# converters, or asynchronous FIFOs.
set_clock_groups -asynchronous \
    -group [get_clocks {clk_fpga_0 clk_fpga_1}] \
    -group [get_clocks {clk100_raw clk50_raw}]
