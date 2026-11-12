"""Verify fixed approval data and retain only counts/byte/protocol checks."""
import json
from pathlib import Path
import sys
import time
import unittest

import test_format_contract
import verify_catalog as v


def main():
    here = Path(__file__).resolve().parent
    output = here/('CHECKS-'+str(time.time_ns()));output.mkdir()
    inputs = v.parse((here/'INPUTS.json').read_bytes())
    approval_ref = {'path': str(here/'APPROVAL.json'), 'sha256': v.sha((here/'APPROVAL.json').read_bytes())}
    entries = dict(inputs['refs']);entries[approval_ref['path']] = {'copy': 'APPROVAL.json', 'sha256': approval_ref['sha256']}
    reader = v.ExactReader(here, entries)
    for original, row in entries.items():
        if 'copy' in row:reader.read_bytes(original)
    verification, approved = v.verify_contract(reader, approval_ref, inputs['catalog_seal'])
    with (output/'TEST.log').open('x') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_format_contract))
    value = {'kind': 'independent-claim-format-responsibility-review-checks', 'recorded_at_unix': time.time(),
             'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'passed': result.wasSuccessful(),
             'documents': verification['documents'], 'counts': verification['counts'], 'classifications': verification['classifications'],
             'approved_locations': len(approved), 'unapproved_locations': 0, 'all_originals_reverified_unchanged': True,
             'approval_ref': approval_ref, 'catalog_seal': inputs['catalog_seal'],
             'read_keys': sorted(set(reader.reads)), 'no_referenced_target_access_or_actual_projection': True,
             'code_pins': {n: v.sha((here/n).read_bytes()) for n in ['verify_catalog.py', 'test_format_contract.py', 'run_checks.py']}}
    path = output/'RESULT.json';path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'result': str(path), 'sha256': v.sha(path.read_bytes()), 'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'approved': len(approved), 'unapproved': 0}))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':raise SystemExit(main())
