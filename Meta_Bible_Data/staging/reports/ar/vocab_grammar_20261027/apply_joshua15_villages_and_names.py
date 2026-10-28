#!/usr/bin/env python3
"""Apply six reviewed village corrections and 11 names; fail closed.

Run only by the integration owner, after review. Outputs persistent before-state
backups and a receipt. No matcher modifications. SQLite + TSV cannot be made
crash-atomic together; on abrupt termination inspect backups and receipt.
"""
import csv, datetime, hashlib, io, json, os, sqlite3, sys, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[4]; NIM=ROOT/'Meta_Bible_Data/Bible_Noun_Extraction'
sys.path.insert(0,str(NIM))
from ar.run_ar_torah import OUT,SOURCE,OVERRIDES,read_anchors
from ar.run_ar_rest_nt import validate
from matcher_ar import ArabicMatcher
DB=NIM/'grammar_tables.sqlite3'
EVIDENCE=HERE/'joshua15_village_corrections.json'
RECEIPT=HERE/'joshua15_villages_and_names_applied.json'
BACKUP_TSV=HERE/'joshua15_villages_and_names_overrides_before.tsv'
BACKUP_DB=HERE/'joshua15_villages_and_names_grammar_before.sqlite3'
OVERRIDE_HASH='84a366e7ed734267099262d211eaa7f330d7b83876cfe882682d9d013c2e70e2'
EVIDENCE_HASH='c7e010eb013a491da78826cd93cbfd20cea2481c9bedb593d4960fccf7b05934'
def need(ok,msg):
 if not ok: raise RuntimeError(msg)
def sha(data): return hashlib.sha256(data).hexdigest()
def atomic_write(path,data):
 fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(name,path)
 finally:
  if os.path.exists(name):os.unlink(name)
for p in (RECEIPT,BACKUP_TSV,BACKUP_DB):need(not p.exists(),f'refusing to overwrite {p}')
before=OVERRIDES.read_bytes(); need(sha(before)==OVERRIDE_HASH,'override TSV changed since preparation')
need(sha(EVIDENCE.read_bytes())==EVIDENCE_HASH,'review evidence changed')
evidence=json.loads(EVIDENCE.read_text()); need(evidence['status']=='PROPOSED_NOT_APPLIED','bad evidence status')
records=evidence['records']; need(len(records)==6 and sum(len(r['additional_names']) for r in records)==11,'unexpected proposal count')
matcher=ArabicMatcher(); effective=read_anchors(); planned=[]; names=[]; groups={}
for r in records:
 key=(r['book'],r['chapter'],r['verse']); stem=f"006_JOS_{r['chapter']:03d}_{r['verse']:03d}"
 source=(SOURCE/f'{stem}_WLC.txt').read_bytes(); target=(OUT/f'{stem}_GOI_Ar.txt').read_bytes(); text=target.decode()
 need(sha(source)==r['source_sha256'] and sha(target)==r['target_sha256'],f'{key}: coordinate hash changed')
 need(source.decode().strip()==r['source'] and text.strip()==r['arabic'],f'{key}: content changed')
 p=r['position'];sid,surf,old=effective[key][p-1]; span=r['proposed_occurrence_rendering']
 need((sid,surf,old)==(2691,r['hebrew'],'فِنَاء'),f'{key}: old village anchor changed')
 need(text.count(span)==1 and matcher.found(span,text),f'{key}: village span failure')
 groups[key]=[(p,span)]
 planned.append({'book':key[0],'chapter':key[1],'verse':key[2],'word_position':p,'strongs_num':2691,'source_surface':surf,'rendering':span,'citation':'قَرْيَة','target_span':span,'target_start':text.index(span),'target_end':text.index(span)+len(span),'sense_key':f'H2691.AR_CONTEXT_JOS_15_{key[2]}','reason':r['reason']})
 for n in r['additional_names']:
  pos=n['position']; sid,surf,old=effective[key][pos-1]; s=n['target_span']; citation=n['proposed_rendering']
  need((sid,surf,old)==(n['strongs_num'],n['hebrew'],''),f"{key} pos {pos}: name anchor changed")
  need(text.count(s)==1 and matcher.found(citation,text),f'{key} pos {pos}: name span or matcher failed')
  row={'book':key[0],'chapter':key[1],'verse':key[2],'word_position':pos,'strongs_num':sid,'source_surface':surf,'rendering':citation,'citation':citation,'target_span':s,'target_start':text.index(s),'target_end':text.index(s)+len(s),'sense_key':f'H{sid}.AR_CONTEXT_JOS_15_{key[2]}','reason':'WLC name and Arabic name independently reviewed in town-list context.'}
  names.append(row);planned.append(row);groups[key].append((pos,citation))
 terms=[dict(groups[key]).get(i,v) for i,(_,_,v) in enumerate(effective[key],1)]
 fail=validate(text.strip(),[x for x in terms if x],matcher);need(not fail,f'{key}: full populated-anchor validation: {fail}')
 need(all(text[x['target_start']:x['target_end']]==x['target_span'] for x in planned if (x['book'],x['chapter'],x['verse'])==key),f'{key}: offset mismatch')
