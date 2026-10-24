#!/usr/bin/env python3
"""Prospectively fixed product-alarm metrics, separate from schema compliance."""
import argparse,json
from pathlib import Path

def ratio(a,b):return a/b if b else None

def coverage(rows):
 counts={s:sum(r['status']==s for r in rows)for s in ['passed','failed','unassessed','not_applicable']}
 assert sum(counts.values())==len(rows)
 app=sum(counts[s]for s in ['passed','failed','unassessed'])
 return {'counts':counts,'applicable':app,'unassessedRatio':ratio(counts['unassessed'],app)}

def agreed_clusters(first,second,product_rows):
 """Compare membership sets, not arbitrary model-chosen cluster names."""
 product=set(product_rows)
 def groups(panel):
  result=[];seen=set()
  for group in panel:
   members=frozenset(group['rows']);assert members and members<=product and not seen.intersection(members)
   assert group.get('reason')and group.get('certainty')in{'confirmed','uncertain'};seen.update(members)
   if group['certainty']=='confirmed':result.append(members)
  assert seen==product,'Each product F needs a cause group or explicit singleton uncertainty before group consensus'
  return set(result)
 a,b=groups(first),groups(second);same=a&b
 return {'confirmed':[sorted(v)for v in sorted(same,key=lambda x:sorted(x))],
         'membershipUncertainRows':sorted(product-set().union(*same))if same else sorted(product),
         'scope':'Exact independent agreement on within-task cause membership; related tasks/platforms are not independent experiments.'}

def detection(truth,claims,clusters,all_claims=None):
 by={r['key']:r for r in truth};assert len(by)==len(truth)
 population={r['claim_id']:r for r in (all_claims if all_claims is not None else claims)}
 assert len(population)==len(all_claims if all_claims is not None else claims)
 product={k for k,r in by.items()if r['status']=='failed'and r.get('cause_category')=='product'}
 counts={'TP':0,'FP':0,'U':0};detected=set();seen=set();decisions=[];schema_rejections=0;duplicates=0;nonalarms=0
 for claim in claims:
  cid=claim['claim_id'];assert cid not in seen;seen.add(cid)
  assert claim['origin']in{'machine','manual'}
  assert set(claim['original_scope'])<=set(by),'Claim scope must come from original case/state/rule, not retrospective root-cause expansion'
  schema_rejections+=bool(claim.get('schema_rejected'))
  if claim.get('duplicate_of'):
   original=population[claim['duplicate_of']];assert original['origin']=='machine'and original['original_status']=='failed'and set(original['original_scope'])==set(claim['original_scope'])and original['claim_id']!=cid
   duplicates+=1;continue
  if claim['original_status']!='failed':nonalarms+=1;continue
  a,b=claim['judge_one'],claim['judge_two'];assert a['status']in counts and b['status']in counts
  for verdict in [a,b]:
   assert set(verdict.get('supported_rows',[]))<=set(claim['original_scope'])
   assert verdict.get('reason')
  shared=set(a.get('supported_rows',[]))&set(b.get('supported_rows',[]))
  if a['status']==b['status']=='TP'and shared and shared<=product:
   status='TP';detected|=shared
  elif a['status']==b['status']=='FP'and a.get('false_alarm_supported')is True and b.get('false_alarm_supported')is True:
   status='FP'
  else:status='U'
  counts[status]+=1;decisions.append({'claim_id':cid,'status':status,'supported_rows':sorted(shared)if status=='TP'else[]})
 matched=[c for c in clusters if set(c)&detected]
 total=sum(counts.values())
 return {'counts':counts,'decisions':decisions,'schemaRejections':schema_rejections,'duplicates':duplicates,'nonFailureObservations':nonalarms,
         'confirmedProductRows':len(product),'detectedProductRows':len(detected),'missedProductRows':sorted(product-detected),
         'rowRecall':ratio(len(detected),len(product)),'rowMissRate':ratio(len(product-detected),len(product)),
         'confirmedProductClusters':len(clusters),'detectedProductClusters':len(matched),'clusterRecall':ratio(len(matched),len(clusters)),
         'conditionalFalseDiscoveryRatio':ratio(counts['FP'],counts['TP']+counts['FP']),
         'allAlarmFalseDiscoveryBounds':[ratio(counts['FP'],total),ratio(counts['FP']+counts['U'],total)],
         'classicalFalsePositiveRate':None,'scope':'Original supported product alarms under independent dual judgment; schema rejection is not a false product alarm. AI consensus is not human gold.'}

def repairs(initial,final,clusters):
 before={r['key']:r for r in initial};after={r['key']:r for r in final};assert len(before)==len(initial)and len(after)==len(final)
 product={k for k,r in before.items()if r['status']=='failed'and r.get('cause_category')=='product'}
 assert product<=set(after)
 outcomes={s:sum(after[k]['status']==s for k in product)for s in ['passed','failed','unassessed','not_applicable']}
 repaired=[c for c in clusters if all(after[k]['status']=='passed'for k in c)]
 return {'confirmedProductRows':len(product),'rowFinalStatuses':outcomes,'productRowRepairRate':ratio(outcomes['passed'],len(product)),
         'confirmedClusters':len(clusters),'repairedClusters':len(repaired),'clusterRepairRate':ratio(len(repaired),len(clusters)),
         'newStrictPublicFailures':sorted(k for k,r in after.items()if k in before and before[k]['status']=='passed'and r['status']=='failed'),
         'scope':'All originally confirmed manifestations must pass. Unknown is not repaired; hidden FINAL has no D0 repair denominator.'}

def summarize(data):
 c=agreed_clusters(data['clusters_one'],data['clusters_two'],[r['key']for r in data['D0']if r['status']=='failed'and r.get('cause_category')=='product'])
 return {'D0':coverage(data['D0']),'FINAL':coverage(data['FINAL']),'clusters':c,
         'detection':{o:detection(data['D0'],[r for r in data['claims']if o=='combined'or r['origin']==o],c['confirmed'],data['claims'])for o in ['machine','manual','combined']},
         'repair':repairs(data['D0'],data['FINAL'],c['confirmed'])}

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();value=summarize(json.loads(a.input.read_text()))
 if a.check:assert json.loads(a.output.read_text())==value
 else:assert not a.output.exists();a.output.write_text(json.dumps(value,indent=2)+'\n')
 print('PASS: prospectively fixed product/schema/uncertainty metrics')
if __name__=='__main__':main()
