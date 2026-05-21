#!/usr/bin/env sh
set -eu

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
PYTHON_EXE="$VENV_DIR/bin/python"

if [ "${RECREATE:-0}" = "1" ] && [ -d "$VENV_DIR" ]; then
  echo "Removing existing .venv..."
  rm -rf "$VENV_DIR"
fi

if [ ! -x "$PYTHON_EXE" ]; then
  echo "Creating local virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

echo "Upgrading pip in .venv..."
"$PYTHON_EXE" -m pip install --upgrade pip

echo "Installing Prompt Evolution CLI in editable mode inside .venv..."
"$PYTHON_EXE" -m pip install -e "$PROJECT_ROOT[dev]"

echo ""
echo "Local setup complete."
echo "Run CLI with:"
echo "  sh scripts/run-local.sh run --config prompt-evolve.yaml --task examples/task.md"
echo ""
echo "Or activate the venv:"
echo "  . .venv/bin/activate"
echo "  prompt-evolve --help"
