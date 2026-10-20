#!/usr/bin/env python3
import sys,json,copy,datetime
from pathlib import Path
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill');O=R/'validation/multitask-forward/independent-generic';sys.path.insert(0,str(R/'validation/multitask-forward/development/v7-neutral-candidate/scripts'));sys.dont_write_bytecode=True;import design_contract as dc;sys.dont_write_bytecode=True;import native_checks as nc
lock=dc.load(O/'approved-lock-rev3.json');digest=json.loads((O/'APPROVAL-rev3.json').read_text())['design_lock_sha256'];plan=dc.load(O/'plans/normal/android/plan.json');rows=[]
for mutation in ['expected','tolerance','drop-assertion','drop-state','source']:
 p=copy.deepcopy(plan)
 if mutation=='expected':p['assertions'][0]['expected']='Unapproved title'
 elif mutation=='tolerance':next(a for a in p['assertions'] if 'tolerance' in a)['tolerance']=100
 elif mutation=='drop-assertion':p['assertions'].pop()
 elif mutation=='drop-state':p['states'].pop()
 else:p['assertions'][0]['source']='unapproved-source'
 try:dc.verify_generated(p,lock,digest,'android');rows.append({'mutation':mutation,'rejected':False})
 except Exception as e:rows.append({'mutation':mutation,'rejected':True,'reason':str(e)})
before={'pid':123,'instance':'pure-control','fixture_index':0,'input_sha256':'input','event_revision':2};after=dict(before,event_revision=3)
base={'outcome':'tapped','binding_after':after,'callback_delta':['selected'],'dispatch':{'attempted':True,'succeeded':True,'method':'xcui_tap','stimulus':'activation','binding_before':before,'event_start':2,'event_end':3,'matches':1,'native_controls':1,'enabled':True}}
callbacks=[]
for label in ['valid','disabled','wrong-input','wrong-method','wrong-event']:
 s=copy.deepcopy(base)
 if label=='disabled':s['outcome']='blocked_disabled';s['dispatch']['attempted']=False
 elif label=='wrong-input':s['binding_after']['input_sha256']='another-input'
 elif label=='wrong-method':s['dispatch']['method']='os_touch'
 elif label=='wrong-event':s['callback_delta']=['wrong']
 callbacks.append({'case':label,'input':s,'result':nc.callback_verdict(s,['selected'],'ios')})
assert all(r['rejected'] for r in rows)
assert [r['result']['status'] for r in callbacks]==['passed','unassessed','unassessed','unassessed','failed']
(O/'controls.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Pure evaluator and plan mutations only; no production source modified.','plan_corruptions':rows,'callback_controls':callbacks},indent=2)+'\n')
print('5 plan corruptions rejected; callback positive, negative and unavailable controls matched.')
