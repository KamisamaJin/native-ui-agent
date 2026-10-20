#!/usr/bin/env python3
"""Materialize approved common acquisition inputs after the source barriers."""
import argparse,hashlib,json,shutil,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['d0','final']);a=p.parse_args();assignment=read(R/'private/assignment.json')
 sources={}
 for unit in assignment['units']:
  source=R/'submissions'/unit/a.phase/'seal.json';assert source.is_file(),'Both source capsules must seal first';sources[unit]=sha(source)
  if a.phase=='final':assert(R/'own-corpora'/unit/'final/corpus-seal.json').is_file(),'Own FINAL public endpoint must finish before holdout input release'
 out=R/'private'/('common-inputs-'+a.phase);assert not out.exists();out.mkdir()
 cases=[(R/'design/public',case)for case in ['P1','P2']]
 if a.phase=='final':cases.append((R/'design/private','H1'))
 for base,case in cases:
  dest=out/case;dest.mkdir();shutil.copy2(base/'cases'/case/'fixtures.json',dest/'fixtures.json')
  for platform in ['ios','android']:shutil.copy2(base/'compiled'/case/platform/'actions.json',dest/('actions.'+platform+'.json'))
 files={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()}
 (out/'seal.json').write_text(json.dumps({'createdAtUTC':datetime.now(timezone.utc).isoformat(),'createdAtUnix':time.time(),'phase':a.phase,'sourceSeals':sources,'designSealSHA256':sha(R/'design/private/DESIGN-SEAL.json'),'files':files},indent=2)+'\n')
 print(json.dumps({'phase':a.phase,'cases':[c for _,c in cases],'files':len(files)}))
if __name__=='__main__':main()
