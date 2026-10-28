#!/usr/bin/env python3
"""Dry-run by default. --apply uses only pinned, independently audited names."""
import argparse,collections,csv,datetime,hashlib,io,json,os,sqlite3,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];NIM=ROOT/'Meta_Bible_Data/Bible_Noun_Extraction';sys.path.insert(0,str(NIM))
from ar.run_ar_torah import OUT,OVERRIDES,SOURCE,ANCHORS,DEFAULTS,read_anchors
from ar.run_ar_rest_nt import validate
from matchers import ArabicMatcher
DB=NIM/'grammar_tables.sqlite3'; AUDIT=HERE/'independent_audit_b_801_850_c.jsonl';QUEUE=HERE/'blank_occurrence_queue.jsonl';MANIFEST=HERE/'prepared_801_850_manifest_c.json';REPORT=HERE/'prepared_801_850_dry_run_c.json';RECEIPT=HERE/'prepared_801_850_applied_c.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atom(path,data):
 fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 manifest=json.loads(MANIFEST.read_text()); watched=[OVERRIDES,DB,ANCHORS,AUDIT,QUEUE,Path(__file__).resolve(),*DEFAULTS]
 if {str(k):sha(k) for k in watched}!=manifest['pinned_hashes']:raise RuntimeError('Pinned ledger/input hash mismatch: refresh review and prepare anew')
 if args.apply and RECEIPT.exists():raise RuntimeError('Application receipt exists')
 queue={i:x for i,x in enumerate(map(json.loads,QUEUE.read_text().splitlines()),1)};audits={x['queue_row']:x for x in map(json.loads,AUDIT.read_text().splitlines())}; assert set(audits)==set(range(801,851))
 anchors=read_anchors();matcher=ArabicMatcher();db=sqlite3.connect('file:'+str(DB)+'?mode=ro',uri=True);assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok';groups=collections.defaultdict(list);held=[]
 with OVERRIDES.open(newline='',encoding='utf8') as f:reader=csv.DictReader(f,delimiter='\t');fields=reader.fieldnames;existing=list(reader)
 keys={(x['book'],int(x['chapter']),int(x['verse']),int(x['word_position'])) for x in existing};assert len(keys)==len(existing)
 for n in range(801,851):
  a=audits[n];p=queue[n];h=p['anchor'];v=(h['book_code'],int(h['chapter']),int(h['verse']));pos=int(h['word_position']);strong=int(h['strongs_num']);key=(*v,pos)
  def hold(reason):held.append({'row':n,'reason':reason})
  if a['decision']!='APPROVED':hold('independent review uncertain');continue
  if a['source_sha256']!=p['source_sha256'] or a['target_sha256']!=p['target_sha256'] or a['source_surface']!=h['source_surface'] or a['stem']!=p['stem']:hold('audit or queue identity differs');continue
  if sha(SOURCE/(p['stem']+'_WLC.txt'))!=p['source_sha256'] or sha(OUT/(p['stem']+'_GOI_Ar.txt'))!=p['target_sha256']:hold('source or target changed');continue
  t=(OUT/(p['stem']+'_GOI_Ar.txt')).read_text();span=a['target_span'];start=a['target_start'];end=a['target_end'];citation=a['citation'];g=a['grammar'];
  if not span or not citation or not isinstance(start,int) or t[start:end]!=span or not matcher.found(citation,t):hold('exact offset or citation matcher failed');continue
  if not isinstance(g,dict) or 'proper' not in g.get('part_of_speech','').lower():hold('proper name grammar not established');continue
  if pos<1 or pos>len(anchors[v]):hold('anchor position invalid');continue
  sid,surface,prior=anchors[v][pos-1]
  if sid!=strong or surface!=h['source_surface'] or prior or key in keys:hold('source anchor changed or already populated');continue
  old=db.execute('SELECT gender,citation_number,plural_form,pos FROM noun_grammar WHERE lang=? AND rendering=?',('ar',citation)).fetchone()
  if old and (old[3]!='PN' or old[0] not in ('U','-') or old[1] not in ('S','U') or old[2]):hold('existing citation grammar conflicts');continue
  item={'row':n,'book':v[0],'chapter':v[1],'verse':v[2],'word_position':pos,'strongs_num':strong,'source_surface':surface,'rendering':citation,'sense_key':f'H{strong}.AR_CONTEXT_{v[0]}_{v[1]}_{v[2]}','reason':a['evidence'],'target_span':span,'target_start':start,'target_end':end,'source_sha256':p['source_sha256'],'target_sha256':p['target_sha256'],'existing_grammar':old}
  groups[v].append(item)
 rows=[]
 for v,items in groups.items():
  t=(OUT/(queue[items[0]['row']]['stem']+'_GOI_Ar.txt')).read_text().strip();adds={x['word_position']:x['rendering'] for x in items};terms=[adds.get(i,term) for i,(_,_,term) in enumerate(anchors[v],1)];fails=validate(t,[x for x in terms if x],matcher)
  if fails:
   for x in items:held.append({'row':x['row'],'reason':'full populated-anchor validation failed','failures':fails})
  else:rows.extend(items)
 db.close(); report={'status':'DRY_RUN','rows':rows,'held':sorted(held,key=lambda x:x['row']),'pinned_hashes':manifest['pinned_hashes']};
 if not args.apply:
  atom(REPORT,(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode());print(json.dumps({'eligible':len(rows),'held':len(held)},ensure_ascii=False));return
 if not rows:raise RuntimeError('No eligible rows')
 if {str(k):sha(k) for k in watched}!=manifest['pinned_hashes']:raise RuntimeError('Inputs changed since preflight')
 before=OVERRIDES.read_bytes()
 for x in rows:
  key=(x['book'],x['chapter'],x['verse'],x['word_position']);assert key not in keys;keys.add(key);existing.append({f:x.get(f,'') for f in fields})
 b=io.StringIO(newline='');w=csv.DictWriter(b,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(existing);new=b.getvalue().encode()
 db=sqlite3.connect(DB);db.execute('BEGIN IMMEDIATE');changed=False
 try:
  if sha(DB)!=manifest['pinned_hashes'][str(DB)] or OVERRIDES.read_bytes()!=before:raise RuntimeError('Live ledger changed during application')
  for x in rows:
   old=db.execute('SELECT gender,citation_number,plural_form,pos FROM noun_grammar WHERE lang=? AND rendering=?',('ar',x['rendering'])).fetchone()
   if old and (old[3]!='PN' or old[0] not in ('U','-') or old[1] not in ('S','U') or old[2]):raise RuntimeError('Grammar conflict')
   db.execute('INSERT OR IGNORE INTO noun_grammar(lang,rendering,gender,citation_number,plural_form,method,model,created_at,pos,pos_method) VALUES(?,?,?,?,?,?,?,?,?,?)',('ar',x['rendering'],'U','S','','source_review','codex+independent_review',datetime.datetime.now(datetime.timezone.utc).isoformat(),'PN','source_review'))
  atom(OVERRIDES,new);changed=True;updated=read_anchors()
  for x in rows:assert updated[(x['book'],x['chapter'],x['verse'])][x['word_position']-1][2]==x['rendering']
  db.commit()
 except BaseException:
  db.rollback()
  if changed:atom(OVERRIDES,before)
  raise
 finally:db.close()
 atom(RECEIPT,(json.dumps({'status':'APPLIED','rows':rows,'held':held,'before_hash':hashlib.sha256(before).hexdigest(),'after_hash':sha(OVERRIDES)},ensure_ascii=False,indent=2)+'\n').encode());print('Applied',len(rows))
if __name__=='__main__':main()
