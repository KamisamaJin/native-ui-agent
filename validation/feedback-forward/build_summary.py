#!/usr/bin/env python3
"""Recompute paired outcomes and observed endpoint costs; no score rewriting."""
import argparse
import study as s
import claim_analysis,metrics,delivery_metrics,final_outcome_metrics,source_outcomes
import design_contract as d,requirement_routes,acceptance
R=s.R

def must_keys(task):
 out=set()
 for name in ['P1','P2','H1']:
  scope=R/'design'/task/('private'if name=='H1'else'public');approval=s.read(scope/'approval.json')
  for pl in ['ios','android']:
   plan=s.read(scope/'compiled'/name/pl/'plan.json');cov=requirement_routes.audit(s.read(scope/'design-lock.json'),approval['design_lock_sha256'],plan,s.read(scope/'routes.json'),approval['routes_sha256'])
   out|={pl+'/'+name+'/'+rid for o in cov['obligations']if o['priority']=='must'for rid in o['assertion_ids']}
 return out

def self_rows(unit,task):
 result=[]
 for pl in ['ios','android']:
  for name in ['P1','P2']:
   path=R/'self-final'/unit/pl/name/'report.json'
   if path.is_file():rows=s.read(path)['assertions']
   else:rows=[{'id':r['id'],'status':'unassessed'}for r in s.read(R/'design'/task/'public/compiled'/name/pl/'plan.json')['assertions']]
   result += [dict(row,key=pl+'/'+name+'/'+row['id'],case=name,platform=pl)for row in rows]
 return result

