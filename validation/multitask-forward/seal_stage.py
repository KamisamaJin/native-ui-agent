#!/usr/bin/env python3
"""Seal an exact configured cohort over complete immutable member directories."""
import argparse,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parents[1]/'native-ui-agent/scripts'));import cohort_gate
p=argparse.ArgumentParser();p.add_argument('stage');p.add_argument('--members',type=Path,required=True);a=p.parse_args();members=json.loads(a.members.read_text());expanded={}
for member,paths in members.items():
 files=[]
 for rel in paths:
  path=R/rel
  if path.is_dir():files += [str(f.relative_to(R))for f in sorted(path.rglob('*'))if f.is_file()and'__pycache__'not in f.parts]
  else:files.append(rel)
 expanded[member]=sorted(set(files))
print(json.dumps(cohort_gate.seal(R/'gates',a.stage,expanded,R),indent=2))
