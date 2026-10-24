#!/usr/bin/env python3
"""Root-only actual D0 or heldout collection after the exact complete barrier."""
import argparse
import study as s
R=s.R
import shared_amendment
shared_amendment.verify()
p=argparse.ArgumentParser();p.add_argument('phase',choices=['d0','hidden']);p.add_argument('name');a=p.parse_args()
assignment=s.read(R/'private/assignment.json')
if a.phase=='d0':
 task=a.name;assert task in{'T1','T2'};cfg=next(v for v in assignment['units'].values()if v['task']==task)
 w=R/'cache'/('builder-'+task);source=R/'submissions'/task/'d0/seal.json';scope=R/'design'/task/'public';cases=['P1','P2'];required='d0-sources';out=R/'corpora'/task/'d0'
else:
 cfg=assignment['units'][a.name];task=cfg['task'];w=R/'cache'/a.name;source=R/'submissions'/a.name/'final/seal.json';scope=R/'design'/task/'private';cases=['H1'];required='public-final';out=R/'corpora'/a.name/'hidden'
raw=R/'cache/acquisitions'/a.name/a.phase
s.collect(w,scope,raw,cfg['simulator'],cases=cases,required_stage=required,source_seal=source,phase=a.phase)
s.archive(raw,out)
