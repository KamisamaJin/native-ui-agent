#!/usr/bin/env python3
"""SDK-free chronology, exact-source, original-image and independent-result replay."""
import json,sys
from pathlib import Path
import study as s
import evaluation,metrics,source_evaluation,shared_amendment
sys.path.insert(0,str(s.REPO/'tools'))
import implementation_audit as source_audit
import design_contract as d,execution_plan as xp,review_contract,native_checks,requirement_routes,acceptance
R=s.R

def source(capsule):
 seal=s.read(capsule/'seal.json');files={str(p.relative_to(capsule/'source')):s.sha(p)for p in (capsule/'source').rglob('*')if p.is_file()};assert files==seal['files']
 for name,target in s.read(R/'operators/source-view-compatibility/protocol.json')['mappings'].items():
  alias=capsule/'source'/name;assert alias.is_symlink()and alias.resolve()==(capsule/'source'/target).resolve()and alias.resolve().is_relative_to((capsule/'source').resolve())
 for rel,h in seal.get('upstreamLicenses',{}).items():assert s.sha(capsule/rel)==h
 return files

def logical(files):
 out={}
 for index,root in enumerate(s.ROOTS):
  for rel,h in files.items():
   path=Path(rel)
   if path.is_relative_to(root):out[str(index)+'/'+str(path.relative_to(root))]=h
 return out

def source_consensus(phase):
 """Execute the frozen merger with an in-memory sink, retaining every field."""
 emitted={};original_save=s.save
 def capture(path,value):
  path=Path(path);assert path not in emitted;emitted[path]=value
 try:
  s.save=capture;source_evaluation.merge(phase)
 finally:s.save=original_save
 assert emitted
 for path,value in emitted.items():assert s.read(path)==value,'Changed source consensus: '+str(path)

def case(raw,scope,name,pl,files):
 compiled=scope/'compiled'/name/pl;approval=s.read(scope/'approval.json');plan=s.read(compiled/'plan.json');lock=s.read(scope/'design-lock.json')
 value=s.read(raw/'execution.json')if(raw/'execution.json').is_file()else None
 if value is None:
  assert(raw/'wrapper-failure.json').is_file();return
 xp.verify_execution(value,plan,lock,approval['design_lock_sha256'],s.read(scope/'cases'/name/'fixtures.json'),s.sha(scope/('Bridge.swift'if pl=='ios'else'ObserverBridge.kt')))
 assert s.read(raw/'source-before.json')==logical(files)
 if(raw/'source-after.json').is_file():assert s.read(raw/'source-after.json')==logical(files)
 result=s.read(raw/'result.json')if(raw/'result.json').is_file()else None
 if result:
  if result.get('image_hashes'):xp.verify_capture_images(result,raw/'native')
  if result.get('observation_sha256'):assert s.sha(raw/'native/observation.json')==result['observation_sha256']
  if result.get('automatic_sha256'):assert s.sha(raw/'automatic.json')==result['automatic_sha256']
 if result and result['status']=='verified_capture':
  assert result['source_sha256']==d.digest(logical(files))and result['native_exit_code']==0 and result['source_unchanged']and result['inputs_unchanged']and result['coverage_satisfied']
  op=raw/'native/observation.json';assert s.sha(op)==result['observation_sha256'];xp.verify_capture_images(result,op.parent)
  assert s.sha(raw/'automatic.json')==result['automatic_sha256']
  assert xp.coverage_receipt(value,s.read(op))==s.read(raw/'execution-coverage.json')
  env=s.read(scope/'cases'/name/('environment.'+pl+'.json'));assert d.digest(env)==approval['environment_sha256'][name][pl]
  assert acceptance.environment(s.read(op),env,pl)==s.read(raw/'environment-check.json')


