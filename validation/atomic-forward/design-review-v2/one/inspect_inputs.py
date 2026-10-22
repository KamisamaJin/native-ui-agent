from pathlib import Path
import json,hashlib,sys
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
BASE=ROOT/'validation/atomic-forward'
OUT=BASE/'design-review-v2/one'
HASHES={}
def raw(p):
 b=p.read_bytes(); HASHES[str(p.relative_to(ROOT))]=hashlib.sha256(b).hexdigest(); return b
def obj(p): return json.loads(raw(p))
def digest(o): return hashlib.sha256(json.dumps(o,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def check(test,msg):
 if not test: raise AssertionError(msg)
freeze=obj(BASE/'candidate-v8-freeze.json')
for n,h in freeze['files'].items(): check(hashlib.sha256(raw(BASE/'candidate-v8'/n)).hexdigest()==h,'frozen '+n)
check(len(freeze['files'])==54,'54 freeze files')
raw(BASE/'DESIGN-INTERFACE.md'); raw(BASE/'design-v2/DELIVERY.md')
cohort=obj(BASE/'design-v2/seal.json')
# Read only allowed design inputs, not other cohort members or revision records.
for t in ['T1','T2','T3']:
 for sub in ['public','private']:
  for p in (BASE/'design-v2'/t/sub).rglob('*'):
   if p.is_file(): raw(p)
 for sub,cases in [('public',['P1','P2']),('private',['H1'])]:
  p=BASE/'design-v2'/t/sub
  ref=obj(p/'reference.json'); co=obj(p/'contract.json'); lock=obj(p/'design-lock.json'); policy=obj(p/'policy.json'); approval=obj(p/'approval.json'); bindings=obj(p/'bindings.json')
  check(lock['contract']==co,t+' contract embedded lock')
  check(lock['contract_sha256']==digest(co),t+' contract digest')
  check(digest(lock)==approval['design_lock_sha256']==policy['design_lock_sha256'],t+' approval lock')
  check(digest(policy)==approval['policy_sha256'],t+' policy digest')
  check(co['sources'][0]['sha256']==hashlib.sha256(raw(p/'reference.json')).hexdigest(),t+' source bytes')
  check(lock['sources']['reference']['document']==ref,t+' locked source')
  check(lock['sources']['reference']['raw_utf8']==(p/'reference.json').read_text(),t+' locked utf8')
  pub=obj(BASE/'design-v2'/t/'public/contract.json')
  check(co['rules']==pub['rules'],t+' hidden rule identities')
  for c in cases:
   sc=co['scenarios'][c]; f=obj(p/'cases'/c/'fixtures.json'); acts=obj(p/'cases'/c/'actions.ios.json'); amap=obj(p/'cases'/c/'checkpoint-map.json')
   check(sc['states']==amap['states'],t+c+' checkpoint map')
   logical=[]
   for a in sc['actions']:
    a=dict(a)
    if isinstance(a.get('target'),str): a['target']=bindings[a['target']]
    logical.append(a)
   check(logical==acts,t+c+' original route')
   check(len(acts)<40 and len(sc['states'])==7,t+c+' manageable state/actions')
   models=[f['initial']]+f['updates']; k=next(k for k in ['slots','incidents','services'] if k in models[0]); multi=t=='T3'; prefix={'T1':'workshop','T2':'river','T3':'bicycle'}[t]
   selected=set(); expanded=False; model=None; index=0; event=[]
   for ai,a in enumerate(acts):
    event=[]
    if model is None or a['type']=='apply_next_fixture':
     if model is not None: index+=1
     model=models[index]; items={x['id']:x for x in model[k]}; ids=model.get('initialSelectedIDs',[model.get('initialSelectedID')]); selected={i for i in ids if i in items and items[i]['available']}; expanded=model['initialDetailsExpanded']
    for item in model[k]: check((item['unavailableReason']=='')==item['available'],t+c+' reason invariant')
    if a['type']=='tap':
     target=a['target']['identifier'].split('.')[-1]
     if target in items and items[target]['available']:
      if multi:
       selected.symmetric_difference_update({target}); event=[f'{prefix}:toggle:{target}:{str(target in selected).lower()}']
      else: selected={target}; event=[f'{prefix}:select:{target}']
     elif target=='disclosure':
      expanded=not expanded; event=[f'{prefix}:details:{"open" if expanded else "closed"}']
     elif target=='submit' and selected:
      event=[f'{prefix}:{"submit" if multi else ("reserve" if t=="T1" else "acknowledge")}:{",".join(sorted(selected))}']
    for state in sc['states']:
     if state['after_action']!=ai: continue
     name=state['id']; expected=ref['cases'][c]['states'][name]
     labels=[x['label'] for x in model[k] if x['id'] in selected]
     summary=(f'Work: {" + ".join(labels)} · {sum(x["minutes"] for x in model[k] if x["id"] in selected)} min' if labels else 'No work selected · 0 min') if multi else (({'T1':'Draft station: ','T2':'Reviewing: '}[t]+labels[0]) if labels else {'T1':'No station selected','T2':'No alert selected'}[t])
     expected_facts={'summary':summary,'selectedA':'a' in selected,'submitEnabled':bool(selected),'disclosure':('Hide ' if expanded else 'Show ')+{'T1':'safety briefing','T2':'reading dossier','T3':'handover notes'}[t]}
     for key,value in expected_facts.items(): check(expected[key]['value']==value,t+c+name+' '+key)
     stimulus=sc['states'][[s['id'] for s in sc['states']].index(name)].get('stimulus_action',ai)
     if stimulus!=ai:
      sa=acts[stimulus]; target=sa['target']['identifier'].split('.')[-1]
      event=[f'{prefix}:details:open'] if target=='disclosure' else [f'{prefix}:{"submit" if multi else ("reserve" if t=="T1" else "acknowledge")}:{",".join(sorted(selected))}']
     check(expected['activationEvents']['value']==event,t+c+name+' callback source')
     check(expected['updateEvents']['value']==[],t+c+name+' quiet update')
     check(expected['primaryColor']==ref['cases'][c]['colors']['enabled' if selected else 'disabled'],t+c+name+' color source')
   for plat in ['ios','android']:
    check(obj(p/'cases'/c/f'actions.{plat}.json')==acts,t+c+' crossplatform route')
    env=obj(p/'cases'/c/f'environment.{plat}.json'); check(digest(env)==approval['environment_sha256'][c][plat],t+c+plat+' environment digest')
    check(env['width']==f['width'] and env['height']==600 and env['direction']==f['direction'] and env['theme']==f['theme'],t+c+plat+' fixture environment')
    check(env['dynamic_type']==f['dynamic_type'] if plat=='ios' else env['font_scale']==f['fontScale'] and env['dimension_encoding']=='paparazzi-float32-screen-config-v1',t+c+plat+' font/encoding')
    plan=obj(p/'compiled'/c/plat/'plan.json'); cells=plan['matrix_contract']['cells']; check(len(cells)==98 and sum(x['disposition']=='required' for x in cells)==81,t+c+plat+' ledger')
   meta=obj(p/f'reference-{c}-expanded.meta.json'); audit=obj(p/f'reference-{c}-text-fit-audit.json')
   for ext in ['png','svg']: check(meta[ext+'_sha256']==hashlib.sha256(raw(p/f'reference-{c}-expanded.{ext}')).hexdigest(),t+c+ext+' reference digest')
   check(meta['width_native']==f['width']-32,t+c+' reference offered width')
   check(all(x['x_min']>=12 and x['x_max']<=meta['width_native']-12 for x in audit['lines']),t+c+' source audit gutter')
  print(t,sub,'state/summary/callback/color derivations, source/lock/policy/environment integrity, route, 98/81/17 ledger: consistent')
# Restrict cohort verification to allowed files already hashed above.
checked=0
for n,h in cohort['files_sha256'].items():
 p=BASE/'design-v2'/n
 key=str(p.relative_to(ROOT))
 if key in HASHES:
  check(HASHES[key]==h,'cohort input '+n); checked+=1
print('frozen files',54,'allowed cohort members checked',checked)
(OUT/'input-hashes.json').write_text(json.dumps(HASHES,ensure_ascii=False,indent=2)+'\n')
(OUT/'inspection.json').write_text(json.dumps({'frozenFilesVerified':54,'allowedCohortMembersVerified':checked,'tasks':3,'cases':9,'casePlatforms':18,'sourceDerivation':'Independent fixture/action reduction against public rules; not a production implementation or native execution.','result':'consistent'},indent=2)+'\n')
