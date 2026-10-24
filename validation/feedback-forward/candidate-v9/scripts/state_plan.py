#!/usr/bin/env python3
"""Compile a declared requirement-by-state matrix; never invent expectations."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from native_checks import validate_plan
from observation_contract import validate_actions, validate_selector


def identifier(value):
    if not isinstance(value, str) or not value or len(value) > 240:
        raise ValueError('Nonempty bounded state and requirement IDs required')
    return value.replace('~', '~0').replace('/', '~1')


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def compile_matrix(matrix, actions=None):
    if matrix.get('version') != 1 or not matrix.get('states') or not matrix.get('requirements'):
        raise ValueError('Nonempty version1 states and requirements required')
    states = copy.deepcopy(matrix['states'])
    requirements = matrix['requirements']
    state_ids = [s['id'] for s in states]
    requirement_ids = [r['id'] for r in requirements]
    for values, declared in [(state_ids, matrix.get('required_state_ids')), (requirement_ids, matrix.get('required_requirement_ids'))]:
        for value in values:
            identifier(value)
        if len(values) != len(set(values)) or not isinstance(declared, list) or len(declared) != len(set(declared)) or set(values) != set(declared):
            raise ValueError('Declared state/requirement IDs must exactly match the complete matrix')
    compiled, ledger = [], []
    for requirement in requirements:
        source = requirement.get('source')
        if not isinstance(source, str) or not source.strip():
            raise ValueError('Each requirement needs its expectation source')
        base = copy.deepcopy(requirement.get('check', {}))
        overrides = requirement.get('by_state', {})
        exclusions = requirement.get('not_applicable', {})
        if not isinstance(overrides, dict) or not isinstance(exclusions, dict) or (set(overrides) | set(exclusions)) - set(state_ids):
            raise ValueError('Unknown state in requirement overrides/dispositions')
        if set(overrides) & set(exclusions):
            raise ValueError('A state cannot be both checked and not applicable')
        for state in states:
            sid = state['id']
            key = identifier(sid) + '/' + identifier(requirement['id'])
            cell = {'id': key, 'state': sid, 'requirement_id': requirement['id'], 'source': source}
            if sid in exclusions:
                reason = exclusions[sid]
                if not isinstance(reason, str) or not reason.strip():
                    raise ValueError('Not-applicable cells need an explicit reason')
                ledger.append(dict(cell, disposition='not_applicable', reason=reason))
                continue
            override = overrides.get(sid, {})
            if not isinstance(override, dict) or set(override) - {'expected', 'target', 'action_index', 'stimulus', 'required_method', 'op'}:
                raise ValueError('Only expected/native-target/stimulus fields can vary by state')
            check = dict(base, **copy.deepcopy(override))
            if check.get('kind') != 'manual' and 'expected' not in check:
                raise ValueError('Missing expected value for ' + key)
            if 'target' in check:
                validate_selector(check['target'])
            if check.get('kind') == 'event':
                check.setdefault('action_index', state.get('stimulus_action', state.get('after_action')))
            compiled.append(dict(check, **cell))
            ledger.append(dict(cell, disposition='required'))
    if not compiled:
        raise ValueError('Matrix has no applicable atomic assertions')
    plan = {'version': 1, 'states': states, 'assertions': compiled,
            'required_assertion_ids': [a['id'] for a in compiled],
            'matrix_contract': {'matrix_sha256': hashlib.sha256(canonical(matrix)).hexdigest(),
                                'selected_states': state_ids, 'selected_requirements': requirement_ids,
                                'cells': ledger,
                                'scope': 'Complete declared matrix, not proof that natural-language requirements were fully translated; explicit exclusions remain auditable.'}}
    validate_plan(plan)
    enriched = [copy.deepcopy(action) for action in actions] if actions is not None else None
    if enriched is not None:
        validate_actions(enriched)
        assigned = {}
        for state in states:
            index = state.get('after_action')
            if index == -1:
                continue
            if type(index) is not int or not 0 <= index < len(enriched):
                raise ValueError('Each action state needs a valid native action index')
            if index in assigned:
                raise ValueError('Two different states cannot relabel one native action')
            assigned[index] = state['id']
            action = enriched[index]
            if action.get('state_id', state['id']) != state['id']:
                raise ValueError('Matrix state differs from original native action state')
            action['state_id'] = state['id']
            if state.get('coverage') != 'targets' or action.get('type') == 'sweep':
                continue
            targets = []
            for assertion in compiled:
                target = assertion.get('target')
                if assertion['state'] == state['id'] and target and target not in targets:
                    targets.append(copy.deepcopy(target))
            if targets:
                action['after_targets'] = targets
        validate_actions(enriched)
    return plan, enriched


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', type=Path, required=True)
    parser.add_argument('--actions', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Fresh output directory required')
    matrix = json.loads(args.matrix.read_text())
    actions = json.loads(args.actions.read_text()) if args.actions else None
    plan, enriched = compile_matrix(matrix, actions)
    args.output.mkdir(parents=True)
    (args.output / 'plan.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n')
    if enriched is not None:
        (args.output / 'actions.json').write_text(json.dumps(enriched, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'assertions': len(plan['assertions']), 'matrix_cells': len(plan['matrix_contract']['cells']),
                      'not_applicable': sum(c['disposition'] == 'not_applicable' for c in plan['matrix_contract']['cells'])}))


if __name__ == '__main__':
    main()
