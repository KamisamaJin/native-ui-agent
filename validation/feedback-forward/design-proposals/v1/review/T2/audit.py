#!/usr/bin/env python3
"""SDK-free reconstruction of immutable T2 design; writes only this review folder."""
from pathlib import Path
import sys, os, json, hashlib, traceback, time, collections
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.dont_write_bytecode=True
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward')
OUT=BASE/'design-review/T2'
sys.path.insert(0,str(BASE/'candidate-v9/scripts'))
import design_contract as design
import requirement_routes, review_contract, execution_plan
from native_environment import validate_environment_contract

def read(p):return design.load(p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
result={'startedAtUnix':time.time(),'sdk_execution':False,'seals':{},'cases':[],'errors':[],'business_mismatches':[],'source_hashes':{}}
for root in [BASE/'design/T2',BASE/'candidate-v9']:
 for p in sorted(root.rglob('*')):
  if p.is_file():result['source_hashes'][str(p.relative_to(BASE))]=sha(p)
for scope in ['public','private']:
 d=BASE/'design/T2'/scope
 try:
  seal=read(d/'SEAL.json');missing=[];changed=[]
  for name,want in seal['files'].items():
   p=d/name
   if not p.is_file():missing.append(name)
   elif sha(p)!=want:changed.append(name)
  result['seals'][scope]={'listed_files':len(seal['files']),'missing':missing,'changed':changed,'unsealed_files':sorted(set(str(p.relative_to(d)) for p in d.rglob('*') if p.is_file())-set(seal['files'])-{'SEAL.json'})}
  lock=read(d/'design-lock.json'); approval=read(d/'approval.json'); locksha=approval['design_lock_sha256']
  design.validate_lock(lock,locksha)
  assert design.seal(d/'contract.json',d)==lock,'resealed lock differs'
  assert design.digest(read(d/'policy.json'))==approval['policy_sha256']
  assert design.digest(read(d/'routes.json'))==approval['routes_sha256']
  ref=read(d/'reference.json');bindings=read(d/'bindings.json');rules={r['id']:r for r in lock['contract']['rules']}
  for case in lock['contract']['scenarios']:
   fx=read(d/'cases'/case/'fixtures.json')
   for platform in ['ios','android']:
    current={'scope':scope,'case':case,'platform':platform}; result['cases'].append(current)
    try:
     actions=read(d/'cases'/case/('actions.'+platform+'.json'))
     plan,enriched=design.compile_contract(lock,locksha,case,platform,bindings,actions)
     assert design.verify_generated(plan,lock,locksha,platform)==enriched
     coverage=requirement_routes.audit(lock,locksha,plan,read(d/'routes.json'),approval['routes_sha256'])
     cat=review_contract.catalog(plan,lock,locksha,read(d/'policy.json'),approval['policy_sha256'],platform)
     cat=dict(cat,catalog_sha256=design.digest(cat))
     bridge=d/('Bridge.swift' if platform=='ios' else 'ObserverBridge.kt')
     execution=execution_plan.compile_execution(plan,lock,locksha,fx,sha(bridge),launch_ref={'source':'reference','pointer':'/launch/'+case+'/'+platform})
     assert execution_plan.verify_execution(execution,plan,lock,locksha,fx,sha(bridge))==execution
     env=read(d/'cases'/case/('environment.'+platform+'.json'))
     validate_environment_contract(env,approval['environment_sha256'][case][platform],platform)
     compare={'plan.json':plan,'actions.json':enriched,'coverage.json':coverage,'review-catalog.json':cat,'execution.json':execution,'execution-inputs/actions.json':execution['actions'],'execution-inputs/fixtures.json':execution['config']}
     current['frozen_artifacts_equal']={name:value==read(d/'compiled'/case/platform/name) for name,value in compare.items()}
     current['canonical_hashes']={name:design.digest(value) for name,value in compare.items()}
     current['assertions']=len(plan['assertions']);current['matrix_cells']=len(plan['matrix_contract']['cells'])
     current['not_applicable']=sum(x['disposition']=='not_applicable' for x in plan['matrix_contract']['cells'])
     current['must_route_gaps']=coverage['must_route_gaps'];current['unowned_assertions']=coverage['unowned_assertions']
     current['manual_atoms']=len(cat['rows']);current['source_provenance_complete']=all(bool(x.get('expectation_provenance')) for x in plan['assertions'])
     current['event_checks']=[{k:x[k] for k in ['id','action_index','stimulus','required_method','expected'] if k in x} for x in plan['assertions'] if x['kind']=='event']
     current['states']=plan['states'];current['environment_validated']=True
     # Business expectation derivation is from BRIEF, independent of reference truth constants.
     wifi=True;expanded=False;requested=False;input_index=0;tour=fx['initial']
     by_action={s['after_action']:s for s in plan['states']}
     for ai,action in enumerate(actions):
      if action['type']=='tap':
       target=action['target']['identifier']
       if target=='audio.disclosure':expanded=not expanded
       elif target=='audio.choice':
        assert not requested;wifi=not wifi
       elif target=='audio.primary':
        assert tour['availableMB']>=tour['downloadSizeMB'] and not(tour['meteredConnection'] and wifi) and not requested
        requested=True
      elif action['type']=='apply_next_fixture':
       input_index+=1;tour=fx['updates'][input_index-1];wifi=True;expanded=False;requested=False
      if ai not in by_action:continue
      state=by_action[ai]['id']
      status='Storage needed' if tour['availableMB']<tour['downloadSizeMB'] else 'Download requested' if requested else 'Wi-Fi required' if tour['meteredConnection'] and wifi else 'Ready to download'
      expected={'title-label':tour['title'],'subtitle-label':tour['language']+' · '+str(tour['downloadSizeMB'])+' MB','status-label':status,'disclosure-label':'Hide chapters' if expanded else 'Review chapters','choice-label':'Wi-Fi only','choice-selected':wifi,'choice-enabled':not requested,'primary-label':'Requested' if requested else 'Get audio','primary-enabled':tour['availableMB']>=tour['downloadSizeMB'] and not(tour['meteredConnection'] and wifi) and not requested}
      for i,chapter in enumerate(tour['chapters']):
       if expanded:expected.update({'section-'+str(i)+'-heading':chapter['title'],'section-'+str(i)+'-body':chapter['body']})
      for rule,value in expected.items():
       a=next(x for x in plan['assertions'] if x['id']==state+'/'+rule)
       if a['expected']!=value:result['business_mismatches'].append({'scope':scope,'case':case,'platform':platform,'assertion':a['id'],'derived':value,'frozen':a['expected']})
     current['passed']=all(current['frozen_artifacts_equal'].values()) and not coverage['must_route_gaps'] and not coverage['unowned_assertions']
    except Exception as e:
     current['error']=str(e);current['traceback']=traceback.format_exc();result['errors'].append(current)
 except Exception as e:
  result['errors'].append({'scope':scope,'error':str(e),'traceback':traceback.format_exc()})
result['finishedAtUnix']=time.time();write(OUT/'mechanical-checks.json',result)
print(json.dumps({'seals':result['seals'],'cases':result['cases'],'errors':result['errors'],'business_mismatches':result['business_mismatches']},indent=2))
