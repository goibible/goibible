#!/usr/bin/env python3
"""Prepared, fail-closed application for five Exodus occurrences. Requires --apply.

Ordinary failures restore the override ledger. Grammar is checked read-only;
inflected occurrence renderings are not entered as noun-grammar citations.
The backup and pending receipt aid recovery after a crash. Only run when other
writers are stopped. Does not change verse files or global matcher rules.
"""
import argparse, csv, datetime, fcntl, hashlib, io, json, os, sqlite3, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
NIM = ROOT / 'Meta_Bible_Data/Bible_Noun_Extraction'
sys.path.insert(0, str(NIM))
from ar.run_ar_torah import OUT, OVERRIDES, SOURCE, read_anchors
from ar.run_ar_rest_nt import validate
from matchers import get_matcher

DB = NIM / 'grammar_tables.sqlite3'
BACKUP = HERE / 'exo_12_4_14_25_override_backup.tsv'
RECEIPT = HERE / 'exo_12_4_14_25_applied_receipt.json'
PENDING = HERE / 'exo_12_4_14_25_pending_receipt.json'
LOCK = HERE / 'exo_12_4_14_25_apply.lock'
VERS = {
 (12,4):('002_EXO_012_004','7b48a55dd7607c382a21d725fbe52cd7142c4cce24f7df633fe3ae215779fdfa','fdc5f9876a1a223600e189a0526333dc9de8e8fcd4ca18c20bdff004bc429431'),
 (14,25):('002_EXO_014_025','bb3397e581be56fc05efb5e4f91e60920331d7351f34282afbf8ecd9840d868e','36cd4cd612471ca3b5c85b19107368bc1de8aaaabbec51ed8352464ab6ff275f'),
}
# ch, verse, noun-position, Strong's, exact source surface, expected current,
# new occurrence rendering, unique exact target span, grammar tuple, rationale.
D = [
 (12,4,4,4373,'בְּמִכְסַ֣ת','','عَدَد','بِعَدَدِ',('M','S','أَعْدَاد','N'),'Number of persons determines lamb allocation.'),
 (12,4,8,400,'אָכְל֔וֹ','طَعَام','يَأْكُلُ','يَأْكُلُ',None,'Source consumption is expressed by an Arabic finite verb, not a food noun.'),
 (14,25,3,3517,'בִּכְבֵדֻ֑ת','','مَشَقَّة','بِمَشَقَّةٍ',('F','S','مَشَقَّات','N'),'WLC driving with heaviness is rendered with difficulty.'),
 (14,25,4,4714,'מִצְרַ֗יִם','مِصْرَايِم','الْمِصْرِيُّونَ','الْمِصْرِيُّونَ',None,'Collective Egypt speaks; target explicitly names the Egyptians.'),
 (14,25,8,4714,'בְּמִצְרָֽיִם','مِصْرَايِم','الْمِصْرِيِّينَ','الْمِصْرِيِّينَ',None,'Yahweh fights against Egypt, rendered as the Egyptians in the target.'),
]

def check(condition, msg):
 if not condition: raise RuntimeError(msg)
