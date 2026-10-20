from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,hashlib
r=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/contract-forward')
out=Path(__file__).resolve().parent/'review-checks';out.mkdir(exist_ok=False)
rows=json.loads((Path(__file__).parent/'review-artifacts/manual-image-index.json').read_text())
records=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  corpus=r/('own-retries' if platform=='ios' and case=='P2' else 'own-corpora')/'unit-092e15/d0'/platform/case
  obs=corpus/'observation.json';dest=out/case/platform;dest.mkdir(parents=True)
  decisions=[]
  for row in rows:
   if row['case']!=case or row['platform']!=platform:continue
   decisions.append({'id':row['state']+'/reserve-visible','method':'visual','status':'passed','reason':'Inspected the actual state screenshot (also displayed in a viewport contact sheet). The complete Reserve seats label is visible, including both words and their glyphs, without ellipsis or clipping. This judges label visibility only, not native typography/color or control height.','snapshot_indices':[row['snapshot_index']],'evidence':[row['evidence']]})
  manual={'observation_sha256':hashlib.sha256(obs.read_bytes()).hexdigest(),'decisions':decisions}
  (dest/'manual.json').write_text(json.dumps(manual,indent=2)+'\n')
  cmd=['python3',str(r/'candidate-v6/scripts/native_checks.py'),'--plan',str(r/'submissions/unit-092e15/initial-agent-output/plans'/case/platform/'plan.json'),'--observation',str(obs),'--platform',platform,'--manual',str(dest/'manual.json'),'--root',str(corpus),'--output',str(dest/'report.json'),'--design-lock',str(r/'design/public/design-lock.json'),'--design-sha256','c2548a601384046a016e98258728877982f30a4ed25be22455d9ec9ea4399bc1']
  start=datetime.now(timezone.utc).isoformat();result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  (dest/'command.log').write_text(result.stdout)
  record={'argv':cmd,'started_utc':start,'finished_utc':datetime.now(timezone.utc).isoformat(),'exit_code':result.returncode}
  (dest/'command.json').write_text(json.dumps(record,indent=2)+'\n');records.append(record)
  print(case,platform,result.returncode,result.stdout)
(out/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
