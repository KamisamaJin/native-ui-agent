#!/usr/bin/env python3
"""Arithmetic on sealed independent grades; never grade business/source/image data."""
import argparse,collections,json
from pathlib import Path
from contract import R,read
BUCKETS=['runtime_business','runtime_visual','runtime_integration','runtime_capability','input_member_integration','source_api']
def ratio(n,d):return {'numerator':n,'denominator':d,'value':n/d if d else None}
def buckets(rows):
 out={}
 for bucket in BUCKETS:
  rs=[r for r in rows if r['denominator']==bucket];c=collections.Counter(r['outcome']for r in rs);out[bucket]={'required':len(rs),**{x:c[x]for x in ['P','F','U']}}
 rs=[r for r in rows if r['denominator'].startswith('runtime_')];c=collections.Counter(r['outcome']for r in rs)
 out['runtime_total']={'required':len(rs),**{x:c[x]for x in ['P','F','U']},'assessedCoverage':ratio(c['P']+c['F'],len(rs)),'unassessedFraction':ratio(c['U'],len(rs))}
 return out
def primary(r):return r['denominator']=='runtime_business'and r['stimulus_gate'].get('required')is True and r['stimulus_gate'].get('established')is True
def metrics(d0,final,matches,findings,platform=None):
 a={r['key']:r for r in d0['rows']if platform is None or r['platform']==platform};b={r['key']:r for r in final['rows']if platform is None or r['platform']==platform}
 assert set(a)<=set(b)
 for k,r in a.items():
  for name in ['platform','case','checkpoint','category','denominator','method','expected_sha256']:assert r[name]==b[k][name],(k,name)
 confirmed={r['id']for r in findings if r.get('certainty')=='confirmed'and(platform is None or r.get('platform')==platform)}
 fs={r['id']:r for r in findings};mapped=set();claimed=set();uncertain_mapped=set()
 for m in matches:
  assert m['row_key']in {r['key']for r in d0['rows']}
  cid=m['claim_id'];assert cid in fs,('Unknown original claim ID',cid)
  if m['row_key']not in a:continue
  if cid in confirmed:claimed.add(m['row_key']);mapped.add(cid)
  else:uncertain_mapped.add(m['row_key'])
 runtime={k for k,r in a.items()if r['denominator'].startswith('runtime_')};fail={k for k,r in a.items()if r['outcome']=='F'};post={k for k,r in a.items()if primary(r)};business_fail=fail&post
 def detection(scope):
  tp=claimed&fail&scope;fp={k for k in claimed&scope if a[k]['outcome']=='P'};unknown={k for k in claimed&scope if a[k]['outcome']=='U'};fn=(fail&scope)-tp
  return {'TP':len(tp),'FP':len(fp),'FN':len(fn),'unassessedClaimRows':len(unknown),'falseDiscoveryShare':ratio(len(fp),len(tp)+len(fp)),'missRate':ratio(len(fn),len(tp)+len(fn)),'detectedKeys':sorted(tp),'falsePositiveKeys':sorted(fp),'missedKeys':sorted(fn),'unassessedClaimKeys':sorted(unknown)}
 def repairs(scope):
  eligible=fail&scope;trans={x:sorted(k for k in eligible if b[k]['outcome']==x)for x in ['P','F','U']}
  return {'eligibleD0Failures':len(eligible),'repaired':len(trans['P']),'persisted':len(trans['F']),'unassessedAfterRepair':len(trans['U']),'successRate':ratio(len(trans['P']),len(eligible)),'transitions':trans}
 return {'d0':buckets(list(a.values())),'final':buckets(list(b.values())),'finalInitialCases':buckets([r for r in b.values()if r['case']in ['C01','C02','C03','C04']]),'finalHoldouts':buckets([r for r in b.values()if r['case']in ['H01','H02']]),'primaryBusiness':detection(post),'runtimeDescriptive':detection(runtime),'initialBusinessDescriptive':detection({k for k,r in a.items()if r['denominator']=='runtime_business'and r['checkpoint']=='initial'}),'primaryBusinessRepair':repairs(post),'runtimeRepair':repairs(runtime),'sourceAPIRepair':repairs({k for k,r in a.items()if r['denominator']=='source_api'}),'regressions':sorted(k for k,r in a.items()if r['outcome']=='P'and b[k]['outcome']=='F'),'newlyAssessedFailures':sorted(k for k,r in a.items()if r['outcome']=='U'and b[k]['outcome']=='F'),'claims':{'originalConfirmed':len(confirmed),'matchedConfirmedFindingIDs':sorted(mapped),'unmappedConfirmedFindingIDs':sorted(confirmed-mapped),'uncertainFindingIDs':[x['id']for x in findings if x.get('certainty')!='confirmed'and(platform is None or x.get('platform')==platform)],'uncertainMappedKeys':sorted(uncertain_mapped)},'primaryBusinessFailureKeys':sorted(business_fail)}
