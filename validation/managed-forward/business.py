#!/usr/bin/env python3
"""Study plumbing: immutable barriers and source capsules, never product oracles."""
import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parent
sys.path.insert(0, str(R / 'candidate-v12.6/scripts'))
import cohort_gate as gate

ROOTS = ['alerttoast/Sources', 'reply/Reply/app/src/main']


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def inventory(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts}


def fingerprint(workspace):
    workspace = Path(workspace).resolve()
    return {str(p.relative_to(workspace)): sha(p) for rel in ROOTS
            for p in sorted((workspace / rel).rglob('*')) if p.is_file()}


def capsule(workspace, output):
    workspace = Path(workspace).resolve()
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    files = fingerprint(workspace)
    for rel in files:
        target = output / 'source' / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(workspace / rel, target)
    for name in ['alerttoast', 'reply']:
        for filename in ['LICENSE', 'LICENSE.md', 'LICENSE.txt', 'NOTICE']:
            path = workspace / name / filename
            if path.is_file():
                target = output / 'licenses' / (name + '-' + filename)
                target.parent.mkdir(exist_ok=True)
                shutil.copy2(path, target)
    save(output / 'seal.json', {'sealed_at_unix': time.time(), 'files': files})
    assert fingerprint(workspace) == files
    return files


def stage(name, members):
    paths = {}
    for member, roots in members.items():
        paths[member] = []
        for item in roots:
            path = Path(item).resolve()
            paths[member].extend(str(p.relative_to(R)) for p in
                                 ([path] if path.is_file() else sorted(path.rglob('*')))
                                 if p.is_file() and '__pycache__' not in p.parts)
    return gate.seal(R / 'gates', name, paths, R)


def authorize(name, workspace=None, source_seal=None):
    result = gate.authorize(R / 'gates', name, R)
    if workspace is not None:
        if source_seal is None or fingerprint(workspace) != read(source_seal)['files']:
            raise ValueError('Actual workspace differs from its pre-acquisition source capsule')
        result['workspace_source_seal_sha256'] = sha(source_seal)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    c = sub.add_parser('capsule')
    c.add_argument('--workspace', type=Path, required=True)
    c.add_argument('--output', type=Path, required=True)
    a = sub.add_parser('authorize')
    a.add_argument('--stage', required=True)
    a.add_argument('--workspace', type=Path)
    a.add_argument('--source-seal', type=Path)
    s = sub.add_parser('seal-stage')
    s.add_argument('--stage', required=True)
    s.add_argument('--members', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'capsule':
        value = capsule(args.workspace, args.output)
    elif args.command == 'authorize':
        value = authorize(args.stage, args.workspace, args.source_seal)
    else:
        value = stage(args.stage, read(args.members))
    print(json.dumps(value, indent=2))
