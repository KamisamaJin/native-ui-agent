#!/usr/bin/env python3
"""Seal independent typed design sources and compile assertions without value overrides.

Hashes establish identity, not authorship or correct interpretation of prose. A
design owner must approve the typed sources before implementation and publish the
lock digest through a separate review/experiment record.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from observation_contract import validate_actions, validate_selector

UNITS = {'pt', 'dp', 'sp', 'scalar', 'count', 'string', 'bool', 'events', 'argb'}
GEOMETRY = {'width', 'height', 'gap_x', 'gap_y', 'inset_left', 'inset_right', 'inset_top', 'inset_bottom'}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def load(path):
    return json.loads(path.read_text())


def pointer(value, path):
    if not isinstance(path, str) or not path.startswith('/'):
        raise ValueError('An exact non-root JSON Pointer is required for each expected value')
    for part in path[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return copy.deepcopy(value)


def typed(value):
    if not isinstance(value, dict) or set(value) != {'value', 'unit'} or value['unit'] not in UNITS:
        raise ValueError('Every source anchor must address exactly {value, unit}')
    v, unit = value['value'], value['unit']
    if unit in {'pt', 'dp', 'sp', 'scalar', 'count'}:
        if type(v) not in {int, float} or not math.isfinite(v) or (unit == 'count' and type(v) is not int):
            raise ValueError('Finite native-unit number required')
    elif unit == 'string' and not isinstance(v, str):
        raise ValueError('String source required')
    elif unit == 'bool' and type(v) is not bool:
        raise ValueError('Boolean source required')
    elif unit == 'events' and (not isinstance(v, list) or any(not isinstance(e, str) for e in v)):
        raise ValueError('Ordered event-string source required')
    elif unit == 'argb':
        if not isinstance(v, str) or len(v) != 9 or not v.startswith('#'):
            raise ValueError('Explicit #AARRGGBB color required; no implicit RGB/alpha conversion')
        value['value'] = int(v[1:], 16)
    return value


def expression(expr, sources):
    if not isinstance(expr, dict):
        raise ValueError('Expected values must reference sealed sources, never inline literals')
    if set(expr) == {'source', 'pointer'}:
        sid, anchor = expr['source'], expr['pointer']
        source = sources[sid]
        datum = typed(pointer(source['document'], anchor))
        return datum, [{'source': sid, 'path': source['path'], 'sha256': source['sha256'],
                        'pointer': anchor, 'source_datum': pointer(source['document'], anchor)}]
    if set(expr) == {'operation', 'arguments'} and expr['operation'] in {'add', 'subtract', 'multiply'}:
        arguments = expr['arguments']
        if not isinstance(arguments, list) or len(arguments) != 2:
            raise ValueError('Derivations require exactly two source-backed operands')
        (a, ap), (b, bp) = [expression(v, sources) for v in arguments]
        if a['unit'] not in {'pt', 'dp', 'sp', 'scalar', 'count'} or b['unit'] not in {'pt', 'dp', 'sp', 'scalar', 'count'}:
            raise ValueError('Only finite numerical derivations are supported')
        op = expr['operation']
        if op == 'multiply':
            if a['unit'] != 'scalar' and b['unit'] != 'scalar':
                raise ValueError('Multiplication needs a dimensionless source factor')
            unit = b['unit'] if a['unit'] == 'scalar' else a['unit']
            v = a['value'] * b['value']
        else:
            if a['unit'] != b['unit']:
                raise ValueError('No implicit pt/dp/sp conversions or mixed-unit arithmetic')
            unit = a['unit']
            v = a['value'] + b['value'] if op == 'add' else a['value'] - b['value']
        return typed({'value': v, 'unit': unit}), ap + bp
    raise ValueError('Unsupported expression or attempted inline/implementation-derived expectation')


def validate_contract(contract, sources):
    if contract.get('version') != 1 or not contract.get('design_owner') or not contract.get('approval_reference'):
        raise ValueError('Independent design owner and separate approval reference required')
    rules = contract.get('rules', [])
    ids = [r['id'] for r in rules]
    if not ids or len(ids) != len(set(ids)) or set(ids) != set(contract.get('required_rule_ids', [])):
        raise ValueError('Design must declare every unique rule ID')
    if not contract.get('scenarios'):
        raise ValueError('Independently selected scenarios and states required')
    for rule in rules:
        if set(rule) - {'id', 'kind', 'target', 'reference_target', 'property', 'basis', 'op', 'coverage', 'allowed_methods', 'stimulus', 'required_method'}:
            raise ValueError('Design rules cannot contain literal expectations or undeclared overrides')
        if rule.get('kind') not in {'control', 'text_layout', 'geometry', 'event', 'manual'}:
            raise ValueError('Unknown design assertion kind')
        if rule.get('op', 'eq') not in {'eq', 'contains', 'gte', 'lte', 'near'}:
            raise ValueError('Unsupported comparison')
        if rule['kind'] != 'event' and not rule.get('target'):
            raise ValueError('A logical target is required, including visual assertions')
        if rule['kind'] == 'geometry' and (rule.get('property') not in GEOMETRY or rule.get('basis', 'semantic') not in {'semantic', 'control'}):
            raise ValueError('Explicit supported native-bound geometry required')
        if rule['kind'] == 'geometry' and rule['property'] not in {'width', 'height'} and not rule.get('reference_target'):
            raise ValueError('Relational geometry needs a second logical target')
        if rule['kind'] in {'control', 'text_layout'} and not rule.get('property'):
            raise ValueError('Native assertion property required')
    for sid, scenario in contract['scenarios'].items():
        states = scenario.get('states', [])
        if not isinstance(scenario.get('actions'), list):
            raise ValueError('Independent scenario stimulus route required')
        state_ids = [s['id'] for s in states]
        if not states or len(state_ids) != len(set(state_ids)) or set(scenario.get('values', {})) != set(ids):
            raise ValueError('Every scenario must disposition every design rule')
        for rule in rules:
            selected = scenario['values'][rule['id']]
            if set(selected) != set(state_ids):
                raise ValueError('Every rule/state cell must have an expectation or an independent N/A reason')
            for state, cell in selected.items():
                if set(cell) == {'not_applicable'}:
                    if not isinstance(cell['not_applicable'], str) or not cell['not_applicable'].strip():
                        raise ValueError('Explicit N/A reason required')
                    continue
                if set(cell) - {'ios', 'android', 'tolerance'} or not {'ios', 'android'} <= set(cell):
                    raise ValueError('Both native platforms need source-backed expected values')
                for platform in ['ios', 'android']:
                    value, _ = expression(cell[platform], sources)
                    unit = value['unit']
                    allowed = ({'pt'} if platform == 'ios' else {'dp'}) if rule['kind'] == 'geometry' else None
                    if allowed and unit not in allowed:
                        raise ValueError('Native geometry unit mismatch')
                    known = {'label': 'string', 'enabled': 'bool', 'present': 'bool', 'unique': 'bool',
                             'selected': 'bool', 'font_sp': 'sp', 'font_weight': 'scalar', 'color_argb': 'argb',
                             'lines': 'count', 'overflow': 'bool', 'ellipsized': 'bool'}
                    expected_unit = 'events' if rule['kind'] == 'event' else known.get(rule.get('property'))
                    if expected_unit and unit != expected_unit:
                        raise ValueError('Property and sealed unit disagree')
                    if rule.get('op') == 'near':
                        if 'tolerance' not in cell:
                            raise ValueError('Approximate comparisons need independently sourced tolerance')
                        tolerance, _ = expression(cell['tolerance'][platform], sources)
                        if tolerance['unit'] != unit or tolerance['value'] < 0:
                            raise ValueError('Tolerance must be finite, nonnegative and in the same unit')


def seal(contract_path, root):
    contract = load(contract_path)
    sources = {}
    for entry in contract.get('sources', []):
        if set(entry) != {'id', 'path', 'sha256'} or entry['id'] in sources:
            raise ValueError('Unique exact source records required')
        path = (root / entry['path']).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError('Design source must be inside the independent design root')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise ValueError('Design source digest differs from approved source')
        sources[entry['id']] = dict(entry, document=json.loads(raw), raw_utf8=raw.decode())
    if not sources:
        raise ValueError('No independent typed sources')
    validate_contract(contract, sources)
    return {'version': 1, 'contract': contract, 'sources': sources,
            'contract_sha256': digest(contract),
            'trust_limit': 'Identity and exact typed derivation only. Authorship, design correctness and approval require a separate preimplementation review record.'}


def validate_lock(lock, trusted_sha256):
    if not trusted_sha256 or digest(lock) != trusted_sha256:
        raise ValueError('Design lock must match a separately pinned canonical SHA256')
    if lock.get('version') != 1 or digest(lock['contract']) != lock['contract_sha256']:
        raise ValueError('Changed design contract')
    for entry in lock['contract']['sources']:
        source = lock['sources'][entry['id']]
        if any(source[k] != entry[k] for k in entry) or hashlib.sha256(source['raw_utf8'].encode()).hexdigest() != entry['sha256']:
            raise ValueError('Changed sealed source')
        if json.loads(source['raw_utf8']) != source['document']:
            raise ValueError('Source document no longer matches exact sealed bytes')
    validate_contract(lock['contract'], lock['sources'])


def compile_contract(lock, trusted_sha256, scenario, platform, bindings, actions):
    from native_checks import validate_plan
    validate_lock(lock, trusted_sha256)
    if platform not in {'ios', 'android'}:
        raise ValueError('Native platform required')
    contract = lock['contract']
    selected = contract['scenarios'][scenario]
    states = copy.deepcopy(selected['states'])
    enriched = copy.deepcopy(actions)
    validate_actions(enriched)
    logical = {r['target'] for r in contract['rules'] if 'target' in r} | {r['reference_target'] for r in contract['rules'] if 'reference_target' in r}
    logical |= {a[field] for a in selected['actions'] for field in ['target', 'after_target'] if isinstance(a.get(field), str)}
    if set(bindings) != logical:
        raise ValueError('Bindings may only supply the complete logical-target selector map; no expected overrides')
    for selector in bindings.values():
        validate_selector(selector)
        if set(selector) - {'identifier', 'label', 'role'}:
            raise ValueError('A binding is only a native identity/role selector, never expected values or operators')
    approved_actions = copy.deepcopy(selected['actions'])
    for action in approved_actions:
        for field in ['target', 'after_target']:
            if isinstance(action.get(field), str):
                action[field] = copy.deepcopy(bindings[action[field]])
    if canonical(actions) != canonical(approved_actions):
        raise ValueError('Stimulus route differs from the independent design; only selectors can be bound')
    assertions, ledger = [], []
    for state in states:
        index = state.get('after_action')
        if type(index) is not int or not -1 <= index < len(enriched):
            raise ValueError('Design state/action index invalid')
        if index >= 0:
            if enriched[index].get('state_id', state['id']) != state['id']:
                raise ValueError('Native route differs from independently selected state')
            enriched[index]['state_id'] = state['id']
        targets = []
        for rule in contract['rules']:
            cell = selected['values'][rule['id']][state['id']]
            identity = state['id'].replace('~', '~0').replace('/', '~1') + '/' + rule['id'].replace('~', '~0').replace('/', '~1')
            row = {'id': identity, 'state': state['id'], 'requirement_id': rule['id']}
            if 'not_applicable' in cell:
                ledger.append(dict(row, disposition='not_applicable', reason=cell['not_applicable']))
                continue
            expected, proof = expression(cell[platform], lock['sources'])
            check = {k: copy.deepcopy(v) for k, v in rule.items() if k not in {'id', 'target', 'reference_target'}}
            check.update(row, expected=expected['value'], unit=expected['unit'], expectation_provenance=proof,
                         source='design-lock:' + trusted_sha256)
            for field in ['target', 'reference_target']:
                if field in rule:
                    check[field] = copy.deepcopy(bindings[rule[field]])
                    if check[field] not in targets:
                        targets.append(check[field])
            if check['kind'] == 'event':
                check.setdefault('action_index', state.get('stimulus_action', index))
            if check.get('op') == 'near':
                tolerance, tp = expression(cell['tolerance'][platform], lock['sources'])
                check['tolerance'] = tolerance['value']
                check['tolerance_provenance'] = tp
            assertions.append(check)
            ledger.append(dict(row, disposition='required', provenance=proof))
        if index >= 0 and state.get('coverage') == 'targets' and targets and enriched[index].get('type') != 'sweep':
            enriched[index]['after_targets'] = targets
    plan = {'version': 1, 'states': states, 'assertions': assertions,
            'required_assertion_ids': [a['id'] for a in assertions],
            'matrix_contract': {'selected_states': [s['id'] for s in states], 'selected_requirements': contract['required_rule_ids'], 'cells': ledger},
            'design_contract': {'lock_sha256': trusted_sha256, 'scenario': scenario, 'platform': platform,
                                'bindings': copy.deepcopy(bindings), 'base_actions': copy.deepcopy(actions)}}
    validate_plan(plan)
    validate_actions(enriched)
    return plan, enriched


def verify_generated(plan, lock, trusted_sha256, platform):
    metadata = plan.get('design_contract', {})
    if metadata.get('lock_sha256') != trusted_sha256 or metadata.get('platform') != platform:
        raise ValueError('Generated plan is not bound to this trusted design/platform')
    expected, actions = compile_contract(lock, trusted_sha256, metadata['scenario'], platform,
                                         metadata['bindings'], metadata['base_actions'])
    if canonical(expected) != canonical(plan):
        raise ValueError('Generated assertions changed: expected value, precision, source, state or rule coverage differs')
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    s = sub.add_parser('seal'); s.add_argument('--contract', type=Path, required=True); s.add_argument('--root', type=Path, required=True); s.add_argument('--output', type=Path, required=True)
    c = sub.add_parser('compile'); c.add_argument('--lock', type=Path, required=True); c.add_argument('--lock-sha256', required=True); c.add_argument('--scenario', required=True); c.add_argument('--platform', choices=['ios', 'android'], required=True); c.add_argument('--bindings', type=Path, required=True); c.add_argument('--actions', type=Path, required=True); c.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Fresh output required; approved expectations are never overwritten')
    if args.command == 'seal':
        result = seal(args.contract, args.root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
        print(json.dumps({'design_lock_sha256': digest(result), 'approval_reference': result['contract']['approval_reference']}))
    else:
        plan, actions = compile_contract(load(args.lock), args.lock_sha256, args.scenario, args.platform, load(args.bindings), load(args.actions))
        args.output.mkdir(parents=True)
        for name, value in [('plan.json', plan), ('actions.json', actions)]:
            (args.output / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
        print(json.dumps({'assertions': len(plan['assertions']), 'cells': len(plan['matrix_contract']['cells']), 'design_lock_sha256': args.lock_sha256}))


if __name__ == '__main__':
    main()
