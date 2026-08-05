#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

unset LD_LIBRARY_PATH
exec "${PYTHON:-.venv/bin/python}" run.py
