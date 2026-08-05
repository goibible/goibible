#!/usr/bin/env python3
"""Normalize the punctuation/whitespace of a verse corpus to a single canonical form.

Plumbing rule: the *data layer* uses unambiguous characters so that search,
tokenization, diffing and downstream parsers behave identically across tools and
languages. Typographic quotes are a *presentation* concern — render them later
if wanted; do not store them.

Canonical form:
  - double quotes  “ ” „ ‟ « »            -> "  (straight ASCII)
  - single/apostr. ‘ ’ ‚ ‛ ‹ ›            -> '  (straight ASCII)
  - en-dash – , horizontal bar ―          -> —  (one canonical em-dash)
  - ellipsis …                            -> ...
  - non-breaking / zero-width spaces       -> normal space / removed
  - collapse runs of spaces, strip line-trailing spaces
  - NFC unicode normalization
  - exactly one trailing newline

Idempotent. Run again any time; a clean corpus reports 0 changes.

Usage:
  python3 tools/normalize_corpus.py [--dir GOI_Bible/GOI_Bible_English] [--check]
    --check : report violations and exit 1 if any (no writes) — for CI/validate.
"""
import argparse, pathlib, re, sys, unicodedata

DOUBLE = dict.fromkeys("“”„‟«»", '"')
SINGLE = dict.fromkeys("‘’‚‛‹›", "'")
DASH   = {"–": "—", "―": "—"}          # en-dash, bar -> em-dash
SPACE  = {" ": " ", " ": " ", " ": " "}      # nbsp variants -> space
REMOVE = dict.fromkeys("​‌‍﻿", "")      # zero-width chars
TRANS  = {**DOUBLE, **SINGLE, **DASH, **SPACE, **REMOVE}

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.translate(str.maketrans(TRANS))
    text = text.replace("…", "...")
    text = "\n".join(re.sub(r"[ \t]+", " ", ln).rstrip() for ln in text.split("\n"))
    return text.rstrip("\n") + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="GOI_Bible/GOI_Bible_English")
    ap.add_argument("--check", action="store_true", help="report only; exit 1 on any violation")
    args = ap.parse_args()
    d = pathlib.Path(args.dir)
    files = sorted(d.glob("*.txt"))
    changed = []
    for f in files:
        raw = f.read_text(encoding="utf-8")
        norm = normalize(raw)
        if norm != raw:
            changed.append(f.name)
            if not args.check:
                f.write_text(norm, encoding="utf-8")
    if args.check:
        print(f"{args.dir}: {len(changed)} file(s) not in canonical form" +
              (f" (e.g. {changed[:5]})" if changed else ""))
        sys.exit(1 if changed else 0)
    print(f"{args.dir}: normalized {len(changed)} of {len(files)} files.")

if __name__ == "__main__":
    main()
