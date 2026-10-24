#!/usr/bin/env python3
"""Same required state/target/dispatch coverage, no extra U or known conflict."""
import argparse,json
import sys
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'development/candidate-attempt-1/scripts'))
import acceptance
def read(p):return json.loads(p.read_text())
def build():
 pairs=[]
 for case in ['ordinary400','narrow280-large']:
  for rep in [1,2]:
   results=[]
   for strategy in ['legacy','coalesced']:
    name=case+'-r'+str(rep)+'-'+strategy
    raw=R/'neutral-captures'/name;record=read(R/'operators/benchmark-logs'/(name+'.result.json'));report=read(raw/'automatic.json');obs=read(raw/'observation.json');manifest=read(raw/'manifest.json')
    results.append({'strategy':strategy,'record':record,'report':report,'observation':obs,'manifest':manifest})
   a,b=results;old={v['id']:v for v in a['report']['assertions']};new={v['id']:v for v in b['report']['assertions']}
   assert old.keys()==new.keys()
   loss=[k for k in old if old[k]['status']!='unassessed'and new[k]['status']=='unassessed']
   conflicts=[k for k in old if{old[k]['status'],new[k]['status']}=={'passed','failed'}]
   new_unknown=[k for k in old if new[k]['status']=='unassessed'and old[k]['status']!='unassessed']
   dispatch=[]
   for value in results:
    dispatch.append([{k:step.get(k)for k in ['index','type','outcome','dispatch','callback_delta','fixture_index_before','fixture_index_after']}for step in value['observation'].get('steps',[])])
   required_equal=a['record']['required_coverage']==b['record']['required_coverage']
   oracle=next(v for v in read(R/'neutral/oracle.json')['cases']if v['case']==case)['required_environment']
   expected={k:oracle[k]for k in ['direction','theme','dynamic_type']};expected.update(width=oracle['offered_width_pt'],height=oracle['viewport_height_pt'])
   environments=[acceptance.environment(v['observation'],expected,'ios')for v in results]
   eligible=required_equal and all(v['record']['exitCode']==0 and v['record'].get('coverage',{}).get('satisfied')for v in results)and not(loss or conflicts or new_unknown)and all(v['status']=='P'for v in environments)
   pairs.append({'case':case,'repetition':rep,'order':['legacy','coalesced']if rep==1 else['coalesced','legacy'],'sameRequiredCoverage':required_equal,'noKnownLoss':not loss,'lostSupported':loss,'knownConflicts':conflicts,'extraUnknown':new_unknown,'speedEligible':eligible,
    'legacySeconds':a['record']['wallSeconds'],'coalescedSeconds':b['record']['wallSeconds'],'reduction':1-b['record']['wallSeconds']/a['record']['wallSeconds']if eligible else None,
    'counts':[v['report']['counts']for v in results],'environments':environments,'nativeManifests':[v['manifest']for v in results],'originalDispatch':dispatch,'operations':b['observation'].get('operations'),
    'nativeLogFindQueries':[sum('Find the'in line for line in (R/'neutral-captures'/(case+'-r'+str(rep)+'-'+v['strategy'])/'test.log').read_text().splitlines())for v in results],
    'scope':'Acquisition and automatic evidence equivalence. Qualitative propositions are not silently passed; native dispatch records and independent completion review remain required.'})
 return {'pairs':pairs,'allEligible':all(v['speedEligible']for v in pairs),'resourceSeconds':{s:sum(v[s+'Seconds']for v in pairs)for s in ['legacy','coalesced']},'scope':'Same source/inputs/required coverage on a neutral host. Cold/warm build/native stages and order retained; not a population latency claim or exclusive blind repair advantage.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();value=build();path=R/'benchmark-summary.json'
 if a.check:assert read(path)==value
 else:
  assert not path.exists();path.write_text(json.dumps(value,indent=2)+'\n')
 print(json.dumps({'allEligible':value['allEligible'],'pairs':[{k:v[k]for k in ['case','repetition','speedEligible','legacySeconds','coalescedSeconds','reduction','counts']}for v in value['pairs']]}))
