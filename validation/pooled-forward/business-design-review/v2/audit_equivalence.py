from pathlib import Path
import json,sys,hashlib,copy,collections,re
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward');ROOT=BASE/'business-design-v2';OLD=BASE/'business-design';OUT=BASE/'business-design-review/v2';TOOL=BASE/'candidate-v13.9/scripts';DEP=BASE/'cache/design-schema-python'
sys.path.insert(0,str(DEP));sys.path.insert(0,str(TOOL));sys.dont_write_bytecode=True
import jsonschema,design_contract as d,action_guard,observation_contract

def load(p):return json.loads(p.read_text())
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def norm(v):
 if isinstance(v,dict):return {('start'if k=='initial'else k):norm(x)for k,x in v.items()}
 if isinstance(v,list):return [norm(x)for x in v]
 if isinstance(v,str):return 'start'if v=='initial'else 'scalar'if v=='number'else v.replace('/states/initial/','/states/start/')
 return v

def leaves(v):
 if isinstance(v,dict):
  for x in v.values():yield from leaves(x)
 elif isinstance(v,list):
  for x in v:yield from leaves(x)
 else:yield v

families=[];profiles=[];errors=[];fixture_count=0;master_total=compiled_total=0
byte_invariants=['fixtures.ios.json','fixtures.android.json','ObserverBridge.swift','ObserverBridge.kt','reference-initial.svg','reference-ready.svg','fixture.schema.json','API.md','PIXEL-SCOPE.md','environment.ios.json','environment.android.json','bindings.ios.json','bindings.android.json']
for t in range(1,6):
 private_input=load(ROOT/f'T{t}/private/fixtures.ios.json');public_input=load(ROOT/f'T{t}/public/fixtures.ios.json');pubstr={v for v in leaves(public_input)if isinstance(v,str)};hidden=sorted({v for v in leaves(private_input)if isinstance(v,str)and len(v)>=16 and v not in pubstr});pubbytes=b'\n'.join(p.read_bytes()for p in sorted((ROOT/f'T{t}/public').rglob('*'))if p.is_file());leaks=[v for v in hidden if v.encode()in pubbytes]
 for phase in ['public','private']:
  p=ROOT/f'T{t}'/phase;old=OLD/f'T{t}'/phase;family=f'T{t}/{phase}';fe=[]
  for name in byte_invariants:
   if (p/name).read_bytes()!=(old/name).read_bytes():fe.append('byte invariant changed:'+name)
  for name in ['reference.json','outcomes.json','denominator.json','actions.ios.json','actions.android.json','target-observations.json','routes.json']:
   if load(p/name)!=norm(load(old/name)):fe.append('normalized invariant changed:'+name)
  den=load(p/'denominator.json');cells=den['cells'];master_total+=den['total_cells'];ref=load(p/'reference.json');oldrules={r['id']:r for r in load(old/'contract.json')['rules']};counts=collections.Counter(x['platforms'][pl]['disposition']for x in cells for pl in ['ios','android'])
  expected={(r,s,pl)for r in den['complete_rule_ids']for s in den['complete_state_ids']for pl in ['ios','android']};actual={(x['requirement'],x['state'],pl)for x in cells for pl in x['platforms']}
  if expected!=actual or den['total_cells']!=len(actual)or len(cells)*2!=len(actual):fe.append('master Cartesian denominator mismatch')
  for pl in ['ios','android']:
   f=load(p/f'fixtures.{pl}.json');schema=load(p/'fixture.schema.json');jsonschema.Draft202012Validator.check_schema(schema);validator=jsonschema.Draft202012Validator(schema)
   for i,value in enumerate([f['initial']]+f['updates']):
    fixture_count+=1
    for e in validator.iter_errors(value):fe.append('fixture schema:'+pl+'/'+str(i)+':'+e.message)
  if phase=='public'and leaks:fe.append('hidden text leak')
  approval=load(p/'PROFILE-APPROVAL.json')
  if d.digest(den)!=approval['master_denominator_sha256']:fe.append('master denominator digest mismatch')
  for pl in ['ios','android']:
   src=p/pl;dst=OUT/family/pl;pe=[];contract=load(src/'contract.json');lock=load(src/'lock.json');plan=load(dst/'generated/plan.json');policy=load(src/'policy.json');cat=load(dst/'catalog.json');routes=load(dst/'route-audit.json');execution=load(dst/'execution/execution.json');projection=load(src/'projection-map.json');seal=load(src/'seal.json');s=next(iter(contract['scenarios'].values()));ids={a['id']for a in plan['assertions']};rows={a['id']:a for a in plan['assertions']};assess={f'{x["state"]}/{x["requirement"]}':x['platforms'][pl]for x in cells if x['platforms'][pl]['disposition']=='assess'};compiled_total+=len(rows)
   if ids!=set(assess)or len(ids)!=len(plan['assertions']):pe.append('assessed denominator projected IDs lost/added/duplicated')
   for aid,value in assess.items():
    a=rows.get(aid,{})
    ev=value['expected'];ev=int(ev[1:],16)if value['unit']=='argb'else ev
    if any(a.get(k)!=v for k,v in [('expected',ev),('unit',value['unit']),('op',value['operator'])] if k!='op')or a.get('op','eq')!=value['operator']:pe.append('projected numeric/operator mismatch:'+aid)
    proof=a.get('expectation_provenance',[])
    if not proof or proof[0]['pointer']!=value['pointer']:pe.append('projected source provenance mismatch:'+aid)
   expected_rules={x['requirement']for x in cells if x['platforms'][pl]['disposition']=='assess'}
   if {r['id']for r in contract['rules']}!=expected_rules:pe.append('rule universe differs from actual applicable master rules')
   for rule in contract['rules']:
    if rule!=oldrules[rule['id']]:pe.append('primitive rule changed:'+rule['id'])
   original_states=norm(next(iter(load(old/'contract.json')['scenarios'].values()))['states'])
   if plan['states']!=original_states:pe.append('selected state/coverage changed')
   # Source documents in each lock must be independently partition-local exact bytes.
   for ss in contract['sources']:
    q=(src/ss['path']).resolve();sealed=lock['sources'][ss['id']]
    if not q.is_relative_to(src.resolve())or hashlib.sha256(q.read_bytes()).hexdigest()!=ss['sha256']or sealed['raw_utf8']!=q.read_text()or sealed['document']!=load(q):pe.append('lock source partition/raw mismatch')
   nsref=load(src/'reference.json')
   for k in ['business_rules','tokens','scope','states','questions','visual','capture_validity']:
    if nsref[k]!=ref[k]:pe.append('namespace source content changed:'+k)
   if routes['must_route_gaps']or routes['unowned_assertions']:pe.append('route gaps or unowned assertions')
   if any(r['kind']=='text_layout'for r in plan['assertions'])and pl=='ios':pe.append('unsupported iOS native computed style')
   if pl=='android':
    for state in plan['states']:
     for rid in ['heading-native-size','heading-native-weight','body-native-size','body-native-ink']:
      if state['id']+'/'+rid not in ids:pe.append('Android native typography dropped')
   if len(execution['actions'])>25 or action_guard.compile_actions(execution['actions'])!=execution['actions']:pe.append('action budget/guards mismatch')
   observation_contract.validate_actions(execution['actions'])
   # Absence can only be acquired under actual full-content execution; absence selectors are never required presences.
   promotions=[]
   for st in plan['states']:
    req=next(x for x in execution['required_coverage']if x['state_id']==st['id'])
    false_selectors=[r['target']for r in rows.values()if r['state']==st['id']and r['kind']=='control'and r.get('property')=='present'and r.get('expected')is False]
    if false_selectors:
     if req['coverage']!='full_content'or any(x in req['targets']for x in false_selectors):pe.append('impossible absent-target acquisition')
     if st['coverage']!='full_content':promotions.append(st['id'])
    for aid,a in rows.items():
     if a['state']!=st['id']or a['kind']!='event':continue
     ai=a['action_index'];typ=execution['actions'][ai]['type']
     if typ not in ['tap','apply_next_fixture']:pe.append('event assertion not bound to business stimulus')
   # Every manual row retains primitive identity and exact question/sampling; coarse enum is metadata only.
   oldpolicy={a['rule_id']:a for a in load(old/'policy.json')['atoms']};catids={r['id']for r in cat['rows']};manualids={r['id']for r in rows.values()if r['kind']=='manual'}
   if catids!=manualids:pe.append('catalog manual row loss')
   for atom in policy['atoms']:
    oa=oldpolicy[atom['rule_id']]
    if any(atom.get(k)!=oa.get(k)for k in ['rule_id','method','question','sampling']):pe.append('question or sampling changed:'+atom['rule_id'])
   if projection['complete_original_platform_cell_count']!=len(cells)or len(projection['cells'])!=len(cells):pe.append('projection map incomplete')
   projkeys={(r['state'],r['requirement'])for r in projection['cells']}
   if projkeys!={(r['state'],r['requirement'])for r in cells}:pe.append('projection map Cartesian identity mismatch')
   entry=approval['profiles'][pl]
   if entry['platform']!=pl or entry['design_sha256']!=d.digest(lock)or entry['hashes']['plan']!=d.digest(plan)or d.digest(projection)!=seal['projection_map_sha256']:pe.append('approval map hash mismatch')
   profiles.append({'family':family,'platform':pl,'assertions':len(rows),'native_style_rows':sum(a['kind']=='text_layout'for a in rows.values()),'manual_rows':len(cat['rows']),'actions':len(execution['actions']),'last_action_index':len(execution['actions'])-1,'absence_full_sweep_promotions':promotions,'errors':pe})
   errors.extend({'family':family,'platform':pl,'error':x}for x in pe)
  families.append({'family':family,'master_cells':den['total_cells'],'assess':counts['assess'],'NA':counts['not_applicable'],'hidden_unique_strings_checked':len(hidden),'errors':fe});errors.extend({'family':family,'error':x}for x in fe)
