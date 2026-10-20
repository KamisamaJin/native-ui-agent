#!/usr/bin/env python3
"""Read-only preflight of already all-task sealed D0; no assignment access."""
import importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));import experiment as ex
ex.gate.verify(R/'gates','grade-d0',R);n=0
for task in ['T1','T2','T3']:
 spec=importlib.util.spec_from_file_location('d0_'+task,R/'design-v2'/task/'private/grader.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
 for source in ex.read(R/'evaluation-inputs/D0'/task/'batch.json')['corpora']:
  for case in ['P1','P2']:
   for platform in ['ios','android']:
    base=R/'evaluation/D0'/task/source['anonymousID']/case/platform;op=R/source['captures']/platform/case/'observation.json';native=g.grade(case,platform,op);assert native==ex.read(base/'native-base-grade.json')
    manual=base/'manual.json';got=g.grade(case,platform,op,manual=manual if manual.is_file()else None,source_root=R/source['sourceCapsule']/'source');saved=ex.read(base/'grade.json')
    for key in got:
     if key!='api_checks':assert got[key]==saved[key],(task,source['anonymousID'],case,platform,key)
    n+=1
print(json.dumps({'status':'PASS','sealedD0NativeAndVisualGradesReplayed':n,'changedGrades':0,'assignmentRead':False}))
