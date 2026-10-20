#!/usr/bin/env python3
"""Seal tools only after native controls and independent scoped forward testing."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess,sys,time
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 out=R/'candidate-v6';assert not out.exists()
 independent=R/'independent-generic';addendum=independent/'POST-FINAL-TRUST-GATE.json';assert addendum.is_file()
 logs=R/'operators';logs.mkdir(exist_ok=True)
 commands=[[sys.executable,'-B','-m','unittest','discover','-s','native-ui-agent/tests','-q'],[sys.executable,'-B',str(R/'verify_generic.py')]]
 records=[]
 for i,cmd in enumerate(commands):
  start=time.time();p=subprocess.run(cmd,cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);log=logs/f'prefreeze-{i}.log';log.write_text(p.stdout);assert p.returncode==0,p.stdout
  records.append({'argv':cmd,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':p.returncode,'logSHA256':sha(log)})
 for rel,h in read(R/'baseline-v5-freeze.json')['files'].items():assert sha(R/'baseline-v5'/rel)==h
 shutil.copytree(REPO/'native-ui-agent',out,ignore=shutil.ignore_patterns('__pycache__','.DS_Store'))
 files={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()}
 data={'frozenAtUTC':datetime.now(timezone.utc).isoformat(),'frozenAtUnix':time.time(),'scope':'Full v6 Skill after real neutral iOS/Android controls and separate-context native forward test, before any new business design or source. No case-specific typography change. Preserve all failures and measurement-scope revisions.','files':files,'rootGenericSummarySHA256':sha(R/'generic-summary.json'),'independentSummarySHA256':sha(independent/'FINAL-SUMMARY.md'),'independentFinalFreezeSHA256':sha(independent/'FINAL-FREEZE.json'),'independentTrustGateSHA256':sha(addendum),'preregistrationSHA256':sha(R/'PREREGISTRATION.md'),'operationsSHA256':sha(R/'OPERATIONS.md'),'preflightCommands':records}
 (R/'candidate-v6-freeze.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({'frozenAtUTC':data['frozenAtUTC'],'files':len(files)}))
if __name__=='__main__':main()
