#!/usr/bin/env python3
"""Enumerate bounded private artifacts for publication AFTER all blind seals.

Never stage private native build trees. Original captures are published through
portable evidence archives. Prints NUL-delimited paths for git add --pathspec-file.
"""
import argparse,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert (R/'private/assignment-release.json').is_file(),'Do not publish identities/holdouts before every blind phase seals'
 files=set()
 def add(path):
  assert path.is_file();assert path.stat().st_size<90_000_000
  assert 'DerivedData'not in path.parts and 'cache'not in path.parts and not any(x.endswith('.xcresult')for x in path.parts)
  files.add(str(path.relative_to(REPO)))
 def tree(path):
  for f in path.rglob('*'):
   if f.is_file()and '__pycache__'not in f.parts:add(f)
 for p in (R/'private').glob('*.json'):add(p)
 for name in ['inputs','audit-seals','grade-capsules']:
  if (R/'private'/name).exists():tree(R/'private'/name)
 for sub in (R/'private/submissions').iterdir():
  for f in sub.iterdir():
   if f.is_file()and f.suffix in {'.json','.log','.txt'}:add(f)
  for name in ['d0','final','review-assets']:tree(sub/name)
 d=R/'design';seal=d/'private/SEAL.json';add(seal)
 for f in json.loads(seal.read_text())['payload']['files']:add(d/f['path'])
 prep=d/'private/evaluator-prep'
 for folder,name in [('', 'PREP-SEAL.json'),('v2','V2-SEAL.json'),('v3','V3-SEAL.json'),('report-conventions','CONVENTIONS-SEAL.json')]:
  root=prep/folder;s=root/name;add(s)
  for f in json.loads(s.read_text())['payload']['files']:add(root/f['path'])
 tree(d/'private/evaluation')
 a.output.write_bytes(b''.join(x.encode()+b'\0'for x in sorted(files)))
 print(json.dumps({'private_publication_files':len(files),'bytes':sum((REPO/x).stat().st_size for x in files),'pathList':str(a.output)}))
if __name__=='__main__':main()
