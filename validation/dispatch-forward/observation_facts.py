#!/usr/bin/env python3
"""Recompute geometric acquisition facts separately from business verdicts."""
import argparse,json
from pathlib import Path
from contract import R,checks,read,sha

def visible(o,step,index,selector,platform):
 if type(index)is not int or not 0<=index<len(o.get('snapshots',[])):return {'status':'unavailable','reason':'missing original frame'}
 snap=o['snapshots'][index]
 if snap.get('capture_consistent')is False or snap.get('binding')!=step.get('binding_after'):return {'status':'unavailable','reason':'inconsistent input/frame binding','snapshot':index}
 result=checks.resolve(snap,selector,platform);semantic=result['semantic'];control=result['control']
 if not result['facts'].get('unique')or not semantic:return {'status':'unavailable','reason':'nonunique or absent semantic target','snapshot':index}
 def fields(n):return {'fullyVisible':n.get('fully_within_viewport',n.get('fully_visible')),'intersectsViewport':n.get('intersects_viewport')}
 return {'status':'observed','snapshot':index,'resolution':result['resolution'],'semantic':fields(semantic),'nativeControl':fields(control)if control else None}
def summarize(root,inputs):
 actions=[];states=[];images=0;tests=0
 for platform in ['ios','android']:
  for p in sorted((root/platform).glob('*-command.json')):
   command=read(p);case=command['case'];native=root/platform/case;manifest=native/'manifest.json';obs=native/'observation.json'
   if manifest.exists():tests+=read(manifest).get('native_test_count',0)
   mapping=read(inputs/case/'mapping.json');o=read(obs)if obs.exists()else {};images+=len(o.get('snapshots',[]))
   for checkpoint,m in mapping.items():
    if m['full_content']:
     spec={'id':m['state_id'],'input_index':m['input_index'],'after_action':m['state_action_index']}
     _,complete,reason,capture=checks.state_evidence(o,spec)
     states.append({'platform':platform,'case':case,'checkpoint':checkpoint,'complete':complete,'reason':reason,'frameCount':len(capture.get('snapshot_indices',[]))if capture else 0,'observationSHA256':sha(obs)if obs.exists()else None})
    i=m.get('trigger_action_index')
    if m['trigger_type']!='activate':continue
    step=o.get('steps',[])[i]if type(i)is int and 0<=i<len(o.get('steps',[]))else {}
    selector=step.get('selector')or step.get('action',{}).get('target')or {}
    immediate=step.get('immediate_after',step.get('after',step.get('snapshot')));after=step.get('after',step.get('snapshot'))
    events=[v.get('event')if isinstance(v,dict)else v for v in step.get('callback_delta',[])]
    gate=checks.callback_verdict(step,events,platform)
    actions.append({'platform':platform,'case':case,'checkpoint':checkpoint,'actionIndex':i,'selector':selector,'nativeStimulusEstablished':gate['stimulus_established'],'gateReason':gate['reason'],'outcome':step.get('outcome'),'immediate':visible(o,step,immediate,selector,platform),'after':visible(o,step,after,selector,platform),'observationSHA256':sha(obs)if obs.exists()else None})
 return {'actions':actions,'fullStates':states,'snapshots':images,'nativeTests':tests,'totals':{'requiredActivations':len(actions),'establishedActivations':sum(x['nativeStimulusEstablished']for x in actions),'afterSemanticFullyVisible':sum(x['after'].get('semantic',{}).get('fullyVisible')is True for x in actions),'requiredFullStates':len(states),'completeFullStates':sum(x['complete']for x in states)},'scope':'Original target geometry and interval coverage only; visibility is not successful activation or business correctness. Unsupported/blocked stimuli remain explicit. No typography, padding or physical hit-region inference.'}
def compute():
 out={}
 for family,sid,phase in [('own-d0','submission-e572b1','d0'),('own-d0','submission-3d6389','d0'),('own-final','submission-e572b1','final'),('own-final','submission-3d6389','final'),('audit-v4-d0','submission-e572b1','d0'),('audit-v4-final','submission-e572b1','final'),('audit-v3-d0','submission-3d6389','d0')]:
  out[family+'/'+sid]=summarize(R/'evidence'/family/sid,R/'private/inputs'/('d0-v2'if phase=='d0'else'final'))
 return {'version':1,'corpora':out}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();out=R/'observation-summary.json';d=compute()
 if a.write:assert not out.exists();out.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
 else:assert read(out)==d
 print('PASS: original native visibility, stimulus and full-state facts reproduce')
if __name__=='__main__':main()
