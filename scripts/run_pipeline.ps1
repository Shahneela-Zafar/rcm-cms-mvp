$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"

& $Python -m src.data.load_ma_scp
& $Python -m src.models.forecast_prophet
& $Python -m src.models.pa_classifier
& $Python -m src.models.delay_predictor
& $Python -m src.models.evaluate

Write-Host "Pipeline complete."

