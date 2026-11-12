#!/usr/bin/env python3
"""Pin the final independent review and preserve all development reproductions."""
import hashlib
import json
import os
from pathlib import Path
import stat
import time


ROOT = Path(__file__).resolve().parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(relative):
    return json.loads((ROOT / relative).read_bytes())


def write(relative, value):
    with (ROOT / relative).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def main():
    snapshots = read('snapshots/SOURCE-SNAPSHOT.json')
    for row in snapshots['files'].values():
        assert sha(Path(row['source'])) == row['sha256'], 'Frozen original changed'
        assert sha(Path(row['snapshot'])) == row['sha256'], 'Frozen source snapshot changed'
    results = {name: read('results/' + name + '/RESULT.json')
               for name in ('final-v1', 'final-v2', 'author-v1', 'author-v2')}
    assert (results['final-v1']['tests_run'], results['final-v1']['failures'], results['final-v1']['errors']) == (41, 22, 0)
    assert (results['final-v2']['tests_run'], results['final-v2']['passed']) == (41, 41)
    assert all((results[name]['tests_run'], results[name]['passed']) == (23, 23) for name in ('author-v1', 'author-v2'))
    control_sha = sha(ROOT / 'controls/review_controls.py')
    for name in ('final-v1', 'final-v2'):
        assert results[name]['control_sha256'] == control_sha
        target = ROOT / 'results' / name / 'CONTROL-SNAPSHOT.py'
        with target.open('xb') as stream:
            stream.write((ROOT / 'controls/review_controls.py').read_bytes())
    code_pins = {path.name: sha(path) for path in sorted((ROOT / 'revision-v2').glob('*.py'))}
    for name in ('final-v2', 'author-v2'):
        assert results[name]['module_sha256'] == code_pins
    defect_patterns = {
        'A': ('test_projection_02_', 'test_projection_03_', 'test_projection_04_'),
        'B': ('test_projection_05_', 'test_projection_06_'),
        'C': ('test_projection_08_', 'test_projection_09_', 'test_packet_02_'),
        'D': ('test_projection_12_', 'test_projection_13_', 'test_projection_14_'),
        'E': ('test_packet_03_', 'test_packet_04_', 'test_packet_05_'),
        'F': ('test_packet_06_', 'test_packet_07_'),
        'G': ('test_gate_07_', 'test_gate_08_', 'test_gate_09_', 'test_gate_10_', 'test_gate_13_'),
        'H': ('test_packet_11_',)}
    failures = []
    for row in results['final-v1']['controls']:
        if row['status'] == 'pass':
            continue
        test = row['test'].rsplit('.', 1)[-1]
        classes = [key for key, prefixes in defect_patterns.items() if test.startswith(prefixes)]
        assert len(classes) == 1, test
        failures.append({'test': test, 'defect_class': classes[0],
                         'reproduction_directory': str(ROOT / 'results/final-v1/cases' / test),
                         'v1_status': row['status'], 'v2_status': 'pass'})
    critical = ['REVIEW.md', 'snapshots/SOURCE-SNAPSHOT.json',
                'snapshots/frozen-v1/ALARM-PRESENTATION-FREEZE.json',
                'controls/review_controls.py', 'controls/author_regressions.py', 'controls/freeze_review.py']
    critical += ['revision-v2/' + name for name in code_pins]
    critical += ['results/' + name + '/RESULT.json' for name in results]
    critical += ['results/RUN-' + name + '.log' for name in results]
    report = {
        'version': 1, 'kind': 'independent-prospective-alarm-presentation-tool-review',
        'review_root': str(ROOT), 'candidate_implementation_revision': 2,
        'source_freeze_sha256': snapshots['frozen_presentation_sha256'],
        'frozen_sources_unchanged_at_close': True,
        'scope': 'Only tool behavior and synthetic inputs; no product, requirement, expected-value, denominator or outcome changes.',
        'reviewer_declaration': {
            'actual_business_alarm_worker_claim_grade_image_judgment_or_mapping_read': False,
            'sibling_finding_read': False, 'SDK_device_Git_network_or_delegation_used': False,
            'actual_alarm_preparation_or_phase2_dispatch': False,
            'candidate_applied_to_business_sources': False},
        'final_results': {name: {key: value[key] for key in ('tests_run', 'passed', 'failures', 'errors')}
                          for name, value in results.items()},
        'critical_files_sha256': {name: sha(ROOT / name) for name in critical},
        'candidate_code_sha256': code_pins,
        'failing_v1_controls': failures,
        'limits': [
            'Compound omission and fact-ancestor guards are bounded schemas, not arbitrary business-semantics classifiers.',
            'strict_json fractional/exponent tokens are Decimal; use json_text/encoded to serialize the exact numbers.',
            'Original raw bytes remain recoverable through exact ledger refs in the retained externally pinned source namespace.',
            'Recorded namespaces must remain under exclusive/read-only control; this is not an OS lock or actor-authentication system.',
            'Raw/decoded/JSON identity scanning does not evaluate arbitrary code or image pixels.',
            'Uniform all15 selections/descriptions, all-specs-before-dispatch and actual cause-barrier verification remain coordinator responsibilities.'],
        'development_runs_excluded_from_final_denominators': ['results/v1', 'results/v1-final', 'results/v2'],
        'development_control_quality_note': 'The earliest v1 run includes an artificial disabled-read_json experiment; preserved but removed from final controls and findings.'}
    write('REVIEW.json', report)
    files = {}; directories = []

    def walk(folder):
        with os.scandir(folder) as entries:
            for entry in sorted(entries, key=lambda item: item.name):
                path = Path(entry.path); relative = path.relative_to(ROOT).as_posix()
                mode = entry.stat(follow_symlinks=False).st_mode
                if stat.S_ISDIR(mode):
                    directories.append(relative); walk(path)
                elif stat.S_ISLNK(mode):
                    target = os.readlink(path)
                    assert path.resolve(strict=False).is_relative_to(ROOT), 'Review symlink escaped exclusive root'
                    files[relative] = {'kind': 'symlink', 'target': target}
                elif stat.S_ISREG(mode):
                    path.chmod(0o444)
                    files[relative] = {'kind': 'regular', 'sha256': sha(path), 'bytes': path.stat().st_size, 'mode': '0444'}
                else:
                    raise ValueError('Unexpected special entry in review tree')
    walk(ROOT)
    freeze = {'version': 1, 'kind': 'independent-synthetic-alarm-tool-review-freeze',
              'at_unix': time.time(), 'review_root': str(ROOT),
              'scope': report['scope'], 'reviewer_declaration': report['reviewer_declaration'],
              'final_counts': report['final_results'], 'all_frozen_sources_unchanged': True,
              'files_excluding_this_freeze': files, 'directories': directories,
              'file_or_symlink_count': len(files), 'directory_count': len(directories),
              'review_json_sha256': sha(ROOT / 'REVIEW.json')}
    write('REVIEW-FREEZE.json', freeze)
    (ROOT / 'REVIEW-FREEZE.json').chmod(0o444)
    print(json.dumps({'review_sha256': sha(ROOT / 'REVIEW.json'),
                      'freeze_sha256': sha(ROOT / 'REVIEW-FREEZE.json'),
                      'candidate_code_sha256': code_pins, 'control_sha256': control_sha,
                      'file_or_symlink_count': len(files), 'directory_count': len(directories)}))


if __name__ == '__main__':
    main()
