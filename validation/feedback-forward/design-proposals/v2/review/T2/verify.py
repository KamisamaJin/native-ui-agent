#!/usr/bin/env python3
import sys,json,hashlib,time,traceback,importlib.util
from pathlib import Path
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
OUT=ROOT/'validation/feedback-forward/design-review/T2'
DESIGN=ROOT/'validation/feedback-forward/design/T2/public'
FROZEN=ROOT/'validation/feedback-forward/candidate-v9'
sys.dont_write_bytecode=True
sys.path.insert(0,str(FROZEN/'scripts'))
import design_contract as d, execution_plan as ex, review_contract as rc, requirement_routes as rr, observation_contract as oc
spec=importlib.util.spec_from_file_location('implementation_audit',ROOT/'tools/implementation_audit.py')
ia=importlib.util.module_from_spec(spec);spec.loader.exec_module(ia)
# The shared sidecar normally prepends a live generic path. Preloading the frozen
# module above binds this SDK-free run solely to authorized candidate-v9 code.
assert Path(ia.d.__file__).resolve()==(FROZEN/'scripts/design_contract.py').resolve()
def load(p):return d.load(p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
logs=[]
def check(name,fn,expected_reject=False):
 row={'command':name,'startedAtUnix':time.time(),'expected_rejection':expected_reject}
 try:
  value=fn();row.update(status='unexpected_acceptance'if expected_reject else'passed',result=value)
 except Exception as e:
  row.update(status='expected_rejection'if expected_reject else'failed',exception=type(e).__name__,message=str(e),traceback=traceback.format_exc())
 row['finishedAtUnix']=time.time();row['wallSeconds']=row['finishedAtUnix']-row['startedAtUnix'];logs.append(row);return row
lock=load(DESIGN/'design-lock.json');ap=load(DESIGN/'approval.json');ref=load(DESIGN/'reference.json');bindings=load(DESIGN/'bindings.json');pol=load(DESIGN/'policy.json');routes=load(DESIGN/'routes.json');auditpol=load(DESIGN/'implementation-audit.json')
locksha=ap['design_lock_sha256'];polsha=ap['policy_sha256'];rsha=ap['routes_sha256'];asha=ap['implementation_audit_sha256']
check('frozen design_contract.validate_lock(design-lock, approval lock SHA)',lambda:d.validate_lock(lock,locksha))
check('frozen design_contract.seal(contract.json, design root) equals submitted lock',lambda: {'equal':d.seal(DESIGN/'contract.json',DESIGN)==lock})
check('canonical approved policy/routes/source-policy digests',lambda:{'policy':d.digest(pol)==polsha,'routes':d.digest(routes)==rsha,'source_policy':d.digest(auditpol)==asha})
check('design seal exact-byte integrity',lambda:{'mismatches':[x for x,h in load(DESIGN/'SEAL.json')['files'].items()if sha(DESIGN/x)!=h]})
for case in ['P1','P2']:
 for platform in ['ios','android']:
  stem=f'{case}-{platform}';source_actions=load(DESIGN/f'cases/{case}/actions.{platform}.json');fixture=load(DESIGN/f'cases/{case}/fixtures.json');bridge=DESIGN/('Bridge.swift'if platform=='ios'else'ObserverBridge.kt')
  try:
   started=time.time();plan,actions=d.compile_contract(lock,locksha,case,platform,bindings,source_actions);oc.validate_actions(actions)
   save(stem+'-plan.json',plan);save(stem+'-actions.json',actions)
   logs.append({'command':f'frozen design_contract.compile_contract({case}, {platform}) and observation_contract.validate_actions','startedAtUnix':started,'finishedAtUnix':time.time(),'status':'passed','result':{'states':len(plan['states']),'actions':len(actions),'assertions':len(plan['assertions']),'required':sum(x['disposition']=='required'for x in plan['matrix_contract']['cells']),'not_applicable':sum(x['disposition']=='not_applicable'for x in plan['matrix_contract']['cells']),'same_as_submitted_plan':plan==load(DESIGN/f'compiled/{case}/{platform}/plan.json'),'same_as_submitted_actions':actions==load(DESIGN/f'compiled/{case}/{platform}/actions.json')}})
  except Exception as e:
   logs.append({'command':f'compile_contract({case}, {platform})','status':'failed','exception':repr(e),'traceback':traceback.format_exc()});continue
  def catalog_check():
   cat=rc.catalog(plan,lock,locksha,pol,polsha,platform);save(stem+'-catalog.json',cat)
   return {'rows':len(cat['rows']),'same_as_submitted':cat==load(DESIGN/f'compiled/{case}/{platform}/review-catalog.json'),'kinds':sorted({(x['method'],x['aspect'])for x in cat['rows']})}
  check(f'frozen review_contract.catalog({case}, {platform})',catalog_check)
  def route_check():
   cov=rr.audit(lock,locksha,plan,routes,rsha);save(stem+'-coverage.json',cov)
   return {'must_route_gaps':cov['must_route_gaps'],'unowned_assertions':cov['unowned_assertions'],'same_as_submitted':cov==load(DESIGN/f'compiled/{case}/{platform}/coverage.json')}
  check(f'frozen requirement_routes.audit({case}, {platform})',route_check)
  def execution_check():
   run=ex.compile_execution(plan,lock,locksha,fixture,sha(bridge),launch_ref={'source':'reference','pointer':f'/launch/{case}/{platform}'})
   ex.verify_execution(run,plan,lock,locksha,fixture,sha(bridge));save(stem+'-execution.json',run)
   return {'scope':run['scope'],'action_count':len(run['actions']),'states':run['selected_states'],'same_as_submitted':run==load(DESIGN/f'compiled/{case}/{platform}/execution.json'),'max_after_targets':max(len(x.get('after_targets',[]))for x in run['actions']),'environment_digest_match':d.digest(load(DESIGN/f'cases/{case}/environment.{platform}.json'))==ap['environment_sha256'][case][platform]}
  check(f'frozen execution_plan.compile_execution and verify_execution({case}, {platform})',execution_check)
# Definitions use no invented production files and do not certify any source.
def definitions_check():
 cat=ia.catalog(lock,locksha,auditpol,asha,OUT/'no-production-read',DESIGN,definition_only=True);save('source-definitions.json',cat)
 return {'mode':cat['mode'],'rows':len(cat['rows']),'production_unread':all(x['sha256']is None for k,x in cat['files'].items()if not k.startswith('@design/')),'module':str(Path(ia.d.__file__).relative_to(ROOT))}
check('shared implementation_audit.catalog(..., definition_only=True) using preloaded frozen design_contract',definitions_check)
cat=load(OUT/'source-definitions.json')
check('shared implementation_audit.bind(definition_only, empty actual submission) must reject',lambda:ia.bind(cat,{'version':1,'catalog_sha256':d.digest(cat),'decisions':[]}),expected_reject=True)
# Recompute every business-state value from original BRIEF semantics.
truth=[]
for case,scenario in lock['contract']['scenarios'].items():
 caller=ref['cases'][case]['caller'];models=[caller['initial']]+caller['updates'];ix=0;wifi=True;opened=False;requested=False
 defs={s['after_action']:s for s in scenario['states']}
 for i,action in enumerate(scenario['actions']):
  events=[]
  if action['type']=='tap':
   t=action['target']
   if t=='disclosure':opened=not opened
   if t=='choice'and not requested:wifi=not wifi;events=[f'audio.wifiOnly:{models[ix]["id"]}:{str(wifi).lower()}']
   if t=='primary'and models[ix]['availableMB']>=models[ix]['downloadSizeMB']and not(models[ix]['meteredConnection']and wifi)and not requested:
    requested=True;events=[f'audio.download:{models[ix]["id"]}:{"wifi"if wifi else"mobile"}']
  if action['type']=='apply_next_fixture':ix+=1;wifi=True;opened=False;requested=False
  if i not in defs:continue
  s=defs[i]['id'];m=models[ix];enabled=m['availableMB']>=m['downloadSizeMB']and not(m['meteredConnection']and wifi)and not requested
  status='Storage needed'if m['availableMB']<m['downloadSizeMB']else'Download requested'if requested else'Wi-Fi required'if m['meteredConnection']and wifi else'Ready to download'
  actual={'title':m['title'],'subtitle':f'{m["language"]} · {m["downloadSizeMB"]} MB','status':status,'disclosure':'Hide chapters'if opened else'Review chapters','disclosureEnabled':True,'choice':'Wi-Fi only','selected':wifi,'choiceEnabled':not requested,'primary':'Requested'if requested else'Get audio','enabled':enabled,'open':opened,'requested':requested,'statusColor':ref['palette']['requested'if requested else 'blocked'if status in ['Storage needed','Wi-Fi required']else'ready']['value'],'buttonColor':ref['palette']['enabled'if enabled else'disabled']['value']}
  expected=ref['cases'][case]['states'][s]
  truth.append({'case':case,'state':s,'action_index':i,'input_index':ix,'expected_input_index':defs[i]['input_index'],'mismatches':{k:{'derived':v,'reference':expected.get(k)}for k,v in actual.items()if expected.get(k,{}).get('value')!=v}})
save('business-derivation.json',truth)
check('original BRIEF business derivation against revised source values',lambda:{'states':len(truth),'mismatches':[x for x in truth if x['mismatches']or x['input_index']!=x['expected_input_index']]})
caller_records=[]
for case,v in ref['cases'].items():
 caller_records.append({'case':case,'initial_matches_claimed_original_digest':d.digest(v['caller']['initial'])==v['original_initial_sha256'],'first_update_matches_claimed_original_digest':d.digest(v['caller']['updates'][0])==v['original_update_sha256'],'fixtures_match_reference_caller':load(DESIGN/f'cases/{case}/fixtures.json')==v['caller'],'original_record_raw_access':'not authorized; only raw v1 BRIEF/API read','appended_competing_gates':{k:v['caller']['updates'][1][k]for k in ['id','downloadSizeMB','availableMB','meteredConnection']}})
save('caller-preservation.json',caller_records)
# Exhaustive declared state/rule dispositions retained for reviewer inspection.
save('runtime-dispositions.json',{case:{rid:{s:({'not_applicable':cell['not_applicable']}if 'not_applicable'in cell else cell)for s,cell in cells.items()}for rid,cells in scenario['values'].items()}for case,scenario in lock['contract']['scenarios'].items()})
inputs=[*DESIGN.rglob('*'),*FROZEN.rglob('*'),ROOT/'tools/implementation_audit.py',ROOT/'validation/feedback-forward/SOURCE-AUDIT.md',ROOT/'validation/feedback-forward/PREIMPLEMENTATION-AMENDMENT.md',ROOT/'validation/feedback-forward/design-proposals/v1/design/T2/public/BRIEF.md',ROOT/'validation/feedback-forward/design-proposals/v1/design/T2/public/API.md',ROOT/'validation/feedback-forward/operators/T2-design-review-request.txt']
save('source-hashes.json',{str(p.relative_to(ROOT)):sha(p)for p in inputs if p.is_file()and'__pycache__'not in p.parts})
save('commands.json',logs)
print(json.dumps({'checks':len(logs),'failed':[x for x in logs if x['status']in ['failed','unexpected_acceptance']],'summaries':[{k:v for k,v in x.items()if k not in ['traceback','startedAtUnix','finishedAtUnix']}for x in logs]},indent=2))
