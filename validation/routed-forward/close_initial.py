#!/usr/bin/env python3
"""Close one authored source, clone exact bytes, seal all members before D0."""
import shutil,time
import study as s
R=s.R
s.tool_verify();s.gate.authorize(R/'gates','design-approved',R)
w=R/'cache/initial';s.host_verify(w);stock=s.read(R/'operators/stock-production.json')['files'];current=s.fingerprint(w)
approval=s.read(R/'design/public/approval.json');allowed=[('alerttoast/'if pl=='ios'else'reply/Reply/')+p for pl,paths in approval['production_paths'].items()for p in paths]
changed={k for k in set(stock)|set(current)if stock.get(k)!=current.get(k)};assert changed==set(allowed),'Exactly the new approved component files are required'
assert(w/'agent-output/initial.json').is_file();s.capsule(w,R/'submissions/initial');shutil.copytree(w/'agent-output',R/'submissions/initial-author-output')
assignment=s.read(R/'private/assignment-draft.json')
for unit,cfg in assignment['units'].items():
 target=R/'cache'/unit;s.host_verify(target)
 for rel in allowed:dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(w/rel,dest)
 assert s.fingerprint(target)==current
 s.capsule(target,R/'submissions'/unit/'initial');cfg['allowed_paths']=allowed
s.save(R/'private/assignment.json',dict(assignment,completedAtUnix=time.time()))
s.save(R/'operators/initial-closed.json',{'closedAtUnix':time.time(),'changed_files':sorted(changed),'initialSealSHA256':s.sha(R/'submissions/initial/seal.json'),'scope':'One natural initial source version, copied byte-identically before D0; no injected edits or pre-seal runtime evidence.'})
s.cohort('initial-source',{'shared-initial':[R/'submissions/initial',R/'submissions/initial-author-output'],**{u:[R/'submissions'/u/'initial']for u in assignment['units']}})
print('Initial and both identical source members closed')
