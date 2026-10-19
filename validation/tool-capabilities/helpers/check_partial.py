#!/usr/bin/env python3
"""Frozen L8: completed prior state cannot make a new partial input state complete."""
import argparse,importlib.util,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('evidence');p.add_argument('--checker',required=True);p.add_argument('--output',required=True);a=p.parse_args();root=Path(a.evidence)
o=json.loads((root/'observation.json').read_text());m=json.loads((root/'manifest.json').read_text());ind=json.loads((root/'independent-state-coverage.json').read_text())
spec=importlib.util.spec_from_file_location('frozen_checker',a.checker);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
states=[]
for id,index,expected in [('initial-full',0,True),('updated-partial',1,False)]:
 captures=[c for c in o['state_captures']if c['state_id']==id];checks=[c for c in ind['native_state_captures']if c['state_id']==id];evaluated=module.state_evidence(o,{'id':id,'input_index':index})
 passed=len(captures)==1 and len(checks)==1 and captures[0]['binding']['fixture_index']==index and captures[0]['complete']is expected and checks[0]['independent']['complete']is expected and evaluated[1]is expected
 states.append({'state_id':id,'expected_complete':expected,'native_capture':captures,'independent_geometry':checks,'checker_complete':evaluated[1],'checker_reason':evaluated[2],'status':'passed'if passed else'failed'})
no_inherited_full=not any(c['binding']['fixture_index']==1 and c['complete']for c in o['state_captures'])
global_complete=o['coverage']['bottom_reached']is True and o['coverage']['missing_identifiers']==[]
expected_issues=['state updated-partial incomplete overlapping full-content coverage']
report={'assertion_id':'L8','status':'passed'if m['native_test_count']>0 and m['status']=='failed'and o['issues']==expected_issues and all(s['status']=='passed'for s in states)and no_inherited_full and global_complete else'failed','native_test_count':m['native_test_count'],'expected_collector_status':'failed','actual_collector_status':m['status'],'native_issues':o['issues'],'global_session_identifier_coverage_complete':global_complete,'updated_input_has_no_inherited_or_automatic_complete_capture':no_inherited_full,'states':states,'scope':'Actual native partial-state run. state_capture:false; explicit initial full sweep, caller update and max_steps1 partial sweep. No automatic updated/final full-content claim.'}
Path(a.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'states':[{k:s[k]for k in ['state_id','expected_complete','checker_complete','status']}for s in states],'global_session_identifier_coverage_complete':global_complete}))
