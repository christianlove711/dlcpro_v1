# `EVNT` fixed DMA frame v1

Every S2MM descriptor transfers exactly **8,320 bytes** (2,080 32-bit AXIS
words).  It is a 128-byte / 32-word little-endian header in PS DDR followed by
1,024 pre-trigger and 1,024 post-trigger 32-bit sample-pair words.  A pair
uses the PL canonical ordering `[31:16]=B, [15:0]=A`, both signed 16-bit.

| Word | Field |
|---:|---|
| 0 | `0x45564E54` (`EVNT`) |
| 1 | `0x00010080`: version 1, header size 128 bytes |
| 2 | model, saturation, OTR, peak polarity flags |
| 3 | sample rate (Hz) |
| 4 / 5 | frame sequence / accepted-event count |
| 6 / 7 | trigger sample index, low / high |
| 8 / 9 | Q16.16 peak location, low / high |
| 10..15 | baseline, peak value, peak-to-peak, width, signed 48-bit area |
| 16..19 | current interval, mean interval Q16, variance Q16 |
| 20..26 | B-channel error statistics, crossing statistics, threshold, noise |
| 27 | dropped-event count at capture time |
| 28..30 | pre-sample count (1024), post-sample count (1024), accepted samples |
| 31 | event count suppressed while the DMA path was disabled |
| 32..1055 | pre-trigger sample pairs, oldest first |
| 1056..2079 | post-trigger sample pairs, trigger sample first |

`DEQUEUE` leases a completed slot. Map the slot with
`zynq_daq_map_slot(fd, frame.slot)`, consume exactly `frame.length` bytes,
then call `zynq_daq_release_frame`. A STOP cancels DMA and invalidates all
outstanding leases.

On ARM, read every header entry as a little-endian `uint32_t`. The first four
memory bytes are `54 4e 56 45`, which decode to the word `0x45564e54`.
