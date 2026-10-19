#!/usr/bin/env python3
"""Seal/recheck published files; works without Git or SDKs after relocation."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parent
REPO = R.parent.parent
MANIFEST = R / 'artifact-manifest.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        assert not MANIFEST.exists(), 'Retain the published artifact seal'
        assert json.loads((R / 'report-index.json').read_text())['blindness_complete']
        paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=REPO).decode().split('\0')
        prefixes = ('validation/tool-forward/', 'validation/tool-capabilities/')
        selected = sorted(p for p in paths if p and p.startswith(prefixes)
                          and p != MANIFEST.relative_to(REPO).as_posix())
        assert selected and all((REPO / p).is_file() for p in selected)
        rows = {p: {'sha256': sha(REPO / p), 'bytes': (REPO / p).stat().st_size} for p in selected}
        assert all(row['bytes'] <= 100 * 1024 * 1024 for row in rows.values()), 'Split oversized derived tables; retain original evidence'
        MANIFEST.write_text(json.dumps({'schema_version': 1, 'files': rows,
                                      'scope': 'Published immutable trial and capability archives, including frozen tool bundles, released design/grades, evidence and trial docs. Build/SDK caches and this manifest excluded. Live tool/root docs/CI can evolve independently; their publication is identified by the Git commit. Hashes establish byte integrity, not UI truth.'}, indent=2) + '\n')
    data = json.loads(MANIFEST.read_text())
    for relative, expected in data['files'].items():
        path = REPO / relative
        assert path.is_file() and path.stat().st_size == expected['bytes'] and sha(path) == expected['sha256'], relative
    print(json.dumps({'status': 'passed_published_artifact_integrity', 'files': len(data['files']),
                      'scope': 'No Git history, SDK replay or new business judgement required.'}))


if __name__ == '__main__':
    main()
