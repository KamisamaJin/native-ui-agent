"""Prelaunch checks of fixed inputs, using candidate snapshot reconstruction APIs."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT.parent / 'development/candidate-attempt-1'
sys.path.insert(0, str(SNAPSHOT / 'scripts'))
import design_contract as design
import execution_plan
import native_checks
import observation_contract
import requirement_routes
import ios_observe

def load(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def rejected(name, operation):
    try:
        operation()
    except ValueError as error:
        return {'name': name, 'status': 'rejected_as_expected', 'message': str(error)}
    raise AssertionError(name + ': changed input was accepted')

def main():
    approval = load(ROOT / 'APPROVAL.json')
    lock = load(ROOT / 'design/lock.json')
    pre = load(ROOT / 'design/PREIMPLEMENTATION.json')
    assert pre['source_exists'] is False
    original_contract = copy.deepcopy(lock['contract'])
    original_contract['sources'] = []
    original_bytes = (json.dumps(original_contract, indent=2, ensure_ascii=False) + '\n').encode()
    assert hashlib.sha256(original_bytes).hexdigest() == pre['sha256']['design/contract.json']
    for name, expected in pre['sha256'].items():
        if name != 'design/contract.json':
            assert sha(ROOT / name) == expected, name
    routes = load(ROOT / 'design/routes.json')
    bridge_sha = sha(ROOT / 'source/Bridge.swift')
    reports = []
    controls = []
    for case in ['ordinary400', 'narrow280-large']:
        fixtures = load(ROOT / ('inputs/' + case + '.json'))
        ios_observe.validate_offered_width(fixtures['width'])
        assert fixtures['initial']['can_review'] is True and fixtures['updates'][0]['can_review'] is False
        assert len(fixtures['initial']['sections']) == 10
        assert [s['number'] for s in fixtures['initial']['sections']] == list(range(1, 11))
        plan = load(ROOT / ('generated/' + case + '/design/plan.json'))
        assert len(plan['states']) == 4 and all(s['after_action'] >= 0 for s in plan['states'])
        native_checks.validate_plan(plan)
        design.verify_generated(plan, lock, approval['design_lock_sha256'], 'ios')
        coverage = requirement_routes.audit(lock, approval['design_lock_sha256'], plan, routes, approval['routes_sha256'])
        assert coverage['must_route_gaps'] == [] and coverage['unowned_assertions'] == []
        pair = []
        for strategy in ['legacy', 'coalesced']:
            execution = load(ROOT / ('generated/' + case + '/' + strategy + '/execution.json'))
            execution_plan.verify_execution(execution, plan, lock, approval['design_lock_sha256'], fixtures, bridge_sha)
            observation_contract.validate_actions(execution['actions'])
            pair.append(execution)
        a, b = pair
        for field in ['required_coverage', 'actions', 'bridge_sha256', 'fixtures_sha256', 'parent_plan_sha256', 'selected_states', 'scope']:
            assert a[field] == b[field], field
        ac, bc = copy.deepcopy(a['config']), copy.deepcopy(b['config'])
        del ac['observation_strategy']; del bc['observation_strategy']
        assert ac == bc
        event_rows = [{'id': r['id'], 'action_index': r['action_index'], 'expected': r['expected'],
                       'stimulus': r.get('stimulus', 'activation'), 'required_method': r['required_method']}
                      for r in plan['assertions'] if r['kind'] == 'event']
        assert [(r['action_index'], r['stimulus']) for r in event_rows] == [(1, 'activation'), (2, 'caller_update')]
        changed_execution = copy.deepcopy(b)
        changed_execution['required_coverage'][0]['targets'].pop()
        controls.append(rejected(case + ': missing required target', lambda: execution_plan.verify_execution(changed_execution, plan, lock, approval['design_lock_sha256'], fixtures, bridge_sha)))
        changed_fixture = copy.deepcopy(fixtures); changed_fixture['width'] += 1
        controls.append(rejected(case + ': changed approved launch fixture', lambda: execution_plan.compile_execution(plan, lock, approval['design_lock_sha256'], changed_fixture, bridge_sha, launch_ref={'source': 'launch', 'pointer': '/' + case})))
        changed_plan = copy.deepcopy(plan); changed_plan['assertions'][0]['expected'] = 'self-approved replacement'
        controls.append(rejected(case + ': changed expected label', lambda: design.verify_generated(changed_plan, lock, approval['design_lock_sha256'], 'ios')))
        reports.append({'case': case, 'offered_width': fixtures['width'], 'dynamic_type': fixtures['dynamic_type'],
                        'required_assertions': len(plan['assertions']), 'required_state_rule_cells': len(plan['matrix_contract']['cells']),
                        'manual_assertions': sum(r['kind'] == 'manual' for r in plan['assertions']),
                        'event_assertions': event_rows, 'required_coverage': b['required_coverage'],
                        'same_source_inputs_actions_and_required_coverage': True,
                        'must_route_gaps': coverage['must_route_gaps'], 'unowned_assertions': coverage['unowned_assertions']})
    # Pinned host-interface bytes are the only upstream interface inspected.
    repo = ROOT.parents[2]
    host = repo / 'native-ui-agent/assets/ios-observer'
    host_rows = []
    for name in ['ObserverApp.swift', 'ObserverTests.swift', 'CONTRACT.md']:
        actual = sha(host / name); snapshot = sha(SNAPSHOT / 'assets/ios-observer' / name)
        assert actual == snapshot, name
        host_rows.append({'file': name, 'pinned_sha256': actual, 'snapshot_sha256': snapshot, 'same': True})
    save('logs/prelaunch-verification.json', {'version': 1, 'checked_unix': time.time(), 'status': 'passed_python_only',
        'cases': reports, 'negative_controls': controls, 'host_interfaces': host_rows,
        'sdk_execution': False, 'limitations': ['Swift has not been compiled.', 'No native hierarchy, event receipt, viewport, content height, image or visual judgment exists yet.']})
    print(json.dumps({'status': 'passed_python_only', 'cases': len(reports), 'negative_controls': len(controls)}, indent=2))

if __name__ == '__main__':
    main()
