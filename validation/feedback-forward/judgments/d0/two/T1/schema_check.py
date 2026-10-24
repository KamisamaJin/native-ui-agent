import json,sys,time,hashlib,importlib.util,traceback
from pathlib import Path
sys.dont_write_bytecode=True
b=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');out=b/'judgments/d0/two/T1';sys.path.insert(0,str(b/'candidate-v9/scripts'))
import acceptance,design_contract as d
run={'startedAtUnix':int(time.time()),'purpose':'Self schema/binding check only. The SAME assessor request is passed twice; this is neither independent consensus nor human gold.','runtime':{},'source':{}}
for p in sorted((b/'evaluation-inputs/d0/T1').glob('*/*/*')):
 i=d.load(p/'inputs.json');dest=out/i['source']/i['platform']/i['case'];judge=d.load(dest/'judge.json');lock=d.load(b/i['scope']/'design-lock.json');policy=d.load(b/i['scope']/'policy.json');obs=d.load(b/i['observation']);env=d.load(b/i['environment']);key='/'.join([i['source'],i['platform'],i['case']]);output=dest/'self-schema-check.json'
 try:
  assert hashlib.sha256((b/i['observation']).read_bytes()).hexdigest()==i['observation_sha256']
  assert d.digest(env)==i['approval']['environment_sha256'][i['case']][i['platform']]
  report=acceptance.evaluate(d.load(p/'plan.json'),lock,i['approval']['design_lock_sha256'],policy,i['approval']['policy_sha256'],obs,i['observation_sha256'],b/i['raw'],i['platform'],env,judge,judge)
  with output.open('x') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  run['runtime'][key]={'schemaAccepted':True,'counts':report['counts'],'environment':report['environment']['status'],'unassessed':[r['id'] for r in report['rows'] if r['status']=='unassessed'],'failures':[{'id':r['id'],'status':r['status'],'cause':r['cause_category']} for r in report['rows'] if r['status']=='failed'],'output':str(output.relative_to(out))}
 except Exception:
  error=traceback.format_exc();(dest/'self-schema-check-rejected.txt').write_text(error);run['runtime'][key]={'schemaAccepted':False,'error':error}
 print(key,run['runtime'][key])
try:
 path=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/tools/implementation_audit.py');spec=importlib.util.spec_from_file_location('permitted_implementation_audit',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);cat=d.load(b/'source-evaluation-inputs/d0/T1/initial/catalog.json');judge=d.load(out/'initial/source-judge.json');report=mod.bind(cat,judge['review']);output=out/'initial/source-self-schema-check.json'
 with output.open('x') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 run['source']={'schemaAccepted':True,'counts':report['counts'],'status':report['status'],'output':str(output.relative_to(out))}
except Exception:
 error=traceback.format_exc();(out/'initial/source-self-schema-check-rejected.txt').write_text(error);run['source']={'schemaAccepted':False,'error':error}
run['endedAtUnix']=int(time.time());(out/'schema-check-log.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n');print('source',run['source'])
