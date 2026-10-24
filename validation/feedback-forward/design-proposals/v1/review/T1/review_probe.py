"""SDK-free, read-only reconstruction of the sealed T1 proposal.

All generated files stay beside this script. No product source is read.
"""
import atexit
import copy
import hashlib
import json
import pathlib
import sys
import time
import traceback
import xml.etree.ElementTree as ET

ROOT = pathlib.Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
OUT = pathlib.Path(__file__).resolve().parent
DESIGN = ROOT / 'validation/feedback-forward/design/T1'
FROZEN = ROOT / 'validation/feedback-forward/candidate-v9'
sys.dont_write_bytecode = True
sys.path.insert(0, str(FROZEN / 'scripts'))
import design_contract as d
import requirement_routes as routes_api
import execution_plan as execution_api
import review_contract as review_api
import native_checks
import acceptance

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def rawsha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

calls = []
atexit.register(lambda: save('api-attempts.json', calls))
def call(name, function, *args, rejected=False, **kwargs):
    start = time.time()
    try:
        value = function(*args, **kwargs)
    except Exception as error:
        calls.append({'api': name, 'startedAtUnix': start, 'finishedAtUnix': time.time(),
                      'outcome': 'expected_rejection' if rejected else 'error',
                      'error': repr(error), 'traceback': traceback.format_exc()})
        if not rejected:
            raise
        return
    calls.append({'api': name, 'startedAtUnix': start, 'finishedAtUnix': time.time(),
                  'outcome': 'unexpected_acceptance' if rejected else 'success'})
    if rejected:
        raise AssertionError('Expected a verifier rejection: ' + name)
    return value

summary = {'version': 1, 'sdk_free': True, 'source_seals': {}, 'reconstructions': [],
           'semantic_route_inventory': [], 'reference_inventory': []}
source_files = {}
for root in [DESIGN, FROZEN]:
    source_files.update({str(p.relative_to(ROOT)): rawsha(p) for p in sorted(root.rglob('*')) if p.is_file()})
request = ROOT / 'validation/feedback-forward/operators/T1-design-review-request.txt'
source_files[str(request.relative_to(ROOT))] = rawsha(request)
save('source-files.json', source_files)

