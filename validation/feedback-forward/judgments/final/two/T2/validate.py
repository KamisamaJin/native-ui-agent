import sys
sys.dont_write_bytecode=True
import json,pathlib,hashlib,time,traceback,importlib.util
BASE=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');OUT=BASE/'judgments/final/two/T2'
sys.path.insert(0,str(BASE/'candidate-v9/scripts'));import acceptance,design_contract,native_pixels
load=lambda p:json.loads(p.read_text())
records={}
for p in sorted((BASE/'evaluation-inputs/final/T2').glob('*/*/*')):
 key='/'.join(p.parts[-3:]);i=load(p/'inputs.json');cat=load(p/'catalog.json');plan=load(p/'plan.json');judge=load(OUT/key/'judge.json');scope=BASE/i['scope'];o=load(BASE/i['observation']);started=time.time()
 try:
  report=acceptance.evaluate(plan,load(scope/'design-lock.json'),cat['design_lock_sha256'],load(scope/'policy.json'),cat['policy_sha256'],o,i['observation_sha256'],BASE/i['raw'],i['platform'],load(BASE/i['environment']),judge,judge)
  compact={k:v for k,v in report.items() if k!='rows'};compact['schema_check_only']='The same assessor request occupies both slots. This is not independent consensus or human gold.';compact['rows']=[{k:v for k,v in r.items() if k in ['id','state','status','ungated_fact_status','responsibility','cause_category','method','reason']} for r in report['rows']]
  compact['original_report_canonical_sha256']=design_contract.digest(report);compact['startedAtUnix']=started;compact['endedAtUnix']=time.time();(OUT/key/'schema-check.json').write_text(json.dumps(compact,ensure_ascii=False,indent=2)+'\n');records[key]={'schema_valid':True,'counts':report['counts'],'unknown_ids':[r['id'] for r in report['rows'] if r['status']=='unassessed'],'failed_ids':[r['id'] for r in report['rows'] if r['status']=='failed']};print(key,records[key],flush=True)
 except Exception as e:
  (OUT/key/'schema-check-rejected.txt').write_text(traceback.format_exc());records[key]={'schema_valid':False,'error':str(e)};print(key,records[key],flush=True)
# Source schemas use the exact supplied source-bound catalog, with hashes independently verified by writer.
spec=importlib.util.spec_from_file_location('shared_implementation_audit',BASE.parents[1]/'tools/implementation_audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
for p in sorted((BASE/'source-evaluation-inputs/final/T2').glob('*')):
 cat=load(p/'catalog.json');judge=load(OUT/p.name/'source-judge.json');report=audit.bind(cat,judge['review']);assert len(judge['review']['decisions'])==len(cat['rows']);(OUT/p.name/'source-schema-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');records[p.name+'/source']={'schema_valid':True,'counts':report['counts'],'status':report['status']};print(p.name+'/source',records[p.name+'/source'],flush=True)
(OUT/'schema-check-summary.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
