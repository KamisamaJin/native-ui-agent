#!/usr/bin/env python3
"""Expand sealed member directories for cohort_gate; leave dispatched helper immutable."""
import json,time
from pathlib import Path
import supplement as s
R=Path(__file__).resolve().parent
members={}
for task in ['T1','T2','T3']:
 root=R/'supplement'/task
 assert s.ex.read(root/'SEAL.json')['files']==s.inventory(root,'SEAL.json'),task
 members[task]=['supplement/'+task+'/'+p for p in sorted(s.inventory(root))]
s.ex.gate.seal(s.REG,'graded',members,R)
print('All THREE posthoc task outputs sealed over exact file inventories')
