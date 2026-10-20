#!/usr/bin/env python3
"""Audit transported claims against original-only artifacts after reveal."""
import json
from pathlib import Path
import experiment as ex
import prepare_claims as transport
R=Path(__file__).resolve().parent
def key(c):return json.dumps({k:c.get(k)for k in ['case','platform','state','requirement','expected','unit','status']},sort_keys=True)
def main():
 ex.gate.verify(R/'gates','reveal',R);assignment=ex.read(R/'private/assignment.json');total=0
 for task,aliases in assignment['gradeAliases'].items():
  for alias,unit in aliases.items():
   base=R/'submissions'/unit;delivered=ex.read(R/'evaluation-inputs/selfreview'/task/alias/'claims.json');expected=[]
   for case in ['P1','P2']:
    for platform in ['ios','android']:
     plan=ex.read(base/'initial-agent-output/plans'/case/platform/'plan.json');by={r['id']:r for r in plan['assertions']};rp=base/'own-checks/d0'/case/platform/'report.json'
     if not rp.is_file():continue
     for i,row in enumerate(ex.read(rp)['assertions']):
      if row['status']!='failed'or by[row['id']]['kind']=='manual':continue
      spec=by[row['id']];expected.append(dict(case=case,platform=platform,state=spec['state'],requirement=spec.get('requirement_id',row['id'].split('/')[-1]),expected=spec['expected'],unit=spec.get('unit'),status='F',typed_pointer='/assertions/'+str(i),original_assertion=row,original_plan=spec))
   assert len(expected)==len(delivered['machine'])
   for original,claim in zip(expected,delivered['machine']):
    for k,v in original.items():assert claim[k]==v,(unit,k)
   typed={key(c)for c in delivered['machine']};originals=ex.read(base/'original-review/review.json')['findings'];seen=set()
   for category in ['manual','ineligible_or_qualitative','non_failure_claims','duplicates_of_original_typed_failure']:
    for c in delivered[category]:
     if'original_finding_index'not in c:assert c['origin']=='machine_check_error';continue
     index=c['original_finding_index'];assert index not in seen;seen.add(index);f=originals[index];assert c['original']==f
     for k in ['case','platform','state','unit']:
      assert(k in c)==(k in f)
      if k in f:assert c[k]==f[k]
     assert c['requirement']==f.get('requirement_id',f.get('requirement',f.get('aspect')))
     assert c['status']=={'failed':'F','unassessed':'U','passed':'P'}.get(f.get('status'),f.get('status'))
     assert('expected'in c)==('expected'in f)
     if'expected'in f:assert c['original_expected']==f['expected']and c['expected']==transport.normalize(f['expected'],c.get('unit'))
     assert len(c['evidence_validation'])==len(f.get('evidence',[]))
     for proof,original in zip(c['evidence_validation'],f.get('evidence',[])):
      assert all(proof[k]==v for k,v in original.items())
      path=R/proof['relative_path'];original_path=path
      # Original auxiliary review evidence already exists byte-exact inside the
      # pre-repair sealed review capsule. Never require omitted SDK workspaces.
      prefix=R/'cache'/unit/'agent-output/review'
      if path.is_relative_to(prefix):
       path=R/'submissions'/unit/'original-review'/path.relative_to(prefix)
       assert path.is_file()and ex.sha(path)==proof.get('sha256'),'Missing original sealed auxiliary evidence'
      valid=path.is_file()and path.is_relative_to(R)and ex.sha(path)==proof.get('sha256')
      capture=original_path.is_relative_to(R/'own-corpora'/unit/'d0')and(original_path.suffix=='.png'or original_path.name=='observation.json')
      assert proof['valid']==valid and proof['original_capture']==capture
     if category=='manual':assert c['status']=='F'and key(c)not in typed and all(p['valid']for p in c['evidence_validation'])and any(p['original_capture']for p in c['evidence_validation'])
     if category=='non_failure_claims':assert c['status']=='P'
     if category=='duplicates_of_original_typed_failure':assert c['status']=='F'and key(c)in typed
   assert seen=={i for i,f in enumerate(originals)if f.get('origin')!='original_typed_native_check'and not f.get('duplicate_of_original_typed_failure')}
   total+=len(delivered['machine'])+len(seen)
 print(json.dumps({'status':'PASS','originalClaimsAndNonfailureRecordsAudited':total,'retroactiveExpectedOrStateExpansion':False}))
if __name__=='__main__':main()
