#!/usr/bin/env python3
"""Omission controls over actual native records; explicitly not new native runs."""
import argparse,copy,hashlib,importlib.util,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('evidence');p.add_argument('--checker',required=True);p.add_argument('--output',required=True);a=p.parse_args()
path=Path(a.evidence)/'observation.json';o=json.loads(path.read_text());checker=Path(a.checker)
spec=importlib.util.spec_from_file_location('candidate_native_checks',checker);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
controls=[]
for c in o.get('state_captures',[]):
    ids=c.get('snapshot_indices',[])
    if not c.get('complete') or len(ids)<3:continue
    state={'id':c['state_id'],'input_index':c['binding']['fixture_index']}
    original=module.state_evidence(o,state)
    for name,kept in [('new-state early stop',[ids[0]]),('missing middle',[ids[0],ids[-1]])]:
        replay=copy.deepcopy(o);current=next(x for x in replay['state_captures'] if x['state_id']==c['state_id']);current['snapshot_indices']=kept
        # The producer claim remains complete:true. Native snapshot geometry must override it.
        result=module.state_evidence(replay,state)
        if name=='missing middle':
            first=o['snapshots'][kept[0]];last=o['snapshots'][kept[-1]]
            f=first['runtime']['content_frame'];l=last['runtime']['content_frame']
            gap=(last['viewport']['y']-l['y'])-(first['viewport']['y']-f['y']+first['viewport']['height'])
            if gap<=1:continue
        controls.append({'control':name,'kind':'derived omission replay over original native snapshots; not a native run','state_id':c['state_id'],'original_complete':original[1],'original_snapshot_indices':ids,'replay_snapshot_indices':kept,'producer_complete_claim':current['complete'],'checker_recomputed_complete':result[1],'reason':result[2],'passed':original[1] is True and result[1] is False})
report={'original_observation_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256(checker.read_bytes()).hexdigest(),'controls':controls,'status':'passed' if controls and all(c['passed'] for c in controls) else 'failed_or_not_representable'}
Path(a.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'control_count':len(controls)}))
