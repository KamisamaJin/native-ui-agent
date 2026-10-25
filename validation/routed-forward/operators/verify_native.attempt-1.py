#!/usr/bin/env python3
"""Portable actual SDK receipt and registered actuals reconstruction. No SDK."""
import json
from pathlib import Path
import study as s
import evidence_review as review,design_contract as d,native_checks,review_contract
R=s.R

def main():
 scopes=[(R/'benchmark-design/lock.json',R/'benchmark-design/policy.json',R/'benchmark-design/FoldGuideBridge.swift')]
 for phase in ['public','private']:scopes.append((R/'design'/phase/'design-lock.json',R/'design'/phase/'policy.json',R/'design'/phase/'Bridge.swift'))
 by_lock={d.digest(s.read(lock)):(lock,policy,bridge)for lock,policy,bridge in scopes};packets={};count=0
 for folder in ['evidence/benchmark','corpora','feedback']:
  for path in sorted((R/folder).rglob('result.json')):
   base=path.parent
   if not(base/'source-before.json').is_file():continue
   receipt=s.read(path);execution=s.read(base/'execution.json');plan=s.read(base/'parent-plan.json');before=s.read(base/'source-before.json')
   assert receipt['source_sha256']==d.digest(before)and receipt['source_unchanged']==(before==s.read(base/'source-after.json'))
   assert receipt['parent_plan_sha256']==d.digest(plan)and receipt['execution_sha256']==execution['execution_sha256']
   for name,h in receipt['input_hashes'].items():assert s.sha(base/name)==h
   op=base/'native/observation.json'
   if receipt.get('observation_sha256'):assert s.sha(op)==receipt['observation_sha256']
   if receipt.get('image_hashes'):s.xp.verify_capture_images(receipt,op.parent)
   if receipt.get('automatic_sha256'):assert s.sha(base/'automatic.json')==receipt['automatic_sha256']
   if receipt.get('status')=='verified_capture':assert receipt['native_exit_code']==0 and receipt['coverage_satisfied']and receipt['inputs_unchanged']and receipt['source_unchanged']
   lock_sha=execution['design_lock_sha256'];lock,policy,bridge=by_lock[lock_sha]
   if execution['platform']=='android':bridge=bridge.parent/'ObserverBridge.kt'
   config={'plan':str(base/'parent-plan.json'),'design_lock':str(lock),'design_sha256':lock_sha,'policy':str(policy),'policy_sha256':d.digest(s.read(policy)),
           'fixtures':str(base/'fixtures.json'),'bridge':str(bridge),'source_roots':receipt['source_roots']}
   # Retain the original namespace for read-only packet reconstruction. No
   # current-workspace fingerprint or relocated source acceptance is invented.
   review.original(config,path,s.sha(path));packets[s.sha(path)]=(path,config);count+=1
 reviews=0
 for store in [R/'evidence/benchmark-review-store',R/'evidence/review-stores']:
  if not store.exists():continue
  for directory in sorted((store/'index').rglob('*')):
   if not directory.is_dir():continue
  for receipt in sorted(store.rglob('review-result.json')):
   envelope=s.read(receipt);capture,config=packets[envelope['capture_sha256']]
   # Business stores have unit/case/platform roots; find the nearest ancestor
   # containing index/<original capture SHA>. The registry is relative-path based.
   candidates=[p for p in receipt.parents if p.is_relative_to(store)and(p/'index'/envelope['capture_sha256']).is_dir()]
   assert candidates,'Missing original append-only registry'
   config=dict(config,review_store=str(candidates[0]));review.reconstruct(config,capture,s.sha(capture),{'path':str(receipt),'sha256':s.sha(receipt)});reviews+=1
 print(json.dumps({'status':'PASS','native_receipts':count,'registered_original_reviews':reviews,'scope':'Exact original namespace/source/input/epoch/image/actual reconstruction; no native rerender or edited-source acceptance.'}))
if __name__=='__main__':main()
