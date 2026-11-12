#!/usr/bin/env python3
"""Freeze the bounded prospective material-helper review and retained history."""
import hashlib
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path(__file__).resolve().parent.parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def read(name): return json.loads((ROOT / name).read_bytes())


def write(name, value):
    with (ROOT / name).open('x') as stream: json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')


def main():
    sources = read('snapshots/SOURCES.json')
    for row in sources['files'].values():
        assert sha(Path(row['source'])) == sha(Path(row['snapshot'])) == row['sha256']
    results = {name: read('results/' + name + '/RESULT.json') for name in ('final-v1', 'final-v3', 'author-v1', 'author-v3')}
    assert (results['final-v1']['tests_run'], results['final-v1']['failures'], results['final-v1']['errors']) == (23, 10, 0)
    assert (results['final-v3']['tests_run'], results['final-v3']['passed']) == (23, 23)
    assert all((results[name]['tests_run'], results[name]['passed']) == (8, 8) for name in ('author-v1', 'author-v3'))
    control = ROOT / 'controls/test_material_behavior.py'
    candidate = 'revision-v3/alarm-material-tools-v3/material.py'
    assert results['final-v3']['module_sha256'] == results['author-v3']['module_sha256'] == sha(ROOT / candidate)
    for name in ('final-v1', 'final-v3'):
        assert results[name]['control_sha256'] == sha(control)
        with (ROOT / 'results' / name / 'CONTROL-SNAPSHOT.py').open('xb') as stream: stream.write(control.read_bytes())
    for revision in ('revision-v2', 'revision-v3'):
        for name, pin in results['final-v3']['presentation_pins'].items():
            assert sha(ROOT / revision / 'publication-alarm-review/revision-v2' / name) == pin
    patterns = {'A': ('test_05_', 'test_06_'), 'B': ('test_10_', 'test_11_', 'test_12_', 'test_13_'),
                'C': ('test_15_',), 'D': ('test_17_', 'test_18_'), 'E': ('test_21_',)}
    failed = []
    for row in results['final-v1']['controls']:
        if row['status'] == 'pass': continue
        test = row['test'].rsplit('.', 1)[-1]
        classes = [key for key, prefixes in patterns.items() if test.startswith(prefixes)]
        assert len(classes) == 1
        failed.append({'test': test, 'class': classes[0], 'case_directory': str(ROOT / 'results/final-v1/cases' / test),
                       'v1_status': row['status'], 'v3_status': 'pass'})
    critical = ['REVIEW.md', 'snapshots/SOURCES.json', 'controls/test_material_behavior.py',
                'controls/author_controls.py', 'controls/freeze_review.py', candidate, 'revision-v3/README.md',
                'revision-v3/DIFF-from-v1.txt', 'revision-v3/RETENTION-DIFF-from-v2.txt']
    critical += ['revision-v3/publication-alarm-review/revision-v2/' + name for name in results['final-v3']['presentation_pins']]
    critical += ['results/' + name + '/RESULT.json' for name in results]
    critical += ['results/RUN-' + name + '.log' for name in results]
    report = {'version': 1, 'kind': 'independent-prospective-material-helper-review',
              'review_root': str(ROOT), 'final_candidate_revision': 3, 'candidate_path': str(ROOT / candidate),
              'candidate_sha256': sha(ROOT / candidate),
              'source_author_freeze_sha256': '1e635aeef3259b4e00cb45fb093b9cf07ff442b3e6aad82ad9d48942448f6e08',
              'source_pins_unchanged': True, 'presentation_library_pins_unchanged': results['final-v3']['presentation_pins'],
              'critical_files_sha256': {name: sha(ROOT / name) for name in critical},
              'final_results': {name: {key: value[key] for key in ('tests_run', 'passed', 'failures', 'errors')} for name, value in results.items()},
              'failing_v1_controls': failed,
              'acquisition_evidence_policy': 'Retain the entire object as a deep-copied fact/provenance claim, including arbitrary scope, refs and nested members; explicit alias neutralization only.',
              'unknown_schema_limit': 'Unknown values that would be omitted stop preparation. Entire fact containers retain unfamiliar nested members. Scalar intent cannot be inferred outside the explicit metadata contract.',
              'import_isolation_limit': 'Fresh execution of already verified bytes isolates pre-import module-cache contamination; not a sandbox against deliberate mutation after import.',
              'gating_scope': 'No all30 gate, actual selection, reference resolution, packet write or dispatch is performed by the material helpers.',
              'declaration': {'synthetic_only': True, 'actual_alarm_grade_map_native_or_report_bodies_read': False,
                              'batch_driver_read_or_audited': False, 'data_application_SDK_Git_network_delegation_used': False,
                              'prior_review_trees_or_original_sources_modified': False},
              'development_excluded_from_final_denominators': ['results/v1', 'results/v2', 'results/author-v2', 'revision-v2']}
    write('REVIEW.json', report)
    files = {}; directories = []
    def walk(folder):
        with os.scandir(folder) as entries:
            for entry in sorted(entries, key=lambda row: row.name):
                path = Path(entry.path); name = path.relative_to(ROOT).as_posix(); mode = entry.stat(follow_symlinks=False).st_mode
                if stat.S_ISDIR(mode): directories.append(name); walk(path)
                elif stat.S_ISLNK(mode):
                    assert path.resolve(strict=False).is_relative_to(ROOT)
                    files[name] = {'kind': 'symlink', 'target': os.readlink(path)}
                elif stat.S_ISREG(mode):
                    path.chmod(0o444); files[name] = {'kind': 'regular', 'sha256': sha(path), 'bytes': path.stat().st_size, 'mode': '0444'}
                else: raise AssertionError(name)
    walk(ROOT)
    assert len(files) + 1 < 1000
    freeze = {'version': 1, 'kind': 'independent-prospective-material-helper-review-freeze', 'at_unix': time.time(),
              'review_root': str(ROOT), 'review_json_sha256': sha(ROOT / 'REVIEW.json'), 'candidate_revision': 3,
              'file_and_symlink_count_including_freeze': len(files) + 1, 'declaration': report['declaration'],
              'files_excluding_this_freeze': files, 'directories': directories}
    write('REVIEW-FREEZE.json', freeze); (ROOT / 'REVIEW-FREEZE.json').chmod(0o444)
    print(json.dumps({'review_sha256': sha(ROOT / 'REVIEW.json'), 'freeze_sha256': sha(ROOT / 'REVIEW-FREEZE.json'),
                      'candidate_code_sha256': sha(ROOT / candidate), 'control_sha256': sha(control),
                      'file_and_symlink_count_including_freeze': len(files) + 1,
                      'result_sha256': {name: sha(ROOT / 'results' / name / 'RESULT.json') for name in results}}))


if __name__ == '__main__': main()
