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
 # Independent standard-control mapping/diagnostic proof, including honest non-reproduction.
 probe=R/'switch-probe';mapping=read(probe/'report.json');assert mapping['status']=='passed'and mapping['native_test_count_total']==4
 for run in mapping['runs']:
  d=probe/run['evidence'];assert read(d/'manifest.json')['native_test_count']==1
  for path,digest in read(d/'sealed-files.json').items():assert sha(d/path)==digest
 for step in mapping['native_switch_activation_steps']:
  assert step['activation_target']['role_raw']==40 and step['activation_target']['enabled']and step['activation_target']['hittable']
  assert step['activation_target']['path']['strategy']=='native_switch_leaf'and step['same_process']and step['callback_delta']
 boundary=read(probe/'expected-bottom-unobserved/observation.json');assert boundary['status']=='failed'and not boundary['snapshots'][-1]['callbacks']
 # Preserve PNG-space measurements separately from native DP; exact native-control crop comparison.
 animated=R/'android-animation'
 for path,digest in read(animated/'audit.json')['files'].items():assert sha(animated/path)==digest
 from PIL import Image,ImageChops
 def control(directory,checkpoint,identifier):
  d=animated/directory;o=read(d/'observation.json');snap=next(x for x in o['snapshots']if x['name']==checkpoint);node=next(n for n in snap['nodes']if n['identifier']==identifier)
  im=Image.open(d/snap['screenshot']).convert('RGB');sx=im.width/390;sy=im.height/600
  box=tuple(round(value*(sx if i%2==0 else sy))for i,value in enumerate(node['unclipped_bounds_dp']))
  return im.crop(box)
 for identifier,checkpoint in [('probe.radio','after_radio'),('probe.check','after_check')]:
  initial=control('animation-static','initial',identifier)
  assert ImageChops.difference(control('animation-live',checkpoint,identifier),initial).getbbox()is not None
  assert ImageChops.difference(control('animation-live-settled',checkpoint,identifier),initial).getbbox()is None
 imported=R/'passed-production-import';assert read(imported/'manifest.json')['native_test_count']==1 and read(imported/'manifest.json')['status']=='passed'
 for path,digest in read(imported/'archived-files.json')['files'].items():assert sha(imported/path)==digest
 print(json.dumps({'status':'passed_archived_capabilities','ios_final_native_tests':2,'ios_final_snapshots':sum(len(read(R/n/'observation.json')['snapshots'])for n in ['passed-390-dark','passed-320-light-accessibility3-rtl']),'android_continuous_native_test':1,'retained_failed_probe':True,'native_switch_probe_tests':4,'native_package_import_test':1,'animated_control_static_comparison':True,'does_not_replay':'Native SDKs, image judgments or generic SwiftUI styles'}))
if __name__=='__main__':main()
