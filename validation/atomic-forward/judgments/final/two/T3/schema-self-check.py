from pathlib import Path
import sys,json,hashlib,time,traceback
sys.dont_write_bytecode=True
root=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
out=root/'judgments/final/two/T3'
sys.path.insert(0,str(root/'candidate-v8/scripts'))
import acceptance,native_checks,review_contract,design_contract
log=[]
for p in sorted((root/'evaluation-inputs/final/T3').glob('*/*/*/inputs.json')):
    started=time.time();inp=json.loads(p.read_text());key=str(p.parent.relative_to(root/'evaluation-inputs/final/T3'))
    design=root/inp['design_root'];plan=json.loads((p.parent/'plan.json').read_text());lock=json.loads((design/'design-lock.json').read_text());policy=json.loads((design/'policy.json').read_text());observation_path=root/inp['observation'];observation=json.loads(observation_path.read_text());obs_sha=hashlib.sha256(observation_path.read_bytes()).hexdigest();judge=json.loads((out/key/'judge.json').read_text());env=json.loads((root/inp['environment']).read_text())
    assert obs_sha==inp['observation_sha256']
    try:
        # This is one schema self-check with this SAME request in both slots.
        # It is explicitly not independent consensus.
        result=acceptance.evaluate(plan,lock,inp['approval']['design_lock_sha256'],policy,inp['approval']['policy_sha256'],observation,obs_sha,root/inp['root'],inp['platform'],env,judge,judge)
        (out/key/'schema-self-check.json').write_text(json.dumps({'scope':'Schema self-check only. Same judge request supplied twice; not independent agreement or human gold.','result':result},indent=2)+'\n')
        blank={'version':1,'catalog_sha256':judge['review']['catalog_sha256'],'observation_sha256':obs_sha,'decisions':[]}
        bound=review_contract.bind(plan,lock,inp['approval']['design_lock_sha256'],policy,inp['approval']['policy_sha256'],observation,obs_sha,root/inp['root'],blank,inp['platform'])
        authoritative=native_checks.evaluate(plan,observation,inp['platform'],bound,root/inp['root'],obs_sha,lock,inp['approval']['design_lock_sha256'],policy,inp['approval']['policy_sha256'])
        (out/key/'recomputed-numerical.json').write_text(json.dumps(authoritative,indent=2)+'\n')
        failures=[x for x in authoritative['assertions'] if x['status']=='failed']
        log.append({'case':key,'schemaAccepted':True,'nativePixelFailures':[x['id']for x in failures],'counts':authoritative['counts'],'startedAtUnix':started,'finishedAtUnix':time.time()})
        print(key,'schema accepted','native/pixel F',len(failures))
    except Exception:
        error=traceback.format_exc();reject=out/key/'rejected-self-check-attempt-1.txt';reject.write_text(error);log.append({'case':key,'schemaAccepted':False,'rejection':str(reject.relative_to(out)),'startedAtUnix':started,'finishedAtUnix':time.time()});print(key,error)
(out/'schema-self-check-log.json').write_text(json.dumps(log,indent=2)+'\n')
