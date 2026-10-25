#!/usr/bin/env python3
"""Verify sealed identity and regenerate every native expectation without SDKs."""
import hashlib, json
from pathlib import Path
import build_inputs as b

def verify_seal(path):
    seal=b.d.load(path/'SEAL.json')
    assert b.d.digest(seal['files'])==seal['manifest_sha256']
    actual={str(p.relative_to(path)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(path.rglob('*')) if p.is_file() and p.name!='SEAL.json' and '__pycache__' not in p.parts}
    if path==b.ROOT:
        for child in ['public','private']:actual[child+'/SEAL.json']=b.sha(path/child/'SEAL.json')
    assert actual==seal['files'], 'Sealed file bytes or directory membership changed'
    return {'scope':seal['scope'],'sealedAtUTC':seal['sealedAtUTC'],'files':len(actual)}

if __name__=='__main__':
    results=[b.verify_scope(b.ROOT/n) for n in ['public','private']]
    seals=[verify_seal(b.ROOT/n) for n in ['public','private']]+[verify_seal(b.ROOT)]
    print(json.dumps({'status':'passed','semantic_checks':results,'seals':seals,'sdk_invoked':False},ensure_ascii=False))
