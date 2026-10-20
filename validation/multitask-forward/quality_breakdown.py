#!/usr/bin/env python3
"""Strict dispositions and independently confirmed product causes by scope."""
import argparse,collections,json
from pathlib import Path
import experiment as ex
import metrics
R=Path(__file__).resolve().parent
def summarize(rows,summary):
 product=metrics.rowids(summary['product_failure_row_ids']);nonproduct=metrics.rowids(summary['non_product_f_rows']);uncertain=metrics.rowids(summary['uncertain_f_rows']);ids={r['id']for r in rows};clusters=[c for c in summary['defect_clusters']if metrics.rowids(c['fixed_row_ids'])&ids]
 return dict(metrics.coverage(rows),confirmedProductFailureRows=len(product&ids),nonProductFailureRows=len(nonproduct&ids),uncertainFailureCauseRows=len(uncertain&ids),confirmedClustersTouchingScope=len(clusters),categories=dict(collections.Counter(c['category']for c in clusters)),productFailureRowIDs=sorted(product&ids))
def build():
 ex.gate.verify(R/'gates','reveal',R);assignment=ex.read(R/'private/assignment.json');tasks={}
 for task,aliases in assignment['gradeAliases'].items():
  tasks[task]={}
  for alias,unit in aliases.items():
   value={'tool':assignment['units'][unit]['tool'],'stages':{}}
   for stage in ['D0','FINAL']:
    summary=ex.read(R/'evaluation'/stage/task/'summary.json')['sources'][alias];rows=metrics.grade_rows(stage,task,alias);groups={'all':rows,'public':[r for r in rows if r['case']!='H1']}
    if stage=='FINAL':groups['heldout']=[r for r in rows if r['case']=='H1']
    for p in ['ios','android']:groups[p]=[r for r in rows if r['platform']==p]
    for c in sorted({r['class']for r in rows}):groups['class:'+c]=[r for r in rows if r['class']==c]
    api=[];inputs=[]
    paths=list((R/'evaluation'/stage/task/alias).glob('*/*/grade.json'))+list((R/'evaluation'/stage/task/alias).glob('*/*/grade-unavailable.json'))
    for path in sorted(paths):
     grade=ex.read(path);case=grade.get('case',path.parent.parent.name);platform=grade.get('platform',path.parent.name);api += [dict(r,case=case,platform=platform)for r in grade.get('api_checks',[])];inputs += [dict(r,case=case,platform=platform)for r in grade.get('input_checks',[])]
    value['stages'][stage]={'scopes':{k:summarize(v,summary)for k,v in groups.items()},'defectClusters':summary['defect_clusters'],'unassertedScope':summary['unasserted_scope'],'unsupportedScope':summary['unsupported_scope'],'sourceAPIIssues':summary.get('source_api_issues',[]),'sourceAPIChecks':api,'inputChecks':inputs}
   d0=metrics.grade_rows('D0',task,alias);final=metrics.grade_rows('FINAL',task,alias);before={r['id']:r for r in d0};confirmed=set(value['stages']['FINAL']['scopes']['public']['productFailureRowIDs']);value['newlyObservedPublicProductFailureRowsFromPriorPass']=sorted(i for i in confirmed if before[i]['status']=='P');tasks[task][alias]=value
 pooled={}
 for tool in ['baseline-v6','candidate-v7']:
  values=[v for a in tasks.values()for v in a.values()if v['tool']==tool];pooled[tool]={}
  for stage in ['D0','FINAL']:
   pooled[tool][stage]={}
   for scope in ['all','public']+(['heldout']if stage=='FINAL'else[]):
    vv=[v['stages'][stage]['scopes'][scope]for v in values];c={s:sum(v['counts'][s]for v in vv)for s in ['P','F','U','N/A']};app=c['P']+c['F']+c['U'];pooled[tool][stage][scope]={'counts':c,'applicable':app,'unassessedRatio':metrics.ratio(c['U'],app),**{k:sum(v[k]for v in vv)for k in ['confirmedProductFailureRows','nonProductFailureRows','uncertainFailureCauseRows','confirmedClustersTouchingScope']}}
 supplement={}
 for tool in ['baseline-v6','candidate-v7']:
  supplement[tool]={}
  for stage in ['D0','FINAL']:
   records=[]
   for task,aliases in assignment['gradeAliases'].items():
    for alias,unit in aliases.items():
     if assignment['units'][unit]['tool']!=tool:continue
     summary=ex.read(R/'supplement'/task/stage/'summary.json')['sources'][alias];records.append({'task':task,'alias':alias,'counts':summary['counts'],'confirmedProductFailureRows':len(metrics.rowids(summary['product_failure_row_ids'])),'nonProductFailureRows':len(metrics.rowids(summary['non_product_f_rows'])),'uncertainFailureCauseRows':len(metrics.rowids(summary['uncertain_f_rows'])),'confirmedProductClusters':len(summary['defect_clusters'])})
   supplement[tool][stage]={'byTask':records,**{k:sum(x[k]for x in records)for k in ['confirmedProductFailureRows','nonProductFailureRows','uncertainFailureCauseRows','confirmedProductClusters']}}
 return {'tasks':tasks,'pooled':pooled,'separatePosthocSharedCorrectionCauses':supplement,'scope':'Independent cause classification accompanies unmodified strict F statuses. Clusters touching public and heldout scopes can overlap and must not be added. Hidden FINAL has no D0 detection/repair denominator. Newly observed prior-P public rows are not automatically proof of a newly introduced root cause. API/input checks remain outside selected acceptance denominator. No new acceptance cell or expected value is created.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();v=build();out=R/'quality-breakdown.json'
 if a.write:assert not out.exists();ex.save(out,v)
 else:assert ex.read(out)==v
 print(json.dumps({'status':'PASS','pooled':v['pooled']}))
if __name__=='__main__':main()
