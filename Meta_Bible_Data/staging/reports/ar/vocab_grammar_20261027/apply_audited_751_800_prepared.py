#!/usr/bin/env python3
"""Apply source-audited 751–800 alignments that pass full verse checks.

Requires --apply. Never overwrites an existing grammar row. SQLite and a file
rename are not crash-atomic together: stop all other writers before execution,
retain backup and pending receipt, and inspect both after interruption.
"""
import argparse,csv,datetime,fcntl,hashlib,io,json,os,sqlite3,sys,tempfile
from collections import defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];NIM=ROOT/'Meta_Bible_Data/Bible_Noun_Extraction';sys.path.insert(0,str(NIM))
from ar.run_ar_torah import OUT,OVERRIDES,SOURCE,read_anchors
from ar.run_ar_rest_nt import validate
from matchers import get_matcher
AUDIT=HERE/'independent_audit_751_800_b.jsonl';AUDIT_SHA='88d17e535fe6010f04059a6b70c8af47a2f85780e975f18c6305b3ba6e1628d3';DB=NIM/'grammar_tables.sqlite3'
BACKUP=HERE/'audit_751_800_override_backup.tsv';PENDING=HERE/'audit_751_800_pending.json';RECEIPT=HERE/'audit_751_800_receipt.json';LOCK=HERE/'audit_751_800_apply.lock'
def check(c,msg):
 if not c:raise RuntimeError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def exclusive(p,b):
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def replace(p,b):
 fd,n=tempfile.mkstemp(prefix='.'+p.name+'.',dir=p.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  os.replace(n,p)
 finally:
  if os.path.exists(n):os.unlink(n)
def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args();check(args.apply,'No changes: explicit --apply required.')
 with LOCK.open('a+b') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);check(not any(p.exists() for p in (BACKUP,PENDING,RECEIPT)),'Existing recovery artifact; inspect it before applying.')
  ab=AUDIT.read_bytes();check(sha(ab)==AUDIT_SHA,'Audit evidence changed');aud=[json.loads(s) for s in ab.splitlines()];check([x['queue_row'] for x in aud]==list(range(751,801)),'Audit row scope changed')
  anchors=read_anchors();matcher=get_matcher('ar');before=OVERRIDES.read_bytes()
  with OVERRIDES.open(encoding='utf-8',newline='') as f:reader=csv.DictReader(f,delimiter='\t');fields=reader.fieldnames;existing=list(reader)
  check(fields==['book','chapter','verse','word_position','strongs_num','rendering','sense_key','reason'],'Unexpected override schema')
  keys={(r['book'],int(r['chapter']),int(r['verse']),int(r['word_position'])) for r in existing};check(len(keys)==len(existing),'Duplicate override keys')
  con=sqlite3.connect(DB,timeout=0);committed=False;replaced=False;inserted=[];chosen=[];held=[];groups=defaultdict(list);texts={};eligible={}
  try:
   con.execute('BEGIN IMMEDIATE')
   for row in aud:
    if row['decision']!='APPROVED_ALIGNMENT':held.append({'queue_row':row['queue_row'],'reason':'audit '+row['decision'],'detail':row['source_context']});continue
    a=row['anchor'];key=(a['book_code'],int(a['chapter']),int(a['verse']));pos=int(a['word_position']);occ=(*key,pos);stem=row['stem'];reason=None
    src=(SOURCE/f'{stem}_WLC.txt').read_bytes();target=(OUT/f'{stem}_GOI_Ar.txt').read_bytes();text=target.decode().strip();texts[key]=text
    if sha(src)!=row['frozen_source_sha256'] or sha(target)!=row['frozen_target_sha256']:reason='source or target hash changed'
    elif occ in keys:reason='override already exists'
    elif anchors[key][pos-1]!=(int(a['strongs_num']),a['source_surface'],''):reason='source anchor or old rendering changed'
    elif text[row['target_start']:row['target_end']]!=row['target_span'] or text.count(row['target_span'])!=1:reason='span or offset changed'
    elif not matcher.found(row['citation'],text):reason='citation not found by matcher'
    else:
     gr=row['grammar'];want=(gr['gender'],gr['citation_number'],gr['plural_form'],gr['pos']);prior=con.execute("select gender,citation_number,plural_form,pos from noun_grammar where lang='ar' and rendering=?",(row['citation'],)).fetchone()
     if prior is not None and prior!=want:reason='existing citation grammar conflicts'
    if reason:held.append({'queue_row':row['queue_row'],'reason':reason});continue
    groups[key].append(row)
   # Validate the whole group together: no candidate admitted if any populated
   # anchor in that verse is missing after all proposed substitutions.
   for key,group in groups.items():
    additions={int(x['anchor']['word_position']):x['citation'] for x in group}
    terms=[additions.get(i,term) for i,(_,_,term) in enumerate(anchors[key],1)];fail=validate(texts[key],[t for t in terms if t],matcher)
    if fail:
     held.extend({'queue_row':x['queue_row'],'reason':'full populated-anchor validation failed','failures':fail} for x in group);continue
    chosen.extend(group);eligible[key]={'remaining_blank_positions':[i for i,t in enumerate(terms,1) if not t],'populated_anchor_count':sum(bool(t) for t in terms)}
   check(chosen,'No audited alignments passed current full-verse gates')
   for row in chosen:
    a=row['anchor'];key=(a['book_code'],int(a['chapter']),int(a['verse']));pos=int(a['word_position']);strong=int(a['strongs_num']);gr=row['grammar'];citation=row['citation'];want=(gr['gender'],gr['citation_number'],gr['plural_form'],gr['pos'])
    prior=con.execute("select gender,citation_number,plural_form,pos from noun_grammar where lang='ar' and rendering=?",(citation,)).fetchone();check(prior is None or prior==want,f'Grammar collision: {citation}')
    if prior is None:
     con.execute('INSERT INTO noun_grammar(lang,rendering,gender,citation_number,plural_form,method,model,created_at,pos,pos_method) VALUES(?,?,?,?,?,?,?,?,?,?)',('ar',citation,*want[:3],'source_review','codex_independent_audit',datetime.datetime.now(datetime.timezone.utc).isoformat(),want[3],'source_review'));inserted.append(citation)
    existing.append(dict(book=key[0],chapter=str(key[1]),verse=str(key[2]),word_position=str(pos),strongs_num=str(strong),rendering=citation,sense_key=f'H{strong}.AR_CONTEXT_{key[0]}_{key[1]}_{key[2]}_{pos}',reason=row['source_context']))
   buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(existing);after=buf.getvalue().encode();check(OVERRIDES.read_bytes()==before,'Override ledger changed during review')
   exclusive(BACKUP,before)
   receipt={'status':'APPLIED','audit_sha256':AUDIT_SHA,'applied':chosen,'held':held,'verse_checks':{':'.join(map(str,k)):v for k,v in eligible.items()},'grammar_inserted':inserted,'override_before_sha256':sha(before),'override_after_sha256':sha(after),'limitations':['Validation checks populated anchors only; remaining blank positions are listed.','Lexical matcher cannot prove semantics, negation, or repeated occurrence multiplicity.','Shared compound-name components intentionally use the same full span.']}
   exclusive(PENDING,(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode());replace(OVERRIDES,after);replaced=True
   updated=read_anchors()
   for row in chosen:
    a=row['anchor'];key=(a['book_code'],int(a['chapter']),int(a['verse']));check(updated[key][int(a['word_position'])-1][2]==row['citation'],'Post-write occurrence mismatch')
   for key in eligible:check(not validate(texts[key],[term for _,_,term in updated[key] if term],matcher),f'Post-write validation failed at {key}')
   con.commit();committed=True;os.replace(PENDING,RECEIPT)
  except BaseException:
   if not committed:con.rollback()
   else:
    con.execute('BEGIN IMMEDIATE')
    for citation in inserted:con.execute("DELETE FROM noun_grammar WHERE lang='ar' AND rendering=? AND method='source_review' AND model='codex_independent_audit'",(citation,))
    con.commit()
   if replaced:replace(OVERRIDES,before)
   if PENDING.exists():PENDING.unlink()
   raise
  finally:con.close()
  print(f'Applied {len(chosen)} occurrence mappings, held {len(held)}; receipt {RECEIPT}')
if __name__=='__main__':main()