# Include exact original and frozen dependency read identities in the new readset without modifying the original review.
rs=load(OUT/'READSET.json');seen={e['path']for e in rs}
extra=[p for p in OLD.rglob('*')if p.is_file()]+[TOOL/n for n in ['design_contract.py','observation_contract.py','native_checks.py','review_contract.py','native_pixels.py','execution_plan.py','requirement_routes.py','action_guard.py','ios_observe.py']]+[BASE/'candidate-v13.9/assets/ios-observer/ObserverTests.swift',BASE/'candidate-v13.9/assets/android-observer/NativeObserverTest.kt']
extra += [Path(m.__file__)for m in list(sys.modules.values())if getattr(m,'__file__',None)and Path(m.__file__).is_relative_to(DEP)]
for p in extra:
 if str(p)not in seen:
  b=p.read_bytes();rs.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'operation':'normative-equivalence-or-pure-generator/schema-dependency-read'});seen.add(str(p))
dump(OUT/'READSET.json',rs)
result={'status':'PASS'if not errors else'FAIL','standard_schema_validator':'jsonschema4.23.0 Draft202012Validator (private pure-only dependency path)','fixture_payloads_validated':fixture_count,'master_denominator_cells':master_total,'compiled_assessed_assertions':compiled_total,'families':families,'profiles':profiles,'errors':errors,'scope':'Pure design-format/atomic-projection/normative-equivalence validation only; no source implementation or SDK/native rendering/coverage approval.'};dump(OUT/'equivalence-schema-projection-audit.json',result)
print(json.dumps({k:v for k,v in result.items()if k not in ['families','profiles','scope']},indent=2))
