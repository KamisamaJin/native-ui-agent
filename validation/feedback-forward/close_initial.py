#!/usr/bin/env python3
"""Retain each naturally authored initial PR before the complete D0 source barrier."""
import argparse,time
import study as s
R=s.R
import shared_amendment
shared_amendment.verify()
p=argparse.ArgumentParser();p.add_argument('task',choices=['T1','T2']);a=p.parse_args();w=R/'cache'/('builder-'+a.task)
s.gate.authorize(R/'gates','design-review',R);s.tool_verify();s.host_verify(w)
assignment=s.read(R/'private/assignment.json');allowed=set(next(v['allowed_paths']for v in assignment['units'].values()if v['task']==a.task));stock=s.read(R/'operators/stock-production.json')['files'];current=s.fingerprint(w)
changed=sorted(k for k in set(stock)|set(current)if stock.get(k)!=current.get(k));assert set(changed)<=allowed
record=s.read(w/'agent-output/implementation.json');assert all(key in record for key in ['startedAtUnix','finishedAtUnix','changed_files'])
s.capsule(w,R/'submissions'/a.task/'d0');s.shutil.copytree(w/'agent-output',R/'submissions'/a.task/'initial-agent-output')
s.save(R/'submissions'/a.task/'initial-submission.json',{'submittedAtUnix':time.time(),'actualChangedFiles':changed,'authoringWallSeconds':record['finishedAtUnix']-record['startedAtUnix'],'withinBudget':record['finishedAtUnix']-record['startedAtUnix']<=1500,'scope':'One naturally authored initial dual-platform PR, copied byte-exact to both later repair arms; no intentional defect injection or rendering feedback during authoring.'})
print('Initial source retained: '+a.task)
