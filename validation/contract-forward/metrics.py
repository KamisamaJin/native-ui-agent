#!/usr/bin/env python3
"""Recompute fixed-denominator metrics; zero denominators remain unavailable."""
import argparse,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def panel(rows):
 c=Counter(r['status']for r in rows);n=sum(c[s]for s in ['P','F','U']);a=c['P']+c['F']
 return {**{s:c[s]for s in ['P','F','U','N/A']},'applicable':n,'unassessedShare':c['U']/n if n else None,'observedShare':a/n if n else None,'conditionalPass':c['P']/a if a else None}
def rows(stage,alias,kind='final'):
 return [r for p in sorted((R/'evaluation'/stage/alias/kind).glob('*/*/grade.json'))for r in read(p)['rows']]
def detection(rs,match):
 fs={r['id']for r in rs if r['status']=='F'};tps={x['fixed_row_id']for x in match['claims']if x['category']=='TP'};n=len(fs)
 return {'naturalFrozenFRows':n,'detected':len(fs&tps),'missed':len(fs-tps),'missShare':len(fs-tps)/n if n else None}
def pair(a,b):
 am={r['id']:r for r in a};bm={r['id']:r for r in b};assert set(am)==set(bm);matrix=Counter();gains=[];losses=[];conflicts=[]
 for i,x in am.items():
  y=bm[i];s,t=x['status'],y['status'];matrix[s+'->'+t]+=1;row={'id':i,'class':x['class'],'platform':x['platform'],'case':x['case'],'state':x['state'],'before':s,'after':t,'beforeActual':x['actual'],'afterActual':y['actual'],'beforeEvidence':x['evidence'],'afterEvidence':y['evidence']}
  if s=='U'and t in ['P','F']:gains.append(row)
  if s in ['P','F']and t=='U':losses.append(row)
  if s in ['P','F']and t in ['P','F']and s!=t:conflicts.append(row)
 return {'v5':panel(a),'v6':panel(b),'gained':len(gains),'lost':len(losses),'netAssessedGain':len(gains)-len(losses),'assessedConflicts':len(conflicts),'matrix':dict(sorted(matrix.items()))},{'gains':gains,'losses':losses,'assessedConflicts':conflicts}
def build():
 assignment=read(R/'private/ASSIGNMENT-RELEASE.json');config=read(R/'private/assignment.json');arms={};pairs={};changes={};allpairs={v:[]for v in ['v5','v6']}
 for alias,unit in assignment['gradeAliases'].items():
  tool=config['units'][unit]['tool'];d0=rows('D0',alias);final=rows('FINAL',alias);comparison=read(R/'evaluation/selfreview'/alias/'comparison.json');classes=sorted({r['class']for r in d0});matched=comparison['combined'];repair=comparison['repair'];uncertain=read(R/'evaluation-inputs/selfreview'/alias/'claims.json')['ineligible_or_qualitative'];tp,fp=matched['TP'],matched['FP'];u=matched['uncertain']+len(uncertain);den=tp+fp+u
  arms[tool]={'unit':unit,'anonymousID':alias,'d0Public':panel(d0),'finalAll':panel(final),'finalPublic':panel([r for r in final if r['case'].startswith('P')]),'finalHidden':panel([r for r in final if r['case'].startswith('H')]),'d0ByClass':{k:panel([r for r in d0 if r['class']==k])for k in classes},'finalByClass':{k:panel([r for r in final if r['class']==k])for k in classes},'finalByPlatform':{p:panel([r for r in final if r['platform']==p])for p in ['ios','android']},'finalByCasePlatform':{c+'/'+p:panel([r for r in final if r['case']==c and r['platform']==p])for c in ['P1','P2','H1']for p in ['ios','android']},'detection':{'combined':detection(d0,matched),'machine':detection(d0,comparison['machine']),'manual':detection(d0,comparison['manual']),'byClass':{k:detection([r for r in d0 if r['class']==k],matched)for k in classes}},'claims':{'TP':tp,'FP':fp,'uncertain':u,'conditionalFDR':fp/(tp+fp)if tp+fp else None,'unknownConservativeBounds':[fp/den,(fp+u)/den]if den else None,'classicalFPR':None,'scope':'Conditional discovery error against frozen assessed rows. Qualitative/ineligible claims remain uncertain; no complete TN universe.'},'repair':repair,'naturalProductSensitivity':read(R/'evaluation/D0/summary.json')['arms'][alias]['natural_product_defect_sensitivity']}
  grades={v:read(R/'evaluation/paired-D0'/alias/v/'grade.json')['rows']for v in ['v5','v6']};native=lambda rs:[r for r in rs if r['class']!='visual'];a,b=native(grades['v5']),native(grades['v6']);summary,changes[alias]=pair(a,b)
  summary['byPlatform']={p:pair([r for r in a if r['platform']==p],[r for r in b if r['platform']==p])[0]for p in ['ios','android']};summary['byClass']={k:pair([r for r in a if r['class']==k],[r for r in b if r['class']==k])[0]for k in classes if k!='visual'}
  summary['costs']={}
  for version,path in [('v5',R/'paired-corpora'/alias/'v5'),('v6',R/'common-corpora'/alias/'d0')]:
   corpus=read(path/'corpus.json');summary['costs'][version]={'commandWallSeconds':sum(r['wallSeconds']for rs in corpus['platformRuns'].values()for r in rs),'byPlatform':{p:sum(r['wallSeconds']for r in rs)for p,rs in corpus['platformRuns'].items()},'snapshots':sum(len(read(path/p/r['case']/'observation.json')['snapshots'])for p,rs in corpus['platformRuns'].items()for r in rs)}
   allpairs[version]+=[dict(r,id=alias+'/'+r['id'])for r in native(grades[version])]
  pairs[alias]=summary
 totals,changes['combined']=pair(allpairs['v5'],allpairs['v6']);totals['commandWallSeconds']={v:sum(p['costs'][v]['commandWallSeconds']for p in pairs.values())for v in ['v5','v6']}
 return {'arms':arms,'pairs':pairs,'pairTotals':totals,'costs':read(R/'costs.json'),'failureSummary':{k:read(R/'failure-index.json')[k]for k in ['nativeCommandCount','snapshotRecords']},'scope':'One fresh complex requirement per arm, both use frozen Skills. Shared approved design and common acceptance; descriptive only. Frozen subresolution geometry F retained and separately limited, no established product/business defect denominator. iOS computed styles unavailable; no token or money estimate.'},changes

def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();result,changes=build()
 for name,data in [('result-summary.json',result),('paired-changes.json',changes)]:
  path=R/name
  if a.write:path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
  else:assert read(path)==data,name
 print(json.dumps({'status':'PASS','arms':list(result['arms']),'pairTotals':result['pairTotals']}))
if __name__=='__main__':main()
