#!/usr/bin/env python3
"""Bounded, ps-free artifact audit. No SDK, subprocess or current repair source reads."""
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
R = OUT.parents[1]
E = R / 'cache/qualification/evidence-candidate-v13.9'
I = R / 'cache/qualification/interruption-evidence-candidate-v13.9'
REPAIR = R / 'cache/qualification/repair/evidence-candidate-v13.9-scope2'
SKILL = R / 'candidate-v13.9'
FORBIDDEN = [R / 'cache/qualification/repair/workspace/alerttoast/Sources',
             R / 'cache/qualification/repair/workspace/reply/Reply/app/src/main']
READSET = {}
CHECKS = []
DETAILS = {}


def veto(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp',
                 'os.fork', 'os.exec', 'os.kill', 'os.killpg'}:
        raise RuntimeError('Read-only artifact review forbids process/SDK operations')
    if event == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
        p = Path(os.fsdecode(args[0])).resolve()
        if any(p == f or p.is_relative_to(f) for f in FORBIDDEN):
            raise RuntimeError('Current repair component source is outside the immutable audit readset')
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        writing = any(c in str(args[1] or '') for c in 'wax+') or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing and not p.is_relative_to(OUT):
            raise RuntimeError('Artifact audit writes only its new review directory')


sys.addaudithook(veto)


def data(path):
    p = Path(path).resolve()
    raw = p.read_bytes()
    if not p.is_relative_to(OUT):
        READSET[str(p)] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    return raw


def sha(path):
    return hashlib.sha256(data(path)).hexdigest()


def load(path):
    return json.loads(data(path))


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def check(identity, passed, evidence, note=''):
    CHECKS.append({'id': identity, 'status': 'P' if passed else 'F',
                   'evidence': [str(p) for p in evidence], 'note': note})


def unknown(identity, evidence, note):
    CHECKS.append({'id': identity, 'status': 'U', 'evidence': [str(p) for p in evidence], 'note': note})


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n')


before = load(OUT / 'BEFORE.json')
for name, digest in before['inputs'].items():
    # BEFORE inputs are immutable, explicitly named records, not open workspace trees.
    p = Path(name)
    expected = digest.get('sha256') if isinstance(digest, dict) else digest
    check('original-pin/' + p.name + '/' + hashlib.sha256(str(p).encode()).hexdigest()[:8], sha(p) == expected, [p])
