#!/usr/bin/env python3
"""Copy native observer evidence without DerivedData or xcresult caches."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('destination');a=p.parse_args()
src=Path(a.source);dst=Path(a.destination)
if dst.exists(): raise SystemExit('Destination must be fresh')
dst.mkdir(parents=True)
for item in src.iterdir():
    if item.name == 'project':
        shutil.copytree(item,dst/'compiled-project'); continue
    if item.name == 'DerivedData' or item.suffix=='.xcresult': continue
    if item.is_dir(): shutil.copytree(item,dst/item.name)
    else: shutil.copy2(item,dst/item.name)
hashes={str(f.relative_to(dst)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(dst.rglob('*')) if f.is_file()}
(dst/'portable-sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
