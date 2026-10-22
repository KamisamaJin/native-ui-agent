#!/usr/bin/env python3
"""Verify original scope byte-exact, plus omitted original gate dependencies."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import publication_closure as closure

P = Path(__file__).resolve().parent
REPO = P.parents[2]
R = REPO / 'validation/atomic-forward'


def read(path):
    return json.loads(Path(path).read_text())


def plan():
    required = {}
    for path in sorted((R / 'gates').glob('*.json')):
        for files in read(path).get('members', {}).values():
            for relative, expected in files.items():
                key = str((R / relative).relative_to(REPO))
                if key in required:
                    assert required[key] == expected
                required[key] = expected
    tracked = set(filter(None, subprocess.check_output(['git', '-C', str(REPO), 'ls-files', '-z']).decode().split('\0')))
    wanted_fold = {v.casefold() for v in required}
    published = {v: closure.sha(REPO / v) for v in tracked if v.casefold() in wanted_fold}
    return closure.audit(required, published)


def inventory():
    paths = [p for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name != 'COMPLETION.json']
    paths += [REPO / rel for rel in ['README.md', '.github/workflows/test.yml']]
    paths += [REPO / v['path'] for v in read(P / 'required-raw-files.json')]
    return {str(p.relative_to(REPO)): {'sha256': closure.sha(p), 'bytes': p.stat().st_size} for p in sorted(set(paths))}


def original_scope():
    meta = read(P / 'original-publication.json')
    original = REPO / meta['originalManifest']
    assert closure.sha(original) == meta['originalManifestSHA256']
    with tempfile.TemporaryDirectory(prefix='atomic-v8-original-publication-') as folder:
        root = Path(folder)
        for relative, expected in read(original)['files'].items():
            alias = meta['mutableAliases'].get(relative)
            source = REPO / (alias['archive'] if alias else relative)
            assert closure.sha(source) == expected['sha256'] and source.stat().st_size == expected['bytes'], relative
            if alias:
                assert alias['sha256'] == expected['sha256']
            target = root / closure.safe(relative); target.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(source, target)
            except OSError:
                shutil.copyfile(source, target)
        target = root / meta['originalManifest']; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
        subprocess.run([sys.executable, '-B', str(root / 'validation/atomic-forward/artifacts.py')], cwd=root, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    target = P / 'COMPLETION.json'
    value = {'files': inventory(), 'closure': plan(), 'scope': 'Publication-only original-byte completion. No changed tools, product sources, seals, expectations, verdicts or metrics; original failed CI and original manifest retained.'}
    if args.freeze:
        assert not target.exists()
        target.write_text(json.dumps(value, indent=2) + '\n')
        print('Frozen explicit publication completion inventory')
        return
    assert read(target) == value, 'Completion inventory or sealed-reference publication closure changed'
    closure.prepare(REPO, value['closure']['caseAliases'])
    print(json.dumps({'sealedReferences': value['closure']['requiredCount'], 'direct': value['closure']['directCount'], 'caseAliases': value['closure']['caseAliases']}))
    if not args.prepare:
        original_scope()
    print('PASS exact original publication plus original sealed dependency completion')


if __name__ == '__main__':
    main()