freeze_path = R / 'CANDIDATE-FREEZE-10.json'
freeze = load(freeze_path)
check('frozen-candidate-manifest', sha(freeze_path) == '6dac704edfb15491e59648ab0259f465469f81ed0f7b61d7cedf0e91e47140cf', [freeze_path])
tree = {str(p.relative_to(SKILL)): sha(p) for p in sorted(SKILL.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
check('frozen-candidate-exact-84-file-tree', tree == freeze['files'] == before['frozen_candidate_files'] and len(tree) == 84, [freeze_path])
for directory, expected in {
    'admission-review': '6140422631cba5044cdb106c4e1d406c433d608ef38b4fc1b35524c87ec2bef0',
    'provider-review': 'cf06e358a011e941cefd0216939e2077f6b3c4979043930c0bcbdd6327d45f8f',
    'operator-review-2': 'b9907e5324ad3ce0703328e0ab46f3077c0be58aee3211a03da6e6f8879ac708',
    'operator-review-3': 'a8d4eab648271defc64ad4a693b72ed5bf38b260e66aa25ec833f3af1bb1a497',
    'operator-review-4': 'c6a7d768374f7d5ce7243c0fbc0071a2c68248cc4cc1d62d9470757694b30297',
    'operator-review-5': 'f0fbc9439f84ac6fe0da770c6756c4588c066df9436a7ccd77c5b17c1911cf7e',
    'review-10': '986a1d3fa8e098a092108d2a2ca024cc12c0d944dbe7d743e209c58e669326e1',
}.items():
    p = R / 'qualification' / directory / 'SEAL.json'
    check('prior-seal-anchor/' + directory, sha(p) == expected, [p], 'Seal anchor only; prior outcomes not re-reviewed')

for rel in ['qualification/spec/PROTOCOL.md', 'qualification/spec/AMENDMENT-1.md',
            'candidate-v13.9/scripts/capture_validity.py', 'candidate-v13.9/scripts/feedback_loop.py',
            'candidate-v13.9/scripts/evidence_responsibility.py', 'candidate-v13.9/scripts/source_identity.py',
            'candidate-v13.9/scripts/execution_plan.py', 'pool_sdk_interruption.py']:
    data(R / rel)

replays = load(OUT / 'REPLAY-RESULTS.json')
check('readonly-replay-vetoes', not replays['blocked_process_or_write_attempts'] and replays['reviewer_SDK_calls'] == 0 and replays['reviewer_native_calls'] == 0,
      [OUT / 'REPLAY-RESULTS.json'])
READSET.update(replays['readset'])
domain_dir = R / 'qualification/spec/lazy-coverage/encoding-domain'
domain_seal = load(domain_dir / 'SEAL.json')
approval = load(domain_dir / 'DOMAIN-APPROVAL.json')
check('independent-domain-sealed-bytes', all(sha(domain_dir / row['path']) == row['sha256'] for row in domain_seal['files']) and canonical(approval) == domain_seal['domain_approval_canonical_sha256'] == '76a1234411828a2185cade516be5ae6188f084cbc23ca23d8bdc8b0e40fc5b91',
      [domain_dir / 'SEAL.json', domain_dir / 'DOMAIN-APPROVAL.json'])
profiles_dir = R / 'cache/qualification/profiles-v3'
profile_admission = load(profiles_dir / 'ADMISSION.json')
check('profiles-v3-three-actual-config-pins', all(sha(profiles_dir / name) == profile_admission['configs'][name] for name in ['ios-cold.json', 'ios-warm.json', 'android.json']) and sha(profile_admission['previous']) == profile_admission['previous_sha256'], [profiles_dir / 'ADMISSION.json'])
check('profiles-v3-admission-self-entry', sha(profiles_dir / 'ADMISSION.json') == profile_admission['configs']['ADMISSION.json'], [profiles_dir / 'ADMISSION.json'],
      'Ancillary metadata discrepancy: ADMISSION.json self-entry is the SHA of an empty file. Three actual config pins and prior admission SHA match; this self-entry supplies no integrity proof and is not used to alter native judgments.')


def packet(stage, directory, repair=False):
    c = directory / 'capture'
    receipt = load(c / 'result.json')
    bad = []
    for name, digest in receipt['packet_files'].items():
        p = (c / name).resolve()
        if not p.is_relative_to(c.resolve()) or not p.is_file() or sha(p) != digest:
            bad.append(name)
    check(stage + '/original-packet-member-hashes', not bad, [c / 'result.json'], str(len(receipt['packet_files'])) + ' members; mismatches=' + str(bad))
    check(stage + '/frozen-tool-identity', bool(receipt['tool_files']) and all(tree.get(k) == v for k, v in receipt['tool_files'].items()), [c / 'result.json', freeze_path])
    beforemap = load(c / 'source-before.json')
    aftermap = load(c / 'source-after.json')
    check(stage + '/immutable-source-before-after', beforemap == aftermap and receipt['source_unchanged'] is True and receipt['inputs_unchanged'] is True and receipt['tool_sources_unchanged'] is True,
          [c / 'source-before.json', c / 'source-after.json', c / 'result.json'])
    if not repair:
        actual = {}
        for i in receipt['source_model']['indices']:
            root = Path(receipt['source_roots'][i])
            for p in sorted(root.rglob('*')):
                if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc':
                    actual[str(i) + '/' + str(p.relative_to(root))] = sha(p)
        check(stage + '/current-normal-complete-source-namespace', actual == beforemap, [c / 'source-before.json', c / 'source-model.json'], 'Normal roots only; repair source is never read')
    auto = load(c / 'automatic.json')
    cov = load(c / 'execution-coverage.json')
    obs = load(c / 'native/observation.json')
    manifest = load(c / 'native/manifest.json')
    env = load(c / 'environment-check.json')
    expected_counts = {'passed': 100, 'failed': 4, 'unassessed': 0} if repair else {'passed': 104, 'failed': 0, 'unassessed': 0}
    ids = [r['id'] for r in auto['assertions']]
    check(stage + '/exact-native-104-denominator', len(ids) == len(set(ids)) == 104 and auto['counts'] == expected_counts == receipt['automatic_counts'], [c / 'automatic.json', c / 'result.json'])
    expected_states = ['start', 'after-primary', 'after-replacement', 'replacement-full', 'after-last']
    check(stage + '/five-state-mandatory-coverage', list(auto['states']) == expected_states and cov['satisfied'] is True and not cov['missing_states'] and [s['state_id'] for s in cov['required_states']] == expected_states,
          [c / 'automatic.json', c / 'execution-coverage.json'])
    check(stage + '/original-native-execution-and-environment', manifest['native_test_count'] == 1 and receipt['native_exit_code'] == 0 and receipt['status'] == 'verified_capture' and receipt['scope'] == 'full' and env['status'] == 'P',
          [c / 'result.json', c / 'native/manifest.json', c / 'environment-check.json'])
    summary = {'packet_sha256': sha(c / 'result.json'), 'packet_members': len(receipt['packet_files']),
               'source_file_count': len(beforemap), 'source_sha256': receipt['source_sha256'],
               'capture_context_sha256': receipt['capture_context_sha256'],
               'counts': auto['counts'], 'state_coverage': [], 'native_test_count': manifest['native_test_count'],
               'fixture_reset': manifest['fixture_reset'], 'steps': [], 'images': len(receipt['image_hashes'])}
    for state in cov['required_states']:
        proof = state.get('coverage_proof', {})
        admission = proof.get('domain_admission', {})
        summary['state_coverage'].append({'state_id': state['state_id'], 'satisfied': state['satisfied'],
            'full_content_required': state.get('complete'), 'required_target_count': len(state.get('targets', [])),
            'proof_strategy': proof.get('proof_strategy'), 'links': len(proof.get('links', [])),
            'domain_admission': admission, 'reason': state['reason']})
    for step in obs['steps']:
        dispatch = step.get('dispatch', {})
        summary['steps'].append({'state_id': step.get('state_id', step.get('action', {}).get('state_id')),
            'type': step.get('action', {}).get('type', step.get('type')), 'outcome': step.get('outcome'),
            'dispatch_method': dispatch.get('method'), 'dispatch_succeeded': dispatch.get('succeeded'),
            'binding_before': dispatch.get('binding_before'), 'binding_after': step.get('binding_after'),
            'callback_delta': step.get('callback_delta')})
    steps = obs['steps']
    for index, event in [(1, 'probe.primary'), (4, 'probe.last')]:
        s = steps[index]
        delta = s.get('callback_delta', [])
        check(stage + '/single-callback/' + event, len(delta) == 1 and (delta[0].get('event') if isinstance(delta[0], dict) else delta[0]) == event and s['dispatch']['succeeded'] is True,
              [c / 'native/observation.json'])
    update = steps[2]
    prev = update['dispatch']['binding_before']
    following = update['binding_after']
    check(stage + '/caller-update-same-session-no-callback', update['dispatch']['succeeded'] is True and update['callback_delta'] == [] and prev['fixture_index'] == 0 and following['fixture_index'] == 1 and prev['instance'] == following['instance'] and prev['event_revision'] == following['event_revision'] and prev['input_sha256'] != following['input_sha256'],
          [c / 'native/observation.json'])
    if manifest.get('build_cache') is not None:
        # Immutable copied project + raw original compile log, not a tool-looking copy alone.
        binding = load(c / 'native/coverage-domain-binding.json')
        prepared = load(c / 'coverage-domain-prepared.json')
        compiled_log = data(c / 'native/compiled-build.log').decode()
        bridgepath = c / 'native/compiled-project/Bridge.swift'
        check(stage + '/compiled-host-exact-pins', sha(c / 'native/compiled-project/ObserverApp.swift') == tree['assets/ios-observer/ObserverApp.swift'] and sha(c / 'native/compiled-project/ObserverTests.swift') == tree['assets/ios-observer/ObserverTests.swift'] and sha(bridgepath) == prepared['bridge']['sha256'],
              [c / 'native/compiled-project/ObserverApp.swift', c / 'native/compiled-project/ObserverTests.swift', bridgepath])
        pbx = data(c / 'native/compiled-project/Observer.xcodeproj/project.pbxproj').decode()
        package = str(Path(prepared['component']['path']).parents[2])
        check(stage + '/compiled-project-imported-production-product', 'XCLocalSwiftPackageReference' in pbx and 'relativePath = "' + package + '"' in pbx and 'productName = "AlertToast"' in pbx and 'import AlertToast' in data(bridgepath).decode() and 'NativeQualificationProbe(' in data(bridgepath).decode(),
              [c / 'native/compiled-project/Observer.xcodeproj/project.pbxproj', bridgepath])
        component_path = prepared['component']['path']
        check(stage + '/actual-production-compile-action', binding['status'] == 'bound_actual_compiled_source' and binding['component_sha256'] == prepared['component']['sha256'] == sha(c / 'native/coverage-domain-component.swift') and binding['compiled_build_log_sha256'] == sha(c / 'native/compiled-build.log') and any(component_path in line and line.startswith('SwiftCompile ') for line in compiled_log.splitlines()) and all(any('/project/' + name in line and line.startswith('SwiftCompile ') for line in compiled_log.splitlines()) for name in ['Bridge.swift', 'ObserverApp.swift', 'ObserverTests.swift']),
              [c / 'native/coverage-domain-binding.json', c / 'native/compiled-build.log', c / 'native/coverage-domain-component.swift'])
        summary['compiled'] = {'binding': binding, 'cache': manifest['build_cache'],
            'build_command': manifest.get('build_command'), 'build_exit_code': manifest.get('build_exit_code'),
            'test_command': manifest['test_command'], 'test_exit_code': manifest['test_exit_code'],
            'compile_log_sha256': sha(c / 'native/compiled-build.log')}
        ns = load(c / 'native/native-summary.json')
        testlog = data(c / 'native/test.log').decode()
        check(stage + '/raw-xctest-count', ns['totalTestCount'] == ns['passedTests'] == 1 and ns['failedTests'] == ns['skippedTests'] == 0 and manifest['test_exit_code'] == 0 and 'Executed 1 test, with 0 failures' in testlog,
              [c / 'native/native-summary.json', c / 'native/test.log'])
        summary['native_summary'] = ns
        summary['original_runtime'] = obs['original_runtime']
        terminal = [{ 'snapshot': s.get('index'), 'state_id': s.get('state_id'), 'boundary': s['bottom_boundary'],
                    'binding_after_capture': s.get('binding_after_capture') }
                    for s in obs['snapshots'] if s.get('bottom_boundary', {}).get('queried')]
        summary['executed_terminal_boundaries'] = terminal
        check(stage + '/executed-terminal-hittability-receipts', len(terminal) == 2 and all(t['boundary']['match_count'] == 1 and t['boundary']['hittable'] is True and t['boundary']['method'] == 'XCUIElement.isHittable' for t in terminal),
              [c / 'native/observation.json'], 'Source-only provider receipt is now paired with actual original executed guard receipts; raster consumer independently replayed for normal packets')
        summary['collector_provisional_sweeps'] = [{k: s.get(k) for k in ['state_id', 'complete', 'stable_height', 'stable_binding', 'top_reached', 'bottom_reached']} for s in obs['state_captures']]
    else:
        junit = ET.fromstring(data(c / 'native/junit.xml'))
        log = data(c / 'native/test.log').decode()
        check(stage + '/raw-junit-and-gradle-count', junit.attrib.get('tests') == '1' and junit.attrib.get('failures') == '0' and junit.attrib.get('errors') == '0' and junit.attrib.get('skipped') == '0' and manifest['exit_code'] == 0 and '> Task :app:testDebugUnitTest' in log and 'BUILD SUCCESSFUL' in log,
              [c / 'native/junit.xml', c / 'native/test.log'])
        summary['command'] = manifest['command']
        summary['junit'] = junit.attrib
        summary['gradle_main_compile_action'] = [l for l in log.splitlines() if ':app:compileDebugKotlin' in l]
        unknown(stage + '/android-per-file-main-compiler-provenance', [c / 'native/test.log', c / 'native/manifest.json'],
                'Raw log reports compileDebugKotlin UP-TO-DATE; source hashes/module ownership and actual main component behavior are supported, but no per-file compiler dependency trace/binary attestation is retained here')
    if not repair:
        replay = load(OUT / ('replay-' + stage + '.json'))
        check(stage + '/independent-normal-packet-replay', replay['passed'] is True and replay['packet_sha256'] == summary['packet_sha256'] and replay['native_counts'] == expected_counts and replay['native_tests'] == 1,
              [OUT / ('replay-' + stage + '.json')])
        summary['reconstructed_source_responsibility'] = replay['responsibility']
    return summary, receipt, auto, beforemap


normal = {}
for stage in ['C0-ios', 'C07-ios', 'C0-android']:
    normal[stage], _, _, _ = packet(stage, E / stage)
check('force-fresh-same-device-distinct-app-session',
      normal['C0-ios']['original_runtime']['instance'] != normal['C07-ios']['original_runtime']['instance'] and
      normal['C0-ios']['original_runtime']['pid'] != normal['C07-ios']['original_runtime']['pid'] and
      normal['C0-ios']['original_runtime']['input_sha256'] == normal['C07-ios']['original_runtime']['input_sha256'] and
      normal['C0-ios']['fixture_reset']['simulator'] == normal['C07-ios']['fixture_reset']['simulator'] and
      all(normal[s]['original_runtime']['fixture_index'] == normal[s]['original_runtime']['event_revision'] == 0 and normal[s]['fixture_reset']['app_data_absent_before_test'] is True and normal[s]['fixture_reset']['after_uninstall'] == [] for s in ['C0-ios', 'C07-ios']),
      [E / 'C0-ios/capture/native/manifest.json', E / 'C07-ios/capture/native/manifest.json'])
check('force-fresh-cached-compile-new-test', normal['C0-ios']['compiled']['cache']['hit'] is False and normal['C07-ios']['compiled']['cache']['hit'] is True and normal['C0-ios']['compiled']['cache']['signature'] == normal['C07-ios']['compiled']['cache']['signature'] and normal['C0-ios']['compiled']['compile_log_sha256'] == normal['C07-ios']['compiled']['compile_log_sha256'],
      [E / 'C0-ios/capture/native/manifest.json', E / 'C07-ios/capture/native/manifest.json'], 'Warm compiled artifact reuse does not count as a second compilation; both actual XCTest invocations are retained')
DETAILS['normal'] = normal

stages = {}
for stage in ['C0-ios', 'C07-ios', 'C0-android', 'R0-ios', 'R0-android', 'F2-ios', 'F2-android']:
    d = E / stage
    cycle = load(d / 'cycle.json')
    driver = load(E / (stage + '-driver.json'))
    record = R / 'operators/commands' / ('candidate-v13.9-' + stage)
    request, result = load(record / 'request.json'), load(record / 'result.json')
    commandlog = data(record / 'command.log').decode()
    check(stage + '/outer-command-source-and-supervision', driver['exit_code'] == 0 and result['exit_code'] == result['wrapper_exit_code'] == 0 and result['error'] is None and result['source_unchanged'] is True and result['source_before'] == result['source_after'] and result['argv'] == request['argv'] and result['config_sha256'] == request['config_sha256'],
          [E / (stage + '-driver.json'), record / 'request.json', record / 'result.json', record / 'command.log'])
    resources = load(d / 'resources.json')
    check(stage + '/resource-receipt-hash-and-cleanup', sha(d / 'resources.json') == cycle['resources_sha256'] and resources['cleanup_errors'] == [] and resources['primary_error'] is None, [d / 'cycle.json', d / 'resources.json'])
    events = [json.loads(l) for l in data(d / 'resource-events.jsonl').decode().splitlines()]
    # This file is a cumulative ownership journal. Extract only the current envelope window.
    lo, hi = result['started_at_unix'], result['finished_at_unix']
    current = [e for e in events if lo <= e['at_unix'] <= hi]
    save('raw-' + stage + '-resource-events.json', current)
    stages[stage] = {'status': cycle['status'], 'native_executed': cycle['native_executed'],
        'capture_result': cycle.get('capture_result'), 'capture_sha256': cycle.get('capture_sha256'),
        'capture_reused': cycle.get('capture_reused'), 'capture_reuse': cycle.get('capture_reuse'),
        'trace': cycle['trace'], 'duties': [{k: row[k] for k in ['id', 'priority', 'owner', 'method', 'status', 'actual', 'expected', 'unit']} for row in cycle['evidence_responsibility']['rows']],
        'resources': {k: resources[k] for k in ['cleanup_errors', 'remaining_directories', 'remaining_devices', 'final', 'pool', 'borrowed_build_paths']},
        'current_window_sdk_commands': [e['argv'] for e in current if e['kind'] == 'simctl_command'],
        'current_window_native_processes': [e['argv'] for e in current if e['kind'] == 'process_started'],
        'request': request, 'result': result, 'driver': driver}
    if stage.startswith(('R0', 'F2')):
        check(stage + '/no-new-collection-dispatch', cycle['native_executed'] is False and not stages[stage]['current_window_native_processes'] and 'reconstruct_original_evidence' in cycle['trace'],
              [d / 'cycle.json', record / 'result.json', d / 'resource-events.jsonl'])
    if stage.startswith('F2'):
        original = 'C07-ios' if stage.endswith('ios') else 'C0-android'
        proof = cycle['capture_reuse']
        check(stage + '/eligible-original-full-adoption', cycle['status'] == 'accepted' and cycle['capture_reused'] is True and Path(cycle['capture_result']) == (E / original / 'capture/result.json') and cycle['capture_sha256'] == normal[original]['packet_sha256'] and proof['eligible'] is True and proof['original_capture']['sha256'] == normal[original]['packet_sha256'] and proof['context_sha256'] == normal[original]['capture_context_sha256'] and 0 <= proof['age_seconds'] <= proof['approved_policy']['max_age_seconds'] <= 3600,
              [d / 'cycle.json', E / original / 'capture/result.json'])
        check(stage + '/all-three-required-responsibilities', len(cycle['evidence_responsibility']['rows']) == 3 and all(r['priority'] == 'must' and r['status'] == 'passed' for r in cycle['evidence_responsibility']['rows']) and not cycle['source_tasks'] and not cycle['domain_tasks'],
              [d / 'cycle.json'], 'Native-derived duties add no assertion credit; source duty is separately bound actual-only source truth')
        check(stage + '/original-time-final-retirement', resources['final'] is True and resources['remaining_devices'] == resources['remaining_directories'] == resources['cleanup_errors'] == [] and resources['pool']['disposition'] == 'retired',
              [d / 'resources.json'])
DETAILS['stages'] = stages

# Inspect only frozen source here: validity inventory is not a new UI collection.
check('C01-literal-zero-SDK-invocations', False, [R / 'qualification/spec/PROTOCOL.md', R / 'qualification/spec/AMENDMENT-1.md', SKILL / 'scripts/capture_validity.py', SKILL / 'scripts/feedback_loop.py', E / 'R0-ios/cycle.json'],
        'No new native capture/build/test is supported. Literal zero SDK invocation is not: current iOS validity context calls xcrun simctl list runtimes; this inventory subprocess is outside the resource-manager command journal. Original C01 literal claim fails; bounded no-new-collection result remains supported, with no regrading of old metadata.')
unknown('present-time-capture-eligibility', [E / 'F2-ios/cycle.json', E / 'F2-android/cycle.json'],
        'Eligibility is verified at original F2 time only. This audit does not refresh the validity clock or inventory and cannot extend a <=3600s validity window.')
unknown('advisory-mounted-child-instance-relation', [domain_dir / 'DOMAIN-APPROVAL.json'],
        'Original source host app/session identity is supported; mounted child-instance continuity remains advisory U, outside mandatory104. No full child identity/OS lifecycle claim is inferred.')

interruption = {}
admission = load(I / 'ADMISSION.json')
check('interruption-script-original-pin', sha(R / 'pool_sdk_interruption.py') == sha(OUT / 'pinned-pool_sdk_interruption.py') == admission['script_sha256'], [I / 'ADMISSION.json', R / 'pool_sdk_interruption.py'])
all_result = load(I / 'RESULT.json')
for phase in ['after-create', 'during-sdk']:
    d = I / phase
    ready, beforekill, result = load(d / 'owned-ready.json'), load(d / 'BEFORE-KILL.json'), load(d / 'RESULT.json')
    resource = load(d / 'recovery/resources.json')
    journal = load(d / 'recovery/resource-journal.json')
    events = [json.loads(l) for l in data(d / 'recovery/resource-events.jsonl').decode().splitlines()]
    start = max(i for i, row in enumerate(events) if row['kind'] == 'lease_acquired' and row.get('pid') == ready['pid'])
    events = events[start:]
    save('raw-interruption-' + phase + '-resource-events.json', events)
    data(d / 'owner.log')
    if phase == 'during-sdk': data(d / 'bootstatus.log')
    device = ready['device']
    original_config = Path(beforekill['argv'][beforekill['argv'].index('--config') + 1])
    check('interruption/' + phase + '/original-config-and-owner-root', sha(original_config) == admission['config_sha256'] and resource['owner'] == ready['resource_identity'] and resource['root'] == str(R / 'cache/qualification/resources/ios') and journal['token'] == ready['resource_identity']['token'] and not journal['devices'] and not journal['directories'],
          [I / 'ADMISSION.json', original_config, d / 'owned-ready.json', d / 'recovery/resources.json', d / 'recovery/resource-journal.json'])
    check('interruption/' + phase + '/original-owner-boundary', beforekill['ready'] == ready and beforekill['argv'][beforekill['argv'].index('--nonce') + 1] == ready['nonce'] and beforekill['inventory']['exit_code'] == 0 and len(beforekill['inventory']['target_rows']) == 1 and beforekill['inventory']['target_rows'][0]['udid'] == device and beforekill['inventory']['device_data_exists'] is True,
          [d / 'owned-ready.json', d / 'BEFORE-KILL.json'])
    check('interruption/' + phase + '/executed-owned-delete-and-empty-after', result['owner_exit'] == -9 and result['passed'] is True and result['after']['exit_code'] == 0 and result['after']['target_rows'] == [] and result['after']['device_data_exists'] is False and result['group_after'] == [] and resource['remaining_devices'] == resource['remaining_directories'] == resource['cleanup_errors'] == [] and result['recovery_resources_sha256'] == sha(d / 'recovery/resources.json') and any(e['kind'] == 'simctl_command' and e['argv'] == ['xcrun', 'simctl', 'delete', device] and e['exit_code'] == 0 for e in events) and all(e['argv'][3] == device for e in events if e['kind'] == 'simctl_command' and e['argv'][2] in ['delete', 'shutdown']),
          [d / 'RESULT.json', d / 'recovery/resources.json', d / 'recovery/resource-events.jsonl'])
    if phase == 'during-sdk':
        process = beforekill['process']
        members = beforekill['actual_group_members']
        check('interruption/during-sdk/actual-command-group-birth-token', process['argv'] == ['xcrun', 'simctl', 'bootstatus', device, '-b'] and process['pid'] == process['pgid'] and str(process['token']) in process['identity']['command'] and process['identity']['started'] and any(Path(v['executable']).name == 'simctl' and v['pgid'] == process['pgid'] for v in members) and any(e['kind'] == 'interrupted_process_reconciled' and e['pid'] == process['pid'] for e in events) and not (d / 'sdk-finished.json').exists(),
              [d / 'BEFORE-KILL.json', d / 'recovery/resource-events.jsonl'])
    else:
        check('interruption/after-create/no-fabricated-SDK-child', beforekill['process'] is None and beforekill['actual_group_members'] == [], [d / 'BEFORE-KILL.json'])
    interruption[phase] = {'ready': ready, 'before_kill': beforekill, 'result': result,
                           'recovery_resources': resource, 'relevant_event_count': len(events), 'journal_keys': list(journal)}
check('interruption/no-UI-performance-business-credit', all_result['passed'] is True and all_result['native_ui_tests'] == all_result['performance_samples'] == all_result['business_tasks'] == 0, [I / 'RESULT.json'])
unknown('interruption/raw-whole-inventory-reconstruction', [I / 'after-create/BEFORE-KILL.json', I / 'during-sdk/BEFORE-KILL.json', I / 'RESULT.json'],
        'Controller retains inventory stdout SHA and selected owned target rows, not the complete raw inventory stdout or raw ps stdout. Existing records establish the bounded observed target/group checks; foreign-resource noninterference and present-time global inventory are not independently reconstructed.')
DETAILS['interruption'] = interruption

repair_details = {}
for stage in ['C0-ios', 'C0-android']:
    d = REPAIR / stage
    summary, receipt, auto, sourcemap = packet('repair-' + stage, d, repair=True)
    cycle = load(d / 'cycle.json')
    task = load(d / 'repair-task.json')
    handoff = load(d / 'handoff.json')
    driver_path = REPAIR / (stage + '-driver.json')
    driver = load(driver_path)
    record = Path(driver['argv'][driver['argv'].index('--record') + 1])
    request, result = load(record / 'request.json'), load(record / 'result.json')
    data(record / 'command.log')
    check('repair-' + stage + '/original-outer-command-source-stability', driver['exit_code'] == 0 and result['exit_code'] == result['wrapper_exit_code'] == 0 and result['error'] is None and result['source_unchanged'] is True and result['source_before'] == result['source_after'] and result['argv'] == request['argv'], [driver_path, record / 'request.json', record / 'result.json'])
    failed = [r for r in auto['assertions'] if r['status'] == 'failed']
    check('repair-' + stage + '/original-failure-task-binding', cycle['status'] == 'awaiting_source_repair' and cycle['native_executed'] is True and len(failed) == 4 and task['capture']['sha256'] == sha(d / 'capture/result.json') and task['cycle']['sha256'] == sha(d / 'cycle.json') and task['source_map'] == sourcemap and task['context_sha256'] == receipt['capture_context_sha256'] and task['failed_assertions'] == failed,
          [d / 'cycle.json', d / 'repair-task.json', d / 'handoff.json', d / 'capture/automatic.json'])
    check('repair-' + stage + '/retained-required-source-unknown', len(cycle['evidence_responsibility']['rows']) == 3 and len(task['source_tasks']) == 1 and task['source_tasks'][0]['id'] == 'thin-bridge-decodes-calls' and task['source_tasks'][0]['status'] == 'unassessed', [d / 'cycle.json', d / 'repair-task.json'], '100P/4F/0U is the native denominator only; separate source duty remains U at this handoff')
    expected_task_prefix = '35d31b7' if stage.endswith('ios') else '1c71909'
    check('repair-' + stage + '/task-and-handoff-exact-original-identities', sha(d / 'repair-task.json').startswith(expected_task_prefix) and handoff['next_work'] == 'awaiting_source_repair' and handoff['cycle'] == task['cycle'] and handoff['capture'] == task['capture'] and handoff['context_sha256'] == task['context_sha256'], [d / 'repair-task.json', d / 'handoff.json'])
    repair_details[stage] = {'capture': summary, 'cycle_sha256': sha(d / 'cycle.json'),
        'task_sha256': sha(d / 'repair-task.json'), 'task_context_sha256': task['context_sha256'],
        'failed_assertion_ids': [r['id'] for r in failed], 'task_failed_assertions_exactly_original': task['failed_assertions'] == failed,
        'source_tasks': task['source_tasks'], 'handoff': handoff,
        'scope': 'Immutable pre-repair capture/task only; current repair source never read, worker not contacted, no postpatch or repair-success opinion'}
DETAILS['repair'] = repair_details

# Re-read every pinned review input once at the end, without refreshing any SDK identity.
after = {}
drift = []
for name, record in sorted(READSET.items()):
    p = Path(name)
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    after[name] = {'sha256': h, 'bytes': p.stat().st_size}
    if h != record['sha256']: drift.append(name)
check('audit-inputs-stable-through-readonly-review', not drift, [], str(drift))
save('AUDIT-DETAILS.json', DETAILS)
save('AUDIT-CHECKS.json', {'checks': CHECKS, 'counts': dict(collections.Counter(c['status'] for c in CHECKS)),
     'scope': 'Read-only corroboration of bounded original NATIVE artifacts; no fresh native, speed, arbitrary dependency closure or business result',
     'reviewer_SDK_calls': 0, 'reviewer_process_management_calls': 0})
save('READSET.json', {'files': READSET, 'forbidden_current_repair_source_roots': [str(p) for p in FORBIDDEN]})
save('AFTER.json', {'files': after, 'changed_inputs': drift, 'frozen_candidate_files': tree})
print(json.dumps({'counts': dict(collections.Counter(c['status'] for c in CHECKS)), 'failed_checks': [c for c in CHECKS if c['status'] == 'F'], 'readset_files': len(READSET), 'sdk_calls': 0}, indent=2))
