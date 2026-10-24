import copy, hashlib, importlib.util, json, os, sys, time
from pathlib import Path
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
SCOPE=os.environ.get('REVIEW_SCOPE','public')
P=ROOT/'validation/feedback-forward/design/T2'/SCOPE
O=Path(__file__).resolve().parent
if SCOPE!='public':O=O/(SCOPE+'-checks')
F=ROOT/'validation/feedback-forward/candidate-v9'
sys.path.insert(0,str(F/'scripts'))
import design_contract as d, execution_plan as e, native_checks as n
started=time.time(); reference=d.load(P/'reference.json'); lock=d.load(P/'design-lock.json');approval=d.load(P/'approval.json')
comparisons=[];event_routes=[]
roles={'Storage needed':'blocked','Download requested':'requested','Wi-Fi required':'waiting','Ready to download':'ready'}
CASES=list(lock['contract']['scenarios'])
for case in CASES:
 fixtures=d.load(P/'cases'/case/'fixtures.json');models=[fixtures['initial'],*fixtures['updates']]
 assert len(models)==3 and len({m['id'] for m in models})==3
 assert len(models[0]['chapters'])==8
 for model in models:
  assert len({c['id'] for c in model['chapters']})==len(model['chapters'])
  assert type(model['downloadSizeMB']) is int and type(model['availableMB']) is int
 # A fresh, independent business interpreter, derived from original prose.
 model=models[0];index=0;wifi=True;opened=False;requested=False;events={}
 states=lock['contract']['scenarios'][case]['states'];actions=lock['contract']['scenarios'][case]['actions']
 for i,action in enumerate(actions):
  emitted=[]
  if action['type']=='apply_next_fixture':
   index+=1;model=models[index];wifi=True;opened=False;requested=False
  elif action['type']=='tap':
   if action['target']=='disclosure':opened=not opened
   elif action['target']=='choice':
    assert not requested;wifi=not wifi;emitted=[f'audio.wifiOnly:{model["id"]}:{str(wifi).lower()}']
   elif action['target']=='primary':
    assert model['availableMB']>=model['downloadSizeMB'] and not(model['meteredConnection'] and wifi) and not requested
    emitted=[f'audio.download:{model["id"]}:{"wifi" if wifi else "mobile"}'];requested=True
  events[i]=emitted
  for state in states:
   if state['after_action']!=i:continue
   sid=state['id'];actual=reference['cases'][case]['states'][sid]
   status=('Storage needed' if model['availableMB']<model['downloadSizeMB'] else 'Download requested' if requested else 'Wi-Fi required' if model['meteredConnection'] and wifi else 'Ready to download')
   enabled=model['availableMB']>=model['downloadSizeMB'] and not(model['meteredConnection'] and wifi) and not requested
   expected={'title':model['title'],'subtitle':f'{model["language"]} · {model["downloadSizeMB"]} MB','status':status,'disclosure':'Hide chapters' if opened else 'Review chapters','disclosureEnabled':True,'choice':'Wi-Fi only','selected':wifi,'choiceEnabled':not requested,'primary':'Requested' if requested else 'Get audio','enabled':enabled,'open':opened,'requested':requested,'statusColor':reference['palette'][roles[status]]['value'],'buttonColor':reference['palette']['enabled' if enabled else 'disabled']['value']}
   for key,value in expected.items():
    assert actual[key]['value']==value,(case,sid,key,value,actual[key])
   assert state['input_index']==index
   comparisons.append({'case':case,'state':sid,'source_fixture_index':index,'values_compared':list(expected),'match':True})
 for platform in ['ios','android']:
  plan=d.load(O/'rebuilt'/case/platform/'plan.json')
  for assertion in plan['assertions']:
   if assertion['kind']=='event':
    event_index=assertion['action_index'];assert assertion['expected']==events[event_index],(case,assertion)
    if assertion['requirement_id']=='replacement-quiet':assert assertion['stimulus']=='caller_update' and actions[event_index]['type']=='apply_next_fixture'
    event_routes.append({'case':case,'platform':platform,'id':assertion['id'],'action_index':event_index,'stimulus':assertion.get('stimulus','activation'),'expected':assertion['expected'],'match_independent_interpreter':True})
  section_rules=[a for a in plan['assertions'] if a['requirement_id'].startswith('section-')]
  for a in section_rules:
   _,number,part=a['requirement_id'].split('-');model=models[next(s['input_index'] for s in states if s['id']==a['state'])]
   assert a['expected']==model['chapters'][int(number)]['title' if part=='heading' else 'body']

controls=[]
def rejected(name,fn):
 try:fn()
 except (ValueError,RuntimeError) as ex:controls.append({'name':name,'result':'rejected','exception':str(ex)})
 else:raise AssertionError('Unexpected acceptance '+name)
case=CASES[0]
plan=d.load(O/'rebuilt'/case/'ios/plan.json');fixture=d.load(P/'cases'/case/'fixtures.json');bridge_sha=hashlib.sha256((P/'Bridge.swift').read_bytes()).hexdigest()
tamper=copy.deepcopy(plan);tamper['assertions'][0]['expected']='FOREIGN EXPECTED'
rejected('expected_override',lambda:d.verify_generated(tamper,lock,approval['design_lock_sha256'],'ios'))
foreign=copy.deepcopy(fixture);foreign['initial']['availableMB']+=1
rejected('foreign_caller_fixture',lambda:e.compile_execution(plan,lock,approval['design_lock_sha256'],foreign,bridge_sha,launch_ref={'source':'reference','pointer':'/launch/'+case+'/ios'}))
execution=d.load(O/'rebuilt'/case/'ios/execution-inputs/execution.json');wrong=copy.deepcopy(execution);wrong['actions'].pop()
rejected('dropped_execution_action',lambda:e.verify_execution(wrong,plan,lock,approval['design_lock_sha256'],fixture,bridge_sha))
for platform in ['ios','android']:
 result=n.callback_verdict({'outcome':'blocked_disabled','callback_delta':[],'dispatch':{'attempted':False,'succeeded':False}},[],platform)
 assert result['status']=='unassessed';controls.append({'name':platform+'_disabled_empty_interval','result':result['status'],'reason':result['reason']})
spec=importlib.util.spec_from_file_location('shared_source_audit',ROOT/'tools/implementation_audit.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
defs=d.load(O/'source-audit-definitions.json')
rejected('definition_only_source_acceptance',lambda:a.bind(defs,{'version':1,'catalog_sha256':d.digest(defs),'decisions':[]}))

result={'startedAtUnix':started,'finishedAtUnix':time.time(),'independent_expected_comparisons':comparisons,'events':event_routes,'rejected_or_unassessed_controls':controls,'scope':'Static interpreter and negative tool controls only; synthetic blocked-action packet is not product or native evidence.'}
(O/'semantic-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'case_states_compared':len(comparisons),'event_assertions_compared':len(event_routes),'negative_controls':controls},indent=2))
