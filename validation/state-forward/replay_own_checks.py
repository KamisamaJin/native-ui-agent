#!/usr/bin/env python3
"""Run each frozen original plan on fresh own-FINAL evidence, without feedback."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 output=R/'own-final-checks';assert not output.exists();output.mkdir()
 ledger=[]
 for unit,tool in [('unit-93485d','candidate-v5'),('unit-fb632e','baseline-v4')]:
  dest=output/unit;dest.mkdir()
  for platform in ['ios','android']:
   for case in ['P1','P2','P3','P4']:
    plan=R/'submissions'/unit/'initial-agent-output/review-plan'/case/('plan.'+platform+'.json')
    capture=R/'own-corpora'/unit/'final'/platform/case
    report=dest/(platform+'-'+case+'.json')
    cmd=[sys.executable,str(R/tool/'scripts/native_checks.py'),'--plan',str(plan),'--observation',str(capture/'observation.json'),'--platform',platform,'--root',str(capture),'--output',str(report)]
    start=time.time();p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);end=time.time()
    log=report.with_suffix('.log');log.write_text(p.stdout)
    assert report.exists(),p.stdout
    data=json.loads(report.read_text())
    ledger.append({'unit':unit,'tool':tool,'platform':platform,'case':case,'argv':cmd,'startedAtUnix':start,'finishedAtUnix':end,'exitCode':p.returncode,'planSHA256':sha(plan),'observationSHA256':sha(capture/'observation.json'),'checkerSHA256':sha(R/tool/'scripts/native_checks.py'),'report':str(report.relative_to(output)),'reportSHA256':sha(report),'counts':data['counts']})
 (output/'invocations.json').write_text(json.dumps(ledger,indent=2)+'\n')
 print(json.dumps({'runs':len(ledger),'scope':'Original plan replay on fresh own FINAL; no source repair or extra feedback; not independent acceptance.'}))
if __name__=='__main__':main()
