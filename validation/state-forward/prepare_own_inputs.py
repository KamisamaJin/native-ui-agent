#!/usr/bin/env python3
"""Bind sealed public-derived review plans to the unchanged native stimulus routes."""
import argparse,hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--plan-archive',type=Path,required=True);a=p.parse_args()
seal=read(a.workspace/'agent-output/plans-seal.json');listed=seal['files']
items=listed.items()if isinstance(listed,dict)else[(x['path'],x['sha256'])for x in listed]
for rel,h in list(items)+list(seal.get('supporting_scripts',{}).items()):assert sha(a.workspace/rel)==h,rel
assert not a.output.exists()and not a.plan_archive.exists()
shutil.copytree(a.workspace/'agent-output',a.plan_archive,ignore=shutil.ignore_patterns('compile-*','__pycache__'))
allowed={'after_target','after_targets','observe_after','observation_max_scrolls','name','expect_callback'}
for case in sorted(p for p in(R/'public-native-inputs').iterdir()if p.is_dir()):
 dest=a.output/case.name;shutil.copytree(case,dest);original=read(case/'actions.json')
 plans=a.workspace/'agent-output/review-plan'/case.name
 for platform in ['ios','android']:
  chosen=plans/('actions.'+platform+'.json')
  if not chosen.exists():chosen=plans/'actions.json'
  if not chosen.exists():continue
  enriched=read(chosen);assert len(enriched)==len(original)
  for old,new in zip(original,enriched):
   assert {k:v for k,v in old.items()if k not in allowed}=={k:v for k,v in new.items()if k not in allowed},'Original stimulus/navigation/state changed'
  shutil.copy2(chosen,dest/('actions.'+platform+'.json'))
files={str(p.relative_to(a.output)):sha(p)for p in sorted(a.output.rglob('*.json'))}
(a.output/'original-plan-binding.json').write_text(json.dumps({'createdAtUTC':datetime.now(timezone.utc).isoformat(),'plansSealSHA256':sha(a.workspace/'agent-output/plans-seal.json'),'files':files,'scope':'All original stimulus routes preserved; only declared post-observation requests and callback checks vary by builder.'},indent=2)+'\n')
print(json.dumps({'output':str(a.output),'planArchive':str(a.plan_archive)}))
