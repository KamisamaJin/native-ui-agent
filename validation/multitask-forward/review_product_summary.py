#!/usr/bin/env python3
"""Aggregate already sealed independent product dispositions; no reclassification."""
import argparse,json
from pathlib import Path
import experiment as ex
import metrics as m
R=Path(__file__).resolve().parent
# Three independently authored output schemas; these are JSON field adapters only.
FIELDS={'T1':['origins','{origin}','confirmed_product_metrics','counts'],'T2':['origin_metrics','{origin}','product_metrics','unique_claim_counts'],'T3':['detection','{origin}','product_claim_metrics']}
def build():
 ex.gate.verify(R/'gates','reveal',R);a=ex.read(R/'private/assignment.json');primary=ex.read(R/'metrics.json');tasks={};groups={k:[]for k in ['baseline-v6','candidate-v7']}
 for t,aliases in a['gradeAliases'].items():
  p=R/'evaluation/selfreview'/t/'comparison.json';raw=ex.read(p);tasks[t]={}
  for alias,unit in aliases.items():
   original=ex.read(R/'evaluation-inputs/selfreview'/t/alias/'claims.json');value={'tool':a['units'][unit]['tool'],'source':str(p.relative_to(R)),'sourceSHA256':ex.sha(p),'origins':{}}
   for origin in ['machine','manual','combined']:
    data=raw['sources'][alias]
    for key in FIELDS[t]:data=data[origin if key=='{origin}'else key]
    c={k:data[k]for k in ['TP','FP','U']};assert all(isinstance(n,int)and n>=0 for n in c.values())
    q=len(original['ineligible_or_qualitative'])if origin!='machine'else 0;n=sum(c.values())+q;u=c['U']+q
    value['origins'][origin]={'sealedEligibleClaimDispositions':c,'additionalQualitativeUnknown':q,'conditionalFalseDiscoveryRatio':m.ratio(c['FP'],c['TP']+c['FP']),'allClaimErrorBounds':[m.ratio(c['FP'],n),m.ratio(c['FP']+u,n)],'classicalFPR':None,'frozenDeterministicIdentityLedger':primary['tasks'][t][alias]['detection'][origin]['counts']}
   tasks[t][alias]=value;groups[value['tool']].append(value)
 pooled={}
 for tool,vv in groups.items():
  pooled[tool]={}
  for origin in ['machine','manual','combined']:
   cs=[v['origins'][origin]for v in vv];c={k:sum(x['sealedEligibleClaimDispositions'][k]for x in cs)for k in ['TP','FP','U']};q=sum(x['additionalQualitativeUnknown']for x in cs);n=sum(c.values())+q
   pooled[tool][origin]={'sealedEligibleClaimDispositions':c,'additionalQualitativeUnknown':q,'conditionalFalseDiscoveryRatio':m.ratio(c['FP'],c['TP']+c['FP']),'allClaimErrorBounds':[m.ratio(c['FP'],n),m.ratio(c['FP']+c['U']+q,n)],'classicalFPR':None}
 return {'unscoredGraderDisagreementAudit':{'path':'grader-disagreements.json','sha256':ex.sha(R/'grader-disagreements.json'),'warning':'Two original grader-labelled FP have contradictory original pixel evidence; actual product false-alarm truth needs external adjudication. No label changed.'},'schemaFieldAdapters':FIELDS,'tasks':tasks,'pooled':pooled,'scope':'Summary of ORIGINAL already sealed independent selfreview product-disposition judgments, as requested before grading. No original claim/expected/unit is repaired; no new TP or row/cluster recall credit. Identity-rejected semantically compatible or unmapped claims may remain product U, rather than confirmed false alarms. The separately frozen deterministic identity ledger is preserved in metrics.json and shown alongside. This summary does not replace that ledger, rejudge any claim or provide a complete true-negative universe. Posthoc shared environment rescoring does not revise these original dispositions.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();v=build();out=R/'review-product-summary.json'
 if a.write:assert not out.exists();ex.save(out,v)
 else:assert ex.read(out)==v
 print(json.dumps({'status':'PASS','pooled':v['pooled']}))
if __name__=='__main__':main()
