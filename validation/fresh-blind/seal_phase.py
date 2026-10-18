#!/usr/bin/env python3
"""Seal a builder's reports/portable scratch artifacts without changing its sources."""
import argparse,hashlib,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--submission',required=True);p.add_argument('--phase',choices=['readonly-review','repair'],required=True);a=p.parse_args()
 workspace=a.workspace.resolve();dest=R/'phase-reports'/a.submission/a.phase;dest.mkdir(parents=True,exist_ok=False)
 required=workspace/'reports'/('self-review.json'if a.phase=='readonly-review'else'repair.json');assert required.is_file()
 files={}
 for name in ['reports','scratch']:
  for source in sorted((workspace/name).rglob('*')):
   if not source.is_file()or source.suffix.lower()not in {'.json','.png','.xml','.log','.txt','.md'}:continue
   relative=source.relative_to(workspace)
   if any(part in {'DerivedData','.build','build','test.xcresult','project','Products','Index.noindex'}for part in relative.parts):continue
   target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);files[str(relative)]=sha(target)
 (dest/'manifest.json').write_text(json.dumps({'sealed_at':time.time(),'source_workspace':str(workspace),'files':files,'scope':'Portable reports and scratch evidence; native build caches are omitted. Raw absolute paths retain their origin and can be remapped relative to this archive.'},indent=2)+'\n')
 print(json.dumps({'submission':a.submission,'phase':a.phase,'files':len(files),'manifest':str(dest/'manifest.json')}))
if __name__=='__main__':main()