def main():
 s.tool_verify();shared_amendment.verify();s.gate.verify(R/'gates','reveal',R)
 for rel,h in s.read(R/'SOURCE-METRICS-METHODS.json')['files'].items():assert s.sha(R/rel)==h
 compat=s.read(R/'operators/source-view-compatibility/protocol.json');assert compat['operatorSHA256']==s.sha(R/'source_views.py')
 for path in (R/'operators/source-view-compatibility').glob('install-*.json'):
  value=s.read(path);assert value['source']==value['source_after']and value['source_unchanged']
 assignment=s.read(R/'private/assignment.json');assert s.sha(R/'private/assignment.json')==s.read(R/'operators/assignment-commitment.json')['assignmentSHA256']
 for tool in ['baseline-v8','candidate-v9']:
  freeze=s.read(R/(tool+'-freeze.json'));assert {str(p.relative_to(R/tool)):s.sha(p)for p in (R/tool).rglob('*')if p.is_file()and'__pycache__'not in p.parts}==freeze['files']
 live=R.parents[1]/'native-ui-agent';assert {str(p.relative_to(live)):s.sha(p)for p in live.rglob('*')if p.is_file()and'__pycache__'not in p.parts}==s.read(R/'candidate-v9-freeze.json')['files']
 for rel,h in s.read(R/'neutral/SEAL.json')['source_and_test_inputs_sha256'].items():assert s.sha(R/'neutral'/rel)==h
 for folder in ['pass1','pass2','pass3','pass4']:s.verify_dir(R/'neutral-review'/folder)
 stock=s.read(R/'operators/stock-production.json')['files'];runs=0
 for task in ['T1','T2']:
  initial=source(R/'submissions'/task/'d0');allowed=set(next(v for v in assignment['units'].values()if v['task']==task)['allowed_paths'])
  author=s.read(R/'submissions'/task/'initial-agent-output/implementation.json');assert author['startedAtUnix']>=s.read(R/'gates/design-review.json')['sealedAtUnix']
  assert s.read(R/'SOURCE-METRICS-METHODS.json')['frozenAtUnix']<author['startedAtUnix']
  assert {k for k in set(stock)|set(initial)if stock.get(k)!=initial.get(k)}<=allowed
  corpus=s.read(R/'corpora'/task/'d0/corpus.json');assert corpus['source']==initial and corpus['startedAtUnix']>=s.read(R/'gates/d0-sources.json')['sealedAtUnix']
  for pl in ['ios','android']:
   for name in ['P1','P2']:case(R/'corpora'/task/'d0'/pl/name,R/'design'/task/'public',name,pl,initial);runs+=1
 for unit,cfg in assignment['units'].items():
  initial=source(R/'submissions'/cfg['task']/'d0');final=source(R/'submissions'/unit/'final');assert {k for k in set(initial)|set(final)if initial.get(k)!=final.get(k)}<=set(cfg['allowed_paths'])
  s.verify_dir(R/'participant-completion'/unit)
  for name in ['claims.json','repair.json']:assert s.sha(R/'participant-completion'/unit/name)==s.sha(R/'submissions'/unit/'agent-output'/name)
  assert s.read(R/'operators'/(unit+'-handoff.json'))['initialSourceFiles']==initial
  requests=sorted((R/'feedback'/unit).glob('request-*'))if(R/'feedback'/unit).exists()else[];assert len(requests)<=2
  for index,request in enumerate(requests,1):
   files=source(R/'submissions'/unit/('feedback-'+str(index)));assert {k for k in set(initial)|set(files)if initial.get(k)!=files.get(k)}<=set(cfg['allowed_paths'])
   req=s.read(request/'request.json');assert req['startedAtUnix']<=s.read(R/'operators'/(unit+'-handoff.json'))['handoffAtUnix']+1200
   corpus=s.read(request/'evidence/corpus.json');assert corpus['source']==files
   for row in corpus['runs']:case(request/'evidence'/row['platform']/row['case'],R/'design'/cfg['task']/'public',row['case'],row['platform'],files);runs+=1
  for phase,cases,scope,barrier in [('final-public',['P1','P2'],'public','d0-raw'),('hidden',['H1'],'private','public-final')]:
   root=R/'corpora'/unit/phase;corpus=s.read(root/'corpus.json');assert corpus['source']==final and corpus['startedAtUnix']>=s.read(R/'gates'/(barrier+'.json'))['sealedAtUnix']
   for pl in ['ios','android']:
    for name in cases:case(root/pl/name,R/'design'/cfg['task']/scope,name,pl,final);runs+=1
  endpoint=s.read(R/'endpoints'/(unit+'.json'));assert endpoint['finishedAtUnix']==s.read(R/'corpora'/unit/'final-public/corpus.json')['finishedAtUnix']
  s.verify_dir(R/'self-final'/unit);runtime=s.read(R/'self-final'/unit/'endpoint.json');assert runtime['finishedAtUnix']>=endpoint['finishedAtUnix']
  scope=R/'design'/cfg['task']/'public';approval=s.read(scope/'approval.json')
  for stage,files in [('original',initial),('final',final)]:
   folder=R/'source-self'/unit/stage;s.verify_dir(folder)
   capsule=R/'submissions'/(cfg['task']if stage=='original'else unit)/('d0'if stage=='original'else'final')
   cat=source_audit.catalog(s.read(scope/'design-lock.json'),approval['design_lock_sha256'],s.read(scope/'implementation-audit.json'),approval['implementation_audit_sha256'],capsule/'source',scope)
   assert cat==s.read(folder/'catalog.json')
   assert source_audit.bind(cat,s.read(folder/'submission.json'))==s.read(folder/'report.json')
   assert s.read(folder/'receipt.json')['source']==files
  api_root=R/'source-api'/unit/'final';api=s.read(api_root/'record.json')
  assert api['source']==api['source_after']==final and api['source_unchanged']
  assert api['bridge_sha256']==s.sha(scope/'Bridge.swift')and api['operator_sha256']==s.sha(R/'check_minimum_api.py')
  api_ok=api['status']=='source_api_typechecked';assert api_ok==(len(api['commands'])==2 and all(v['exitCode']==0 for v in api['commands']))
  assert api['deployment_target']=='14.0'and api['compiler_target']=='arm64-apple-ios14.0-simulator'
  for index in range(len(api['commands'])):assert(api_root/('step-'+str(index)+'.log')).is_file()
  s.verify_dir(R/'self-complete'/unit);complete=s.read(R/'self-complete'/unit/'endpoint.json');source_ok=s.read(R/'source-self'/unit/'final/report.json')['status']=='accepted'
  assert complete['accepted']==(runtime['accepted']and source_ok and api_ok)
  assert complete['runtimeAccepted']==runtime['accepted']and complete['sourceAccepted']==source_ok and complete['minimumSourceAPIAccepted']==api_ok
  assert complete['runtimeEndpointSHA256']==s.sha(R/'self-final'/unit/'endpoint.json')and complete['sourceReceiptSHA256']==s.sha(R/'source-self'/unit/'final/receipt.json')
  assert complete['minimumSourceAPIRecordSHA256']==s.sha(api_root/'record.json')and complete['finishedAtUnix']>=api['finishedAtUnix']>=runtime['finishedAtUnix']
 for phase in ['d0','final']:
  s.verify_dir(R/'evaluation-inputs'/phase)
  s.verify_dir(R/'source-evaluation-inputs'/phase)
  for task in ['T1','T2']:
   for panel in ['one','two']:s.verify_dir(R/'judgments'/phase/panel/task)
   for base in (R/'evaluation-inputs'/phase/task).glob('*/*/*'):
    if not(base/'inputs.json').is_file():continue
    alias,pl,name=base.parts[-3:]
    meta=s.read(base/'inputs.json')
    for rel,h in meta['original_files'].items():assert s.sha(R/rel)==h,rel
    judgments=[R/'judgments'/phase/p/task/alias/pl/name/'judge.json'for p in ['one','two']]
    assert evaluation.report(phase,task,alias,pl,name,*judgments)==s.read(R/'evaluation'/phase/task/alias/pl/name/'acceptance.json')
   for base in (R/'source-evaluation-inputs'/phase/task).iterdir():
    alias=base.name;meta=s.read(base/'inputs.json')
    for rel,h in meta['original_files'].items():assert s.sha(R/rel)==h
    scope=R/meta['design_root'];approval=s.read(scope/'approval.json')
    cat=source_audit.catalog(s.read(scope/'design-lock.json'),approval['design_lock_sha256'],s.read(scope/'implementation-audit.json'),approval['implementation_audit_sha256'],R/meta['capsule']/'source',scope)
    assert cat==s.read(base/'catalog.json')
  source_consensus(phase)
 for path in (R/'evaluation/claims').glob('*/*/metric-input.json'):assert metrics.summarize(s.read(path))==s.read(path.with_name('metrics.json'))
 print(json.dumps({'status':'PASS','guardedBusinessNativeRequests':runs,'scope':'No SDK rerun. Original sources, coverage, chronology, images, full-public endpoints, independent consensus and unchanged metric calculations replayed. Failed/unknown results are retained, not required to pass.'}))
if __name__=='__main__':main()
