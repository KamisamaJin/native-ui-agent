"""Retain original admissions and bounded independent controls in a new HOST run."""
import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import unittest

import coverage_registry_v2 as revised
import test_coverage_review as tests


def save(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
    with path.open('xb') as stream:
        stream.write(data)
    path.chmod(0o444)
    return {'path': str(path), 'sha256': revised.sha(data)}


def run(output):
    revised.need(not output.exists(), 'Review output must be fresh; retain all earlier failures')
    output.mkdir(parents=True)
    author = subprocess.run([sys.executable, '-B', str(Path(__file__).resolve().parent/'vendor/test_coverage_registry.py'), '-v'], capture_output=True)
    (output/'AUTHOR4.stdout').write_bytes(author.stdout)
    (output/'AUTHOR4.stderr').write_bytes(author.stderr)
    fixture = tests.fixture()
    fixture_ref = save(output/'BASE-FIXTURE.json', {'tasks': fixture[0], 'cells': fixture[1], 'evidence': fixture[2], 'synthetic_only': True})
    paths, pins = tests.write_fixture(output)
    completed = tests.cli(paths, pins, output/'GENERIC-PROJECTION.json')
    (output/'CLI.stdout').write_text(completed.stdout)
    (output/'CLI.stderr').write_text(completed.stderr)
    suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
    with (output/'RUN.log').open('x') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    admissions_ref = save(output/'RETAINED-ORIGINAL-ADMISSIONS.json', {
        'frozen_author_version_unchanged': True, 'base_fixture': fixture_ref, 'observations': tests.OBSERVATIONS,
        'scope': 'Synthetic original weaknesses and boundary observations only; no actual design, report, source, image, grade or map data.'})
    value = {'kind': 'independent-prospective-coverage-adapter-review-result-v1', 'recorded_at_unix': time.time(),
             'interpreter': sys.version, 'platform': platform.platform(), 'tests': result.testsRun,
             'failures': len(result.failures), 'errors': len(result.errors), 'generic_cli_returncode': completed.returncode,
             'passed': result.wasSuccessful() and completed.returncode == 0 and author.returncode == 0,
             'original_author_freeze_sha256': 'd76216dbcc573d1a3732046e6034849332534ed9cc99f514e3347a69c850d71c',
             'original_author_tests_reproduced': 4, 'original_author_tests_returncode': author.returncode, 'original_admissions': admissions_ref,
             'generic_inputs': [{'path': str(p), 'sha256': h} for p, h in zip(paths, pins)],
             'code_sha256': {name: revised.sha((Path(__file__).resolve().parent/name).read_bytes()) for name in
                             ['coverage_registry_v2.py', 'test_coverage_review.py', 'run_review.py']},
             'actual_study_inputs_read_or_applied': False,
             'limitation': 'External original prospective seal authenticates complete cells/task order. No state/cell oracle or outcome inference. Projection cannot change source U into P.'}
    ref = save(output/'RESULT.json', value)
    print(json.dumps(ref))
    return 0 if value['passed'] else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    raise SystemExit(run(p.parse_args().output))
