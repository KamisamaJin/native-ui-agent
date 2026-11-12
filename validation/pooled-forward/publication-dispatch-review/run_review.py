"""Run bounded dispatch review; never create or read actual study inputs."""
import json
from pathlib import Path
import platform
import sys
import time
import unittest

import test_dispatch_review as tests
from fixture_dispatch import HERE, sha, encoded, AUTHOR_FREEZE_SHA, BATCH_FREEZE_SHA


def main():
    host = HERE/'HOST';host.mkdir(exist_ok=True)
    run = host/('review-'+str(time.time_ns()));run.mkdir()
    code = {}
    for name in ['prepare_alarm_dispatch_v3.py', 'fixture_dispatch.py', 'test_dispatch_review.py', 'run_review.py']:
        code[name] = sha((HERE/name).read_bytes())
    assert sha((HERE/'vendor/ALARM-DISPATCH-v2-AUTHOR-FREEZE.json').read_bytes()) == AUTHOR_FREEZE_SHA
    with (run/'RUN.log').open('x') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    (run/'OBSERVATIONS.json').write_bytes(encoded(tests.OBSERVATIONS))
    count = sum(p.is_file() for p in HERE.rglob('*'))+1
    value = {'kind': 'independent-synthetic-dispatch-review-result-v1', 'recorded_at_unix': time.time(),
             'interpreter': sys.version, 'platform': platform.platform(), 'tests': result.testsRun,
             'failures': len(result.failures), 'errors': len(result.errors), 'passed': result.wasSuccessful() and count <= 400,
             'new_file_count_at_result': count, 'file_limit': 400,
             'author_freeze_sha256': AUTHOR_FREEZE_SHA, 'borrowed_batch_review_freeze_sha256': BATCH_FREEZE_SHA,
             'code_sha256': code, 'observations_sha256': sha((run/'OBSERVATIONS.json').read_bytes()),
             'synthetic_anchor_only_cli': True, 'production_outer_supplement_anchor_unchanged': True,
             'actual_study_reads_or_dispatch': False, 'borrowed_corpus_mutated': False,
             'scope': 'Recorded synthetic input/context/byte bindings and local prompt/START preparation, not genuine actor execution, product truth, native acquisition or source-domain validation.'}
    (run/'RESULT.json').write_bytes(encoded(value))
    print(json.dumps({'path': str(run/'RESULT.json'), 'sha256': sha((run/'RESULT.json').read_bytes()), 'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'files': count}))
    return 0 if value['passed'] else 1


if __name__ == '__main__':raise SystemExit(main())
