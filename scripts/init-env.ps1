param(
    [ValidateSet("openrouter", "gigachat", "mock")]
    [string]$Provider = "openrouter",
    [string]$Model = "openai/gpt-4.1",
    [int]$TargetTests = 40,
    [int]$Iterations = 3,
    [int]$Candidates = 4,
    [int]$PassK = 4,
    [string]$OutputDir = "runs/latest",
    [string]$OpenRouterApiKey = $env:OPENROUTER_API_KEY,
    [string]$GigaChatCredentials = $env:GIGACHAT_CREDENTIALS,
    [string]$GigaChatBaseUrl = $env:GIGACHAT_BASE_URL,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-FileIfAllowed {
    param(
        [string]$Path,
        [string]$Content
    )
    if ((Test-Path $Path) -and -not $Force) {
        Write-Host "$Path already exists. Use -Force to overwrite."
        return
    }
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force $parent | Out-Null
    }
    Set-Content -Path $Path -Value $Content -Encoding UTF8
    Write-Host "Wrote $Path"
}

if ($Provider -eq "gigachat" -and $Model -eq "openai/gpt-4.1") {
    $Model = "GigaChat-Pro"
}

$openRouterValue = if ($OpenRouterApiKey) { $OpenRouterApiKey } else { "PASTE_OPENROUTER_API_KEY_HERE" }
$gigaCredentialsValue = if ($GigaChatCredentials) { $GigaChatCredentials } else { "PASTE_GIGACHAT_CREDENTIALS_HERE" }
$gigaBaseUrlValue = if ($GigaChatBaseUrl) { $GigaChatBaseUrl } else { "PASTE_GIGACHAT_BASE_URL_HERE" }

$envContent = @"
OPENROUTER_API_KEY=$openRouterValue
GIGACHAT_CREDENTIALS=$gigaCredentialsValue
GIGACHAT_BASE_URL=$gigaBaseUrlValue
"@

$configContent = @"
provider: $Provider
model: $Model

target_tests: $TargetTests
iterations: $Iterations
candidates: $Candidates
pass_k: $PassK
reasoning: max
self_check: true
user_tests_only: false

output:
  dir: $OutputDir
  save_markdown_report: true
  save_json_report: true
  save_final_prompt: true

openrouter:
  api_key_env: OPENROUTER_API_KEY
  base_url: https://openrouter.ai/api/v1

gigachat:
  enabled: true
  credentials_env: GIGACHAT_CREDENTIALS
  base_url: $gigaBaseUrlValue
"@

Write-FileIfAllowed -Path ".env" -Content $envContent
Write-FileIfAllowed -Path "prompt-evolve.yaml" -Content $configContent

Write-Host ""
Write-Host "Initialization complete."
Write-Host "Next steps:"
Write-Host "1. Edit .env and replace PASTE_* placeholders with real secrets."
Write-Host "2. Run: prompt-evolve run --config prompt-evolve.yaml --task examples/task.md"
Write-Host "3. Docker: docker compose run --rm prompt-evolve run --config prompt-evolve.yaml --task examples/task.md"
