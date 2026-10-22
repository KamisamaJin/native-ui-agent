import json,pathlib,hashlib,subprocess,time
b=pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
out=pathlib.Path(__file__).resolve().parent
public=b/'design-v2/T3/public';commands=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  root=b/'own-corpora/unit-7d82e7/d0'/platform/case
  observation=root/'observation.json';o=json.loads(observation.read_text())
  cat=json.loads((b/'submissions/unit-7d82e7/own-checks/d0'/case/platform/'bound/catalog.json').read_text())
  decisions=[]
  for row in cat['rows']:
   if row['method']!='visual':continue
   state=row['state'];cap=next(x for x in o['state_captures'] if x['state_id']==state)
   clipped=case=='P2' and platform=='android'
   if clipped:
    reason=('The fully visible native disclosure button has the first glyph of each wrapped line visibly cut by its rounded leading corners in the original PNG. Other required text is present across the complete state sweep. This is visible glyph clipping, independent of native ellipsized=false.' if row['aspect']=='wrapping' else 'The disclosure text occupies the rounded clipping area of its native button: the leading portions of the first glyphs are visibly occluded although the entire button is inside the viewport. Other controls remain separated. This shares one root cause with the wrapping failure.')
   else:
    reason=('Across the original overlapping exact-state sweep, all required title, subtitle, notice, service labels, details/reason, summary, action and footer text are readable with no ellipsis or missing words; expanded guidance is included only in the expanded state. Character fallback in narrow iOS labels preserves all characters.' if row['aspect']=='wrapping' else 'Across the complete original exact-state sweep, text, indicators, reason/status content, summary, disclosure content and primary action occupy separate areas without collision or occlusion. Viewport-edge cuts are covered in overlapping original frames.')
   decisions.append({'review_id':row['review_id'],'actual':not clipped,'reason':reason,'snapshot_indices':cap['snapshot_indices']})
  submission={'version':1,'catalog_sha256':cat['catalog_sha256'],'observation_sha256':hashlib.sha256(observation.read_bytes()).hexdigest(),'decisions':decisions}
  sp=out/f'submission-{case}-{platform}.json';sp.write_text(json.dumps(submission,indent=2)+'\n')
  target=out/'bound'/case/platform
  command=['python3',str(b/'candidate-v8/scripts/review_contract.py'),'review','--plan',str(b/'submissions/unit-7d82e7/initial-agent-output/plans'/case/platform/'plan.json'),'--design-lock',str(public/'design-lock.json'),'--design-sha256','0653c194d723fbb087b20ee8eac97b1388256ff2b8e3ba6db203c7a45cec4656','--policy',str(public/'policy.json'),'--policy-sha256','806d2317c0adc6db6057c5d7ed40d857f98e45286c5c0d24b1b4867a0aa63dc8','--platform',platform,'--observation',str(observation),'--submission',str(sp),'--output',str(target)]
  start=time.time();p=subprocess.run(command,capture_output=True,text=True)
  lp=out/f'bound-{case}-{platform}.log';lp.write_text(p.stdout+p.stderr)
  commands.append({'case':case,'platform':platform,'command':command,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':p.returncode,'log':str(lp),'submission':str(sp),'output':str(target)})
  (out/'bound-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
  print(case,platform,p.returncode,p.stdout,p.stderr)
