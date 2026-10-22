import pathlib,json,sys,hashlib,time,traceback
B=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward');O=B/'judgments/final/one/T3';sys.dont_write_bytecode=True;sys.path.insert(0,str(B/'candidate-v8/scripts'))
import acceptance,native_checks,design_contract
results=[];audit={}
for ip in sorted((B/'evaluation-inputs/final/T3').glob('*/*/*/inputs.json')):
 key=str(ip.parent.relative_to(B/'evaluation-inputs/final/T3'));d=json.loads(ip.read_text());p=json.loads((ip.parent/'plan.json').read_text());obs=json.loads((B/d['observation']).read_text());judge=json.loads((O/key/'judge.json').read_text());out=O/'schema-self-checks'/key;out.mkdir(parents=True,exist_ok=True);t=time.time()
 states={}
 for s in p['states']:
  found,complete,reason,cap=native_checks.bound_state_evidence(obs,s);res={}
  for id in ['bicycle.canvas','bicycle.title','bicycle.notice','bicycle.choice.a','bicycle.choice.b','bicycle.choice.c','bicycle.choice.d','bicycle.choice.e','bicycle.choice.f','bicycle.summary','bicycle.disclosure','bicycle.submit','bicycle.footer']:
   rows=[]
   for i,snap in found:
    r=native_checks.resolve(snap,{'identifier':id},d['platform'])
    if r.get('facts',{}).get('present'):
     rows.append({'snapshot_index':i,**r})
   res[id]=rows
  states[s['id']]={'complete':complete,'coverage_reason':reason,'capture':cap,'targets':res}
 audit[key]={'state_targets':states,'steps':obs['steps'],'fixture_sha256':hashlib.sha256((B/d['root']/'fixtures.json').read_bytes()).hexdigest()}
 try:
  report=acceptance.evaluate(p,json.loads((B/d['design_root']/'design-lock.json').read_text()),d['approval']['design_lock_sha256'],json.loads((B/d['design_root']/'policy.json').read_text()),d['approval']['policy_sha256'],obs,d['observation_sha256'],B/d['root'],d['platform'],json.loads((B/d['environment']).read_text()),judge,judge)
  (out/'same-request-twice.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  r={'case':key,'accepted_schema':True,'counts':report['counts'],'durationSeconds':time.time()-t,'purpose':'Schema self-check only. This one request is supplied in both judge slots; this is not independent agreement.'}
 except Exception as e:
  r={'case':key,'accepted_schema':False,'error':repr(e),'durationSeconds':time.time()-t};(out/'rejected-attempt-1.txt').write_text(traceback.format_exc())
 results.append(r);(O/'schema-self-check-results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(r),flush=True)
(O/'native-state-action-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
