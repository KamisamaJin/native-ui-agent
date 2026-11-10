#!/usr/bin/env python3
"""Derive anonymous observed costs; never infer quality from a process exit."""
import argparse
import json
from pathlib import Path

import business

R = Path(__file__).resolve().parent


def compute():
    start = business.read(R / 'business-administration/author-dispatch.json')['started_at_unix']
    initial = business.read(R / 'business-administration/initial-ready.json')['at_unix']
    result = {'author_dispatch_at_unix': start, 'shared_author_to_initial_seal_seconds': initial - start,
              'arms': {}, 'scope': 'Observed command, development endpoint and sampled allocated-byte costs. Command sums are serial-equivalent work, not overlapping wall time. Common initial-reference/independent grading/publication are separate.'}
    samples = []
    for name in ['whole-study-meter.jsonl', 'whole-study-meter-2.jsonl']:
        path = R / 'business-administration' / name
        if path.is_file():
            samples.extend(json.loads(line) for line in path.read_text().splitlines() if line)
    for arm in ['A', 'B']:
        phases = {}
        for phase in ['D0', 'D1', 'D2', 'Final', 'Hidden']:
            scope = 'private/Hidden' if phase == 'Hidden' else 'public/' + phase
            commands = {pl: business.read(R / 'business-evidence' / arm / scope / pl / 'command.json') for pl in ['ios', 'android']}
            phases[phase] = {'platform_seconds': {pl: row['finished_at_unix'] - row['started_at_unix'] for pl, row in commands.items()},
                             'first_start_at_unix': min(row['started_at_unix'] for row in commands.values()),
                             'last_end_at_unix': max(row['finished_at_unix'] for row in commands.values()),
                             'exit_codes': {pl: row['exit_code'] for pl, row in commands.items()}}
            phases[phase]['elapsed_span_seconds'] = phases[phase]['last_end_at_unix'] - phases[phase]['first_start_at_unix']
        closure = business.read(R / 'business-administration' / ('public-closure-' + arm + '.json'))
        self_end = max(closure['final_self_completion_at_unix'], closure['final_claims_file_mtime_unix'])
        repair = business.read(R / 'business-administration' / ('repair-dispatch-' + arm + '.json'))
        end_native = phases['Hidden']['last_end_at_unix']
        own_rows = [row for row in samples if start <= row['started_at_unix'] <= end_native]
        result['arms'][arm] = {'phases': phases, 'self_closed_at_unix': self_end,
                              'author_to_public_self_closure_seconds': self_end - start,
                              'repair_dispatch_to_public_self_closure_seconds': self_end - repair['started_at_unix'],
                              'D0_to_repair_dispatch_wait_seconds': repair['started_at_unix'] - phases['D0']['last_end_at_unix'],
                              'public_self_to_common_hidden_dispatch_wait_seconds': phases['Hidden']['first_start_at_unix'] - self_end,
                              'native_command_seconds_by_platform': {pl: sum(phases[p]['platform_seconds'][pl] for p in ['D0', 'D2', 'Final', 'Hidden']) for pl in ['ios', 'android']},
                              'shared_bad_argument_request_seconds_by_platform': phases['D1']['platform_seconds'],
                              'configured_group_peak_allocated_bytes_through_own_hidden_native': max(row['groups'][arm]['allocated_bytes'] for row in own_rows),
                              'disk_window': 'Author dispatch through this arm final hidden command closure; exclude later common-reference use of the shared study-owned control device. Configured workspace/build/evidence/device paths only; not APFS physical bytes or global SDK caches.'}
    result['configured_whole_study_observed_peak_allocated_bytes'] = max(row['total_allocated_bytes'] for row in samples)
    result['sample_counts'] = {'all': len(samples), 'budget_exceeded': sum(row['budget_exceeded'] for row in samples)}
    result['measurement_limits'] = 'Sample timestamps/elapsed directory walks are retained; nominal interval is 2 seconds, not guaranteed exact cadence. Whole-study means configured roots in both segment specs. Independent reviewer packet/crop/output storage is separately inventoried, not an exact project/global physical disk maximum.'
    common = {pl: business.read(R / 'business-evidence/initial/private-reference' / pl / 'command.json') for pl in ['ios', 'android']}
    result['common_initial_hidden_reference_seconds_by_platform'] = {pl: row['finished_at_unix'] - row['started_at_unix'] for pl, row in common.items()}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    value = compute()
    if args.output:
        business.save(args.output, value)
    else:
        print(json.dumps(value, indent=2))
