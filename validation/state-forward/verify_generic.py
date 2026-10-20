#!/usr/bin/env python3
"""Replay neutral native facts and independently check evidence/callback boundaries."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'candidate-v5/scripts'))
import native_checks as checks
def read(p):return json.loads(p.read_text())
def main():
 plan=read(R/'generic/compiled/plan.json');summary={}
 for platform in ['ios','android']:
  for version in ['v4-v1','v5-v1','v4-warm','v5-warm']:
   name=platform+'-'+version;d=R/'generic-evidence'/name
   o=read(d/'observation.json');m=read(d/'manifest.json')
   assert m['native_test_count']==1 and m['status']in {'passed','captured_not_graded'}
   for image,sha in m['image_hashes'].items():
    assert hashlib.sha256((d/image).read_bytes()).hexdigest()==sha
   result=checks.evaluate(plan,o,platform)
   expected={'passed':15,'failed':0,'unassessed':1} if version.startswith('v5') else {'passed':7 if platform=='ios'else 6,'failed':0,'unassessed':9 if platform=='ios'else 10}
   assert result['counts']==expected,(name,result['counts'])
   assert result['assertions'][-1]['status']=='unassessed'
   assert not any(s['complete']for s in result['states'].values())
   if version.startswith('v5'):
    for i in [1,2,4,5]:
     step=o['steps'][i];bundle=step['observation_set']
     assert bundle['all_targets_observed']is True
     assert bundle['scrolls_used']<=bundle['scroll_budget']
     assert bundle['binding']==step['binding_after']==bundle['binding_after_observation']
     assert step['dispatch']['event_end']==step['binding_after']['event_revision']
    missing=o['steps'][3]['observation_set']
    assert missing['scrolls_used']==0 and missing['all_targets_observed']is False
    assert missing['targets'][0]['status']=='unavailable'
    negative=read(R/f'generic/{platform}-negative-plan.json')
    neg=checks.evaluate(negative,o,platform)
    assert neg['counts']=={'passed':11,'failed':4,'unassessed':1}
    assert {f['state']for f in neg['machine_findings']}=={'expanded','continued','updated','disabled'}
    # Replays intentionally mutate copied metadata, never originals. An input,
    # process, event or image mismatch must withhold every fact in that target set.
    for field,value in [('instance','different'),('event_revision',999),('input_sha256','changed')]:
     altered=copy.deepcopy(o);s=altered['steps'][1];idx=s['observation_set']['snapshot_indices'][-1]
     altered['snapshots'][idx]['binding'][field]=value
     verdict=checks.evaluate(plan,altered,platform)
     assert all(a['status']=='unassessed'for a in verdict['assertions']if a['state']=='expanded')
   command=read(R/'generic/commands'/(name+'.json'))
   summary[name]={'counts':result['counts'],'snapshots':len(o['snapshots']),'wall_seconds':command['wall_seconds'],
                  'native_test_count':m['native_test_count'],'callback_disabled':'unassessed'}
 print(json.dumps({'status':'PASS','runs':summary},indent=2))
if __name__=='__main__':main()
