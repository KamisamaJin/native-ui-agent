#!/usr/bin/env python3
"""One approved business/observation route, with explicitly scoped feedback."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
import design_contract as design
from observation_contract import validate_actions, validate_selector


def compile_execution(plan, lock, lock_sha, fixtures, bridge_sha, *, launch_ref, states=None, strategy='coalesced'):
    platform = plan['design_contract']['platform']
    actions = design.verify_generated(plan, lock, lock_sha, platform)
    if set(launch_ref) != {'source', 'pointer'}:
        raise ValueError('Independently sealed launch-input source required')
    approval = design.pointer(lock['sources'][launch_ref['source']]['document'], launch_ref['pointer'])
    expected_launch = {'fixtures_sha256': design.digest(fixtures), 'bridge_sha256': bridge_sha,
                       'scenario': plan['design_contract']['scenario'], 'platform': platform}
    if approval != expected_launch:
        raise ValueError('Fixture, bridge, scenario or platform differs from independently sealed launch approval')
    all_states = [s['id'] for s in plan['states']]
    selected = all_states if states is None else list(states)
    if not selected or len(selected) != len(set(selected)) or not set(selected) <= set(all_states):
        raise ValueError('Explicit known unique feedback states required')
    if any(s['id'] in selected and s.get('after_action', -1) < 0 for s in plan['states']):
        raise ValueError('Execution manifests require explicit initial checkpoints in the approved route')
    if strategy not in {'legacy', 'coalesced'} or len(bridge_sha) != 64:
        raise ValueError('Known strategy and exact bridge identity required')
    # Parent assertions and expectations never change. A partial capture remains
    # a partial capture; the admission tool will not promote it to a full PR pass.
    required = []
    for state in plan['states']:
        if state['id'] not in selected: continue
        targets = []
        for rule in plan['assertions']:
            if rule['state'] == state['id']:
                for key in ['target', 'reference_target']:
                    target = rule.get(key)
                    if target and target not in targets: validate_selector(target); targets.append(copy.deepcopy(target))
        required.append({'state_id': state['id'], 'coverage': state.get('coverage', 'targets'), 'targets': targets})
    enriched = copy.deepcopy(actions)
    for action in enriched:
        state_id = action.get('state_id')
        entry = next((v for v in required if v['state_id'] == state_id), None)
        if entry:
            targets = list(action.get('after_targets', []))
            if action.get('after_target') and action['after_target'] not in targets: targets.append(action['after_target'])
            if entry['coverage'] == 'targets':
                for target in entry['targets']:
                    if target not in targets: targets.append(copy.deepcopy(target))
            if targets: action['after_targets'] = targets
            action['capture_scope'] = entry['coverage']
        elif set(selected) != set(all_states):
            action['capture_scope'] = 'none'
            action['observe_after'] = False
            action.pop('after_targets', None); action.pop('after_target', None)
        else:
            action['capture_scope'] = 'targets' if action['type'] == 'tap' or action.get('after_targets') or action.get('after_target') else 'none'
        # Observation-only sweeps can be omitted, but every business action and
        # original index remains present for dispatch/callback identity.
        if action['type'] == 'sweep' and not entry: action['type'] = 'checkpoint'
    if set(selected) != set(all_states):
        last = max(s['after_action'] for s in plan['states'] if s['id'] in selected)
        enriched = enriched[:last + 1]
    validate_actions(enriched)
    config = copy.deepcopy(fixtures)
    config['state_capture'] = True
    config['observation_strategy'] = strategy
    config['execution_states'] = copy.deepcopy(required)
    config['execution_state_definitions'] = copy.deepcopy(plan['states'])
    config['execution_scope'] = 'full' if set(selected) == set(all_states) else 'targeted'
    targets = list(config.get('observation_targets', [])) if config['execution_scope'] == 'full' else []
    for entry in required:
        for target in entry['targets']:
            if target not in targets: targets.append(copy.deepcopy(target))
    config['observation_targets'] = targets
    if config['execution_scope'] == 'targeted':
        wanted_ids = {t.get('identifier') for t in targets}
        config['required_identifiers'] = [v for v in config.get('required_identifiers', []) if v in wanted_ids]
    value = {'version': 1, 'platform': platform, 'scope': config['execution_scope'],
             'parent_plan_sha256': design.digest(plan), 'design_lock_sha256': lock_sha, 'launch_ref': copy.deepcopy(launch_ref),
             'fixtures_sha256': design.digest(fixtures), 'bridge_sha256': bridge_sha,
             'selected_states': selected, 'required_coverage': required, 'actions': enriched, 'config': config,
             'parent_action_count': len(actions), 'executed_action_count': len(enriched),
             'scope_limit': 'Full execution retains the business route; targeted execution keeps its original action prefix and indices. Original parent expectations stay fixed; omitted states are unverified.'}
    value['execution_sha256'] = design.digest(value)
    return value


def verify_execution(value, plan, lock, lock_sha, fixtures, bridge_sha):
    # Reconstructs required after-target extensions from the actual approved plan;
    # a caller cannot substitute a sibling base route or drop coverage extensions.
    expected = compile_execution(plan, lock, lock_sha, fixtures, bridge_sha,
                                 launch_ref=value.get('launch_ref', {}), states=value.get('selected_states'), strategy=value.get('config', {}).get('observation_strategy'))
    if expected != value: raise ValueError('Execution manifest differs from independently rebuilt business/observation route')
    return expected


def coverage_receipt(execution, observation):
    from native_checks import bound_state_evidence, resolve
    missing, states = [], []
    for entry in execution['required_coverage']:
        parent = {'id': entry['state_id']}
        # Exact state definitions are carried in config by the CLI/runner caller
        # below; never infer an input epoch from an arbitrary matching label.
        parent = next(s for s in execution['config']['execution_state_definitions'] if s['id'] == entry['state_id'])
        found, complete, reason, _ = bound_state_evidence(observation, parent)
        target_rows = []
        for target in entry['targets']:
            seen = []
            for index, snapshot in found:
                result = resolve(snapshot, target, execution['platform'])
                semantic = result.get('semantic', {})
                if result.get('facts', {}).get('unique') and semantic.get('intersects_viewport'):
                    seen.append(index)
            target_rows.append({'target': target, 'indices': seen, 'observed': bool(seen)})
        good = bool(found) and (complete if entry['coverage'] == 'full_content' else True) and all(v['observed'] for v in target_rows)
        if not good: missing.append(entry['state_id'])
        states.append({'state_id': entry['state_id'], 'complete': complete, 'satisfied': good, 'reason': reason, 'targets': target_rows})
    return {'execution_sha256': execution['execution_sha256'], 'scope': execution['scope'], 'required_states': states,
            'satisfied': not missing, 'missing_states': missing}


def source_fingerprint(roots):
    result = {}
    for index, root in enumerate(roots):
        root = Path(root).resolve()
        if not root.exists(): raise ValueError('Production source root missing')
        paths = [root] if root.is_file() else sorted(p for p in root.rglob('*') if p.is_file())
        for path in paths:
            relative = path.name if root.is_file() else str(path.relative_to(root))
            if '__pycache__' in path.parts or path.suffix == '.pyc': continue
            result[str(index) + '/' + relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not result: raise ValueError('Nonempty actual production source set required')
    return result


def run_execution(value, plan, lock, lock_sha, fixtures, bridge, output, source_roots, native_options, *, policy=None, policy_sha=None):
    bridge = Path(bridge).resolve(); output = Path(output).resolve()
    bridge_sha = hashlib.sha256(bridge.read_bytes()).hexdigest()
    verify_execution(value, plan, lock, lock_sha, fixtures, bridge_sha)
    roots = [Path(p).resolve() for p in source_roots]
    if any(output.is_relative_to(p) for p in roots): raise ValueError('Fresh evidence must be outside production source roots')
    before = source_fingerprint(roots)
    output.mkdir(parents=True, exist_ok=False)
    def save(name, data): (output / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    save('execution.json', value); save('fixtures.json', value['config']); save('actions.json', value['actions'])
    save('parent-plan.json', plan); save('source-before.json', before)
    script = Path(__file__).resolve().parent / (value['platform'] + '_observe.py')
    command = [sys.executable, '-B', str(script), 'run', '--bridge', str(bridge), '--fixtures', str(output / 'fixtures.json'),
               '--actions', str(output / 'actions.json'), '--output', str(output / 'native')]
    allowed = ({'package', 'simulator', 'developer-dir', 'build-cache', 'product', 'sdk'} if value['platform'] == 'ios'
               else {'project', 'java-home', 'android-sdk'})
    if set(native_options) - allowed: raise ValueError('Only explicit platform-native options are accepted')
    for key, item in native_options.items():
        if item is not None: command += ['--' + key, str(item)]
    record = {'version': 1, 'startedAtUnix': time.time(), 'execution_sha256': value['execution_sha256'],
              'source_sha256': design.digest(before), 'source_roots': list(map(str, roots)), 'argv': command,
              'scope': value['scope'], 'input_hashes': {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in ['fixtures.json', 'actions.json']}}
    save('request.json', record)
    with (output / 'native.log').open('w') as stream:
        record['native_exit_code'] = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT,
             env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1')).returncode
    record['nativeFinishedAtUnix'] = time.time()
    after = source_fingerprint(roots); save('source-after.json', after)
    record['source_unchanged'] = before == after and hashlib.sha256(bridge.read_bytes()).hexdigest() == bridge_sha
    record['inputs_unchanged'] = all(hashlib.sha256((output / name).read_bytes()).hexdigest() == h for name, h in record['input_hashes'].items())
    observation_path = output / 'native/observation.json'
    if observation_path.is_file() and record['source_unchanged'] and record['inputs_unchanged']:
        import native_checks
        import review_contract
        observation = design.load(observation_path); obs_sha = hashlib.sha256(observation_path.read_bytes()).hexdigest()
        receipt = coverage_receipt(value, observation); save('execution-coverage.json', receipt)
        record['coverage_satisfied'] = receipt['satisfied']
        manual = None
        if policy is not None:
            catalog = review_contract.catalog(plan, lock, lock_sha, policy, policy_sha, value['platform'])
            submission = {'version': 1, 'catalog_sha256': design.digest(catalog), 'observation_sha256': obs_sha, 'decisions': []}
            manual = review_contract.bind(plan, lock, lock_sha, policy, policy_sha, observation, obs_sha, observation_path.parent, submission, value['platform'])
        report = native_checks.evaluate(plan, observation, value['platform'], manual, observation_path.parent, obs_sha, lock, lock_sha, policy, policy_sha)
        save('automatic.json', report); record['automatic_counts'] = report['counts']
    else: record['coverage_satisfied'] = False
    record['finishedAtUnix'] = time.time(); record['status'] = ('verified_capture' if record['source_unchanged'] and record['inputs_unchanged'] and record['coverage_satisfied'] else 'invalid_or_incomplete_capture')
    record['scope_limit'] = 'A source-bound capture/automatic-check result, not full PR acceptance or independent visual truth.'
    save('result.json', record)
    return record


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run', action='store_true'); p.add_argument('--execution', type=Path)
    for name in ['plan', 'design-lock', 'fixtures', 'output']: p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--design-sha256', required=True); p.add_argument('--bridge', type=Path, required=True)
    p.add_argument('--launch-source', required=True); p.add_argument('--launch-pointer', required=True)
    p.add_argument('--state', action='append'); p.add_argument('--strategy', choices=['legacy', 'coalesced'], default='coalesced')
    p.add_argument('--source-root', type=Path, action='append')
    p.add_argument('--policy', type=Path); p.add_argument('--policy-sha256')
    for name in ['package', 'project', 'simulator', 'developer-dir', 'build-cache', 'product', 'sdk', 'java-home', 'android-sdk']:
        p.add_argument('--' + name)
    a = p.parse_args()
    plan = design.load(a.plan)
    lock = design.load(a.design_lock); fixtures = design.load(a.fixtures)
    value = compile_execution(plan, lock, a.design_sha256, fixtures, hashlib.sha256(a.bridge.read_bytes()).hexdigest(), launch_ref={'source': a.launch_source, 'pointer': a.launch_pointer}, states=a.state, strategy=a.strategy)
    if a.execution:
        supplied = design.load(a.execution)
        if supplied != value: raise ValueError('CLI request differs from exact execution manifest')
    if a.run:
        if not a.source_root: raise ValueError('Actual production source roots required for a native run')
        names = ['package', 'simulator', 'developer-dir', 'build-cache', 'product', 'sdk'] if value['platform'] == 'ios' else ['project', 'java-home', 'android-sdk']
        result = run_execution(value, plan, lock, a.design_sha256, fixtures, a.bridge, a.output, a.source_root,
                               {name: getattr(a, name.replace('-', '_')) for name in names if getattr(a, name.replace('-', '_')) is not None},
                               policy=design.load(a.policy) if a.policy else None, policy_sha=a.policy_sha256)
        print(json.dumps(result, indent=2)); return
    a.output.mkdir(exist_ok=False, parents=True)
    for name, data in [('execution.json', value), ('actions.json', value['actions']), ('fixtures.json', value['config'])]:
        (a.output / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
if __name__ == '__main__': main()
