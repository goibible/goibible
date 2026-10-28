#!/usr/bin/env python3
"""Prepare only reviewed Arabic occurrence proposals; no canonical writes."""
import hashlib,json,sys
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'Meta_Bible_Data/Bible_Noun_Extraction'))
from ar.run_ar_torah import OUT,SOURCE,read_anchors
from ar.run_ar_rest_nt import validate
from matcher_ar import ArabicMatcher
queue=[json.loads(x) for x in (HERE/'blank_occurrence_queue.jsonl').read_text().splitlines()]
audit={x['queue_row']:x for x in map(json.loads,(HERE/'independent_audit_b_101_200.jsonl').read_text().splitlines())}
# Verified citation, POS, gender, contextual number, plural; plural null means unasserted.
grammar={102:('عَدَد','noun','masculine','singular','أَعْدَاد'),103:('حِفْظ','verbal noun','masculine','singular',None),104:('حِفْظ','verbal noun','masculine','singular',None),105:('مَشَقَّة','noun','feminine','singular','مَشَقَّات'),107:('إِنَاء','noun','masculine','singular','آنِيَة'),109:('أَسْفَل','adverbial noun','masculine','singular',None),110:('مِثْقَب','noun','masculine','singular','مَثَاقِب'),114:('نَقْب','verbal noun','masculine','singular',None),117:('وَقِيد','noun','masculine','singular',None),122:('سِلْسِلَة','noun','feminine','plural','سَلَاسِل'),123:('دِرْع','noun','feminine','singular','دُرُوع'),124:('رُبْع','noun','masculine','singular','أَرْبَاع'),125:('كَفَّارَة','noun','feminine','plural','كَفَّارَات'),130:('كَسْرَة','noun','feminine','singular','كَسَرَات'),132:('نُقْرَة','noun','feminine','singular','نُقَر'),134:('غَزْل','noun','masculine','singular',None),143:('دِرْع','noun','feminine','singular','دُرُوع'),147:('جَرِيش','noun','masculine','mass',None),148:('جَرِيش','noun','masculine','mass',None),149:('عُصْعُص','noun','masculine','singular','عَصَاعِص')}
# 107/110 previously integrated; nevertheless retain explicit verification.
# Correct source-position error for first quarter of a hin of oil.
corrected={124:'بِرُبْعِ'}
anchors=read_anchors(); matcher=ArabicMatcher(); rows=[]
for i in range(101,151):
 q=queue[i-1]; a=q['anchor']; report=audit[i]; key=(a['book_code'],int(a['chapter']),int(a['verse'])); p=int(a['word_position']); stem=q['stem']
 source=(SOURCE/f'{stem}_WLC.txt').read_text(); target=(OUT/f'{stem}_GOI_Ar.txt').read_text()
 live_hash={'source':hashlib.sha256(source.encode()).hexdigest(),'target':hashlib.sha256(target.encode()).hexdigest()}
 assert live_hash['source']==q['source_sha256'] and live_hash['target']==q['target_sha256'],(i,'coordinate changed')
 assert source.strip()==q['source'] and target.strip()==q['arabic']
 sid,surface,current=anchors[key][p-1];assert sid==int(a['strongs_num']) and surface==a['source_surface'],(i,'anchor mismatch')
 proposed=grammar.get(i); span=corrected.get(i,report['candidate_span']); rec={'queue_row':i,'stem':stem,'anchor':a,'source_sha256':q['source_sha256'],'target_sha256':q['target_sha256'],'audit_decision':report['decision'],'audit_reason':report['rationale'],'current_rendering':current,'decision':'UNRESOLVED','target_span':span or None,'citation':None,'grammar':None,'matcher_found':None,'populated_anchor_validation':None,'reason':report['rationale']}
 if proposed:
  citation,pos,gender,number,plural=proposed
  assert span and span in target,(i,span)
  rec.update(citation=citation,grammar={'pos':pos,'gender':gender,'number':number,'plural':plural},target_start=target.index(span),target_end=target.index(span)+len(span))
  rec['matcher_found']=bool(matcher.found(citation,target))
  # Verify all currently populated anchors in this verse, with the proposed mapping substituted.
  terms=[citation if j==p else term for j,(_,_,term) in enumerate(anchors[key],1)]
  errors=validate(target.strip(),[t for t in terms if t],matcher)
  rec['populated_anchor_validation']={'pass':not bool(errors),'errors':errors,'populated_count':sum(bool(t) for t in terms),'blank_count':sum(not bool(t) for t in terms)}
  if current and current!=citation:rec['reason']='Existing occurrence rendering differs; integration requires reconciliation.'
  elif not rec['matcher_found']:rec['reason']='Existing Arabic matcher does not recognize proposed citation in verse.'
  elif errors:rec['reason']='At least one currently populated anchor fails verse validation.'
  else:
   rec['decision']='ALREADY_MAPPED' if current else 'READY'
   rec['reason']='WLC source anchor aligns to the identified Arabic expression; contextual Arabic morphology reviewed. '
   if i==124:rec['reason']+='First quarter of a hin refers to oil; corrected earlier wine occurrence.'
   else:rec['reason']+=report['rationale']
 elif report['decision']=='APPROVED':rec['reason']='Alignment plausible, but Arabic POS/gender/number or plural has not been independently confirmed; keep unresolved.'
 rows.append(rec)
path=HERE/'proposals_a_101_150.jsonl';path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
print(path,dict(Counter(x['decision'] for x in rows)))
