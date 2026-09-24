#!/usr/bin/env python3
"""Normalize Louis Segond 1910 (eBible fraLSG VPL) onto the GOI/KJV verse spine, verified by content.

eBible's LSG is a versification hybrid: KJV numbering in most books, Hebrew (BHS) numbering for Psalm
titles, and its own divisions in a few places (ECC 11-12, JOB 38-41, ...). Naive address matching
silently pairs the wrong French verse with a GOI coordinate from any shift point to the end of a chapter
(the Russian RUSSYN lesson), so every coordinate here is checked by content, not only the chapters whose
verse counts differ.

Method
  1. Embed every LSG verse and every KJV verse with the local Qwen3-Embedding-8B server (llama.cpp,
     http://127.0.0.1:12025; first 1024 dims, L2-normalised; cache in .embed_cache.npz, ignored).
  2. Chapters whose verse set equals the KJV chapter map by address ("exact").
  3. Runs of consecutive differing chapters are aligned by an order-preserving, banded dynamic program
     over 1:1, 2:1, 3:1 (French verses joined into one KJV verse, e.g. Psalm titles) and 1:2 (one French
     verse spanning two KJV verses; both coordinates carry that text), scored by cosine similarity.
  4. Every mapped coordinate gets a similarity score. It is flagged `review` if the score is below
     --review-below, or if the French text matches an ADJACENT KJV verse clearly better than its own
     (a hidden boundary shift).
Outputs
  One_Directory_LSG1910_GOI/<NNN>_<BOOK>_<CCC>_<VVV>_LSG1910.txt   exactly the 31,102 KJV coordinates
  alignment_exceptions.csv   every non-exact or flagged coordinate (playbook columns + similarity)
  alignment_report.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KJV_DIR = ROOT / "Reference_Bible/English_Bible_KJV/One_Directory_KJV"
ZIP = HERE / "source/fraLSG_vpl.zip"
MEMBER = "fraLSG_vpl.txt"
OUT = HERE / "One_Directory_LSG1910_GOI"
EXC = HERE / "alignment_exceptions.csv"
REPORT = HERE / "alignment_report.json"
CACHE = HERE / ".embed_cache.npz"
ENDPOINT = "http://127.0.0.1:12025/v1/embeddings"
DIM = 1024
BAND = 12
# Chapters with equal verse COUNTS but shifted CONTENT, found by the neighbour test on a first pass.
EXTRA_CHAPTERS = {("PSA", 13)}
# Verses LSG (following the critical text) presents in a different ORDER; an order-preserving alignment cannot
# express a swap, so these are mapped explicitly (GOI coordinate -> LSG coordinate).
REORDER = {("PHP", 1, 16): ("PHP", 1, 17), ("PHP", 1, 17): ("PHP", 1, 16)}
# Flagged coordinates read by hand (French vs KJV) and judged correctly aligned; the flag came from free
# paraphrase, a textual variant, or a partial boundary difference, not a misalignment.
HAND_REVIEWED = {
    **{k: "hand-reviewed: correct verse; low score from free paraphrase (poetry/lists)" for k in [
        ("GEN", 36, 41), ("EXO", 21, 25), ("EXO", 27, 14), ("EXO", 35, 17), ("LEV", 11, 14), ("LEV", 14, 56),
        ("LEV", 24, 12), ("NUM", 2, 26), ("DEU", 14, 13), ("JDG", 17, 11), ("2KI", 4, 11), ("1CH", 1, 52),
        ("1CH", 9, 43), ("2CH", 4, 14), ("JOB", 3, 8), ("JOB", 6, 10), ("JOB", 6, 16), ("JOB", 6, 19),
        ("JOB", 6, 21), ("JOB", 6, 22), ("JOB", 9, 21), ("JOB", 11, 10), ("JOB", 12, 5), ("JOB", 13, 9),
        ("JOB", 16, 21), ("JOB", 17, 5), ("JOB", 18, 9), ("JOB", 18, 21), ("JOB", 19, 17), ("JOB", 21, 23),
        ("JOB", 22, 20), ("JOB", 22, 21), ("JOB", 23, 6), ("JOB", 27, 12), ("JOB", 28, 4), ("JOB", 33, 16),
        ("JOB", 33, 19), ("JOB", 34, 14), ("JOB", 34, 27), ("JOB", 35, 15), ("JOB", 36, 15), ("JOB", 36, 17),
        ("JOB", 36, 19), ("JOB", 37, 13), ("JOB", 40, 24), ("JOB", 41, 13), ("JOB", 41, 22), ("PSA", 3, 2),
        ("PSA", 55, 2), ("PSA", 58, 9), ("PSA", 64, 6), ("PSA", 73, 4), ("PSA", 73, 7), ("PSA", 74, 5),
        ("PSA", 81, 15), ("PSA", 87, 7), ("PRO", 9, 4), ("PRO", 9, 16), ("PRO", 21, 4), ("PRO", 26, 10),
        ("PRO", 30, 31), ("SNG", 6, 7), ("ISA", 3, 23), ("ISA", 19, 10), ("ISA", 27, 8), ("ISA", 29, 21),
        ("ISA", 32, 8), ("ISA", 32, 12), ("JER", 25, 35), ("EZK", 24, 12), ("EZK", 27, 20), ("HOS", 5, 2),
        ("JOL", 2, 8), ("HAB", 1, 7), ("HAB", 1, 11), ("ZEP", 2, 1), ("LUK", 21, 19), ("1CO", 15, 33),
        ("2CO", 2, 5), ("1TI", 4, 2), ("HEB", 2, 16), ("JUD", 1, 19)]},
    **{k: "hand-reviewed: correct verse; LSG verse boundary differs slightly (part of a neighbour verse moved)" for k in [
        ("LEV", 13, 35), ("1KI", 18, 34), ("MAT", 14, 2), ("MAT", 26, 33), ("ACT", 3, 20), ("ACT", 15, 18),
        ("ACT", 24, 3), ("ROM", 1, 31), ("2CO", 8, 13)]},
    ("MRK", 9, 44): "hand-reviewed: textual variant -- LSG (critical text) has no 'worm' verse; its 9:44 is the end of KJV 9:43",
    ("JUD", 1, 22): "hand-reviewed: textual variant -- LSG follows the critical text of Jude 22",
}
BOOK_CODE_MAP = {"1JO": "1JN", "2JO": "2JN", "3JO": "3JN", "EZE": "EZK", "JAM": "JAS", "JOE": "JOL",
                 "JOH": "JHN", "MAR": "MRK", "NAH": "NAM", "PHI": "PHP", "SOL": "SNG"}
LINE = re.compile(r"^([1-3]?[A-Z]{2,3})\s+(\d+):(\d+)\s+(.*)$")


def norm(t):
    t = unicodedata.normalize("NFC", t).replace(" ", " ")
    return re.sub(r"\s+", " ", t).strip()


def load_lsg():
    raw = zipfile.ZipFile(ZIP).read(MEMBER).decode("utf-8")
    verses = {}
    for n, line in enumerate(raw.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        m = LINE.match(line)
        if not m:
            raise SystemExit(f"{MEMBER}:{n}: unparseable: {line[:80]!r}")
        b, c, v, t = m.groups()
        key = (BOOK_CODE_MAP.get(b, b), int(c), int(v))
        if key in verses:
            raise SystemExit(f"{MEMBER}:{n}: duplicate {key}")
        verses[key] = norm(t)
    return verses


def load_kjv():
    verses, prefix = {}, {}
    for p in sorted(KJV_DIR.glob("*_KJV.txt")):
        pre, b, c, v, _ = p.stem.split("_")
        verses[(b, int(c), int(v))] = norm(p.read_text(encoding="utf-8"))
        prefix[(b, int(c), int(v))] = pre
    if len(verses) != 31102:
        raise SystemExit(f"KJV spine has {len(verses)} verses, expected 31102")
    return verses, prefix


class Embedder:
    def __init__(self):
        self.vec = {}
        if CACHE.exists():
            z = np.load(CACHE, allow_pickle=False)
            for t, v in zip(z["texts"], z["vecs"]):
                self.vec[str(t)] = v.astype(np.float32)

    def fill(self, texts):
        need = [t for t in dict.fromkeys(texts) if t not in self.vec]
        for i in range(0, len(need), 64):
            batch = need[i:i + 64]
            req = urllib.request.Request(ENDPOINT, data=json.dumps({"input": batch}).encode(),
                                         headers={"Content-Type": "application/json"})
            data = sorted(json.load(urllib.request.urlopen(req, timeout=900))["data"], key=lambda d: d["index"])
            for t, d in zip(batch, data):
                v = np.asarray(d["embedding"][:DIM], dtype=np.float32)
                self.vec[t] = v / (np.linalg.norm(v) or 1.0)
            if (i // 64) % 50 == 0:
                print(f"  embedded {i + len(batch)}/{len(need)}", flush=True)
        if need:
            texts_ = list(self.vec)
            np.savez(CACHE, texts=np.array(texts_), vecs=np.stack([self.vec[t] for t in texts_]).astype(np.float16))

    def __getitem__(self, t):
        return self.vec[t]


def align_block(fr, en, E):
    """Banded DP. fr/en: lists of (key, text). Returns [(fr_keys, en_keys, score)]."""
    F, N = len(fr), len(en)
    fj = lambda i, k: " ".join(t for _, t in fr[i - k:i])
    ej = lambda j, k: " ".join(t for _, t in en[j - k:j])
    ops = [(1, 1, 0.0), (2, 1, 0.06), (3, 1, 0.10), (1, 2, 0.06)]
    NEG = -1e9
    best = np.full((F + 1, N + 1), NEG)
    back = {}
    best[0, 0] = 0.0
    for i in range(F + 1):
        centre = i * N / max(F, 1)
        for j in range(max(0, int(centre) - BAND), min(N, int(centre) + BAND) + 1):
            if best[i, j] == NEG:
                continue
            for df, de, pen in ops:
                ni, nj = i + df, j + de
                if ni > F or nj > N:
                    continue
                s = float(E[fj(ni, df)] @ E[ej(nj, de)])
                if best[i, j] + s - pen > best[ni, nj]:
                    best[ni, nj] = best[i, j] + s - pen
                    back[(ni, nj)] = (i, j, s)
    if best[F, N] == NEG:
        raise RuntimeError(f"no alignment path for block starting {fr[0][0]}")
    out, i, j = [], F, N
    while (i, j) != (0, 0):
        pi, pj, s = back[(i, j)]
        out.append(([k for k, _ in fr[pi:i]], [k for k, _ in en[pj:j]], s))
        i, j = pi, pj
    return out[::-1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--review-below", type=float, default=0.55)
    ap.add_argument("--neighbour-margin", type=float, default=0.08)
    args = ap.parse_args()

    lsg = load_lsg()
    kjv, prefix = load_kjv()
    order = sorted(kjv, key=lambda k: (prefix[k], k[1], k[2]))
    book_rank = {}
    for k in order:
        book_rank.setdefault(k[0], len(book_rank))
    chap_fr, chap_en = defaultdict(set), defaultdict(set)
    for b, c, v in lsg:
        chap_fr[(b, c)].add(v)
    for b, c, v in kjv:
        chap_en[(b, c)].add(v)
    differ = {k for k in set(chap_en) | set(chap_fr) if chap_en.get(k) != chap_fr.get(k)}
    # pad by one chapter each side: a boundary shift can move material into a neighbour whose COUNT is unchanged
    # (ISA 63:19 carries KJV 64:1). EXTRA_CHAPTERS holds chapters added by the neighbour test (PSA 13: same count,
    # but LSG numbers the title as verse 1, so every verse was off by one).
    padded = set(differ) | set(EXTRA_CHAPTERS)
    for b, c in list(padded):
        for d in (-1, 1):
            if (b, c + d) in chap_en:
                padded.add((b, c + d))
    blocks = []
    for b, c in sorted(padded, key=lambda k: (book_rank[k[0]], k[1])):
        if blocks and blocks[-1][0] == b and blocks[-1][1][-1] == c - 1:
            blocks[-1][1].append(c)
        else:
            blocks.append((b, [c]))
    in_block = {(b, c) for b, run in blocks for c in run}

    E = Embedder()
    texts = list(lsg.values()) + list(kjv.values())
    for b, run in blocks:
        fr = [lsg[k] for k in sorted(k for k in lsg if k[0] == b and k[1] in run)]
        en = [kjv[k] for k in sorted(k for k in kjv if k[0] == b and k[1] in run)]
        texts += [" ".join(fr[i - k:i]) for k in (2, 3) for i in range(k, len(fr) + 1)]
        texts += [" ".join(en[j - 2:j]) for j in range(2, len(en) + 1)]
    E.fill(texts)

    mapping = {}
    for k in kjv:
        if (k[0], k[1]) not in in_block:
            if k not in lsg:
                raise SystemExit(f"exact chapter missing verse {k}")
            mapping[k] = ([k], "exact", float(E[lsg[k]] @ E[kjv[k]]))
    for b, run in blocks:
        fr = [(k, lsg[k]) for k in sorted(k for k in lsg if k[0] == b and k[1] in run)]
        en = [(k, kjv[k]) for k in sorted(k for k in kjv if k[0] == b and k[1] in run)]
        for fks, eks, s in align_block(fr, en, E):
            if len(eks) == 1:
                rel = "exact" if fks == eks else ("merged" if len(fks) > 1 else "shifted")
                mapping[eks[0]] = (fks, rel, s)
            else:
                for ek in eks:
                    mapping[ek] = (fks, "split", s)

    for goi, ref in REORDER.items():
        mapping[goi] = ([ref], "reordered", float(E[lsg[ref]] @ E[kjv[goi]]))

    # neighbour test: does this French text match an adjacent KJV verse clearly better than its own?
    pos = {k: i for i, k in enumerate(order)}
    rows, flagged = [], 0
    for k in order:
        fks, rel, s = mapping.get(k, ([], "missing", 0.0))
        ftext = " ".join(lsg[f] for f in fks)
        why = []
        if s < args.review_below:
            why.append(f"low similarity {s:.3f}")
        if fks and rel in ("exact", "shifted"):
            fv = E[ftext] if ftext in E.vec else None
            if fv is not None:
                for d in (-1, 1):
                    n = pos[k] + d
                    if 0 <= n < len(order) and order[n][0] == k[0]:
                        ns = float(fv @ E[kjv[order[n]]])
                        if ns > s + args.neighbour_margin:
                            why.append(f"neighbour {order[n][1]}:{order[n][2]} scores {ns:.3f} > own {s:.3f}")
        status = "review" if why else "resolved"
        if why and k in HAND_REVIEWED:
            why.append(HAND_REVIEWED[k])
            status = "resolved"
        flagged += status == "review"
        if rel == "exact" and not why:
            continue
        reason = {"exact": "address match", "merged": "LSG numbers this material as separate verses (e.g. Psalm title); joined to one KJV verse",
                  "shifted": "chapter/verse boundary differs from KJV; content-aligned",
                  "split": "one LSG verse spans two KJV verses; text shared by both coordinates",
                  "missing": "no LSG content aligned",
                  "reordered": "LSG (critical text) presents these verses in a different order; mapped explicitly"}[rel]
        if why:
            reason += " | " + "; ".join(why)
        ref = ";".join(f"{fc}:{fv}" for _, fc, fv in fks)
        rows.append([prefix[k], k[0], k[1], k[2], fks[0][0] if fks else "", fks[0][1] if fks else "", ref,
                     rel, reason, "Claude (Qwen3 embedding DP)", status, f"{s:.3f}"])
    missing = [k for k in kjv if k not in mapping]
    used = {f for fks, _, _ in mapping.values() for f in fks}
    unused = sorted(set(lsg) - used)
    sims = np.array([m[2] for m in mapping.values()])
    report = {"source": "eBible fraLSG (Louis Segond 1910) VPL", "lsg_verses": len(lsg),
              "kjv_coordinates": len(kjv), "mapped": len(mapping), "missing": len(missing),
              "lsg_verses_unused": [f"{b} {c}:{v}" for b, c, v in unused],
              "differing_chapters": len(differ), "content_aligned_blocks": [f"{b} {r[0]}-{r[-1]}" for b, r in blocks],
              "relations": {r: sum(1 for m in mapping.values() if m[1] == r) for r in ("exact", "shifted", "merged", "split", "reordered")},
              "similarity": {"min": round(float(sims.min()), 3), "p01": round(float(np.percentile(sims, 1)), 3),
                             "median": round(float(np.median(sims)), 3)},
              "flagged_review": flagged}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with EXC.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["goi_ordinal", "book", "chapter", "verse", "reference_book", "reference_chapter",
                    "reference_verse", "relation", "reason", "reviewer", "status", "similarity"])
        w.writerows(rows)
    if args.write:
        if missing:
            raise SystemExit(f"refusing to write: {len(missing)} GOI coordinates unmapped")
        OUT.mkdir(exist_ok=True)
        for k, (fks, _, _) in mapping.items():
            text = " ".join(lsg[f] for f in fks)
            if not text.strip():
                raise SystemExit(f"empty text for {k}")
            (OUT / f"{prefix[k]}_{k[0]}_{k[1]:03d}_{k[2]:03d}_LSG1910.txt").write_text(text + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("content_aligned_blocks",)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
