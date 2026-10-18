#!/usr/bin/env python3
"""Portable artifact/protocol audit, not a replay of SDKs or model judgments."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=read(R/'preflight-report.json');assert report['native_test_count_final_passed']==2
 for name in ['passed-390-dark','passed-320-light-accessibility3-rtl','failed-initial-offscreen-tap']:
  d=R/name
  for path,digest in read(d/'sealed-files.json').items():assert sha(d/path)==digest,(name,path)
  m=read(d/'manifest.json');o=read(d/'observation.json')
  assert m['native_test_count']==1
  for s in o['snapshots']:assert (d/s['screenshot']).is_file()
  if name.startswith('passed-'):
   assert m['status']=='passed' and o['status']=='passed'
   assert o['coverage']['bottom_reached'] and not o['coverage']['missing_identifiers']
   assert all(x.get('same_process')for x in o['steps'])
   assert len({(s['runtime']['pid'],s['runtime']['instance'])for s in o['snapshots']})==1
   assert o['snapshots'][0]['runtime']['fixture_index']==0 and o['snapshots'][-1]['runtime']['fixture_index']==1
   assert all(s['viewport']['height']==600 for s in o['snapshots'])
   disabled=[x for x in o['steps']if x['outcome']=='blocked_disabled'];assert disabled and all(not x['callback_delta']and x['target']['enabled']is False for x in disabled)
   callbacks=[x['event']for x in o['snapshots'][-1]['callbacks']];assert callbacks==['probe.primary','probe.last','probe.primary']
  else:assert m['status']!='passed'
 for name in ['android','android-final']:
  d=R/name;a=read(d/'audit.json')
  for path,digest in a['artifact_sha256'].items():assert sha(d/path)==digest,(name,path)
 a=read(R/'android-final/observation.json');assert a['phase']=='complete'and a['coverage']['bottom_reached']and a['events']==['confirm:probe','retry']
 assert a['steps'][1]['model_update']and all(s['execution']=='observed'for s in a['steps'])
 print(json.dumps({'status':'passed_archived_capabilities','ios_final_native_tests':2,'ios_final_snapshots':sum(len(read(R/n/'observation.json')['snapshots'])for n in ['passed-390-dark','passed-320-light-accessibility3-rtl']),'android_continuous_native_test':1,'retained_failed_probe':True,'does_not_replay':'Native SDKs, image judgments or generic SwiftUI styles'}))
if __name__=='__main__':main()
