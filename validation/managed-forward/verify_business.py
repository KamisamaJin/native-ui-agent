#!/usr/bin/env python3
"""Closed paired-study verification; no SDK, live namespace, or cleanup action."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import business
import build_business_metrics

R = Path(__file__).resolve().parent
REPO = R.parents[1]


def check_seal(path):
    value = business.read(path)
    for relative, entry in value['files'].items():
        p = path.parent / relative
        expected = entry if isinstance(entry, str) else entry['sha256']
        assert business.sha(p) == expected, str(p)
        if isinstance(entry, dict) and 'bytes' in entry:
            assert p.stat().st_size == entry['bytes']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tracked', action='store_true')
    parser.add_argument('--replay', action='store_true', help='Recompute all original automatic/independent hidden image facts')
    args = parser.parse_args()
    for name in ['tools', 'design', 'initial', 'self-finals', 'quality', 'reveal']:
        business.authorize(name)
    for relative, expected in business.read(R / 'RELEASE.json')['files'].items():
        assert business.sha(R / relative) == expected
    for root in [R / 'business-design/public', R / 'business-design/private',
                 R / 'business-quality/reviewer-1', R / 'business-quality/reviewer-2', R / 'business-quality/cause-matching',
                 R / 'business-quality/packet-public', R / 'business-quality/packet-hidden-finals', R / 'business-quality/packet-initial-hidden']:
        check_seal(root / ('SEAL.json' if root.name.startswith('packet-') else 'seal.json'))
    approval_root = R / 'business-design-review'
    approval = business.read(approval_root / 'seal.json')
    assert approval['decision'] == 'approved'
    assert business.sha(approval_root / 'approval.json') == approval['approval_file_sha256']
    for relative, expected in approval['review_files_sha256'].items():
        assert business.sha(approval_root / relative) == expected
    for relative, expected in approval['original_design_files_sha256'].items():
        assert business.sha(R / 'business-design' / relative) == expected
    # A case-insensitive Mac glob also returns lowercase source-capsule seal.json
    # for SEAL.json. Preserve the distinct original schemas on Linux and macOS.
    for path in (R / 'business-evidence').rglob('*'):
        if not path.is_file():
            continue
        if path.name in ['ARCHIVE-SEAL.json', 'SEAL.json']:
            check_seal(path)
        elif path.name == 'seal.json' and (path.parent / 'source').is_dir():
            for relative, expected in business.read(path)['files'].items():
                assert business.sha(path.parent / 'source' / relative) == expected
    initial = business.read(R / 'business-evidence/initial/seal.json')['files']
    assert initial == business.read(R / 'business-evidence/A/initial/seal.json')['files'] == business.read(R / 'business-evidence/B/initial/seal.json')['files']
    for arm in ['A', 'B']:
        source = R / 'business-evidence' / arm / 'final-source'
        for rel, expected in business.read(source / 'seal.json')['files'].items():
            assert business.sha(source / 'source' / rel) == expected
        lock = business.read(R / 'business-administration' / ('source-lock-' + arm + '.json'))
        assert not lock['late_source_files'] and lock['source_stable_during_seal']
        for n in [1, 2]:
            request = business.read(R / 'business-administration' / ('diagnostic-' + str(n) + '-request-' + arm + '.json'))
            assert request['request_index'] == n and request['before_deadline'] and request['at_unix'] <= lock['deadline_unix']
        for phase in ['D0', 'D1', 'D2', 'Final', 'Hidden']:
            base = R / 'business-evidence' / arm / ('private/Hidden' if phase == 'Hidden' else 'public/' + phase)
            for pl in ['ios', 'android']:
                command = business.read(base / pl / 'command.json')
                assert command['host_unchanged'] and command['source_unchanged']
                assert command['exit_code'] == (2 if phase == 'D1' else 0)
                safety = business.read(base / pl / 'common-safety/resources.json')
                assert not safety['cleanup_errors'] and not safety['remaining_devices'] and not safety['remaining_directories']
        for reviewer in ['1', '2']:
            for pl in ['ios', 'android']:
                bound = R / 'business-evidence/independent-evaluation/independent-bindings-v3' / ('reviewer-' + reviewer) / arm / pl
                assert business.read(bound / 'evaluation.json')['status'] == 'accepted'
                assert business.read(bound / 'completion/evaluated.json')['counts'] == {'passed': 303, 'failed': 0, 'unassessed': 0}
                assert not business.read(bound / 'common-responsibility.json')['blocking_claims']
    retired = business.read(R / 'operators/owned-device-final-check.json')
    assert retired['exit_code'] == 0 and retired['owned_count'] == 12
    assert not retired['remaining_target_rows'] and not any(retired['device_directory_exists'].values())
    hidden = business.read(R / 'business-administration/hidden-acquisition-dispatch.json')
    self_seal = business.read(R / 'gates/self-finals.json')
    assert hidden['started_at_unix'] >= self_seal['sealedAtUnix']
    cleanup = business.read(R / 'CLEANUP-2.json')
    assert cleanup['status'] == 'complete' and not cleanup['post_cleanup']['path_exists']
    assert business.read(R / 'METRICS.json') == build_business_metrics.compute()
    if args.replay:
        for reviewer in ['1', '2']:
            for candidate in ['A', 'B', 'initial']:
                for pl in ['ios', 'android']:
                    subprocess.run([sys.executable, '-B', str(R / 'replay_business_case.py'), '--candidate', candidate,
                                    '--platform', pl, '--scope', 'private', '--reviewer', reviewer], check=True)
        for candidate in ['A', 'B', 'initial']:
            for pl in ['ios', 'android']:
                subprocess.run([sys.executable, '-B', str(R / 'replay_business_case.py'), '--candidate', candidate,
                                '--platform', pl, '--scope', 'public'], check=True)
    if args.tracked:
        tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=REPO).decode().split('\0'))
        missing = [str(p.relative_to(REPO)) for p in R.rglob('*')
                   if p.is_file() and 'cache' not in p.parts and '__pycache__' not in p.parts
                   and str(p.relative_to(REPO)) not in tracked]
        assert not missing, 'Untracked closed-study artifacts: ' + repr(missing[:20])
    print(json.dumps({'status': 'PASS', 'scope': 'Original complete paired-study artifact/barrier replay; no SDK rerun, fresh product test, population quality or cost claim.'}))


if __name__ == '__main__':
    main()
