"""Bounded SDK-free supplemental H1 design check; no product inputs."""
import copy,hashlib,importlib.util,json,sys,time
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
BASE=ROOT/'validation/feedback-forward'
D=BASE/'design/T1/private'
P=BASE/'design/T1/public'
F=BASE/'candidate-v9'
began=time.time()
sys.dont_write_bytecode=True
sys.path.insert(0,str(F/'scripts'))
import design_contract as dc
import execution_plan as ep
import review_contract as rc
import requirement_routes as rr
import native_checks as nc

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,v):
 p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x')as f:f.write(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def same(a,b):assert a==b;return True
rows=[]
def check(name,fn,reject=False):
 t=time.time()
 try:
  v=fn()
  assert not reject,'Missing expected rejection'
  rows.append({'name':name,'startedAtUnix':t,'finishedAtUnix':time.time(),'status':'passed'})
  return v
 except ValueError as e:
  if not reject:raise
  rows.append({'name':name,'startedAtUnix':t,'finishedAtUnix':time.time(),'status':'expected_rejection','reason':str(e)})

a=dc.load(D/'approval.json');l=dc.load(D/'design-lock.json');r=l['sources']['reference']['document'];ls=a['design_lock_sha256']
seal=dc.load(D/'SEAL.json')
check('all private original byte-seal entries',lambda:same({k:sha(D/k)for k in seal['files']},seal['files']))
check('actual frozen seal API reconstructs H1 lock',lambda:same(dc.seal(D/'contract.json',D),l))
check('validate_lock canonical/source/expression validation',lambda:dc.validate_lock(l,ls))
check('private API bytes equal public API',lambda:same((D/'API.md').read_bytes(),(P/'API.md').read_bytes()))
for n in ['Bridge.swift','ObserverBridge.kt','routes.json','bindings.json','compatibility.json','implementation-audit.json']:
 check('private/public shared input '+n,lambda n=n:same((D/n).read_bytes(),(P/n).read_bytes()))
raw=BASE/'design-proposals/v1/design/T1/public/API.md'
for lang in ['swift','kotlin']:
 check('original public '+lang+' declarations preserved',lambda lang=lang:same((D/'API.md').read_text().split('```'+lang+'\n',1)[1].split('```',1)[0],raw.read_text().split('```'+lang+'\n',1)[1].split('```',1)[0]))
pubr=dc.load(P/'reference.json')
for key in ['palette','geometry','questions','api_declaration_contracts','audit_propositions','implementation_audits']:
 check('H1 matches public shared business/source '+key,lambda key=key:same(r[key],pubr[key]))
check('pinned minimum API checker interface hash',lambda:same(sha(BASE/'check_minimum_api.py'),r['compatibility']['shared_checker']['sha256']))

fx=dc.load(D/'cases/H1/fixtures.json');models=[fx['initial']]+fx['updates']
assert len(models)==2 and models[0]['id']!=models[1]['id']
check('caller fixture exactly equals sealed independent caller',lambda:same({'initial':fx['initial'],'updates':fx['updates']},r['cases']['H1']['caller']))
check('initial caller matches original caller canonical hash pin',lambda:same(dc.digest(models[0]),r['cases']['H1']['original_initial_sha256']))
check('replacement caller matches original caller canonical hash pin',lambda:same(dc.digest(models[1]),r['cases']['H1']['original_update_sha256']))
assert models[0]['sealIntact'] is True and models[0]['coolantReady'] is True
assert models[1]['sealIntact'] is False and models[1]['coolantReady'] is False
assert fx['width']==400 and fx['viewportHeight']==600 and fx['theme']=='light' and fx['direction']=='rtl' and fx['dynamic_type']=='large' and fx['fontScale']==1.0
for m in models:
 assert all(isinstance(m[k],str)for k in ['id','title','destination','temperatureRange'])
 assert len(m['notes'])==8 and len({n['id']for n in m['notes']})==8
 assert all(isinstance(n[k],str)for n in m['notes']for k in ['id','title','body'])

pol=dc.load(D/'policy.json');routes=dc.load(D/'routes.json');bind=dc.load(D/'bindings.json')
rule=next(v for v in l['contract']['rules']if v['id']=='status-leading-inset')
assert rule['property']=='inset_right'and rule['op']=='gte'and rule['basis']=='semantic'and rule['measurement']=='accessibility_box'
atom=next(v for v in pol['atoms']if v['rule_id']=='status-leading-clear')
assert atom['sampling']['region']==[.96,0,1,1]and atom['sampling']['minimum_support']==1.0 and atom['sampling']['channel_tolerance']==0
assert next(v for v in pol['atoms']if v['rule_id']=='status-fill')['sampling']['region']==[.965,.2,.988,.8]

