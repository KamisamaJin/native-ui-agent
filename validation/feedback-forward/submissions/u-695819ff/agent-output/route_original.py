import json,pathlib,subprocess
b=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');d=b/'design/T2/public';a=json.load(open(d/'approval.json'));s=b/'candidate-v9/scripts/requirement_routes.py'
for case in ['P1','P2']:
 for platform in ['ios','android']:
  out=pathlib.Path('agent-output/original-routes')/platform/case;out.mkdir(parents=True,exist_ok=True)
  common=['python3',str(s),'--plan',str(d/'compiled'/case/platform/'plan.json'),'--design-lock',str(d/'design-lock.json'),'--design-sha256',a['design_lock_sha256'],'--routes',str(d/'routes.json'),'--routes-sha256',a['routes_sha256']]
  r=subprocess.run(common[:2]+['route']+common[2:]+['--report',str(b/'corpora/T2/d0'/platform/case/'automatic.json'),'--observation',str(b/'corpora/T2/d0'/platform/case/'native/observation.json'),'--output',str(out/'route.json')],capture_output=True,text=True)
  (out/'run.json').write_text(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2));print(platform,case,r.returncode,r.stdout[:150],r.stderr[:150])
