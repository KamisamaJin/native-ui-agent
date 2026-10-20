#!/usr/bin/env python3
"""Two native slots; each unit is authorized before source restore and SDK launch."""
import argparse,concurrent.futures,json,queue,subprocess,sys,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['own-D0','own-FINAL','common-D0','common-FINAL','paired-D0']);a=p.parse_args()
 assignment=ex.read(R/'private/assignment.json');devices=ex.read(R/'operators/simulators.json')['devices'];own=a.phase.startswith('own-');phase='final'if a.phase.endswith('FINAL')else'd0'
 required={'own-D0':'d0-sources','own-FINAL':'final-sources','common-D0':'d0-sources','common-FINAL':'hidden-inputs','paired-D0':'own-final'}[a.phase]
 ex.gate.authorize(R/'gates',required,R)
 slots=queue.Queue()
 for slot in ['a','b']:slots.put(slot)
 def work(unit):
  slot=slots.get()
  try:
   data=assignment['units'][unit];task=data['task'];caps=R/'submissions'/unit/phase;public=R/json.loads((R/'DESIGN-ROOT.json').read_text())['directory']/task/'public';alias=next(k for k,u in assignment['gradeAliases'][task].items()if u==unit)
   if own:
    w=R/'cache'/unit;tool=data['tool'];inputs=public/'cases';archive=R/'own-corpora'/unit/phase
   else:
    w=R/'cache'/('audit-'+slot);ex.restore(caps,w);tool='baseline-v6'if a.phase=='paired-D0'else'candidate-v7';inputs=(R/'private/common-inputs-final'/task)if phase=='final'else public/'compiled';archive=(R/'paired-corpora'/task/alias/'v6')if a.phase=='paired-D0'else(R/'common-corpora'/task/alias/phase)
   cmd=[sys.executable,'-B',str(R/'experiment.py'),'collect','--workspace',str(w),'--capsule',str(caps),'--required-stage',required,'--tool',tool,'--inputs',str(inputs),'--bridges',str(public),'--simulator',devices[('own-'if own else'audit-')+slot],'--output',str(R/'cache/runs'/a.phase/unit),'--archive',str(archive),'--phase',a.phase]
   if own:cmd+=['--own-plans',str(R/'submissions'/unit/'initial-agent-output/plans')]
   row={'unit':unit,'task':task,'slot':slot,'phase':a.phase,'argv':cmd,'startedAtUnix':time.time()};path=R/'operators'/(a.phase+'-'+unit+'.json');ex.save(path,row)
   with(R/'operators'/(a.phase+'-'+unit+'.log')).open('w')as stream:code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT).returncode
   row.update(exitCode=code,finishedAtUnix=time.time());ex.save(path,row)
   assert code==0,'Wrapper failed; preserve this attempt and investigate without overwriting'
   c=ex.read(archive/'corpus.json');expected=['H1','P1','P2']if a.phase=='common-FINAL'else['P1','P2']
   assert set(c['platformRuns'])=={'ios','android'}
   for platform,rows in c['platformRuns'].items():assert sorted(r['case']for r in rows)==expected
   print(json.dumps({'phase':a.phase,'unit':unit,'slot':slot,'nativeNonzeroExits':sum(r['exitCode']!=0 for rows in c['platformRuns'].values()for r in rows),'wallSeconds':row['finishedAtUnix']-row['startedAtUnix']}),flush=True)
   return row
  finally:slots.put(slot)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(work,assignment['units']))
 ex.save(R/'operators'/(a.phase+'-batch.json'),{'phase':a.phase,'runs':rows,'finishedAtUnix':time.time()})
if __name__=='__main__':main()
