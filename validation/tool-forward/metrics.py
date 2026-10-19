#!/usr/bin/env python3
"""Arithmetic over independently sealed atomic grades, never a UI evaluator."""
import argparse,collections,json
from pathlib import Path
OUTCOMES=('PASS','FAIL','UNASSESSED')
def fraction(n,d):return {'numerator':n,'denominator':d,'value':n/d if d else None}
def index_grade(grade):
 rows=grade['results'];index={}
 if grade.get('requiredAssessmentCount',len(rows))!=len(rows):raise ValueError('Missing required assessment rows')
 for row in rows:
  key=(row['platform'],row['key'])
  if key in index or row['outcome']not in OUTCOMES or type(row['sourceOnly'])is not bool:raise ValueError('Invalid/duplicate assessment')
  index[key]=row
 return index

def counts(rows):
 c=collections.Counter(r['outcome']for r in rows);n=sum(c.values())
 return {'required':n,**{k:c[k]for k in OUTCOMES},'unassessed_ratio':fraction(c['UNASSESSED'],n),'all_requested_assessments_passed':bool(n)and c['PASS']==n}
def grade_stats(grade):
 rows=list(index_grade(grade).values());result={'all':counts(rows),'runtime':counts([r for r in rows if not r['sourceOnly']]),'source':counts([r for r in rows if r['sourceOnly']])}
 result['by_platform']={p:{'all':counts([r for r in rows if r['platform']==p]),'runtime':counts([r for r in rows if r['platform']==p and not r['sourceOnly']]),'source':counts([r for r in rows if r['platform']==p and r['sourceOnly']])}for p in sorted({r['platform']for r in rows})}
 result['runtime_by_aspect']={a:counts([r for r in rows if not r['sourceOnly']and r.get('aspect')==a])for a in sorted({r.get('aspect','unspecified')for r in rows if not r['sourceOnly']})}
 result['unassessed_missing_methods']=dict(collections.Counter(m for r in rows if r['outcome']=='UNASSESSED'for m in r.get('missingEvidenceMethod',[])))
 return result

def stratified_stats(grade,plan):
 """Stratify by frozen case/state metadata rather than parsing display names."""
 actual=index_grade(grade);expected={(r['platform'],r['key']):r for r in plan['assessments']}
 if set(actual)!=set(expected):raise ValueError('Stratification plan differs from required assessments')
 cases=collections.defaultdict(list);states=collections.defaultdict(list)
 for key,row in actual.items():
  metadata=expected[key];cases[metadata['caseId']].append(row)
  if not row['sourceOnly']:states[(row['platform'],metadata['caseId'],metadata['stateId'])].append(row)
 return {'by_case':{case:counts(rows)for case,rows in sorted(cases.items())},'runtime_by_state':[{'platform':p,'caseId':c,'stateId':s,**counts(rows)}for(p,c,s),rows in sorted(states.items())]}

def transitions(before,after):
 a=index_grade(before);b=index_grade(after)
 if not set(a)<=set(b):raise ValueError('Final grade lost initial assessment keys')
 matrix={x:{y:0 for y in OUTCOMES}for x in OUTCOMES};fixed=[];unresolved=[];regressions=[];newly_observed=[]
 for key,old in a.items():
  new=b[key]
  if old.get('expected')!=new.get('expected')or old['sourceOnly']!=new['sourceOnly']:raise ValueError('Acceptance changed between phases')
  x,y=old['outcome'],new['outcome'];matrix[x][y]+=1;ref={'platform':key[0],'key':key[1]}
  if x=='FAIL':(fixed if y=='PASS'else unresolved).append(dict(ref,finalOutcome=y))
  if x=='PASS'and y=='FAIL':regressions.append(ref)
  if x=='UNASSESSED'and y=='FAIL':newly_observed.append(ref)
 extra=[b[k]for k in b.keys()-a.keys()]
 return {'initial_to_final':matrix,'repair_success':fraction(len(fixed),len(fixed)+len(unresolved)),'fixed_confirmed_initial_failures':fixed,'unresolved_confirmed_initial_failures':unresolved,'confirmed_regressions':regressions,'newly_observed_failures':newly_observed,'additional_final_assessments':counts(extra)}

