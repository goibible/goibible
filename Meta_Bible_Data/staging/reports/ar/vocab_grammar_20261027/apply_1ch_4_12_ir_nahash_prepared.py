#!/usr/bin/env python3
"""Prepare two compound-name occurrence mappings; requires --apply.

The corrected verse is pre-existing and never written. SQLite and filesystem
are not crash-atomic together: run with other writers stopped and retain backup
and pending receipt for manual recovery after interruption.
"""
import argparse,csv,datetime,fcntl,hashlib,io,json,os,sqlite3,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];NIM=ROOT/'Meta_Bible_Data/Bible_Noun_Extraction';sys.path.insert(0,str(NIM))
from ar.run_ar_torah import OUT,OVERRIDES,SOURCE,read_anchors
from ar.run_ar_rest_nt import validate
from matchers import get_matcher
STEM='013_1CH_004_012';SOURCE_SHA='0347e99125debcb2ed5a339628ea16a1a000e11436ff57da3dfcddaeec512ecf';TARGET_SHA='10f5cf453cd85792c517ea73ece3572a61a5882925390c6c67562f0532bfc7bf'
CITATION='عِير نَاحَاش';SPAN='عِيرِ نَاحَاشَ';NAME_GRAMMAR=('U','S','','PN')
D=[(7,'עִ֣יר','5904+'),(8,'נָחָ֑שׁ','5904')]
DB=NIM/'grammar_tables.sqlite3';BACKUP=HERE/'1ch_4_12_ir_nahash_override_backup.tsv';PENDING=HERE/'1ch_4_12_ir_nahash_pending.json';RECEIPT=HERE/'1ch_4_12_ir_nahash_receipt.json';LOCK=HERE/'1ch_4_12_ir_nahash_apply.lock'
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
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();check(a.apply,'No changes: explicit --apply required.')
 with LOCK.open('a+b') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  check(not any(x.exists() for x in (BACKUP,PENDING,RECEIPT)),'Existing application artifact; inspect recovery state.')
  source=(SOURCE/f'{STEM}_WLC.txt').read_bytes();target=(OUT/f'{STEM}_GOI_Ar.txt').read_bytes();check(sha(source)==SOURCE_SHA and sha(target)==TARGET_SHA,'WLC or corrected target changed.')
  text=target.decode().strip();check(text.count(SPAN)==1,'Compound target phrase missing or ambiguous.');offset=text.index(SPAN);matcher=get_matcher('ar');check(matcher.found(CITATION,text),'Compound name not matched.')
  for snippet,want in [('أَبَ عِيرِ نَاحَاشَ',True),('أَبَ نَاحَاشَ',False),('أَبَ عِيرِ',False),('أَبَ عِيرِ حَانُونَ',False)]:check(matcher.found(CITATION,snippet)==want,'Name matcher regression.')
  anchors=read_anchors()[('1CH',4,12)];check(len(anchors)==10,'Source anchor count changed.')
  for pos,surface,lemma in D:
   num,surf,old=anchors[pos-1];check((num,surf,old)==(5904,surface,''),f'Changed source or already populated position {pos}.')
  # Check the CSV distinguishes the two H5904 component lemmas.
  with (NIM/'ar/source_anchor_occurrences/ar_ot_source_noun_occurrences.csv').open(encoding='utf-8',newline='') as f:
   raw=[r for r in csv.DictReader(f) if (r['book_code'],r['chapter'],r['verse'])==('1CH','4','12')]
  for pos,surface,lemma in D:
   found=[r for r in raw if int(r['word_position'])==pos];check(len(found)==1 and found[0]['lemma']==lemma and found[0]['source_surface']==surface and found[0]['is_proper_name']=='1',f'Source morphology changed at {pos}.')
  terms=[CITATION if i in (7,8) else r for i,(_,_,r) in enumerate(anchors,1)];blanks=[i for i,r in enumerate(terms,1) if not r]
  check(blanks==[5],f'Unexpected remaining blank positions: {blanks}');fail=validate(text,[r for r in terms if r],matcher);check(not fail,f'Populated anchor validation failed: {fail}')
  before=OVERRIDES.read_bytes()
  with OVERRIDES.open(encoding='utf-8',newline='') as f:reader=csv.DictReader(f,delimiter='\t');fields=reader.fieldnames;rows=list(reader)
  check(fields==['book','chapter','verse','word_position','strongs_num','rendering','sense_key','reason'],'Unexpected override schema')
  keys=[(r['book'],int(r['chapter']),int(r['verse']),int(r['word_position'])) for r in rows];check(len(keys)==len(set(keys)),'Duplicate override keys')
  for pos,surface,lemma in D:
   check(('1CH',4,12,pos) not in keys,f'Existing override position {pos}')
   rows.append(dict(book='1CH',chapter='4',verse='12',word_position=str(pos),strongs_num='5904',rendering=CITATION,sense_key=f'H5904.AR_CONTEXT_1CH_4_12_{pos}',reason='Two WLC noun anchors are components of one Ir-nahash name; map each to the same verified full target phrase.'))
  buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows);after=buf.getvalue().encode()
  con=sqlite3.connect(DB,timeout=0);inserted=False;committed=False;replaced=False
  try:
   con.execute('BEGIN IMMEDIATE');old=con.execute("select gender,citation_number,plural_form,pos from noun_grammar where lang='ar' and rendering=?",(CITATION,)).fetchone();check(old is None or old==NAME_GRAMMAR,f'Conflicting compound-name grammar: {old}')
   if old is None:
    con.execute('INSERT INTO noun_grammar(lang,rendering,gender,citation_number,plural_form,method,model,created_at,pos,pos_method) VALUES(?,?,?,?,?,?,?,?,?,?)',('ar',CITATION,*NAME_GRAMMAR[:3],'source_review','codex_review',datetime.datetime.now(datetime.timezone.utc).isoformat(),NAME_GRAMMAR[3],'source_review'));inserted=True
   check(OVERRIDES.read_bytes()==before,'Overrides changed concurrently');exclusive(BACKUP,before)
   receipt={'status':'APPLIED','coordinate':'1CH 4:12','source_sha256':SOURCE_SHA,'corrected_target_sha256':TARGET_SHA,'target_span':SPAN,'target_start':offset,'target_end':offset+len(SPAN),'citation':CITATION,'grammar':{'part_of_speech':'PN','gender':'U','citation_number':'S','plural_form':''},'source_occurrences':[{'position':pos,'strongs':'H5904','lemma':lemma,'source_surface':surface} for pos,surface,lemma in D],'remaining_blank_positions':blanks,'populated_anchor_validation':'passed; lexical matcher only','matcher_probes':4,'grammar_inserted':inserted,'override_before_sha256':sha(before),'override_after_sha256':sha(after),'limitations':['The two anchor mappings intentionally share one compound target span.','Position 5 remains blank and is not certified.','Matcher does not establish semantic adequacy or occurrence multiplicity.']}
   exclusive(PENDING,(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode());replace(OVERRIDES,after);replaced=True
   updated=read_anchors()[('1CH',4,12)]
   for pos,_,_ in D:check(updated[pos-1][2]==CITATION,'Post-write occurrence mismatch')
   check(not validate(text,[r for _,_,r in updated if r],matcher),'Post-write populated validation failed');con.commit();committed=True;os.replace(PENDING,RECEIPT)
  except BaseException:
   if not committed:con.rollback()
   elif inserted:
    con.execute('BEGIN IMMEDIATE');con.execute("DELETE FROM noun_grammar WHERE lang='ar' AND rendering=? AND method='source_review' AND model='codex_review'",(CITATION,));con.commit()
   if replaced:replace(OVERRIDES,before)
   if PENDING.exists():PENDING.unlink()
   raise
  finally:con.close()
  print(f'Applied two compound-name anchors; receipt {RECEIPT}')
if __name__=='__main__':main()
