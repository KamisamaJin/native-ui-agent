#!/usr/bin/env python3
"""Retain all scored failures, unknown reasons and acquisition nonzero exits."""
import argparse,collections,json
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
def build():
 ex.gate.verify(R/'gates','reveal',R);grades=[];native=[];unknown=collections.Counter()
 for stage in ['D0','FINAL']:
  for p in sorted((R/'evaluation'/stage).glob('*/*/*/*/grade*.json')):
   data=ex.read(p)
   for row in data.get('rows',[]):
    canonical=p.name in ['grade.json','grade-unavailable.json']
    if row['status']=='F':grades.append({'grade':str(p.relative_to(R)),'gradeSHA256':ex.sha(p),'recordKind':'canonical'if canonical else'preserved_attempt','row':row})
    if row['status']=='U'and canonical:unknown[(stage,row['platform'],row['class'],row['reason'])]+=1
 for directory in ['own-corpora','common-corpora','paired-corpora']:
  for p in sorted((R/directory).rglob('corpus.json')):
   for platform,runs in ex.read(p).get('platformRuns',{}).items():
    for row in runs:
     if row['exitCode']!=0:native.append({'corpus':str(p.relative_to(R)),'platform':platform,'command':row})
 compiles={}
 for unit in sorted((R/'submissions').iterdir()):
  for folder in ['initial-agent-output','final-agent-output']:
   for p in sorted((unit/folder).rglob('*.json')):
    d=ex.read(p)
    if not isinstance(d,dict)or d.get('kind')!='common_compile_only_no_render':continue
    key=json.dumps([d['argv'],d['startedAtUnix']],sort_keys=True);entry=compiles.setdefault(key,{'record':d,'evidence':[]});entry['evidence'].append(str(p.relative_to(R)))
 return {'acceptanceFailures':grades,'nativeNonzeroExits':native,'compileOnlyAttempts':list(compiles.values()),'compileOnlyNonzeroExits':[x for x in compiles.values()if x['record']['exitCode']!=0],'unassessedReasons':[dict(stage=k[0],platform=k[1],assertionClass=k[2],reason=k[3],count=v)for k,v in sorted(unknown.items())],'additionalPreservedRecords':['generic-runs.json','generic-summary.json','operators/root-neutral-limitations.json','operators/preimplementation-design-review.json','operators/publication-alias-preflight.json','operators/actual-wrapper-early-launch.json','operators/shared-environment-correction-record.json','operators/shared-environment-tests-attempt-1.log','shared-environment-v1/PROTOCOL.md','supplement/','grader-disagreements.json','GRADER-DISAGREEMENTS.md'],'scope':'Unmodified original F/U dispositions. Independent cause classification lives alongside the scored failures. Failed engineering controls, rejected design cohort and old trial records remain available.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();v=build();out=R/'failures.json'
 if a.write:assert not out.exists();ex.save(out,v)
 else:assert ex.read(out)==v
 print(json.dumps({'status':'PASS','canonicalAcceptanceFailures':sum(r['recordKind']=='canonical'for r in v['acceptanceFailures']),'allPreservedFailureRows':len(v['acceptanceFailures']),'nativeNonzeroExits':len(v['nativeNonzeroExits'])}))
if __name__=='__main__':main()
