"""Retain bounded source-only/synthetic nullable-cost review evidence."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import unittest

import test_cost_inputs as tests


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    here = Path(__file__).resolve().parent;host = here/'HOST';run = host/('review-'+str(time.time_ns()));run.mkdir()
    freeze_raw = (here/'vendor/AUTHOR-FREEZE.json').read_bytes()
    assert sha(freeze_raw) == 'ce385d32506b055e1cc53f37266133052e96fcd462fbf3185c01efc82fafa5d7'
    for name, expected in json.loads(freeze_raw)['files'].items():assert sha((here/'vendor'/name).read_bytes()) == expected
    author = subprocess.run([sys.executable, '-B', str(here/'vendor/test_shared_unknown.py'), '-v'], capture_output=True)
    (run/'AUTHOR8.stdout').write_bytes(author.stdout);(run/'AUTHOR8.stderr').write_bytes(author.stderr)
    with (run/'RUN.log').open('x') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    fixture = tests.fixture()
    (run/'BASE-FIXTURE.json').write_text(json.dumps({'synthetic_only': True, 'cases': fixture[0], 'synthetic_assignment': fixture[1], 'coverage_registry': fixture[2], 'shared_costs': fixture[3]}, indent=2, sort_keys=True)+'\n')
    (run/'OBSERVATIONS.json').write_text(json.dumps(tests.OBSERVATIONS, indent=2, sort_keys=True, allow_nan=False)+'\n')
    value = {'kind': 'independent-nullable-shared-cost-input-review-result-v1', 'recorded_at_unix': time.time(),
        'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'author_tests': 8, 'author_returncode': author.returncode, 'passed': result.wasSuccessful() and author.returncode == 0,
        'interpreter': sys.version, 'platform': platform.platform(), 'original_author_freeze_sha256': sha(freeze_raw),
        'code_sha256': {n: sha((here/n).read_bytes()) for n in ['test_cost_inputs.py', 'run_review.py']},
        'metric_v2_sha256': sha((here/'vendor/upstream/metric_rules_v2.py').read_bytes()),
        'metric_v3_sha256': sha((here/'vendor/metric_rules_v3.py').read_bytes()),
        'actual_data_read_or_applied': False, 'source_correction_needed': False,
        'scope': 'Only nullable shared cost reporting. Complete-cell/quality/cost provenance remains caller responsibility; known subtotal is not total study cost and no allocation is introduced.'}
    (run/'RESULT.json').write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'path': str(run/'RESULT.json'), 'sha256': sha((run/'RESULT.json').read_bytes()), 'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'author_returncode': author.returncode}))
    return 0 if value['passed'] else 1


if __name__ == '__main__':raise SystemExit(main())
