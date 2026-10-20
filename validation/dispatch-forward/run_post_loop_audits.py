#!/usr/bin/env python3
"""One-shot post-loop scheduling: never contend with measured primary loops."""
import concurrent.futures,json,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
from trial_operator import fingerprint,read,save
R=Path(__file__).resolve().parent
def utc():return datetime.now(timezone.utc).isoformat()
def collect(sid,phase,tool,workspace,simulator,family):
 src=R/'private/submissions'/sid/phase;w=R/'cache'/workspace
 assert fingerprint(w)==read(src/'seal.json')['files'],'Dedicated audit host source differs'
 archive=R/'evidence'/family/sid;seal=R/'private/audit-seals'/(family+'-'+sid+'.json');out=R/'cache'/family/sid;log=R/'cache'/(family+'-'+sid+'-process.log')
 cmd=[sys.executable,str(R/'run_collection.py'),'--workspace',str(w),'--tool',tool,'--phase',phase,'--inputs',str(R/'private/inputs'/('d0-v2'if phase=='d0'else'final')),'--simulator',simulator,'--output',str(out),'--archive',str(archive),'--seal',str(seal)]
 row={'family':family,'submission':sid,'phase':phase,'startedAtUTC':utc(),'startedAtUnix':time.time(),'argv':cmd}
 with log.open('w')as stream:code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT).returncode
 row.update(exitCode=code,finishedAtUTC=utc(),finishedAtUnix=time.time());save(R/'private/audit-seals'/(family+'-'+sid+'-process.json'),row)
 assert code==0 and seal.is_file(),'Audit collection failed; original logs retained'
 print(json.dumps({'event':'audit_corpus_sealed','family':family,'submission':sid,'atUTC':utc()}),flush=True)
 return row
def baseline():
 rows=[collect('submission-e572b1','d0','candidate-v4','audit-e572b1','FA4FF655-FBA2-46B1-BBB1-84FCD48C46CD','audit-v4-d0')]
 subprocess.run([sys.executable,str(R/'install_capsule.py'),str(R/'private/submissions/submission-e572b1/final'),str(R/'cache/audit-e572b1')],check=True,stdout=subprocess.DEVNULL)
 rows.append(collect('submission-e572b1','final','candidate-v4','audit-e572b1','FA4FF655-FBA2-46B1-BBB1-84FCD48C46CD','audit-v4-final'));return rows
def main():
 output=R/'private/audit-orchestration.json';assert not output.exists()
 print('Waiting for BOTH assigned-tool FINAL corpus seals; no experiment native work starts before them.',flush=True)
 ids=['submission-e572b1','submission-3d6389']
 while not all((R/'private/submissions'/sid/'final-corpus-seal.json').is_file()for sid in ids):time.sleep(10)
 barrier=max(read(R/'private/submissions'/sid/'final-corpus-seal.json')['sealedAtUnix']for sid in ids)
 record={'startedAtUTC':utc(),'startedAtUnix':time.time(),'bothPrimaryLoopsEndUnix':barrier,'primarySeals':{sid:read(R/'private/submissions'/sid/'final-corpus-seal.json')['sealedAtUTC']for sid in ids},'sourceSlots':'Same two dedicated simulators, one iOS and one Android worker per source; baseline v4 D0 completes on both platforms before exact FINAL source installation.','runs':[]};assert record['startedAtUnix']>=barrier;save(output,record)
 print(json.dumps({'event':'both_primary_loops_complete_audits_start','atUTC':utc()}),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
  a=pool.submit(baseline);b=pool.submit(collect,'submission-3d6389','d0','common-v3','audit-3d6389','9D4C16CE-714A-4FB2-9102-9AA15396D9F5','audit-v3-d0')
  record['runs']=a.result()+[b.result()]
 record.update(finishedAtUTC=utc(),finishedAtUnix=time.time());save(output,record);print(json.dumps({'event':'all_experiment_native_audits_complete','atUTC':utc()}),flush=True)
if __name__=='__main__':main()
