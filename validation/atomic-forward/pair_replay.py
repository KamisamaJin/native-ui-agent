#!/usr/bin/env python3
"""Prospective same-source, same-original-evidence offline automation diagnostic."""
import subprocess,sys,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent

def main():
 receipt=ex.gate.authorize(R/'gates','grade-selfreview',R);out=R/'evaluation/pair';assert not out.exists();members={}
 for task in ['T1','T2','T3']:
  for alias in ['source-a','source-b']:
   for pl in ['ios','android']:
    for case in ['P1','P2']:
     base=R/'evaluation-inputs/d0'/task/alias/pl/case;meta=ex.read(base/'inputs.json');scope=R/meta['design_root'];dest=out/task/alias/pl/case;dest.mkdir(parents=True);approval=meta['approval'];common=['--plan',str(base/'plan.json'),'--observation',str(R/meta['observation']),'--platform',pl,'--design-lock',str(scope/'design-lock.json'),'--design-sha256',approval['design_lock_sha256']]
     for label in ['v7','v8']:
      if label=='v7':cmd=[sys.executable,'-B',str(R/'baseline-v7/scripts/native_checks.py'),*common,'--root',str(R/meta['root']),'--output',str(dest/'v7-report.json')];report=dest/'v7-report.json'
      else:cmd=[sys.executable,'-B',str(R/'candidate-v8/scripts/review_contract.py'),'review',*common,'--policy',str(scope/'policy.json'),'--policy-sha256',approval['policy_sha256'],'--output',str(dest/'v8-bound')];report=dest/'v8-bound/report.json'
      row={'argv':cmd,'startedAtUnix':time.time(),'originalObservationSHA256':meta['observation_sha256'],'newSDKCommands':0,'qualitativeSubmissions':0}
      with(dest/(label+'.log')).open('w')as stream:row['exitCode']=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT).returncode
      row.update(finishedAtUnix=time.time(),reportExists=report.is_file());ex.save(dest/(label+'-command.json'),row)
     reports=[ex.read(p)if p.is_file()else None for p in [dest/'v7-report.json',dest/'v8-bound/report.json']]
     comparisons=[]
     if all(reports):
      old,new=[{r['id']:r for r in report['assertions']}for report in reports];assert set(old)==set(new)
      for rid in old:comparisons.append({'id':rid,'v7':old[rid]['status'],'v8':new[rid]['status'],'changed':old[rid]['status']!=new[rid]['status']})
     ex.save(dest/'comparison.json',{'counts':{label:report['counts']if report else None for label,report in zip(['v7','v8'],reports)},'rows':comparisons,'scope':'Same original common D0 bytes, no qualitative input and no SDK. Automation coverage only; not development quality or native latency proof.'})
  members[task]=[str((out/task).relative_to(R))]
 path=R/'operators/grade-pair-members.json';ex.save(path,members);subprocess.run([sys.executable,'-B',str(R/'seal_stage.py'),'grade-pair','--members',str(path)],check=True,stdout=subprocess.DEVNULL);print('Closed offline same-evidence diagnostic; assignment still undisclosed')
if __name__=='__main__':main()
