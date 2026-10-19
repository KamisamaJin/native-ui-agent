#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root');a=p.parse_args();root=Path(a.root)
files={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(root.rglob('*')) if f.is_file() and f.name!='portable-sha256.json'}
(root/'portable-sha256.json').write_text(json.dumps(files,indent=2)+'\n')
