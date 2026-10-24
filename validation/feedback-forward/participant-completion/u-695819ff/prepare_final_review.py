import pathlib,json,subprocess,hashlib,time
b=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');d=b/'design/T2/public';a=json.load(open(d/'approval.json'));out=pathlib.Path('agent-output/final-self');out.mkdir(parents=True,exist_ok=True)
phase=out/'phase.json'
if not phase.exists():phase.write_text(json.dumps({'startedAtUnix':time.time(),'scope':'Fresh full final-public original PNGs, plus all approved targeted visual checkpoints; no source-only or pixel overrides.'},indent=2))
for platform in ['ios','android']:
 for case in ['P1','P2']:
  target=out/platform/case;target.mkdir(parents=True,exist_ok=True)
  cmd=['python3',str(b/'candidate-v9/scripts/review_contract.py'),'catalog','--plan',str(d/'compiled'/case/platform/'plan.json'),'--design-lock',str(d/'design-lock.json'),'--design-sha256',a['design_lock_sha256'],'--policy',str(d/'policy.json'),'--policy-sha256',a['policy_sha256'],'--platform',platform,'--output',str((target/'catalog.json').resolve())]
  r=subprocess.run(cmd,capture_output=True,text=True);(target/'catalog-run.json').write_text(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2));print(platform,case,r.returncode,r.stderr[:200])
