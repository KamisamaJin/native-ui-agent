#!/usr/bin/env python3
"""Inventory published trial bytes, including failures, excluding native build caches."""
import argparse,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parent;REPO=R.parents[1]
OMIT={'cache','__pycache__','.git','DerivedData','.build','checkouts'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enumerate_files():
 result={}
 candidates=list(R.rglob('*'))+list((REPO/'native-ui-agent').rglob('*'))+list((REPO/'validation/publications/state-v5').rglob('*'))
 candidates += [REPO/p for p in ['README.md','LICENSE','THIRD_PARTY_NOTICES.md','.gitignore','.github/workflows/test.yml','validation/publication_history.py']]
 for path in sorted(set(candidates)):
  rel=path.relative_to(REPO)
  if not path.is_file() or path==R/'ARTIFACTS.json' or any(part in OMIT or part.endswith('.xcresult')for part in rel.parts)or path.name=='.DS_Store'or path.suffix in {'.pyc','.pyo'}:continue
  result[str(rel)]={'sha256':sha(path),'bytes':path.stat().st_size}
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();current=enumerate_files();target=R/'ARTIFACTS.json'
 if a.write:
  assert not target.exists(),'A published manifest is immutable; preserve original before new revisions'
  data={'createdAtUTC':datetime.now(timezone.utc).isoformat(),'files':current,'scope':'Published original sources, independent design, tools, native evidence, claims, grades, failures and costs. SDK/build caches omitted; retained portable SHA manifests attest original images/JSON/logs. Historical v5 mutable publication aliases preserved byte-exact.'};target.write_text(json.dumps(data,indent=2)+'\n')
 else:
  data=json.loads(target.read_text());assert data['files']==current,'Published files changed or inventory omitted files'
 print(json.dumps({'status':'PASS','files':len(current),'bytes':sum(v['bytes']for v in current.values())}))
if __name__=='__main__':main()
