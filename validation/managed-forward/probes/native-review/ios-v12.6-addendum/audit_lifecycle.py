#!/usr/bin/env python3
"""Offline comparison of original lifecycle facts; no ps, SDK, signal or device actions."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = OUT.parents[2]
EVIDENCE = BASE / 'evidence/ios-qualification-v12.6'


def load(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def events(p):
    return [json.loads(x) for x in p.read_text().splitlines()]


def command_success(trace, verb, uuid):
    return [x for x in trace if x['kind'] == 'simctl_command' and
            x['argv'] == ['xcrun', 'simctl', verb, uuid] and x['exit_code'] == 0]


source_map = {
    str(BASE / 'cache/neutral/alerttoast/Sources/AlertToast/NeutralCounter.swift'): sha(BASE / 'evidence/probes/production/alerttoast/Sources/AlertToast/NeutralCounter.swift'),
    str(BASE / 'cache/neutral/reply/Reply/app/src/main/java/com/example/reply/ui/components/NeutralCounter.kt'): sha(BASE / 'evidence/probes/production/reply/Reply/app/src/main/java/com/example/reply/ui/components/NeutralCounter.kt'),
}
interrupts = []
for name, opname, rootname in [('term', 'ios-sdk-term-v12.6', 'term-resources'),
                               ('kill-reconcile', 'ios-sdk-kill-reconcile-v12.6', 'kill-resources')]:
    op = BASE / 'operators' / opname
    raw = EVIDENCE / name
    result = load(op / 'result.json')
    manifest = load(raw / 'capture/native/manifest.json')
    receipt = result['sdk_receipt_before']
    leader = next(x for x in result['group_before'] if x['pid'] == receipt['pid'])
    trace = events(EVIDENCE / rootname / 'events.jsonl')
    started = next(x for x in trace if x['kind'] == 'process_started')
    first = (op / 'pre-interrupt-test.log').read_bytes()
    retained = (raw / 'capture/native/test.log').read_bytes()
    uuid = result['device_before']['udid']
    creates = [x for x in trace if x['kind'] == 'simctl_command' and 'create' in x['argv']]
    creation_digest = hashlib.sha256((uuid + '\n').encode()).hexdigest()
    resources = result['resources']
    row = {
        'mode': name, 'producer_status_not_used_as_verdict': result['status'],
        'operator_result_sha256': sha(op / 'result.json'),
        'signal': result['signal'], 'signal_at_unix': result['signal_at_unix'],
        'outer_exit_code': result['outer_exit_code'],
        'owned_receipt_matches_journal_process_start': all(receipt[k] == started[k] for k in ['pid', 'pgid', 'token', 'identity', 'argv']),
        'recorded_leader_birth_matches': leader['started'] == receipt['identity']['started'],
        'recorded_leader_pid_pgid_matches': leader['pid'] == receipt['identity']['pid'] == receipt['pid'] and leader['pgid'] == receipt['identity']['pgid'] == receipt['pgid'],
        'recorded_leader_command_sha_matches': hashlib.sha256(receipt['identity']['command'].encode()).hexdigest() == leader['command_sha256'],
        'random_token_in_recorded_leader_command': receipt['token'] in receipt['identity']['command'],
        'owned_group_before': result['group_before'],
        'live_xcodebuild_in_exact_group_before': any(x['executable'] == 'xcodebuild' and x['pgid'] == receipt['pgid'] and not x['state'].startswith('Z') for x in result['group_before']),
        'xctest_started_in_pre_interrupt_log': b"Test Case '-[ObserverTests.ObserverTests testObserve]' started." in first,
        'image_attachment_ack_in_pre_interrupt_log': b'Added attachment named' in first and b'.png' in first,
        'pre_interrupt_log_sha256': sha(op / 'pre-interrupt-test.log'),
        'pre_interrupt_log_bytes': len(first), 'retained_log_bytes': len(retained),
        'entire_original_prefix_retained': retained.startswith(first),
        'producer_in_flight_image_decoded': result['in_flight_image_decoded'],
        'actual_exported_png_files': [str(p.relative_to(raw)) for p in raw.rglob('*.png')],
        'native_exported_test_count': manifest['native_test_count'],
        'native_manifest_error': manifest['error'], 'native_manifest_status': manifest['status'],
        'cycle_absent': not (raw / 'cycle.json').exists(),
        'after_outer_exit_group': result['after_outer_exit_group'],
        'after_recovery_group': result['after_recovery_group'],
        'exact_device_uuid': uuid,
        'owned_device_name_matches_owner_prefix': result['device_before']['name'].startswith('NativeUI-' + resources['owner']['token'][:12] + '-'),
        'create_stdout_digest_matches_exact_uuid': bool(creates) and creates[0]['stdout_sha256'] == creation_digest,
        'shutdown_succeeded_exact_uuid': bool(command_success(trace, 'shutdown', uuid)),
        'delete_succeeded_exact_uuid': bool(command_success(trace, 'delete', uuid)),
        'post_query_exit': result['device_after']['exit_code'],
        'post_query_exact_target_rows': result['device_after']['target_rows'],
        'post_query_device_data_exists': result['device_after']['data_path_exists'],
        'signal_to_post_device_sample_seconds': result['device_after']['at_unix'] - result['signal_at_unix'],
        'original_10_second_retirement_bound_met_at_sample': result['device_after']['at_unix'] - result['signal_at_unix'] < 10,
        'final_resource_cleanup_errors': resources['cleanup_errors'],
        'remaining_devices': resources['remaining_devices'], 'remaining_directories': resources['remaining_directories'],
        'protected_counter_hashes_before_after_and_archive_match': result['source_hashes_before'] == result['source_hashes_after'] == source_map,
        'no_exported_frame_or_full_os_tree_credit': True,
        'scope': 'Recorded actual XCTest interruption, exact journal-owned process group and self-created device retirement only. Empty recorded after-samples do not measure escaped daemons, unrelated sessions or borrowed devices. native_test_count=0 is incomplete interrupted export, not a completed successful test or a zero-test acceptance.',
    }
    if name == 'term':
        row['service_error'] = load(raw / 'service-error.json')
        row['final_resources_match_operator'] = resources == load(raw / 'resources.json')
    else:
        row['reconcile_argv'] = result['reconcile_argv']
        row['reconcile_exit_code'] = result['reconcile_exit_code']
        row['reconcile_resources_match_operator'] = resources == load(op / 'reconcile/resources.json')
        row['reconcile_journal_empty'] = not load(op / 'reconcile/resource-journal.json')['devices'] and not load(op / 'reconcile/resource-journal.json')['directories']
        row['original_same_leader_present_after_SIGKILL'] = any(x['pid'] == leader['pid'] and x['started'] == leader['started'] and x['pgid'] == leader['pgid'] and x['command_sha256'] == leader['command_sha256'] for x in result['after_outer_exit_group'])
    interrupts.append(row)
save('interrupt-audit.json', {'rows': interrupts, 'scope': 'No SDK, process inspection, signal, or device action was executed by this reviewer; original logged field relationships and retained artifact bytes were recomputed.'})

leases = []
for row in load(BASE / 'operators/ios-device-lease-qualification.json')['rows']:
    prefix = 'normal' if row['case'] == 'normal_quota' else 'exception'
    receipt = load(EVIDENCE / (prefix + '-lease-receipt/resources.json'))
    trace = events(EVIDENCE / (prefix + '-lease/events.jsonl'))
    before = row['during']['target_rows'][0]
    facts = {
        'case': row['case'], 'device_uuid': row['udid'],
        'producer_status_not_used_as_verdict': row['status'],
        'receipt_matches_operator_copy': receipt == row['resources'],
        'before_exact_uuid_and_owner_name': before['udid'] == row['udid'] and before['name'].startswith('NativeUI-' + row['owner']['token'][:12] + '-'),
        'actual_device_state': before['state'],
        'before_query_exit': row['during']['exit_code'],
        'before_device_data_exists': row['during']['device_data_exists'],
        'after_query_exit': row['after']['exit_code'],
        'after_exact_target_rows': row['after']['target_rows'],
        'after_device_data_exists': row['after']['device_data_exists'],
        'cleanup_errors': receipt['cleanup_errors'],
        'remaining_devices': receipt['remaining_devices'], 'remaining_directories': receipt['remaining_directories'],
        'context_primary_error': receipt['primary_error'],
        'delete_exact_uuid_exit_zero': bool(command_success(trace, 'delete', row['udid'])),
        'scope': 'Actual CoreSimulator acquisition of one fresh self-owned initially-shutdown device, API quota or context-exception retirement. No real SDK command, borrowed-device protection, initial-off existing-device restoration or interrupt trial in these two API cases.',
    }
    if prefix == 'normal':
        facts['second_acquisition_error'] = row['second_acquisition_rejected']
        facts['quota_rejection_preserves_first_target'] = row['during']['target_rows'] == row['after_rejection']['target_rows'] and row['after_rejection']['device_data_exists']
    leases.append(facts)
save('device-lease-audit.json', {'rows': leases})

meter = BASE / 'operators/ios-v12.6-positive-meter.jsonl'
samples = events(meter)
spec = load(BASE / 'operators/ios-v12.6-positive-meter-spec.json')
summary = load(BASE / 'operators/ios-v12.6-positive-meter.summary.json')
peaks = {name: max(row['groups'][name]['allocated_bytes'] for row in samples) for name in spec['groups']}
total_peak = max(row['total_allocated_bytes'] for row in samples)
save('meter-audit.json', {
    'spec_sha256_matches_recorded': sha(BASE / 'operators/ios-v12.6-positive-meter-spec.json') == summary['spec_sha256'],
    'actual_sample_count': len(samples), 'summary_sample_count_matches': len(samples) == summary['sample_count'],
    'recomputed_group_peaks': peaks, 'group_peaks_match_summary': peaks == summary['observed_peak_allocated_bytes'],
    'recomputed_total_peak': total_peak, 'total_peak_matches_summary': total_peak == summary['observed_total_peak_allocated_bytes'],
    'minimum_recorded_free_bytes': min(row['free_bytes'] for row in samples),
    'budget_exceeded_in_any_sample': any(row['budget_exceeded'] for row in samples),
    'every_sample_within_32GiB_and_5GiB_free': all(row['total_allocated_bytes'] <= spec['max_total_allocated_bytes'] and row['free_bytes'] >= spec['min_free_bytes'] for row in samples),
    'configured_sample_seconds': spec['sample_seconds'],
    'maximum_observed_start_interval_seconds': max(b['started_at_unix'] - a['started_at_unix'] for a, b in zip(samples, samples[1:])),
    'scope': 'Recorded sampled allocated-byte observations only, not exact transient peaks, APFS physical/clone-shared usage, global SDK resources or RAM.'})
print(json.dumps({'interrupt_modes': [r['mode'] for r in interrupts],
 'log_prefixes_retained': [r['entire_original_prefix_retained'] for r in interrupts],
 'interruption_group_after_empty': [r['after_recovery_group'] == [] for r in interrupts],
 'ten_second_retirement_bound': [r['original_10_second_retirement_bound_met_at_sample'] for r in interrupts],
 'lease_cases': [r['case'] for r in leases], 'meter_total_peak': total_peak}, indent=2))
