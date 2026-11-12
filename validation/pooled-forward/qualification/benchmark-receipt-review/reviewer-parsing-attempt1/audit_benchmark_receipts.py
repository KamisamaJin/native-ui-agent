#!/usr/bin/env python3
"""Finite immutable benchmark accounting; no replay, SDK or current source fingerprint."""
import collections
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
R = OUT.parents[1]
G = R / 'qualification/benchmark-gate'
ORDER = [('block-1', 'A'), ('block-1', 'B'), ('block-2', 'B'), ('block-2', 'A')]
STEPS = [('C0-android', 'android'), ('C0-ios', 'ios-cold'), ('R0-android', 'android'), ('R0-ios-cold', 'ios-cold'), ('W1-ios', 'ios-warm'), ('F2-ios-warm', 'ios-warm'), ('F2-android', 'android')]
COMMANDS = [('C0-android', 'android', 'C0'), ('C0-ios', 'ios-cold', 'C0'), ('R0-source-android', 'android', 'R0'), ('R0-android', 'android', 'R0'), ('R0-source-ios-cold', 'ios-cold', 'R0'), ('R0-ios-cold', 'ios-cold', 'R0'), ('W1-ios', 'ios-warm', 'W1'), ('F2-ios-warm', 'ios-warm', 'F2'), ('F2-android', 'android', 'F2')]
READSET, CHECKS = {}, []
ACTUAL_OPERATIONS = []


