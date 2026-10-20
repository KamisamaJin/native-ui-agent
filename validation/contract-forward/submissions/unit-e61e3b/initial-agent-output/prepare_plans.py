#!/usr/bin/env python3
"""Pre-feedback translation of the public design into baseline-v5 native checks.
No production source or rendered candidate is read. Baseline-v5 has no design-lock
compiler; its supported native plan schema is used directly. A near comparison
is expressed as two supported inclusive native numeric bounds, preserving the
public family requirement_id and independently sourced serialization tolerance.
"""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/contract-forward')
OUT = Path(__file__).resolve().parent
PUBLIC = ROOT / 'design/public'
SKILL = ROOT / 'baseline-v5'
sys.path.insert(0, str(SKILL / 'scripts'))
from native_checks import validate_plan
from observation_contract import validate_actions


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


lock = read(PUBLIC / 'design-lock.json')
lock_hash = hashlib.sha256(canonical(lock)).hexdigest()
assert lock_hash == 'c2548a601384046a016e98258728877982f30a4ed25be22455d9ec9ea4399bc1'
contract = read(PUBLIC / 'contract.json')
reference = read(PUBLIC / 'reference.json')
bindings = read(PUBLIC / 'bindings.json')
assert sha(PUBLIC / 'reference.json') == contract['sources'][0]['sha256']


def resolve(ref):
    assert ref['source'] == 'reference'
    value = reference
    for key in ref['pointer'].split('/')[1:]:
        value = value[key.replace('~1', '/').replace('~0', '~')]
    assert set(value) >= {'value', 'unit'}
    return deepcopy(value)