def pair(old,new):
 a={r['key']:r for r in old['rows']};b={r['key']:r for r in new['rows']};assert set(a)==set(b)
 out={}
 for platform in [None,'ios','android']:
  scopes={}
  for bucket in BUCKETS+['runtime_total']:
   rs=[r for r in a.values()if(platform is None or r['platform']==platform)and(r['denominator']==bucket or bucket=='runtime_total'and r['denominator'].startswith('runtime_'))]
   matrix=collections.Counter(r['outcome']+'->'+b[r['key']]['outcome']for r in rs)
   gained=[r['key']for r in rs if r['outcome']=='U'and b[r['key']]['outcome']!='U'];lost=[r['key']for r in rs if r['outcome']!='U'and b[r['key']]['outcome']=='U']
   scopes[bucket]={'required':len(rs),'matrix':{x+'->'+y:matrix[x+'->'+y]for x in ['P','F','U']for y in ['P','F','U']},'gained':len(gained),'lost':len(lost),'net':len(gained)-len(lost),'gainedKeys':gained,'lostKeys':lost,'gainedMethods':dict(collections.Counter(a[k]['method']for k in gained)),'conflictingAssessedKeys':[r['key']for r in rs if r['outcome']!='U'and b[r['key']]['outcome']!='U'and r['outcome']!=b[r['key']]['outcome']]}
  out[platform or 'all']=scopes
 return out
def compute():
 assert (R/'private/assignment-release.json').is_file(),'Arithmetic is deferred until every blind seal and formal release'
 mapping=read(R/'private/grade-assignment.json')['mapping'];evaluation=R/'design/private/evaluation';arms={};pairs={}
 for anon,sid in mapping.items():
  d0=read(evaluation/'d0'/anon/'grade.json');final=read(evaluation/'final'/anon/'grade.json');matching=read(evaluation/'selfreview'/anon/'matching.json');findings=read(R/'private/submissions'/sid/'review.json')['findings']
  arms[sid]={'anonymous_id':anon,'all':metrics(d0,final,matching['matches'],findings),'platforms':{p:metrics(d0,final,matching['matches'],findings,p)for p in ['ios','android']}}
  paired=read(evaluation/'paired-d0'/anon/'paired-grade.json');pairs[sid]=pair(paired,d0)
 return {'version':1,'scope':'Fixed atomic required cells. Business misses require established requested native stimulus. Zero defect denominators are N/A; U is retained; no classical FP/(FP+TN) without a negative universe. Runtime/input/source are separate. Uncertain and unmapped original claims are retained, not automatically called false positives.','arms':arms,'sameSourceD0':pairs}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();out=R/'result-summary.json';d=compute()
 if a.write:assert not out.exists();out.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
 else:assert read(out)==d
 print('PASS: independent grade arithmetic reproduces')
if __name__=='__main__':main()
