#!/usr/bin/env python3
"""Run the eight unchanged small author controls within the review namespace."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


def main():
    p = argparse.ArgumentParser(); p.add_argument('--modules', type=Path, required=True); p.add_argument('--run', type=Path, required=True); a = p.parse_args()
    root = Path(__file__).resolve().parent.parent
    assert all(path.is_absolute() and path.is_relative_to(root) for path in (a.modules, a.run))
    a.run.mkdir(parents=True, exist_ok=False); (a.run / 'temporary').mkdir(); tempfile.tempdir = str(a.run / 'temporary')
    sys.path.insert(0, str(a.modules))
    source = root / 'snapshots/publication-tools/cold_storage/test_cold.py'
    spec = importlib.util.spec_from_file_location('test_cold', source); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    value = {'tests_run': result.testsRun, 'passed': result.testsRun - len(result.failures) - len(result.errors),
             'failures': len(result.failures), 'errors': len(result.errors),
             'code_sha256': sha(a.modules / 'cold.py'), 'test_sha256': sha(source),
             'parent_archive_sha256': sha(a.modules.parent / 'archive.py'),
             'details': [{'test': test.id(), 'traceback': tb} for test, tb in result.failures + result.errors],
             'scope': 'Eight unchanged author controls, separate from independent behavioral controls; synthetic only.'}
    (a.run / 'RESULT.json').write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    print(json.dumps(value)); return 0 if result.wasSuccessful() else 1


if __name__ == '__main__': raise SystemExit(main())
