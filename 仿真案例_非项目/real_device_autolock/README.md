# Real Device Autolock

This folder contains the real-hardware path for one-click locking.

Current stage:
- Read `transmission` and single `error` waveforms from a Tektronix MDO/MSO oscilloscope.
- Save synchronized frames as CSV for algorithm validation.

Next stage:
- Add DLC pro control for Scan Offset / PZT fine / FALC enable.
- Feed each oscilloscope frame into the lock-point decision algorithm.

Expected oscilloscope channels:
- CH1: transmission
- CH2: error

CSV output columns:
```text
time,transmission,error
```
