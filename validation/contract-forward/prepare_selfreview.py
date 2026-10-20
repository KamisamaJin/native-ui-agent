#!/usr/bin/env python3
"""Deliver sealed original claims without using acceptance values to repair them."""
import hashlib,json,shutil,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
 assert(R/'evaluation/FINAL/SEAL.json').is_file(),'Both FINAL grades must seal first'
 out=R/'evaluation-inputs/selfreview';assert not out.exists();out.mkdir(parents=True)
 for alias,unit in read(R/'private/assignment.json')['gradeAliases'].items():
  base=R/'submissions'/unit;dest=out/alias;dest.mkdir()
  for src,name in [(base/'initial-agent-output/plans','plans'),(base/'original-review','original-review'),(base/'own-checks/d0','typed-reports')]:shutil.copytree(src,dest/name)
  for stage,name in [('D0','d0-grade.json'),('FINAL','final-grade.json')]:
   parts=[read(p)for p in sorted((R/'evaluation'/stage/alias/'final').glob('*/*/grade.json'))];save(dest/name,{'rows':[r for part in parts for r in part['rows']],'checks':[r for part in parts for r in part['checks']],'scope':'Exact immutable independent final case grades, aggregated without rescoring.'})
  effective=read(base/'effective-own-d0.json');machine=[];manual=[];uncertain=[]
  for case in ['P1','P2']:
   for platform in ['ios','android']:
    report=dest/'typed-reports'/case/platform/'report.json';plan=read(dest/'plans'/case/platform/'plan.json');by={x['id']:x for x in plan['assertions']}
    for i,row in enumerate(read(report)['assertions']):
     if row['status']!='failed':continue
     own=by[row['id']]
     if own['kind']=='manual':continue
     machine.append({'case':case,'platform':platform,'state':own.get('state'),'aspect':own.get('requirement_id',own['id'].split('/')[-1]),'expected':own.get('expected'),'unit':own.get('unit'),'origin':'machine','own_assertion_id':row['id'],'typed_report':str(report.relative_to(R)),'typed_pointer':'/assertions/'+str(i),'original_plan':own,'original_assertion':row,'observation':effective['captures'][platform+'/'+case]+'/observation.json'})
  review=read(dest/'original-review/review.json')
  for i,finding in enumerate(review.get('findings',[])):
   if finding.get('origin')=='original_typed_native_check' or finding.get('duplicate_of_original_typed_failure'):continue
   claim={k:finding[k]for k in ['case','platform','state','aspect','expected','unit']if k in finding}
   if finding.get('requirement_id'):claim['aspect']=finding['requirement_id']
   proofs=[]
   for proof in finding.get('evidence',[]):
    original=Path(proof['path']);marker='/validation/contract-forward/';local=R/str(original).split(marker,1)[1]if marker in str(original)else original
    proofs.append(dict(proof,valid=local.is_file()and sha(local)==proof.get('sha256'),local_path=str(local.relative_to(R))if local.is_relative_to(R)else str(local)))
   claim.update(origin='manual',original_finding_index=i,original=finding,evidence_validation=proofs)
   if finding.get('status')=='failed'and proofs and all(p['valid']for p in proofs):manual.append(claim)
   else:claim['ineligible_reason']='Original finding was qualitative/unconfirmed or lacks valid original evidence; retained as uncertainty, never upgraded into a confirmed failure.';uncertain.append(claim)
  save(dest/'claims.json',{'machine':machine,'manual':manual,'ineligible_or_qualitative':uncertain,'scope':'Expectations copied only from sealed own plan/original finding. No grader value fills missing descriptors. Original typed duplicates remain in review but do not inflate manual claims.'})
 files={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()}
 save(out/'batch.json',{'stage':'selfreview','anonymousIDs':['source-a','source-b'],'scope':'Match original-only claims against independently sealed D0 rows; compare D0->FINAL using fixed row IDs. Assignment remains withheld.'})
 files['batch.json']=sha(out/'batch.json');save(out/'DELIVERY-SEAL.json',{'sealedAtUTC':datetime.now(timezone.utc).isoformat(),'sealedAtUnix':time.time(),'files':files})
 print(json.dumps({'stage':'selfreview','files':len(files)}))
if __name__=='__main__':main()
