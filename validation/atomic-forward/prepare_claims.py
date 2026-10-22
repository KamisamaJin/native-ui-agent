#!/usr/bin/env python3
"""Transport original claims unchanged; establish possible scope from original identities only.

No later acceptance verdict or repair outcome supplies a claim's expectation/scope.
"""
import json,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent

def main():
 receipt=ex.gate.authorize(R/'gates','grade-final',R);assignment=ex.read(R/'private/assignment.json');design=R/ex.read(R/'DESIGN-ROOT.json')['directory'];out=R/'evaluation-inputs/claims';assert not out.exists();out.mkdir(parents=True)
 for task,aliases in assignment['gradeAliases'].items():
  for alias,unit in aliases.items():
   base=R/'submissions'/unit;claims=[];annotations=[];original_files={}
   def add(row,origin,pointer,path,case=None,platform=None):
    case=row.get('case',case);platform=row.get('platform',platform);state=row.get('state');rid=row.get('requirement_id',row.get('requirement'))
    scope=[];plan=None
    if case in ['P1','P2']and platform in ['ios','android']:
     plan=ex.read(design/task/'public/compiled'/case/platform/'plan.json');ids={r['id']:r for r in plan['assertions']}
     exact=row.get('id')
     if exact in ids:scope=[case+'/'+platform+'/'+exact]
     else:
      # Broad legacy findings retain broad possible original STATE scope. The
      # independent claim judges must justify each supported semantic row; an
      # unresolved state retains the original case/platform upper bound instead
      # of becoming an automatic descriptor rejection. This
      # list is not credit and does not use later truth or expand to hidden data.
      selected=[r for r in plan['assertions']if r['state']==state]if state in plan['matrix_contract']['selected_states']else list(plan['assertions'])
      if rid in plan['matrix_contract']['selected_requirements']:selected=[r for r in selected if r['requirement_id']==rid]
      scope=[case+'/'+platform+'/'+r['id']for r in selected]
    original_plan=None
    if origin=='machine'and case in ['P1','P2']and platform in ['ios','android']:
     original_plan=next((r for r in ex.read(base/'initial-agent-output/plans'/case/platform/'plan.json')['assertions']if r['id']==row.get('id')),None)
    status={'F':'failed','P':'passed','U':'unassessed'}.get(row.get('status'),row.get('status','unassessed'))
    cid=alias+'-'+str(len(claims)).zfill(4)
    claims.append({'claim_id':cid,'origin':origin,'original_status':status,'original_scope':scope,'original':row,'original_plan':original_plan,'original_json':str(path.relative_to(R)),'original_pointer':pointer,'case':case,'platform':platform,'state':state,'requirement':rid,'observation_root':str((R/'own-corpora'/unit/'d0'/platform/case).relative_to(R))if case in ['P1','P2']and platform in ['ios','android']else None})
   for case in ['P1','P2']:
    for platform in ['ios','android']:
     folder=base/'own-checks/d0'/case/platform;rp=folder/'report.json'
     if not rp.is_file():rp=folder/'bound/report.json'
     if rp.is_file():
      for i,row in enumerate(ex.read(rp)['assertions']):add(row,'machine','/assertions/'+str(i),rp,case,platform)
   bound=list((base/'original-review/bound').glob('*/*/findings.json'))
   for fp in sorted(bound):
    case,platform=fp.parts[-3:-1]
    for i,row in enumerate(ex.read(fp)):
     # Recomputed pixels were already available in original machine checks.
     if row.get('aspect','').startswith('rendered_'):continue
     add(row,'manual','/'+str(i),fp,case,platform)
   fp=base/'original-review/review.json';free=ex.read(fp)
   for i,row in enumerate(free.get('findings',[])):
    # Bound qualitative findings are the original treatment record. A free-form
    # note for that same case/platform/rule is retained separately as an annotation.
    matches=[c for c in claims if c['origin']=='manual'and c['case']==row.get('case')and c['platform']==row.get('platform')and c['state']==row.get('state')and c['requirement']==row.get('requirement_id')and c['original_status']==row.get('status')]
    if bound and matches:
     annotations.append({'original':row,'original_json':str(fp.relative_to(R)),'original_pointer':'/findings/'+str(i),'annotation_of':matches[0]['claim_id'],'reason':'Same state/rule/status restates the sealed bound finding; contradictory statuses remain independent original claims.'});continue
    add(row,'manual','/findings/'+str(i),fp)
   machine={tuple(c['original_scope']):c['claim_id']for c in claims if c['origin']=='machine'and c['original_status']=='failed'and c['original_scope']}
   for c in claims:
    original=c['original']
    if c['origin']=='manual'and c['original_status']=='failed'and tuple(c['original_scope'])in machine and (original.get('origin')=='original_typed_native_check'or original.get('duplicate_of_original_typed_failure')or 'review_id'in original):c['duplicate_of']=machine[tuple(c['original_scope'])]
   for folder in [base/'initial-agent-output/plans',base/'own-checks/d0',base/'original-review',R/'own-corpora'/unit/'d0']:
    original_files.update({str(p.relative_to(R)):ex.sha(p)for p in folder.rglob('*')if p.is_file()and'__pycache__'not in p.parts})
   ex.save(out/task/alias/'claims.json',{'claims':claims,'annotations':annotations,'original_files':original_files,'scope':'Original-only, no expected/unit rewriting or later truth/repair expansion. Candidate scope is an upper bound, not detection credit. All non-failure observations retained.'})
 ex.save(out/'DELIVERY-SEAL.json',{'atUnix':time.time(),'authorization':receipt,'adapterSHA256':ex.sha(Path(__file__)),'files':{str(p.relative_to(out)):ex.sha(p)for p in sorted(out.rglob('*'))if p.is_file()}})
 print('Sealed original anonymous claim transport')
if __name__=='__main__':main()
