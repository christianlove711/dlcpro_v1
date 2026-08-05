# AD9269 dual-DMA Linux interface

The final bitstream contains one ADC (AD9269) and two independent receive
paths:

- Event DMA: `/dev/zynq_daq`, mode 1, 64 slots, 8,320-byte `EVNT` frames,
  12,288-byte mmap stride, AXI DMA 0 through HP0.
- Scope DMA: `/dev/zynq_daq`, mode 0, 16 slots, 32,832-byte `SCOP` frames,
  36,864-byte mmap stride, AXI DMA 1 through HP1.

The channels, descriptor rings, interrupts and coherent buffers are
independent. Software may initialize both channels, but PL produces frames
only for the active mutually-exclusive acquisition mode.

`ZYNQ_DAQ_IOC_START` starts Event/automatic-lock mode.
`ZYNQ_DAQ_IOC_SCOPE_START` starts Scope mode with rate, decimation, trigger
and FPS settings. Both modes use the same `DEQUEUE`, `RELEASE`, `GET_STATUS`
and `STOP` operations; each dequeued frame reports its mode, valid length and
mmap stride.

Supported ADC rates are 5/10/20/40/80 MSPS. The PC PL-UDP monitor is a
separate path and accepts only 5/10/20 MSPS. `set_threshold` remains reserved
and returns `EOPNOTSUPP`; peak parameters are fixed in this RTL release.

Build the out-of-tree driver using `driver/Makefile`, merge
`zynq-daq-events.dtsi` with the XSA-generated device tree, and compile the
examples against `include/zynq_daq.h`. See `REGISTER_MAP.md`,
`EVNT_FRAME_FORMAT.md` and `SCOP_FRAME_FORMAT.md`.
