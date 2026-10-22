#!/usr/bin/env python3
import json,hashlib,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'development/native-v8-attempt1/scripts'))
import design_contract as d,acceptance,native_pixels

def files(root):return{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(root.rglob('*'))if p.is_file()and p.name!='SEAL.json'and'__pycache__'not in p.parts}
def main():
 for judge in ['J1','J2']:
  p=R/'neutral-judges'/judge;assert d.load(p/'SEAL.json')['files']==files(p)
 design=R/'neutral/design';lock=d.load(design/'lock.json');policy=d.load(design/'policy.json');approval=d.load(design/'approval.json');out=R/'neutral-consensus';assert not out.exists();out.mkdir();summary=[]
 for pl in ['ios','android']:
  for case in ['N1','N2']:
   base=R/'neutral-checks'/pl/case;raw=R/'neutral-evidence'/pl/case;op=raw/'observation.json'
   report=acceptance.evaluate(d.load(base/'plan.json'),lock,approval['design_lock_sha256'],policy,approval['policy_sha256'],d.load(op),native_pixels.sha(op),raw,pl,d.load(R/'neutral'/case/('environment.'+pl+'.json')),d.load(R/'neutral-judges/J1'/pl/case/'judge.json'),d.load(R/'neutral-judges/J2'/pl/case/'judge.json'))
   (out/(pl+'-'+case+'.json')).write_text(json.dumps(report,indent=2)+'\n');summary.append({'platform':pl,'case':case,'counts':report['counts'],'environment':report['environment']['status']})
 (out/'summary.json').write_text(json.dumps({'completedAtUnix':time.time(),'runs':summary,'scope':'Independent neutral panel consensus, not a product trial or human gold.'},indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
