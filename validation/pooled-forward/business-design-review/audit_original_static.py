from pathlib import Path
import json,sys,hashlib,copy,re,collections
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward');ROOT=BASE/'business-design';OUT=BASE/'business-design-review';TOOL=BASE/'candidate-v13.9/scripts'
sys.path.insert(0,str(TOOL))
import design_contract as d,observation_contract as oc,review_contract as rc,native_pixels as pixels
try:
 import jsonschema
except ImportError:jsonschema=None

def load(p):return json.loads(p.read_text())
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def typed_plain(v):
 if isinstance(v,dict) and set(v)=={'value','unit'}:return v['value']
 if isinstance(v,dict):return {k:typed_plain(x) for k,x in v.items()}
 if isinstance(v,list):return [typed_plain(x) for x in v]
 return v

def leaves(v,p=''):
 if isinstance(v,dict):
  for k,x in v.items():yield from leaves(x,p+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):yield from leaves(x,p+'/'+str(i))
 else:yield p,v

rows=[];all_errors=[]
for t in range(1,6):
 pub=ROOT/f'T{t}'/'public';private=ROOT/f'T{t}'/'private'
 public_bytes=b'\n'.join(p.read_bytes() for p in sorted(pub.rglob('*')) if p.is_file())
 hidden_data=load(private/'fixtures.ios.json');public_data=load(pub/'fixtures.ios.json')
 known_public={v for _,v in leaves(public_data) if isinstance(v,str)}
 unique_hidden=sorted({v for _,v in leaves(hidden_data) if isinstance(v,str) and len(v)>=16 and v not in known_public})
 leakage=[v for v in unique_hidden if v.encode() in public_bytes]
 for phase in ['public','private']:
  p=ROOT/f'T{t}'/phase;c=load(p/'contract.json');lock=load(p/'lock.json');ref=load(p/'reference.json');seal=load(p/'seal.json');policy=load(p/'policy.json');routes=load(p/'routes.json');den=load(p/'denominator.json');outcomes=load(p/'outcomes.json');obs=load(p/'target-observations.json')
  sid=seal['scenario'];s=c['scenarios'][sid];errs=[];cell_errors=[];schemas=[];actions=[]
  if d.digest(lock)!=seal['design_lock_sha256']:errs.append('canonical lock mismatch')
  if d.digest(policy)!=seal['policy_sha256']:errs.append('canonical policy mismatch')
  if d.digest(routes)!=seal['routes_sha256']:errs.append('canonical routes mismatch')
  if lock['contract']!=c:errs.append('lock embedded contract mismatch')
  for source in c['sources']:
   src=p/source['path'];l=lock['sources'][source['id']]
   if not src.resolve().is_relative_to(p.resolve()):errs.append('source escaped partition')
   if hashlib.sha256(src.read_bytes()).hexdigest()!=source['sha256']:errs.append('source byte hash mismatch')
   if l['raw_utf8']!=src.read_text() or l['document']!=load(src):errs.append('embedded source document/raw mismatch')
  for platform in ['ios','android']:
   env=load(p/f'environment.{platform}.json');fixture=load(p/f'fixtures.{platform}.json');aa=load(p/f'actions.{platform}.json');bind=load(p/f'bindings.{platform}.json')
   if d.digest(env)!=seal['environment_sha256'][platform]:errs.append('environment canonical mismatch '+platform)
   if load(p/'launch.json')[platform]['fixtures_sha256']!=d.digest(fixture):errs.append('launch fixture mismatch '+platform)
   if load(p/'launch.json')[platform]['bridge_sha256']!=hashlib.sha256((p/('ObserverBridge.swift' if platform=='ios' else 'ObserverBridge.kt')).read_bytes()).hexdigest():errs.append('launch bridge mismatch '+platform)
   try:oc.validate_actions(aa);action_error=None
   except Exception as e:action_error=str(e)
   actions.append({'platform':platform,'action_count':len(aa),'max_index':len(aa)-1,'count_le25':len(aa)<=25,'validator_error':action_error})
   schema=load(p/'fixture.schema.json')
   if jsonschema:
    jsonschema.Draft202012Validator.check_schema(schema)
    validator=jsonschema.Draft202012Validator(schema)
    for i,f in enumerate([fixture['initial']]+fixture['updates']):
     for e in validator.iter_errors(f):schemas.append({'platform':platform,'input_index':i,'pointer':'/'+('/'.join(map(str,e.path))),'reason':e.message})
   else:schemas.append({'error':'jsonschema unavailable'})
   for rule in c['rules']:
    for state,cell in s['values'][rule['id']].items():
     if 'not_applicable' in cell:continue
     try:d.expression(copy.deepcopy(cell[platform]),lock['sources'])
     except Exception as e:cell_errors.append({'rule':rule['id'],'state':state,'platform':platform,'expression':cell[platform],'reason':str(e)})
   for selector in bind.values():oc.validate_selector(selector)
  # Exact independent outcome ledger and typed reference agreement.
  semantic=[]
  for state in outcomes['states']:
   target=typed_plain(ref['states'][state['id']]);statex=state['exact_business_state']
   checks={'entity':statex['entity'],'description':statex['description'],'summary':statex['summary'],'status':statex['status'],'preview_present':statex['preview'] is not None}
   if statex['preview'] is not None:checks['preview']=statex['preview']
   for k,v in checks.items():
    if target.get(k)!=v:semantic.append({'state':state['id'],'key':k,'outcome':v,'reference':target.get(k)})
   for name,ctrl in statex['controls'].items():
    for k,v in ctrl.items():
     if k!='kind' and target['controls'][name].get(k)!=v:semantic.append({'state':state['id'],'key':name+'/'+k})
   if target['controls']['primary']['enabled']!=statex['primary_enabled']:semantic.append({'state':state['id'],'key':'primary_enabled'})
   aa=load(p/'actions.ios.json');ai=state.get('stimulus_action')
   if ai is not None and aa[ai]['type']=='tap':
    if target['tap_events']!=state['exact_callback_interval']:semantic.append({'state':state['id'],'key':'tap_events'})
   elif ai is not None and aa[ai]['type']=='apply_next_fixture':
    if target['replacement_events']!=state['exact_callback_interval']:semantic.append({'state':state['id'],'key':'replacement_events'})
  atom_errors=[]
  for atom in policy['atoms']:
   if atom['method']=='visual':
    if atom['aspect'] not in rc.VISUAL_ASPECTS:atom_errors.append({'rule':atom['rule_id'],'aspect':atom['aspect'],'reason':'unsupported frozen visual aspect enum'})
    q,_=d.expression(atom['question'],lock['sources'])
    if q['unit']!='string' or not q['value'].strip():atom_errors.append({'rule':atom['rule_id'],'reason':'invalid proposition'})
   elif atom['method']=='native_pixels':
    try:pixels.validate_sampling(atom['sampling'])
    except Exception as e:atom_errors.append({'rule':atom['rule_id'],'reason':str(e)})
  # Source metadata / references are strictly partition-local. Public has no exact hidden unique strings.
  if leakage and phase=='public':errs.append('hidden fixture text leaked into public artifacts')
  row={'family':f'T{t}/{phase}','lock_sha256':d.digest(lock),'rule_count':len(c['rules']),'state_count':len(s['states']),'contract_cells':len(c['rules'])*len(s['states']),'denominator_keys':list(den),'denominator_rows':len(den.get('cells',[])),'schema_errors':schemas,'identity_errors':errs,'expression_errors':cell_errors,'policy_errors':atom_errors,'reference_outcome_errors':semantic,'action_summaries':actions,'hidden_unique_strings_checked':len(unique_hidden),'hidden_public_leak_matches':leakage if phase=='public' else [],'full_states':[st['id'] for st in s['states'] if st['coverage']=='full_content'],'target_states':[st['id'] for st in s['states'] if st['coverage']=='targets']}
  rows.append(row)
  all_errors.extend([{'family':row['family'],'kind':'identity','detail':e} for e in errs]+[{'family':row['family'],'kind':'schema','detail':e} for e in schemas]+[{'family':row['family'],'kind':'reference_outcome','detail':e} for e in semantic])
dump(OUT/'static-original-audit.json',{'families':rows,'nonformat_errors':all_errors})
# Complete relevant public tool readset including pure-loaded modules and files inspected with rg.
rs=load(OUT/'READSET.json');seen={e['path'] for e in rs}
for name in ['design_contract.py','observation_contract.py','native_checks.py','native_pixels.py','review_contract.py','execution_plan.py','requirement_routes.py','action_guard.py','evidence_responsibility.py','native_environment.py']:
 p=TOOL/name
 if str(p) not in seen:
  b=p.read_bytes();rs.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'operation':'pure-generator-schema-dependency-or-inspection'})
dump(OUT/'READSET.json',rs)
print(json.dumps({'families':len(rows),'nonformat_errors':len(all_errors),'expression_errors':sum(len(r['expression_errors']) for r in rows),'policy_errors':sum(len(r['policy_errors']) for r in rows),'reserved_action_errors':sum(bool(a['validator_error']) for r in rows for a in r['action_summaries']),'schema_available':bool(jsonschema),'schemas_passed':all(not r['schema_errors'] for r in rows),'source_hashes_and_no_hidden_leaks_passed':all(not r['identity_errors'] for r in rows)},indent=2))
