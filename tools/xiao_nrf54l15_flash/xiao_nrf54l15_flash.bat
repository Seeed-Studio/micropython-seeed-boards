@echo off
REM nRF54L15 one-click flash script (Windows)
REM Behavior:
REM   * Auto-upgrades pyocd & intelhex unless SKIP_PYOCD_UPGRADE=1
REM   * Auto-detects HEX: merged.hex > only file > newest modified
REM   * Always performs mass erase before programming
REM   * Supports optional: --hex <file>, --probe <id>
REM Usage examples:
REM   flash.bat
REM   flash.bat --probe E2DAE686
REM   flash.bat --hex app.hex --probe E2DAE686
REM Skip upgrade: set SKIP_PYOCD_UPGRADE=1 & flash.bat

set SCRIPT_DIR=%~dp0
set PY_SCRIPT=%SCRIPT_DIR%xiao_nrf54l15_flash.py
if not exist "%PY_SCRIPT%" (
	echo [ERROR] Missing script %PY_SCRIPT%
	exit /b 1
)

REM Pick python
set PYTHON=
for %%P in (python.exe python3.exe py.exe) do (
	where %%P >nul 2>nul && if not defined PYTHON set PYTHON=%%P
)
if not defined PYTHON (
	echo [ERROR] No python interpreter found.
	exit /b 2
)

REM Pass all args straight through
set ARGS=%*
echo Running: %PYTHON% %PY_SCRIPT% %ARGS%
%PYTHON% "%PY_SCRIPT%" %ARGS%
exit /b %errorlevel%