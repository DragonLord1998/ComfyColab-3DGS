#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON:-python3}"

"$PYTHON_BIN" -m compileall -q custom_nodes runtime scripts tests
PYTHONPATH="$ROOT" "$PYTHON_BIN" -m unittest discover -s tests -t . -v
"$PYTHON_BIN" runtime/doctor.py
"$PYTHON_BIN" -m json.tool comfycolab-pack.json >/dev/null
for path in workflows/*.json docs/*.json; do
  "$PYTHON_BIN" -m json.tool "$path" >/dev/null
done