def build():
 s.gate.authorize(R/'gates','reveal',R);assignment=s.read(R/'private/assignment.json');units={};pairs={}
 for task,aliases in assignment['gradeAliases'].items():
  initial=claim_analysis.truth('d0',task,'initial');must=must_keys(task);pair={}
  author=s.read(R/'submissions'/task/'initial-agent-output/implementation.json');initial_raw=s.read(R/'corpora'/task/'d0/corpus.json')
  author_seconds=author['finishedAtUnix']-author['startedAtUnix'];initial_seconds=initial_raw['finishedAtUnix']-initial_raw['startedAtUnix']
  for alias,unit in aliases.items():
   cfg=assignment['units'][unit];final=claim_analysis.truth('final',task,alias);claims=s.read(R/'evaluation/claims'/task/alias/'metrics.json')
   handoff=s.read(R/'operators'/(unit+'-handoff.json'))['handoffAtUnix'];automatic=s.read(R/'endpoints'/(unit+'.json'));runtime_endpoint=s.read(R/'self-final'/unit/'endpoint.json');self_endpoint=s.read(R/'self-complete'/unit/'endpoint.json')
   requests=[s.read(p/'evidence/corpus.json')for p in sorted((R/'feedback'/unit).glob('request-*'))]if(R/'feedback'/unit).exists()else[]
   final_native=s.read(R/'corpora'/unit/'final-public/corpus.json');all_native=[*requests,final_native]
   execution_rows=[v for corpus in all_native for v in corpus['runs']]
   timed=[r for r in execution_rows if'nativeFinishedAtUnix'in r];api=s.read(R/'source-api'/unit/'final/record.json')
   own=self_rows(unit,task);outcome=final_outcome_metrics.summarize(final,own,must,self_accepted=self_endpoint['accepted'])
   self_seconds=self_endpoint['finishedAtUnix']-handoff
   cost={'handoffToAutomaticSeconds':automatic['finishedAtUnix']-handoff,'handoffToRuntimeSelfCheckSeconds':runtime_endpoint['finishedAtUnix']-handoff,'handoffToCompleteSelfCheckSeconds':self_seconds,'selfAcceptedLatencySeconds':self_seconds if self_endpoint['accepted']else None,'sharedInitialAuthoringSeconds':author_seconds,'sharedInitialEvidenceSeconds':initial_seconds,
         'authoringPlusEvidencePlusFullSelfCheckSeconds':author_seconds+initial_seconds+self_seconds,'observedInitialAuthorStartToSelfCheckSeconds':self_endpoint['finishedAtUnix']-author['startedAtUnix'],
         'observedSharedDesignPreparationStartToSelfCheckSeconds':self_endpoint['finishedAtUnix']-s.read(R/'gates/tools.json')['sealedAtUnix'],
         'feedbackRequests':len(requests),'feedbackServiceSeconds':sum(v['finishedAtUnix']-v['startedAtUnix']for v in requests),'nativeRequestWallSumSeconds':sum(v['finishedAtUnix']-v['startedAtUnix']for v in execution_rows),'nativeQueueSumSeconds':sum(v.get('queueSeconds',0)for v in execution_rows),
         'recordedNativeSubprocessWallSumSeconds':sum(v['nativeFinishedAtUnix']-v['startedAtUnix']for v in timed),'recordedAfterNativeAutomaticWallSumSeconds':sum(v['finishedAtUnix']-v['nativeFinishedAtUnix']for v in timed),'nativeTimingUnrecordedRequests':len(execution_rows)-len(timed),'minimumSourceAPISubprocessSeconds':sum(v['finishedAtUnix']-v['startedAtUnix']for v in api['commands']),'tokens':None,'money':None,
         'scope':'Raw observed per-unit endpoints, same shared initial authoring/evidence cost assigned to both arms. Resource walls can overlap and are not added to latency. Self acceptance is AI self-verification; independent/public/hidden truth remains separate.'}
   source_initial=s.read(R/'evaluation/source/d0'/task/'initial/acceptance.json')['rows'];source_final=s.read(R/'evaluation/source/final'/task/alias/'acceptance.json')['rows']
   source_own0=s.read(R/'source-self'/unit/'original/report.json')['rows'];source_own=s.read(R/'source-self'/unit/'final/report.json')['rows']
   source_result=source_outcomes.summarize(source_initial,source_final,source_own0,source_own,complete_accepted=self_endpoint['accepted'])
   final_by={r['key']:r for r in final};strict={r['key']:final_by[r['key']]['status']for r in initial if r['status']=='failed'}
   value={'unit':unit,'task':task,'alias':alias,'condition':cfg['tool'],'initial':metrics.coverage(initial),'final':metrics.coverage(final),'finalPublic':metrics.coverage([r for r in final if r['case']in{'P1','P2'}]),'hidden':metrics.coverage([r for r in final if r['case']=='H1']),'originalDetection':claims['detection'],'repair':claims['repair'],'clusters':claims['clusters'],
          'finalOutcome':outcome,'sourceOutcome':source_result,'strictDiagnosticTransitions':{'rows':strict,'counts':{k:sum(v==k for v in strict.values())for k in ['passed','failed','unassessed','not_applicable']},'scope':'Raw original strict-F transitions only, irrespective of cause. Not a confirmed product repair rate or independent bug count.'},'delivery':delivery_metrics.compare(initial,final,claims['clusters']['confirmed'],must),'selfCheck':self_endpoint,'runtimeSelfCheck':runtime_endpoint,'cost':cost}
   units[unit]=value;pair[cfg['tool']]=value
  pairs[task]={tool:{'unit':v['unit'],'finalPublicProductFailures':v['finalOutcome']['confirmedFinalPublicMustProductFailures'],'finalKnownMisses':len(v['finalOutcome']['finalKnownFalseNegatives']),'finalUnresolvedProductFailures':len(v['finalOutcome']['finalUnresolvedProductFailures']),'finalFalseAlarmRows':len(v['finalOutcome']['finalKnownFalseAlarmRows']),'confirmedProductRegressions':len(v['delivery']['confirmedProductRegressions']),'productRowRepairRate':v['repair']['productRowRepairRate'],'clusterRepairRate':v['repair']['clusterRepairRate'],'sourceOnlyOutcome':v['sourceOutcome'],'selfAccepted':v['selfCheck']['accepted'],'handoffToCompleteSelfCheckSeconds':v['cost']['handoffToCompleteSelfCheckSeconds'],'authoringEvidenceFullSelfSeconds':v['cost']['authoringPlusEvidencePlusFullSelfCheckSeconds']}for tool,v in pair.items()}
 times={name:s.read(R/'gates'/(name+'.json'))['sealedAtUnix']for name in ['tools','design-review','d0-sources','d0-raw','public-final','hidden','claims-two','reveal']}
 spans={'neutralEngineeringAndReleaseWallSeconds':times['tools']-s.read(R/'PREREGISTRATION.json')['recordedAtUnix'],'sharedDesignProtocolPreparationWallSeconds':times['design-review']-times['tools'],'allInitialAuthoringAndSourceBarrierWallSeconds':times['d0-sources']-times['design-review'],'initialEvidenceAndCohortBarrierWallSeconds':times['d0-raw']-times['d0-sources'],'allArmsAndFullSelfCheckBarrierWallSeconds':times['public-final']-times['d0-raw'],'heldoutCollectionWallSeconds':times['hidden']-times['public-final'],'externalIndependentGradingAndClaimsWallSeconds':times['claims-two']-times['hidden'],'wholeStudyThroughRevealWallSeconds':times['reveal']-s.read(R/'PREREGISTRATION.json')['recordedAtUnix'],'scope':'Stage-to-stage wall clocks include operator gaps and concurrent work; not active labor, independent resources, or amortized single-PR production cost. Design/contract preparation is shared and substantial, not silently excluded from observed full study cost. Publishing/CI occurs later.'}
 return {'units':units,'pairs':pairs,'studySpans':spans,'neutralPerformance':s.read(R/'benchmark-summary.json'),'scope':'Two fresh feature pairs share ONE naturally authored initial PR per task. Incremental v8/v9 decision-tool comparison with SHARED optimized execution infrastructure. No artificial defects; unknowns, failures and AI disagreement retained. Descriptive paired observations, not a general causal or P90 claim.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();value=build();path=R/'summary.json'
 if a.check:assert s.read(path)==value
 else:s.save(path,value)
 print('PASS paired original/final quality and observed consumer cost recomputation')
if __name__=='__main__':main()
