#!/usr/bin/env python3
"""SDK-free replay of pre-business controls and disclosed scope calibration."""
import argparse,ast,hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replay(tool,plans):
 code='''import sys,json\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\nimport native_checks as n,design_contract as d\nr=Path(sys.argv[2]);plans=Path(sys.argv[3]);lock=d.load(plans/'design-lock.json');result={}\nfor platform in ['ios','android']:\n for version in ['v5-cold','v6-cold','v6-warm','v5-warm']:\n  key=platform+'-'+version;p=r/'generic-evidence'/key;o=d.load(p/'observation.json');plan=d.load(plans/('plan.'+platform+'.json'));report=n.evaluate(plan,o,platform,design_lock=lock,design_sha256=d.digest(lock));result[key]={'counts':report['counts'],'statuses':{v['id']:v['status']for v in report['assertions']},'snapshots':len(o['snapshots'])}\nprint(json.dumps(result))'''
 return json.loads(subprocess.check_output([sys.executable,'-B','-c',code,str(tool/'scripts'),str(R),str(plans)],text=True))
def build():
 alpha=R/'development/v6-alpha'
 for rel,h in read(R/'development/alpha-seal.json')['files'].items():assert sha(alpha/rel)==h
 original=replay(alpha,R/'generic');current=replay(REPO/'native-ui-agent',R/'generic-scoped')
 rows={}
 for key,v in current.items():
  platform,version=key.split('-',1);path=R/'generic-evidence'/key
  for rel,h in read(path/'portable-sha256.json').items():assert sha(path/rel)==h,(key,rel)
  m=read(path/'manifest.json');o=read(path/'observation.json');command=read(R/'generic/commands'/(key+'.json'))
  assert m['native_test_count']==1 and command['exitCode']==0
  for rel,h in m['image_hashes'].items():assert sha(path/rel)==h
  assert v['counts']==({'passed':15,'failed':0,'unassessed':12}if platform=='ios'else{'passed':27,'failed':0,'unassessed':0}),(key,v['counts'])
  assert original[key]['counts']==({'passed':15,'failed':8,'unassessed':4}if platform=='ios'else{'passed':27,'failed':0,'unassessed':0})
  for idx in [1,2,4,5]:
   step=o['steps'][idx];bundle=step['observation_set']
   assert bundle['all_targets_observed'] is True
   assert bundle['binding']==bundle['binding_after_observation']==step['binding_after']
   assert bundle['scrolls_used']<=bundle['scroll_budget']
  assert o['steps'][3]['observation_set']['scrolls_used']==0
  assert o['steps'][3]['observation_set']['targets'][0]['status']=='unavailable'
  rows[key]={'originalUnscopedCounts':original[key]['counts'],'scopedCounts':v['counts'],'snapshots':v['snapshots'],'wallSeconds':command['wallSeconds'],'scrolls':sum(s.get('observation_set',{}).get('scrolls_used',0)for s in o['steps'])}
 for platform in ['ios','android']:
  a=current[platform+'-v5-warm']['statuses'];b=current[platform+'-v6-warm']['statuses'];assert a==b
 old=ast.parse((R/'baseline-v5/scripts/native_checks.py').read_text());new=ast.parse((REPO/'native-ui-agent/scripts/native_checks.py').read_text())
 function=lambda tree:ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='callback_verdict'),include_attributes=False)
 assert function(old)==function(new)
 return {'status':'PASS','runs':rows,'warmWallChangesPercent':{p:(rows[p+'-v6-warm']['wallSeconds']/rows[p+'-v5-warm']['wallSeconds']-1)*100 for p in ['ios','android']},'scope':'Eight real native commands, equal sources/inputs/targets. Original incorrect AX-vs-layout scope failures preserved. Scoped replay is a common pre-business calibration, not new images or a blind product repair. No native fact gain/loss in these controls; timing is one shared-Mac sample per configuration, not a statistical speed claim.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();result=build();out=R/'generic-summary.json'
 if a.write:out.write_text(json.dumps(result,indent=2)+'\n')
 else:assert read(out)==result
 print(json.dumps({'status':'PASS','warmWallChangesPercent':result['warmWallChangesPercent']}))
if __name__=='__main__':main()
