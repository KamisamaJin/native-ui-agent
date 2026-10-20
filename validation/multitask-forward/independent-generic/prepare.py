#!/usr/bin/env python3
import sys,json,hashlib,time,datetime,subprocess
from pathlib import Path
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
OUT=ROOT/'validation/multitask-forward/independent-generic'
S=ROOT/'validation/multitask-forward/development/v7-neutral-candidate/scripts'
HOST=ROOT/'validation/multitask-forward/cache/independent-neutral/host'
sys.path.insert(0,str(S))
sys.dont_write_bytecode=True
import cohort_gate as gate
sys.dont_write_bytecode=True;import design_contract as dc

def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(x,indent=2)+'\n' if not isinstance(x,str) else x,encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
write(OUT/'.gitignore','__pycache__/\n')
# A truly independent two-member workflow tests the stage barrier before SDK work.
b=OUT/'barrier';b.mkdir(exist_ok=True);reg=b/'registry';reg.mkdir(exist_ok=True)
write(b/'a.txt','neutral member a\n');write(b/'b.txt','neutral member b\n')
write(reg/'config.json',{'version':1,'artifact_root':str(b),'stages':{'design':{'members':['owner'],'requires':[]},'sources':{'members':['a','b'],'requires':['design']}}})
receipts=[]
for label,fn in [('early-launch',lambda:gate.authorize(reg,'sources')),('partial-members',lambda:gate.seal(reg,'sources',{'a':['a.txt']}))]:
 try: fn();receipts.append({'control':label,'unexpected_accept':True,'at':now()})
 except Exception as e:receipts.append({'control':label,'rejected':True,'reason':str(e),'at':now()})
