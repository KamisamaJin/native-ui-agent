#!/usr/bin/env python3
"""Run unmodified v12 validators against their exact original indexed bytes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

P=Path(__file__).resolve().parent
REPO=P.parents[2]


def raw_hash(path,entry):
    h=hashlib.sha256();g=hashlib.sha1()
    g.update(b'blob '+str(entry['bytes']).encode()+b'\0');size=0
    if entry['mode']=='120000':
        assert path.is_symlink(),str(path)
        data=os.readlink(path).encode();h.update(data);g.update(data);size=len(data)
    else:
        assert not path.is_symlink()and path.is_file(),str(path)
        with path.open('rb')as f:
            for data in iter(lambda:f.read(1024*1024),b''):
                h.update(data);g.update(data);size+=len(data)
    assert size==entry['bytes']and h.hexdigest()==entry['sha256']and g.hexdigest()==entry['git_blob'],str(path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-sources-only',action='store_true')
    a=parser.parse_args();manifest=json.loads((P/'SOURCE-INVENTORY.json').read_text())
    assert manifest['source_commit']=='e75dd9227203dd06350a923cc249b79ff710687f'
    for logical,entry in manifest['files'].items():
        assert not Path(logical).is_absolute()and'..'not in Path(logical).parts
        source=(REPO/entry['source'])
        assert source.resolve().is_relative_to(REPO)
        raw_hash(source,entry)
    if a.verify_sources_only:
        print('PASS exact v12 historical input inventory, original Git objects and SHA256');return
    # Hard links avoid copying the 2 GB historical publication on one volume;
    # original validators are read-only and Python bytecode is disabled.
    with tempfile.TemporaryDirectory(prefix='native-v12-original-')as folder:
        root=Path(folder)
        for logical,entry in manifest['files'].items():
            source=REPO/entry['source'];target=root/logical
            target.parent.mkdir(parents=True,exist_ok=True)
            if entry['mode']=='120000':target.symlink_to(os.readlink(source))
            else:
                try:os.link(source,target)
                except OSError:shutil.copy2(source,target)
        env=dict(os.environ,GIT_DIR=str(REPO/'.git'),GIT_WORK_TREE=str(root),
                 GIT_INDEX_FILE=str(root/'.historical-index'),PYTHONDONTWRITEBYTECODE='1')
        subprocess.run(['git','read-tree','--empty'],cwd=root,env=env,check=True)
        entries=[v['mode']+' '+v['git_blob']+'\t'+rel+'\0'for rel,v in manifest['files'].items()]
        subprocess.run(['git','update-index','-z','--index-info'],input=''.join(entries).encode(),cwd=root,env=env,check=True)
        for command in manifest['commands']:
            print('Original v12 command: '+' '.join(command),flush=True)
            subprocess.run([sys.executable,'-B',*command],cwd=root,env=env,check=True)
        for logical,entry in manifest['files'].items():raw_hash(root/logical,entry)
    print('PASS immutable v12 source, all original failures, native evidence, barriers and frozen business replays')


if __name__=='__main__':main()
