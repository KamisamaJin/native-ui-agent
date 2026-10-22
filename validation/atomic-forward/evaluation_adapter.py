#!/usr/bin/env python3
"""Transport anonymous original artifacts into the pre-frozen shared evaluator.

No expected values, verdict rules or metrics are supplied by this adapter.
"""
import argparse,json,sys,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'candidate-v8/scripts'))
import design_contract as d,review_contract as review,native_checks as native,acceptance

def table(root):return{str(p.relative_to(root)):ex.sha(p)for p in sorted(root.rglob('*'))if p.is_file()and'__pycache__'not in p.parts and p.name!='DELIVERY-SEAL.json'}
def verify_delivery(root):
 for rel,h in ex.read(root/'DELIVERY-SEAL.json')['files'].items():assert ex.sha(root/rel)==h,rel
 for meta in root.rglob('inputs.json'):
  for rel,h in ex.read(meta)['original_files'].items():assert ex.sha(R/rel)==h,rel

def prepare(phase):
 receipt=ex.gate.authorize(R/'gates','own-final'if phase=='d0'else'grade-d0',R)
 assignment=ex.read(R/'private/assignment.json');design=R/ex.read(R/'DESIGN-ROOT.json')['directory'];out=R/'evaluation-inputs'/phase;assert not out.exists();out.mkdir(parents=True)
 for task,aliases in assignment['gradeAliases'].items():
  for alias,unit in aliases.items():
   cases=['P1','P2']if phase=='d0'else['P1','P2','H1']
   for case in cases:
    scope=design/task/('private'if case=='H1'else'public');approval=ex.read(scope/'approval.json')
    compiled=scope/'compiled'/case
    for pl in ['ios','android']:
     dest=out/task/alias/pl/case;dest.mkdir(parents=True)
     raw=R/'common-corpora'/task/alias/phase/pl/case;obpath=raw/'observation.json'
     plan=ex.read(compiled/pl/'plan.json');lock=ex.read(scope/'design-lock.json');policy=ex.read(scope/'policy.json')
     if obpath.is_file():observation=ex.read(obpath);obs_sha=ex.sha(obpath)
     else:
      observation={'snapshots':[],'state_captures':[],'capture_failure':'No observation produced; see original SDK command/log. Not fabricated native evidence.'}
      ex.save(dest/'missing-observation.json',observation);obpath=dest/'missing-observation.json';obs_sha=ex.sha(obpath)
     cat=review.catalog(plan,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'],pl)
     request={'version':1,'catalog_sha256':d.digest(cat),'observation_sha256':obs_sha,'decisions':[]}
     manual=review.bind(plan,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'],observation,obs_sha,raw,request,pl)
     automatic=native.evaluate(plan,observation,pl,manual,raw,obs_sha,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'])
     envpath=scope/('compiled/H1'if case=='H1'else'cases/'+case)/('environment.'+pl+'.json')
     if not envpath.is_file():envpath=scope/'cases'/case/('environment.'+pl+'.json')
     expected_env=ex.read(envpath);envsha=approval['environment_sha256'][case][pl];assert d.digest(expected_env)==envsha
     ex.save(dest/'plan.json',plan);ex.save(dest/'catalog.json',dict(cat,catalog_sha256=d.digest(cat)));ex.save(dest/'automatic.json',automatic);ex.save(dest/'environment-check.json',acceptance.environment(observation,expected_env,pl))
     capsule=R/'submissions'/unit/('d0'if phase=='d0'else'final');original_files={str(p.relative_to(R)):ex.sha(p)for folder in [scope,raw,capsule]for p in folder.rglob('*')if p.is_file()and'__pycache__'not in p.parts}
     ex.save(dest/'inputs.json',{'original_files':original_files,'task':task,'source':alias,'platform':pl,'case':case,'phase':phase,'root':str(raw.relative_to(R)),'observation':str(obpath.relative_to(R)),'observation_sha256':obs_sha,'design_root':str(scope.relative_to(R)),'approval':approval,'environment':str(envpath.relative_to(R)),'source_capsule':str((R/'submissions'/unit/('d0'if phase=='d0'else'final')/'source').relative_to(R))})
     # Independent context fills only scoped qualitative actuals plus separate failure causes.
     ex.save(dest/'judge-template.json',{'review':request,'attributions':[]})
 ex.save(out/'DELIVERY-SEAL.json',{'sealedAtUnix':time.time(),'authorization':receipt,'adapterSHA256':ex.sha(Path(__file__)),'files':table(out)})
 print('Prepared anonymous sealed input:',phase)

def panel_report(phase,task,alias,pl,case,one,two):
 base=R/'evaluation-inputs'/phase/task/alias/pl/case;meta=ex.read(base/'inputs.json');scope=R/meta['design_root'];approval=meta['approval'];op=R/meta['observation'];assert ex.sha(op)==meta['observation_sha256']
 return acceptance.evaluate(ex.read(base/'plan.json'),ex.read(scope/'design-lock.json'),approval['design_lock_sha256'],ex.read(scope/'policy.json'),approval['policy_sha256'],ex.read(op),meta['observation_sha256'],R/meta['root'],pl,ex.read(R/meta['environment']),ex.read(one),ex.read(two))

def close_panel(phase,panel):
 required=('own-final'if phase=='d0'else'grade-d0')if panel=='one'else'grade-'+phase+'-one'
 ex.gate.authorize(R/'gates',required,R);verify_delivery(R/'evaluation-inputs'/phase)
 root=R/'judgments'/phase/panel;members={}
 for task in ['T1','T2','T3']:
  dest=root/task;assert(dest/'phase.json').is_file()and(dest/'SEAL.json').is_file()
  seal=ex.read(dest/'SEAL.json');assert seal['files']=={k:v for k,v in table(dest).items()if k!='SEAL.json'}
  checks=[]
  for base in sorted((R/'evaluation-inputs'/phase/task).glob('*/*/*')):
   if not(base/'inputs.json').is_file():continue
   alias,pl,case=base.parts[-3:];path=dest/alias/pl/case/'judge.json';report=panel_report(phase,task,alias,pl,case,path,path);checks.append({'source':alias,'platform':pl,'case':case,'schemaValidated':True,'counts':report['counts']})
  checkpath=R/'operators'/('judge-'+phase+'-'+panel+'-'+task+'-schema.json');ex.save(checkpath,{'atUnix':time.time(),'checks':checks});members[task]=[str(dest.relative_to(R)),str(checkpath.relative_to(R))]
 manifest=R/'operators'/('grade-'+phase+'-'+panel+'-members.json');ex.save(manifest,members)
 import subprocess
 subprocess.run([sys.executable,'-B',str(R/'seal_stage.py'),'grade-'+phase+'-'+panel,'--members',str(manifest)],check=True,stdout=subprocess.DEVNULL)
 print('Closed complete independent panel',phase,panel)

def merge(phase):
 ex.gate.authorize(R/'gates','grade-'+phase+'-two',R);verify_delivery(R/'evaluation-inputs'/phase);root=R/'evaluation'/phase;assert not root.exists();members={}
 for task in ['T1','T2','T3']:
  for base in sorted((R/'evaluation-inputs'/phase/task).glob('*/*/*')):
   if not(base/'inputs.json').is_file():continue
   alias,pl,case=base.parts[-3:];panels=[R/'judgments'/phase/v/task/alias/pl/case/'judge.json'for v in ['one','two']];report=panel_report(phase,task,alias,pl,case,*panels)
   ex.save(root/task/alias/pl/case/'acceptance.json',report)
  members[task]=[str((root/task).relative_to(R))]
 manifest=R/'operators'/('grade-'+phase+'-members.json');ex.save(manifest,members)
 import subprocess
 subprocess.run([sys.executable,'-B',str(R/'seal_stage.py'),'grade-'+phase,'--members',str(manifest)],check=True,stdout=subprocess.DEVNULL)
 print('Merged pre-frozen evaluator and sealed complete stage',phase)

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','close','merge']);p.add_argument('phase',choices=['d0','final']);p.add_argument('--panel',choices=['one','two']);a=p.parse_args()
 if a.command=='prepare':prepare(a.phase)
 elif a.command=='close':assert a.panel;close_panel(a.phase,a.panel)
 else:merge(a.phase)
if __name__=='__main__':main()
