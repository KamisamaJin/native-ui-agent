#!/usr/bin/env python3
"""Independent checks that snapshots remain attached to actual caller/state input."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('evidence');p.add_argument('--output',required=True);a=p.parse_args();root=Path(a.evidence)
o=json.loads((root/'observation.json').read_text());original=o.get('original_runtime',{});checks=[];inputs={}
for s in o['snapshots']:
    rt=s['runtime'];binding=s.get('state_binding',s.get('binding',{}));idx=rt.get('fixture_index')
    labels=[n['label'] for n in s['nodes'] if n['identifier']=='cap.title'];expected='Capability '+('initial' if idx==0 else 'updated')
    known=idx in (0,1);same=rt.get('pid')==original.get('pid') and rt.get('instance')==original.get('instance')
    binding_index=binding.get('fixture_index');digest=binding.get('input_sha256');event_revision=binding.get('event_revision')
    if digest:inputs.setdefault(idx,set()).add(digest)
    checks.append({'snapshot_index':s['index'],'fixture_index':idx,'title_labels':labels,'expected_title':expected,'same_native_process_and_instance':same,'state_binding':binding,'binding_matches_runtime_index':binding_index==idx if binding else None,'event_revision_matches_receipt_count':event_revision==len(s.get('callbacks',[])) if event_revision is not None else None,'label_matches_input':known and labels==[expected]})
report={'checks':checks,'fixture_input_hashes':{str(k):sorted(v) for k,v in inputs.items()},'status':'passed' if checks and all(c['same_native_process_and_instance'] and c['label_matches_input'] and c['binding_matches_runtime_index'] is not False and c['event_revision_matches_receipt_count'] is not False for c in checks) and (not inputs or len(inputs)==2 and len(inputs[0])==1 and len(inputs[1])==1 and inputs[0].isdisjoint(inputs[1])) else 'failed'}
Path(a.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'snapshots':len(checks),'fixture_input_hashes':report['fixture_input_hashes']}))
