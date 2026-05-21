param(
    [switch]$Recreate
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvDir = Join-Path $ProjectRoot ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

if ($Recreate -and (Test-Path $VenvDir)) {
    Write-Host "Removing existing .venv..."
    Remove-Item -Recurse -Force $VenvDir
}

if (-not (Test-Path $PythonExe)) {
    Write-Host "Creating local virtual environment..."
    python -m venv $VenvDir
}

Write-Host "Upgrading pip in .venv..."
& $PythonExe -m pip install --upgrade pip

Write-Host "Installing Prompt Evolution CLI in editable mode inside .venv..."
& $PythonExe -m pip install -e "$ProjectRoot[dev]"

Write-Host ""
Write-Host "Local setup complete."
Write-Host "Run CLI with:"
Write-Host "  .\scripts\run-local.ps1 run --config prompt-evolve.yaml --task examples/task.md"
Write-Host ""
Write-Host "Or activate the venv:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  prompt-evolve --help"
