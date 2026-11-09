"""Approved action dependencies and native preconditions, separate from assertions.

No desired business outcome is inferred from a successful tap. The next action
may require observed native facts. A blocked dependency keeps its descendants
unassessed; it does not create a product failure or satisfy a missing requirement.
"""
from __future__ import annotations
import copy

PROPERTIES = {'present', 'enabled', 'selected', 'label', 'value'}


def compile_actions(actions):
    from observation_contract import validate_selector
    result = copy.deepcopy(actions)
    for index, action in enumerate(result):
        deps = action.get('depends_on', [index - 1] if index else [])
        if not isinstance(deps, list) or len(set(deps)) != len(deps) or any(type(i) is not int or not 0 <= i < index for i in deps):
            raise ValueError('Action dependencies must be unique earlier action indices')
        action['depends_on'] = deps
        conditions = action.get('preconditions', [])
        if not isinstance(conditions, list) or len(conditions) > 16: raise ValueError('Bounded native preconditions required')
        for condition in conditions:
            if set(condition) != {'target', 'property', 'op', 'expected'} or condition['property'] not in PROPERTIES or condition['op'] not in {'eq', 'contains'}:
                raise ValueError('Exact typed native precondition required')
            validate_selector(condition['target'])
            if condition['property'] in {'present', 'enabled', 'selected'} and type(condition['expected']) is not bool:
                raise ValueError('Boolean native precondition expected')
            if condition['op'] == 'contains' and type(condition['expected']) is not str:
                raise ValueError('Contains precondition needs a string')
        action['preconditions'] = conditions
    return result


def condition_passes(condition, actual):
    if actual is None: return False
    from native_checks import compare
    return compare(actual, condition['expected'], condition['op'])


def readiness(action, steps):
    """The producer uses established receipts; the consumer independently replays."""
    return all(i < len(steps) and steps[i].get('guard', {}).get('established') is True for i in action.get('depends_on', []))


def replay(actions, steps, platform):
    from native_checks import callback_verdict
    actions = compile_actions(actions); rows = []
    for index, action in enumerate(actions):
        blocked = [i for i in action['depends_on'] if i >= len(rows) or not rows[i]['established']]
        step = steps[index] if index < len(steps) else {}; proof = step.get('guard', {})
        conditions = proof.get('conditions', [])
        condition_ok = (len(conditions) == len(action['preconditions']) and
                        all(v.get('condition') == c and condition_passes(c, v.get('actual'))
                            for c, v in zip(action['preconditions'], conditions)))
        ready = (not blocked and proof.get('protocol') == 1 and proof.get('depends_on') == action['depends_on'] and condition_ok and proof.get('ready') is True)
        kind = action['type']
        if kind in {'tap', 'apply_next_fixture'}:
            delta = step.get('callback_delta')
            events = [v.get('event') if isinstance(v, dict) else v for v in delta] if isinstance(delta, list) else []
            verdict = callback_verdict(step, events, platform, stimulus='activation' if kind == 'tap' else 'caller_update')
            dispatched = verdict['stimulus_established'] and proof.get('binding') == step.get('dispatch', {}).get('binding_before')
        else:
            dispatched = (step.get('outcome') in {'observed', 'completed'} and bool(step.get('binding_after'))
                          and proof.get('binding') == step.get('binding_after'))
        established = bool(ready and dispatched)
        # A producer flag cannot certify its own successful activation.
        if proof.get('established') is not established: established = False
        rows.append({'action_index': index, 'ready': ready, 'established': established, 'blocked_on': blocked,
                     'reason': 'approved native action path established' if established else 'action prerequisite/dispatch not established',
                     'conditions': conditions})
    return rows


def state_verdict(observation, state, platform):
    if observation.get('guard_protocol') != 1: return None
    index = state.get('after_action')
    if type(index) is not int or index < 0: return None
    steps = observation.get('steps', [])
    actions = observation.get('guard_actions')
    if not isinstance(actions, list) or index >= len(actions):
        return {'established': False, 'reason': 'missing approved guarded action route', 'action_index': index}
    rows = replay(actions, steps, platform)
    return rows[index]


def verify_observation(actions, observation, platform):
    if observation.get('guard_protocol') != 1 or observation.get('guard_platform') != platform or observation.get('guard_actions') != compile_actions(actions):
        raise ValueError('Native packet did not execute the exact compiled guarded route')
    return replay(actions, observation.get('steps', []), platform)
