#!/usr/bin/env python3
"""Freeze unreviewed Arabic OT anchor packets; never change texts or ledgers."""
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
NIM = ROOT / 'Meta_Bible_Data/Bible_Noun_Extraction'
sys.path.insert(0, str(NIM))
from ar.run_ar_torah import ANCHORS, BOOK_NUM, OUT, SOURCE, read_anchors

effective = read_anchors()
rows = []
with ANCHORS.open(encoding='utf-8', newline='') as f:
    for row in csv.DictReader(f):
        book = row['book_code']
        if book not in BOOK_NUM:
            continue
        chapter, verse, pos = (int(row[x]) for x in ('chapter', 'verse', 'word_position'))
        key = (book, chapter, verse)
        number, surface, rendering = effective[key][pos - 1]
        assert number == int(row['strongs_num']) and surface == row['source_surface']
        if rendering:
            continue
        stem = f'{BOOK_NUM[book]}_{book}_{chapter:03d}_{verse:03d}'
        source = (SOURCE / f'{stem}_WLC.txt').read_text(encoding='utf-8')
        target = (OUT / f'{stem}_GOI_Ar.txt').read_text(encoding='utf-8')
        rows.append({'anchor': row, 'stem': stem, 'source': source.strip(),
                     'arabic': target.strip(),
                     'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                     'target_sha256': hashlib.sha256(target.encode()).hexdigest(),
                     'status': 'UNREVIEWED'})
rows.sort(key=lambda r: (int(r['stem'][:3]), int(r['anchor']['chapter']),
                         int(r['anchor']['verse']), int(r['anchor']['word_position'])))
path = Path(__file__).with_name('blank_occurrence_queue.jsonl')
path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
print(f'{len(rows)} unreviewed occurrences in {len({r["stem"] for r in rows})} verses: {path}')
