#!/usr/bin/env python3
"""Analyze the blocked Joshua 15 village anchors; write staging evidence only."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'Meta_Bible_Data/Bible_Noun_Extraction'))
from ar.run_ar_torah import OUT,SOURCE,read_anchors
from ar.run_ar_rest_nt import validate
from matcher_ar import ArabicMatcher
queue=[json.loads(x) for x in (HERE/'blank_occurrence_queue.jsonl').read_text().splitlines()]
candidates={r['queue_row']:r for r in map(json.loads,(HERE/'review_batch_b_501_600.jsonl').read_text().splitlines())}
ids=[564,565,566,567,568,583,589,590,594,595,598]
anchors=read_anchors();matcher=ArabicMatcher();records=[]
for verse,nums in [(32,[564,565]),(36,[566,567,568]),(51,[583]),(54,[589,590]),(59,[594,595]),(62,[598])]:
 q=queue[nums[0]-1]; key=('JOS',15,verse);stem=q['stem']; src=(SOURCE/f'{stem}_WLC.txt').read_text();ar=(OUT/f'{stem}_GOI_Ar.txt').read_text()
 assert hashlib.sha256(src.encode()).hexdigest()==q['source_sha256'] and hashlib.sha256(ar.encode()).hexdigest()==q['target_sha256']
 existing=anchors[key]; found=[(i,z) for i,z in enumerate(existing,1) if z[0]==2691 and z[2]=='فِنَاء']; assert len(found)==1,(key,found)
 pos,(_,hebrew,old)=found[0];span='قُرَاهَا' if verse in (32,36) else 'قُرَاهُنَّ'; assert ar.count(span)==1
 before=validate(ar.strip(),[v for _,_,v in existing if v],matcher)
 revised=[span if i==pos else value for i,(_,_,value) in enumerate(existing,1)]
 after=validate(ar.strip(),[v for v in revised if v],matcher)
 additional=[]
 for n in nums:
  cand=candidates[n]; p=int(cand['anchor']['word_position']);assert (cand['stem']==stem and cand['span'] in ar and existing[p-1][0]==int(cand['anchor']['strongs_num']))
  additional.append({'queue_row':n,'position':p,'strongs_num':int(cand['anchor']['strongs_num']),'hebrew':cand['anchor']['source_surface'],'target_span':cand['span'],'proposed_rendering':cand['citation'],'matcher_found':matcher.found(cand['citation'],ar)})
  revised[p-1]=cand['citation']
 after_names=validate(ar.strip(),[v for v in revised if v],matcher)
 records.append({'book':'JOS','chapter':15,'verse':verse,'source_sha256':q['source_sha256'],'target_sha256':q['target_sha256'],'source':src.strip(),'arabic':ar.strip(),'position':pos,'strongs_num':2691,'hebrew':hebrew,'old_rendering':old,'proposed_occurrence_rendering':span,'arabic_citation':'قَرْيَة','grammar':{'pos':'noun','gender':'feminine','number':'broken plural with third-person feminine plural possessive suffix','plural':'قُرًى'},'reason':'WLC חצרים in a town-list context means dependent settlements/villages; Arabic قراها/قراهن explicitly denotes their villages. Existing فناء denotes a courtyard and is absent. The exact occurrence form avoids a global matcher change.','before_failures':before,'after_village_only_failures':after,'additional_names':additional,'after_village_and_names_failures':after_names,'unpopulated_anchor_count':sum(not t for t in revised)})
assert all(not r['after_village_only_failures'] and not r['after_village_and_names_failures'] and all(x['matcher_found'] for x in r['additional_names']) for r in records)
path=HERE/'joshua15_village_corrections.json';path.write_text(json.dumps({'status':'PROPOSED_NOT_APPLIED','global_matcher_changed':False,'records':records},ensure_ascii=False,indent=2)+'\n')
print(path,'verses',len(records),'blocked names',sum(len(r['additional_names']) for r in records))