spec=importlib.util.spec_from_file_location('h1_implementation_audit',ROOT/'tools/implementation_audit.py');ia=importlib.util.module_from_spec(spec);spec.loader.exec_module(ia);assert ia.d is dc
defs=check('actual source-only definitions API with frozen compiler preloaded',lambda:ia.catalog(l,ls,dc.load(D/'implementation-audit.json'),a['implementation_audit_sha256'],OUT/'no-product',D,definition_only=True))
check('source-only definitions equal published definitions',lambda:same(defs,dc.load(D/'compiled/source-audit-definitions.json')))
save('source-audit-definitions.json',defs)
check('definition-only rows cannot certify source acceptance',lambda:ia.bind(defs,{}),True)
summaries=[];semantics=[];plans={};gaps=[]
for platform in ['ios','android']:
 case='H1';env=dc.load(D/'cases/H1'/('environment.'+platform+'.json'))
 assert dc.digest(env)==a['environment_sha256'][case][platform]
 assert env['width']==400 and env['height']==600 and env['theme']=='light'and env['direction']=='rtl'
 assert env.get('dynamic_type')=='large'if platform=='ios'else env.get('font_scale')==1.0
 source_actions=dc.load(D/'cases/H1'/('actions.'+platform+'.json'))
 plan,actions=check('actual frozen compile_contract H1/'+platform,lambda:dc.compile_contract(l,ls,case,platform,bind,source_actions));plans[platform]=plan
 target=D/'compiled/H1'/platform
 check('published plan/actions exact '+platform,lambda:same([plan,actions],[dc.load(target/'plan.json'),dc.load(target/'actions.json')]))
 cat=check('actual frozen review_contract.catalog '+platform,lambda:rc.catalog(plan,l,ls,pol,a['policy_sha256'],platform))
 provided=dc.load(target/'review-catalog.json');assert provided.pop('catalog_sha256')==dc.digest(cat)
 check('published catalog exact '+platform,lambda:same(cat,provided))
 cov=check('actual frozen requirement_routes.audit '+platform,lambda:rr.audit(l,ls,plan,routes,a['routes_sha256']))
 assert not cov['must_route_gaps'] and not cov['unowned_assertions']
 check('published coverage exact '+platform,lambda:same(cov,dc.load(target/'coverage.json')))
 bridge=D/('Bridge.swift'if platform=='ios'else'ObserverBridge.kt')
 ex=check('actual frozen compile_execution '+platform,lambda:ep.compile_execution(plan,l,ls,fx,sha(bridge),launch_ref={'source':'reference','pointer':'/launch/H1/'+platform}))
 check('actual frozen verify_execution '+platform,lambda:ep.verify_execution(ex,plan,l,ls,fx,sha(bridge)))
 check('published execution exact '+platform,lambda:same(ex,dc.load(target/'execution.json')))
 assert len(plan['states'])==9 and len(ex['actions'])==13<=40
 assert {s['id']for s in plan['states']if s['coverage']=='full_content'}=={'overview','permitted','requested','requested-closed','replaced'}
 for o in r['obligations']:
  if o['priority']=='must':
   for state in o['states']:
    if not any(c['state']==state and c['requirement_id']in routes['routes'][o['id']]['rule_ids']and c['disposition']=='required'for c in plan['matrix_contract']['cells']):gaps.append([platform,o['id'],state])
 ack=False;requested=False;opened=False;idx=0;at={};receipts={}
 for i,act in enumerate(ex['actions']):
  m=models[idx];events=[]
  if act['type']=='tap':
   id=act['target']['identifier']
   if id=='transfer.disclosure':opened=not opened
   elif id=='transfer.choice':
    assert not requested;ack=not ack;events=['transfer.ack:'+m['id']+':'+str(ack).lower()]
   elif id=='transfer.primary':
    assert m['sealIntact']and m['coolantReady']and ack and not requested
    requested=True;events=['transfer.release:'+m['id']]
  elif act['type']=='apply_next_fixture':idx+=1;ack=requested=opened=False
  m=models[idx];status='Seal needs attention'if not m['sealIntact']else'Coolant not ready'if not m['coolantReady']else'Release requested'if requested else'Ready for release'if ack else'Awaiting check'
  receipts[i]=events
  at[i]={'title-label':m['title'],'subtitle-label':m['destination']+' · '+m['temperatureRange'],'status-label':status,'status-text-label':status,'disclosure-label':'Hide handling'if opened else'Review handling','disclosure-enabled':True,'choice-label':'Seal check confirmed'if ack else'Confirm seal checked','choice-selected':ack,'choice-enabled':not requested,'primary-label':'Requested'if requested else'Release transfer','primary-enabled':m['sealIntact']and m['coolantReady']and ack and not requested,'model':m,'open':opened,'input_index':idx}
 facts=[]
 for state in plan['states']:
  expected=at[state['after_action']];assert state['input_index']==expected['input_index']
  event=[]
  for v in [v for v in plan['assertions']if v['state']==state['id']]:
   rid=v['requirement_id'];assert v['expectation_provenance']
   if rid in expected:assert v['expected']==expected[rid],(platform,state['id'],rid)
   if rid.startswith('section-'):
    _,num,role=rid.split('-');assert expected['open'];assert v['expected']==expected['model']['notes'][int(num)]['title'if role=='heading'else'body']
   if rid=='status-fill':assert v['expected']==int(r['palette'][r['status_role_mapping'][expected['status-label']]['value']]['value'][1:],16)
   if rid=='primary-fill':assert v['expected']==int(r['palette']['enabled'if expected['primary-enabled']else'disabled']['value'][1:],16)
   if rid=='status-leading-inset':assert v['property']=='inset_right'and v['expected']==16 and v['unit']==('pt'if platform=='ios'else'dp')and'tolerance'not in v
   if v['kind']=='event':
    ai=state.get('stimulus_action',state['after_action']);assert v['action_index']==ai and v['expected']==receipts[ai]
    assert ex['actions'][ai]['type']in{'tap','apply_next_fixture'}
    assert (v.get('stimulus')=='caller_update')==(ex['actions'][ai]['type']=='apply_next_fixture')
    event.append({'rule':rid,'action_index':ai,'stimulus':v.get('stimulus','activation'),'expected':v['expected']})
  facts.append({'state':state,'status':expected['status-label'],'choice_selected':expected['choice-selected'],'primary_enabled':expected['primary-enabled'],'callbacks':event})
 assert at[11]['status-label']=='Seal needs attention'and at[12]['status-label']=='Seal needs attention'and at[12]['choice-selected']is True and at[12]['primary-enabled']is False
 semantics.append({'platform':platform,'reference_values_match_independent_business_simulation':True,'states':facts})
 for name,value in [('plan',plan),('actions',actions),('catalog',cat),('coverage',cov),('execution',ex)]:save('reconstructed/'+platform+'/'+name+'.json',value)
 summaries.append({'case':case,'platform':platform,'states':9,'actions':13,'assertions':len(plan['assertions']),'cells':len(plan['matrix_contract']['cells']),'manual_catalog_rows':len(cat['rows']),'NA_cells':sum(c['disposition']=='not_applicable'for c in plan['matrix_contract']['cells']),'plan_sha256':dc.digest(plan),'execution_sha256':ex['execution_sha256'],'must_route_gaps':cov['must_route_gaps']})
 if platform=='ios':
  wrong=copy.deepcopy(ex);wrong['actions'][10]['type']='checkpoint'
  check('removed successful update route is rejected',lambda:ep.verify_execution(wrong,plan,l,ls,fx,sha(bridge)),True)
 assert nc.callback_verdict({'callback_delta':[],'dispatch':{'attempted':False,'succeeded':False}},[],platform)['status']=='unassessed'
