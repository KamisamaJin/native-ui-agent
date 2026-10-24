#!/usr/bin/env python3
"""Byte-identical initial source handoff; editing clock starts only at delivery."""
import argparse,time
import study as s
R=s.R
p=argparse.ArgumentParser();p.add_argument('unit');a=p.parse_args();cfg=s.read(R/'private/assignment.json')['units'][a.unit]
s.gate.authorize(R/'gates','d0-raw',R);s.tool_verify()
w=R/'cache'/a.unit;assert w.resolve().is_relative_to((R/'cache').resolve());s.host_verify(w)
source=R/'submissions'/cfg['task']/'d0';original=s.read(source/'seal.json')['files']
assert not(w/'SESSION.json').exists()
for rel in s.ROOTS:
 if(w/rel).exists():s.shutil.rmtree(w/rel)
for rel,h in original.items():
 assert s.sha(source/'source'/rel)==h
 target=w/rel;target.parent.mkdir(parents=True,exist_ok=True);s.shutil.copy2(source/'source'/rel,target)
assert s.fingerprint(w)==original
(w/'agent-output').mkdir(exist_ok=False)
s.save(w/'SESSION.json',{'unit':a.unit,'handoffAtUnix':time.time(),'initialSourceSealSHA256':s.sha(source/'seal.json'),'initialSourceFiles':original,'editingBudgetSeconds':1200,'maxInnerRequests':2,'noFurtherEditsAfterFinalSeal':True})
s.save(R/'operators'/(a.unit+'-handoff.json'),s.read(w/'SESSION.json'))
print(w)
