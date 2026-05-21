$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    & $VenvPython -m prompt_evolve.cli @args
    exit $LASTEXITCODE
}

Write-Host "Local .venv was not found. Falling back to current Python."
Write-Host "For an isolated setup, run: .\scripts\setup-local.ps1"
python -m prompt_evolve.cli @args
exit $LASTEXITCODE
