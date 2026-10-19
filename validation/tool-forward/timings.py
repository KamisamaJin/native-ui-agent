#!/usr/bin/env python3
"""Extract recorded calendar/native costs without inventing active model time."""
import argparse
import json
from pathlib import Path

R = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def captures(root):
    rows = []
    for path in sorted(root.glob('*/*/capture.json')):
        capture = read(path)
        manifest_path = path.parent / 'manifest.json'
        observation_path = path.parent / 'observation.json'
        manifest = read(manifest_path) if manifest_path.exists() else {}
        observation = read(observation_path) if observation_path.exists() else {}
        rows.append({'platform': path.parent.parent.name, 'case': path.parent.name,
                     'seconds': capture['seconds'], 'exit_code': capture['exit_code'],
                     'started_at': manifest.get('started_at'),
                     'finished_at': manifest.get('finished_at'),
                     'native_test_count': manifest.get('native_test_count'),
                     'snapshots': len(observation.get('snapshots', [])),
                     'observation_available': observation_path.is_file(),
                     'capture': str(path.relative_to(R))})
    by_platform = {}
    for platform in sorted({r['platform'] for r in rows}):
        selected = [r for r in rows if r['platform'] == platform]
        starts = [r['started_at'] for r in selected if r['started_at'] is not None]
        ends = [r['finished_at'] for r in selected if r['finished_at'] is not None]
        by_platform[platform] = {'captures': len(selected),
                                 'command_seconds_sum': round(sum(r['seconds'] for r in selected), 3),
                                 'native_snapshots': sum(r['snapshots'] for r in selected),
                                 'recorded_span_seconds': round(max(ends) - min(starts), 3)
                                 if len(starts) == len(ends) == len(selected) else None}
    return {'captures': rows, 'by_platform': by_platform,
            'command_seconds_sum': round(sum(r['seconds'] for r in rows), 3),
            'scope': 'Command sums include native build/test/export. Parallel sums are not total wall time; spans include inter-command overhead.'}


def phases(submission):
    result = {}
    paths = {'d0': R / 'implementations/d0' / submission / 'reports/d0.json',
             'readonly_review': R / 'phase-reports' / submission / 'readonly-review/reports/self-review.json',
             'repair': R / 'phase-reports' / submission / 'repair/reports/repair.json'}
    for phase, path in paths.items():
        if not path.is_file():
            continue
        report = read(path)
        result[phase] = {k: report.get(k) for k in ['startedAt', 'finishedAt', 'elapsedSeconds', 'budgetSeconds']}
        result[phase]['recorded_timing_details'] = {
            k: v for k, v in report.items()
            if any(word in k.lower() for word in ['timing', 'accounting', 'pause', 'interrupt', 'activewall'])}
        result[phase]['report'] = str(path.relative_to(R))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--submission', required=True)
    a = p.parse_args()
    output = {'submission': a.submission, 'phases': phases(a.submission),
              'independent_captures': {}, 'active_model_seconds': None,
              'limitation': 'Exact reasoning/queue split is unavailable. Do not equate calendar duration or interruption-subtracted estimates with measured active model time.'}
    for phase in ['d0', 'final']:
        root = R / 'evidence' / phase / a.submission
        if root.is_dir():
            output['independent_captures'][phase] = captures(root)
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
