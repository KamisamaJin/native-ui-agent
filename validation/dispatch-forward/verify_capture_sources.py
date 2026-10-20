#!/usr/bin/env python3
"""Cache-free provenance audit; no business expected values or UI judgments."""
import argparse,hashlib,json,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native_encoding_v2',R/'design/private/evaluator-prep/v2/native_encoding.py');encoding=importlib.util.module_from_spec(spec);spec.loader.exec_module(encoding)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def check(source_capsule,corpus,platform):
 seal=read(source_capsule/'seal.json');runs=[]
 for command in sorted(corpus.glob('*-command.json')):
  c=read(command);d=corpus/c['case'];manifest=d/'manifest.json'
  if not manifest.is_file():
   assert c['exitCode']!=0,'Successful wrapper without native manifest'
   runs.append({'case':c['case'],'exitCode':c['exitCode'],'manifest':False});continue
  m=read(manifest);native=m.get('source_hashes',{})
  for rel,h in seal['files'].items():
   assert sha(source_capsule/'source'/rel)==h
   prefix='alerttoast/' if platform=='ios' else 'reply/Reply/'
   if not rel.startswith(prefix):continue
   suffix='/'+rel[len(prefix):]
   found=[v for k,v in native.items() if k.endswith(suffix)]
   assert found==[h],(command,rel,'Captured production source differs from sealed source')
  bridge='Bridge.swift' if platform=='ios' else 'ObserverBridge.kt'
  assert [v for k,v in native.items() if k.endswith('/'+bridge)]==[sha(R/'bridges'/bridge)]
  for name,h in m.get('image_hashes',{}).items():assert sha(d/name)==h
  obs=d/'observation.json'
  if obs.exists():
   if 'observation_sha256' in m:assert sha(obs)==m['observation_sha256']
   else:
    portable=read(corpus/'portable-sha256.json');assert sha(obs)==portable[str(obs.relative_to(corpus))]
   fixtures=read(d/'fixtures.json');models=[fixtures['initial']]+fixtures.get('updates',[])
   for snap in read(obs).get('snapshots',[]):
    assert (d/snap['screenshot']).is_file(),'Original native screenshot missing'
    binding=snap.get('binding',{});index=binding.get('fixture_index',binding.get('input_index'));assert type(index)is int and 0<=index<len(models)
    expected,_=encoding.native_model_hash(models[index],platform);assert binding.get('input_sha256')==expected,'Native current-model input identity mismatch'
  runs.append({'case':c['case'],'exitCode':c['exitCode'],'nativeTests':m.get('native_test_count',0),'manifest':True,'observation':obs.exists()})
 return runs
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--platform',choices=['ios','android'],required=True);a=p.parse_args();print(json.dumps(check(a.source,a.corpus,a.platform)))
if __name__=='__main__':main()
