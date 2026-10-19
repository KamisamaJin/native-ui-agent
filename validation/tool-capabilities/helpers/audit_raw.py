#!/usr/bin/env python3
"""Independent raw-fact extraction; never converts source inspection into a native pass."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('evidence');p.add_argument('--output');a=p.parse_args()
root=Path(a.evidence);m=json.loads((root/'manifest.json').read_text());o=json.loads((root/'observation.json').read_text())
summary={'observer_status':m.get('status'),'native_test_count':m.get('native_test_count'),'native_test_exit_code':m.get('test_exit_code'),'issues':o.get('issues'),'coverage':o.get('coverage'),'steps':[],'state_coverage':[]}
for n,s in enumerate(o['steps']):
    summary['steps'].append({'index':n,'action':s['action'],'outcome':s['outcome'],'semantic_target':s.get('semantic_target',s.get('target')),'activation_target':s.get('activation_target'),'callback_delta':s.get('callback_delta'),'same_process':s.get('same_process'),'assertions':s.get('assertions',s.get('assertion_results'))})
states={}
for s in o['snapshots']:
    nodes=s['nodes']; title=next((n for n in nodes if n['identifier']=='cap.title'),None)
    if not title: continue
    expanded=any(n['identifier']=='cap.expanded.marker' for n in nodes)
    key=(s['runtime']['fixture_index'],expanded)
    state=states.setdefault(key,{'fixture_index':key[0],'expanded':expanded,'snapshot_indices':[],'intervals':[],'top_seen':False,'bottom_seen':False,'title_labels':set(),'native_tall_heights':set()})
    state['title_labels'].add(title['label']);state['snapshot_indices'].append(s['index'])
    state['top_seen']|=bool(title.get('fully_within_viewport'))
    state['bottom_seen']|=bool(s.get('bottom_sentinel_visible'))
    vy=s['viewport']['y'];vh=s['viewport']['height'];ty=title['frame']['y']
    state['intervals'].append({'snapshot':s['index'],'start':vy-ty,'end':vy+vh-ty})
    state['native_tall_heights'].update(n['frame']['height'] for n in nodes if n['identifier']=='cap.tall')
for state in states.values():
    intervals=sorted(state['intervals'],key=lambda x:x['start']);gaps=[];reach=intervals[0]['end']
    for i in intervals[1:]:
        if i['start']>reach+.5: gaps.append({'start':reach,'end':i['start'],'next_snapshot':i['snapshot']})
        reach=max(reach,i['end'])
    state['gaps']=gaps;state['raw_coverage_complete']=state['top_seen'] and state['bottom_seen'] and not gaps
    state['title_labels']=sorted(state['title_labels']);state['native_tall_heights']=sorted(state['native_tall_heights']);summary['state_coverage'].append(state)
text=json.dumps(summary,indent=2)
if a.output: Path(a.output).write_text(text+'\n')
else: print(text)