def discovery_stats(grade,matching):
 """Count independently classified matches; duplicates do not multiply credit."""
 index=index_grade(grade);findings=matching['findings'];ids={f['id']for f in findings}
 if len(ids)!=len(findings)or matching['originalFindingCount']!=len(findings):raise ValueError('Invalid original finding count/IDs')
 sets={c:set()for c in ['TP','FP','UNCERTAIN']};duplicates=[]
 for row in matching['atomicMatches']:
  if row['findingId']not in ids or row['classification']not in sets:raise ValueError('Unmapped finding/classification')
  if row.get('key')is None:
   if row['classification']!='UNCERTAIN':raise ValueError('Confirmed match lacks assessment key')
   continue
  key=(row['platform'],row['key']);classification=row['classification']
  if key not in index:raise ValueError('Match is outside frozen D0 assessments')
  if classification in {'TP','FP'}and index[key]['outcome']!=('FAIL'if classification=='TP'else'PASS'):raise ValueError('Match contradicts independent grade')
  if key in sets[classification]:duplicates.append(row)
  sets[classification].add(key)
 failures={key for key,row in index.items()if row['outcome']=='FAIL'};fn=failures-sets['TP']
 def stats(selected):
  tp=len(sets['TP']&selected);fp=len(sets['FP']&selected);miss=len(fn&selected)
  return {'TP':tp,'FP':fp,'FN':miss,'confirmed_false_discovery_share':fraction(fp,tp+fp),'miss_rate':fraction(miss,tp+miss),'uncertain_assessment_keys':len(sets['UNCERTAIN']&selected),'classical_false_positive_rate':None,'classical_fpr_limitation':'No complete independently reviewed negative-claim universe.'}
 refs=lambda keys:[{'platform':p,'key':k}for p,k in sorted(keys)]
 return {'all':stats(set(index)),'by_platform':{p:stats({k for k in index if k[0]==p})for p in sorted({k[0]for k in index})},'runtime':stats({k for k,r in index.items()if not r['sourceOnly']}),'source':stats({k for k,r in index.items()if r['sourceOnly']}),'original_finding_count':len(findings),'finding_classifications':dict(collections.Counter(f['classification']for f in findings)),'duplicate_atomic_matches':duplicates,'TP_keys':refs(sets['TP']),'FP_keys':refs(sets['FP']),'FN_keys':refs(fn),'uncertain_keys':refs(sets['UNCERTAIN'])}

def self_test():
 def row(key,outcome,source=False):return {'platform':'apple','key':key,'outcome':outcome,'sourceOnly':source,'expected':True,'aspect':'nativeSemantics'}
 before={'results':[row('fix','FAIL'),row('unknown','FAIL'),row('regress','PASS'),row('new','UNASSESSED'),row('api','PASS',True)]}
 after={'results':[row('fix','PASS'),row('unknown','UNASSESSED'),row('regress','FAIL'),row('new','FAIL'),row('api','PASS',True),row('heldout','FAIL')]}
 s=grade_stats(before);assert s['runtime']['required']==4 and s['source']['required']==1 and s['runtime']['unassessed_ratio']['value']==.25
 t=transitions(before,after);assert t['repair_success']['value']==.5 and len(t['unresolved_confirmed_initial_failures'])==1 and len(t['confirmed_regressions'])==len(t['newly_observed_failures'])==1 and t['additional_final_assessments']['FAIL']==1
 assert fraction(0,0)['value']is None
 matching={'originalFindingCount':3,'findings':[{'id':i,'classification':c}for i,c in [('a','TP_ONLY'),('b','FP_ONLY'),('c','UNCERTAIN')]],'atomicMatches':[{'findingId':i,'platform':'apple','key':k,'classification':c}for i,k,c in [('a','fix','TP'),('a','fix','TP'),('b','regress','FP'),('c','new','UNCERTAIN')]]}
 d=discovery_stats(before,matching);assert d['all']['TP']==d['all']['FP']==d['all']['FN']==1 and d['all']['confirmed_false_discovery_share']['value']==.5 and len(d['duplicate_atomic_matches'])==1
 try:discovery_stats(before,dict(matching,atomicMatches=[{'findingId':'a','platform':'apple','key':'unknown','classification':'FP'}]))
 except ValueError:pass
 else:raise AssertionError('Contradictory independent match was counted')
 try:transitions(before,{'results':after['results'][1:]})
 except ValueError:pass
 else:raise AssertionError('Lost assessment was silently ignored')
 changed={'results':[dict(r,expected=False)if r['key']=='fix'else r for r in after['results']]}
 try:transitions(before,changed)
 except ValueError:pass
 else:raise AssertionError('Changed acceptance was silently compared')
 print(json.dumps({'status':'passed_metric_arithmetic_invariants','scope':'Synthetic arithmetic invariants only, not a native or business-quality test.'}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');p.add_argument('--grade',type=Path);p.add_argument('--final',type=Path);a=p.parse_args()
 if a.self_test:self_test()
 elif a.grade:
  original=json.loads(a.grade.read_text());out=grade_stats(original)
  if a.final:out['transitions']=transitions(original,json.loads(a.final.read_text()))
  print(json.dumps(out,indent=2))
 else:p.error('--self-test or --grade required')
