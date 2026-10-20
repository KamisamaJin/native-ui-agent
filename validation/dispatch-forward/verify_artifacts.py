#!/usr/bin/env python3
"""Hash every published trial artifact; no SDK, simulator or previous cache needed."""
import argparse,hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();out=R/'artifact-manifest.json'
 if a.write:
  assert not out.exists()
  tracked=subprocess.check_output(['git','ls-files','-z'],cwd=REPO).decode().split('\0');files={}
  for rel in sorted(x for x in tracked if x and (x.startswith('validation/dispatch-forward/')or x.startswith('native-ui-agent/')or x in ['README.md','THIRD_PARTY_NOTICES.md','.gitignore','LICENSE','.github/workflows/test.yml'])):
   path=REPO/rel
   if path==out:continue
   assert '/cache/'not in rel and 'DerivedData'not in path.parts and '.xcresult'not in rel
   size=path.stat().st_size;assert size<90_000_000,('Unexpected oversized publication',rel)
   files[rel]={'sha256':sha(path),'bytes':size}
  out.write_text(json.dumps({'version':1,'scope':'All staged/tracked dispatch-forward trial files, current published Skill and listed root documentation/workflow. Build caches, simulator runtimes and credentials excluded. This manifest itself is excluded.','files':files},indent=2,ensure_ascii=False)+'\n')
 d=json.loads(out.read_text())
 for rel,m in d['files'].items():
  path=(REPO/rel).resolve();assert path.is_relative_to(REPO.resolve())
  assert path.stat().st_size==m['bytes']and sha(path)==m['sha256'],rel
 print(json.dumps({'status':'PASS','published_files':len(d['files']),'published_bytes':sum(x['bytes']for x in d['files'].values())}))
if __name__=='__main__':main()
