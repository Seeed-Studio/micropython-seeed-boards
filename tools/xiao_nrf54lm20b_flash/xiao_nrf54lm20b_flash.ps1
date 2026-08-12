# XIAO nRF54LM20B USB DFU flasher (portable, Windows, no install needed).
#
# Uploads a signed MCUboot app image with `nrfutil mcu-manager serial
# image-upload`. The board enters the MCUboot USB serial-recovery loader when
# you HOLD the USER button and press RESET (enumerates as VID:PID 2886:0013).
#
# nrfutil is resolved (in order) from: next to this script, a sibling nrfutil/
# dir, the release-package tools/nrfutil/, C:\nrfutil\, then PATH. If a bundled
# nrfutil with its own home is found, NRFUTIL_HOME is pointed at it, so the
# mcu-manager plugin is used with zero install.
#
# Usage:
#   .\xiao_nrf54lm20b_flash.ps1                                # default firmware/*.signed.bin
#   .\xiao_nrf54lm20b_flash.ps1 -Firmware other.bin
#   .\xiao_nrf54lm20b_flash.ps1 -Port COM22                    # skip auto-detect
param(
    [string]$Firmware = "",
    [string]$Port = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# ---- resolve firmware -------------------------------------------------------
if (-not $Firmware) {
    foreach ($c in @((Join-Path $ScriptDir '..\firmware\zephyr.signed.bin'),
                     (Join-Path $ScriptDir 'zephyr.signed.bin'))) {
        if (Test-Path -LiteralPath $c) { $Firmware = $c; break }
    }
}
if (-not $Firmware) { $Firmware = Read-Host "Path to signed image (.bin)" }
if (-not (Test-Path -LiteralPath $Firmware)) { throw "Firmware not found: $Firmware" }
$Firmware = (Resolve-Path -LiteralPath $Firmware).Path

# ---- resolve nrfutil --------------------------------------------------------
$Nrfutil = $null
$candidates = @(
    (Join-Path $ScriptDir 'nrfutil.exe'),
    (Join-Path $ScriptDir '..\nrfutil\nrfutil.exe'),
    (Join-Path $ScriptDir '..\tools\nrfutil\nrfutil.exe'),
    'C:\nrfutil\nrfutil.exe'
)
foreach ($c in $candidates) {
    if (Test-Path -LiteralPath $c) { $Nrfutil = (Resolve-Path -LiteralPath $c).Path; break }
}
if ($Nrfutil) {
    $homeDir = Join-Path (Split-Path -Parent $Nrfutil) 'home'
    if (Test-Path -LiteralPath $homeDir) { $env:NRFUTIL_HOME = (Resolve-Path -LiteralPath $homeDir).Path }
} else {
    $cmd = Get-Command nrfutil.exe -ErrorAction SilentlyContinue
    if ($cmd) { $Nrfutil = $cmd.Source } else { throw "nrfutil.exe not found (neither bundled nor on PATH)." }
}
Write-Host "nrfutil: $Nrfutil"
if ($env:NRFUTIL_HOME) { Write-Host "NRFUTIL_HOME: $env:NRFUTIL_HOME" }

# ---- find the loader port (VID:PID 2886:0013) -------------------------------
function Find-LoaderPort {
    $devs = Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue |
        Where-Object { $_.DeviceID -match 'VID_2886.*PID_0013' }
    foreach ($d in $devs) {
        if ($d.Name -match '\((COM\d+)\)') { return $Matches[1] }
    }
    return $null
}

if (-not $Port) {
    Write-Host ""
    Write-Host ">> Enter DFU mode: HOLD the USER button, press RESET, then release USER."
    Write-Host ">> Looking for loader USB CDC (2886:0013) ..."
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
        $Port = Find-LoaderPort
        if ($Port) { Write-Host "[OK] Loader found on $Port"; break }
        Start-Sleep -Milliseconds 700
    }
    if (-not $Port) { throw "Loader (2886:0013) not found. Hold USER while pressing RESET." }
}

# ---- upload -----------------------------------------------------------------
Write-Host ""
Write-Host "Firmware: $Firmware"
Write-Host "Port:     $Port"
Write-Host ""
& $Nrfutil mcu-manager serial image-upload --serial-port $Port --timeout 60 --firmware $Firmware
if ($LASTEXITCODE -ne 0) { throw "image-upload failed (exit $LASTEXITCODE)." }

try {
    & $Nrfutil mcu-manager serial reset --serial-port $Port --timeout 60
} catch {
    Write-Warning "Upload finished, but reset did not complete. Press RESET manually."
}

Write-Host ""
Write-Host "[DONE] Upload complete. The board should boot the new application."
