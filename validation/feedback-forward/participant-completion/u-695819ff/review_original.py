import json,pathlib,hashlib,subprocess,time
b=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/feedback-forward');d=b/'design/T2/public';a=json.load(open(d/'approval.json'));s=b/'candidate-v9/scripts/review_contract.py';claims=json.load(open('agent-output/claims.json'))['findings']
for platform in ['ios','android']:
 for case in ['P1','P2']:
  out=pathlib.Path('agent-output/original-review')/platform/case;out.mkdir(parents=True,exist_ok=True);p=b/'corpora/T2/d0'/platform/case/'native/observation.json';c=json.load(open(d/'compiled'/case/platform/'review-catalog.json'))
  decisions=[]
  for r in c['rows']:
   if r['method']!='visual': continue
   f=next((f for f in claims if f['platform']==platform and f['case']==case and r['id'] in f['assertion_ids']),None)
   decisions.append({'review_id':r['review_id'],'actual':True if f else None,'reason':f['reason'] if f else 'This original targeted checkpoint was not visually reviewed before the first edit; it remains unknown, and later repair evidence will not expand original detection scope.','snapshot_indices':f['snapshot_indices'] if f else []})
  sub={'version':1,'catalog_sha256':c['catalog_sha256'],'observation_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'decisions':decisions};sp=out/'submission.json';sp.write_text(json.dumps(sub,indent=2))
  cmd=['python3',str(s),'review','--plan',str(d/'compiled'/case/platform/'plan.json'),'--design-lock',str(d/'design-lock.json'),'--design-sha256',a['design_lock_sha256'],'--policy',str(d/'policy.json'),'--policy-sha256',a['policy_sha256'],'--platform',platform,'--observation',str(p),'--submission',str(sp.resolve()),'--output',str((out/'bound').resolve())]
  r=subprocess.run(cmd,capture_output=True,text=True);(out/'run.json').write_text(json.dumps({'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2));print(platform,case,r.returncode,r.stderr[:200])
