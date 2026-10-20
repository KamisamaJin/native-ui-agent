#!/usr/bin/env python3
"""Copy an immutable production capsule into a fresh owned audit host, without edits."""
import argparse,hashlib,json,shutil
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('capsule',type=Path);p.add_argument('workspace',type=Path);a=p.parse_args();c=a.capsule.resolve();w=a.workspace.resolve();seal=json.loads((c/'seal.json').read_text())
 assert(w/'bootstrap.json').is_file(),'Requires dedicated bootstrapped audit host'
 allowed=['alerttoast/Sources','reply/Reply/app/src/main/java/com/example/reply/ui/waterround']
 for rel,h in seal['files'].items():
  f=c/'source'/rel;assert f.resolve().is_relative_to((c/'source').resolve());assert any(rel.startswith(x+'/')for x in allowed);assert hashlib.sha256(f.read_bytes()).hexdigest()==h
 for rel in allowed:
  d=w/rel
  if d.exists():shutil.rmtree(d)
 for rel,h in seal['files'].items():
  d=w/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(c/'source'/rel,d);assert hashlib.sha256(d.read_bytes()).hexdigest()==h
 print(json.dumps({'installed':str(c),'workspace':str(w),'exactFiles':len(seal['files'])}))
if __name__=='__main__':main()
