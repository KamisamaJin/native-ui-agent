#!/usr/bin/env python3
"""SDK-free immutable oracle replay and anonymous delivery provenance audit."""
import importlib.util,json
from pathlib import Path
import experiment as ex
import metrics
R=Path(__file__).resolve().parent
def files(root):return{str(p.relative_to(root)):ex.sha(p)for p in sorted(root.rglob('*'))if p.is_file()and'__pycache__'not in p.parts}
def check_seal(root,name='SEAL.json'):
 seal=ex.read(root/name);assert seal['files']=={k:v for k,v in files(root).items()if k!=name},root
def main():
 ex.gate.verify(R/'gates','reveal',R);design=R/ex.read(R/'DESIGN-ROOT.json')['directory'];assignment=ex.read(R/'private/assignment.json');replayed=0;rows=0
 for stage in ['D0','FINAL','selfreview','paired-D0']:check_seal(R/'evaluation-inputs'/stage,'DELIVERY-SEAL.json')
 for task,aliases in assignment['gradeAliases'].items():
  spec=importlib.util.spec_from_file_location('independent_'+task,design/task/'private/grader.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
  for stage in ['D0','FINAL','selfreview','paired-D0']:check_seal(R/'evaluation'/stage/task)
  for stage in ['D0','FINAL']:
   delivery=ex.read(R/'evaluation-inputs'/stage/task/'batch.json');assert{c['anonymousID']for c in delivery['corpora']}==set(aliases)
   for source in delivery['corpora']:
    alias=source['anonymousID'];cap=R/source['sourceCapsule'];raw=R/source['captures'];unit=aliases[alias];phase=stage.lower()
    assert ex.sha(cap/'seal.json')==source['sourceSealSHA256']==ex.sha(R/'submissions'/unit/phase/'seal.json')
    assert ex.sha(raw/'portable-sha256.json')==source['portableManifestSHA256']
    for case in delivery['cases']:
     for platform in ['ios','android']:
      out=R/'evaluation'/stage/task/alias/case/platform;op=raw/platform/case/'observation.json'
      if not op.is_file():
       missing=ex.read(out/'grade-unavailable.json');assert all(r['status']in['U','N/A']for r in missing['rows']);continue
      native=g.grade(case,platform,op);assert native==ex.read(out/'native-base-grade.json'),out;assert native['native_report']==ex.read(out/'native-base.json');replayed+=1
      manual=out/'manual.json';accepted=g.grade(case,platform,op,manual=manual if manual.is_file()else None,source_root=cap/'source');saved=ex.read(out/'grade.json')
      # Source-bound human API disposition is separately reported; all actual
      # acceptance, input validity and raw assertions must replay exactly.
      for key in accepted:
       if key!='api_checks':assert accepted[key]==saved[key],(out,key)
      assert all(p['status']in['P','F','U']for p in saved['api_checks'])
      rows+=len(saved['rows'])
    summary=ex.read(R/'evaluation'/stage/task/'summary.json')['sources'][alias];rr=metrics.grade_rows(stage,task,alias);ids={r['id']for r in rr if r['status']=='F'};sets=[metrics.rowids(summary[k])for k in ['product_failure_row_ids','non_product_f_rows','uncertain_f_rows']];assert set.union(*sets)==ids and sum(map(len,sets))==len(ids),(stage,task,alias,'F cause partition')
  batch=ex.read(R/'evaluation-inputs/paired-D0'/task/'batch.json')
  for source in batch['corpora']:
   for record in source['exactCopies']:assert ex.sha(R/record['source'])==ex.sha(R/record['destination'])==record['sha256']
   for case in ['P1','P2']:
    for platform in ['ios','android']:
     raw=R/source['v6Captures']/platform/case/'observation.json';out=R/'evaluation/paired-D0'/task/source['anonymousID']/case/platform
     if raw.is_file():assert g.grade(case,platform,raw)==ex.read(out/'native-grade-v6.json');replayed+=1
 print(json.dumps({'status':'PASS','originalNativeGradesReplayed':replayed,'acceptanceCellsReplayed':rows,'allCausePartitionsAndExactCopies':True}))
if __name__=='__main__':main()
