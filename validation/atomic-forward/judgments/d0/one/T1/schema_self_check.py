import pathlib,json,sys,time,traceback,hashlib
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/d0/one/T1';sys.path.insert(0,str(B/'candidate-v8/scripts'));import acceptance,native_checks
records=[]
for p in sorted((B/'evaluation-inputs/d0/T1').glob('*/*/*')):
 key=str(p.relative_to(B/'evaluation-inputs/d0/T1'));inp=json.loads((p/'inputs.json').read_text());plan=json.loads((p/'plan.json').read_text());judge=json.loads((O/key/'judge.json').read_text());lock=json.loads((B/inp['design_root']/'design-lock.json').read_text());policy=json.loads((B/inp['design_root']/'policy.json').read_text());obs=json.loads((B/inp['observation']).read_text());env=json.loads((B/inp['environment']).read_text());start=time.time()
 record={'case':key,'startedAtUnix':start,'purpose':'Schema self-check and frozen native/pixel recomputation only; identical own request passed twice, not an independent second judgment or consensus.'}
 try:
  result=acceptance.evaluate(plan,lock,inp['approval']['design_lock_sha256'],policy,inp['approval']['policy_sha256'],obs,inp['observation_sha256'],B/inp['root'],inp['platform'],env,judge,judge)
  dest=O/'schema-self-checks'/key/'acceptance-same-judge.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');record.update({'schema_valid':True,'counts':result['counts'],'artifact':str(dest.relative_to(O))})
 except Exception as e:
  record.update({'schema_valid':False,'error':str(e),'traceback':traceback.format_exc()});dest=O/'rejected-attempts'/key/'schema-rejection-1.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(record,indent=2)+'\n')
 record['finishedAtUnix']=time.time();records.append(record);print(key,record.get('schema_valid'),record.get('counts',record.get('error')))
(O/'schema-self-checks.json').write_text(json.dumps(records,indent=2)+'\n')
if not all(x['schema_valid'] for x in records):sys.exit(1)
