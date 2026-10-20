#!/usr/bin/env python3
"""Checksum the published trial and live entry points, excluding only caches/self."""
import argparse,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files():
 paths=list(R.rglob('*'))+list((REPO/'native-ui-agent').rglob('*'))
 paths += [REPO/p for p in ['README.md','LICENSE','THIRD_PARTY_NOTICES.md','.gitignore','.github/workflows/test.yml']]
 for p in sorted(set(paths)):
  if not p.is_file()or p==R/'ARTIFACTS.json':continue
  rel=p.relative_to(REPO)
  if any(x in {'cache','__pycache__','.git','DerivedData','.build','checkouts'}or x.endswith('.xcresult')for x in rel.parts)or p.name=='.DS_Store'or p.suffix in {'.pyc','.pyo'}:continue
  yield p
def build():return {str(p.relative_to(REPO)):{'sha256':sha(p),'bytes':p.stat().st_size}for p in files()}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();target=R/'ARTIFACTS.json';data=build()
 if a.write:target.write_text(json.dumps({'files':data,'scope':'All published state-forward files and live Skill/README/workflow/notices, excluding this manifest and ignored runtime caches/bytecode.'},indent=2)+'\n')
 else:
  expected=json.loads(target.read_text())['files'];assert data==expected,'Published artifact membership or bytes changed'
 print(json.dumps({'status':'PASS','files':len(data),'bytes':sum(x['bytes']for x in data.values())}))
if __name__=='__main__':main()
