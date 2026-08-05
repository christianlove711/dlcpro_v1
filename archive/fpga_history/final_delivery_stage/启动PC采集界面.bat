@echo off
setlocal
pushd "%~dp0.."
rem Compatibility shortcut for the canonical app.py ADC entry.
python app.py --open-adc
set "DAQ_EXIT=%ERRORLEVEL%"
popd
exit /b %DAQ_EXIT%
