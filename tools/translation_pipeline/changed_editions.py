#!/usr/bin/env python3
"""Print the active GOI edition IDs whose flatfiles or download DB changed between BASE and HEAD (all active GOI editions if BASE is empty/zero).
Used by CI so each edition is verified on its own and one language's work in progress never fails another's push.   python3 changed_editions.py [BASE]"""
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
base = sys.argv[1] if len(sys.argv) > 1 else ""
cat = [e for e in json.loads((ROOT / "Meta_Bible_Data/sqlite/editions.json").read_text(encoding="utf-8")) if e["status"] == "active" and e["edition_id"].startswith("GOI_")]
if not base or set(base) == {"0"}:
    print(" ".join(e["edition_id"] for e in cat)); raise SystemExit
files = subprocess.run(["git", "diff", "--name-only", base, "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
out = []
for e in cat:
    pre = (e["flatfile_dir"].rstrip("/") + "/", f"Meta_Bible_Data/goi_db_download/{e['edition_id']}.db")
    if any(f.startswith(pre[0]) or f == pre[1] for f in files): out.append(e["edition_id"])
print(" ".join(out))
