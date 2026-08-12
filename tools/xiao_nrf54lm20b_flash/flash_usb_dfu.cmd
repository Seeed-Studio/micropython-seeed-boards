@echo off
REM Double-click / cmd launcher for the portable PowerShell USB DFU flasher.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0xiao_nrf54lm20b_flash.ps1" %*
exit /b %ERRORLEVEL%
