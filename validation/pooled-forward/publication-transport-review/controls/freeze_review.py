#!/usr/bin/env python3
"""Freeze this bounded independent transport review, without following aliases."""
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
    results = {name: read('results/' + name + '/RESULT.json') for name in ('final-v1', 'final-v2', 'author-v1', 'author-v2')}
    assert (results['final-v1']['tests_run'], results['final-v1']['failures'], results['final-v1']['errors']) == (17, 2, 0)
    assert (results['final-v2']['tests_run'], results['final-v2']['passed']) == (17, 17)
    assert all((results[name]['tests_run'], results[name]['passed']) == (8, 8) for name in ('author-v1', 'author-v2'))
    for name in ('final-v1', 'final-v2'):
        assert results[name]['test_sha256'] == sha(ROOT / 'controls/test_transport_behavior.py')
        target = ROOT / 'results' / name / 'CONTROL-SNAPSHOT.py'
        with target.open('xb') as stream: stream.write((ROOT / 'controls/test_transport_behavior.py').read_bytes())
    candidate = 'revision-v2/publication-tools/cold_storage/cold.py'
    parent = 'revision-v2/publication-tools/archive.py'
    assert sha(ROOT / parent) == 'c412b03c20c9c97b59a550bd5afa02c4c6fd58d0fbd6f9dc81a3bdf9b02796b8'
    assert results['final-v2']['code_sha256'] == results['author-v2']['code_sha256'] == sha(ROOT / candidate)
    critical = ['REVIEW.md', 'snapshots/SOURCES.json', 'controls/test_transport_behavior.py',
                'controls/author_controls.py', 'controls/freeze_review.py', candidate, parent,
                'revision-v2/README.md', 'revision-v2/DIFF.txt']
    critical += ['results/' + name + '/RESULT.json' for name in results]
    critical += ['results/RUN-' + name + '.log' for name in results]
    report = {'version': 1, 'kind': 'bounded-independent-synthetic-transport-review',
              'source_pins_unchanged': True,
              'author_freeze_sha256': '52d7b3a4054b4c3e740f765615470342d36275a22bbd38a650b3dddb1a9a5139',
              'parent_archive_sha256': sha(ROOT / parent),
              'candidate_code_sha256': sha(ROOT / candidate),
              'critical_files_sha256': {name: sha(ROOT / name) for name in critical},
              'results': {name: {k: v[k] for k in ('tests_run', 'passed', 'failures', 'errors')} for name, v in results.items()},
              'finding': 'Required original-index pin accepts None/null; two explicit checks correct this without changing the frozen verifier or valid transport bytes.',
              'finding_scope': 'No corrupted-byte acceptance or bypass of an existing external transport pin was demonstrated.',
              'declaration': {'synthetic_only': True, 'actual_business_grade_alarm_map_report_bodies_read': False,
                              'actual_study_transport_or_cleanup_applied': False, 'SDK_Git_network_delegation_used': False,
                              'prior_alarm_review_and_production_sources_modified': False},
              'development_runs_excluded_from_final_counts': ['results/v1', 'results/v2']}
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
    freeze = {'version': 1, 'kind': 'bounded-independent-synthetic-transport-review-freeze', 'at_unix': time.time(),
              'review_root': str(ROOT), 'review_json_sha256': sha(ROOT / 'REVIEW.json'),
              'file_and_symlink_count_including_freeze': len(files) + 1, 'declaration': report['declaration'],
              'files_excluding_this_freeze': files, 'directories': directories}
    write('REVIEW-FREEZE.json', freeze); (ROOT / 'REVIEW-FREEZE.json').chmod(0o444)
    print(json.dumps({'review_sha256': sha(ROOT / 'REVIEW.json'), 'freeze_sha256': sha(ROOT / 'REVIEW-FREEZE.json'),
                      'candidate_code_sha256': sha(ROOT / candidate), 'independent_test_sha256': sha(ROOT / 'controls/test_transport_behavior.py'),
                      'file_and_symlink_count_including_freeze': len(files) + 1,
                      'results_sha256': {name: sha(ROOT / 'results' / name / 'RESULT.json') for name in results}}))


if __name__ == '__main__': main()
