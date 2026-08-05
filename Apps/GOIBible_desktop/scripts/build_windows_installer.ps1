$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

& "$PSScriptRoot\build_windows_portable.ps1"

$Makensis = Get-Command makensis.exe -ErrorAction SilentlyContinue
if (-not $Makensis) {
    $DefaultNsis = "${env:ProgramFiles(x86)}\NSIS\makensis.exe"
    if (Test-Path $DefaultNsis) {
        $Makensis = Get-Item $DefaultNsis
    }
}

if (-not $Makensis) {
    throw "NSIS makensis.exe was not found. Install NSIS from https://nsis.sourceforge.io/Download, then rerun this script."
}

& $Makensis.Source "installer\goibible.nsi"
Write-Host "Installer: $Root\dist\goibible_install.exe"
