# MSO64B + DLC pro One-Click Lock App

This is the first real-hardware GUI for cavity lock development.

## Run

```powershell
& C:\Users\chris\anaconda3\python.exe C:\Users\chris\dlcpro_v1\one_click_lock_app\app.py
```

or double-click:

```text
C:\Users\chris\dlcpro_v1\one_click_lock_app\run_one_click_lock_app.bat
```

## Current Workflow

- Connect MSO64B by LAN socket or USB/VISA.
- Connect DLC pro by LAN or USB/Serial through the official TOPTICA Laser SDK v3.3.3.
- Read only basic DLC pro status, scan status, lock status, and FALC status.
- Manually set `Scan Offset` and `Scan Amplitude`.
- Capture one oscilloscope frame and refresh `transmission` / `error` plots.
- Run one-click lock analysis to reach `Ready for FALC`.

## Hardware Write Guards

- `Configure 1 Hz Piezo Scan` writes:
  - `laser1.scan.output_channel = 50` (`PC Voltage`)
  - `laser1.scan.signal_type = 1` (`Triangle`)
  - `laser1.scan.frequency`
  - `laser1.scan.enabled = True`
- `Apply Offset/Amplitude` writes:
  - `laser1.scan.offset`
  - `laser1.scan.amplitude`
- FALC Main/Unlim writes require the `允许写 FALC 使能` checkbox.
- One-click automatic FALC enable requires the `允许一键锁频自动使能 FALC` checkbox.

## Notes

The first version intentionally does not do fast real-time acquisition. It treats each MSO64B acquisition as one frame, analyzes the frame, and updates the GUI.
