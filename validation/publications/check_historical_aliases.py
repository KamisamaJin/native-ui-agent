#!/usr/bin/env python3
"""Fast admission for historical mutable-file aliases, before expensive replay.

Native evidence inventories, grading and publication checks still run in full.
This only checks the small aliased tool/document/adapter readsets.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
from historical_sources import archived_source

REPO = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(path.read_text())


def inputs():
    old=REPO/'validation/feedback-forward';new=REPO/'validation/default-forward'
    publication=REPO/'validation/publications/feedback-v9'
    meta=read(publication/'original-publication.json')
    for rel,item in read(old/'ARTIFACTS.json')['files'].items():
        source=REPO/meta['mutableAliases'].get(rel,rel)
        if rel.startswith('native-ui-agent/'):
            source=new/'baseline-v9'/rel.removeprefix('native-ui-agent/')
        yield 'v9',rel,source,item['sha256']
    for rel,item in read(publication/'MANIFEST.json')['files'].items():
        source=new/'historical-root'/rel if(new/'historical-root'/rel).is_file()else REPO/rel
        yield 'v9-completion',rel,source,item['sha256']
    for version,old,new in [('v10','default-forward','routed-forward'),('v11','routed-forward','managed-forward')]:
        inventory=read(REPO/'validation'/old/'ARTIFACTS.json')['files']
        entries=[(rel,item['sha256'])for rel,item in inventory.items()]
        entries += [(rel,value)for rel,value in read(REPO/'validation'/old/'RELEASE.json')['repository_files'].items()if rel not in inventory]
        for rel,expected in entries:
            source=REPO/rel;root=REPO/'validation'/new
            if rel.startswith('native-ui-agent/'):
                source=root/('baseline-'+version)/rel.removeprefix('native-ui-agent/')
            elif(root/'historical-root'/rel).is_file():
                source=root/'historical-root'/rel
            yield version,rel,source,expected


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();rows=[];counts={}
    for version,rel,source,expected in inputs():
        parts=Path(rel).parts
        if not(source!=REPO/rel or len(parts)==1 or parts[0]=='.github' or parts[:2]==('validation','publications')):
            continue
        def digest(path):
            raw=os.readlink(path).encode()if path.is_symlink()else path.read_bytes()
            return hashlib.sha256(raw).hexdigest()
        actual=digest(source)if source.is_file()or source.is_symlink()else None
        if actual!=expected and source==REPO/rel:
            source=archived_source(REPO,rel,expected);actual=digest(source)
        assert actual==expected,(version,rel,'Historical source alias digest differs')
        rows.append({'version':version,'logical_path':rel,'source':str(source.relative_to(REPO)),'sha256':actual})
        counts[version]=counts.get(version,0)+1
    assert all(counts.get(version,0)>0 for version in ['v9','v9-completion','v10','v11'])
    record={'at_unix':time.time(),'status':'PASS','counts':counts,'rows':rows,
            'scope':'Aliased tools/documents/adapters only. No native SDK, full evidence inventory, grading, or new business acceptance credit.'}
    if args.output:
        assert not args.output.exists(),'Fresh preflight output required'
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'status':'PASS','alias_counts':counts,'scope':record['scope']}))


if __name__=='__main__':
    main()
