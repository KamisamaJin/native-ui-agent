#!/usr/bin/env python3
"""Run the eight frozen author material controls against one selected revision."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest


def main():
    p = argparse.ArgumentParser(); p.add_argument('--module', type=Path, required=True); p.add_argument('--run', type=Path, required=True); a = p.parse_args()
    root = Path(__file__).resolve().parent.parent
    assert all(path.is_absolute() and path.is_relative_to(root) for path in (a.module, a.run))
    a.run.mkdir(parents=True, exist_ok=False); sys.path.insert(0, str(a.module.parent))
    source = root / 'snapshots/alarm-material-tools-v1/test_material.py'
    spec = importlib.util.spec_from_file_location('test_material', source); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    value = {'tests_run': result.testsRun, 'passed': result.testsRun - len(result.failures) - len(result.errors),
             'failures': len(result.failures), 'errors': len(result.errors),
             'module_sha256': sha(a.module), 'test_sha256': sha(source),
             'details': [{'test': test.id(), 'traceback': tb} for test, tb in result.failures + result.errors],
             'scope': 'Eight unchanged author controls; separate denominator; synthetic only.'}
    (a.run / 'RESULT.json').write_text(json.dumps(value, indent=2, sort_keys=True) + '\n'); print(json.dumps(value))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__': raise SystemExit(main())
