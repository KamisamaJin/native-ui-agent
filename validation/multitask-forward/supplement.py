#!/usr/bin/env python3
"""Separately gated posthoc shared-environment recheck, never a primary replacement."""
import argparse,importlib.util,json,time,sys
from pathlib import Path
import experiment as ex
import metrics as m
import pair_metrics as pm
R=Path(__file__).resolve().parent
REG=R/'shared-environment-v1/gates'
def inventory(root,except_name=None):return{str(p.relative_to(root)):ex.sha(p)for p in sorted(root.rglob('*'))if p.is_file()and p.name!=except_name and'__pycache__'not in p.parts and p.suffix!='.pyc'}
def init():
 REG.mkdir();ex.save(REG/'config.json',{'version':1,'artifact_root':str(R),'stages':{'fix':{'members':['shared-adapter'],'requires':[]},'original-finalized':{'members':['T1','T2','T3'],'requires':['fix']},'graded':{'members':['T1','T2','T3'],'requires':['original-finalized']}}})
 paths=['shared-environment-v1/'+n for n in ['oracle_common.py','PATCH.json','PROTOCOL.md']]+['../../tools/native_environment.py','test_shared_environment.py','operators/shared-environment-tests.log']
 # cohort_gate prohibits escaping its artifact root: bind the reusable source via a
 # byte-exact in-root copy and independently verify external identity below.
 target=R/'shared-environment-v1/native_environment.py';assert not target.exists();target.write_bytes((R.parents[1]/'tools/native_environment.py').read_bytes());paths.remove('../../tools/native_environment.py');paths.append('shared-environment-v1/native_environment.py')
 ex.gate.seal(REG,'fix',{'shared-adapter':paths},R)
def prep():
 ex.gate.verify(R/'gates','grade-pair',R);ex.gate.verify(REG,'fix',R)
 assert ex.sha(R.parents[1]/'tools/native_environment.py')==ex.sha(R/'shared-environment-v1/native_environment.py')
 members={t:['gates/grade-pair.json']+['evaluation/'+s+'/'+t+'/SEAL.json'for s in ['D0','FINAL','selfreview','paired-D0']]for t in ['T1','T2','T3']}
 for t in ['T1','T2','T3']:
  out=R/'supplement'/t
  text=f'''You are the same independent anonymous task evaluator for {t}, conducting a separately gated POSTHOC shared environment compatibility supplement. Read {R}/shared-environment-v1/PROTOCOL.md and PATCH.json, then only this task's original four stage deliveries/outputs, original approved design public/private and original named raw corpora/source capsules. Original truth, sources, input fixtures, expected values, tolerances and row denominator are immutable. Assignment/other tasks/builders/own-corpora remain forbidden. No SDK, edits outside your output, repairs, subagents, commits or pushes. Verify fix and original-finalized gates via cohort_gate before scoring. Frozen fixed oracle is {R}/shared-environment-v1/oracle_common.py; import it separately and call grade_task({R}/design-v2/{t},case,platform,raw_observation,...). It only canonicalizes known native direction wire values and records proof. This is shared infrastructure, not treatment benefit.
Write ONLY {out} (and task temporary cache). Start actual phase.json now. For D0 and FINAL, use the original corresponding batch.json. First call fixed oracle with manual=None/source_root=None; save complete native-base-grade.json and its native_report as native-base.json under {out}/<D0|FINAL>/<alias>/<case>/<platform>. Then use valid inspected original manual decisions to produce grade.json. Save the effective frozen-evaluator manual input exactly as manual.json in each case/platform output; preserve original manual bytes with provenance where reused; if additional Android visual inspection is needed, write supplementary manual decisions separately with original PNG SHA/snapshot indices and reasons. Never manufacture passed numeric iOS styles or omit original F/U. For iOS, the effective manual.json must be byte-exact copy of the corresponding original manual.json; preserve original iOS acceptance statuses. Any newly noticed iOS review concern belongs in an unscored note, not a revised iOS disposition in this direction-only supplement. Only Android may need additional visual inspection after the formerly invalid input gate is corrected. Preserve failed attempts and original grades. Review all newly unmasked F causes, original sources/API and actual PNGs; do not convert F to P by classification. Each stage summary.json must follow the same sources/flat counts/defect_clusters/product_failure_row_ids/non_product_f_rows/uncertain_f_rows/unasserted_scope/unsupported_scope/source_api_issues schema. Any previously confirmed iOS issue and F cause classification must stay unchanged unless there is a demonstrable recheck error, which must be preserved separately, not silently reclassified. Newly unmasked Android F requires independent actual evidence to classify as product; numeric F alone is insufficient.
Run {R}/evaluation_schema.py on {out}/D0 --cases P1 P2 and {out}/FINAL --cases P1 P2 H1 before seal. Also grade the actual v6 paired-D0 corpora from this task's original paired batch with the SAME fixed oracle and manual=None. Write {out}/paired-D0/<alias>/<case>/<platform>/native-grade-v6.json. The paired v7 side is corrected D0 native-base-grade.json, without manual. Save task pair-comparison.json using unchanged compare_pair and only its four native classes. Record row deltas separately from original primary Android-U result. Original own-review claims remain unchanged; root will apply the identical frozen metric functions to corrected truth after all task seals. No new discoveries receive self-review detection credit.
Finish actual phase.json, then SEAL.json with sealedAtUnix and exact every-file SHA inventory except itself/pycache/pyc. Stop. All THREE supplement outputs seal before assignment release. Primary sealed grades are never overwritten; this posthoc correction has weaker evidence status than the primary blind experiment.
'''
  (R/'prompts'/(t+'-evaluate-supplement.txt')).write_text(text)
 dispatch=R/'shared-environment-v1/SUPPLEMENT-DISPATCH.json';assert not dispatch.exists();ex.save(dispatch,{'dispatchedAfterOriginalFourStagesAtUnix':time.time(),'helperSHA256':ex.sha(Path(__file__)),'primaryMetricFunctionsSHA256':ex.sha(R/'metrics.py'),'prompts':{t:ex.sha(R/'prompts'/(t+'-evaluate-supplement.txt'))for t in ['T1','T2','T3']},'scopeClarification':'Direction-only compatibility patch: iOS manual inputs are byte-exact originals, iOS dispositions unchanged. Any new iOS concern stays an unscored note. Android visual inspection may finish previously rejected input cases. No new native/product actions or retrospective claim expansion.'})
 for t in members:members[t]+=['shared-environment-v1/SUPPLEMENT-DISPATCH.json','prompts/'+t+'-evaluate-supplement.txt']
 ex.gate.seal(REG,'original-finalized',members,R)
 print('All original primary stages sealed; fixed shared supplement task prompts ready')
