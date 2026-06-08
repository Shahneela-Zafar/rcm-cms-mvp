$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
& $Python -m streamlit run .\src\dashboard\app.py
