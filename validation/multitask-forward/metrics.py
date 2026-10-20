#!/usr/bin/env python3
"""Deterministic post-reveal aggregation; never alters independent dispositions."""
import argparse,collections,json
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
STATUSES=['P','F','U','N/A']
KEY=['case','platform','state','requirement']

def ratio(n,d):return n/d if d else None
def counts(rows):return {s:sum(r['status']==s for r in rows)for s in STATUSES}
def rowids(value):
 return {v if isinstance(v,str)else v.get('id',v.get('row_id'))for v in value}
def grade_rows(stage,task,alias):
 rows=[]
 for p in sorted((R/'evaluation'/stage/task/alias).glob('*/*/grade.json')):rows+=ex.read(p)['rows']
 for p in sorted((R/'evaluation'/stage/task/alias).glob('*/*/grade-unavailable.json')):rows+=ex.read(p)['rows']
 assert len({r['id']for r in rows})==len(rows)
 return rows
def coverage(rows):
 c=counts(rows);app=c['P']+c['F']+c['U'];return dict(counts=c,applicable=app,assessed=c['P']+c['F'],unassessedRatio=ratio(c['U'],app),assessedRatio=ratio(c['P']+c['F'],app))
def detection(rows,summary,claims,qualitative=0):
 index={tuple(r[k]for k in KEY):r for r in rows};product=rowids(summary['product_failure_row_ids']);nonproduct=rowids(summary['non_product_f_rows']);uncertain=rowids(summary['uncertain_f_rows'])
 assert not(product&nonproduct or product&uncertain or nonproduct&uncertain)
 assert product|nonproduct|uncertain=={r['id']for r in rows if r['status']=='F'}
 clusters=summary['defect_clusters'];clusterids={c['cluster_id']for c in clusters};assert len(clusterids)==len(clusters)
 unique={};duplicates=[]
 for origin,claim in claims:
  identity=json.dumps({k:claim.get(k)for k in KEY+['expected','unit','status']},sort_keys=True)
  if identity in unique:duplicates.append({'origin':origin,'claim':claim});continue
  unique[identity]=(origin,claim)
 decisions=[];detected=set()
 for origin,c in unique.values():
  row=index.get(tuple(c.get(k)for k in KEY));verdict='U';reason='Unmapped scope or unknown independent disposition'
  if row:
   if 'expected'not in c or 'unit'not in c:reason='Original claim omitted expected/unit; not repaired after the fact'
   elif c['expected']!=row['expected']or c['unit']!=row['unit']:verdict='FP';reason='Original expected/unit contradicts fixed contract'
   elif c.get('status')!='F':reason='Not an original failure claim'
   elif row['status']=='U':reason='Independent evidence is unassessed'
   elif row['id']in product:verdict='TP';reason='Confirmed natural product contradiction';detected.add(row['id'])
   elif row['status']in ['P','N/A']or row['id']in nonproduct:verdict='FP';reason='Independent pass/N/A or confirmed non-product alarm'
   elif row['id']in uncertain:reason='Failure cause not independently established'
  decisions.append({'origin':origin,'key':{k:c.get(k)for k in KEY},'row_id':row['id']if row else None,'status':verdict,'reason':reason})
 c=collections.Counter(d['status']for d in decisions);u=c['U']+qualitative;n=c['TP']+c['FP']+u
 hitclusters=[x['cluster_id']for x in clusters if rowids(x['fixed_row_ids'])&detected]
 return {'counts':{'TP':c['TP'],'FP':c['FP'],'U':u,'eligibleUniqueClaims':len(decisions),'qualitativeOrIneligible':qualitative,'duplicates':len(duplicates)},'confirmedProductFailureRows':len(product),'detectedProductRows':len(detected),'missedProductRows':sorted(product-detected),'rowRecall':ratio(len(detected),len(product)),'rowMissRate':ratio(len(product-detected),len(product)),'confirmedProductClusters':len(clusterids),'detectedProductClusters':len(hitclusters),'clusterRecall':ratio(len(hitclusters),len(clusterids)),'conditionalFalseDiscoveryRatio':ratio(c['FP'],c['TP']+c['FP']),'allClaimsFalseDiscoveryBounds':[ratio(c['FP'],n),ratio(c['FP']+u,n)],'classicalFalsePositiveRate':None,'decisions':decisions,'duplicates':duplicates}
def repairs(before,after,summary):
 index={r['id']:r for r in after if r['case']!='H1'};pub=[r for r in before if r['case']!='H1'];assert{r['id']for r in pub}==set(index)
 trans=collections.Counter(r['status']+'->'+index[r['id']]['status']for r in pub)
 product=rowids(summary['product_failure_row_ids']);producttrans=collections.Counter(index[i]['status']for i in product);resolved=[];unknown=[]
 for cluster in summary['defect_clusters']:
  ids=rowids(cluster['fixed_row_ids']);assert ids and ids<=product
  if all(index[i]['status']=='P'for i in ids):resolved.append(cluster['cluster_id'])
  elif any(index[i]['status']=='U'for i in ids):unknown.append(cluster['cluster_id'])
 return {'allPublicRowTransitions':dict(trans),'confirmedProductRows':len(product),'productRowFinalStatuses':dict(producttrans),'productRowRepairRate':ratio(producttrans['P'],len(product)),'confirmedClusters':len(summary['defect_clusters']),'resolvedClusters':resolved,'unassessedClusters':unknown,'clusterRepairRate':ratio(len(resolved),len(summary['defect_clusters'])),'scope':'Hidden FINAL outcomes have no D0 repair denominator. Every known D0 manifestation must pass for a cluster to count resolved.'}
