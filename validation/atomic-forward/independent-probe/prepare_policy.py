import json,hashlib,time
from pathlib import Path
R=Path(__file__).resolve().parent
canon=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
lock=canon(json.loads((R/'design/lock.json').read_text()))
def sample(region,visibility):return {'region':region,'minimum_pixels':12,'minimum_support':0.9,'channel_tolerance':0,'basis':'semantic','visibility':visibility}
policy={'version':1,'design_lock_sha256':lock,'approval_reference':'design/APPROVAL.md; independently selected before implementation','ownership':{x:'component'for x in ['band','canvas','title','body']},'atoms':[{'rule_id':'band-fill','aspect':'rendered_fill','method':'native_pixels','sampling':sample([0.15,0.2,0.85,0.8],'fully_visible')},{'rule_id':'canvas-fill','aspect':'rendered_canvas','method':'native_pixels','sampling':sample([0.01,0.08,0.04,0.92],'visible_fragment')},{'rule_id':'text-wrap','aspect':'wrapping','method':'visual','question':{'source':'reference','pointer':'/questions/wrap'}},{'rule_id':'text-overlap','aspect':'overlap','method':'visual','question':{'source':'reference','pointer':'/questions/overlap'}}]}
(R/'design/policy.json').write_text(json.dumps(policy,indent=2)+'\n')
approval={'design_lock_sha256':lock,'policy_sha256':canon(policy),'frozen_before_component_source_epoch':time.time(),'scope':'Independent neutral tool validation; same context designed and implements; no independent second visual judge or product-study score'}
(R/'APPROVAL.json').write_text(json.dumps(approval,indent=2)+'\n')
F=R/'fixtures';F.mkdir(exist_ok=True)
ref=json.loads((R/'design/reference.json').read_text())
initial={k:ref[k]['A']['value']for k in ['title','body']};initial.update(canvas='EBE6F5',band='605082')
updated={k:ref[k]['B']['value']for k in ['title','body']};updated.update(canvas='E7EEE7',band='41614D')
for p in ['ios','android']:
 for scenario in ['normal','narrow-large']:
  narrow=scenario=='narrow-large';config={'width':260 if narrow else 390,'theme':'light','direction':'ltr','initial':initial,'updates':[updated],'required_identifiers':['moment.band','moment.title','moment.body','moment.action','moment.canvas'],'state_capture':True,'max_scrolls':12}
  config.update({'dynamic_type':'accessibility3'if narrow else'large','canvas_color':'#FFFFFF'}if p=='ios'else{'fontScale':1.7 if narrow else 1.0,'viewportHeight':600})
  (F/f'{p}-{scenario}.json').write_text(json.dumps(config,indent=2)+'\n')
# Pure capability preflight has no design assertions and is not a product substitute.
probe={'width':390,'theme':'light','direction':'ltr','dynamic_type':'large','fontScale':1.0,'viewportHeight':600,'initial':{'title':'Capability initial','detail':'Initial detail'},'updates':[{'title':'Capability updated','detail':'Updated detail'}],'max_scrolls':24,'required_identifiers':['probe.title','probe.primary','probe.last','probe.detail']}
(F/'preflight.json').write_text(json.dumps(probe,indent=2)+'\n')
(R/'preflight-actions.json').write_text(json.dumps([{'type':'tap','target':{'identifier':'probe.primary'},'reveal':True,'expect_callback':'probe.primary','state_id':'primary'},{'type':'apply_next_fixture','state_id':'updated'},{'type':'tap','target':{'identifier':'probe.last'},'reveal':True,'expect_callback':'probe.last','state_id':'last'}],indent=2)+'\n')
print(json.dumps(approval))
