#!/usr/bin/env python3
"""Transport original-only claims after both complete common grade stages."""
import hashlib,json,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent

def normalize(value,unit):
 if unit=='argb'and isinstance(value,str)and len(value)==9 and value.startswith('#'):
  try:return int(value[1:],16)
  except ValueError:pass
 return value
def local(path):
 p=Path(path)
 if p.is_file()and p.resolve().is_relative_to(R):return p.resolve()
 marker='/validation/multitask-forward/'
 return R/str(path).split(marker,1)[1]if marker in str(path)else p

def main():
 receipt=ex.gate.authorize(R/'gates','grade-final',R);assignment=ex.read(R/'private/assignment.json');out=R/'evaluation-inputs/selfreview';assert not out.exists();out.mkdir(parents=True)
 for task,aliases in assignment['gradeAliases'].items():
  for alias,unit in aliases.items():
   base=R/'submissions'/unit;machine=[];manual=[];uncertain=[];nonfailures=[];typed_duplicates=[]
   for case in ['P1','P2']:
    for platform in ['ios','android']:
     plan=ex.read(base/'initial-agent-output/plans'/case/platform/'plan.json');rp=base/'own-checks/d0'/case/platform/'report.json'
     if not rp.is_file():uncertain.append({'origin':'machine_check_error','case':case,'platform':platform,'reason':'Original native check did not produce a report; no failure claim invented.'});continue
     by={r['id']:r for r in plan['assertions']}
     for i,row in enumerate(ex.read(rp)['assertions']):
      if row['status']!='failed':continue
      spec=by[row['id']]
      if spec['kind']=='manual':continue
      machine.append({'case':case,'platform':platform,'state':spec['state'],'requirement':spec.get('requirement_id',row['id'].split('/')[-1]),'expected':spec['expected'],'unit':spec.get('unit'),'status':'F','origin':'machine','original_assertion':row,'original_plan':spec,'typed_report':str(rp.relative_to(R)),'typed_pointer':'/assertions/'+str(i)})
   descriptor=lambda c:json.dumps({k:c.get(k)for k in ['case','platform','state','requirement','expected','unit','status']},sort_keys=True)
   typed_descriptors={descriptor(c)for c in machine}
   original=ex.read(base/'original-review/review.json')
   for i,row in enumerate(original.get('findings',[])):
    if row.get('origin')=='original_typed_native_check'or row.get('duplicate_of_original_typed_failure'):continue
    claim={k:row[k]for k in ['case','platform','state','expected','unit']if k in row};claim.update(requirement=row.get('requirement_id',row.get('requirement',row.get('aspect'))),status={'failed':'F','unassessed':'U','passed':'P'}.get(row.get('status'),row.get('status')),origin='manual',original_finding_index=i,original=row)
    proofs=[]
    for proof in row.get('evidence',[]):
     path=local(proof['path']);proofs.append(dict(proof,relative_path=str(path.relative_to(R))if path.is_relative_to(R)else str(path),valid=path.is_file()and path.is_relative_to(R)and ex.sha(path)==proof.get('sha256'),original_capture=path.is_relative_to(R/'own-corpora'/unit/'d0')and(path.suffix=='.png'or path.name=='observation.json')))
    claim['evidence_validation']=proofs
    if 'expected'in claim:claim['original_expected']=claim['expected'];claim['expected']=normalize(claim['expected'],claim.get('unit'))
    if claim['status']=='P':nonfailures.append(claim)
    elif claim['status']=='F'and descriptor(claim)in typed_descriptors:claim['duplicate_reason']='Exact descriptor already present in original typed failure; no extra manual detection credit.';typed_duplicates.append(claim)
    elif claim['status']=='F'and proofs and all(p['valid']for p in proofs)and any(p['original_capture']for p in proofs):manual.append(claim)
    else:claim['ineligible_reason']='Original qualitative/non-failure finding or no exact original artifact evidence; retained as uncertainty.';uncertain.append(claim)
   ex.save(out/task/alias/'claims.json',{'machine':machine,'manual':manual,'ineligible_or_qualitative':uncertain,'non_failure_claims':nonfailures,'duplicates_of_original_typed_failure':typed_duplicates,'scope':'No acceptance expected value, state expansion or later discovery is used. Exact original-only claims; typed argb representation normalization declared before implementation. Successful observations are retained outside the failure-claim denominator; exact typed duplicates cannot earn extra manual detection credit.'})
 ex.save(out/'DELIVERY-SEAL.json',{'sealedAtUnix':time.time(),'authorization':receipt,'files':{str(p.relative_to(out)):ex.sha(p)for p in sorted(out.rglob('*'))if p.is_file()}});print('Sealed anonymous original claim transports for six sources')
if __name__=='__main__':main()
