#!/usr/bin/env bash
# Linux/macOS launcher for PixelPal.
# Creates a local virtualenv on first run, then launches the app.
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Setting up virtual environment (first run only)..."
    python3 -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    pip install --upgrade pip >/dev/null
    pip install -e .
else
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

exec python -m pixelpal.main "$@"
