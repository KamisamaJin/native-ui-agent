#!/usr/bin/env python3
"""Check native state captures independently and replay intentional omissions.

Replay results are derived-data negative controls, not additional native runs.
No screenshot, AX fact, callback or original observation is changed.
"""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('evidence');p.add_argument('--output',required=True);a=p.parse_args()
root=Path(a.evidence);path=root/'observation.json';o=json.loads(path.read_text());by_index={s['index']:s for s in o['snapshots']}
def interval(s):
    t=next((n for n in s['nodes'] if n['identifier']=='cap.title'),None)
    if t is None: return None
    v=s['viewport'];return (v['y']-t['frame']['y'],v['y']+v['height']-t['frame']['y'])
def check(indices):
    shots=[by_index[i] for i in indices if i in by_index]
    vals=sorted(((*interval(s),s['index']) for s in shots if interval(s) is not None))
    top=any(any(n['identifier']=='cap.title' and n['fully_within_viewport'] for n in s['nodes']) for s in shots)
    bottom=any(s.get('bottom_sentinel_visible') for s in shots)
    gaps=[]
    if vals:
        reach=vals[0][1]
        for start,end,index in vals[1:]:
            if start>reach+.5:gaps.append({'from':reach,'to':start,'next_snapshot':index})
            reach=max(reach,end)
    return {'top_seen':top,'bottom_seen':bottom,'gaps':gaps,'complete':bool(vals) and top and bottom and not gaps,'intervals':[{'start':x,'end':y,'snapshot_index':i} for x,y,i in vals]}
checks=[];controls=[]
for c in o.get('state_captures',[]):
    ids=c.get('snapshot_indices',[]);result=check(ids)
    checks.append({'state_id':c.get('state_id'),'raw_binding':c.get('binding',c.get('state_binding')),'raw_complete':c.get('complete'),'independent':result})
    if not result['complete'] or len(ids)<2:continue
    # Keep one top snapshot only: prior complete captures must not fill this new-state replay.
    first=min(ids,key=lambda i:interval(by_index[i])[0])
    early=check([first]);controls.append({'control':'new state ends early','kind':'native-evidence omission replay; not a native run','state_id':c.get('state_id'),'kept_snapshot_indices':[first],'independent':early,'expected_complete':False,'control_passed':early['complete'] is False})
    # Keep just endpoint screenshots, which leave long content between them unobserved.
    last=max(ids,key=lambda i:interval(by_index[i])[1])
    endpoints=check([first,last])
    if endpoints['gaps']:
        controls.append({'control':'middle interval omitted','kind':'native-evidence omission replay; not a native run','state_id':c.get('state_id'),'kept_snapshot_indices':[first,last],'independent':endpoints,'expected_complete':False,'control_passed':endpoints['complete'] is False and bool(endpoints['gaps'])})
report={'observation_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'native_state_captures':checks,'omission_replay_negative_controls':controls,'status':'passed' if checks and all(c['independent']['complete']==c['raw_complete'] for c in checks) and all(c['control_passed'] for c in controls) else 'failed_or_not_representable'}
Path(a.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'native_state_capture_count':len(checks),'negative_control_count':len(controls)}))
