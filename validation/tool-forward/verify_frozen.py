#!/usr/bin/env python3
"""Verify preregistered bytes and portable seals; does not evaluate business UI."""
import argparse
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_files(root, files):
    for relative, digest in files.items():
        path = root / relative
        assert path.is_file() and sha(path) == digest, str(path)
    return len(files)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--include-private', action='store_true')
    args = parser.parse_args()
    checked = 0
    for variant, manifest in [('tool-v2', 'baseline-tool-freeze.json'),
                              ('tool-v3', 'candidate-tool-freeze.json')]:
        checked += checked_files(R / variant, read(R / manifest)['files'])
    transport = read(R / 'transport-amendment/freeze.json')
    assert sha(R / 'transport-amendment/apply.py') == transport['patch_sha256']
    assert sha(R / 'transport-amendment/native-probe/manifest.json') == transport['native_probe']['manifest_sha256']
    for variant, files in transport['variants'].items():
        checked += checked_files(R / variant, files)
        original = read(R / ('baseline-tool-freeze.json' if variant.endswith('v2')
                             else 'candidate-tool-freeze.json'))['files']
        changed = {name for name in original if original[name] != files[name]}
        assert changed == {'scripts/ios_observe.py', 'assets/ios-observer/ObserverTests.swift'}
        assert set(files) == set(original)
    for manifest in ['operator-freeze.json', 'phase-prompt-freeze.json', 'matching-prompt-freeze.json']:
        checked += checked_files(R, read(R / manifest)['files'])
    checked += checked_files(R / 'harness', read(R / 'harness-freeze.json')['files'])
    assert sha(R / 'METHODS.md') == read(R / 'methods-commitment.json')['sha256']
    amendment = read(R / 'operator-amendment-1.json')
    assert sha(R / amendment['selected_operator']) == amendment['selected_sha256']
    design = read(R / 'selected-design-commitment.json')
    files = {name: digest for name, digest in design['files'].items()
             if args.include_private or not name.startswith('private/')}
    checked += checked_files(R / design['selected'], files)
    assert sha(R / 'candidate-tool-freeze.json') == design['tool_freeze_sha256']
    portable = 0
    for folder in ['engineering', 'evidence', 'paired-evidence', 'transport-amendment/native-probe']:
        for manifest in sorted((R / folder).rglob('portable-sha256.json')):
            checked += checked_files(manifest.parent, read(manifest))
            portable += 1
    sources = 0
    for manifest in sorted((R / 'implementations').glob('*/*/manifest.json')):
        data = read(manifest)
        checked += checked_files(manifest.parent, data['files'])
        checked += checked_files(manifest.parent / 'reports', data.get('reports', {}))
        sources += 1
    phases = 0
    for manifest in sorted((R / 'phase-reports').glob('*/*/manifest.json')):
        checked += checked_files(manifest.parent, read(manifest)['files'])
        phases += 1
    print(json.dumps({'status': 'passed_frozen_byte_integrity', 'checked_files': checked,
                      'portable_capture_seals': portable, 'source_capsules': sources,
                      'phase_report_seals': phases,
                      'private_design_included': args.include_private,
                      'scope': 'Byte integrity only; not UI acceptance or native SDK replay.'}))


if __name__ == '__main__':
    main()
