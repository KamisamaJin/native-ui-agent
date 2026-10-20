"""Preserve v1 and revise only the incorrectly conflated measurement scope.

This is pre-business calibration, not a blind product repair or a new native
acquisition. Actual sources, values, raw images and v1 assertions stay intact.
"""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parent;REPO=R.parents[2]
sys.path.insert(0,str(REPO/'native-ui-agent/scripts'))
import design_contract as d
out=R.parent/'generic-scoped';out.mkdir()
for name in ['reference.json','bindings.json','actions-base.json','fixtures.json']:(out/name).write_bytes((R/name).read_bytes())
contract=d.load(R/'contract.json')
contract['approval_reference']='Pre-business measurement calibration; see generic-scoped/AMENDMENT.json'
for rule in contract['rules']:
 if rule['kind']=='geometry':rule['measurement']={'ios':'layout_box','android':'accessibility_box'}
def save(name,v):(out/name).write_text(json.dumps(v,indent=2)+'\n')
save('contract.json',contract)
lock=d.seal(out/'contract.json',out);save('design-lock.json',lock)
save('AMENDMENT.json',{'kind':'pre-business generic measurement scope correction','reason':'The neutral SwiftUI marker frame allocation72pt is not its AX text frame11.33pt. Comparing these as the same geometry produced eight false failures. Preserve all original data; no expected numeric value or source byte changed. Android checks explicitly address the native semantic marker bounds, not a generic effective layout API.','canonicalSHA256':d.digest(lock),'nativeReacquisition':False,'oldInputsUnchanged':True,'blindTrialBenefit':False})
for platform in ['ios','android']:
 plan,actions=d.compile_contract(lock,d.digest(lock),'neutral',platform,d.load(out/'bindings.json'),d.load(out/'actions-base.json'))
 assert actions==d.load(R/('actions.'+platform+'.json'))
 save('plan.'+platform+'.json',plan);save('actions.'+platform+'.json',actions)
print(d.digest(lock))