for scope in ['public', 'private']:
    base = DESIGN / scope
    seal = d.load(base / 'SEAL.json')
    actual_files = {str(p.relative_to(base)) for p in base.rglob('*') if p.is_file() and p.name != 'SEAL.json'}
    assert set(seal['files']) == actual_files
    assert all(rawsha(base / name) == digest for name, digest in seal['files'].items())
    approval = d.load(base / 'approval.json')
    lock = d.load(base / 'design-lock.json')
    rebuilt_lock = call(scope + ': design_contract.seal', d.seal, base / 'contract.json', base)
    assert rebuilt_lock == lock
    call(scope + ': design_contract.validate_lock', d.validate_lock, lock, approval['design_lock_sha256'])
    policy = d.load(base / 'policy.json')
    routes = d.load(base / 'routes.json')
    assert d.digest(policy) == approval['policy_sha256']
    assert d.digest(routes) == approval['routes_sha256']
    summary['source_seals'][scope] = {'verified_files': len(actual_files),
                                    'lock_canonical_sha256': d.digest(lock),
                                    'approval_raw_sha256': rawsha(base / 'approval.json')}
    ref = d.load(base / 'reference.json')
    for case in lock['contract']['scenarios']:
        fixtures = d.load(base / 'cases' / case / 'fixtures.json')
        assert ref['cases'][case]['caller'] == fixtures
        models = [fixtures['initial']] + fixtures['updates']
        actions_log = lock['contract']['scenarios'][case]['actions']
        summary['semantic_route_inventory'].append({
            'scope': scope, 'case': case,
            'states': lock['contract']['scenarios'][case]['states'],
            'action_types': [a['type'] for a in actions_log],
            'tap_targets': [a['target'] for a in actions_log if a['type'] == 'tap'],
            'guard_combinations': [[m['sealIntact'], m['coolantReady']] for m in models],
            'acknowledged_hold_checkpoint': False,
            'choice_false_event_source_present': any(':false' in e for state in ref['cases'][case]['states'].values()
                                                      for e in state['choiceEvents']['value']),
            'note_counts': [len(m['notes']) for m in models],
            'profile': {k: fixtures[k] for k in ['width', 'viewportHeight', 'direction', 'theme', 'dynamic_type', 'fontScale']}})
        for platform in ['ios', 'android']:
            prefix = scope + '/' + case + '/' + platform
            stored = base / 'compiled' / case / platform
            actions = d.load(base / 'cases' / case / ('actions.' + platform + '.json'))
            plan, derived_actions = call(prefix + ': design_contract.compile_contract', d.compile_contract,
                                         lock, approval['design_lock_sha256'], case, platform,
                                         d.load(base / 'bindings.json'), actions)
            assert plan == d.load(stored / 'plan.json')
            assert derived_actions == d.load(stored / 'actions.json')
            call(prefix + ': design_contract.verify_generated', d.verify_generated,
                 plan, lock, approval['design_lock_sha256'], platform)
            coverage = call(prefix + ': requirement_routes.audit', routes_api.audit,
                            lock, approval['design_lock_sha256'], plan, routes, approval['routes_sha256'])
            assert coverage == d.load(stored / 'coverage.json')
            catalog = call(prefix + ': review_contract.catalog', review_api.catalog,
                           plan, lock, approval['design_lock_sha256'], policy, approval['policy_sha256'], platform)
            # The frozen CLI adds this self-excluding catalog digest to its file.
            stored_catalog = d.load(stored / 'review-catalog.json')
            assert stored_catalog == dict(catalog, catalog_sha256=d.digest(catalog))
            bridge = base / ('Bridge.swift' if platform == 'ios' else 'ObserverBridge.kt')
            execution = call(prefix + ': execution_plan.compile_execution', execution_api.compile_execution,
                             plan, lock, approval['design_lock_sha256'], fixtures, rawsha(bridge),
                             launch_ref={'source': 'reference', 'pointer': '/launch/' + case + '/' + platform})
            assert execution == d.load(stored / 'execution.json')
            call(prefix + ': execution_plan.verify_execution', execution_api.verify_execution,
                 execution, plan, lock, approval['design_lock_sha256'], fixtures, rawsha(bridge))
            assert execution['actions'] == d.load(stored / 'execution-inputs/actions.json')
            assert execution['config'] == d.load(stored / 'execution-inputs/fixtures.json')
            environment = d.load(base / 'cases' / case / ('environment.' + platform + '.json'))
            assert d.digest(environment) == approval['environment_sha256'][case][platform]
            empty_env = call(prefix + ': acceptance.environment schema preflight', acceptance.environment, {}, environment, platform)
            assert empty_env['status'] == 'U'  # No invented native evidence.
            event_assertions = [a for a in plan['assertions'] if a['kind'] == 'event']
            assert [(a['requirement_id'], a['action_index']) for a in event_assertions] == [
                ('choice-receipt', 2), ('request-receipt', 4), ('replacement-quiet', 6)]
            assert event_assertions[-1]['stimulus'] == 'caller_update'
            assert all(s['coverage'] == 'full_content' for s in plan['states'])
            summary['reconstructions'].append({'scope': scope, 'case': case, 'platform': platform,
                'all_reconstructions_equal_sealed': True, 'assertions': len(plan['assertions']),
                'matrix_cells': len(plan['matrix_contract']['cells']), 'catalog_atoms': len(catalog['rows']),
                'must_route_gaps_against_index': coverage['must_route_gaps'],
                'unowned_assertions': coverage['unowned_assertions'], 'event_assertions': event_assertions,
                'environment_schema_valid_no_native_claim': True})
            # Generic source-binding negatives, never product defects or revised expectations.
            changed = copy.deepcopy(plan)
            changed['assertions'][0]['expected'] += ' tampered'
            call(prefix + ': rejects changed plan expectation', d.verify_generated,
                 changed, lock, approval['design_lock_sha256'], platform, rejected=True)
            changed = copy.deepcopy(execution)
            changed['actions'][6]['type'] = 'checkpoint'
            call(prefix + ': rejects dropped caller-update action', execution_api.verify_execution,
                 changed, plan, lock, approval['design_lock_sha256'], fixtures, rawsha(bridge), rejected=True)
    for svg in sorted(base.rglob('*.svg')):
        tree = ET.fromstring(svg.read_text())
        texts = tree.findall('{http://www.w3.org/2000/svg}text')
        summary['reference_inventory'].append({'path': str(svg.relative_to(DESIGN)),
            'width': tree.attrib['width'], 'height': tree.attrib['height'], 'text_nodes': len(texts),
            'description': tree.find('{http://www.w3.org/2000/svg}desc').text,
            'title': tree.find('{http://www.w3.org/2000/svg}title').text})

assert (DESIGN / 'public/API.md').read_bytes() == (DESIGN / 'private/API.md').read_bytes()
assert (DESIGN / 'public/Bridge.swift').read_bytes() == (DESIGN / 'private/Bridge.swift').read_bytes()
assert (DESIGN / 'public/ObserverBridge.kt').read_bytes() == (DESIGN / 'private/ObserverBridge.kt').read_bytes()
summary['same_api_and_bridge_in_hidden_case'] = True

for platform in ['ios', 'android']:
    before = {'instance': 'synthetic-verifier-probe', 'fixture_index': 0,
              'input_sha256': 'a' * 64, 'event_revision': 0}
    if platform == 'ios': before['pid'] = 12345
    after = dict(before, fixture_index=1, input_sha256='b' * 64)
    step = {'outcome': 'updated', 'binding_after': after, 'callback_delta': [],
            'dispatch': {'attempted': True, 'succeeded': True, 'method': 'caller_fixture_update',
                         'stimulus': 'caller_update', 'binding_before': before, 'event_start': 0, 'event_end': 0}}
    good = call(platform + ': native_checks.callback_verdict successful update gate', native_checks.callback_verdict,
                step, [], platform, stimulus='caller_update')
    assert good['status'] == 'passed'
    step['dispatch']['succeeded'] = False
    blocked = call(platform + ': native_checks.callback_verdict rejects unestablished update', native_checks.callback_verdict,
                   step, [], platform, stimulus='caller_update')
    assert blocked['status'] == 'unassessed'
summary['callback_gate_generic_probes'] = 'success required; empty events after unsuccessful update remain unassessed'
save('api-attempts.json', calls)
save('mechanical-checks.json', summary)
print(json.dumps({'reconstructed_case_platforms': len(summary['reconstructions']),
                  'source_seals': summary['source_seals'], 'api_attempts': len(calls),
                  'expected_rejections': sum(c['outcome'] == 'expected_rejection' for c in calls),
                  'errors': [c for c in calls if c['outcome'] in ['error', 'unexpected_acceptance']]}))
