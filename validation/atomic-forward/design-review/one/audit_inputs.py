from pathlib import Path
import json,hashlib,copy
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill');BASE=ROOT/'validation/atomic-forward';D=BASE/'design-v1';OUT=BASE/'design-review/one';inputs={};issues=[];summary=[]
def raw(p):
 b=p.read_bytes();inputs[str(p.relative_to(ROOT))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def canon(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def dg(x):return hashlib.sha256(canon(x)).hexdigest()
def ck(ok,msg):
 if not ok:issues.append(msg)
def pointer(x,p):
 for q in p.strip('/').split('/'):x=x[q.replace('~1','/').replace('~0','~')]
 return x
frozen=read(BASE/'candidate-v8-freeze.json')
for name,hash_ in frozen['files'].items():ck(hashlib.sha256(raw(BASE/'candidate-v8'/name)).hexdigest()==hash_,'frozen mismatch '+name)
gate=read(BASE/'gates/tools.json');raw(BASE/'DESIGN-INTERFACE.md')
for name in ['assets/ios-observer/CONTRACT.md','scripts/design_contract.py','scripts/native_checks.py','scripts/native_pixels.py','scripts/review_contract.py','scripts/native_environment.py','scripts/observation_contract.py']:
 p=BASE/'candidate-v8'/name;ck(inputs[str(p.relative_to(ROOT))]==gate['members']['candidate-v8']['candidate-v8/'+name],'gate mismatch '+name)
for t,prefix,key,pre,submit in [('T1','workshop','slots','Draft station: ','reserve'),('T2','river','incidents','Reviewing: ','acknowledge'),('T3','bicycle','services','Work: ','submit')]:
 pub=read(D/t/'public/contract.json');pubpolicy=read(D/t/'public/policy.json')
 for scope,cases in [('public',['P1','P2']),('private',['H1'])]:
  p=D/t/scope;c=read(p/'contract.json');ref=read(p/'reference.json');lock=read(p/'design-lock.json');pol=read(p/'policy.json');approval=read(p/'approval.json');bind=read(p/'bindings.json')
  ck(c==lock['contract'],t+scope+' lock contract mismatch');ck(dg(c)==lock['contract_sha256'],t+scope+' canonical contract mismatch');ck(dg(lock)==approval['design_lock_sha256']==pol['design_lock_sha256'],t+scope+' lock approval mismatch');ck(dg(pol)==approval['policy_sha256'],t+scope+' policy approval mismatch')
  ck(c['rules']==pub['rules'] and c['required_rule_ids']==pub['required_rule_ids'],t+scope+' hidden rule drift');ck(pol['atoms']==pubpolicy['atoms'] and pol['ownership']==pubpolicy['ownership'],t+scope+' hidden policy drift')
  for src in c['sources']:
   ck(hashlib.sha256(raw(p/src['path'])).hexdigest()==src['sha256'],t+scope+' source hash');ck(lock['sources'][src['id']]['document']==ref and lock['sources'][src['id']]['raw_utf8']==(p/src['path']).read_text(),t+scope+' sealed source differs')
  for name in (['BRIEF.md','API.md','Bridge.swift','ObserverBridge.kt'] if scope=='public' else ['HELDOUT.md']):raw(p/name)
  for case in cases:
   sc=c['scenarios'][case];fx=read(p/'cases'/case/'fixtures.json');ck(fx==read(p/'compiled'/case/'fixtures.json'),t+case+' copied fixture')
   meta=read(p/f'reference-{case}-expanded.meta.json');ck(hashlib.sha256(raw(p/f'reference-{case}-expanded.svg')).hexdigest()==meta['svg_sha256'],t+case+' SVG hash');ck(hashlib.sha256(raw(p/f'reference-{case}-expanded.png')).hexdigest()==meta['png_sha256'],t+case+' PNG hash');ck(meta['width_native']==fx['width']-32,t+case+' reference width')
   items=fx['initial'][key];model=fx['initial'];sel=set(model.get('initialSelectedIDs',[]) if t=='T3' else ([model['initialSelectedID']] if model['initialSelectedID'] else []));opened=model['initialDetailsExpanded'];state_expected={};events={}
   for ai,a in enumerate(sc['actions']):
    if a['type']=='tap':
     target=a['target'];ev=[]
     if target in ['choiceA','choiceB','locked']:
      id_={'choiceA':'a','choiceB':'b','locked':'c'}[target];item=next(x for x in items if x['id']==id_)
      if item['available']:
       if t=='T3':
        if id_ in sel:sel.remove(id_)
        else:sel.add(id_)
        ev=[f'{prefix}:toggle:{id_}:{str(id_ in sel).lower()}']
       else:sel={id_};ev=[f'{prefix}:select:{id_}']
     elif target=='disclosure':opened=not opened;ev=[f'{prefix}:details:{"open" if opened else "closed"}']
     elif target=='submit':ev=[f'{prefix}:{submit}:{",".join(sorted(sel))}'] if sel else []
     events[ai]=ev
    elif a['type']=='apply_next_fixture':
     model=fx['updates'][0];items=model[key];valid={x['id'] for x in items if x['available']};sel=set(model.get('initialSelectedIDs',[]) if t=='T3' else ([model['initialSelectedID']] if model['initialSelectedID'] else []))&valid;opened=model['initialDetailsExpanded'];events[ai]=[]
    for st in sc['states']:
     if st['after_action']!=ai:continue
     vals=ref['cases'][case]['states'][st['id']];labels=[x['label'] for x in items if x['id'] in sel]
     summary_text=(pre+' + '.join(labels)+' · '+str(sum(x['minutes'] for x in items if x['id'] in sel))+' min' if labels else 'No work selected · 0 min') if t=='T3' else (pre+labels[0] if labels else ('No station selected' if t=='T1' else 'No alert selected'))
     ck(vals['summary']['value']==summary_text and vals['selectedA']['value']==('a'in sel) and vals['submitEnabled']['value']==bool(sel),t+case+st['id']+' current state semantics')
     eventcell=sc['values']['successful-activation-callback'][st['id']]
     if 'not_applicable'not in eventcell:ck(vals['activationEvents']['value']==events[st.get('stimulus_action',ai)],t+case+st['id']+' callback semantics')
   for platform in ['ios','android']:
    env=read(p/'cases'/case/f'environment.{platform}.json');ck(dg(env)==approval['environment_sha256'][case][platform],t+case+platform+' environment hash');ck(env==read(p/'compiled'/case/f'environment.{platform}.json'),t+case+' environment copy')
    actions=read(p/'cases'/case/f'actions.{platform}.json');base=copy.deepcopy(sc['actions'])
    for a in base:
     if 'target'in a:a['target']=bind[a['target']]
    ck(actions==base,t+case+platform+' original native route')
    plan=read(p/'compiled'/case/platform/'plan.json');acts=read(p/'compiled'/case/platform/'actions.json');ck(plan['states']==sc['states'],t+case+platform+' state indices')
    for a in plan['assertions']:
     cell=sc['values'][a['requirement_id']][a['state']];datum=pointer(ref,cell[platform]['pointer']);value=int(datum['value'][1:],16) if datum['unit']=='argb' else datum['value'];ck(a['expected']==value and a['unit']==datum['unit'],t+case+a['id']+' compiled expected')
     if a['kind']=='event':
      st=next(s for s in sc['states'] if s['id']==a['state']);ck(a['action_index']==st.get('stimulus_action',st['after_action']),t+case+a['id']+' callback index')
    for st in sc['states']:
     idx=st['after_action'];ck(acts[idx]['state_id']==st['id'],t+case+platform+' state id')
     if st['coverage']=='targets':
      targets=[]
      for a in plan['assertions']:
       if a['state']==st['id'] and 'target'in a and a['target']not in targets:targets.append(a['target'])
      ck(acts[idx]['after_targets']==targets,t+case+platform+' after-target index map')
    summary.append({'task':t,'scope':scope,'case':case,'platform':platform,'ledgerCells':len(plan['matrix_contract']['cells']),'requiredCells':len(plan['assertions']),'selectedNativeStyleUnavailableIOS':7 if platform=='ios'else 0,'actions':len(actions),'stateSemanticChecks':'match'})
(OUT/'verification-audit.json').write_text(json.dumps({'sdkInvoked':False,'frozenFilesVerified':len(frozen['files']),'issues':issues,'cases':summary},indent=2)+'\n')
(OUT/'input-hashes.json').write_text(json.dumps(inputs,sort_keys=True,indent=2)+'\n')
print(json.dumps({'structuralIssues':issues,'casePlatformCount':len(summary),'inputFileCount':len(inputs)}))
