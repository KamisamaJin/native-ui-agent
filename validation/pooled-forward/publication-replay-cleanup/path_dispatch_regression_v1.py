"""Reproduce the CI fixture error with Python3.11 Path.chmod dispatch semantics.

Runs only one tiny hostile member replacement for each retained test version.
This is a dispatch shim on the local interpreter, not an actual Linux/3.11 run.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback
from unittest import mock

HERE = Path(__file__).resolve().parent
RUN = HERE / 'HOST-path-dispatch-v1'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def python311_chmod(self, mode, *, follow_symlinks=True):
    return os.chmod(self, mode, follow_symlinks=follow_symlinks)


def main():
    assert not RUN.exists()
    RUN.mkdir()
    results = []
    for version in ['v2', 'v3']:
        source = HERE / ('test_cleanup_' + version + '.py')
        module = load(source, 'retained_dispatch_controls_' + version)
        work = RUN / version
        work.mkdir()
        controls = module.Controls(work)
        case = work / 'CASES/member-preempt'
        case.mkdir()
        fixture = controls.fixture(case)
        caught = None
        try:
            with mock.patch.object(Path, 'chmod', python311_chmod):
                actual = controls.fault(fixture, 'member-preempt')
        except BaseException as error:
            caught = {'type': type(error).__name__, 'message': str(error)}
            (work / 'ORIGINAL-FAILURE.txt').write_text(traceback.format_exc())
        if version == 'v2':
            assert caught == {'type': 'AssertionError', 'message': 'Path chmod forbidden'}
            row = {'version': version, 'expected_original_test_failure_reproduced': True, 'caught': caught}
        else:
            assert caught is None and actual['caught']['type'] == 'ValueError'
            assert actual['source_unchanged'] and actual['failure_exists'] and not actual['success_exists']
            row = {'version': version, 'fixture_completed_and_real_helper_rejected_replacement': True, 'actual': actual}
        results.append(row)
    result = {'version': 1, 'at_unix': time.time(), 'status': 'verified', 'actual_python': sys.version,
              'actual_linux_python311_run': False, 'shim': 'Path.chmod delegates to os.chmod as CPython v3.11.18 does',
              'primary_source': 'https://github.com/python/cpython/blob/v3.11.18/Lib/pathlib.py',
              'helper_changed': False, 'results': results, 'sdk_or_main_dataset_access': False}
    (RUN / 'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'verified', 'old_fixture_failure_reproduced': True, 'new_fixture_tests_unchanged_guard': True}))


if __name__ == '__main__':
    main()
