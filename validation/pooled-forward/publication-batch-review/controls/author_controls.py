#!/usr/bin/env python3
"""Run four unchanged author gate/alias controls within the review root."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--module', type=Path, required=True); parser.add_argument('--run', type=Path, required=True); args = parser.parse_args()
    assert all(p.is_absolute() and p.is_relative_to(ROOT) for p in (args.module, args.run))
    args.run.mkdir(); (args.run / 'temporary').mkdir(); tempfile.tempdir = str(args.run / 'temporary')
    sys.path.insert(0, str(args.module.parent)); source = ROOT / 'snapshots/driver-v1/test_batch.py'
    spec = importlib.util.spec_from_file_location('test_batch', source); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    value = {'tests_run': result.testsRun, 'passed': result.testsRun - len(result.failures) - len(result.errors),
             'failures': len(result.failures), 'errors': len(result.errors),
             'module_sha256': sha(args.module), 'test_sha256': sha(source),
             'details': [{'test': test.id(), 'traceback': tb} for test, tb in result.failures + result.errors],
             'scope': 'Four unchanged synthetic author controls; no native or quality credit.'}
    (args.run / 'RESULT.json').write_text(json.dumps(value, indent=2, sort_keys=True) + '\n'); print(json.dumps(value))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__': raise SystemExit(main())
