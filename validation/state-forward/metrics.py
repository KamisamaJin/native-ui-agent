#!/usr/bin/env python3
"""Recompute fixed-denominator outcomes, original findings and paired evidence."""
import argparse,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def panel(rows):
 c=Counter(x['status']for x in rows);n=sum(c[s]for s in ['P','F','U']);observed=c['P']+c['F']
 return {'P':c['P'],'F':c['F'],'U':c['U'],'denominator':n,'unassessedShare':c['U']/n if n else None,'observedShare':observed/n if n else None,'conditionalPass':c['P']/observed if observed else None}
def runtime(rows,scope='all',kind='all'):
 return [x for x in rows if x['classification'].startswith('runtime.')and(scope=='all'or(x.get('caseID')or'').startswith(scope))and(kind=='all'or(kind=='native'and x['classification']!='runtime.style.visual')or x['classification'].startswith(kind))]
def detection(rows,manual,typed):
 ids={x['cellID']for x in rows if x['status']=='F'};combined=manual|typed;n=len(ids)
 return {'naturalFRows':n,'denominator':n or None,'manualDetected':len(ids&manual),'typedDetected':len(ids&typed),'combinedDetected':len(ids&combined),'manualMissed':len(ids-manual),'combinedMissed':len(ids-combined),'manualMissShare':len(ids-manual)/n if n else None,'combinedMissShare':len(ids-combined)/n if n else None}
def pair(before,after):
 a={x['cellID']:x for x in before};b={x['cellID']:x for x in after};assert set(a)==set(b)
 changes={'gains':[],'losses':[],'assessedConflicts':[]};matrix=Counter()
 for i,x in a.items():
  y=b[i];s,t=x['status'],y['status'];matrix[s+'->'+t]+=1
  kind='gains'if s=='U'and t in ['P','F']else'losses'if s in ['P','F']and t=='U'else'assessedConflicts'if s in ['P','F']and t in ['P','F']and s!=t else None
  if kind:changes[kind].append({'cellID':i,'classification':x['classification'],'platform':x['platform'],'caseID':x['caseID'],'stateID':x['stateID'],'before':s,'after':t,'beforeActual':x.get('actual'),'afterActual':y.get('actual'),'beforeRefs':x.get('evidenceRefs'),'afterRefs':y.get('evidenceRefs')})
 return {'v4':panel(before),'v5':panel(after),'gainedRows':len(changes['gains']),'lostRows':len(changes['losses']),'netAssessedGain':len(changes['gains'])-len(changes['losses']),'assessedConflicts':len(changes['assessedConflicts']),'matrix':dict(sorted(matrix.items()))},changes
