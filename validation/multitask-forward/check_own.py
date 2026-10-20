#!/usr/bin/env python3
"""Run each arm's original, unchanged typed plan on its own actual corpus."""
import argparse,json,subprocess,sys,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('phase',choices=['d0','final']);a=p.parse_args();assignment=ex.read(R/'private/assignment.json')
ex.gate.authorize(R/'gates','d0-sources'if a.phase=='d0'else'final-sources',R)
assert all((R/'own-corpora'/u/a.phase/'corpus-seal.json').is_file()for u in assignment['units']),'All SIX own corpora must seal before typed self-check evaluation'
for unit,config in assignment['units'].items():
 base=R/'submissions'/unit;public=R/json.loads((R/'DESIGN-ROOT.json').read_text())['directory']/config['task']/'public';digest=ex.read(public/'approval.json')['design_lock_sha256'];results=[]
 for case in ['P1','P2']:
  for platform in ['ios','android']:
   plan=base/'initial-agent-output/plans'/case/platform/'plan.json';raw=R/'own-corpora'/unit/a.phase/platform/case;dest=base/'own-checks'/a.phase/case/platform;dest.mkdir(parents=True);output=dest/'report.json'
   cmd=[sys.executable,'-B',str(R/config['tool']/'scripts/native_checks.py'),'--plan',str(plan),'--observation',str(raw/'observation.json'),'--platform',platform,'--root',str(raw),'--design-lock',str(public/'design-lock.json'),'--design-sha256',digest,'--output',str(output)]
   row={'argv':cmd,'startedAtUnix':time.time(),'planSHA256':ex.sha(plan),'observationExists':(raw/'observation.json').is_file()}
   with(dest/'check.log').open('w')as stream:code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT).returncode
   row.update(exitCode=code,finishedAtUnix=time.time(),reportExists=output.is_file());ex.save(dest/'command.json',row);results.append({'case':case,'platform':platform,'exitCode':code,'counts':ex.read(output)['counts']if output.is_file()else None})
 ex.save(base/('own-checks-'+a.phase+'.json'),{'completedAtUnix':time.time(),'originalPlanScope':True,'results':results});print(json.dumps({'unit':unit,'phase':a.phase,'results':results}),flush=True)