summary = []
for case, scenario in contract['scenarios'].items():
    for platform in ['ios', 'android']:
        folder = OUT / 'plans' / case / platform
        folder.mkdir(parents=True, exist_ok=False)
        states = deepcopy(scenario['states'])
        actions = read(PUBLIC / 'cases' / case / ('actions.' + platform + '.json'))
        original_actions = deepcopy(actions)
        assertions, matrix = [], []
        for rule in contract['rules']:
            rid = rule['id']
            for state in states:
                sid = state['id']
                cell_id = sid + '/' + rid
                ref = scenario['values'][rid][sid]
                source = {
                    'path': str(PUBLIC / 'reference.json'),
                    'sha256': sha(PUBLIC / 'reference.json'),
                    'contract_path': str(PUBLIC / 'contract.json'),
                    'contract_sha256': sha(PUBLIC / 'contract.json'),
                    'approved_lock_canonical_sha256': lock_hash,
                }
                cell = {'id': cell_id, 'state': sid, 'requirement_id': rid,
                        'source': source, 'assertion_ids': []}
                if 'not_applicable' in ref:
                    cell.update(disposition='not_applicable', reason=ref['not_applicable'])
                    matrix.append(cell)
                    continue
                origin = ref[platform]
                expected = resolve(origin)
                source.update(pointer=origin['pointer'], original_value=deepcopy(expected))
                item = {'id': cell_id, 'state': sid, 'requirement_id': rid,
                        'kind': rule['kind'], 'source': json.dumps(source, sort_keys=True),
                        'expected': expected['value']}
                if 'target' in rule:
                    item['target'] = deepcopy(bindings[rule['target']])
                if 'property' in rule:
                    item['property'] = rule['property']
                if rule['kind'] == 'geometry':
                    # Native semantic/control bounds only, never glyph or padding claims.
                    item.update(kind='control', property='ax_height', op='gte',
                                measurement_scope='Native control accessibility box in pt/dp; '
                                'require full target visibility in subsequent state evidence.')
                elif rule['kind'] == 'event':
                    item['action_index'] = state['after_action']
                    item['stimulus'] = rule.get('stimulus', 'activation')
                    item['required_method'] = ('caller_fixture_update' if item['stimulus'] == 'caller_update'
                                               else 'xcui_tap' if platform == 'ios' else 'compose_onclick')
                    item['dispatch_limit'] = 'No dispatch / blocked disabled / wrong method remains U, including expected empty callback intervals.'
                elif rule['kind'] == 'manual':
                    item.update(coverage='target', allowed_methods=['visual'])
                    item['review_scope'] = 'Only complete Reserve seats label visibility in actual SHA-bound state screenshots; no computed typography, color or geometry inference.'
                elif rule['property'] == 'color_argb':
                    item['expected'] = int(expected['value'].removeprefix('#'), 16)
                    item['conversion'] = 'Exact unsigned ARGB integer from independently supplied eight-digit hexadecimal ARGB.'
                if platform == 'ios' and rule['kind'] == 'text_layout':
                    item['capability_limit'] = 'Generic SwiftUI computed style/ellipsis is unsupported by baseline-v5 native observer; retain U. Source declarations and visual opinions cannot establish this fact.'
                cell.update(disposition='required')
                if rid == 'title-font':
                    tolerance_ref = ref['tolerance'][platform]
                    tolerance = resolve(tolerance_ref)
                    cell['tolerance_source'] = tolerance_ref
                    for suffix, op, value in [('lower', 'gte', expected['value'] - tolerance['value']),
                                              ('upper', 'lte', expected['value'] + tolerance['value'])]:
                        bound = deepcopy(item)
                        bound.update(id=cell_id + '/' + suffix, op=op, expected=value)
                        bound['tolerance_provenance'] = {'reference_sha256': sha(PUBLIC / 'reference.json'),
                                                        'pointer': tolerance_ref['pointer'],
                                                        'value': tolerance,
                                                        'scope': 'Serialization tolerance only, not visual size tolerance.'}
                        assertions.append(bound)
                        cell['assertion_ids'].append(bound['id'])
                else:
                    assertions.append(item)
                    cell['assertion_ids'].append(item['id'])
                matrix.append(cell)
        plan = {
            'version': 1,
            'states': states,
            'required_assertion_ids': [a['id'] for a in assertions],
            'assertions': assertions,
            'matrix_contract': {
                'selected_states': [s['id'] for s in states],
                'selected_requirements': contract['required_rule_ids'],
                'cells': matrix,
                'scope': 'Original public selected rule families. Independent N/A cells retained; missing native capability and dispatch remain U.',
            },
            'limits': [
                'iOS computed title size/color and detail ellipsis remain U.',
                'Native control geometry lower bound does not establish padding, glyph size, or physical touch bounds.',
                'Fully visible target evidence must be confirmed; baseline checker uses intersects_viewport for raw native fact eligibility.',
                'Manual Reserve-label checks need actual state screenshots, hashes and snapshot indices; no manual verdict supplied before captures.',
                'Corner radius, internal padding, gaps, borders, non-title fonts/colors, course-description clipping and whole-card visual similarity are outside selected numerical scope.',
            ],
        }
        validate_plan(plan)
        for state in states:
            if state['coverage'] != 'targets':
                continue
            index = state['after_action']
            action = actions[index]
            assert action['state_id'] == state['id']
            targets = []
            for assertion in assertions:
                target = assertion.get('target')
                if assertion['state'] == state['id'] and target is not None and target not in targets:
                    targets.append(deepcopy(target))
            action.update(after_targets=targets, observation_max_scrolls=40)
        validate_actions(actions)
        observation_fields = {'after_targets', 'after_target', 'observation_max_scrolls', 'observe_after'}
        assert [{k: v for k, v in a.items() if k not in observation_fields} for a in actions] == original_actions
        dump(folder / 'plan.json', plan)
        dump(folder / 'actions.json', actions)
        dump(folder / 'matrix.json', {'version': 1, 'case': case, 'platform': platform,
                                      'states': states, 'required_rule_ids': contract['required_rule_ids'],
                                      'cells': matrix, 'plan_assertion_ids': plan['required_assertion_ids']})
        summary.append({'case': case, 'platform': platform, 'states': len(states),
                        'rule_families': len(contract['required_rule_ids']),
                        'assertions': len(assertions), 'cells': len(matrix),
                        'not_applicable': sum(c['disposition'] == 'not_applicable' for c in matrix),
                        'plan_path': str(folder / 'plan.json'), 'actions_path': str(folder / 'actions.json')})
dump(OUT / 'plans-summary.json', {'prepared_utc': datetime.now(timezone.utc).isoformat(),
                                 'reference_approved_lock_sha256': lock_hash,
                                 'plans': summary})
print(json.dumps(summary, indent=2))
