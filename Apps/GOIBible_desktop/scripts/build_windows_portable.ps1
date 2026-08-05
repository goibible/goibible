$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Test-Path ".venv")) {
    py -3 -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements-windows.txt

$DataBackup = $null
if (Test-Path "dist\GOIBible\data") {
    $DataBackup = Join-Path ([System.IO.Path]::GetTempPath()) ("GOIBibleData_" + [System.Guid]::NewGuid())
    New-Item -ItemType Directory -Path $DataBackup | Out-Null
    Copy-Item "dist\GOIBible\data" "$DataBackup\data" -Recurse
}

& .\.venv\Scripts\pyinstaller.exe `
    --noconfirm `
    --windowed `
    --name GOIBible `
    --icon "goibible\resources\goibible-icon.ico" `
    --add-data "goibible\resources;goibible\resources" `
    run.py

if ($DataBackup) {
    if (Test-Path "dist\GOIBible\data") {
        Remove-Item "dist\GOIBible\data" -Recurse -Force
    }
    Copy-Item "$DataBackup\data" "dist\GOIBible\data" -Recurse
    Remove-Item $DataBackup -Recurse -Force
}

Copy-Item "goibible\resources\goibible-icon.ico" "dist\GOIBible\goibible-icon.ico" -Force
Write-Host "Windows portable build: $Root\dist\GOIBible"
