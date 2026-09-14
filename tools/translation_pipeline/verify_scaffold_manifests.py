#!/usr/bin/env python3
"""Verify optional tracked source manifests for language reference scaffolds.

Each `Reference_Bible/**/SOURCE_MANIFEST.json` lists preserved files as
`{"path": "source/file", "bytes": 123, "sha256": "..."}`. A scaffold may
not claim readiness until this verifier passes for its manifest.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    manifests = sorted((ROOT / "Reference_Bible").glob("**/SOURCE_MANIFEST.json"))
    errors: list[str] = []
    for manifest in manifests:
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            files = data["files"]
            if data.get("rights_status") not in {"verified_public_domain", "licensed"}:
                errors.append(f"{manifest.relative_to(ROOT)}: rights_status is not distributable")
            for item in files:
                path = manifest.parent / item["path"]
                if not path.is_file() or path.stat().st_size == 0:
                    errors.append(f"{manifest.relative_to(ROOT)}: missing or empty {item['path']}")
                elif path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
                    errors.append(f"{manifest.relative_to(ROOT)}: integrity mismatch {item['path']}")
            print(f"OK {manifest.relative_to(ROOT)}: {len(files)} preserved files")
        except (KeyError, TypeError, ValueError, OSError) as exc:
            errors.append(f"{manifest.relative_to(ROOT)}: invalid manifest ({exc})")
    if errors:
        print("SCAFFOLD MANIFEST FAILED", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"SCAFFOLD MANIFEST OK: {len(manifests)} manifests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
