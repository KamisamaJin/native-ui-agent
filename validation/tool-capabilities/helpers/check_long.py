#!/usr/bin/env python3
"""Frozen L1-L7 checks from actual exported native observation facts only."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('evidence');p.add_argument('--output',required=True);a=p.parse_args();root=Path(a.evidence)
o=json.loads((root/'observation.json').read_text());m=json.loads((root/'manifest.json').read_text());coverage=json.loads((root/'independent-state-coverage.json').read_text());checks=[]
def record(id,passed,evidence):checks.append({'id':id,'status':'passed' if passed else 'failed','evidence':evidence})
heights=[n['frame']['height']for s in o['snapshots'] for n in s['nodes']if n['identifier']=='cap.tall'];viewports=sorted(set(s['viewport']['height']for s in o['snapshots']))
record('L1',bool(heights)and all(abs(h-940)<.5 for h in heights)and viewports==[600],{'native_tall_heights':sorted(set(heights)),'native_viewport_heights':viewports})
for id,index,event,require_full in [('L2',0,'cap.distant',True),('L3.initial',1,'cap.top',True),('L3.updated',5,'cap.top',True),('L4',6,'cap.label.distant',False)]:
 s=o['steps'][index];actual=s.get('activation_target',{});events=[x['event']for x in s['callback_delta']]
 ok=s['outcome']=='tapped'and actual.get('role_raw')==9 and actual.get('enabled')is True and events==[event]and(not require_full or actual.get('fully_within_viewport')is True)
 if id=='L4':ok=ok and s['semantic_target'].get('identifier')==''and s['semantic_target'].get('label')=='Label only distant action'
 record(id,ok,{'step_index':index,'outcome':s['outcome'],'actual_native_activation_target':actual,'semantic_target':s['semantic_target'],'real_callback_delta':s['callback_delta']})
for id,state,idx in [('L5','initial',0),('L6','updated',1),('L7','expanded',1)]:
 captures=[c for c in o['state_captures']if c['state_id']==state];ind=[c for c in coverage['native_state_captures']if c['state_id']==state]
 ok=len(captures)==len(ind)==1 and captures[0]['binding']['fixture_index']==idx and captures[0]['complete']is True and ind[0]['independent']['complete']is True
 if state=='expanded'and captures:
  shots=[o['snapshots'][i]for i in captures[0]['snapshot_indices']];visible={n['identifier']for s in shots for n in s['nodes']if n.get('intersects_viewport')}
  rows=['cap.expanded.marker']+['cap.expanded.'+str(i)for i in range(8)];events=[x['event']for x in o['steps'][4]['callback_delta']]
  ok=ok and all(r in visible for r in rows)and events==['cap.expand']
  extra={'expanded_native_visible_identifiers':sorted(visible),'real_expand_callback_delta':o['steps'][4]['callback_delta']}
 else:extra={}
 record(id,ok,{'native_state_capture':captures,'independent_state_interval_check':ind,**extra})
report={'status':'passed'if m['native_test_count']>0 and all(c['status']=='passed'for c in checks)else'failed','native_test_count':m['native_test_count'],'collector_status':m['status'],'checks':checks}
Path(a.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checks':{c['id']:c['status']for c in checks}}))
