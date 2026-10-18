#!/usr/bin/env python3
"""Copy portable native evidence; preserve original JSON and images byte for byte."""
import argparse,hashlib,json,shutil
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pack(source,output):
 output.mkdir(parents=True,exist_ok=False);files=set()
 for name in ['observation.json','capture.json','manifest.json','native-summary.json','junit.xml','actual.png','actions.json','fixtures.json','test.log','operator.log']:
  if(source/name).is_file():files.add(source/name)
 if(source/'observation.json').exists():
  obs=json.loads((source/'observation.json').read_text())
  for s in obs['snapshots']:
   if s.get('screenshot'):files.add(source/s['screenshot'])
 if(source/'manifest.json').exists():
  manifest=json.loads((source/'manifest.json').read_text())
  files.update(source/path for path in manifest.get('image_hashes',{}))
 for f in sorted(files):
  if not f.resolve().is_relative_to(source.resolve()):raise ValueError('Escaped evidence path')
  target=output/f.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
 index={str(p.relative_to(output)):sha(p)for p in output.rglob('*')if p.is_file()}
 (output/'archived-files.json').write_text(json.dumps({'source':str(source),'files':index,'scope':'Byte-for-byte portable archive; build cache/xcresult remain local. No visual/business grade implied.'},indent=2)+'\n')
 return {'files':len(index),'bytes':sum(p.stat().st_size for p in output.rglob('*')if p.is_file())}

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(pack(a.source.resolve(),a.output.resolve())))
if __name__=='__main__':main()
