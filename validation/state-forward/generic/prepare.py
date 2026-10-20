#!/usr/bin/env python3
"""Fix neutral inputs and expected facts before any native collection."""
import json
from pathlib import Path
R=Path(__file__).resolve().parent
def write(name,value):
 p=R/name
 if p.exists():raise ValueError('Fresh preparation only')
 p.write_text(json.dumps(value,indent=2)+'\n')
def target(x):return {'identifier':'probe.'+x}
config={'initial':{'rows':8,'token':'A'},'updates':[{'rows':12,'token':'B'}],
        'width':390,'theme':'light','dynamic_type':'large','fontScale':1.0,
        'direction':'ltr','state_capture':False,'max_scrolls':20,
        'observation_targets':[target(x) for x in ['header','footer','secondary','disclosure','disabled']]}
actions=[{'type':'sweep','state_id':'full-initial','max_steps':24},
         {'type':'tap','target':target('disclosure'),'reveal':True,'state_id':'expanded'},
         {'type':'tap','target':target('secondary'),'reveal':True,'state_id':'continued'},
         {'type':'capture','state_id':'bounded-missing','after_targets':[target('missing')],'observation_max_scrolls':0},
         {'type':'apply_next_fixture','state_id':'updated'},
         {'type':'tap','target':target('disabled'),'reveal':True,'allow_disabled':True,'state_id':'disabled'},
         {'type':'sweep','state_id':'full-update','max_steps':24}]
states=[{'id':s,'input_index':i,'after_action':a,'coverage':'targets'} for s,i,a in
        [('expanded',0,1),('continued',0,2),('updated',1,4),('disabled',1,5)]]
requirements=[]
for name,prefix in [('header','Panel '),('footer','End '),('secondary','Continue ')]:
 requirements.append({'id':name+'-label','source':'generic/prepare.py: neutral fixed label contract',
   'check':{'kind':'control','target':target(name),'property':'label'},
   'by_state':{s['id']:{'expected':prefix+('A' if s['input_index']==0 else 'B')}for s in states}})
requirements.append({'id':'event','source':'generic/prepare.py: dispatch/quietness contract',
 'check':{'kind':'event'},'by_state':{'expanded':{'expected':['expanded']},
 'continued':{'expected':['secondary']},'updated':{'expected':[],'stimulus':'caller_update'},'disabled':{'expected':[]}}})
matrix={'version':1,'required_state_ids':[s['id']for s in states],
        'required_requirement_ids':[r['id']for r in requirements], 'states':states,'requirements':requirements}
write('fixtures.json',config);write('actions-base.json',actions);write('matrix.json',matrix)
write('expected.json',{'scope':'Chosen before native commands; no business component or prior result used.',
 'target_label_cells':12,'enabled_event_cells_expected_P':3,'disabled_event_expected_U':1,
 'missing_target':'Unavailable with zero observation scrolls; no callback claim.',
 'callback_boundary':'Exactly one activation for each enabled action; no observation extends callback window.',
 'coverage':'Target sets never establish full-content completeness; explicit full sweeps separate.',
 'comparison':'Same bridge/inputs/actions/plan, frozen v4 vs v5. Legacy frames earn actual native facts; no manufactured U.'})
