import json,pathlib,sys,time,importlib.util,traceback
R=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');O=R/'judgments/final/one/T1';sys.dont_write_bytecode=True;sys.path.insert(0,str(R/'candidate-v9/scripts'));import acceptance,design_contract,native_checks
spec=importlib.util.spec_from_file_location('implementation_audit',R.parents[1]/'tools/implementation_audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
checks=[]
for p in sorted((R/'evaluation-inputs/final/T1').glob('*/*/*')):
 begin=time.time();inp=json.loads((p/'inputs.json').read_text());dst=O/inp['source']/inp['platform']/inp['case'];request=json.loads((dst/'judge.json').read_text());plan=json.loads((p/'plan.json').read_text());scope=R/inp['scope'];lock=json.loads((scope/'design-lock.json').read_text());policy=json.loads((scope/'policy.json').read_text());obs=json.loads((R/inp['observation']).read_text());c=json.loads((p/'catalog.json').read_text());env=json.loads((R/inp['environment']).read_text())
 record={'source':inp['source'],'platform':inp['platform'],'case':inp['case'],'startedAtUnix':begin,'function':'candidate-v9/scripts/acceptance.evaluate','same_request_in_both_panel_slots':True,'independent_consensus':False}
 try:
  report=acceptance.evaluate(plan,lock,c['design_lock_sha256'],policy,c['policy_sha256'],obs,inp['observation_sha256'],(R/inp['raw']).resolve(),inp['platform'],env,request,request)
  record.update({'schema_binding_check':'accepted','counts':report['counts'],'environment_status':report['environment']['status'],'nonpass_rows':[x for x in report['rows']if x['status']!='passed']})
 except Exception as e:
  record.update({'schema_binding_check':'rejected','error':str(e),'traceback':traceback.format_exc()})
 record['endedAtUnix']=time.time();(dst/'self-schema-check.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');checks.append({k:v for k,v in record.items()if k not in ['nonpass_rows']});print(inp['source'],inp['platform'],inp['case'],record['schema_binding_check'],record.get('counts'),flush=True)
for alias in ['source-a','source-b']:
 cat=json.loads((R/'source-evaluation-inputs/final/T1'/alias/'catalog.json').read_text());request=json.loads((O/alias/'source-judge.json').read_text());record={'function':'tools/implementation_audit.py:bind','source':alias,'independent_consensus':False}
 try:
  report=audit.bind(cat,request['review']);record.update({'schema_binding_check':'accepted','counts':report['counts'],'status':report['status'],'nonpass_rows':[x for x in report['rows']if x['status']!='passed']})
 except Exception as e:record.update({'schema_binding_check':'rejected','error':str(e),'traceback':traceback.format_exc()})
 (O/alias/'source-schema-check.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');checks.append(record);print(alias,'source',record['schema_binding_check'],record.get('counts'),flush=True)
(O/'schema-check-summary.json').write_text(json.dumps(checks,indent=2)+'\n')
