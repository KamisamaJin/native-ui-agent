from pathlib import Path
import json,sys,hashlib,subprocess,os
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward');ROOT=BASE/'business-design-v2';OUT=BASE/'business-design-review/v2-postapproval-responsibility';TOOL=BASE/'candidate-v13.9/scripts';sys.path.insert(0,str(TOOL));sys.dont_write_bytecode=True
import evidence_responsibility as er

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
placeholder=OUT/'pure-placeholder-subjects';component=placeholder/'component/component-placeholder.txt';bridge=placeholder/'bridge-placeholder.txt';integration=placeholder/'integration-placeholder.txt'
for p in [component,bridge,integration]:
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text('PURE SCHEMA PLACEHOLDER ONLY. No production implementation or native evidence.\n')
runs=[];profiles=[];readset=load(OUT/'READSET.json');seen={r['path']for r in readset}
def readlog(p,op):
 if str(p)not in seen:readset.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'operation':op});seen.add(str(p))
for t in range(1,6):
 for phase in ['public','private']:
  for platform in ['ios','android']:
   group=f'T{t}/{phase}/{platform}';src=ROOT/group;out=OUT/group;out.mkdir(parents=True,exist_ok=True);seal=load(src/'seal.json');plan=load(src/'generated/plan.json');lock=load(src/'lock.json')
   config={'design_sha256':seal['design_sha256'],'plan':str(src/'generated/plan.json'),'design_lock':str(src/'lock.json'),'policy':str(src/'policy.json'),'policy_sha256':seal['policy_sha256'],'responsibility_ref':{'source':'reference','pointer':'/responsibilities'},'source_roots':[str(component.parent)],'bridge':str(bridge),'source_review_store':str(OUT/'EMPTY_NO_ACTUAL_SOURCE_OBSERVATIONS'),'evidence_subjects':{'production-component':[str(component)],'thin-bridge':[str(bridge)],'host-integration':[str(integration)]},'pure_placeholder_scope':'Only structural claim compilation; these subject files are not production source and establish no source/native correctness.'}
   dump(out/'placeholder-config.json',config)
   cmd=[sys.executable,'-B',str(TOOL/'evidence_responsibility.py'),'audit','--config',str(out/'placeholder-config.json'),'--output',str(out/'compiled.json')]
   proc=subprocess.run(cmd,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),text=True,capture_output=True)
   (out/'audit.stdout.txt').write_text(proc.stdout);(out/'audit.stderr.txt').write_text(proc.stderr);runs.append({'profile':group,'argv':cmd,'exit_code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
   assert proc.returncode==0
   compiled=load(out/'compiled.json');evaluated=er.evaluate(config,compiled,report=None);dump(out/'no-evidence-evaluation.json',evaluated)
   empty=[c for c in compiled['claims']if c['method']in er.NATIVE and not c['rule_ids']]
   affected=[r for r in evaluated['rows']if r['id']=='component-text_layout']
   profiles.append({'profile':group,'empty_native_claims':empty,'compile_issues':compiled['issues'],'component_text_layout_evaluation':affected,'placeholder_source_boundary_checks_only':True,'actual_evidence_provided':False})
   for p in [src/'reference.json',src/'contract.json',src/'lock.json',src/'generated/plan.json',src/'policy.json',src/'seal.json']:readlog(p,'sealed-projected-responsibility-source-read')
for name in ['design_contract.py','native_checks.py','observation_contract.py']:
 readlog(TOOL/name,'pure-responsibility-compiler-dependency')
dump(OUT/'READSET.json',readset);dump(OUT/'pure-run-log.json',runs);dump(OUT/'reproduction-results.json',{'scope':'PURE structural preflight using clearly labeled nonproduction placeholder files. No actual implementation or native report was read or asserted. The no-evidence evaluations are diagnostic, not study outcome judgments.','profiles':profiles})
print(json.dumps({'profiles_compiled':len(profiles),'ios_unsupported_empty_claims':sum(len(r['empty_native_claims'])for r in profiles if r['profile'].endswith('/ios')),'android_unsupported_empty_claims':sum(len(r['empty_native_claims'])for r in profiles if r['profile'].endswith('/android')),'ios_affected_rows_unassessed':all(all(x['status']=='unassessed'for x in r['component_text_layout_evaluation'])for r in profiles if r['profile'].endswith('/ios')),'actual_source_or_native_evidence_used':False},indent=2))