def veto(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp', 'os.fork', 'os.exec', 'os.kill', 'os.killpg'}:
        ACTUAL_OPERATIONS.append(event)
        raise RuntimeError('Accounting audit forbids SDK/process operations')
    if event == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).resolve()
        if 'business-design' in path.parts or 'business-designs' in path.parts:
            raise RuntimeError('Business design is outside this audit')
        if path.is_relative_to(R / 'cache/benchmark') and 'workspace' in path.relative_to(R / 'cache/benchmark').parts:
            raise RuntimeError('Current application source fingerprint is outside this audit')
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        writing = any(c in str(args[1] or '') for c in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing and not path.is_relative_to(OUT): raise RuntimeError('Writes restricted to this new receipt review')


sys.addaudithook(veto)


def data(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    if not path.is_relative_to(OUT):
        READSET.setdefault(str(path), {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)})
    return raw


def sha(path): return hashlib.sha256(data(path)).hexdigest()
def load(path): return json.loads(data(path))
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
def finite(value, positive=False): return type(value) in [int, float] and math.isfinite(value) and (value > 0 if positive else value >= 0)
def check(name, good, detail): CHECKS.append({'id': name, 'status': 'P' if good else 'F', 'detail': detail})
def save(name, value): (OUT / name).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
def filemap(value): return {k: v if isinstance(v, str) else v['sha256'] for k, v in value.items()}
def duties(cycle): return sorted([{k: row.get(k) for k in ['id', 'priority', 'owner', 'method', 'status', 'expected', 'unit']} for row in cycle['evidence_responsibility']['rows']], key=lambda row: row['id'])
def native_facts(replay): return sorted([{k: value for k, value in row.items() if k != 'reason'} for row in replay['rows']], key=lambda row: row['id'])


admission = load(R / 'BENCHMARK-ADMISSION.json')
gate = load(G / 'RESULT.json')
summary = load(R / 'BENCHMARK-SUMMARY.json')
batch = load(R / 'operators/benchmark-run/RESULT.json')
pins = load(OUT / 'INITIAL-PINS.json')
check('01-original-admission-gate-summary-batch-binding', all(sha(R / p) == v['sha256'] for p, v in pins['inputs'].items()) and gate['admission_sha256'] == batch['admission_sha256'] == sha(R / 'BENCHMARK-ADMISSION.json') and summary['original_gate_sha256'] == sha(G / 'RESULT.json') and gate['passed'] is True and gate['errors'] == [] and batch['failed'] is None, {'admission_sha256': sha(R / 'BENCHMARK-ADMISSION.json'), 'gate_sha256': sha(G / 'RESULT.json')})
check('02-fixed-threshold-order-and-no-adaptive-run-declaration', admission['order'] == [list(x) for x in ORDER] and admission['threshold'] == .20 and admission['required_native_atoms'] == 104 and admission['required_source_must_claims_separate'] == 1 and admission['max_machine_seconds'] == 7200 and admission['no_adaptive_runs'] is True, {'order': ORDER, 'threshold': admission['threshold'], 'collection_clock': admission['collection_clock']})
prereqs_ok = all(sha(R / rel) == h for rel, h in admission['prerequisite_files'].items())
archived_operators = {'driver_sha256': 'neutral_episode.py', 'verifier_sha256': 'verify_benchmark.py', 'envelope_sha256': 'native_envelope.py', 'prepare_neutral_sha256': 'prepare_neutral.py', 'batch_sha256': 'run_benchmark.py'}
operator_ok = all(sha(R / 'qualification/batch-review-2' / ('pinned-' + name)) == admission[key] for key, name in archived_operators.items())
check('03-prerequisite-seal-and-reviewed-operator-pins', prereqs_ok and operator_ok, {'prerequisite_files': len(admission['prerequisite_files']), 'operators': {k: admission[k] for k in archived_operators}, 'scope': 'Named original seals/archived reviewed operators only; no current application source fingerprint'})
freezes = {arm: load(R / admission['arms'][arm]['freeze']) for arm in ['A', 'B']}
check('04-declared-frozen-arm-identities', all(sha(R / admission['arms'][arm]['freeze']) == admission['arms'][arm]['freeze_sha256'] for arm in ['A', 'B']), {'arms': admission['arms'], 'file_counts': {arm: len(freezes[arm]['files']) for arm in ['A', 'B']}, 'scope': 'Frozen inventory manifest identity; original gate performed full-tree rehash/replay. This audit does not newly fingerprint current arm trees.'})
ledger = load(R / 'qualification/COMMON-FOUNDATION-6.json')
base = load(R / 'baseline-seal.json')
basefiles, afiles, bfiles = filemap(base['files']), filemap(freezes['A']['files']), filemap(freezes['B']['files'])
changes = ledger['changes']
actual_changed = {name for name in set(basefiles) | set(afiles) if basefiles.get(name) != afiles.get(name)}
common = ledger['whole_byte_identical_common_files']
adapted = sorted(set(changes) - set(common))
data(R / 'qualification/baseline-common-foundation-6.patch')
foundation_ok = len(changes) == 18 and actual_changed == set(changes) and all(basefiles.get(name) == row['before_sha256'] and afiles.get(name) == row['after_sha256'] for name, row in changes.items()) and len(common) == len(set(common)) == 15 and all(afiles[name] == bfiles[name] for name in common) and adapted == ['scripts/execution_plan.py', 'scripts/feedback_loop.py', 'scripts/ios_observe.py'] and sha(R / 'port_common_6.py') == ledger['port_script_sha256'] == freezes['A']['port_script_sha256'] and freezes['A']['treatment_features_backported'] is False
check('05-common18path-floor-and-control-attribution', foundation_ok, {'control': admission['arms']['A']['skill'], 'base_commit': freezes['A']['base_commit'], 'common_18_paths': sorted(changes), 'whole_byte_identical_15_paths': common, 'adapted_3_paths': adapted, 'ledger_scope': ledger['scope'], 'declared_treatment_only_modules': {name: {'present_A': name in afiles, 'present_B': name in bfiles} for name in ['scripts/source_identity.py', 'scripts/capture_validity.py', 'scripts/workflow_state.py']}, 'limit': 'Confirms original declared bytes/port identity, not a new semantic port audit. Control is v12.6 plus common foundation, not untouched v12.6.'})

production = admission['production_files']
mapped_production = {('0/' + k[len('alerttoast/Sources/'):]) if k.startswith('alerttoast/Sources/') else ('1/' + k[len('reply/Reply/app/src/main/'):]): v for k, v in production.items()}
episodes, replays, cycles, packets = [], {}, {}, {}
flags = collections.defaultdict(list)
command_details, final_details = [], []
for block, arm in ORDER:
    root = R / 'cache/benchmark' / block / arm
    result, entry = load(root / 'result.json'), load(root / 'ADMISSION.json')
    profiles = load(root / 'profiles/ADMISSION.json')
    flags['source'].append(len(production) == len(result['source_after']) == len(entry['source_map']) == len(profiles['production_files']) == 85 and entry['source_map'] == profiles['production_files'] == production and result['source_after'] == mapped_production and result['source_unchanged'] is True)
    flags['entry'].append(entry['arm'] == arm and entry['block'] == block and entry['skill_seal_sha256'] == admission['arms'][arm]['freeze_sha256'] and entry['driver_sha256'] == admission['driver_sha256'] and entry['envelope_sha256'] == admission['envelope_sha256'] and entry['profile_admission_sha256'] == sha(root / 'profiles/ADMISSION.json'))
    flags['profiles'].append(set(profiles['configs']) == {'ios-cold.json', 'ios-warm.json', 'android.json'} and all(sha(root / 'profiles' / name) == value for name, value in profiles['configs'].items()))
    flags['episode_time'].append(result['failed'] is None and result['collection_clock_basis'] == 'clock_gettime(CLOCK_MONOTONIC)' and all(finite(result[key], True) for key in ['clock_start', 'clock_end', 'collection_wall_seconds']) and result['collection_wall_seconds'] == result['clock_end'] - result['clock_start'])
    stage_map = {row['stage']: row for row in result['stages']}
    last = result['clock_start']; stage_ok = list(stage_map) == ['C0', 'R0', 'W1', 'F2']
    for name, expected_count in [('C0', 2), ('R0', 4), ('W1', 1), ('F2', 2)]:
        row = stage_map[name]
        stage_ok = stage_ok and row == load(root / ('stage-' + name + '.json')) and all(finite(row[k], True) for k in ['clock_start', 'clock_end', 'wall_seconds']) and row['wall_seconds'] == row['clock_end'] - row['clock_start'] and row['clock_start'] >= last and row['clock_end'] <= result['clock_end'] and row['new_commands'] == expected_count
        last = row['clock_end']
    flags['stages'].append(stage_ok)
    stage_sum = sum(row['wall_seconds'] for row in result['stages'])
    flags['sums'].append(result['collection_stage_seconds'] == stage_sum and finite(result['operator_and_meter_seconds']) and result['operator_and_meter_seconds'] == result['collection_wall_seconds'] - stage_sum)
    last_command = result['clock_start']; command_sum = 0; command_ok = True
    for name, profile, stage in COMMANDS:
        directory = root / 'commands' / (block + '-' + arm + '-' + name)
        request, cmd = load(directory / 'request.json'), load(directory / 'result.json')
        driver = load(root / 'commands' / (name + '.driver.json'))
        start, end = cmd['clock_start'], cmd['clock_end']
        command_ok = command_ok and cmd['clock_basis'] == 'clock_gettime(CLOCK_MONOTONIC)' and all(finite(cmd[k], True) for k in ['clock_start', 'clock_end', 'wall_seconds']) and cmd['wall_seconds'] == end - start and stage_map[stage]['clock_start'] <= start < end <= stage_map[stage]['clock_end'] and start >= last_command and cmd['exit_code'] == cmd['wrapper_exit_code'] == driver['exit_code'] == 0 and cmd['error'] is None and cmd['argv'] == request['argv'] and cmd['config_sha256'] == request['config_sha256'] == sha(root / 'profiles' / (profile + '.json')) and cmd['source_before'] == cmd['source_after'] == mapped_production and cmd['source_unchanged'] is True and cmd['envelope_sha256'] == admission['envelope_sha256']
        last_command = end; command_sum += cmd['wall_seconds']
    flags['commands'].append(command_ok and command_sum <= stage_sum)
    command_details.append({'block': block, 'arm': arm, 'commands': len(COMMANDS), 'raw_command_wall_sum': command_sum, 'stage_wall_sum': stage_sum, 'operator_and_meter_seconds': result['operator_and_meter_seconds']})
    previous = {}
    collections_count = 0
    for step, profile in STEPS:
        directory = root / 'evidence' / step
        cycle = load(directory / 'cycle.json'); cycles[(block, arm, step)] = cycle
        collections_count += int(cycle['native_executed'])
        platform = 'android' if profile == 'android' else 'ios'
        if cycle.get('capture_result'): previous[platform] = Path(cycle['capture_result'])
        packet_path = previous[platform]
        replay_path = G / (block + '-' + arm + '-' + step + '.json')
        replay, driver = load(replay_path), load(replay_path.with_suffix('.driver.json'))
        replays[(block, arm, step)] = replay
        flags['replay'].append(driver['exit_code'] == 0 and replay['passed'] is True and replay['packet'] == str(packet_path) and replay['packet_sha256'] == sha(packet_path) and replay['source_map'] == mapped_production and replay['native_tests'] == 1 and replay['source_must_claim_ids'] == ['thin-bridge-decodes-calls'] and replay['environment']['status'] == 'P' and replay['coverage']['satisfied'] is True and len(replay['coverage']['required_states']) == 5 and set(driver['argv'][driver['argv'].index('--skill') + 1:driver['argv'].index('--skill') + 2]) == {str(R / admission['arms'][arm]['skill'])})
        if str(packet_path) not in packets:
            receipt = load(packet_path)
            automatic = load(packet_path.parent / 'automatic.json')
            manifest = load(packet_path.parent / 'native/manifest.json')
            before_source, after_source = load(packet_path.parent / 'source-before.json'), load(packet_path.parent / 'source-after.json')
            automatic_bound = digest(automatic) == receipt['automatic_sha256']
            if receipt.get('packet_files'):
                automatic_bound = automatic_bound and sha(packet_path.parent / 'automatic.json') == receipt['packet_files']['automatic.json']
            flags['packets'].append(receipt['status'] == 'verified_capture' and receipt['scope'] == 'full' and receipt['source_unchanged'] is True and receipt['inputs_unchanged'] is True and receipt['tool_sources_unchanged'] is True and receipt['native_exit_code'] == 0 and receipt['automatic_counts'] == automatic['counts'] == {'passed': 104, 'failed': 0, 'unassessed': 0} and automatic_bound and before_source == after_source == mapped_production and manifest['native_test_count'] == 1 and all(filemap(freezes[arm]['files']).get(rel) == h for rel, h in receipt['tool_files'].items()))
            packets[str(packet_path)] = {'block': block, 'arm': arm, 'packet_sha256': sha(packet_path), 'native_counts': automatic['counts'], 'native_test_count': manifest['native_test_count'], 'automatic': automatic, 'manifest': manifest, 'packet': receipt}
        original = packets[str(packet_path)]['automatic']
        statuses = {row['id']: (row['state'], row['status']) for row in original['assertions']}
        flags['native'].append(len(replay['rows']) == len({row['id'] for row in replay['rows']}) == len(statuses) == 104 and {row['id']: (row['state'], row['status']) for row in replay['rows']} == statuses and replay['native_counts'] == {'passed': 104, 'failed': 0, 'unassessed': 0})
        if step.startswith('F2-'):
            resource = load(directory / 'resources.json')
            flags['finals'].append(cycle['status'] == 'accepted' and len(cycle['evidence_responsibility']['rows']) == 3 and cycle['evidence_responsibility'] == replay['responsibility'] and all(row['status'] == 'passed' for row in cycle['evidence_responsibility']['rows']) and resource['final'] is True and resource['remaining_devices'] == resource['remaining_directories'] == resource['cleanup_errors'] == [] and sha(directory / 'resources.json') == cycle['resources_sha256'])
            flags['adoption'].append(cycle['native_executed'] is (arm == 'A') and (arm == 'A' or (cycle['capture_reused'] is True and cycle['capture_sha256'] == replay['packet_sha256'])))
            final_details.append({'block': block, 'arm': arm, 'step': step, 'accepted': cycle['status'], 'native_executed': cycle['native_executed'], 'capture_reused': cycle.get('capture_reused'), 'packet_sha256': replay['packet_sha256'], 'resources_sha256': cycle['resources_sha256'], 'pool': resource.get('pool'), 'remaining_devices': resource['remaining_devices'], 'remaining_directories': resource['remaining_directories'], 'cleanup_errors': resource['cleanup_errors']})
    meter = load(root / 'meter.summary.json')
    flags['meter'].append(meter['sampling_error'] is None and meter['budget_exceeded'] is False and finite(meter['observed_total_peak_allocated_bytes']) and meter['sample_count'] > 0)
    episodes.append({'block': block, 'arm': arm, 'clock_start': result['clock_start'], 'clock_end': result['clock_end'], 'started_at_unix': result['collection_started_at_unix'], 'finished_at_unix': result['finished_at_unix'], 'collection_wall_seconds': result['collection_wall_seconds'], 'stages': result['stages'], 'native_collections': collections_count, 'sampled_peak_allocated_bytes': meter['observed_total_peak_allocated_bytes'], 'meter_scope': meter['scope']})

check('06-same-initial85-and-recorded-complete-source-before-after', all(flags['source']) and all(flags['entry']), {'source_files': 85, 'source_map_sha256': digest(production), 'episodes': len(episodes), 'limit': 'Immutable measured maps/receipts only; no present-time source fingerprint'})
check('07-exact-three-profile-configs-and-original-config-hashes', all(flags['profiles']), {'config_count_per_episode': 3, 'self_hash_entry_present': False})
check('08-four-positive-exact-enclosing-episode-clocks', all(flags['episode_time']), {'episodes': [{k: e[k] for k in ['block', 'arm', 'clock_start', 'clock_end', 'collection_wall_seconds']} for e in episodes]})
check('09-raw-stage-identity-nesting-order-and-2-4-1-2-command-counts', all(flags['stages']), {'stages_per_episode': ['C0', 'R0', 'W1', 'F2'], 'command_counts': [2, 4, 1, 2]})
check('10-stage-sums-and-nonnegative-inclusive-operator-cost', all(flags['sums']), command_details)
check('11-all36-command-clock-source-config-wrapper-bindings', all(flags['commands']), {'command_receipts': 36, 'per_episode': command_details})
nooverlap = all(x['clock_end'] <= y['clock_start'] and x['finished_at_unix'] <= y['started_at_unix'] for x, y in zip(episodes, episodes[1:]))
batch_ok = [(v['block'], v['arm']) for v in batch['episodes']] == ORDER
deadline = None
for ep, row in zip(episodes, batch['episodes']):
    root = R / 'cache/benchmark' / ep['block'] / ep['arm']
    request = load(R / 'operators/benchmark-run' / (ep['block'] + '-' + ep['arm'] + '-request.json'))
    if deadline is None: deadline = request['deadline']
    batch_ok = batch_ok and request['deadline'] == deadline and row['exit_code'] == 0 and row['result_sha256'] == sha(root / 'result.json') and row['collection_wall_seconds'] == ep['collection_wall_seconds'] and request['clock_start'] <= ep['clock_start'] <= ep['clock_end'] <= row['clock_end'] and request['argv'][request['argv'].index('--candidate') + 1] == admission['arms']['B']['skill'] and request['argv'][request['argv'].index('--baseline') + 1] == admission['arms']['A']['skill']
collection_sum = sum(e['collection_wall_seconds'] for e in episodes)
batch_ok = batch_ok and finite(batch['enclosing_wall_seconds'], True) and collection_sum <= batch['enclosing_wall_seconds'] <= admission['max_machine_seconds'] and episodes[-1]['clock_end'] <= deadline
check('12-original-ABBA-order-no-overlap-and-batch-budget', nooverlap and batch_ok, {'batch_enclosing_wall_seconds': batch['enclosing_wall_seconds'], 'summed_collection_wall_seconds': collection_sum, 'batch_outside_collection_seconds': batch['enclosing_wall_seconds'] - collection_sum, 'gate_research_replay_outside_collection': True})
A = sum(e['collection_wall_seconds'] for e in episodes if e['arm'] == 'A')
B = sum(e['collection_wall_seconds'] for e in episodes if e['arm'] == 'B')
reduction = 1 - B / A
blocks = []
for block in ['block-1', 'block-2']:
    values = {e['arm']: e['collection_wall_seconds'] for e in episodes if e['block'] == block}
    blocks.append({'block': block, 'A_seconds': values['A'], 'B_seconds': values['B'], 'reduction': 1 - values['B'] / values['A']})
check('13-independent-formula-and-no-rounding-threshold', A == gate['A_seconds'] == summary['A_seconds'] and B == gate['B_seconds'] == summary['B_seconds'] and reduction == gate['reduction'] == summary['reduction'] and blocks == gate['blocks'] == summary['blocks'] and reduction >= admission['threshold'], {'A_seconds': A, 'B_seconds': B, 'reduction': reduction, 'percentage': reduction * 100, 'blocks': blocks, 'scope': 'Four local ordered episode walls; no statistical/population inference'})
comparisons = []; pair_flags = []; source_flags = []; oracle_flags = []; U_counts = collections.Counter()
for block in ['block-1', 'block-2']:
    for step, _profile in STEPS:
        x, y = replays[(block, 'A', step)], replays[(block, 'B', step)]
        dx, dy = duties(cycles[(block, 'A', step)]), duties(cycles[(block, 'B', step)])
        source_flags.append(dx == dy and len(dx) == 3 and {v['id'] for v in dx} == {'component-native-controls', 'component-native-callbacks', 'thin-bridge-decodes-calls'} and all(v['priority'] == 'must' for v in dx))
        pair_flags.append(native_facts(x) == native_facts(y))
        oracle_flags.append(all(x[key] == y[key] for key in ['design_sha256', 'plan_sha256', 'fixtures_sha256', 'bridge_sha256', 'environment_sha256']))
        source = next(v for v in dx if v['method'] == 'source'); U_counts[source['status']] += 1
        comparisons.append({'block': block, 'step': step, 'A_packet_sha256': x['packet_sha256'], 'B_packet_sha256': y['packet_sha256'], 'native_atoms': 104, 'native_counts_A': x['native_counts'], 'native_counts_B': y['native_counts'], 'native_facts_sha256_A': digest(native_facts(x)), 'native_facts_sha256_B': digest(native_facts(y)), 'original_responsibilities_A': dx, 'original_responsibilities_B': dy, 'same_inputs': oracle_flags[-1]})
check('14-all28-replays-bound-to-original-packets-and-frozen-arms', all(flags['replay']) and len(replays) == 28, {'replay_receipts': len(replays), 'scope': 'Existing original gate replay outputs and driver bindings audited; no new image replay or SDK invocation'})
check('15-all16-unique-original-collection-packet-native-anchors', len(packets) == 16 and all(flags['packets']), {'unique_packet_count': len(packets), 'unique_test_count': sum(v['native_test_count'] for v in packets.values()), 'packets': {path: {k: v for k, v in record.items() if k in ['block', 'arm', 'packet_sha256', 'native_counts', 'native_test_count']} for path, record in packets.items()}})
check('16-fourteen-exact104-native-PFU-and-oracle-comparisons', len(comparisons) == 14 and all(pair_flags) and all(oracle_flags) and all(flags['native']) and all(v['same_mandatory_pfu'] for v in gate['comparisons']), {'comparisons': 14, 'native_atoms_per_comparison': 104, 'native_U_increase': False, 'native_counts_each': {'passed': 104, 'failed': 0, 'unassessed': 0}})
check('17-original-required-source-PFU-separate-and-no-U-increase', all(source_flags) and U_counts == {'unassessed': 4, 'passed': 10} and all(v['same_original_responsibility_pfu'] for v in gate['comparisons']) and summary['source_claim_separate'] == 1 and summary['mandatory_U_increase'] is False, {'source_claims_per_comparison': 1, 'source_status_pair_counts': dict(U_counts), 'native_derived_duties_add_no_duplicate_credit': True, 'C0_source_U_preserved': True})
collections_by_arm = {arm: sum(e['native_collections'] for e in episodes if e['arm'] == arm) for arm in ['A', 'B']}
check('18-native-collection-counts-and-final-adoption-versus-recapture', [e['native_collections'] for e in episodes] == [5, 3, 3, 5] and collections_by_arm == {'A': 10, 'B': 6} and all(flags['adoption']) and [(e['block'], e['arm'], e['native_collections']) for e in gate['episodes']] == [(e['block'], e['arm'], e['native_collections']) for e in episodes], {'per_episode': [e['native_collections'] for e in episodes], 'per_arm': collections_by_arm, 'final_receipts': final_details})
check('19-all8-final-current-duty-and-owned-resource-closure-receipts', all(flags['finals']) and len(final_details) == 8, {'final_receipts': final_details, 'scope': 'Original-time accepted/current-bound full packet/source-duty/owned closure records; no fresh global SDK inventory'})
check('20-sampled-resource-scope-and-ancillary-failures-retained', all(flags['meter']) and len(admission['retained_ancillary_failures']) == 3 and summary['same_native_pfu_comparisons'] == summary['same_original_responsibility_comparisons'] == 14 and summary['native_atoms_per_comparison'] == 104, {'sampled_peak_allocated_bytes': [{'block': e['block'], 'arm': e['arm'], 'bytes': e['sampled_peak_allocated_bytes']} for e in episodes], 'meter_limit': episodes[0]['meter_scope'], 'retained_ancillary_failures': admission['retained_ancillary_failures'], 'known_scope': admission['qualification_scope']})

# Only two selected raw native log pairs are needed as immutable execution anchors;
# all unique manifest/test counts and all original automatic row links were checked above.
anchors = []
for arm in ['A', 'B']:
    for step in ['C0-ios', 'C0-android']:
        replay = replays[('block-1', arm, step)]
        path = Path(replay['packet']).parent / 'native/test.log'
        text = data(path).decode(errors='replace')
        anchors.append({'arm': arm, 'step': step, 'path': str(path), 'sha256': sha(path), 'matching_lines': [line for line in text.splitlines() if 'Executed 1 test, with 0 failures' in line or 'BUILD SUCCESSFUL' in line or ':app:testDebugUnitTest' in line]})
drift = []
for name, record in sorted(READSET.items()):
    if hashlib.sha256(Path(name).read_bytes()).hexdigest() != record['sha256']: drift.append(name)
check('21-audit-readset-stable-and-no-native-or-process-operations', not drift and not ACTUAL_OPERATIONS, {'changed_inputs': drift, 'actual_operation_attempts': ACTUAL_OPERATIONS, 'current_application_source_fingerprinted': False, 'business_design_read': False})
save('CHECKS.json', {'checks': CHECKS, 'counts': dict(collections.Counter(row['status'] for row in CHECKS))})
save('COMPARISONS.json', comparisons)
save('ACCOUNTING.json', {'episodes': episodes, 'A_seconds': A, 'B_seconds': B, 'reduction': reduction, 'blocks': blocks, 'batch_enclosing_wall_seconds': batch['enclosing_wall_seconds'], 'batch_outside_collection_seconds': batch['enclosing_wall_seconds'] - collection_sum, 'command_accounting': command_details, 'selected_native_log_anchors': anchors, 'initial_source_files': 85, 'source_status_pair_counts': dict(U_counts), 'native_collections': collections_by_arm})
save('READSET.json', {'files': READSET, 'changed_inputs': drift, 'SDK_native_process_operations': 0, 'current_application_source_fingerprinted': False, 'business_design_read': False})
save('AFTER.json', {'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'all_inputs_unchanged': not drift, 'files': {name: record for name, record in sorted(READSET.items())}})
print(json.dumps({'counts': dict(collections.Counter(row['status'] for row in CHECKS)), 'failed_checks': [row for row in CHECKS if row['status'] == 'F'], 'readset_files': len(READSET), 'A_seconds': A, 'B_seconds': B, 'reduction': reduction, 'source_status_pairs': dict(U_counts)}, indent=2))
