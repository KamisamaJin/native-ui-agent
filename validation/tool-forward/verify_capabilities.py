#!/usr/bin/env python3
"""Portable independent capability audit; original native SDKs are not replayed."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent.parent/'tool-capabilities'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for relative,digest in read(R/'DELIVERABLE-SHA256.json').items():assert sha(R/relative)==digest,relative
 outcome=read(R/'CAPABILITY-OUTCOMES.json');assert outcome['frozen_expectations_intact']
 tests=shots=0
 for d in sorted((R/'evidence').iterdir()):
  if not d.is_dir():continue
  m=read(d/'manifest.json');o=read(d/'observation.json');assert m['native_test_count']==1
  tests+=m['native_test_count'];shots+=len(o['snapshots'])
  for s in o['snapshots']:assert(d/s['screenshot']).is_file()
 for entry in read(R/'SOURCE-INTEGRITY.json')['compiled_native_source_copies']:
  assert entry['intact']and sha(R/entry['portable_source'])==entry['sha256']
 assert tests==outcome['native_test_count']==6 and shots==outcome['native_screenshot_count']==232
 positive=read(R/'evidence/candidate-semantic-positive/typed-checkpoint-assertions.json');assert positive['counts']=={'passed':13,'failed':1,'unassessed':0}
 negative=read(R/'evidence/candidate-semantic-negative/observation.json');assert all(s['outcome']=='unavailable'and not s['callback_delta']for s in negative['steps'])
 long=read(R/'evidence/candidate-long/observation.json');assert len(long['state_captures'])==5 and all(c['complete']and c['max_gap']==0 for c in long['state_captures'])
 assert read(R/'evidence/candidate-long/typed-assertions.json')['counts']=={'passed':11,'failed':0,'unassessed':0}
 omission=read(R/'evidence/candidate-long/checker-omission-replays.json');assert omission['status']=='passed'and len(omission['controls'])==10 and all(c['passed']for c in omission['controls'])
 partial=read(R/'evidence/candidate-long-partial/observation.json');assert partial['coverage']['bottom_reached']and not partial['coverage']['missing_identifiers']
 assert [(c['state_id'],c['complete'])for c in partial['state_captures']]==[('initial-full',True),('updated-partial',False)]
 assert read(R/'evidence/candidate-long-partial/capability-result.json')['status']=='passed'
 print(json.dumps({'status':'passed_archived_independent_capabilities','native_tests':tests,'native_snapshots':shots,'derived_omission_controls':10,'scope':'Integrity/native facts only; no SDK replay or business-quality claim.'}))
if __name__=='__main__':main()
