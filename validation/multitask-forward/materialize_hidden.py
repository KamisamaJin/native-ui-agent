#!/usr/bin/env python3
"""Materialize heldout SDK inputs only after every public FINAL endpoint."""
import json,shutil,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
receipt=ex.gate.authorize(R/'gates','own-final',R);out=R/'private/common-inputs-final';assert not out.exists();out.mkdir(parents=True);members={}
for task in ['T1','T2','T3']:
 d=R/json.loads((R/'DESIGN-ROOT.json').read_text())['directory']/task
 for case in ['P1','P2']:shutil.copytree(d/'public/compiled'/case,out/task/case)
 shutil.copytree(d/'private/compiled/H1',out/task/'H1')
 ex.save(out/task/'materialization.json',{'materializedAtUnix':time.time(),'authorization':receipt,'scope':'Exact frozen public and heldout inputs copied after six fresh own-FINAL public endpoints; no expected values recomputed.'})
 members[task]=[str(p.relative_to(R))for p in sorted((out/task).rglob('*'))if p.is_file()]
ex.gate.seal(R/'gates','hidden-inputs',members,R);print('Materialized and sealed all three heldout input sets')
