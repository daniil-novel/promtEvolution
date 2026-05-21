#!/usr/bin/env sh
set -eu

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PYTHON_EXE="$PROJECT_ROOT/.venv/bin/python"

if [ -x "$PYTHON_EXE" ]; then
  exec "$PYTHON_EXE" -m prompt_evolve.cli "$@"
fi

echo "Local .venv was not found. Falling back to current Python."
echo "For an isolated setup, run: sh scripts/setup-local.sh"
exec python3 -m prompt_evolve.cli "$@"
