#!/usr/bin/env python3
"""Bind original self-check plans to public native stimuli without changing values."""
import argparse,hashlib,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parent
OBSERVATION_FIELDS={'after_target','after_targets','observation_max_scrolls','observe_after'}
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stripped(actions):return [{k:v for k,v in a.items()if k not in OBSERVATION_FIELDS}for a in actions]
def main():
 p=argparse.ArgumentParser();p.add_argument('unit');p.add_argument('--phase',choices=['d0','final'],default='d0');a=p.parse_args();base=R/'submissions'/a.unit;src=base/('initial-agent-output'if a.phase=='d0'else'final-agent-output');out=base/('own-inputs'if a.phase=='d0'else'own-inputs-final');assert not out.exists();out.mkdir()
 files={}
 for case in sorted(p for p in(R/'design/public/cases').iterdir()if p.is_dir()):
  dest=out/case.name;dest.mkdir();shutil.copy2(case/'fixtures.json',dest/'fixtures.json')
  for platform in ['ios','android']:
   planned=src/'plans'/case.name/platform;plan=planned/'plan.json';actions=planned/'actions.json';assert plan.is_file()and actions.is_file(),str(planned)
   original=read(case/('actions.'+platform+'.json'));actual=read(actions)
   assert stripped(original)==stripped(actual),'Original stimulus route/state/ordering changed'
   shutil.copy2(actions,dest/('actions.'+platform+'.json'));files[str(plan.relative_to(base))]=sha(plan);files[str(actions.relative_to(base))]=sha(actions)
 for p in sorted(out.rglob('*')):
  if p.is_file():files[str(p.relative_to(base))]=sha(p)
 (out/'original-plan-binding.json').write_text(json.dumps({'createdAtUnix':time.time(),'files':files,'scope':'Exact original own plans and observation-only action enrichments; original inputs, stimulus order and state identities preserved.'},indent=2)+'\n')
 print(json.dumps({'unit':a.unit,'files':len(files)}))
if __name__=='__main__':main()
