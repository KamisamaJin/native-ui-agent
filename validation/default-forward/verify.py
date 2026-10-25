#!/usr/bin/env python3
"""Portable replay of frozen identities, native receipts and default-chain adoption."""
import json,sys
from pathlib import Path
import study as s
import execution_plan as xp,design_contract as d
R=s.R

def namespace(files):
 return {str(i)+'/'+key[len(prefix)+1:]:value for i,prefix in enumerate(s.ROOTS)for key,value in files.items()if key.startswith(prefix+'/')}

def main():
 s.tool_verify()
 live=s.REPO/'native-ui-agent';candidate=R/'candidate-v10'
 assert s.table(live)==s.table(candidate),'Live skill differs from frozen treatment'
 capsules={}
 for seal in (R/'submissions').rglob('seal.json'):
  files=s.read(seal)['files'];source=seal.parent/'source'
  actual={str(p.relative_to(source)):s.sha(p)for p in source.rglob('*')if p.is_file()}
  assert actual==files,str(seal);capsules[d.digest(namespace(files))]=files
 assert capsules,'No sealed production capsule'
 for stage in sorted((R/'gates').glob('*.json')):
  # cohort_gate maintains its own immutable exact file-member rules.
  if stage.stem!='index':
   value=s.read(stage)
   if value.get('stage'):s.gate.authorize(R/'gates',value['stage'],R)
 counts={'captures':0,'verified':0,'incomplete':0,'default_cycles':0,'intakes':0,'blocked_cycles':0}
 for result in sorted(R.rglob('result.json')):
  if any(v in result.parts for v in ['cache','probe-design','probe-review','baseline-v9','candidate-v10']):continue
  base=result.parent
  if not(base/'source-before.json').is_file():continue
  receipt=s.read(result);before=s.read(base/'source-before.json');after=s.read(base/'source-after.json')
  assert d.digest(before) in capsules,str(base)
  assert receipt['source_sha256']==d.digest(before)
  assert receipt['source_unchanged']==(before==after)
  execution=s.read(base/'execution.json');plan=s.read(base/'parent-plan.json')
  assert receipt['parent_plan_sha256']==d.digest(plan)and receipt['execution_sha256']==execution['execution_sha256']
  for name,h in receipt['input_hashes'].items():assert s.sha(base/name)==h
  if receipt.get('observation_sha256'):assert s.sha(base/'native/observation.json')==receipt['observation_sha256']
  if receipt.get('automatic_sha256'):assert s.sha(base/'automatic.json')==receipt['automatic_sha256']
  if receipt.get('image_hashes'):xp.verify_capture_images(receipt,base/'native')
  if receipt.get('status')=='verified_capture':
   assert receipt['native_exit_code']==0 and receipt['source_unchanged']and receipt['inputs_unchanged']and receipt['coverage_satisfied']
   counts['verified']+=1
  else:counts['incomplete']+=1
  counts['captures']+=1
 for cycle in sorted(R.rglob('cycle.json')):
  if any(v in cycle.parts for v in ['cache','probe-design','probe-review','baseline-v9','candidate-v10']):continue
  value=s.read(cycle);trace=value['trace'];counts['default_cycles']+=1
  for name in ['route_findings','locator_diagnostics','retest_plan.unresolved']:assert name in trace,str(cycle)
  for name in ['coverage.json','before-routes.json','before-diagnostics.json','retest-plan.json']:assert(cycle.parent/name).is_file()
  if value.get('intake'):assert not value['native_executed'];counts['intakes']+=1
  elif value['native_executed']:
   for name in ['execution_plan.run_execution','route_findings_after','locator_diagnostics_after','admission']:assert name in trace
   if value['final']:assert s.read(cycle.parent/'capture/execution.json')['scope']=='full'
  else:counts['blocked_cycles']+=1;assert value['status']=='blocked_repeated_unchanged_evidence'
 assert counts['captures'] and counts['intakes'] and counts['default_cycles']
 print(json.dumps({'status':'PASS',**counts,'scope':'Identity/chronology/evidence/mandatory invocation replay, no SDK rerun or invented product pass.'}))
if __name__=='__main__':main()
