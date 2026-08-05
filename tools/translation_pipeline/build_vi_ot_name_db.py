#!/usr/bin/env python3
"""Compatibility wrapper for the generic OT name database builder."""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def main() -> int:
    args = ["python3", str(ROOT / "tools" / "translation_pipeline" / "build_ot_name_db.py"), "--profile", "vi", *sys.argv[1:]]
    return subprocess.call(args)


if __name__ == "__main__":
    raise SystemExit(main())