def close():
 members={}
 for t in ['T1','T2','T3']:
  out=R/'supplement'/t;seal=ex.read(out/'SEAL.json');assert seal['files']==inventory(out,'SEAL.json'),t;members[t]=['supplement/'+t]
 ex.gate.seal(REG,'graded',members,R);print('All THREE posthoc shared-infrastructure task outputs sealed')
def rows(stage,task,alias):
 rr=[]
 for p in sorted((R/'supplement'/task/stage/alias).glob('*/*/grade.json')):rr+=ex.read(p)['rows']
 return rr
def build():
 ex.gate.verify(R/'gates','reveal',R);ex.gate.verify(REG,'graded',R);a=ex.read(R/'private/assignment.json');tasks={};groups={k:[]for k in ['baseline-v6','candidate-v7']}
 for t,aliases in a['gradeAliases'].items():
  tasks[t]={}
  for alias,unit in aliases.items():
   d0=rows('D0',t,alias);final=rows('FINAL',t,alias);assert len(d0)==528 and len(final)==792
   s=ex.read(R/'supplement'/t/'D0/summary.json')['sources'][alias];claims=ex.read(R/'evaluation-inputs/selfreview'/t/alias/'claims.json')
   detection={}
   for origin in ['machine','manual','combined']:
    origins=['machine','manual']if origin=='combined'else[origin];cs=[(o,c)for o in origins for c in claims[o]];detection[origin]=m.detection(d0,s,cs,len(claims['ineligible_or_qualitative'])if origin!='machine'else 0)
   value={'tool':a['units'][unit]['tool'],'unit':unit,'D0':m.coverage(d0),'FINAL':m.coverage(final),'FINALPublic':m.coverage([x for x in final if x['case']!='H1']),'FINALHidden':m.coverage([x for x in final if x['case']=='H1']),'detection':detection,'repairs':m.repairs(d0,final,s),'primaryToCorrectedTransitions':{}}
   for stage,rr in [('D0',d0),('FINAL',final)]:
    old={x['id']:x for x in m.grade_rows(stage,t,alias)};c={}
    for x in rr:
     y=old[x['id']];assert all(x[k]==y[k]for k in ['id','expected','unit','op','tolerance']);key=y['status']+'->'+x['status'];c[key]=c.get(key,0)+1
     if x['platform']=='ios':assert x['status']==y['status'],(t,alias,stage,x['id'],'iOS truth unexpectedly changed')
    value['primaryToCorrectedTransitions'][stage]=c
   tasks[t][alias]=value;groups[value['tool']].append(value)
 pooled={}
 for tool,vv in groups.items():
  pooled[tool]={'detection':{o:m.sum_detection([v['detection'][o]for v in vv])for o in ['machine','manual','combined']},'quality':{},'repair':{}}
  for stage in ['D0','FINAL','FINALPublic','FINALHidden']:
   c={s:sum(v[stage]['counts'][s]for v in vv)for s in m.STATUSES};app=c['P']+c['F']+c['U'];pooled[tool]['quality'][stage]={'counts':c,'applicable':app,'pooledUnassessedRatio':m.ratio(c['U'],app)}
  n=sum(v['repairs']['confirmedClusters']for v in vv);p=sum(len(v['repairs']['resolvedClusters'])for v in vv);nr=sum(v['repairs']['confirmedProductRows']for v in vv);pr=sum(v['repairs']['productRowFinalStatuses'].get('P',0)for v in vv)
  pooled[tool]['repair']={'confirmedClusters':n,'repairedClusters':p,'pooledClusterRepairRate':m.ratio(p,n),'confirmedProductRows':nr,'repairedRows':pr,'pooledProductRowRepairRate':m.ratio(pr,nr)}
 pairrows=[]
 spec=importlib.util.spec_from_file_location('shared_pair_oracle',R/'shared-environment-v1/oracle_common.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
 for t,aliases in a['gradeAliases'].items():
  for alias in aliases:
   aa=[];bb=[]
   for case in ['P1','P2']:
    for platform in ['ios','android']:
     aa+=ex.read(R/'supplement'/t/'paired-D0'/alias/case/platform/'native-grade-v6.json')['rows'];bb+=ex.read(R/'supplement'/t/'D0'/alias/case/platform/'native-base-grade.json')['rows']
   pairrows += [dict(x,task=t,alias=alias)for x in g.compare_pair({'rows':aa},{'rows':bb})['rows']]
 pairing={'pooled':pm.transitions(pairrows,'a','b'),'byPlatform':{p:pm.transitions([x for x in pairrows if x['platform']==p],'a','b')for p in ['ios','android']},'byTask':{t:pm.transitions([x for x in pairrows if x['task']==t],'a','b')for t in ['T1','T2','T3']},'byClass':{c:pm.transitions([x for x in pairrows if x['class']==c],'a','b')for c in sorted({x['class']for x in pairrows})},'rows':pairrows}
 return {'tasks':tasks,'pooled':pooled,'correctedCollectorSessions':pairing,'scope':'POSTHOC shared environment compatibility correction, original observations and claims. Neither a primary blind result nor a v7 benefit. Original primary metrics retain all Android U. No further product repairs or native acquisitions. Same primary metric functions; no descriptor/expectation repair.'}
def verify():
 ex.gate.verify(REG,'graded',R);assert ex.sha(R.parents[1]/'tools/native_environment.py')==ex.sha(R/'shared-environment-v1/native_environment.py')
 spec=importlib.util.spec_from_file_location('fixed_shared_oracle',R/'shared-environment-v1/oracle_common.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);n=0
 for t in ['T1','T2','T3']:
  out=R/'supplement'/t;assert ex.read(out/'SEAL.json')['files']==inventory(out,'SEAL.json')
  for stage in ['D0','FINAL']:
   b=ex.read(R/'evaluation-inputs'/stage/t/'batch.json')
   for src in b['corpora']:
    for case in b['cases']:
     for platform in ['ios','android']:
      base=out/stage/src['anonymousID']/case/platform;op=R/src['captures']/platform/case/'observation.json';native=g.grade_task(R/'design-v2'/t,case,platform,op)
      assert native==ex.read(base/'native-base-grade.json');assert native['native_report']==ex.read(base/'native-base.json');n+=1
      saved=ex.read(base/'grade.json');manual=base/'manual.json'
      if platform=='ios':assert ex.sha(manual)==ex.sha(R/'evaluation'/stage/t/src['anonymousID']/case/platform/'manual.json'),'Supplement modified original iOS visual decisions'
      accepted=g.grade_task(R/'design-v2'/t,case,platform,op,manual=manual if manual.is_file()else None,source_root=R/src['sourceCapsule']/'source')
      for key in accepted:
       if key!='api_checks':assert accepted[key]==saved[key],(t,stage,src['anonymousID'],case,platform,key)
      assert saved['input_checks']==native['input_checks'];assert saved['counts']==m.counts(saved['rows'])
  b=ex.read(R/'evaluation-inputs/paired-D0'/t/'batch.json')
  for src in b['corpora']:
   for case in ['P1','P2']:
    for platform in ['ios','android']:
     op=R/src['v6Captures']/platform/case/'observation.json';saved=ex.read(out/'paired-D0'/src['anonymousID']/case/platform/'native-grade-v6.json');assert g.grade_task(R/'design-v2'/t,case,platform,op)==saved;n+=1
 print('PASS: fixed shared supplement native grade replay',n)
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['init','prepare','close','metrics','verify']);p.add_argument('--write',action='store_true');a=p.parse_args()
 if a.action=='metrics':
  v=build();path=R/'supplement-metrics.json'
  if a.write:assert not path.exists();ex.save(path,v)
  else:assert ex.read(path)==v
  print(json.dumps({'status':'PASS','pooled':v['pooled']}))
 else:globals()[{'prepare':'prep'}.get(a.action,a.action)]()
if __name__=='__main__':main()
