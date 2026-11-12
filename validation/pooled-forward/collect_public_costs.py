#!/usr/bin/env python3
"""Summarize immutable public controller receipts; never infer hidden quality."""
import argparse
import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text())


def collect(root):
    manifest = load(root / 'manifest.json')
    rows = {}
    for task in manifest['tasks']:
        for arm in task['arms']:
            seal = root / 'arms' / task['id'] / arm / 'SELF-SEAL.json'
            value = load(seal) if seal.exists() else {}
            rows[task['id'] + '/' + arm] = {'task': task['id'], 'arm': arm, 'self_sealed': bool(value),
                'own_delivery_wall_seconds': value.get('own_delivery_wall_seconds'),
                'public_service_accepted': value.get('public_service_accepted'),
                'hidden_quality': 'NOT_ASSESSED_BY_THIS_COST_TOOL', 'profile_commands': [], 'request_errors': []}
    for path in sorted((root / 'requests').glob('*/result.json')):
        result = load(path)
        row = rows[result['task'] + '/' + result['arm']]
        for outcome in result['outcomes']:
            item = {k: outcome.get(k) for k in ['action', 'profile', 'wall_seconds', 'exit_code', 'error',
                    'accepted', 'service_status', 'new_ui_acquisition', 'native_collection_success', 'capture_reused']}
            item.update(request_id=result['request_id'], queue_wait_seconds=result['queue_wait_seconds'])
            folder = path.parent / outcome['profile']
            meter = folder / 'meter.jsonl'
            if meter.exists():
                samples = [json.loads(v) for v in meter.read_text().splitlines()]
                item['observed_meter_sample_durations_seconds'] = [v['finished_at_unix'] - v['started_at_unix'] for v in samples]
            if outcome.get('capture'):
                native = Path(outcome['capture']['path']).parent / 'native/manifest.json'
                if native.exists():
                    original = load(native)
                    item['native_manifest'] = {k: original.get(k) for k in ['status', 'native_test_count',
                                                    'test_exit_code', 'exit_code', 'timings']}
                    if original.get('started_at') is not None and original.get('finished_at') is not None:
                        item['collector_wall_seconds'] = original['finished_at'] - original['started_at']
                        item['collector_reference_is_new_work'] = item['new_ui_acquisition'] is True
            row['profile_commands'].append(item)
            if item['error']:
                row['request_errors'].append({'request_id': result['request_id'], 'profile': item['profile'], 'error': item['error']})
    for row in rows.values():
        row['profile_service_wall_seconds'] = sum(v['wall_seconds'] for v in row['profile_commands'])
        row['new_native_UI_acquisitions'] = sum(v['new_ui_acquisition'] is True for v in row['profile_commands'])
        row['verified_new_native_collections'] = sum(v['native_collection_success'] is True for v in row['profile_commands'])
        row['ordinary_capture_reuse_flags'] = sum(v['capture_reused'] is True for v in row['profile_commands'])
        row['new_collector_wall_seconds'] = sum(v.get('collector_wall_seconds', 0)
                                                for v in row['profile_commands'] if v['new_ui_acquisition'] is True)
        row['work_by_action_seconds'] = {a: sum(v['wall_seconds'] for v in row['profile_commands'] if v['action'] == a)
                                        for a in sorted({v['action'] for v in row['profile_commands']})}
    return {'kind': 'PUBLIC_RECEIPT_COSTS_ONLY', 'rows': list(rows.values()),
            'scope': 'Observed own public wall and full per-profile service costs including common supervision/sampling. Collector flags and SDK success are not delivery or hidden quality. Source/image/cause verdicts require separate sealed independent grading.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    value = collect(args.run.resolve())
    with args.output.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'rows': len(value['rows']), 'self_sealed': sum(r['self_sealed'] for r in value['rows']),
                      'hidden_quality_evaluated': False}))


if __name__ == '__main__':
    main()
