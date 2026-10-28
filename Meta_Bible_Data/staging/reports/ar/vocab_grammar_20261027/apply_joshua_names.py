#!/usr/bin/env python3
"""Apply independently reviewed Joshua place names with fail-closed checks."""
import csv, datetime, hashlib, io, json, sqlite3, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
NIM = ROOT / 'Meta_Bible_Data/Bible_Noun_Extraction'
sys.path.insert(0, str(NIM))
from ar.run_ar_torah import OUT, OVERRIDES, SOURCE, read_anchors
from ar.run_ar_rest_nt import validate
from matcher_ar import ArabicMatcher

receipt = HERE / 'joshua_names_applied.json'
assert not receipt.exists(), 'Already applied'
queue = {i: r for i, r in enumerate(map(json.loads, (HERE/'blank_occurrence_queue.jsonl').read_text().splitlines()), 1)}
candidates = {r['queue_row']: r for r in map(json.loads, (HERE/'review_batch_b_501_600.jsonl').read_text().splitlines())}
audits = {r['queue_row']: r for r in map(json.loads, (HERE/'independent_audit_b_501_600_c.jsonl').read_text().splitlines())}
anchors = read_anchors(); matcher = ArabicMatcher()
db = sqlite3.connect(NIM/'grammar_tables.sqlite3')
rows = []; skipped = []; byverse = {}
for number in range(551, 601):
    p, c, a = queue[number], candidates[number], audits[number]
    anchor = p['anchor']; key = (anchor['book_code'], int(anchor['chapter']), int(anchor['verse']))
    position, strong = int(anchor['word_position']), int(anchor['strongs_num'])
    if a['decision'] != 'APPROVE' or c['status'] != 'MATCH_CANDIDATE' or anchor['is_proper_name'] != '1':
        skipped.append({'row': number, 'reason': 'not independently approved as a proper name'}); continue
    source = (SOURCE/f"{p['stem']}_WLC.txt").read_bytes()
    target = (OUT/f"{p['stem']}_GOI_Ar.txt").read_bytes()
    if hashlib.sha256(source).hexdigest() != p['source_sha256'] or hashlib.sha256(target).hexdigest() != p['target_sha256']:
        skipped.append({'row': number, 'reason': 'source or target changed'}); continue
    text = target.decode(); span, citation = c['span'], c['citation']
    if not span or text.count(span) != 1 or not matcher.found(citation, text):
        skipped.append({'row': number, 'reason': 'span or matcher check failed'}); continue
    sid, surface, prior = anchors[key][position-1]
    if sid != strong or surface != anchor['source_surface'] or prior:
        skipped.append({'row': number, 'reason': 'source anchor changed or already populated'}); continue
    old = db.execute('SELECT gender,citation_number,plural_form,pos FROM noun_grammar WHERE lang=? AND rendering=?', ('ar', citation)).fetchone()
    if old and old[3] != 'PN':
        skipped.append({'row': number, 'reason': 'existing citation grammar is not a proper name'}); continue
    item = {'row':number, 'book':key[0], 'chapter':key[1], 'verse':key[2], 'word_position':position,
            'strongs_num':strong, 'source_surface':surface, 'rendering':citation,
            'sense_key':f'H{strong}.AR_CONTEXT_{key[0]}_{key[1]}_{key[2]}',
            'reason':'WLC place name in Joshua list; exact Arabic name checked against independent source-context review.',
            'target_span':span, 'target_start':text.index(span), 'source_sha256':p['source_sha256'], 'target_sha256':p['target_sha256'],
            'existing_grammar':old}
    byverse.setdefault(key, []).append(item)
for key, group in byverse.items():
    text = (OUT/f"{queue[group[0]['row']]['stem']}_GOI_Ar.txt").read_text()
    additions = {r['word_position']:r['rendering'] for r in group}
    required = [additions.get(i, term) for i, (_, _, term) in enumerate(anchors[key], 1)]
    failures = validate(text.strip(), [x for x in required if x], matcher)
    if failures:
        skipped.extend({'row':r['row'], 'reason':'verse anchor validation', 'failures':failures} for r in group)
    else:
        rows.extend(group)
assert rows, 'No reviewed names passed validation'
before = OVERRIDES.read_bytes()
with OVERRIDES.open(encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f, delimiter='\t'); fields = reader.fieldnames; existing = list(reader)
keys = {(r['book'], int(r['chapter']), int(r['verse']), int(r['word_position'])) for r in existing}
for r in rows:
    key = (r['book'], r['chapter'], r['verse'], r['word_position'])
    assert key not in keys; keys.add(key)
    existing.append({name:r.get(name, '') for name in fields})
buf=io.StringIO(newline=''); writer=csv.DictWriter(buf,fieldnames=fields,delimiter='\t',lineterminator='\n'); writer.writeheader(); writer.writerows(existing)
(HERE/'joshua_overrides_before.tsv').write_bytes(before)
db.execute('BEGIN IMMEDIATE')
try:
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for r in rows:
        db.execute('INSERT OR IGNORE INTO noun_grammar(lang,rendering,gender,citation_number,plural_form,method,model,created_at,pos,pos_method) VALUES(?,?,?,?,?,?,?,?,?,?)', ('ar',r['rendering'],'U','S','','source_review','codex+independent_review',now,'PN','source_review'))
    assert OVERRIDES.read_bytes()==before
    OVERRIDES.write_text(buf.getvalue(),encoding='utf-8')
    updated=read_anchors()
    for r in rows:
        assert updated[(r['book'],r['chapter'],r['verse'])][r['word_position']-1][2]==r['rendering']
    db.commit()
except BaseException:
    db.rollback(); OVERRIDES.write_bytes(before); raise
receipt.write_text(json.dumps({'status':'APPLIED','reviewed':rows,'skipped':skipped,'count':len(rows),
    'override_before_sha256':hashlib.sha256(before).hexdigest(),
    'override_after_sha256':hashlib.sha256(OVERRIDES.read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
print(f'Applied {len(rows)} checked mappings; held {len(skipped)} for follow-up.')
