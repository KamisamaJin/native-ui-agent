#!/usr/bin/env python3
"""Seal one compile-only natural initial and copy identical independent arms."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import time

R = Path(__file__).resolve().parent
EXCLUDED = {'.git', 'build', '.gradle', '.kotlin', '.build', '.swiftpm', '__pycache__'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source(workspace):
    roots = [workspace / 'alerttoast/Sources', workspace / 'reply/Reply/app/src/main']
    files = {}
    for i, root in enumerate(roots):
        for p in sorted(root.rglob('*')):
            if p.is_symlink():
                raise ValueError('Source symlinks are not admitted')
            if p.is_file():
                files[str(i) + '/' + p.relative_to(root).as_posix()] = {'sha256': sha(p), 'bytes': p.stat().st_size}
    return roots, files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True)
    parser.add_argument('--compile-result', required=True, type=Path)
    args = parser.parse_args()
    if not re.fullmatch('T[1-5]', args.task):
        raise ValueError('Exact declared task ID required')
    original = R / 'cache/business/initial' / args.task
    workspace = original / 'workspace'
    compiled = json.loads(args.compile_result.read_text())
    if compiled.get('passed') is not True or {v['platform'] for v in compiled['records']} != {'ios', 'android'}:
        raise ValueError('Both real compile-only platform receipts required')
    roots, files = source(workspace)
    if any(not r['source_unchanged'] or r['source_after'] != {p: v['sha256'] for p, v in files.items()}
           for r in compiled['records']):
        raise ValueError('Source differs from compiler-admitted bytes')
    capsule = original / 'source-seal'
    capsule.mkdir(exist_ok=False)
    for relative in files:
        index, tail = relative.split('/', 1)
        target = capsule / 'files' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(roots[int(index)] / tail, target)
        target.chmod(0o444)
    jar = workspace / 'reply/Reply/.native-ui/java-desktop.jar'
    arms = {}
    def copy_file(src, dst):
        if Path(src) == jar:
            os.link(src, dst)
            return dst
        return shutil.copy2(src, dst)
    for arm in ['A', 'B']:
        destination = R / 'cache/business' / args.task / arm / 'workspace'
        shutil.copytree(workspace, destination, copy_function=copy_file,
                        ignore=lambda _, names: [n for n in names if n in EXCLUDED])
        _, copied = source(destination)
        if copied != files:
            raise ValueError('Paired source identity failed')
        arms[arm] = {'workspace': str(destination), 'source_files': copied,
                     'private_jdk_dependency_hardlinked': True}
    if source(workspace)[1] != files:
        raise ValueError('Initial source changed during pairing')
    for root in roots:
        for p in [*root.rglob('*'), root]:
            p.chmod(stat.S_IMODE(p.stat().st_mode) & ~0o222)
    receipt = {'at_unix': time.time(), 'task': args.task, 'source_files': files, 'arms': arms,
               'compile_result': {'path': str(args.compile_result.resolve()), 'sha256': sha(args.compile_result)},
               'scope': 'Natural compile-only initial source seal and byte-identical independent arm copies; no business UI/native test/render.'}
    with (capsule / 'SEAL.json').open('x') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'task': args.task, 'paired': True, 'source_files': len(files), 'seal_sha256': sha(capsule / 'SEAL.json')}))


if __name__ == '__main__':
    main()
