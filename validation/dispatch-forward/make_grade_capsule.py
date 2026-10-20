#!/usr/bin/env python3
"""Anonymous, hash-bound raw evidence transfer. No grade/expected values are read."""
import argparse,hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst)
def ref(root,p):return {'path':str(p.relative_to(root)),'sha256':sha(p)}
def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['d0','final'],required=True);p.add_argument('--anonymous-id',required=True);p.add_argument('--source-capsule',type=Path,required=True);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);a=p.parse_args();out=a.destination.resolve();assert not out.exists();out.mkdir(parents=True);sources=[];observations=[];seal=json.loads((a.source_capsule/'seal.json').read_text())
 for rel,h in seal['files'].items():
  src=a.source_capsule/'source'/rel;assert sha(src)==h;dst=out/'source'/rel;copy(src,dst);sources.append(ref(out,dst))
 for src,name in [(R/'bridges/Bridge.swift','bridges/Bridge.swift'),(R/'bridges/ObserverBridge.kt','bridges/ObserverBridge.kt'),(R/'common-host/Package.swift','alerttoast/Package.swift')]:
  dst=out/'source'/name;copy(src,dst);sources.append(ref(out,dst))
 cases=['C01','C02','C03','C04']+(['H01','H02'] if a.phase=='final' else [])
 for platform in ['ios','android']:
  for case in cases:
   native=a.corpus/platform/case;obs=native/'observation.json'
   if not obs.is_file():continue
   dest=out/'native'/platform/case;copy(obs,dest/'observation.json');copy(native/'fixtures.json',dest/'fixtures.json');copy(a.inputs/case/'mapping.json',dest/'mapping.json')
   for snap in json.loads(obs.read_text())['snapshots']:
    rel=snap['screenshot'];target=(dest/rel).resolve();assert target.is_relative_to(dest.resolve());copy(native/rel,target)
   observations.append({'platform':platform,'case':case,'observation':ref(out,dest/'observation.json'),'fixture':ref(out,dest/'fixtures.json'),'mapping':ref(out,dest/'mapping.json'),'model_pointers':{'initial':'/initial','replacement':'/updates/0'}})
 save(out/'manifest.json',{'version':1,'phase':a.phase,'anonymous_id':a.anonymous_id,'source_files':sources,'observations':observations})
 save(out/'capsule-seal.json',{'createdAtUTC':datetime.now(timezone.utc).isoformat(),'phase':a.phase,'anonymous_id':a.anonymous_id,'files':{str(f.relative_to(out)):sha(f) for f in sorted(out.rglob('*')) if f.is_file()}})
 print(json.dumps({'phase':a.phase,'anonymous_id':a.anonymous_id,'observations':len(observations),'destination':str(out)}))
if __name__=='__main__':main()
