"""Reproduce bounded HOST checks from owned metadata; no live original reads."""
import argparse
import copy
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

from clock_audit import SnapshotReader, audit, digest, need, parse
from test_clock_audit import original_helper_observations


def save(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
    with path.open('xb') as stream:
        stream.write(raw)
    path.chmod(0o444)
    return {'path': str(path), 'sha256': digest(raw)}


def run(evidence_path, expected, output):
    raw = evidence_path.read_bytes()
    need(digest(raw) == expected, 'External evidence pin differs')
    evidence = parse(raw)
    need(not output.exists(), 'HOST output must be new; preserve earlier attempts')
    output.mkdir(parents=True)
    reader = SnapshotReader(evidence_path.parent, evidence['refs'])
    ledger = audit(reader, evidence)
    ledger_ref = save(output/'LEDGER.json', ledger)
    observations_ref = save(output/'ORIGINAL-HELPER-OBSERVATIONS.json', original_helper_observations())

    negatives = []

    def rejected(name, action):
        try:
            action()
        except (ValueError, KeyError, FileNotFoundError) as exc:
            negatives.append({'name': name, 'status': 'expected rejection', 'exception': type(exc).__name__, 'message': str(exc)})
        else:
            raise ValueError('Hostile control unexpectedly admitted: '+name)

    changed = copy.deepcopy(evidence)
    key = next(k for k in changed['refs'] if k.endswith('/episodes/T1/B/continuation/END.json'))
    del changed['refs'][key]
    rejected('omitted failed T1/B v2 END is not silently ignored', lambda: audit(reader, changed))
    changed = copy.deepcopy(evidence)
    changed['collector_controls']['1']['entry']['clock_metadata']['scheduler']['sha256'] = '0'*64
    rejected('unbound same-parent collector context', lambda: audit(reader, changed))
    changed = copy.deepcopy(evidence)
    changed['public_events'][10]['clock_metadata']['previous_sha256'] = '0'*64
    rejected('changed public event clock-projection chain', lambda: audit(reader, changed))
    changed = copy.deepcopy(evidence)
    changed['corrections'][0]['sha256'] = '0'*64
    rejected('changed original correction byte pin', lambda: audit(reader, changed))
    changed = copy.deepcopy(evidence)
    changed['public_events'] = [x for x in changed['public_events'] if x['clock_metadata']['kind'] != 'self_sealed']
    rejected('missing public self seals cannot become complete timing', lambda: audit(reader, changed))
    rejected('undeclared original key has no live-path fallback', lambda: reader.read_bytes('/undeclared/START.json'))
    negative_ref = save(output/'EXPECTED-REJECTIONS.json', {'controls': negatives, 'count': len(negatives)})

    completed = subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v', 'test_clock_audit'],
                               cwd=Path(__file__).resolve().parent, capture_output=True)
    (output/'UNIT.stdout').write_bytes(completed.stdout)
    (output/'UNIT.stderr').write_bytes(completed.stderr)
    result = {'kind': 'independent-clock-audit-HOST-result-v1', 'recorded_at_unix': time.time(),
              'interpreter': sys.version, 'platform': platform.platform(),
              'evidence': {'path': str(evidence_path), 'sha256': expected},
              'counts': ledger['counts'], 'unit_returncode': completed.returncode,
              'unit_control_count': 28, 'hostile_metadata_rejection_count': len(negatives),
              'ledger': ledger_ref, 'original_helper_observations': observations_ref,
              'negative_controls': negative_ref, 'actual_grade_report_source_image_map_bodies_opened': False,
              'status': 'passed' if completed.returncode == 0 else 'failed'}
    ref = save(output/'RESULT.json', result)
    need(completed.returncode == 0, 'Unit controls failed; retained logs/results')
    return ref


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--evidence-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(run(args.evidence, args.evidence_sha256, args.output), sort_keys=True))
