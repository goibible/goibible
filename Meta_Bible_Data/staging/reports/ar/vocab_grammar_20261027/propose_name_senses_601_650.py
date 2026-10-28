#!/usr/bin/env python3
"""Prepare occurrence-specific Joshua name senses without global grammar writes."""
import hashlib,json,pathlib,sqlite3,sys
from collections import defaultdict
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[4];NIM=ROOT/'Meta_Bible_Data/Bible_Noun_Extraction';sys.path.insert(0,str(NIM))
from ar.run_ar_torah import SOURCE,OUT,read_anchors
from ar.run_ar_rest_nt import validate
from matcher_ar import ArabicMatcher
selected=[602,611,616,618,620,631,632,636,643,644]
source_candidates={r['queue_row']:r for r in map(json.loads,(HERE/'reviewed_proposals_601_650_c.jsonl').read_text().splitlines())}
audits={r['queue_row']:r for r in map(json.loads,(HERE/'independent_audit_601_650_a.jsonl').read_text().splitlines())}
anchors=read_anchors();matcher=ArabicMatcher();db=sqlite3.connect(f'file:{NIM}/grammar_tables.sqlite3?mode=ro',uri=True);groups=defaultdict(list)
for number in selected:
 x=source_candidates[number];audit=audits[number];a=x['anchor'];key=(a['book_code'],int(a['chapter']),int(a['verse']));p=int(a['word_position']);src=(SOURCE/f"{x['stem']}_WLC.txt").read_bytes();target=(OUT/f"{x['stem']}_GOI_Ar.txt").read_bytes();text=target.decode()
 assert hashlib.sha256(src).hexdigest()==x['source_sha256'] and hashlib.sha256(target).hexdigest()==x['target_sha256']
 assert text[x['target_start']:x['target_end']]==x['target_span'] and text.count(x['target_span'])==1
 sid,surface,prior=anchors[key][p-1];assert sid==int(a['strongs_num']) and surface==a['source_surface'] and not prior
 assert matcher.found(x['citation'],text)
 old=db.execute('SELECT gender,citation_number,plural_form,pos FROM noun_grammar WHERE lang=? AND rendering=?',('ar',x['citation'])).fetchone();assert old and old[3]=='N' and tuple(old)==tuple(audit['existing_grammar'])
 groups[key].append({'queue_row':number,'stem':x['stem'],'anchor':a,'source_sha256':x['source_sha256'],'target_sha256':x['target_sha256'],'target_span':x['target_span'],'target_start':x['target_start'],'target_end':x['target_end'],'occurrence_rendering':x['citation'],'sense_key':f"H{sid}.AR_CONTEXT_{a['book_code']}_{a['chapter']}_{a['verse']}",'sense_grammar':{'pos':'PN','gender':'U','citation_number':'S','plural_form':''},'existing_global_grammar':old,'global_grammar_action':'preserve unchanged','reason':'WLC identifies a named town or boundary feature; the exact Arabic toponym occupies the same contextual position. Grammar describes this occurrence-specific proper-name sense only, not all meanings of its spelling.'})
result=[]
for key,items in groups.items():
 additions={int(x['anchor']['word_position']):x['occurrence_rendering'] for x in items};required=[additions.get(i,v) for i,(_,_,v) in enumerate(anchors[key],1)];text=(OUT/f"{items[0]['stem']}_GOI_Ar.txt").read_text().strip();failures=validate(text,[v for v in required if v],matcher)
 assert not failures,(key,failures)
 for item in items:item['populated_anchor_check']={'pass':True,'failures':failures,'populated_count':sum(bool(v) for v in required),'remaining_blank_count':sum(not bool(v) for v in required)};result.append(item)
out=HERE/'name_senses_601_650_proposals.jsonl';out.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in sorted(result,key=lambda r:r['queue_row'])),encoding='utf-8');print(out,len(result))
