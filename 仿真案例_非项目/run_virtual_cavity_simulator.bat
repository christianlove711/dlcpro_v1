@echo off
set "ROOT=%~dp0"
set "PYTHONW=C:\Users\chris\anaconda3\pythonw.exe"

if exist "%PYTHONW%" (
    start "" "%PYTHONW%" "%ROOT%virtual_cavity_lock_simulator.py"
) else (
    start "" pythonw "%ROOT%virtual_cavity_lock_simulator.py"
)
