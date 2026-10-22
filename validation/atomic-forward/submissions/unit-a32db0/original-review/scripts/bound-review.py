from pathlib import Path
import json,hashlib,subprocess,time
base=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
root=base/'cache/unit-a32db0'
out=root/'agent-output/review'
records=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  old=base/f'submissions/unit-a32db0/own-checks/d0/{case}/{platform}/bound/catalog.json'
  obs=base/f'own-corpora/unit-a32db0/d0/{platform}/{case}/observation.json'
  c=json.load(open(old));o=json.load(open(obs));decisions=[]
  for row in c['rows']:
   if row['method']!='visual':continue
   state=row['state'];inds=next(x['snapshot_indices'] for x in o['state_captures'] if x['state_id']==state)
   if row['aspect']=='overlap':
    actual=True;reason='Read the entire original overlapping full-content sweep: heading, notice, disclosure, card labels/severities/reasons, inline dossier when expanded, summary, action and footer occupy separate areas. No unintended overlap or occlusion is visible; viewport-edge cropping is continued in adjacent indexed frames.'
   elif case=='P2' and platform=='android':
    actual=False;reason='The required Ferry card label wraps pressure-gauge as pressure-gau / ge drift even though the existing hyphen gives a natural break and each segment fits. This contradicts the approved natural wrapping question and the brief preference for spaces/hyphens before character fallback. Every character remains visible; this is unnatural wrapping, not truncation. In expanded state the dossier also wraps Maintenance-held as Maintenance-h / eld alerts.'
   else:
    actual=True;reason='Read every indexed original full-content frame. All currently required title/subtitle/notice/labels/severities/reasons, selected inline detail in expanded state, summary/action/footer are present and continue across natural wrapped lines or character fallback for overlong unbroken segments. No truncation or ellipsis is visible. Closed dossiers and no-selection guidance intentionally hidden in these three routes are excluded.'
   decisions.append({'review_id':row['review_id'],'actual':actual,'reason':reason,'snapshot_indices':inds})
  submission={'version':1,'catalog_sha256':c['catalog_sha256'],'observation_sha256':hashlib.sha256(obs.read_bytes()).hexdigest(),'decisions':decisions}
  path=out/f'submissions/{case}-{platform}.json';path.write_text(json.dumps(submission,indent=2)+'\n')
  argv=['python3',str(base/'candidate-v8/scripts/review_contract.py'),'review','--plan',str(base/f'submissions/unit-a32db0/initial-agent-output/plans/{case}/{platform}/plan.json'),'--design-lock',str(base/'design-v2/T2/public/design-lock.json'),'--design-sha256','c21f3c012a188c7c39e8017dc92e8749b821a74aa3ad84d007732cfffa48e000','--policy',str(base/'design-v2/T2/public/policy.json'),'--policy-sha256','e31cc38ba6456e8e3c787ad9c1e962586ce6795d7934e23e817fa7ae90ae3543','--platform',platform,'--observation',str(obs),'--submission',str(path),'--output',str(out/f'bound/{case}/{platform}')]
  start=time.time();p=subprocess.run(argv,cwd=root,capture_output=True,text=True);finish=time.time()
  log=out/f'logs/{case}-{platform}-bound.log';log.write_text(p.stdout+p.stderr)
  records.append({'case':case,'platform':platform,'argv':argv,'startedAtUnix':start,'finishedAtUnix':finish,'exitCode':p.returncode,'log':str(log),'submission':str(path)})
  (out/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
  print(case,platform,p.returncode,p.stdout,p.stderr)