with OVERRIDES.open(encoding='utf-8',newline='') as f:
 reader=csv.DictReader(f,delimiter='\t');fields=reader.fieldnames; rows=list(reader)
need(fields and {'book','chapter','verse','word_position','rendering','strongs_num'}<=set(fields),'unexpected override schema')
index={}
for i,row in enumerate(rows):
 k=(row['book'],int(row['chapter']),int(row['verse']),int(row['word_position']));need(k not in index,f'duplicate TSV occurrence {k}');index[k]=i
for r in planned:
 k=(r['book'],r['chapter'],r['verse'],r['word_position'])
 if r['strongs_num']==2691:
  if k in index:
   prev=rows[index[k]];need(prev['rendering']=='فِنَاء' and int(prev['strongs_num'])==2691,f'{k}: unexpected override')
   rows[index[k]]={name:r.get(name,'') for name in fields}
  else:rows.append({name:r.get(name,'') for name in fields});index[k]=len(rows)-1
 else:
  need(k not in index,f'{k}: name override already exists');rows.append({name:r.get(name,'') for name in fields});index[k]=len(rows)-1
buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows);after=buf.getvalue().encode()
# Consistent SQLite snapshot precedes lock; data_version detects an intervening writer.
db=sqlite3.connect(DB,timeout=30);version=db.execute('PRAGMA data_version').fetchone()[0]
backup=sqlite3.connect(BACKUP_DB)
try:db.backup(backup)
finally:backup.close()
BACKUP_TSV.write_bytes(before)
receipt_written=False;changed=False
try:
 db.execute('BEGIN IMMEDIATE');need(db.execute('PRAGMA data_version').fetchone()[0]==version,'grammar database changed during snapshot')
 need(OVERRIDES.read_bytes()==before,'override TSV changed during preflight')
 village=db.execute('SELECT gender,citation_number,plural_form,pos FROM noun_grammar WHERE lang=? AND rendering=?',('ar','قَرْيَة')).fetchone()
 need(village==('F','S','قرى','N'),f'village citation grammar conflict: {village}')
 # Exact target surface forms are occurrence renderings, not citation lemmas.
 # Do not insert them as separate grammar entries with misleading citation_number.
 for surface in ('قُرَاهَا','قُرَاهُنَّ'):
  need(db.execute('SELECT 1 FROM noun_grammar WHERE lang=? AND rendering=?',('ar',surface)).fetchone() is None,f'unexpected grammar entry for inflected form {surface}')
 now=datetime.datetime.now(datetime.timezone.utc).isoformat(); added=[]
 for citation in sorted({r['citation'] for r in names}):
  old=db.execute('SELECT gender,citation_number,plural_form,pos FROM noun_grammar WHERE lang=? AND rendering=?',('ar',citation)).fetchone()
  if old:need(old[3]=='PN' and old[1]=='S' and old[2]=='',f'grammar conflict for {citation}: {old}')
  else:
   db.execute('INSERT INTO noun_grammar(lang,rendering,gender,citation_number,plural_form,method,model,created_at,pos,pos_method) VALUES(?,?,?,?,?,?,?,?,?,?)',('ar',citation,'U','S','','source_review','codex+independent_review',now,'PN','source_review'));added.append(citation)
 atomic_write(OVERRIDES,after);changed=True
 current=read_anchors()
 for r in planned:
  k=(r['book'],r['chapter'],r['verse']);need(current[k][r['word_position']-1][2]==r['rendering'],f'{k}: readback mismatch')
 for key in groups:
  text=(OUT/f'006_JOS_{key[1]:03d}_{key[2]:03d}_GOI_Ar.txt').read_text()
  need(not validate(text.strip(),[v for _,_,v in current[key] if v],matcher),f'{key}: final verse check failed')
 receipt={'status':'APPLIED','reviewed':planned,'grammar_added':added,'village_citation':'قَرْيَة','village_occurrence_forms':['قُرَاهَا','قُرَاهُنَّ'],'overrides_before_sha256':sha(before),'overrides_after_sha256':sha(after),'grammar_backup_sha256':sha(BACKUP_DB.read_bytes()),'evidence_sha256':EVIDENCE_HASH,'caveat':'Cross-file SQLite/TSV update is not crash-atomic; backups supplied.'}
 atomic_write(RECEIPT,(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode());receipt_written=True
 db.commit()
except BaseException:
 db.rollback()
 if changed:atomic_write(OVERRIDES,before)
 if receipt_written:RECEIPT.unlink(missing_ok=True)
 raise
finally:db.close()
print('Applied six occurrence corrections and 11 place names; backups and receipt recorded.')
