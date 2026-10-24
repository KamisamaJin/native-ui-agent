from pathlib import Path
import json,time,hashlib
O=Path(__file__).resolve().parent
B=O.parents[3]
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
count=0
for source in ['source-a','source-b']:
 s=load(O/source/'source-judge.json');assert set(s)=={'review','attributions'}
 cat=load(B/'source-evaluation-inputs/final/T2'/source/'catalog.json')
 assert len(s['review']['decisions'])==len(cat['rows'])==107
 assert {r['review_id'] for r in cat['rows']}=={r['review_id'] for r in s['review']['decisions']}
 assert not s['attributions']
 for plat in ['ios','android']:
  for case in ['P1','P2','H1']:
   p=O/source/plat/case;j=load(p/'judge.json');c=load(B/'evaluation-inputs/final/T2'/source/plat/case/'catalog.json')
   assert set(j)=={'review','attributions'} and set(j['review'])=={'version','catalog_sha256','observation_sha256','decisions'}
   assert len(j['review']['decisions'])==154
   assert {r['review_id'] for r in c['rows'] if r['method']=='visual'}=={r['review_id'] for r in j['review']['decisions']}
   assert j['review']['catalog_sha256']==c['catalog_sha256']
   assert load(p/'self-schema-check.json')['schema']=='accepted'
   count+=1
assert count==12
assert all(q['matches'] for q in load(O/'input-hash-verification.json'))
phase=load(O/'phase.json');phase['endUnix']=time.time();phase['status']='complete';(O/'phase.json').write_text(json.dumps(phase,indent=2)+'\n')
files={str(p.relative_to(O)):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SEAL.json' and '__pycache__' not in p.parts}
seal={'sealedAtUnix':time.time(),'files':files};(O/'SEAL.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps({'sealedAtUnix':seal['sealedAtUnix'],'sealed_files':len(files),'seal_sha256':sha(O/'SEAL.json'),'task_directory':str(O)}))
