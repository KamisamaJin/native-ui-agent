#!/usr/bin/env python3
"""Run immutable publication checks against their original mutable aliases."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize(destination, publication):
    archive = REPO / 'validation/publications' / publication
    metadata = json.loads((archive / 'publication.json').read_text())
    manifest = REPO / metadata['originalManifest']
    assert sha(manifest) == metadata['originalManifestSHA256']
    original = json.loads(manifest.read_text())
    mutable = metadata['mutablePublicationFiles']
    for rel, expected in original['files'].items():
        source = archive / rel if rel in mutable else REPO / rel
        assert source.is_file() and sha(source) == expected['sha256'], rel
        if rel in mutable:
            assert mutable[rel] == expected['sha256']
        target = destination / rel
        assert target.resolve().is_relative_to(destination.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(source, target)
        except OSError:
            shutil.copyfile(source, target)
    # A historical checker may read an older immutable release that its own
    # publication manifest did not enumerate. Pin those read-only dependencies
    # separately rather than rewriting the original manifest or verifier.
    for rel, expected in metadata.get('supplementalDependencies', {}).items():
        source = REPO / rel
        assert source.is_file() and sha(source) == expected, rel
        target = destination / rel
        assert target.resolve().is_relative_to(destination.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert sha(target) == expected
        else:
            try:
                os.link(source, target)
            except OSError:
                shutil.copyfile(source, target)
    target = destination / metadata['originalManifest']
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(manifest, target)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('publication', choices=['dispatch-v4', 'state-v5', 'contract-v6'])
    parser.add_argument('check', choices=['verify_trial.py', 'verify_artifacts.py', 'artifacts.py', 'verify_tools.py', 'verify_generic.py'])
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='native-publication-audit-') as temporary:
        root = Path(temporary)
        metadata = materialize(root, args.publication)
        directory = Path(metadata['originalManifest']).parent
        subprocess.run([sys.executable, '-B', str(root / directory / args.check)],
                       cwd=root, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), check=True)
    print('PASS: historical publication aliases and original evidence remain byte-exact')


if __name__ == '__main__':
    main()
