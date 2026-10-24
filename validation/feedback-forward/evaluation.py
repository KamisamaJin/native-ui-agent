#!/usr/bin/env python3
"""Anonymous original-image delivery and unchanged shared acceptance replay."""
import argparse,time
from pathlib import Path
import study as s
import design_contract as d,native_checks as native,review_contract as review,acceptance
R=s.R

def prepare(phase):
 s.gate.authorize(R/'gates','hidden'if phase=='d0'else'grade-d0-two',R)
 assignment=s.read(R/'private/assignment.json');out=R/'evaluation-inputs'/phase;assert not out.exists()
 for task in ['T1','T2']:
  sources={'initial':None}if phase=='d0'else assignment['gradeAliases'][task]
  for alias,unit in sources.items():
   for case in (['P1','P2']if phase=='d0'else['P1','P2','H1']):
    scope=R/'design'/task/('private'if case=='H1'else'public');approval=s.read(scope/'approval.json');lock=s.read(scope/'design-lock.json');policy=s.read(scope/'policy.json')
    for pl in ['ios','android']:
     raw=R/'corpora'/task/'d0'/pl/case/'native'if phase=='d0'else R/'corpora'/unit/('hidden'if case=='H1'else'final-public')/pl/case/'native'
     observation_path=raw/'observation.json';base=out/task/alias/pl/case;plan=s.read(scope/'compiled'/case/pl/'plan.json')
     if observation_path.is_file():observation=s.read(observation_path);obs_sha=s.sha(observation_path)
     else:
      observation={'snapshots':[],'state_captures':[],'capture_failure':'No native observation; original failed SDK log is preserved. This is an empty missing-evidence record.'};s.save(base/'missing-observation.json',observation);observation_path=base/'missing-observation.json';obs_sha=s.sha(observation_path)
     cat=review.catalog(plan,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'],pl);request={'version':1,'catalog_sha256':d.digest(cat),'observation_sha256':obs_sha,'decisions':[]}
     manual=review.bind(plan,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'],observation,obs_sha,raw,request,pl)
     automatic=native.evaluate(plan,observation,pl,manual,raw,obs_sha,lock,approval['design_lock_sha256'],policy,approval['policy_sha256'])
     env=scope/'cases'/case/('environment.'+pl+'.json');assert d.digest(s.read(env))==approval['environment_sha256'][case][pl]
     capsule=R/'submissions'/(task if phase=='d0'else unit)/('d0'if phase=='d0'else'final')
     for name,value in [('plan.json',plan),('catalog.json',dict(cat,catalog_sha256=d.digest(cat))),('automatic.json',automatic),('environment-check.json',acceptance.environment(observation,s.read(env),pl)),('judge-template.json',{'review':request,'attributions':[]})]:s.save(base/name,value)
     s.save(base/'inputs.json',{'phase':phase,'task':task,'source':alias,'platform':pl,'case':case,'scope':str(scope.relative_to(R)),'raw':str(raw.relative_to(R)),'observation':str(observation_path.relative_to(R)),'observation_sha256':obs_sha,'capsule':str((capsule/'source').relative_to(R)),'source_seal_sha256':s.sha(capsule/'seal.json'),'approval':approval,'environment':str(env.relative_to(R)),'original_files':{str(p.relative_to(R)):s.sha(p)for folder in [scope,raw,capsule]for p in sorted(folder.rglob('*'))if p.is_file()and'__pycache__'not in p.parts}})
 s.seal_dir(out)

def report(phase,task,alias,pl,case,first,second):
 base=R/'evaluation-inputs'/phase/task/alias/pl/case;meta=s.read(base/'inputs.json');scope=R/meta['scope'];approval=meta['approval'];op=R/meta['observation'];assert s.sha(op)==meta['observation_sha256']
 return acceptance.evaluate(s.read(base/'plan.json'),s.read(scope/'design-lock.json'),approval['design_lock_sha256'],s.read(scope/'policy.json'),approval['policy_sha256'],s.read(op),meta['observation_sha256'],R/meta['raw'],pl,s.read(R/meta['environment']),s.read(first),s.read(second))

def close(phase,panel):
 previous=('hidden'if phase=='d0'else'grade-d0-two')if panel=='one'else'grade-'+phase+'-one';s.gate.authorize(R/'gates',previous,R);s.verify_dir(R/'evaluation-inputs'/phase)
 members={}
 for task in ['T1','T2']:
  out=R/'judgments'/phase/panel/task;s.verify_dir(out)
  for base in sorted((R/'evaluation-inputs'/phase/task).glob('*/*/*')):
   if not(base/'inputs.json').is_file():continue
   alias,pl,case=base.parts[-3:];path=out/alias/pl/case/'judge.json';report(phase,task,alias,pl,case,path,path)
  members[task]=[out]
 s.cohort('grade-'+phase+'-'+panel,members)
 if panel=='two':
  for task in ['T1','T2']:
   for base in sorted((R/'evaluation-inputs'/phase/task).glob('*/*/*')):
    if not(base/'inputs.json').is_file():continue
    alias,pl,case=base.parts[-3:];paths=[R/'judgments'/phase/p/task/alias/pl/case/'judge.json'for p in ['one','two']]
    s.save(R/'evaluation'/phase/task/alias/pl/case/'acceptance.json',report(phase,task,alias,pl,case,*paths))

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','close']);p.add_argument('phase',choices=['d0','final']);p.add_argument('--panel',choices=['one','two']);a=p.parse_args()
 prepare(a.phase)if a.command=='prepare'else close(a.phase,a.panel)
if __name__=='__main__':main()