def sum_detection(ds):
 keys=['TP','FP','U','eligibleUniqueClaims','qualitativeOrIneligible','duplicates'];c={k:sum(d['counts'][k]for d in ds)for k in keys};nr=sum(d['confirmedProductFailureRows']for d in ds);dr=sum(d['detectedProductRows']for d in ds);nc=sum(d['confirmedProductClusters']for d in ds);dc=sum(d['detectedProductClusters']for d in ds);n=c['TP']+c['FP']+c['U']
 return {'counts':c,'confirmedProductFailureRows':nr,'detectedProductRows':dr,'pooledRowRecall':ratio(dr,nr),'pooledRowMissRate':ratio(nr-dr,nr),'confirmedProductClusters':nc,'detectedProductClusters':dc,'pooledClusterRecall':ratio(dc,nc),'conditionalFalseDiscoveryRatio':ratio(c['FP'],c['TP']+c['FP']),'allClaimsFalseDiscoveryBounds':[ratio(c['FP'],n),ratio(c['FP']+c['U'],n)],'classicalFalsePositiveRate':None,'macroTaskRowRecall':mean([d['rowRecall']for d in ds]),'macroTaskClusterRecall':mean([d['clusterRecall']for d in ds])}
def mean(values):
 v=[x for x in values if x is not None];return sum(v)/len(v)if v else None
def build():
 ex.gate.verify(R/'gates','reveal',R);assignment=ex.read(R/'private/assignment.json');tasks={};arms={t:[]for t in ['baseline-v6','candidate-v7']}
 for task,aliases in assignment['gradeAliases'].items():
  tasks[task]={}
  for alias,unit in aliases.items():
   summary=ex.read(R/'evaluation/D0'/task/'summary.json')['sources'][alias];d0=grade_rows('D0',task,alias);final=grade_rows('FINAL',task,alias);assert len(d0)==528 and len(final)==792
   original=ex.read(R/'evaluation-inputs/selfreview'/task/alias/'claims.json');det={}
   for origin in ['machine','manual','combined']:
    origins=['machine','manual']if origin=='combined'else[origin];cs=[(o,c)for o in origins for c in original[o]];det[origin]=detection(d0,summary,cs,len(original['ineligible_or_qualitative'])if origin in ['manual','combined']else 0)
   value={'unit':unit,'tool':assignment['units'][unit]['tool'],'D0':coverage(d0),'FINALPublic':coverage([r for r in final if r['case']!='H1']),'FINALHidden':coverage([r for r in final if r['case']=='H1']),'FINAL':coverage(final),'detection':det,'repairs':repairs(d0,final,summary),'byPlatform':{},'byClass':{},'unassertedScope':summary.get('unasserted_scope',[]),'unsupportedScope':summary.get('unsupported_scope',[]),'sourceAPI':summary.get('source_api_issues',[])}
   for key,out in [('platform','byPlatform'),('class','byClass')]:
    for v in sorted({r[key]for r in final}):value[out][v]={'D0':coverage([r for r in d0 if r[key]==v]),'FINAL':coverage([r for r in final if r[key]==v])}
   tasks[task][alias]=value;arms[value['tool']].append(value)
 pooled={}
 for tool,values in arms.items():
  pooled[tool]={'detection':{o:sum_detection([v['detection'][o]for v in values])for o in ['machine','manual','combined']},'quality':{},'repair':{}}
  for stage in ['D0','FINALPublic','FINALHidden','FINAL']:
   c={s:sum(v[stage]['counts'][s]for v in values)for s in STATUSES};app=c['P']+c['F']+c['U'];pooled[tool]['quality'][stage]={'counts':c,'applicable':app,'pooledUnassessedRatio':ratio(c['U'],app),'macroTaskUnassessedRatio':mean([v[stage]['unassessedRatio']for v in values])}
  n=sum(v['repairs']['confirmedProductRows']for v in values);p=sum(v['repairs']['productRowFinalStatuses'].get('P',0)for v in values);nc=sum(v['repairs']['confirmedClusters']for v in values);pc=sum(len(v['repairs']['resolvedClusters'])for v in values)
  pooled[tool]['repair']={'confirmedProductRows':n,'repairedRows':p,'pooledProductRowRepairRate':ratio(p,n),'confirmedClusters':nc,'repairedClusters':pc,'pooledClusterRepairRate':ratio(pc,nc),'macroTaskClusterRepairRate':mean([v['repairs']['clusterRepairRate']for v in values])}
 return {'tasks':tasks,'pooled':pooled,'scope':'Three prospective task pairs, six independently produced sources. Selected fixed assertion families only; repeated states/platforms are not independent trials. Natural product classification is independently sealed; numerical oracle F is separately retained. Conditional false discovery is not classical FPR; zero denominators are null. No injected defects. Small sample and shared scheduling preclude a causal quality/speed claim.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();v=build();out=R/'metrics.json'
 if a.write:assert not out.exists();ex.save(out,v)
 else:assert ex.read(out)==v
 print(json.dumps({'status':'PASS','pooled':v['pooled']}))
if __name__=='__main__':main()