write(b/'rejected-early-launch.json',receipts)
gate.seal(reg,'design',{'owner':['a.txt']});gate.seal(reg,'sources',{'a':['a.txt'],'b':['b.txt']})
write(b/'authorized.json',gate.authorize(reg,'sources'))
write(OUT/'PREREGISTRATION.md','''# Independent neutral forward pass\n\nFixed before implementation: an expandable reading/status panel, neutral title, a 48 native-unit disclosure growing to 72 when expanded, selectable reading preference, disabled export action, twelve long text sections, and caller replacement resetting expansion and selection.\n\nPublic normal: 360 logical width, light, default text. Public dark-large: 390 logical width, dark, iOS xLarge / Android 1.2. Both use the same action sequence: expand, select, observe disabled action, caller replacement.\n\nAcceptance uses exact labels/selected/enabled flags, native accessibility-bound disclosure height with independently allowed 0.75-unit quantization tolerance, Android title 22sp and theme ink; iOS computed style and framework layout allocation remain unassessed. Manual review inspects legibility, ordering, clipped text, and the changed disclosure. Callbacks require native delivery; observing a blocked disabled control cannot pass a callback assertion.\n\nNo pixel regression reference is asserted; the typed design and this authored layout description are the new design reference. Source/capture identity does not prove design interpretation correct. No actual application navigation/keyboard/lifecycle/OS physical Android touch claim.\n''')
T=lambda v,u:{'value':v,'unit':u}
ref={'labels':{'old':T('Reading room','string'),'new':T('Evening notes','string')},'bool':{'yes':T(True,'bool'),'no':T(False,'bool')},'events':{'expand':T(['expanded'],'events'),'select':T(['selected'],'events'),'quiet':T([],'events')},'title':{'font':T(22,'sp'),'normal':T('#FF233347','argb'),'dark-large':T('#FFE6EAF0','argb')},'geometry':{p:{'collapsed':T(48,u),'expanded':T(72,u),'tolerance':T(.75,u)} for p,u in [('ios','pt'),('android','dp')]},'visual':T('Clear reading hierarchy, unclipped controls, expanded status and readable scrolling sections.','string')}
d=OUT/'design';write(d/'reference.json',ref)
rules=[{'id':'title','kind':'control','target':'title','property':'label'}, {'id':'disclosure-height','kind':'geometry','target':'expand','property':'height','basis':'control','measurement':'accessibility_box','op':'near'}, {'id':'layout-height','kind':'geometry','target':'expand','property':'height','basis':'control','measurement':'layout_box','op':'near'}, {'id':'selection','kind':'control','target':'choice','property':'selected'}, {'id':'disabled','kind':'control','target':'disabled','property':'enabled'}, {'id':'title-font','kind':'text_layout','target':'title','property':'font_sp'}, {'id':'title-ink','kind':'text_layout','target':'title','property':'color_argb'}, {'id':'expand-event','kind':'event'}, {'id':'select-event','kind':'event'}, {'id':'disabled-event','kind':'event'}, {'id':'replacement-event','kind':'event','stimulus':'caller_update'}, {'id':'visual','kind':'manual','target':'title','coverage':'targets','allowed_methods':['visual']}]
states=[{'id':'initial','input_index':0,'coverage':'full_content'}, {'id':'expanded','input_index':0,'after_action':0,'coverage':'targets'}, {'id':'selected','input_index':0,'after_action':1,'coverage':'targets'}, {'id':'blocked','input_index':0,'after_action':2,'coverage':'targets'}, {'id':'replaced','input_index':1,'after_action':3,'coverage':'targets'}]
actions=[{'type':'tap','target':'expand','reveal':True,'state_id':'expanded'}, {'type':'tap','target':'choice','reveal':True,'state_id':'selected'}, {'type':'tap','target':'disabled','reveal':True,'allow_disabled':True,'state_id':'blocked'}, {'type':'apply_next_fixture','state_id':'replaced'}]
def expr(pointer):return {'source':'reference','pointer':pointer}
scenarios={}
for config in ['normal','dark-large']:
 values={}
 for rule in rules:
  rid=rule['id']; cells={}
  for st in states:
   sid=st['id'];pointer=None
   if rid=='title':pointer='/labels/'+('new' if sid=='replaced' else 'old')
   elif rid in ['disclosure-height','layout-height']:
    v='expanded' if sid in ['expanded','selected','blocked'] else 'collapsed'
    cells[sid]={p:expr('/geometry/'+p+'/'+v) for p in ['ios','android']}
    cells[sid]['tolerance']={p:expr('/geometry/'+p+'/tolerance') for p in ['ios','android']};continue
   elif rid=='selection':pointer='/bool/'+('yes' if sid in ['selected','blocked'] else 'no')
   elif rid=='disabled':pointer='/bool/no'
   elif rid=='title-font':pointer='/title/font'
   elif rid=='title-ink':pointer='/title/'+config
   elif rid=='visual':pointer='/visual'
   else:
    eventstate={'expand-event':'expanded','select-event':'selected','disabled-event':'blocked','replacement-event':'replaced'}[rid]
    if sid!=eventstate:cells[sid]={'not_applicable':'This state has a different stimulus; no callback attribution to this rule.'};continue
    pointer='/events/'+{'expand-event':'expand','select-event':'select','disabled-event':'quiet','replacement-event':'quiet'}[rid]
   cells[sid]={p:expr(pointer) for p in ['ios','android']}
  values[rid]=cells
 scenarios[config]={'states':states,'actions':actions,'values':values}
contract={'version':1,'design_owner':'Independent neutral forward context, design fixed before source','approval_reference':'../APPROVAL.json and PREREGISTRATION.md','sources':[{'id':'reference','path':'reference.json','sha256':sha(d/'reference.json')}],'required_rule_ids':[r['id'] for r in rules],'rules':rules,'scenarios':scenarios}
write(d/'contract.json',contract)
lock=dc.seal(d/'contract.json',d);write(OUT/'approved-lock.json',lock)
digest=dc.digest(lock)
write(OUT/'APPROVAL.json',{'approvedAt':now(),'design_lock_sha256':digest,'reference_sha256':sha(d/'reference.json'),'contract_sha256':sha(d/'contract.json'),'interpretation':'Independent author fixed the typed design and acceptance before writing implementation. No external human approval is claimed.','native_commands_limit':4,'configurations':['normal','dark-large']})
print(json.dumps({'lock_sha256':digest,'at':now(),'barrier':receipts}))