def sha(x): return hashlib.sha256(x).hexdigest()
def exclusive(path, data):
 with path.open('xb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
def replace_bytes(path, data):
 fd, name = tempfile.mkstemp(prefix='.'+path.name+'.', dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
  os.replace(name,path)
 finally:
  if os.path.exists(name): os.unlink(name)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 check(args.apply,'No changes made: explicit --apply is required.')
 with LOCK.open('a+b') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  check(not any(p.exists() for p in (BACKUP,RECEIPT,PENDING)), 'Existing backup, receipt or pending marker: inspect/recover first.')
  matcher=get_matcher('ar'); anchors=read_anchors();before=OVERRIDES.read_bytes(); texts={}; reviewed=[]
  with OVERRIDES.open(encoding='utf-8',newline='') as f:
   reader=csv.DictReader(f,delimiter='\t');fields=reader.fieldnames;existing=list(reader)
  check(fields==['book','chapter','verse','word_position','strongs_num','rendering','sense_key','reason'],'Override schema changed.')
  keys={}
  for r in existing:
   k=(r['book'],int(r['chapter']),int(r['verse']),int(r['word_position']));check(k not in keys,'Duplicate override key');keys[k]=r
  for (ch,v),(stem,sh,th) in VERS.items():
   source=(SOURCE/f'{stem}_WLC.txt').read_bytes();target=(OUT/f'{stem}_GOI_Ar.txt').read_bytes()
   check(sha(source)==sh and sha(target)==th,f'{stem} WLC or target changed')
   texts[(ch,v)]=target.decode('utf-8').strip()
  for ch,v,pos,strong,surface,old,new,span,grammar,reason in D:
   sid,surf,rendering=anchors[('EXO',ch,v)][pos-1]; key=('EXO',ch,v,pos); text=texts[(ch,v)]
   check((sid,surf,rendering)==(strong,surface,old),f'{key} source/old rendering changed')
   if key == ('EXO',12,4,8):
    context='بِحَسَبِ مَا يَأْكُلُ'
    check(text.count(context)==1, f'{key} contextual phrase is absent or ambiguous')
    span_start=text.index(context)+len(context)-len(span)
    check(text[span_start:span_start+len(span)]==span, f'{key} token offset mismatch')
    check(span_start+len(span)==len(text) or not text[span_start+len(span)].isalpha(), f'{key} token is a prefix of another word')
   else:
    check(text.count(span)==1, f'{key} target span is absent or ambiguous')
    span_start=text.index(span)
   check(matcher.found(new,text),f'{key} target matcher failed')
   if key in keys:
    row=keys[key];check(int(row['strongs_num'])==strong and row['rendering']==old,f'{key} override changed')
   else:
    row={'book':'EXO','chapter':str(ch),'verse':str(v),'word_position':str(pos)};existing.append(row);keys[key]=row
   row.update(strongs_num=str(strong),rendering=new,sense_key=f'H{strong}.AR_CONTEXT_EXO_{ch}_{v}_{pos}',reason=reason)
   reviewed.append({'book':'EXO','chapter':ch,'verse':v,'word_position':pos,'strongs_num':strong,'source_surface':surface,'old':old,'new':new,'target_span':span,'target_start':span_start,'target_end':span_start+len(span),'context_phrase':context if key==('EXO',12,4,8) else None,'citation_grammar':({'gender':grammar[0],'citation_number':grammar[1],'plural_form':grammar[2],'pos':grammar[3]} if grammar else None),'occurrence_form_only':grammar is None,'reason':reason})
  for ch,v in VERS:
   substitutions={d[2]:d[6] for d in D if d[:2]==(ch,v)}
   required=[substitutions.get(i,r) for i,(_,_,r) in enumerate(anchors[('EXO',ch,v)],1)]
   check(all(required),f'EXO {ch}:{v} still has blank anchors')
   failures=validate(texts[(ch,v)],required,matcher);check(not failures,f'EXO {ch}:{v} fails full validation: {failures}')
  cases=[('يَأْكُلُ','بِحَسَبِ مَا يَأْكُلُ',True),('يَأْكُلُ','بِحَسَبِ مَا يَشْرَبُ',False),('الْمِصْرِيُّونَ','فَقَالَ الْمِصْرِيُّونَ',True),('الْمِصْرِيُّونَ','ضِدَّ الْمِصْرِيِّينَ',False),('الْمِصْرِيِّينَ','ضِدَّ الْمِصْرِيِّينَ',True),('الْمِصْرِيِّينَ','فَقَالَ الْمِصْرِيُّونَ',False),('الْمِصْرِيِّينَ','ضِدَّ السُّورِيِّينَ',False)]
  for term,text,want in cases:check(matcher.found(term,text)==want,f'matcher regression: {term} / {text}')
  buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=fields,delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(existing);after=buf.getvalue().encode()
  # Verify the two noun citations already exist with precisely reviewed grammar.
  # Verb and demonym surfaces are occurrence forms, never citation rows.
  con=sqlite3.connect(f'file:{DB}?mode=ro',uri=True);replaced=False
  try:
   citation_checks=[]
   for d in D:
    rendering=d[6];grammar=d[8]
    if grammar is None: continue
    prior=con.execute('SELECT gender,citation_number,plural_form,pos FROM noun_grammar WHERE lang=? AND rendering=?',('ar',rendering)).fetchone()
    check(prior==grammar,f'Missing or conflicting citation grammar for {rendering}: {prior}')
    citation_checks.append({'citation':rendering,'gender':prior[0],'citation_number':prior[1],'plural_form':prior[2],'pos':prior[3]})
   check(OVERRIDES.read_bytes()==before,'Overrides changed during preflight')
   exclusive(BACKUP,before)
   receipt={'status':'APPLIED','reviewed':reviewed,'verses':{f'{ch}:{v}':{'source_sha256':VERS[(ch,v)][1],'target_sha256':VERS[(ch,v)][2]} for ch,v in VERS},'override_before_sha256':sha(before),'override_after_sha256':sha(after),'grammar_citations_checked_readonly':citation_checks,'grammar_mutations':0,'full_anchor_validation':'passed','matcher_tests':len(cases),'limitations':['Matcher is lexical; it does not detect negation or prove semantic adequacy.','Source and target verse files remain unchanged.','Inflected verb and demonym forms are occurrence renderings, not noun-grammar citations.']}
   exclusive(PENDING,(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode())
   replace_bytes(OVERRIDES,after);replaced=True
   updated=read_anchors()
   for d in D:check(updated[('EXO',d[0],d[1])][d[2]-1][2]==d[6],'Post-write anchor mismatch')
   for ch,v in VERS:
    terms=[a[2] for a in updated[('EXO',ch,v)]];check(all(terms) and not validate(texts[(ch,v)],terms,matcher),'Post-write full validation failed')
   os.replace(PENDING,RECEIPT)
  except BaseException:
   if replaced:replace_bytes(OVERRIDES,before)
   if PENDING.exists():PENDING.unlink()
   raise
  finally:con.close()
  print(f'Applied five reviewed occurrences; receipt: {RECEIPT}')
if __name__=='__main__':main()
