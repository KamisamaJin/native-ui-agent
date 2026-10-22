#!/usr/bin/env python3
"""Audit actual acquisition scopes without replacing frozen routes or scores."""
import argparse,json
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent

def without_after_targets(value):
 if isinstance(value,dict):return{k:without_after_targets(v)for k,v in value.items()if k!='after_targets'}
 if isinstance(value,list):return[without_after_targets(v)for v in value]
 return value

def compute():
 ex.gate.authorize(R/'gates','reveal',R)
 assignment=ex.read(R/'private/assignment.json');design=R/ex.read(R/'DESIGN-ROOT.json')['directory'];rows=[]
 for task,aliases in assignment['gradeAliases'].items():
  for alias,unit in aliases.items():
   for phase in ['d0','final']:
    own=ex.read(R/'own-corpora'/unit/phase/'corpus.json');common=ex.read(R/'common-corpora'/task/alias/phase/'corpus.json')
    for platform in ['ios','android']:
     actual={v['case']:v for v in common['platformRuns'][platform]}
     for run in own['platformRuns'][platform]:
      case=run['case'];other=actual[case]
      paths=[R/'submissions'/unit/'initial-agent-output/plans'/case/platform/'actions.json',design/task/'public/compiled'/case/('actions.'+platform+'.json')]
      for path,record in zip(paths,[run,other]):assert ex.sha(path)==record['inputHashes']['actions.json']
      left,right=[ex.read(p)for p in paths]
      rows.append({'task':task,'source':alias,'unit':unit,'phase':phase,'platform':platform,'case':case,'ownActions':str(paths[0].relative_to(R)),'commonActions':str(paths[1].relative_to(R)),'ownActionsSHA256':ex.sha(paths[0]),'commonActionsSHA256':ex.sha(paths[1]),'exactEqual':left==right,'equalWithoutAfterTargets':without_after_targets(left)==right,'ownAfterTargetActionCount':sum(bool(v.get('after_targets'))for v in left),'commonAfterTargetActionCount':sum(bool(v.get('after_targets'))for v in right),'commonSweepStates':[v.get('state_id')for v in right if v.get('type')=='sweep'],'fixtureSHAEqual':run['inputHashes']['fixtures.json']==other['inputHashes']['fixtures.json'],'bridgeSHAEqual':run['inputHashes']['bridge']==other['inputHashes']['bridge']})
 assert len(rows)==48,len(rows)
 return {'pairs':rows,'pairCount':len(rows),'exactActionEqualityPairs':sum(v['exactEqual']for v in rows),'sameBusinessRouteWithoutAfterTargetsPairs':sum(v['equalWithoutAfterTargets']for v in rows),'sameFixtureAndBridgePairs':sum(v['fixtureSHAEqual']and v['bridgeSHAEqual']for v in rows),'scope':'Post-acquisition audit of original sealed public launch inputs, not a change to expectations, observations or verdicts. Own compiled routes include additional after-target observations; common routes use the approved base route. Both arms share this scope difference. Missing common evidence remains U. Cross-batch latency is not a collector-speed comparison; original claims require original own evidence. No extra SDK acquisition or retrospective repair is performed.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();value=compute();path=R/'action-scope.json'
 if a.check:assert ex.read(path)==value
 else:assert not path.exists();ex.save(path,value)
 print('PASS original acquisition-scope audit (not route equivalence)')
if __name__=='__main__':main()
