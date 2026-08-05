@echo off
setlocal
pushd "%~dp0.."
rem Compatibility shortcut: use the main application's single authoritative
rem ADC window so DLC pro connection and recording metadata are shared.
python app.py --open-adc
set "DAQ_EXIT=%ERRORLEVEL%"
popd
exit /b %DAQ_EXIT%
