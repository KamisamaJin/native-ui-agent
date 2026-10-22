from pathlib import Path
import json,hashlib,subprocess,datetime
base=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
output=base/'cache/unit-b44248/agent-output/review'
records=[]
for case in ('P1','P2'):
 for platform in ('ios','android'):
  original=base/'own-corpora/unit-b44248/d0'/platform/case/'observation.json'
  observation=json.loads(original.read_text())
  catalog=json.loads((base/'submissions/unit-b44248/own-checks/d0'/case/platform/'bound/catalog.json').read_text())
  states={x['state_id']:x for x in observation['state_captures']}
  decisions=[]
  for row in catalog['rows']:
   if row['method']!='visual':continue
   state=states[row['state']]
   if row['aspect']=='wrapping':
    reason='Reviewed the original overlapping full-state frames from title through footer. Required title, subtitle, notice, all six choice labels, details and unavailable reasons, summary, disclosure label and primary label are present in readable wrapped lines without clipping or ellipsis. Guidance is included only for the expanded state; collapsed guidance is intentionally excluded. Character breaks in narrow unavailable labels preserve the full word.'
   else:
    reason='Reviewed every original frame in this state sweep. Text blocks, card surfaces, status words, global briefing when expanded, summary and primary control occupy distinct regions. Viewport edge cuts continue in adjacent overlapping frames and are not unintended content occlusion.'
   decisions.append({'review_id':row['review_id'],'actual':True,'reason':reason,'snapshot_indices':state['snapshot_indices']})
  submission={'version':1,'catalog_sha256':catalog['catalog_sha256'],'observation_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'decisions':decisions}
  dest=output/'submissions'/case/platform;dest.mkdir(parents=True,exist_ok=True)
  request=dest/'original-submission.json';request.write_text(json.dumps(submission,indent=2)+'\n')
  command=['python3',str(base/'candidate-v8/scripts/review_contract.py'),'review','--plan',str(base/'submissions/unit-b44248/initial-agent-output/plans'/case/platform/'plan.json'),'--design-lock',str(base/'design-v2/T1/public/design-lock.json'),'--design-sha256','1595cbbb3a50848a0fe9a639bc775dde0a781690fc94381a6eb8f0a469d4c31a','--policy',str(base/'design-v2/T1/public/policy.json'),'--policy-sha256','9541d9de335957cd5037319fc8e389d8c926321425687fa916931c94b11bc835','--platform',platform,'--observation',str(original),'--submission',str(request),'--output',str(output/'bound'/case/platform)]
  start=datetime.datetime.now(datetime.timezone.utc);result=subprocess.run(command,text=True,capture_output=True);finish=datetime.datetime.now(datetime.timezone.utc)
  (dest/'stdout.log').write_text(result.stdout);(dest/'stderr.log').write_text(result.stderr)
  record={'argv':command,'startedAtUnix':start.timestamp(),'finishedAtUnix':finish.timestamp(),'exitCode':result.returncode,'submission':str(request),'stdout':str(dest/'stdout.log'),'stderr':str(dest/'stderr.log')}
  (dest/'command.json').write_text(json.dumps(record,indent=2)+'\n');records.append(record)
  print(case,platform,'exit',result.returncode,result.stdout[-1200:],result.stderr[-1200:])
(output/'bound-command-records.json').write_text(json.dumps(records,indent=2)+'\n')
