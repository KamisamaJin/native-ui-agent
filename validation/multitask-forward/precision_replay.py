#!/usr/bin/env python3
"""Preregistered exact-same-frame checkers, separate from native session pairing."""
import json,subprocess,sys,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent

def main():
 receipt=ex.gate.authorize(R/'gates','grade-selfreview',R);assignment=ex.read(R/'private/assignment.json');design=R/ex.read(R/'DESIGN-ROOT.json')['directory'];out=R/'precision-replay';assert not out.exists();out.mkdir(parents=True)
 for task,aliases in assignment['gradeAliases'].items():
  public=design/task/'public';digest=ex.read(public/'approval.json')['design_lock_sha256'];changes=[]
  for alias in aliases:
   for case in ['P1','P2']:
    for platform in ['ios','android']:
     op=R/'common-corpora'/task/alias/'d0'/platform/case/'observation.json';plan=public/'compiled'/case/platform/'plan.json';dest=out/task/alias/case/platform;dest.mkdir(parents=True);commands=[];reports={}
     if not op.is_file():ex.save(dest/'missing.json',{'scope':'No original native observation; no replay or facts invented.'});continue
     original=ex.sha(op)
     for tool in ['baseline-v6','candidate-v7']:
      result=dest/(tool+'.json');cmd=[sys.executable,'-B',str(R/tool/'scripts/native_checks.py'),'--plan',str(plan),'--observation',str(op),'--platform',platform,'--root',str(op.parent),'--design-lock',str(public/'design-lock.json'),'--design-sha256',digest,'--output',str(result)]
      start=time.time()
      with(dest/(tool+'.log')).open('w')as stream:code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT).returncode
      commands.append({'tool':tool,'argv':cmd,'startedAtUnix':start,'finishedAtUnix':time.time(),'exitCode':code,'observationSHA256':original,'planSHA256':ex.sha(plan),'SDKStarted':False});assert code in [0,1,3]and result.is_file();reports[tool]={r['id']:r for r in ex.read(result)['assertions']};assert ex.sha(op)==original
     ex.save(dest/'commands.json',commands)
     for spec in ex.read(plan)['assertions']:
      if spec['kind']!='geometry':continue
      before,after=(reports[t][spec['id']]for t in ['baseline-v6','candidate-v7']);changes.append({'alias':alias,'case':case,'platform':platform,'id':spec['id'],'expected':spec['expected'],'unit':spec['unit'],'op':spec.get('op','eq'),'tolerance':spec.get('tolerance'),'before':before['status'],'after':after['status'],'beforeActual':before['actual'],'afterActual':after['actual'],'observationSHA256':original,'reportPaths':{t:str((dest/(t+'.json')).relative_to(R))for t in reports}})
  ex.save(out/task/'comparison.json',{'authorization':receipt,'geometryRows':changes,'scope':'Exact same original observation and fixed expected/tolerance. Offline checker replay, zero new native commands. All public D0 geometry rows; not selected based on outcomes. Native sessions are reported separately.'})
 print('Completed all three same-frame precision diagnostics')
if __name__=='__main__':main()
