#!/usr/bin/env python3
"""Published bytes, including all original failures; no native build caches."""
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
OMIT={'cache','__pycache__','.git','DerivedData','.build','checkouts'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enumerate_files():
 result={};candidates=list(R.rglob('*'))+list((REPO/'native-ui-agent').rglob('*'))+list((REPO/'validation/publications/contract-v6').rglob('*'))
 candidates += [REPO/p for p in ['README.md','LICENSE','THIRD_PARTY_NOTICES.md','.gitignore','.github/workflows/test.yml','validation/publication_history.py','tools/native_environment.py','tools/README.md','tools/__init__.py']]
 for path in sorted(set(candidates)):
  rel=path.relative_to(REPO)
  if not path.is_file()or path==R/'ARTIFACTS.json'or any(part in OMIT or part.endswith('.xcresult')for part in rel.parts)or path.name=='.DS_Store'or path.suffix in{'.pyc','.pyo'}:continue
  result[str(rel)]={'sha256':sha(path),'bytes':path.stat().st_size}
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();current=enumerate_files();target=R/'ARTIFACTS.json'
 if a.write:
  assert not target.exists(),'Published manifests are immutable'
  target.write_text(json.dumps({'createdAtUTC':datetime.now(timezone.utc).isoformat(),'files':current,'scope':'Prospective tools, rejected and accepted independent designs, six original/final sources and self-reviews, all portable native captures, anonymous grades, natural-defect classification, failures and actual costs. SDK caches omitted. Previous mutable v6 publication dependencies preserved byte-exact through contract-v6 alias.'},indent=2)+'\n')
 else:assert json.loads(target.read_text())['files']==current,'Published inventory changed or omitted files'
 print(json.dumps({'status':'PASS','files':len(current),'bytes':sum(v['bytes']for v in current.values())}))
if __name__=='__main__':main()