def build():
 release=read(R/'private/ASSIGNMENT-RELEASE.json');mapping=read(R/'private/grade-assignment.json')['mapping'];assigned={x['id']:x for x in read(R/'private/assignment.json')['units']}
 result={'scope':'One new task per Skill arm; fixed public D0, all6 FINAL, same-source paired public runtime; descriptive, not causal. No complete TN universe.','arms':{},'pairs':{},'pairTotals':{},'release':release};changeledger={}
 allpair={v:[]for v in ['v4','v5']}
 for alias,unit in mapping.items():
  tool=assigned[unit]['tool'];d0=read(R/'evaluation/D0'/alias/'grade.json')['rows'];final=read(R/'evaluation/FINAL'/alias/'grade.json')['rows'];comparison=read(R/'evaluation/selfreview'/alias/'comparison.json');matching=comparison['reviewMatching'];manual=set(matching['manualDetectedRows']);typed=set(matching['actualTypedDetectedRows'])
  original=read(R/'evaluation/selfreview'/alias/'comparison-original-reports-only.json')['reviewMatching']
  assert set(original['combinedDetectedRows'])==manual|typed,'Diagnostic reruns must not inflate unique detection'
  before=runtime(d0,'P');after=runtime(final);finalmap={x['cellID']:x for x in final};fixed=[{'cellID':x['cellID'],'classification':x['classification'],'after':finalmap[x['cellID']]['status']}for x in before if x['status']=='F'];f=Counter(x['after']for x in fixed)
  classes=sorted({x['classification']for x in before});declared=read(R/'submissions'/unit/'initial-agent-output/plans-seal.json')
  result['arms'][tool]={'anonymousID':alias,'unit':unit,'d0PublicRuntime':panel(before),'finalRuntime':panel(after),'finalPublicRuntime':panel(runtime(final,'P')),'finalHeldoutRuntime':panel(runtime(final,'H')),'d0ByClass':{c:panel([x for x in before if x['classification']==c])for c in classes},'finalByClass':{c:panel([x for x in after if x['classification']==c])for c in classes},'detection':{'allRuntime':detection(before,manual,typed),'business':detection([x for x in before if x['classification'].startswith('runtime.business.')],manual,typed),'byClass':{c:detection([x for x in before if x['classification']==c],manual,typed)for c in classes}},'repair':{'denominator':len(fixed)or None,'FtoP':f['P'],'FtoF':f['F'],'FtoU':f['U'],'verifiedPassShare':f['P']/len(fixed)if fixed else None},'claims':{k:matching[k]for k in ['claimCounts','conditionalFalseDiscoveryShare','allUncertainConservativeInterval','classicalFPR','byScope']},'originalPlanSealShape':'dict'if isinstance(declared['files'],dict)else'list'}
  keys=['claimCounts','conditionalFalseDiscoveryShare','allUncertainConservativeInterval','classicalFPR','byScope']
  result['arms'][tool]['claimsAllActualReports']=result['arms'][tool]['claims']
  result['arms'][tool]['claims']={k:original[k]for k in keys}
  result['arms'][tool]['claimPanels']=read(R/'evaluation/selfreview'/alias/'claim-panels.json')
  grades={v:read(R/'evaluation/paired-D0'/alias/v/'grade.json')['rows']for v in ['v4','v5']}
  assert grades['v5']==d0,'Paired v5 literal rows must be exact original common-D0 reuse'
  a,b=[runtime(grades[v],'P')for v in ['v4','v5']];summary,changes=pair(a,b);summary['nativeOnly'],_=pair(runtime(grades['v4'],'P','native'),runtime(grades['v5'],'P','native'))
  summary['byClass']={c:pair([x for x in a if x['classification']==c],[x for x in b if x['classification']==c])[0]for c in classes}
  summary['byPlatform']={p:pair([x for x in a if x['platform']==p],[x for x in b if x['platform']==p])[0]for p in ['ios','android']}
  costs={};snapshots={}
  for v,path in [('v4',R/'paired-corpora'/alias/'v4'),('v5',R/'common-corpora'/alias/'d0')]:
   corpus=read(path/'corpus.json');costs[v]={p:sum(x['wallSeconds']for x in runs)for p,runs in corpus['platformRuns'].items()};costs[v]['total']=sum(costs[v].values());snapshots[v]=sum(len(read(path/p/x['case']/'observation.json')['snapshots'])for p,runs in corpus['platformRuns'].items()for x in runs)
  summary['actualCommandWallSeconds']=costs;summary['snapshotRecords']=snapshots;result['pairs'][alias]=summary;changeledger[alias]=changes
  for v in ['v4','v5']:allpair[v]+=[dict(x,cellID=alias+'/'+x['cellID'])for x in runtime(grades[v],'P')]
 result['pairTotals'],changeledger['combined']=pair(allpair['v4'],allpair['v5']);result['pairTotals']['actualCommandWallSeconds']={v:sum(x['actualCommandWallSeconds'][v]['total']for x in result['pairs'].values())for v in ['v4','v5']}
 result['costs']=read(R/'costs.json');result['failures']={'plannedNativeCommands':88,'retainedNonzeroExits':len(read(R/'failure-index.json')['unsuccessfulNativeAcquisitions']),'snapshotRecords':1891}
 return result,changeledger
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();result,changes=build()
 for name,data in [('result-summary.json',result),('paired-changes.json',changes)]:
  path=R/name
  if a.write:path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
  else:assert read(path)==data,name+' differs from fixed rows'
 print(json.dumps({'status':'PASS','arms':list(result['arms']),'paired':result['pairTotals']}))
if __name__=='__main__':main()
