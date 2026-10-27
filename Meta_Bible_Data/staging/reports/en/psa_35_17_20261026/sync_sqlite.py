"""Synchronize owner-approved GOI_En PSA35:17; preserve references and historical snapshots."""
from pathlib import Path
import json,sqlite3,sys,hashlib,datetime
HERE=Path(__file__).parent;ROOT=HERE.resolve().parents[4];NIM=ROOT/'Meta_Bible_Data/Bible_Noun_Extraction';sys.path.insert(0,str(NIM));sys.path.insert(0,str(NIM/'translation_cube'))
from scipy import sparse
from build_cube import vectorize,WINDOW
from target_adapters import TargetAdapter
NEW=(ROOT/'GOI_Bible/GOI_Bible_English/019_PSA_035_017_GOI_En.txt').read_text().strip()
assert NEW=='Lord, how long will you look on? Rescue my soul from their destructions, my precious life from the young lions.'
inventory=json.loads((HERE/'sqlite_inventory.json').read_text());records=[];historical=[]
def archive(path):return '/archive/' in path or '/local_backups/' in path or '/staging/deploy/' in path or '/.GOIBible-win-before-' in path
for item in inventory['databases']:
 if not item['matches']:continue
 rel=item['path']
 if archive(rel):historical.append(rel);continue
 if rel.endswith('/en_cube.sqlite3'):continue
 path=ROOT/rel;assert path.stat().st_nlink==1
 conn=sqlite3.connect(path,timeout=30);conn.row_factory=sqlite3.Row
 try:
  conn.execute('BEGIN IMMEDIATE')
  for match in item['matches']:
   assert match['column']=='verse_text';table=match['table'];assert table in ('verses','verse_journalability')
   old=dict(conn.execute(f'SELECT rowid,* FROM {table} WHERE rowid=?',(match['rowid'],)).fetchone());assert old['chapter']==35 and old['verse']==17
   if table=='verses':assert old['edition_id']=='GOI_En' and old['conical']==19 and old['book']=='PSA'
   else:assert old['version']=='GOI_En' and old['canonical']==19 and old['osis']=='PSA'
   assert 'lions my self' in old['verse_text'] or old['verse_text']==NEW
   conn.execute(f'UPDATE {table} SET verse_text=? WHERE rowid=?',(NEW,match['rowid']))
   records.append(dict(database=rel,table=table,rowid=match['rowid'],before=match['value'],after=NEW,score_preserved=old.get('score'),edition='GOI_En'))
  conn.commit();assert conn.execute('PRAGMA quick_check').fetchone()[0]=='ok';conn.execute('PRAGMA wal_checkpoint(PASSIVE)')
 finally:conn.close()
# Regenerate all affected cube windows with the production adapter; keep source facts/other coordinates.
path=NIM/'translation_cube/cubes/en_cube.sqlite3';conn=sqlite3.connect(path);conn.row_factory=sqlite3.Row;adapter=TargetAdapter('en')
chunks=[dict(r) for r in conn.execute("SELECT * FROM chunks WHERE language='en' AND book='PSA' AND chapter=35 AND verse=17 ORDER BY id")];assert len(chunks)==5
updates=[]
for old in chunks:
 if old['chunk_type']=='verse':text=NEW
 else:
  ob=conn.execute('SELECT t.* FROM target_observations t JOIN noun_occurrences o ON o.id=t.occurrence_id WHERE o.book=? AND o.chapter=? AND o.verse=? AND o.anchor_position=?',('PSA',35,17,old['anchor_position'])).fetchone();matches=adapter.locate(ob['rendering'],NEW)
  if len(matches)>1:
   # H5315 is the explicit soul noun; life renders the later יחידתי, outside this noun anchor.
   assert ob['rendering']=='soul'
   matches=[v for v in matches if v.observed==ob['observed_form']]
  assert len(matches)==1;assert matches[0].observed==ob['observed_form'];text=adapter.window(NEW,matches[0],WINDOW)
 assert old['feature_text'].startswith(old['text']);features=text+old['feature_text'][len(old['text']):];index=conn.execute('SELECT row_index FROM vector_rows WHERE chunk_id=?',(old['id'],)).fetchone()[0]
 updates.append(dict(id=old['id'],row_index=index,before_text=old['text'],after_text=text,feature_text=features,content_sha256=hashlib.sha256(text.encode()).hexdigest()))
index_path=path.with_name('en_vectors.npz');matrix=sparse.load_npz(index_path);patch=vectorize([r['feature_text'] for r in updates]);assert patch.shape[1]==matrix.shape[1]
parts=[];cursor=0
for n,r in sorted(enumerate(updates),key=lambda v:v[1]['row_index']):
 i=r['row_index'];parts.extend([matrix[cursor:i],patch[n:n+1]]);cursor=i+1
parts.append(matrix[cursor:]);new_matrix=sparse.vstack(parts,format='csr');assert matrix.shape==new_matrix.shape
pending=index_path.with_name('en_vectors.psa35_17.pending.npz');sparse.save_npz(pending,new_matrix,compressed=True)
try:
 conn.execute('BEGIN IMMEDIATE')
 for r in updates:conn.execute('UPDATE chunks SET text=?,feature_text=?,content_sha256=? WHERE id=?',(r['after_text'],r['feature_text'],r['content_sha256'],r['id']))
 conn.execute("UPDATE target_observations SET feature_confidence=feature_confidence||'+direct_source_span_PSA35_17' WHERE occurrence_id=(SELECT id FROM noun_occurrences WHERE book='PSA' AND chapter=35 AND verse=17 AND strongs_num=5315)")
 conn.execute('INSERT OR REPLACE INTO metadata(key,value) VALUES(?,?)',('incremental_text_patch_PSA_35_17',json.dumps(dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),verse_sha256=hashlib.sha256(NEW.encode()).hexdigest(),scope='This coordinate and sparse rows only; original whole-corpus build fingerprints are retained, not recertified.'))))
 conn.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES('vector_nonzero',?)",(str(new_matrix.nnz),));conn.commit();pending.replace(index_path)
except BaseException:conn.rollback();raise
assert conn.execute('PRAGMA quick_check').fetchone()[0]=='ok';conn.close()
report=dict(status='SYNCED',databases_inventoried=inventory['databases_scanned'],active_databases_updated=len({r['database'] for r in records})+1,verse_rows_updated=len(records),cube_chunks_updated=len(updates),sparse_rows_updated=len(updates),historical_snapshots_preserved=historical,updates=records,cube_updates=updates,source_and_reference_texts_changed=False)
(HERE/'sqlite_updates.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('updates','cube_updates')},ensure_ascii=False))
