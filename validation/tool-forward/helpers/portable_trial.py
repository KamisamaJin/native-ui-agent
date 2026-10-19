#!/usr/bin/env python3
"""Retain raw PNG/JSON/native logs; inventory omitted build caches/system videos."""
import argparse,hashlib,json,shutil
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('destination',type=Path);a=p.parse_args();src=a.source;dst=a.destination;dst.mkdir(parents=True,exist_ok=False);omitted=[]
 for f in sorted(src.rglob('*')):
  if not f.is_file():continue
  rel=f.relative_to(src)
  if 'DerivedData'in rel.parts or any(x.endswith('.xcresult')for x in rel.parts):continue
  if f.suffix.lower()in {'.mp4','.mov'}:
   omitted.append({'path':str(rel),'sha256':sha(f),'bytes':f.stat().st_size,'reason':'Automatic XCTest system diagnostic video excluded from portable repository; failure logs, full raw observation and all assertion screenshots retained. Original remains in local ignored cache.'});continue
  parts=list(rel.parts)
  if parts[0]=='project':parts[0]='compiled-project'
  out=dst.joinpath(*parts);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,out)
 (dst/'portable-scope.json').write_text(json.dumps({'source':str(src),'omitted_system_videos':omitted,'retained':'All collected PNG snapshots, raw JSON, native summaries, exact inputs/compiled host source and command logs. DerivedData/xcresult caches omitted.'},indent=2)+'\n')
 hashes={str(f.relative_to(dst)):sha(f)for f in sorted(dst.rglob('*'))if f.is_file()};(dst/'portable-sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
 print(json.dumps({'destination':str(dst),'files':len(hashes),'omitted_videos':len(omitted)}))
if __name__=='__main__':main()