assert not gaps
cw=dc.load(D/'requirement-crosswalk.json');assert cw['clauses']==r['requirement_crosswalk']
for c in cw['clauses']:
 assert set(c['source_audit_ids'])<={v['id']for v in defs['rows']}
 assert set(c['runtime_rule_ids'])<=set(l['contract']['required_rule_ids'])
 if not c['id'].startswith('retained-rendered-'):
  source=ROOT/c['original_source']['path'];assert source.name in {'BRIEF.md','API.md'}and'design-proposals/v1/design/T1/public'in str(source)
  assert sha(source)==c['original_source']['sha256']and 1<=c['original_source']['line']<=len(source.read_text().splitlines())
save('semantic-checks.json',semantics)
save('checks.json',{'command':['python3','-B',str(Path(__file__).resolve())],'startedAtUnix':began,'finishedAtUnix':time.time(),'checks':rows,'summaries':summaries,'source_definitions':len(defs['rows']),'seal_entries':len(seal['files']),'per_MUST_selected_state_route_gaps':gaps,'authoring_parser_errors':[],'scope':'Pure Python design-source reconstruction and independent business simulation, no SDK/product source/runtime.'})
print(json.dumps({'status':'passed','checks':len(rows),'summaries':summaries,'source_definitions':len(defs['rows']),'errors':[]},indent=2))
