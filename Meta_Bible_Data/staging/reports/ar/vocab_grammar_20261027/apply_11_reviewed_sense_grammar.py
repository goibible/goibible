#!/usr/bin/env python3
"""Dry-run by default; apply only via --apply. Never alters target verse text.

SQLite and TSV are separate files and not crash-atomic. Backups are durable
and a pending marker exists until database commit and receipt complete.
"""
import argparse,csv,datetime,hashlib,io,json,os,sqlite3,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];NIM=ROOT/'Meta_Bible_Data/Bible_Noun_Extraction';sys.path.insert(0,str(NIM));sys.path.insert(0,str(NIM/'translation_cube'))
from ar.run_ar_torah import OUT,SOURCE,OVERRIDES,read_anchors
from ar.run_ar_rest_nt import validate
from ar.cube_adapter import ot_occurrence_overrides,ArabicAdapter
from matcher_ar import ArabicMatcher
DB=NIM/'grammar_tables.sqlite3';SCHEMA=NIM/'translation_cube/sense_grammar_schema.sql'
PROPOSALS=HERE/'name_senses_601_650_proposals.jsonl';TEH=HERE/'1ch_4_12_tehinnah_independent_review.json'
RECEIPT=HERE/'11_sense_grammar_applied.json';PENDING=HERE/'11_sense_grammar_PENDING.json';BTSV=HERE/'11_sense_overrides_before.tsv';BDB=HERE/'11_sense_grammar_before.sqlite3'
PIN={PROPOSALS:'c44523b972364587bc379bc0672f512ca2c910d22204ed61ca7d8b06c89f20ca',TEH:'2d71d840a8439a77062da9e1949e851ed47fcbe28aedfb66760c3b9765baa3e9',SCHEMA:'9dd886083df3e49753a07b54607a719f98cc70a5b4df981cb9e845e2abcb9484',OVERRIDES:'7ad2997ad7bb77073fe01a16ae0cac2e61c0054fcbf2333163833163a0dd1a5f'}
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def digest(b):return hashlib.sha256(b).hexdigest()
def atomic(path,data):
 fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
for path,expected in PIN.items():need(digest(path.read_bytes())==expected,f'input changed: {path}')
for path in (RECEIPT,PENDING,BTSV,BDB):need(not path.exists(),f'existing recovery artifact: {path}')
proposals=[json.loads(line) for line in PROPOSALS.read_text().splitlines()];t=json.loads(TEH.read_text());need(len(proposals)==10 and t['decision']=='ALIGNED_GRAMMAR_CONFLICT_HOLD','unexpected evidence')
a=t['anchor'];proposals.append({'queue_row':1308,'stem':'013_1CH_004_012','anchor':{'book_code':'1CH','chapter':'4','verse':'12',**a},'source_sha256':t['source_sha256'],'target_sha256':t['target_sha256'],'target_span':t['target_span'],'target_start':t['target_start'],'target_end':t['target_end'],'occurrence_rendering':t['citation'],'sense_key':'H8468.AR_CONTEXT_1CH_4_12','sense_grammar':t['proposed_grammar'],'existing_global_grammar':[t['current_grammar'][k] for k in ('gender','citation_number','plural_form','pos')],'reason':t['source_context']+' '+t['target_context']})
matcher=ArabicMatcher();anchors=read_anchors();existing=ot_occurrence_overrides();needed={}; prepared=[];sense_keys=set();adapter=ArabicAdapter('ar')
with sqlite3.connect(f'file:{DB}?mode=ro',uri=True) as check:
 table=check.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sense_grammar'").fetchone()
 for r in proposals:
  a=r['anchor'];key=(a['book_code'],int(a['chapter']),int(a['verse']));p=int(a['word_position']);strong=int(a['strongs_num']);cid=r['occurrence_rendering'];sense=r['sense_key'];identity=(*key,p)
  need(identity not in existing and sense not in sense_keys,f'existing override or duplicated sense: {identity}/{sense}');sense_keys.add(sense)
  sid,surface,old=anchors[key][p-1];need((sid,surface,old)==(strong,a['source_surface'],''),f'anchor drift {identity}')
  source=(SOURCE/f"{r['stem']}_WLC.txt").read_bytes();target=(OUT/f"{r['stem']}_GOI_Ar.txt").read_bytes();text=target.decode()
  need(digest(source)==r['source_sha256'] and digest(target)==r['target_sha256'],f'verse changed {identity}')
  start,end=r['target_start'],r['target_end'];need(text[start:end]==r['target_span'] and text.count(r['target_span'])==1 and matcher.found(cid,text),f'bad span/matcher {identity}')
  global_row=check.execute('SELECT gender,citation_number,plural_form,pos FROM noun_grammar WHERE lang=? AND rendering=?',('ar',cid)).fetchone();need(global_row is not None and tuple(global_row)==tuple(r['existing_global_grammar']),f'global grammar changed {identity}')
  if table:need(check.execute('SELECT 1 FROM sense_grammar WHERE lang=? AND sense_key=?',('ar',sense)).fetchone() is None,f'sense exists {sense}')
  g=r['sense_grammar'];need(g=={'pos':'PN','gender':'U','citation_number':'S','plural_form':''},f'grammar not reviewed {sense}')
  need(sense not in adapter._sense_grammar,f'sense already loaded {sense}');adapter._sense_grammar[sense]=(cid,g['gender'],g['citation_number'],g['plural_form']);features=adapter.lexical_features(cid,sense);need((features.gender,features.citation_number,features.plural_forms,features.confidence)==('U','S',(),'sense_grammar'),f'adapter cannot read {sense}')
  needed.setdefault(key,[]).append((p,cid));prepared.append({'book':key[0],'chapter':key[1],'verse':key[2],'word_position':p,'strongs_num':strong,'source_surface':surface,'rendering':cid,'sense_key':sense,'reason':r['reason'],'target_span':r['target_span'],'target_start':start,'target_end':end,'source_sha256':r['source_sha256'],'target_sha256':r['target_sha256'],'prior_global_grammar':global_row,'sense_grammar':g})
