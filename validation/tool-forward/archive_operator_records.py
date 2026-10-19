#!/usr/bin/env python3
"""Retain batch timing/scheduling records after all captures are portable."""
import hashlib
import json
import shutil
from pathlib import Path

R = Path(__file__).resolve().parent


def main():
    sources = []
    for phase in ['d0', 'final']:
        for submission in ['submission-b2e249', 'submission-4f4364']:
            evidence = R / 'evidence' / phase / submission
            plan = json.loads((R / 'private/inputs' / phase / 'manifest.json').read_text())
            expected = {(platform, case['case']) for platform in ['android', 'ios'] for case in plan['cases']}
            actual = {(path.parent.parent.name, path.parent.name) for path in evidence.glob('*/*/capture.json')}
            assert actual == expected, 'Wait for every frozen case and platform'
            assert all((evidence / platform / case / 'portable-sha256.json').is_file() for platform, case in expected)
            inventory = evidence / 'capture-inventory.json'
            if inventory.exists():
                assert json.loads(inventory.read_text())['complete'], 'Wait for complete native attempts, not just running logs'
            sources.append((R / 'cache/ground-truth' / phase / submission, Path(phase) / submission))
    sources.append((R / 'cache/paired-collector-evidence/d0', Path('paired/d0')))
    files = {}
    for source, relative in sources:
        records = sorted(source.glob('*-progress.json')) + sorted(source.glob('*operator-summary.json'))
        assert records, str(source)
        for path in records:
            target = R / 'operator-records' / relative / path.name
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
            else:
                shutil.copy2(path, target)
            files[str(target.relative_to(R))] = digest
    result = {'files': files, 'scope': 'Original completed orchestration records. Command sums, sequential/parallel spans and native failures retained; not business grades or exact active model time.'}
    output = R / 'operator-records/manifest.json'
    encoded = json.dumps(result, indent=2) + '\n'
    if output.exists():
        assert output.read_text() == encoded
    else:
        output.write_text(encoded)
    print(json.dumps({'archived_batch_records': len(files)}))


if __name__ == '__main__':
    main()
