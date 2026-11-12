#!/usr/bin/env python3
"""Copy a pinned stock host, without SDK execution or business implementation.

The only hard link is a private, unchanged, locally reconstructed JDK dependency.
Production sources are always independent copies. Existing destinations reject.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

R = Path(__file__).resolve().parent
EXCLUDED = {'.git', 'build', '.gradle', '.kotlin', '.build', '.swiftpm', '__pycache__'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clone(source, destination):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    began = time.time()
    if destination.exists():
        raise ValueError('A fresh workspace is required')
    private_jar = source / 'reply/Reply/.native-ui/java-desktop.jar'
    def copy_file(original, target):
        if Path(original) == private_jar:
            os.link(original, target)
            return target
        return shutil.copy2(original, target)
    shutil.copytree(source, destination, copy_function=copy_file,
                    ignore=lambda _, names: [name for name in names if name in EXCLUDED])
    roots = [destination / 'alerttoast/Sources', destination / 'reply/Reply/app/src/main']
    files = {str(i) + '/' + p.relative_to(root).as_posix(): sha(p)
             for i, root in enumerate(roots) for p in sorted(root.rglob('*')) if p.is_file()}
    receipt = {'version': 1, 'stock_setup_sha256': sha(source / 'setup.json'),
               'source': str(source), 'workspace': str(destination),
               'production_source_roots': list(map(str, roots)), 'stock_production_files': files,
               'private_jdk_dependency': {'path': str(destination / private_jar.relative_to(source)),
                                        'sha256': sha(private_jar), 'hard_linked': True,
                                        'publish_binary': False},
               'started_at_unix': began, 'finished_at_unix': time.time(),
               'scope': 'Stock source/test-host preparation only. No business code, native render or SDK execution.'}
    with (destination / 'STOCK-COPY.json').open('x') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, default=R / 'cache/hosts')
    parser.add_argument('--destination', required=True, type=Path)
    args = parser.parse_args()
    result = clone(args.stock, args.destination)
    print(json.dumps({'workspace': result['workspace'], 'stock_files': len(result['stock_production_files']),
                      'wall_seconds': result['finished_at_unix'] - result['started_at_unix']}))


if __name__ == '__main__':
    main()
