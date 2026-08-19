@echo off
REM XIAO STM32C5 one-click flash (Windows) -- thin wrapper over the Python helper.
REM Put the board in bootloader mode first (double-click Reset -> XIAOC5BOOT drive),
REM then run this script. It copies micropython-xiao-stm32c5.uf2 onto the board.
setlocal
set SCRIPT_DIR=%~dp0
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] python not found in PATH. Install Python 3 or run xiao_stm32c5_flash.py with your interpreter.
  exit /b 2
)
python "%SCRIPT_DIR%xiao_stm32c5_flash.py" %*
