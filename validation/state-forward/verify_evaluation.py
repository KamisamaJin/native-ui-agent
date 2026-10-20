#!/usr/bin/env python3
"""Replay frozen native normalization and grading, independent of old absolute paths.

Manual screenshot/source judgments remain explicitly AI-reviewed records. This
verifier checks their sealed bytes and arithmetic, not a human visual gold.
"""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def local(ref):
 marker='/validation/state-forward/'
 assert marker in ref,ref
 return R/ref.split(marker,1)[1].split('#',1)[0]
def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['D0','FINAL','selfreview','paired-D0']);a=p.parse_args()
 root=R/'evaluation';stages=[a.stage]if a.stage else ['D0','FINAL','selfreview','paired-D0']
 oracle=read(R/'design/private/oracle.json');ledger=read(R/'design/private/states-ledger.json')
 sys.path.insert(0,str(R/'candidate-v5/scripts'));helper=load('verified_native_helper',R/'candidate-v5/scripts/native_checks.py')
 modules={v:(load('verified_norm_'+v,base/'normalize.py'),load('verified_grade_'+v,base/'grade.py'))for v,base in [('v3',R/'design/private'),('v2',R/'design/history/grader-v2/private')]}
 gradecount=casecount=0
 for stage in stages:
  folder=root/stage;seal=read(folder/'SEAL.json')
  for item in seal['files']:assert sha(folder/item['path'])==item['sha256'],(stage,item['path'])
  for path in sorted(folder.rglob('*grade.json')):
   if path.name=='native-grade.json':evidence=path.parent/'native-normalized.json'
   else:evidence=path.parent/'normalized.json'
   assert evidence.exists(),path
   version='v2'if'v2'in path.relative_to(folder).parts else'v3';grader=modules[version][1]
   actual=read(path);expected=grader.grade(oracle,read(evidence))
   for key,value in expected.items():assert actual[key]==value,(path,key)
   assert len(actual['rows'])==15316 and actual['summary']['all']['denominator']==14420 and actual['summary']['all']['NA']==896
   gradecount+=1
  for path in sorted(folder.glob('**/by-case/*.json')):
   original=read(path);platform,cid=path.stem.split('-',1);version='v2'if'v2'in path.relative_to(folder).parts else'v3'
   rawref,mapref=original['rawEvidence'][:2]
   norm=modules[version][0].normalize(oracle,ledger,read(local(rawref)),read(local(mapref)),platform,cid,original['anonymousID'],original['stage'],helper,rawref,mapref)
   # The delivered interchange is JSON: native candidate tuples serialize to
   # arrays. Compare that exact JSON round trip, without changing any value.
   assert json.loads(json.dumps(norm))==original,(path,'native normalization replay differs')
   casecount+=1
  for path in sorted(folder.glob('*/measurement-sensitivity.json')):
   data=read(path);before=read(local(data['v2OriginalGrade']));after=read(local(data['v3CorrectedGrade']))
   changes=[x['cellID']for x,y in zip(before['rows'],after['rows'])if any(x.get(k)!=y.get(k)for k in ['actual','measurement','normalization','status'])]
   statuses=[x['cellID']for x,y in zip(before['rows'],after['rows'])if x['status']!=y['status']]
   assert changes==[x['cellID']for x in data['allChangedMeasurementProvenanceOrStatusCells']]
   assert len(changes)==data['changedCellCount']and len(statuses)==data['statusChangedCellCount']
  inventory=folder/'screenshot-inventory.json'
  if inventory.exists():
   for item in read(inventory)['images']:assert sha(local(item['path']))==item['sha256']
  if stage=='selfreview':
   compare=load('verified_original_compare',R/'design/private/compare.py')
   for alias in ['source-a','source-b']:
    claims=read(folder/alias/'claims.json');d0=read(root/'D0'/alias/'grade.json');final=read(root/'FINAL'/alias/'grade.json')
    assert compare.compare(d0,final,claims)==read(folder/alias/'comparison.json')
    original=dict(claims,claims=[c for c in claims['claims']if c.get('reportSeries')!='review-semantic-diagnostics'])
    assert compare.compare(d0,final,original)==read(folder/alias/'comparison-original-reports-only.json')
    actual=set()
    for claim in claims['claims']:
     if claim.get('origin')!='typed':continue
     assert claim['typedCheckEstablished']is True
     for ref in claim['typedNativeReportRefs']:
      file,pointer=ref.split('#',1);report=read(local(file));row=modules['v3'][0].pointer(report,pointer)
      assert row['status']=='failed'and row==claim['original']['assertion']
      key=(str(local(file).relative_to(R)),pointer);assert key not in actual;actual.add(key)
    required=set();base=R/'evaluation-inputs/selfreview'/alias/'original'
    for series in ['review-original','review-semantic-diagnostics']:
     for path in (base/series).glob('*.json'):
      if not path.name.startswith(('ios-P','android-P')):continue
      data=read(path)
      for i,row in enumerate(data['assertions']):
       if row['status']=='failed':required.add((str(path.relative_to(R)),'/assertions/'+str(i)))
    assert actual==required,'Actual failed native rows missing/duplicated in format-neutral claim ledger'
  if stage=='paired-D0':
   for alias in ['source-a','source-b']:
    for name in ['grade.json','normalized.json']:
     assert(folder/alias/'v5'/name).read_bytes()==(root/'D0'/alias/name).read_bytes(),'Reused v5 evidence/judgments changed'
 print(json.dumps({'status':'PASS','sealedStages':stages,'replayedGrades':gradecount,'replayedNativeCaseNormalizations':casecount}))
if __name__=='__main__':main()
