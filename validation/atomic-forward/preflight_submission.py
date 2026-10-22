#!/usr/bin/env python3
"""Validate generated source-backed plans and unchanged pinned project settings."""
import argparse,subprocess,sys,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'candidate-v8/scripts'))
import design_contract as d
p=argparse.ArgumentParser();p.add_argument('unit');a=p.parse_args();config=ex.read(R/'private/assignment.json')['units'][a.unit];w=R/'cache'/a.unit;design=R/ex.read(R/'DESIGN-ROOT.json')['directory']/config['task']/'public';approval=ex.read(design/'approval.json');lock=ex.read(design/'design-lock.json');checks=[]
for case in ['P1','P2']:
 for pl in ['ios','android']:
  base=w/'agent-output/plans'/case/pl;plan=ex.read(base/'plan.json');actions=d.verify_generated(plan,lock,approval['design_lock_sha256'],pl);assert d.canonical(actions)==d.canonical(ex.read(base/'actions.json'))
  assert plan['design_contract']['scenario']==case;checks.append({'case':case,'platform':pl,'plan_sha256':ex.sha(base/'plan.json'),'actions_sha256':ex.sha(base/'actions.json'),'verified':True})
settings=[]
pristine=ex.read(R/'operators/pristine-settings.json')['bootstrapTrackedChanges']
for project,prefix in [('alerttoast','Sources/'),('reply','Reply/app/src/main/')]:
 root=w/project;result=subprocess.run(['git','diff','--name-only'],cwd=root,capture_output=True,text=True,check=True)
 for changed in result.stdout.splitlines():
  if changed.startswith(prefix):continue
  assert changed in pristine[project],(project,changed)
  assert ex.sha(root/changed)==pristine[project][changed],(project,changed,'bootstrap settings drift')
 for changed,h in pristine[project].items():assert ex.sha(root/changed)==h
 settings.append({'project':project,'trackedChanges':result.stdout.splitlines(),'nonProductionSettingsValidated':True})
ex.save(R/'operators'/(a.unit+'-initial-preflight.json'),{'atUnix':time.time(),'checks':checks,'settings':settings});print('PASS original source-backed plans and pinned settings:',a.unit)
