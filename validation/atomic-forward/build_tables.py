#!/usr/bin/env python3
"""Render already-frozen metrics; no rescoring or retrospective expectation edits."""
import argparse
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
TOOLS=['baseline-v7','candidate-v8']
def pct(x):return 'N/A'if x is None else f'{100*x:.2f}%'
def frac(a,b):return f'{a}/{b}'+(' (N/A)'if not b else'')
def cov(x):return ' / '.join(str(x['counts'][s])for s in ['passed','failed','unassessed','not_applicable'])
def sec(x):return f'{x:.1f}s ({x/60:.2f}min)'
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |'for row in rows])
def render():
 s=ex.read(R/'summary.json');c=ex.read(R/'costs.json');g=ex.read(R/'grading-costs.json');parts=['# Frozen comparison tables','Both arms already have v7 contract/native capabilities. These are three task pairs, not a Skill versus no Skill comparison. All ratios are relative to sealed independent AI consensus, not human gold.','## Pooled public natural-product results']
 def values(fn):return[fn(s['groups'][t]['public'])for t in TOOLS]
 rows=[]
 def add(label,fn):rows.append([label,*values(fn)])
 add('D0 confirmed product manifestations',lambda x:x['detection']['combined']['confirmedProductRows'])
 add('Agreed product cause clusters',lambda x:len(x['clusters']['confirmed']))
 add('Cause membership uncertain manifestations',lambda x:len(x['clusters']['membershipUncertainRows']))
 for origin in ['machine','manual','combined']:
  add(origin+' original TP / FP / unknown alarms',lambda x,o=origin:' / '.join(str(x['detection'][o]['counts'][k])for k in ['TP','FP','U']))
  add(origin+' detected product rows',lambda x,o=origin:frac(x['detection'][o]['detectedProductRows'],x['detection'][o]['confirmedProductRows']))
 add('Combined row miss ratio',lambda x:pct(x['detection']['combined']['rowMissRate']))
 add('Detected agreed clusters',lambda x:frac(x['detection']['combined']['detectedProductClusters'],x['detection']['combined']['confirmedProductClusters']))
 add('Conditional FP/(TP+FP)',lambda x:pct(x['detection']['combined']['conditionalFalseDiscoveryRatio']))
 add('Unknown-inclusive alarm FP bounds',lambda x:' – '.join(pct(v)for v in x['detection']['combined']['allAlarmFalseDiscoveryBounds']))
 add('Product F→P / F / U / N/A',lambda x:' / '.join(str(x['repair']['rowFinalStatuses'][k])for k in ['passed','failed','unassessed','not_applicable']))
 add('Product-row repair ratio',lambda x:pct(x['repair']['productRowRepairRate']))
 add('Agreed cluster repair',lambda x:frac(x['repair']['repairedClusters'],x['repair']['confirmedClusters']))
 add('New strict public P→F',lambda x:len(x['repair']['newStrictPublicFailures']))
 parts +=[table(['Metric',*TOOLS],rows),'Classic FPR is N/A: no independently adjudicated complete TN universe. Unknown claims are retained; schema/descriptor problems are not automatic false product alarms. Repeated states and both platforms are correlated manifestations. Cluster membership must independently agree; uncertain associations are not invented bugs.','## Coverage (P / F / U / N/A)']
 rows=[]
 for label,key in [('D0 public','D0'),('FINAL public','FINAL')]:
  rows += [[label,*values(lambda x,k=key:cov(x[k]))],[label+' U/applicable',*values(lambda x,k=key:pct(x[k]['unassessedRatio']))]]
 for label,key in [('FINAL heldout','hiddenFinal'),('FINAL public+heldout','allFinal')]:
  rows +=[[label,*[cov(s['groups'][t][key])for t in TOOLS]],[label+' U/applicable',*[pct(s['groups'][t][key]['unassessedRatio'])for t in TOOLS]]]
 parts +=[table(['Scope',*TOOLS],rows),'Heldout FINAL has no D0 repair denominator. A selected requirement passed only within its declared atom/evidence scope; unsupported native font style and incomplete evidence remain U. Full brief requirements outside the selected ledger are not covered.','## Per task']
 rows=[]
 for task,arms in s['tasks'].items():
  for tool in TOOLS:
   x=arms[tool]['public'];d=x['detection']['combined'];r=x['repair'];rows.append([task,tool,frac(d['detectedProductRows'],d['confirmedProductRows']),len(x['clusters']['confirmed']),'/'.join(str(d['counts'][k])for k in ['TP','FP','U']),pct(d['rowMissRate']),frac(r['rowFinalStatuses']['passed'],r['confirmedProductRows']),cov(arms[tool]['allFinal'])])
 parts +=[table(['Task','Tool','Detected rows','Agreed clusters','TP/FP/U alarms','Row miss','Repaired rows','All FINAL P/F/U/N/A'],rows),table(['Macro task recall',*TOOLS],[['Mean recall across defined task denominators',*[pct(s['groups'][t]['macroTaskCombinedRowRecall'])for t in TOOLS]],['Tasks with defined recall',*[s['groups'][t]['macroRecallDefinedTasks']for t in TOOLS]]]),'## Per platform (public)']
 rows=[]
 for pl in ['ios','android']:
  for tool in TOOLS:
   x=s['groups'][tool]['platforms'][pl];d=x['detection']['combined'];r=x['repair'];rows.append([pl,tool,frac(d['detectedProductRows'],d['confirmedProductRows']),'/'.join(str(d['counts'][k])for k in ['TP','FP','U']),frac(r['rowFinalStatuses']['passed'],r['confirmedProductRows']),cov(x['FINAL']),pct(x['FINAL']['unassessedRatio'])])
 parts +=[table(['Platform','Tool','Detected rows','TP/FP/U alarms','Repaired rows','FINAL P/F/U/N/A','U/applicable'],rows),'## Original descriptor compliance (engineering only)']
 parts +=[table(['Metric',*TOOLS],[[k,*[s['groups'][t]['descriptorCompliance'][k]for t in TOOLS]]for k in ['uniqueOriginalAlarms','exactTypedDescriptor','otherOrUnresolvedDescriptor']]),'This is reported separately from semantic detection. Sealed original expectations/units are never rewritten to match later acceptance.','## Consumer and resource costs']
 rows=[]
 for label,key in [('Mean implementation start→own FINAL raw+check endpoint','meanOwnFinalRawAndCheckSeconds'),('Mean implementation start→own FINAL raw seal','meanOwnFinalRawSeconds'),('Mean implementation start→all-six own FINAL closure','meanAllSixClosureSeconds'),('Model phase wall sum (including compile waits)','modelPhaseWallSumSeconds'),('Own native command resource wall sum','ownNativeCommandSumSeconds'),('Recorded own native slot queue sum','nativeQueueSeconds')]:rows.append([label,*[sec(c['groups'][t][key])for t in TOOLS]])
 for phase in ['implementation','review','repair']:rows.append([phase+' model wall sum',*[sec(c['groups'][t]['phaseWallSumSeconds'][phase])for t in TOOLS]])
 parts +=[table(['Recorded quantity',*TOOLS],rows),'Sums include overlapping work; they are not elapsed latency. Consumer endpoints include actual cohort barriers and automatic checks. Shared caches, scheduling/order and only three pairs prevent a causal speed claim. Tokens and money were not observed.','## Shared experiment overhead']
 rows=[[v['phase'],sec(v['wallSeconds']),sec(v['queueSeconds'])]for v in c['acquisitionBatches']]
 parts +=[table(['Acquisition batch','Elapsed span','Resource queue sum'],rows),table(['Shared quantity','Actual'],[['All main native commands',len(g['nativeCommands'])],['All native command resource wall sum',sec(g['nativeCommandWallSumSeconds'])],['18 independent judgment task wall sum',sec(g['judgmentTaskWallSumSeconds'])],['Same-evidence offline replay process wall sum',sec(g['offlineReplayWallSumSeconds'])],['Offline replay extra SDK commands',g['offlineReplaySDKCommands']],['Pre-registration→tool freeze',sec(c['chronology']['preregistrationToToolFreezeSeconds'])],['Tool freeze→design approval',sec(c['chronology']['toolFreezeToDesignApprovalSeconds'])],['Pre-registration→assignment reveal',sec(c['chronology']['preregistrationToRevealSeconds'])]]),'Removing redundant paired acquisition and overlapping public anonymous collection with read-only review are shared infrastructure. They are not exclusive v8 benefits. Publication/CI is separate and visible in Git history and the exact-head Actions run.','## Same-source, same-evidence automatic review diagnostic']
 pair=s['offlineSameEvidence'];counts=pair['counts'];rows=[[status,*[counts[t][status]for t in ['v7','v8']]]for status in ['passed','failed','unassessed']];trans={}
 for item in pair['comparisons']:
  for row in item['rows']:
   key=row['v7']+'→'+row['v8'];trans[key]=trans.get(key,0)+1
 parts +=[f"{pair['configurations']} configurations; {pair['newSDKCommands']} additional SDK commands. Qualitative submissions are withheld in both methods.",table(['Automatic status','v7','v8'],rows),table(['Transition','Rows'],sorted(trans.items())),'This isolates automatic evidence availability on identical raw bytes. It is not proof of better implementation quality, model judgment, native acquisition speed or lower whole-development cost.','[Original metrics](summary.json) · [Primary costs](costs.json) · [Shared judging/replay costs](grading-costs.json) · [Failure records](FAILURES.md) · [Method](PREREGISTRATION.md)']
 audit=ex.read(R/'action-scope.json')
 parts +=['## Acquisition-scope audit',f"{audit['pairCount']} original public own/common launch pairs checked: {audit['exactActionEqualityPairs']} exact action-route matches; {audit['sameBusinessRouteWithoutAfterTargetsPairs']} match after removing only after-target observations; {audit['sameFixtureAndBridgePairs']} have matching fixture and bridge hashes.",'Own generated routes include four after-target observation extensions; common acquisition uses the sealed base routes. Both arms share this observation-scope gap. Missing common evidence remains U; original alarms need original own proof. Own-to-common timing is not a same-route speed comparison. No frozen routes, expectations or verdicts were replaced. [Exact scope audit](action-scope.json) · [Shared harness limitation](ENGINEERING.md#acquisition-scope-gap-found-during-the-frozen-run)']
 return '\n\n'.join(parts)+'\n'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();value=render();path=R/'TABLES.md'
 if a.check:assert path.read_text()==value
 else:assert not path.exists();path.write_text(value)
 print('PASS frozen comparison tables')
if __name__=='__main__':main()
