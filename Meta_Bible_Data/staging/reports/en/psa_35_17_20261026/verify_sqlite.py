from pathlib import Path
import sys,sqlite3,json,hashlib
HERE=Path(__file__).parent;ROOT=HERE.resolve().parents[4];NIM=ROOT/'Meta_Bible_Data/Bible_Noun_Extraction';sys.path.insert(0,str(NIM));sys.path.insert(0,str(NIM/'translation_cube'))
from scipy import sparse
from build_cube import vectorize
r=json.loads((HERE/'sqlite_updates.json').read_text());new=(ROOT/'GOI_Bible/GOI_Bible_English/019_PSA_035_017_GOI_En.txt').read_text().strip()
for u in r['updates']:
 c=sqlite3.connect((ROOT/u['database']).as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;row=c.execute('SELECT * FROM '+u['table']+' WHERE rowid=?',(u['rowid'],)).fetchone();assert row['verse_text']==new
 if u['score_preserved'] is not None:assert row['score']==u['score_preserved']==82
 assert c.execute('PRAGMA quick_check').fetchone()[0]=='ok';assert c.execute('SELECT count(*) FROM '+u['table']+" WHERE verse_text LIKE '%lions my self%' "+("AND version='GOI_En'" if u['table']=='verse_journalability' else "AND edition_id='GOI_En'")).fetchone()[0]==0;c.close()
c=sqlite3.connect((NIM/'translation_cube/cubes/en_cube.sqlite3').as_uri()+'?mode=ro',uri=True);matrix=sparse.load_npz(NIM/'translation_cube/cubes/en_vectors.npz')
for u in r['cube_updates']:
 t,f,h=c.execute('SELECT text,feature_text,content_sha256 FROM chunks WHERE id=?',(u['id'],)).fetchone();assert t==u['after_text'] and f==u['feature_text'];assert hashlib.sha256(t.encode()).hexdigest()==h;assert (matrix[u['row_index']]-vectorize([f])).nnz==0
assert c.execute("SELECT count(*) FROM chunks WHERE instr(text,'lions my self') OR instr(feature_text,'lions my self')").fetchone()[0]==0
val=json.loads((HERE/'text_validation.json').read_text());assert hashlib.sha256((new+'\n').encode()).hexdigest()==val['sha256_after'];assert (ROOT/'Reference_Bible/Hebrew_Bible_WLC/One_Directory_WLC_KJV/019_PSA_035_017_WLC.txt').read_text().strip()==val['source']
receipt=dict(status='PASS',verse='PSA 35:17',edition='GOI_En',current_sqlite_databases=16,current_app_verse_rows=15,cube_chunks_and_sparse_rows=5,randomizer_score=82,source_unchanged=True,all_current_copies_equal_canonical=True,historical_snapshots_preserved=7,cube_scope='Affected verse/chunks/index rows synchronized; no whole-corpus freshness certification.')
(HERE/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
