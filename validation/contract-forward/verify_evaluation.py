#!/usr/bin/env python3
"""Replay frozen design grades; validate AI decisions as sealed evidence, not human gold."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module():
 p=R/'design/private/grader.py';s=importlib.util.spec_from_file_location('contract_oracle',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
 # Prefer this publication's files when original absolute checkouts still exist.
 # This relocates references only; no measurement or scoring value is modified.
 def remap(p,root):
  p=Path(p);marker='/validation/contract-forward/'
  if p.is_absolute()and p.is_relative_to(root):return p
  if marker in str(p):return root/str(p).split(marker,1)[1]
  return p if p.is_absolute() else root/p
 m.remap=remap;return m

def canonical_paths(v):
 if isinstance(v,dict):return {k:canonical_paths(x)for k,x in v.items()}
 if isinstance(v,list):return [canonical_paths(x)for x in v]
 if isinstance(v,str)and v.startswith(str(R)+'/'):return 'TRIAL/'+v[len(str(R))+1:]
 if isinstance(v,str)and'/validation/contract-forward/'in v:return 'TRIAL/'+v.split('/validation/contract-forward/',1)[1]
 return v

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['D0','FINAL']);args=parser.parse_args();m=module();total=0
 for stage in [args.stage]if args.stage else ['D0','FINAL']:
  folder=R/'evaluation'/stage;seal=read(folder/'SEAL.json')
  for rel,h in seal['files'].items():assert sha(folder/rel)==h,(stage,rel)
  for path in sorted(folder.glob('source-*/*/*/*/grade.json')):
   alias,kind,case,platform=path.relative_to(folder).parts[:4];original=read(path);obs=m.remap(original['rows'][0]['evidence']['observation'],R)
   source=next(x for x in original['checks']if x['requirement']=='production-file').get('actual');source_root=None
   # Source-root depth should be derived from the known grader-owned relative file.
   if source:
    suffix='Sources/AlertToast/WorkshopEnrollmentCard.swift'if platform=='ios'else'app/src/main/java/com/example/reply/ui/components/WorkshopEnrollmentCard.kt';source_root=Path(str(m.remap(source,R))[:-len(suffix)])
   manual=path.parent/'manual.json';api=path.parent/'api-review.json'
   expected=m.grade(case,platform,obs,R,manual if manual.is_file()else None,source_root,api if api.is_file()else None)
   assert canonical_paths(expected)==canonical_paths(original),(path,'frozen grade replay differs')
   assert len(original['rows'])==24*({'P1':5,'P2':6,'H1':5}[case]);total+=1
 # Matching/repair and paired replay are checked only after their dual stage seals.
 folder=R/'evaluation/selfreview'
 if(folder/'SEAL.json').exists():
  for alias in ['source-a','source-b']:
   claims=read(R/'evaluation-inputs/selfreview'/alias/'claims.json');d0=read(R/'evaluation-inputs/selfreview'/alias/'d0-grade.json');final=read(R/'evaluation-inputs/selfreview'/alias/'final-grade.json');record=read(folder/alias/'comparison.json')
   for label,cs in [('machine',claims['machine']),('manual',claims['manual']),('combined',claims['machine']+claims['manual'])]:assert m.match_claims(d0,cs)==record[label],(alias,label)
   assert m.repair(d0,final)==record['repair']
 folder=R/'evaluation/paired-D0'
 if(folder/'SEAL.json').exists():
  for alias in ['source-a','source-b']:
   for version in ['v5','v6']:
    aggregate=read(folder/alias/version/'grade.json');allrows=[]
    for case in ['P1','P2']:
     for platform in ['ios','android']:
      path=folder/alias/version/'native-base'/case/platform/'grade.json';original=read(path)
      if version=='v6':assert path.read_bytes()==(R/'evaluation/D0'/alias/'native-base'/case/platform/'grade.json').read_bytes(),'V6 original native-base reuse changed'
      else:
       obs=R/'paired-corpora'/alias/'v5'/platform/case/'observation.json';expected=m.grade(case,platform,obs,R)
       assert canonical_paths(expected)==canonical_paths(original),(path,'paired frozen replay differs')
      allrows+=original['rows']
    assert {r['id']:r for r in aggregate['rows']}=={r['id']:r for r in allrows},(alias,version,'paired aggregate differs')
 print(json.dumps({'status':'PASS','replayedNativeAndFinalCaseGrades' :total,'scope':'AI visual/API judgments retain original SHA-bound evidence; replay validates their application, not an independent human gold standard.'}))
if __name__=='__main__':main()
