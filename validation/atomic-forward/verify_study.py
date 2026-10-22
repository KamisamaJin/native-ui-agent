#!/usr/bin/env python3
"""SDK-free integrity, phase chronology and exact-source verification."""
import json,sys
from pathlib import Path
import experiment as ex
import evaluation_adapter as evaluation
import claim_panels
import metrics
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'candidate-v8/scripts'));import design_contract as d

def main():
 ex.gate.verify(R/'gates','reveal',R);assignment=ex.read(R/'private/assignment.json')
 for tool in ['baseline-v7','candidate-v8']:
  freeze=ex.read(R/(tool+'-freeze.json'));actual={str(p.relative_to(R/tool)):ex.sha(p)for p in (R/tool).rglob('*')if p.is_file()and'__pycache__'not in p.parts};assert actual==freeze['files']
 live={str(p.relative_to(R.parents[1]/'native-ui-agent')):ex.sha(p)for p in (R.parents[1]/'native-ui-agent').rglob('*')if p.is_file()and'__pycache__'not in p.parts};assert live==ex.read(R/'candidate-v8-freeze.json')['files']
 design=R/ex.read(R/'DESIGN-ROOT.json')['directory'];count=0;budget=[]
 for unit,config in assignment['units'].items():
  base=R/'submissions'/unit;public=design/config['task']/'public';lock=ex.read(public/'design-lock.json');approval=ex.read(public/'approval.json')
  for case in ['P1','P2']:
   for pl in ['ios','android']:
    folder=base/'initial-agent-output/plans'/case/pl;actions=d.verify_generated(ex.read(folder/'plan.json'),lock,approval['design_lock_sha256'],pl);assert d.canonical(actions)==d.canonical(ex.read(folder/'actions.json'))
  for phase,which in [('d0','d0-sources'),('final','final-sources')]:
   source=ex.read(base/phase/'seal.json')['files'];assert source=={str(p.relative_to(base/phase/'source')):ex.sha(p)for p in (base/phase/'source').rglob('*')if p.is_file()}
   corpus=ex.read(R/'own-corpora'/unit/phase/'corpus.json');assert corpus['source']==source;assert corpus['startedAtUnix']>=ex.read(R/'gates'/(which+'.json'))['sealedAtUnix'];count+=sum(len(rows)for rows in corpus['platformRuns'].values())
  for phase,path,gate,limit in [('initial',base/'initial-agent-output/implementation.json','design',1500),('review',base/'original-review/review.json','own-d0',720),('repair',base/'final-agent-output/repair.json','reviews',900)]:
   row=ex.read(path);assert row['startedAtUnix']>=ex.read(R/'gates'/(gate+'.json'))['sealedAtUnix'];wall=row['finishedAtUnix']-row['startedAtUnix'];assert wall>=0;budget.append({'unit':unit,'phase':phase,'wallSeconds':wall,'limit':limit,'withinBudget':wall<=limit})
 for phase in ['d0','final']:
  evaluation.verify_delivery(R/'evaluation-inputs'/phase)
  for task in ['T1','T2','T3']:
   for alias in ['source-a','source-b']:
    unit=assignment['gradeAliases'][task][alias]
    corpus=ex.read(R/'common-corpora'/task/alias/phase/'corpus.json');assert corpus['source']==ex.read(R/'submissions'/unit/phase/'seal.json')['files'];count+=sum(len(rows)for rows in corpus['platformRuns'].values())
    for base in sorted((R/'evaluation-inputs'/phase/task/alias).glob('*/*')):
     pl,case=base.parts[-2:];paths=[R/'judgments'/phase/panel/task/alias/pl/case/'judge.json'for panel in ['one','two']];expected=evaluation.panel_report(phase,task,alias,pl,case,*paths);assert ex.read(R/'evaluation'/phase/task/alias/pl/case/'acceptance.json')==expected
 assert count==108,count
 for task in ['T1','T2','T3']:
  for alias in ['source-a','source-b']:
   base=R/'evaluation/claims'/task/alias;assert metrics.summarize(ex.read(base/'metric-input.json'))==ex.read(base/'metrics.json')
 assert ex.sha(R/'private/assignment.json')==ex.read(R/'operators/assignment-commitment.json')['assignmentSHA256']
 print(json.dumps({'verifiedMainNativeCommands':count,'budgetChecks':budget,'scope':'Native SDKs are not rerun. Original evidence, frozen executable methods, complete cohort ordering and regenerated consensus/metrics are verified. Preserved native/measurement/product failures do not become hidden passes.'},indent=2))
if __name__=='__main__':main()
