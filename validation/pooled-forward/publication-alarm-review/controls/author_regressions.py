#!/usr/bin/env python3
"""Run the unchanged three frozen author test files against a chosen revision."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--modules', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    if not all(path.is_absolute() and path.is_relative_to(root) for path in (args.modules, args.output)):
        raise ValueError('Review paths must remain inside the exclusive review root')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'temporary-cases').mkdir()
    tempfile.tempdir = str(args.output / 'temporary-cases')
    source = root / 'snapshots/frozen-v1'
    sys.path.insert(0, str(args.modules))
    suite = unittest.TestSuite()
    test_pins = {}
    for name in ('test_phase_barriers', 'test_anonymous_projection', 'test_alarm_packet'):
        path = source / (name + '.py')
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec); sys.modules[name] = module
        spec.loader.exec_module(module)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
        test_pins[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    value = {'version': 1, 'kind': 'frozen-author-regressions-against-selected-revision',
             'modules': str(args.modules), 'tests_run': result.testsRun,
             'failures': len(result.failures), 'errors': len(result.errors),
             'passed': result.testsRun - len(result.failures) - len(result.errors),
             'test_files_sha256': test_pins,
             'module_sha256': {name + '.py': hashlib.sha256((args.modules / (name + '.py')).read_bytes()).hexdigest()
                               for name in ('anonymous_projection', 'phase_barriers', 'alarm_packet')},
             'failure_details': [{'test': test.id(), 'traceback': tb} for test, tb in result.failures + result.errors],
             'scope': 'Unchanged author controls, reported separately from independent behavioral controls; synthetic only.'}
    (args.output / 'RESULT.json').write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: value[key] for key in ('tests_run', 'passed', 'failures', 'errors')}))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
