$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$LogDir = Join-Path $Root "logs"
$StdoutLog = Join-Path $LogDir "jupyter.stdout.log"
$StderrLog = Join-Path $LogDir "jupyter.stderr.log"
$Port = 8899
$Token = "rcm-cms-mvp"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Args = @(
    "-m", "jupyter", "lab",
    "--no-browser",
    "--ip=127.0.0.1",
    "--port=$Port",
    "--ServerApp.token=$Token",
    "--ServerApp.password="
)

Start-Process `
    -FilePath $Python `
    -ArgumentList $Args `
    -WorkingDirectory $Root `
    -RedirectStandardOutput $StdoutLog `
    -RedirectStandardError $StderrLog `
    -WindowStyle Hidden

Write-Host "Jupyter Lab started."
Write-Host "Open: http://127.0.0.1:$Port/lab/tree/notebooks/01_data_inventory_and_quality.ipynb?token=$Token"
Write-Host "Stdout log: $StdoutLog"
Write-Host "Stderr log: $StderrLog"
