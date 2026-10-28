#!/usr/bin/env python3
"""Apply three individually reviewed OT occurrence mappings, fail closed."""
import csv, hashlib, io, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
NIM = ROOT / 'Meta_Bible_Data/Bible_Noun_Extraction'
sys.path.insert(0, str(NIM))
from ar.run_ar_torah import BOOK_NUM, OUT, OVERRIDES, SOURCE, read_anchors
from ar.run_ar_rest_nt import validate
from matcher_ar import ArabicMatcher

# Reviewed against each WLC verse and exact Arabic target span.
decisions = [
    (('EXO', 29, 40, 4), 7253, 'رُبْع', 'بِرُبْعِ', 'First Hebrew quarter is the quarter measure of oil; this is the first Arabic ربع, distinct from the later wine measure.'),
    (('EXO', 30, 16, 2), 3722, 'كَفَّارَة', 'الْكَفَّارَاتِ', 'Hebrew הכפרים identifies the atonement money; Arabic الكفارات expresses atonements.'),
]
packets = {(p['anchor']['book_code'], int(p['anchor']['chapter']), int(p['anchor']['verse']), int(p['anchor']['word_position'])): p for p in map(json.loads, (HERE/'blank_occurrence_queue.jsonl').read_text().splitlines())}
anchors = read_anchors(); matcher = ArabicMatcher(); reviewed = []
before = OVERRIDES.read_bytes()
with OVERRIDES.open(encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f, delimiter='\t'); fields = reader.fieldnames; existing = list(reader)
keys = {(r['book'], int(r['chapter']), int(r['verse']), int(r['word_position'])) for r in existing}
for key, strong, rendering, span, reason in decisions:
    book, chapter, verse, position = key
    p = packets[key]; stem = p['stem']
    target = (OUT / f'{stem}_GOI_Ar.txt').read_text(encoding='utf-8')
    source = (SOURCE / f'{stem}_WLC.txt').read_text(encoding='utf-8')
    assert hashlib.sha256(target.encode()).hexdigest() == p['target_sha256']
    assert hashlib.sha256(source.encode()).hexdigest() == p['source_sha256']
    sid, surface, old = anchors[(book, chapter, verse)][position - 1]
    assert sid == strong and not old and key not in keys
    assert target.count(span) == 1 and matcher.found(rendering, target)
    required = [rendering if i == position else term for i, (_, _, term) in enumerate(anchors[(book, chapter, verse)], 1)]
    assert not validate(target.strip(), [x for x in required if x], matcher)
    data = {'book': book, 'chapter': chapter, 'verse': verse, 'word_position': position,
            'strongs_num': strong, 'rendering': rendering,
            'sense_key': f'H{strong}.AR_CONTEXT_{book}_{chapter}_{verse}', 'reason': reason}
    existing.append({name: data.get(name, '') for name in fields})
    reviewed.append({**data, 'source_surface': surface, 'target_span': span,
                     'target_start': target.index(span), 'source_sha256': p['source_sha256'],
                     'target_sha256': p['target_sha256'], 'reason': reason})
buf = io.StringIO(newline=''); writer = csv.DictWriter(buf, fieldnames=fields, delimiter='\t', lineterminator='\n')
writer.writeheader(); writer.writerows(existing)
assert not (HERE/'exodus_second_applied.json').exists()
(HERE/'exodus_second_overrides_before.tsv').write_bytes(before)
try:
    OVERRIDES.write_text(buf.getvalue(), encoding='utf-8')
    updated = read_anchors()
    for row in reviewed:
        key = row['book'], row['chapter'], row['verse']
        assert updated[key][row['word_position']-1][2] == row['rendering']
except BaseException:
    OVERRIDES.write_bytes(before)
    raise
(HERE/'exodus_second_applied.json').write_text(json.dumps({'status':'APPLIED', 'reviewed':reviewed,
    'before_sha256':hashlib.sha256(before).hexdigest(),
    'after_sha256':hashlib.sha256(OVERRIDES.read_bytes()).hexdigest()}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('Applied and verified two reviewed mappings; no verse text changed.')
