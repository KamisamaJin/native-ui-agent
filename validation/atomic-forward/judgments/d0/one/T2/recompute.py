import json,pathlib,sys,hashlib
sys.dont_write_bytecode=True
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/d0/one/T2'
sys.path.insert(0,str(B/'candidate-v8/scripts'))
import review_contract,native_checks
load=lambda p:json.loads(p.read_text())
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
lock=load(B/'design-v2/T2/public/design-lock.json');policy=load(B/'design-v2/T2/public/policy.json')
summary={}
for case in sorted((B/'evaluation-inputs/d0/T2').glob('*/*/*')):
 key=str(case.relative_to(B/'evaluation-inputs/d0/T2'));inputs=load(case/'inputs.json');plan=load(case/'plan.json');cat=load(case/'catalog.json');root=B/inputs['root'];obs=load(B/inputs['observation']);platform=inputs['platform'];d=O/key
 blank={'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':inputs['observation_sha256'],'decisions':[]}
 bound=review_contract.bind(plan,lock,inputs['approval']['design_lock_sha256'],policy,inputs['approval']['policy_sha256'],obs,inputs['observation_sha256'],root,blank,platform)
 save(d/'recomputed-pixels.json',bound)
 report=native_checks.evaluate(plan,obs,platform,bound,root,inputs['observation_sha256'],lock,inputs['approval']['design_lock_sha256'],policy,inputs['approval']['policy_sha256'])
 save(d/'recomputed-native.json',report)
 audit={}
 for st in plan['states']:
  found,complete,why,capture=native_checks.bound_state_evidence(obs,st)
  frames=[]
  for i,s in found:
   targets={}
   for ident in ['river.canvas','river.title','river.notice','river.disclosure','river.choice.a','river.choice.b','river.choice.c','river.choice.d','river.choice.e','river.choice.f','river.summary','river.submit','river.footer']:
    resolution=native_checks.resolve(s,{'identifier':ident},platform);node=resolution.get('semantic',{})
    targets[ident]={'facts':resolution.get('facts'),**{k:v for k,v in node.items() if k in ['label','native_text','enabled','selected','frame','bounds_dp','unclipped_bounds_dp','native_geometry','image_frame','image_bounds_px','fully_visible','fully_within_viewport','intersects_viewport']}}
   frames.append({'index':i,'targets':targets})
  audit[st['id']]={'binding':capture.get('binding') if capture else None,'complete':complete,'reason':why,'frames':frames}
 save(d/'state-target-audit.json',audit)
 steps=[]
 for i,s in enumerate(obs['steps']):
  steps.append({'index':i,**{k:v for k,v in s.items() if k not in ['observation_set','reveal','reveal_diagnostics','before_controls','after_controls']}})
 save(d/'action-audit.json',steps)
 fails=[r for r in report['assertions'] if r['status']=='failed'];summary[key]={'counts':report['counts'],'failures':fails}
 for f in fails:print(key,f['id'],f['snapshot_indices'])
 print(key,report['counts'])
save(O/'recomputed-summary.json',summary)
