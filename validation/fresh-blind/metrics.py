#!/usr/bin/env python3
"""Recalculate descriptive trial metrics from sealed independent decisions."""
import json,hashlib
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def rows(grade,platform):return {(c['caseId'],r['ruleId']):r['status'] for c in grade['platforms'][platform]['cases'] for r in c['ratings']}
def pairs(value):return {(x['caseId'],x['ruleId'])for x in value}
def ratio(a,b):return round(a/b,6)if b else None
def counts(values):
 c=Counter(values);return {k:c[k]for k in ['passed','failed','unassessed']}

def coverage_scope():
 p=R/'design/grader/coverage-scope-addendum.json';d=read(p)
 return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'postDetectionReportingAudit':True,'exhaustiveFullRequirementRollupAvailable':d['conservativeFullRequirementCoverageRollup']['fullRequirementCoverageRollupAvailable'],'documentedScopeSummary':d['documentedScopeSummary'],'knownExclusionUpperBounds':{x['artifactId']:{k:c[k]for k in ['sealedCountsUnchanged','knownPassedEntriesWithRequiredTouchRegionGap','maximumPossibleFullySupportedPassEntriesAfterKnownExclusions']}for x in d['conservativeFullRequirementCoverageRollup']['knownScopeExclusionBounds']for c in x['cohorts']if c['cohort']=='all'},'meaning':'Upper bounds only, not fully verified pass counts; no original grades/detection/repair credit changed.'}

def calculate():
 release=read(R/'unblinding.json');matches=read(R/'design/grader/review-match.json');out={}
 for sub,arm in release['submissions'].items():
  result={}
  for platform in ['android','ios']:
   d0=read(R/'design/grader'/f'{sub}-d0-{platform}.json');final=read(R/'design/grader'/f'{sub}-final-{platform}.json')
   first=rows(d0,platform);last=rows(final,platform);failed={k for k,v in first.items()if v=='failed'}
   match=matches['submissions'][sub]['platforms'][platform]
   tp=pairs(match['exactRuleTP']);assert tp<=failed
   clusters={x['id']for x in d0['clusters']if x['platform']==platform};cluster_tp=set(match['clusterTP']);assert cluster_tp<=clusters
   resolved={k for k in failed if last.get(k)=='passed'};remaining={k for k in failed if last.get(k)=='failed'};repair_unassessed=failed-resolved-remaining
   regressions={k for k,v in first.items()if v=='passed'and last.get(k)=='failed'}
   newly_observed={k for k,v in first.items()if v=='unassessed'and last.get(k)=='failed'}
   heldout={k:v for k,v in last.items()if k[0].startswith('repair_holdout_')}
   visual={p:{c['caseId']:c['visualScore']for c in grade['platforms'][platform]['cases']} for p,grade in [('d0',d0),('final',final)]}
   result[platform]={'d0':counts(first.values()),'final':counts(last.values()),
    'defectClusters':len(clusters),'rootCauseDetection':{'TP':len(cluster_tp),'FN':len(clusters-cluster_tp),'missRate':ratio(len(clusters-cluster_tp),len(clusters))},
    'exactRuleDetection':{'TP':len(tp),'FN':len(failed-tp),'missRate':ratio(len(failed-tp),len(failed)),'FP':len(pairs(match['falsePositiveRulePairs'])),'FPFindings':len(match['falsePositiveFindings']),'uncertainFindings':len(match.get('uncertainFindings',[]))},
    'repair':{'resolvedClusters':sum(all(last.get((x['caseId'],x['ruleId']))=='passed'for x in c['affected'])for c in d0['clusters']if c['platform']==platform),'clusterDenominator':len(clusters),'resolved':len(resolved),'denominator':len(failed),'successRate':ratio(len(resolved),len(failed)),'remainingFailed':len(remaining),'unassessed':len(repair_unassessed)},
    'initialCaseTransitions':dict(Counter(v+'->'+last.get(k,'unassessed')for k,v in first.items())),'regressions':len(regressions),'newlyObservedInitialFailures':len(newly_observed),'holdout':counts(heldout.values()),
    'visualScores':visual,'visualRationales':{p:{c['caseId']:c.get('visualRationale')for c in grade['platforms'][platform]['cases']}for p,grade in [('d0',d0),('final',final)]},'visualScoreScope':'Observed regions only; partial case rationale is retained. A numeric visual score does not pass unobserved requirements.','visualMeanD0':round(sum(visual['d0'].values())/len(visual['d0']),3),'visualMeanFinal':round(sum(visual['final'].values())/len(visual['final']),3)}
  out[arm]={'submission':sub,'platforms':result}
 return {'schemaVersion':1,'task':'service_visit_rescheduling','nativeCaptures':84,'cleanReplayCapturesOutsideTrial':2,'initialCaseRulePairsPerPlatform':59,'finalCaseRulePairsPerPlatform':84,'arms':out,'timing':read(R/'timing.json'),'coverageScopeAudit':coverage_scope(),'limits':['One task, one run per arm, correlated platforms; descriptive, no causal or statistical generalization.','Common improved native observers available in all arms; observer gains are not a v2-only advantage.','Shared hardware/cache and unmeasured service/model seeds; timings are descriptive.','Source checks are separate from runtime case-rule counts; unavailable evidence is not a pass.','Android semantic activation is not physical OS touch; iOS runtime26.5 does not prove runtime14 compatibility.']}

def main():
 result=calculate();p=R/'result-summary.json';p.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':'recalculated','output':str(p)}))
if __name__=='__main__':main()
