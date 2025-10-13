@echo off
REM -------------------------------------------------------------
REM flash.bat - Simple one-click flashing entry point for Windows.
REM Purpose: Invoke the Python helper script xiao_mg24_flash.py to:
REM   1. Auto-select (or user-specified) single .hex firmware in current directory
REM   2. Ensure pyocd is installed (install if missing)
REM   3. Run "pyocd flash"
REM Usage: Double-click or run in a terminal. All arguments are forwarded to Python.
REM Examples:
REM   flash.bat --dry-run
REM   flash.bat --hex my_firmware.hex --target efr32mg24b220f1536im48
REM Add this directory to PATH if you want to call it from anywhere.
REM -------------------------------------------------------------

REM Change to the directory where this batch file resides (so relative files are found)
pushd %~dp0 >nul

REM Call Python (must be on PATH). %* forwards all provided arguments.
python xiao_mg24_flash.py %*
set RET=%ERRORLEVEL%

REM Return to original directory
popd >nul

REM Propagate underlying script's exit code (useful for CI / automation)
exit /b %RET%