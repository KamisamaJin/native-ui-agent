#!/usr/bin/env python3
"""Prepare equal review inputs only after both independent initial grade seals."""
import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

R = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--source-capsule', type=Path, required=True)
    p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--runtime-capability', type=Path, required=True)
    p.add_argument('--both-grade-seal', type=Path, required=True)
    a = p.parse_args()
    workspace = a.workspace.resolve()
    assert a.both_grade_seal.is_file(), 'Both independent D0 grades must already be sealed'
    source_manifest = json.loads((a.source_capsule / 'manifest.json').read_text())
    for relative, digest in source_manifest['files'].items():
        assert sha(workspace / relative) == digest, relative
    for platform in ['android', 'ios']:
        for n in range(1, 7):
            case = a.evidence / platform / ('C%02d' % n)
            assert (case / 'capture.json').is_file() and (case / 'portable-sha256.json').is_file()
            for relative, digest in json.loads((case / 'portable-sha256.json').read_text()).items():
                assert sha(case / relative) == digest
    # Fresh destinations prevent silent replacement of an earlier review corpus.
    shutil.copytree(a.evidence, workspace / 'initial-evidence')
    shutil.copytree(R / 'private/inputs/d0', workspace / 'initial-inputs')
    changes = {}
    for relative in ['scripts/ios_observe.py', 'assets/ios-observer/ObserverTests.swift']:
        target = workspace / 'capability' / relative
        source = a.runtime_capability / relative
        changes[relative] = {'before': sha(target), 'after': sha(source)}
        shutil.copy2(source, target)
    assert sha(workspace / 'capability/SKILL.md') == sha(a.runtime_capability / 'SKILL.md')
    provenance = {'prepared_at': time.time(), 'workspace': str(workspace),
                  'source_manifest_sha256': sha(a.source_capsule / 'manifest.json'),
                  'independent_d0_seal_sha256': sha(a.both_grade_seal),
                  'assigned_evidence_origin': str(a.evidence.resolve()),
                  'uniform_transport_only_changes': changes,
                  'input_manifest_sha256': sha(R / 'private/inputs/d0/manifest.json'),
                  'scope': 'No oracle, independent outcomes or other submission supplied.'}
    output = workspace / 'review-input-provenance.json'
    output.write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps({'prepared': str(output), 'production_fingerprints_unchanged': True}))


if __name__ == '__main__':
    main()
