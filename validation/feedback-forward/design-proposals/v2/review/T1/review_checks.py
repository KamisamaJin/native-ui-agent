#!/usr/bin/env python3
"""SDK-free review reconstruction. No source/design mutation; synthetic controls are not product evidence."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, os, subprocess, sys, time, traceback
ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
OUT=ROOT/'validation/feedback-forward/design-review/T1'
DESIGN=ROOT/'validation/feedback-forward/design/T1/public'
FROZEN=ROOT/'validation/feedback-forward/candidate-v9'
SCRIPTS=FROZEN/'scripts'
sys.dont_write_bytecode=True
sys.path.insert(0,str(SCRIPTS))
import design_contract as d, execution_plan as ep, requirement_routes as rr, review_contract as rc, native_checks as nc, observation_contract as oc
spec=importlib.util.spec_from_file_location('review_shared_implementation_audit', ROOT/'tools/implementation_audit.py')
sa=importlib.util.module_from_spec(spec);spec.loader.exec_module(sa)
assert sa.d is d, 'Source-only audit must use the frozen compiler module for this scoped reconstruction'

def save(path,value):
 path=OUT/path;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
LOG=OUT/'command-log.jsonl'

def command(argv):
 start=time.time();r=subprocess.run([str(x) for x in argv],cwd=ROOT,text=True,capture_output=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 row={'startedAtUnix':start,'finishedAtUnix':time.time(),'argv':[str(x) for x in argv],'cwd':str(ROOT),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'sdk_invoked':False}
 with LOG.open('a')as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
 return row

approval=d.load(DESIGN/'approval.json'); lock=d.load(DESIGN/'design-lock.json'); reference=d.load(DESIGN/'reference.json'); policy=d.load(DESIGN/'policy.json'); routes=d.load(DESIGN/'routes.json')
ls=approval['design_lock_sha256'];ps=approval['policy_sha256'];rs=approval['routes_sha256'];sas=approval['implementation_audit_sha256']
summary={'startedAtUnix':time.time(),'sdk_invoked':False,'commands':[],'cases':{},'checks':{},'api_controls':{},'operator_errors':[]}
# Record exact permitted source identity; no other study/product/native files opened.
hashes={}
for root in [DESIGN,FROZEN]:
 for p in sorted(root.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':hashes[str(p.relative_to(ROOT))]=sha(p)
for rel in ['validation/feedback-forward/design-proposals/v1/design/T1/public/BRIEF.md','validation/feedback-forward/design-proposals/v1/design/T1/public/API.md','tools/implementation_audit.py','validation/feedback-forward/SOURCE-AUDIT.md','validation/feedback-forward/PREIMPLEMENTATION-AMENDMENT.md','validation/feedback-forward/operators/T1-design-review-request.txt']:
 hashes[rel]=sha(ROOT/rel)
save(Path('source-hashes.json'),{'hash_type':'exact_file_bytes_SHA256','files':hashes})
# Full exact source/lock integrity and approved digest reconstruction.
r=command([sys.executable,SCRIPTS/'design_contract.py','seal','--contract',DESIGN/'contract.json','--root',DESIGN,'--output',OUT/'mechanical/resealed-lock.json']);summary['commands'].append({'operation':'seal','exit_code':r['exit_code']})
if not r['exit_code']:
 resealed=d.load(OUT/'mechanical/resealed-lock.json');summary['checks']['lock_resealed_exactly']=resealed==lock;summary['checks']['lock_canonical_digest']=d.digest(resealed)
summary['checks']['approved_canonical_digests']={'lock':d.digest(lock)==ls,'policy':d.digest(policy)==ps,'routes':d.digest(routes)==rs,'source_audit_policy':d.digest(d.load(DESIGN/'implementation-audit.json'))==sas}
seal=d.load(DESIGN/'SEAL.json'); sf=seal.get('files',{})
summary['checks']['design_seal']={'file_count':len(sf),'missing_or_changed':[rel for rel,h in sf.items()if not (DESIGN/rel).is_file()or sha(DESIGN/rel)!=h]}
for case in ['P1','P2']:
 for platform in ['ios','android']:
  tag=f'{case}/{platform}'; dest=OUT/'mechanical'/case/platform
  bridge=DESIGN/('Bridge.swift'if platform=='ios'else'ObserverBridge.kt')
  result=command([sys.executable,SCRIPTS/'design_contract.py','compile','--lock',DESIGN/'design-lock.json','--lock-sha256',ls,'--scenario',case,'--platform',platform,'--bindings',DESIGN/'bindings.json','--actions',DESIGN/f'cases/{case}/actions.{platform}.json','--output',dest]);summary['commands'].append({'operation':tag+'/compile','exit_code':result['exit_code']})
  if result['exit_code']:continue
  for op,argv in [
   ('coverage',[sys.executable,SCRIPTS/'requirement_routes.py','audit','--plan',dest/'plan.json','--design-lock',DESIGN/'design-lock.json','--design-sha256',ls,'--routes',DESIGN/'routes.json','--routes-sha256',rs,'--output',dest/'coverage.json']),
   ('catalog',[sys.executable,SCRIPTS/'review_contract.py','catalog','--plan',dest/'plan.json','--design-lock',DESIGN/'design-lock.json','--design-sha256',ls,'--policy',DESIGN/'policy.json','--policy-sha256',ps,'--platform',platform,'--output',dest/'review-catalog.json']),
   ('execution',[sys.executable,SCRIPTS/'execution_plan.py','--plan',dest/'plan.json','--design-lock',DESIGN/'design-lock.json','--design-sha256',ls,'--fixtures',DESIGN/f'cases/{case}/fixtures.json','--bridge',bridge,'--launch-source','reference','--launch-pointer',f'/launch/{case}/{platform}','--output',dest/'execution-inputs'])]:
   result=command(argv);summary['commands'].append({'operation':tag+'/'+op,'exit_code':result['exit_code']})
  plan=d.load(dest/'plan.json');coverage=d.load(dest/'coverage.json');cat=d.load(dest/'review-catalog.json');exe=d.load(dest/'execution-inputs/execution.json')
  ep.verify_execution(exe,plan,lock,ls,d.load(DESIGN/f'cases/{case}/fixtures.json'),sha(bridge))
  old=DESIGN/'compiled'/case/platform
  comparisons={name:d.load(dest/name)==d.load(old/name) for name in ['plan.json','actions.json','coverage.json','review-catalog.json']}
  comparisons['execution.json']=exe==d.load(old/'execution.json')
  summary['cases'][tag]={'assertions':len(plan['assertions']),'matrix_cells':len(plan['matrix_contract']['cells']),'catalog_rows':len(cat['rows']),'must_route_gaps':coverage['must_route_gaps'],'unowned_assertions':coverage['unowned_assertions'],'states':plan['states'],'action_count':len(exe['actions']),'maximum_after_targets':max(len(a.get('after_targets',[]))for a in exe['actions']),'full_content_states':[s['id']for s in plan['states']if s['coverage']=='full_content'],'reconstructed_equal_to_supplied':comparisons,'execution_verified':True,'events':[{'id':a['id'],'action_index':a['action_index'],'stimulus':a.get('stimulus','activation'),'expected':a['expected']}for a in plan['assertions']if a['kind']=='event']}
# Exact in-scope caller/launch pin checks, with internally recorded original value digests.
summary['checks']['caller_and_launch']={}
for case in ['P1','P2']:
 fixtures=d.load(DESIGN/f'cases/{case}/fixtures.json');ref=reference['cases'][case]
 summary['checks']['caller_and_launch'][case]={'caller_equals_case_fixture':ref['caller']==fixtures,'initial_matches_recorded_original_digest':d.digest(fixtures['initial'])==ref['original_initial_sha256'],'first_update_matches_recorded_original_digest':d.digest(fixtures['updates'][0])==ref['original_update_sha256'],'independent_v1_fixture_access':False,'limit':'Recorded v1 digests are within revised reference; raw v1 fixture/bridge access was not authorized. This checks internal preservation consistency, not independent original-byte comparison.'}
 for platform in ['ios','android']:
  env=d.load(DESIGN/f'cases/{case}/environment.{platform}.json');summary['checks']['caller_and_launch'][case][platform+'_environment_matches_approval']=d.digest(env)==approval['environment_sha256'][case][platform]
# Source-only definitions via the unmodified shared tool's actual API with frozen compiler already imported.
start=time.time();definitions=sa.catalog(lock,ls,d.load(DESIGN/'implementation-audit.json'),sas,OUT/'no-production-source',DESIGN,definition_only=True)
save(Path('mechanical/source-audit-definitions.json'),definitions)
with LOG.open('a')as f:f.write(json.dumps({'startedAtUnix':start,'finishedAtUnix':time.time(),'api':'tools/implementation_audit.py:catalog(...,definition_only=True)','compiler_module':str(Path(d.__file__).relative_to(ROOT)),'output':'mechanical/source-audit-definitions.json','sdk_invoked':False})+'\n')
summary['checks']['source_definitions']={'mode':definitions['mode'],'rows':len(definitions['rows']),'must':sum(r['priority']=='must'for r in definitions['rows']),'production_paths':{k:v for k,v in definitions['files'].items()if not k.startswith('@design/')},'bridge_paths':{k:v for k,v in definitions['files'].items()if k.startswith('@design/')},'source_acceptance_claimed':False,'dependency_note':'The shared tool normally prepends native-ui-agent/scripts. This scoped API invocation preloads the authorized frozen candidate-v9 design_contract module and verifies sa.d is d; tool source is unchanged.'}
try:sa.bind(definitions,{'version':1,'catalog_sha256':d.digest(definitions),'decisions':[]})
except Exception as e:summary['api_controls']['definition_only_bind_rejected']={'exception':type(e).__name__,'message':str(e)}
else:summary['api_controls']['definition_only_bind_rejected']=False
# Real source-bound catalog refuses missing code; no fake implementation is authored.
try:sa.catalog(lock,ls,d.load(DESIGN/'implementation-audit.json'),sas,OUT/'no-production-source',DESIGN)
except Exception as e:summary['api_controls']['missing_source_catalog_rejected']={'exception':type(e).__name__,'message':str(e)}
else:summary['api_controls']['missing_source_catalog_rejected']=False
# Schema/method controls. These deliberately synthetic facts validate generic gates only.
for platform in ['ios','android']:
 same={'instance':'synthetic-generic-only','pid':123,'fixture_index':0,'input_sha256':'a'*64,'event_revision':0}
 after=dict(same,event_revision=1)
 step={'outcome':'tapped','callback_delta':['synthetic:event'],'binding_after':after,'dispatch':{'attempted':True,'succeeded':True,'method':'xcui_tap'if platform=='ios'else'compose_onclick','stimulus':'activation','binding_before':same,'matches':1,'native_controls':1,'enabled':True,'event_start':0,'event_end':1}}
 summary['api_controls'][platform+'_synthetic_activation']=nc.callback_verdict(step,['synthetic:event'],platform)
 blocked={'outcome':'blocked_disabled','callback_delta':[],'binding_after':same,'dispatch':dict(step['dispatch'],attempted=False,succeeded=False,enabled=False,event_end=0)}
 summary['api_controls'][platform+'_synthetic_disabled']=nc.callback_verdict(blocked,[],platform)
 updated=dict(same,fixture_index=1,input_sha256='b'*64)
 upd={'outcome':'updated','callback_delta':[],'binding_after':updated,'dispatch':{'attempted':True,'succeeded':True,'method':'caller_fixture_update','stimulus':'caller_update','binding_before':same,'event_start':0,'event_end':0}}
 summary['api_controls'][platform+'_synthetic_update']=nc.callback_verdict(upd,[],platform,stimulus='caller_update')
 bad=dict(upd,dispatch=dict(upd['dispatch'],method='compose_onclick'))
 summary['api_controls'][platform+'_synthetic_wrong_update_method']=nc.callback_verdict(bad,[],platform,stimulus='caller_update')
summary['api_controls']['comparison_boundaries']={'gte_16_accepts_16':nc.compare(16,16,'gte'),'gte_16_rejects_15_999':not nc.compare(15.999,16,'gte'),'near_56_075_accepts_56_75':nc.compare(56.75,56,'near',.75),'near_56_075_rejects_56_751':not nc.compare(56.751,56,'near',.75)}
try:oc.validate_actions([{'type':'checkpoint'}]*41)
except Exception as e:summary['api_controls']['forty_action_bound']={'exception':type(e).__name__,'message':str(e)}
summary['finishedAtUnix']=time.time();save(Path('mechanical-summary.json'),summary)
print(json.dumps({'cases':{k:{a:v[a]for a in ['assertions','catalog_rows','must_route_gaps','action_count','execution_verified','reconstructed_equal_to_supplied']}for k,v in summary['cases'].items()},'checks':summary['checks'],'controls':summary['api_controls']},indent=2))
