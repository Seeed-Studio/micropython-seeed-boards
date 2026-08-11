@echo off
set SCRIPT_DIR=%~dp0
set PY_SCRIPT=%SCRIPT_DIR%xiao_nrf54lm20b_flash.py
if not exist "%PY_SCRIPT%" (
    echo [ERROR] Missing script %PY_SCRIPT%
    exit /b 1
)

set PYTHON=
for %%P in (python.exe python3.exe py.exe) do (
    where %%P >nul 2>nul && if not defined PYTHON set PYTHON=%%P
)
if not defined PYTHON (
    echo [ERROR] No python interpreter found.
    exit /b 2
)

set ARGS=%*
echo Running: %PYTHON% %PY_SCRIPT% %ARGS%
%PYTHON% "%PY_SCRIPT%" %ARGS%
