#!/usr/bin/env python3
"""Extract recorded calendar/native costs without inventing active model time."""
import argparse
import hashlib
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
        summary = manifest.get('native_summary', {})
        test_start, test_end = summary.get('startTime'), summary.get('finishTime')
        native_span = test_end - test_start if isinstance(test_start, (int, float)) and isinstance(test_end, (int, float)) else None
        archive_span = manifest['finished_at'] - test_end if isinstance(test_end, (int, float)) and manifest.get('finished_at') is not None else None
        assert native_span is None or native_span >= 0, str(path)
        assert archive_span is None or archive_span >= 0, str(path)
        rows.append({'platform': path.parent.parent.name, 'case': path.parent.name,
                     'seconds': capture['seconds'], 'exit_code': capture['exit_code'],
                     'started_at': manifest.get('started_at'),
                     'finished_at': manifest.get('finished_at'),
                     'native_summary_test_span_seconds': round(native_span, 3) if native_span is not None else None,
                     'post_test_finish_archive_seconds': round(archive_span, 3) if archive_span is not None else None,
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
                                 'native_summary_test_span_seconds_sum': round(sum(r['native_summary_test_span_seconds'] for r in selected), 3)
                                 if all(r['native_summary_test_span_seconds'] is not None for r in selected) else None,
                                 'post_test_finish_archive_seconds_sum': round(sum(r['post_test_finish_archive_seconds'] for r in selected), 3)
                                 if all(r['post_test_finish_archive_seconds'] is not None for r in selected) else None,
                                 'recorded_span_seconds': round(max(ends) - min(starts), 3)
                                 if len(starts) == len(ends) == len(selected) else None}
    starts = [r['started_at'] for r in rows if r['started_at'] is not None]
    ends = [r['finished_at'] for r in rows if r['finished_at'] is not None]
    return {'captures': rows, 'by_platform': by_platform,
            'recorded_span_seconds': round(max(ends) - min(starts), 3)
            if rows and len(starts) == len(ends) == len(rows) else None,
            'command_seconds_sum': round(sum(r['seconds'] for r in rows), 3),
            'scope': 'Command sums include native build/test/export. Parallel sums are not total wall time; spans include inter-command overhead. iOS summary test spans include the native test session, not isolated AX CPU time. Post-test-finish archive spans include summary reading, attachment export and archive assembly, not isolated export CPU time; unavailable timestamps remain null.'}


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


def engineering_costs():
    groups = {
        'generic_tool_engineering': list((R / 'engineering').glob('*/manifest.json')),
        'independent_generic_validation': list((R.parent / 'tool-capabilities/evidence').glob('*/manifest.json')),
        'common_numeric_transport_probe': [R / 'transport-amendment/native-probe/manifest.json']}
    output = {}
    for name, paths in groups.items():
        rows = []
        for path in sorted(paths):
            m = read(path)
            observation = read(path.parent / 'observation.json')
            rows.append({'case': path.parent.name, 'manifest': str(path.relative_to(R.parent)),
                         'manifest_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                         'native_tests': m['native_test_count'],
                         'seconds': round(m['finished_at'] - m['started_at'], 3),
                         'snapshots': len(observation['snapshots'])})
        output[name] = {'attempts': rows, 'native_tests': sum(r['native_tests'] for r in rows),
                        'native_seconds_sum': round(sum(r['seconds'] for r in rows), 3),
                        'snapshots': sum(r['snapshots'] for r in rows)}
    output['scope'] = 'Recorded native build/test/export spans including failed/negative probes. Sums are not overall wall time or exact model engineering time; generic probes are not extra business trial samples.'
    return output


def main():
    p = argparse.ArgumentParser()
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--submission')
    group.add_argument('--engineering', action='store_true')
    a = p.parse_args()
    if a.engineering:
        print(json.dumps(engineering_costs(), indent=2))
        return
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