for key,additions in needed.items():
 sample=next(x for x in proposals if (x['anchor']['book_code'],int(x['anchor']['chapter']),int(x['anchor']['verse']))==key); text=(OUT/f"{sample['stem']}_GOI_Ar.txt").read_text().strip();replace=dict(additions); terms=[replace.get(i,rendering) for i,(_,_,rendering) in enumerate(anchors[key],1)];fail=validate(text,[v for v in terms if v],matcher);need(not fail,f'populated verse anchors failed {key}: {fail}')
for key in sense_keys:need(key in adapter._sense_grammar,f'adapter missing planned sense {key}')
need(len(prepared)==11 and len(sense_keys)==11,'incorrect sense count')
before=OVERRIDES.read_bytes()
with OVERRIDES.open(encoding='utf-8',newline='') as f:
 reader=csv.DictReader(f,delimiter='\t');fields=reader.fieldnames;rows=list(reader)
need(fields and {'book','chapter','verse','word_position','strongs_num','rendering','sense_key'}<=set(fields),'override schema mismatch')
for row in prepared:rows.append({field:row.get(field,'') for field in fields})
buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows);after=buf.getvalue().encode()
if not args.apply:
 print(json.dumps({'mode':'DRY_RUN','occurrence_count':len(prepared),'sense_count':len(sense_keys),'populated_verse_checks':len(needed),'grammar_table_exists':bool(table),'remaining_blank_anchors':{f'{k[0]} {k[1]}:{k[2]}':sum(not (dict(v).get(i,term)) for i,(_,_,term) in enumerate(anchors[k],1)) for k,v in needed.items()}},ensure_ascii=False));sys.exit(0)
# Re-check immediately around snapshot and lock; preserve global noun_grammar.
db=sqlite3.connect(DB,timeout=30);version=db.execute('PRAGMA data_version').fetchone()[0];backup=sqlite3.connect(BDB)
try:db.backup(backup)
finally:backup.close()
with BTSV.open('xb') as f:f.write(before);f.flush();os.fsync(f.fileno())
atomic(PENDING,(json.dumps({'status':'PENDING','overrides_before_sha256':digest(before),'grammar_backup_sha256':digest(BDB.read_bytes())})+'\n').encode())
changed=False;committed=False
try:
 db.execute('BEGIN IMMEDIATE');need(db.execute('PRAGMA data_version').fetchone()[0]==version and OVERRIDES.read_bytes()==before,'concurrent modification')
 exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sense_grammar'").fetchone()
 if not exists:db.execute(SCHEMA.read_text())
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 for r in prepared:
  need(db.execute('SELECT gender,citation_number,plural_form,pos FROM noun_grammar WHERE lang=? AND rendering=?',('ar',r['rendering'])).fetchone()==tuple(r['prior_global_grammar']),'global grammar drift')
  db.execute('INSERT INTO sense_grammar(lang,sense_key,rendering,gender,citation_number,plural_form,pos,provenance) VALUES(?,?,?,?,?,?,?,?)',('ar',r['sense_key'],r['rendering'],'U','S','','PN','reviewed_joshua_tehinnah'))
 atomic(OVERRIDES,after);changed=True
 loaded=ot_occurrence_overrides(); updated=read_anchors()
 for r in prepared:
  key=(r['book'],r['chapter'],r['verse'],r['word_position']);need(loaded.get(key)==(r['strongs_num'],r['rendering'],r['sense_key']) and updated[key[:3]][key[3]-1][2]==r['rendering'],f'override readback failed {key}')
  dbrow=db.execute('SELECT rendering,gender,citation_number,plural_form,pos FROM sense_grammar WHERE lang=? AND sense_key=?',('ar',r['sense_key'])).fetchone();need(dbrow==(r['rendering'],'U','S','','PN'),f'grammar readback failed {key}')
 need(len(prepared)==len(sense_keys)==11,'count mismatch')
 db.commit();committed=True
 receipt_data={'status':'APPLIED','occurrence_count':11,'sense_count':11,'reviewed':prepared,'overrides_before_sha256':digest(before),'overrides_after_sha256':digest(after),'grammar_backup_sha256':digest(BDB.read_bytes()),'applied_at':now,'recovery':'SQLite/TSV updates are not crash-atomic; retain backups and inspect pending marker.'}
 atomic(RECEIPT,(json.dumps(receipt_data,ensure_ascii=False,indent=2)+'\n').encode())
 PENDING.unlink()
except BaseException:
 if db.in_transaction:db.rollback()
 if changed and not committed:atomic(OVERRIDES,before)
 # After commit, leave pending marker and backups for explicit recovery rather than falsely restore only one file.
 raise
finally:db.close()
print('Applied 11 occurrence and sense grammar records; receipt and backups retained.')
