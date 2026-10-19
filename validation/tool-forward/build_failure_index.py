#!/usr/bin/env python3
"""Index original attempts without deciding whether a product assertion passed."""
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parent


def main():
    rows = []
    for folder in ['evidence', 'paired-evidence']:
        for path in sorted((R / folder).rglob('capture.json')):
            capture = json.loads(path.read_text())
            rows.append({
                'capture': str(path.relative_to(R)),
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'status': capture.get('status'),
                'exit_code': capture.get('exit_code'),
                'seconds': capture.get('seconds'),
                'observation_available': (path.parent / 'observation.json').is_file(),
                'raw_log': str((path.parent / 'operator.log').relative_to(R))
                if (path.parent / 'operator.log').is_file() else None,
                'portable_seal': str((path.parent / 'portable-sha256.json').relative_to(R)),
            })
    assert len(rows) == 68, 'Wait for every preregistered capture, including failures'
    notes = []
    for path in sorted((R / 'phase-reports').glob('*/*/manifest.json')):
        notes.append({'phase_archive': str(path.parent.relative_to(R)),
                      'manifest_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    result = {
        'scope': 'All 68 planned native attempts, not 68 successful tests. Nonzero native exit can coexist with usable partial evidence; only sealed independent atomic grades determine product outcomes.',
        'attempts': rows,
        'nonzero_exit_attempts': [row['capture'] for row in rows if row['exit_code'] != 0],
        'unavailable_observations': [row['capture'] for row in rows if not row['observation_available']],
        'builder_phase_archives': notes,
        'common_transport_repair': 'transport-amendment/freeze.json',
        'common_scheduler_pre_native_failures': 'operator-case-name-amendment.json',
        'public_integration_reports': [str(path.relative_to(R)) for path in
                                       sorted((R / 'implementations/d0').glob('*/reports/d0.json'))],
        'omitted_automatic_videos': [str(path.relative_to(R)) for folder in
                                    ['evidence', 'paired-evidence', 'phase-reports'] for path in
                                    sorted((R / folder).rglob('portable-scope.json'))],
    }
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    destination = R / 'failure-index.json'
    if destination.exists():
        assert destination.read_text() == encoded, 'Original failure index changed'
    else:
        destination.write_text(encoded)
    print(json.dumps({'indexed_native_attempts': len(rows),
                      'nonzero_exit_attempts': len(result['nonzero_exit_attempts']),
                      'scope': 'Execution status only, not UI acceptance.'}))


if __name__ == '__main__':
    main()
