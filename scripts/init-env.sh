#!/usr/bin/env sh
set -eu

PROVIDER="${PROVIDER:-openrouter}"
MODEL="${MODEL:-openai/gpt-4.1}"
TARGET_TESTS="${TARGET_TESTS:-40}"
ITERATIONS="${ITERATIONS:-3}"
CANDIDATES="${CANDIDATES:-4}"
PASS_K="${PASS_K:-4}"
OUTPUT_DIR="${OUTPUT_DIR:-runs/latest}"
OPENROUTER_VALUE="${OPENROUTER_API_KEY:-PASTE_OPENROUTER_API_KEY_HERE}"
GIGACHAT_VALUE="${GIGACHAT_CREDENTIALS:-PASTE_GIGACHAT_CREDENTIALS_HERE}"
GIGACHAT_BASE_VALUE="${GIGACHAT_BASE_URL:-PASTE_GIGACHAT_BASE_URL_HERE}"
FORCE="${FORCE:-0}"

if [ "$PROVIDER" = "gigachat" ] && [ "$MODEL" = "openai/gpt-4.1" ]; then
  MODEL="GigaChat-Pro"
fi

write_file() {
  path="$1"
  content="$2"
  if [ -f "$path" ] && [ "$FORCE" != "1" ]; then
    echo "$path already exists. Set FORCE=1 to overwrite."
    return
  fi
  printf "%s\n" "$content" > "$path"
  echo "Wrote $path"
}

write_file ".env" "OPENROUTER_API_KEY=$OPENROUTER_VALUE
GIGACHAT_CREDENTIALS=$GIGACHAT_VALUE
GIGACHAT_BASE_URL=$GIGACHAT_BASE_VALUE"

write_file "prompt-evolve.yaml" "provider: $PROVIDER
model: $MODEL

target_tests: $TARGET_TESTS
iterations: $ITERATIONS
candidates: $CANDIDATES
pass_k: $PASS_K
reasoning: max
self_check: true
user_tests_only: false

output:
  dir: $OUTPUT_DIR
  save_markdown_report: true
  save_json_report: true
  save_final_prompt: true

openrouter:
  api_key_env: OPENROUTER_API_KEY
  base_url: https://openrouter.ai/api/v1

gigachat:
  enabled: true
  credentials_env: GIGACHAT_CREDENTIALS
  base_url: $GIGACHAT_BASE_VALUE"

echo ""
echo "Initialization complete."
echo "Next steps:"
echo "1. Edit .env and replace PASTE_* placeholders with real secrets."
echo "2. Run: prompt-evolve run --config prompt-evolve.yaml --task examples/task.md"
echo "3. Docker: docker compose run --rm prompt-evolve run --config prompt-evolve.yaml --task examples/task.md"
