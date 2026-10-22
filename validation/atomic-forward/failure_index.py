#!/usr/bin/env python3
"""Index preserved strict failures, unknowns and engineering attempts without rescoring."""
import argparse
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
def compute():
 ex.gate.authorize(R/'gates','reveal',R);commands=[];strict=[];unknown=[]
 for pattern in ['own-corpora/*/*/corpus.json','common-corpora/*/*/*/corpus.json']:
  for p in sorted(R.glob(pattern)):
   data=ex.read(p)
   for pl,rows in data.get('platformRuns',{}).items():
    commands += [{'record':str(p.relative_to(R)),'platform':pl,'case':v['case'],'exitCode':v['exitCode'],'startedAtUnix':v['startedAtUnix'],'finishedAtUnix':v['finishedAtUnix']}for v in rows]
 assert len(commands)==108,len(commands)
 for p in sorted(R.glob('evaluation/*/*/*/*/*/acceptance.json')):
  report=ex.read(p)
  for row in report['rows']:
   if row['status']not in {'failed','unassessed'}:continue
   value={'report':str(p.relative_to(R)),'assertion_id':row['id'],'state':row.get('state'),'requirement_id':row.get('requirement_id'),'cause_category':row.get('cause_category'),'row':row}
   (strict if row['status']=='failed'else unknown).append(value)
 preserved=[]
 for pattern in ['operators/*attempt*','operators/*retry*','operators/*control*','operators/design-scope-deviation.json','operators/preseal-launch-control.json','adapter-revisions/**/*','design-review/**/review.json','design-review-v2/**/review.json','independent-probe/REPORT*','independent-probe/**/rejected*','submissions/*/original-review/**/*','submissions/*/initial-agent-output/inspection-record*']:
  preserved += [str(p.relative_to(R))for p in R.glob(pattern)if p.is_file()and'cache'not in p.parts and'__pycache__'not in p.parts]
 ownchecks=[]
 for p in sorted(R.glob('submissions/*/own-checks/*/*/*/command.json')):
  v=ex.read(p);ownchecks.append({'record':str(p.relative_to(R)),'exitCode':v['exitCode'],'reportExists':v['reportExists']})
 return {'mainNativeCommands':commands,'mainNativeNonzeroExits':[v for v in commands if v['exitCode']!=0],'strictAcceptanceFailures':strict,'unassessedAcceptanceRows':unknown,'ownCheckCommands':ownchecks,'preservedEngineeringAndOriginalReviewRecords':sorted(set(preserved)),'scope':'Strict F does not alone establish a product defect; cause disagreements and missing observations remain separate. All original SDK, schema, design and metrology attempts remain in the publication manifest. Neutral synthetic controls are labeled engineering tests, never seeded product defects.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();value=compute();path=R/'FAILURES.json'
 if a.check:assert ex.read(path)==value
 else:assert not path.exists();ex.save(path,value)
 print('PASS preserved failures and unknowns')
if __name__=='__main__':main()
