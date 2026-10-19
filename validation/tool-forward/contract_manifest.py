#!/usr/bin/env python3
"""Mechanical expansion of the independent frozen oracle, never an evaluator."""
import json,argparse,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent

def expand(oracle,phase):
 rows=[]
 for source in oracle['sourceAssertions']:
  for platform in source['platforms']:rows.append(dict(source,platform=platform,scope='source',caseId='COMMON',stateId='source'))
 for case in oracle['cases']:
  if phase=='d0'and case['split']!='initial':continue
  for cp in case['checkpoints']:
   assertions=list(cp['assertions'])
   for group in cp['parameterizedGroups']:
    base={k:v for k,v in group.items()if k not in {'groupKey','members'}}
    assertions +=[dict(base,**member,groupKey=group['groupKey'])for member in group['members']]
   for assertion in assertions:
    for platform in assertion['platforms']:
     rows.append(dict(assertion,platform=platform,scope='runtime',caseId=case['caseId'],stateId=cp['stateId'],modelId=cp['modelId'],fullVisualCheckpoint=cp['fullVisualCheckpoint']))
 assert len({(x['platform'],x['key'])for x in rows})==len(rows)
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['d0','final'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();source=R/'design/size-revision/private/oracle.json';rows=expand(json.loads(source.read_text()),a.phase);assert not a.output.exists();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'phase':a.phase,'oracle_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'assessments':rows},indent=2)+'\n');print(json.dumps({'assessments':len(rows),'runtime':sum(x['scope']=='runtime'for x in rows),'source':sum(x['scope']=='source'for x in rows)}))
if __name__=='__main__':main()
