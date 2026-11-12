#!/usr/bin/env python3
"""Finite immutable post-repair audit; no current component fingerprint or SDK."""
import collections
import hashlib
import json
import os
from pathlib import Path
import sys

ADD = Path(__file__).resolve().parent
OUT = ADD.parent
R = OUT.parents[1]
P = R / 'cache/qualification/repair/evidence-candidate-v13.9-scope2'
W = R / 'qualification/repair-worker-v13.9/ios-neutral-20261110T150920Z'
FORBIDDEN = [R / 'cache/qualification/repair/workspace/alerttoast/Sources', R / 'cache/qualification/repair/workspace/reply/Reply/app/src/main']
READS = {}
CHECKS = []


def veto(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp', 'os.fork', 'os.exec', 'os.kill', 'os.killpg'}:
        raise RuntimeError('No SDK/process operations in the receipt addendum')
    if event == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).resolve()
        if any(path == root or path.is_relative_to(root) for root in FORBIDDEN):
            raise RuntimeError('Current repair component source is excluded; immutable maps/archive only')
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        writing = any(c in str(args[1] or '') for c in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing and not path.is_relative_to(ADD): raise RuntimeError('Addendum writes only its new subdirectory')


sys.addaudithook(veto)


def data(p):
    p = Path(p).resolve()
    raw = p.read_bytes()
    if not p.is_relative_to(ADD): READS[str(p)] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    return raw


def load(p): return json.loads(data(p))
def sha(p): return hashlib.sha256(data(p)).hexdigest()
def check(name, good, refs, note=''):
    CHECKS.append({'id': name, 'status': 'P' if good else 'F', 'evidence': [str(p) for p in refs], 'note': note})
def save(name, value): (ADD / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


seal = load(OUT / 'SEAL.json')
check('main-seal-and-all25-members-unchanged', sha(OUT / 'SEAL.json') == '9d27104fe80fc5f85d6d88c6180aea235a90367efb73a9a5bdf21bfccfe57eb0' and all(sha(OUT / row['path']) == row['sha256'] for row in seal['files']), [OUT / 'SEAL.json'])
rr = load(OUT / 'POST-REPAIR-REPLAY-RESULTS.json')
check('post-repair-replay-had-no-process-or-write-veto-attempts', not rr['blocked_process_or_write_attempts'] and rr['reviewer_SDK_calls'] == rr['reviewer_native_calls'] == 0, [OUT / 'POST-REPAIR-REPLAY-RESULTS.json'])
READS.update(rr['readset'])
d1 = P / 'D1-ios-after-measured-patch'
final = P / 'F2-ios-after-repair'
android = P / 'R0-android-after-ios-patch'
origin = P / 'C0-ios'
origin_and = P / 'C0-android'
cycle = load(d1 / 'cycle.json')
receipt = load(d1 / 'capture/result.json')
old_receipt = load(origin / 'capture/result.json')
new_map, new_after = load(d1 / 'capture/source-before.json'), load(d1 / 'capture/source-after.json')
old_map = load(origin / 'capture/source-before.json')
completion_ref = cycle['repair_completion']
completion = load(completion_ref['path'])
task = load(origin / 'repair-task.json')
task_sha = sha(origin / 'repair-task.json')
replay = load(OUT / 'post-repair-replay-D1-ios.json')
replay_android = load(OUT / 'post-repair-replay-retained-C0-android.json')
changed = [name for name in sorted(set(old_map) | set(new_map)) if old_map.get(name) != new_map.get(name)]
check('original-task-and-measured-completion-binding', task_sha == '35d31b7bbc476a5feaa3622676bb0fcb3db35bce84f84f008b995207e6dfee39' and sha(completion_ref['path']) == completion_ref['sha256'] and completion['task'] == {'path': str(origin / 'repair-task.json'), 'sha256': task_sha} and completion['capture'] == task['capture'] and completion['context_sha256'] == task['context_sha256'] and completion['explicit_worker_completion'] is True and completion['status'] == 'patched_needs_native_retest', [origin / 'repair-task.json', completion_ref['path'], d1 / 'cycle.json'])
check('exact-one-file-measured-patch-and-immutable-maps', changed == completion['measured_changed_files'] == ['0/AlertToast/NativeQualificationProbe.swift'] and completion['source_after_map'] == new_map == new_after and completion['source_before_sha256'] == old_receipt['source_sha256'] and completion['source_after_sha256'] == receipt['source_sha256'] and receipt['source_unchanged'] is True and receipt['inputs_unchanged'] is True and receipt['tool_sources_unchanged'] is True and new_map[changed[0]] == '90f68fa0652a9287d3ced24100db7aa344b68f0e12afed1b76ed0fc37064c974', [origin / 'capture/source-before.json', d1 / 'capture/source-before.json', d1 / 'capture/source-after.json', completion_ref['path']], 'No current repair component is read/fingerprinted; these are original stored maps')
check('fresh-affected-code-native104-replay', cycle['native_executed'] is True and cycle['capture_reused'] is False and cycle['capture_sha256'] == sha(d1 / 'capture/result.json') == replay['packet_sha256'] == '4070ad676e2fdeb2f16293fc41f90c58881c7450d204539fe8c7b1f63ff24ac8' and replay['native_counts'] == {'passed': 104, 'failed': 0, 'unassessed': 0} and replay['native_tests'] == 1 and replay['coverage']['satisfied'] is True and replay['environment']['status'] == 'P', [d1 / 'cycle.json', d1 / 'capture/result.json', OUT / 'post-repair-replay-D1-ios.json'])
bad = [rel for rel, digest in receipt['packet_files'].items() if sha(d1 / 'capture' / rel) != digest]
check('new-native-packet-all-member-digests', not bad, [d1 / 'capture/result.json'], str(len(receipt['packet_files'])) + ' members; mismatch=' + repr(bad))
prepared = load(d1 / 'capture/coverage-domain-prepared.json')
binding = load(d1 / 'capture/native/coverage-domain-binding.json')
manifest = load(d1 / 'capture/native/manifest.json')
log = data(d1 / 'capture/native/compiled-build.log').decode()
check('actual-patched-production-and-same-compiled-host-bytes', binding['component_sha256'] == sha(d1 / 'capture/native/coverage-domain-component.swift') == new_map[changed[0]] and binding['compiled_build_log_sha256'] == sha(d1 / 'capture/native/compiled-build.log') and any(line.startswith('SwiftCompile ') and prepared['component']['path'] in line for line in log.splitlines()) and sha(d1 / 'capture/native/compiled-project/ObserverApp.swift') == 'cfffc6a72eedff2dde17978a838b0d2897bb8386b5a369d866f39c3ace4ae5e2' and sha(d1 / 'capture/native/compiled-project/ObserverTests.swift') == '33281971ff84df7eb4fee11b39721ff50f13458eec1da5be6ba9aacbec7b0d0c' and sha(d1 / 'capture/native/compiled-project/Bridge.swift') == prepared['bridge']['sha256'], [d1 / 'capture/native/coverage-domain-binding.json', d1 / 'capture/native/compiled-build.log', d1 / 'capture/native/compiled-project/ObserverApp.swift', d1 / 'capture/native/compiled-project/ObserverTests.swift'])
ns = load(d1 / 'capture/native/native-summary.json')
check('new-actual-native-test-and-reset', ns['passedTests'] == ns['totalTestCount'] == 1 and ns['failedTests'] == ns['skippedTests'] == 0 and manifest['test_exit_code'] == 0 and manifest['fixture_reset']['app_data_absent_before_test'] is True and manifest['fixture_reset']['after_uninstall'] == [] and 'Executed 1 test, with 0 failures' in data(d1 / 'capture/native/test.log').decode(), [d1 / 'capture/native/native-summary.json', d1 / 'capture/native/test.log', d1 / 'capture/native/manifest.json'])
worker = load(W / 'audit.json')
bind_attempt = load(W / 'bind-source-review-attempt1.json')
failed_attempt = load(W / 'complete-native-repair-attempt1.json')
success_attempt = load(W / 'complete-native-repair-attempt2.json')
check('worker-reported-source-change-and-task-consistent', worker['task_sha256'] == task_sha and worker['after_probe_sha256'] == new_map[changed[0]] and len(worker['changed_source_files']) == 1 and bind_attempt['returncode'] == 0 and success_attempt['returncode'] == 0 and json.loads(success_attempt['stdout']) == completion, [W / 'audit.json', W / 'bind-source-review-attempt1.json', W / 'complete-native-repair-attempt2.json'], 'Worker readset/blinding is recorded self-report, not an attestation of absence of unlogged prior knowledge; no worker was contacted')
check('six-cited-original-PNG-identities', len(worker['images_viewed']) == 6 and all(image['path'] in old_receipt['image_hashes'] and sha(origin / 'capture/native' / image['path']) == old_receipt['image_hashes'][image['path']] for image in worker['images_viewed']), [W / 'audit.json', origin / 'capture/result.json'], 'Image-view records are preserved; native verdict is independently reconstructed from original pixels/hierarchy')
check('first-worker-completion-failure-retained', failed_attempt['returncode'] == 1 and 'simctl' in failed_attempt['stderr'] and 'list' in failed_attempt['stderr'] and 'runtimes' in failed_attempt['stderr'] and 'CalledProcessError' in failed_attempt['stderr'], [W / 'complete-native-repair-attempt1.json'], 'Actual failed identity-query attempt precedes successful completion; not omitted or counted as a native UI pass')
check('worker-literal-no-SDK-wording', not ('No SDK invocation' in worker['limits'] and 'subprocess.run' in failed_attempt['stderr']), [W / 'audit.json', W / 'complete-native-repair-attempt1.json'], 'Retained terminology F: worker itself did not launch a UI collection, but completion tool attempted a real SDK identity query. Same distinction as main C01 finding; no native judgment regrade.')
stage_records = {}
for name, directory in [('D1-ios-after-measured-patch', d1), ('F2-ios-after-repair', final), ('R0-android-after-ios-patch', android)]:
    c = load(directory / 'cycle.json')
    driver_path = P / (name + '-driver.json')
    driver = load(driver_path)
    record = Path(driver['argv'][driver['argv'].index('--record') + 1])
    request, result = load(record / 'request.json'), load(record / 'result.json')
    data(record / 'command.log')
    resource = load(directory / 'resources.json')
    events = [json.loads(line) for line in data(directory / 'resource-events.jsonl').decode().splitlines()]
    events = [row for row in events if result['started_at_unix'] <= row['at_unix'] <= result['finished_at_unix']]
    save('raw-' + name + '-resource-events.json', events)
    check(name + '/original-envelope-and-source-stability', driver['exit_code'] == 0 and result['exit_code'] == result['wrapper_exit_code'] == 0 and result['error'] is None and result['source_unchanged'] is True and result['source_before'] == result['source_after'] and result['argv'] == request['argv'] and result['config_sha256'] == request['config_sha256'], [driver_path, record / 'request.json', record / 'result.json'])
    check(name + '/resource-receipt-hash', sha(directory / 'resources.json') == c['resources_sha256'] and resource['cleanup_errors'] == [] and resource['primary_error'] is None, [directory / 'cycle.json', directory / 'resources.json'])
    stage_records[name] = {'cycle': c, 'resources': resource, 'request': request, 'result': result, 'managed_native_commands': [row['argv'] for row in events if row['kind'] == 'process_started'], 'sdk_lifecycle_commands': [row['argv'] for row in events if row['kind'] == 'simctl_command']}

f = stage_records['F2-ios-after-repair']['cycle']
resource = stage_records['F2-ios-after-repair']['resources']
proof = f['capture_reuse']
check('final-exact-D1-full-adoption-within-original-validity', f['status'] == 'accepted' and f['native_executed'] is False and f['capture_reused'] is True and f['capture_result'] == str(d1 / 'capture/result.json') and f['capture_sha256'] == replay['packet_sha256'] and proof['eligible'] is True and proof['context_sha256'] == receipt['capture_context_sha256'] and 0 <= proof['age_seconds'] <= proof['approved_policy']['max_age_seconds'] <= 3600 and not stage_records['F2-ios-after-repair']['managed_native_commands'], [final / 'cycle.json', d1 / 'capture/result.json'])
check('final-three-required-duties-and-source-actual', len(f['evidence_responsibility']['rows']) == 3 and all(row['status'] == 'passed' for row in f['evidence_responsibility']['rows']) and f['evidence_responsibility'] == replay['responsibility'] and not f['source_tasks'] and not f['domain_tasks'], [final / 'cycle.json', OUT / 'post-repair-replay-D1-ios.json'])
check('post-repair-final-owned-resource-retirement', resource['final'] is True and resource['pool']['disposition'] == 'retired' and resource['remaining_devices'] == resource['remaining_directories'] == resource['cleanup_errors'] == [] and any(argv[:3] == ['xcrun', 'simctl', 'delete'] for argv in stage_records['F2-ios-after-repair']['sdk_lifecycle_commands']), [final / 'resources.json', final / 'resource-events.jsonl'])
andreuse = stage_records['R0-android-after-ios-patch']
and_before = load(android / 'before-evaluated.json')
and_original = load(origin_and / 'capture/automatic.json')
platform_record = load(P / 'ANDROID-PLATFORM-REUSE.json')
check('unchanged-Android-original4F-and-no-new-UI', andreuse['cycle']['status'] == 'awaiting_source_repair' and andreuse['cycle']['native_executed'] is False and not andreuse['managed_native_commands'] and and_before['assertions'] == and_original['assertions'] and and_before['counts'] == replay_android['native_counts'] == {'passed': 100, 'failed': 4, 'unassessed': 0} and replay_android['packet_sha256'] == platform_record['original_packet_sha256'] == sha(origin_and / 'capture/result.json'), [android / 'cycle.json', android / 'before-evaluated.json', origin_and / 'capture/automatic.json', OUT / 'post-repair-replay-retained-C0-android.json'])
and_map = load(origin_and / 'capture/source-before.json')
outer_after = andreuse['result']['source_after']
check('recorded-platform-source-separation', {k: v for k, v in outer_after.items() if k.startswith('1/')} == and_map and {k: v for k, v in outer_after.items() if k.startswith('0/')} == new_map and platform_record['ios_source_changed_to_sha256'] == new_map[changed[0]] and andreuse['cycle']['source_tasks'][0]['status'] == 'unassessed', [android / 'cycle.json', P / 'ANDROID-PLATFORM-REUSE.json'], 'Original envelope maps only; no current source fingerprint. Android remains unresolved and is not delivered.')
summary = load(P / 'IOS-REPAIR-RESULT.json')
check('root-postrepair-summary-agrees-with-originals', summary['passed'] is True and summary['original_task_sha256'] == task_sha and summary['final_capture_sha256'] == replay['packet_sha256'] and summary['final_native_counts'] == replay['native_counts'] and summary['final_native_executed'] is False and summary['final_capture_reused'] is True and summary['resources_closed'] is True, [P / 'IOS-REPAIR-RESULT.json'])
drift = []
for name, record in sorted(READS.items()):
    if hashlib.sha256(Path(name).read_bytes()).hexdigest() != record['sha256']: drift.append(name)
check('all-additive-inputs-and-main-seal-unchanged', not drift and sha(OUT / 'SEAL.json') == '9d27104fe80fc5f85d6d88c6180aea235a90367efb73a9a5bdf21bfccfe57eb0', [], repr(drift))
save('DETAILS.json', {'completion': completion, 'measured_changed_files': changed, 'worker_record': worker, 'failed_worker_completion_attempt': failed_attempt, 'successful_worker_completion_attempt': success_attempt, 'stage_records': stage_records, 'root_summaries': [summary, platform_record]})
save('CHECKS.json', {'checks': CHECKS, 'counts': dict(collections.Counter(row['status'] for row in CHECKS)), 'scope': 'Immutable post-repair neutral receipt addendum; no current repair source fingerprint, SDK, performance, business or broad blinding attestation'})
save('READSET.json', {'files': READS, 'changed_inputs': drift, 'current_repair_source_fingerprinted': False, 'reviewer_SDK_calls': 0, 'reviewer_native_calls': 0})
print(json.dumps({'counts': dict(collections.Counter(row['status'] for row in CHECKS)), 'failed_checks': [row for row in CHECKS if row['status'] == 'F'], 'readset_files': len(READS)}, indent=2))
