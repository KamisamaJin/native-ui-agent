"""Bounded observation requests shared by the native command adapters."""


def validate_selector(value):
    if not isinstance(value, dict) or sum(isinstance(value.get(k), str) and bool(value[k]) for k in ('identifier', 'label')) != 1:
        raise ValueError('Selector needs exactly one nonempty identifier or exact label')
    if str(value.get('role', 'button')).lower() not in {'button', 'switch', 'other', 'statictext', 'text'}:
        raise ValueError('Unsupported selector role')


def validate_actions(actions):
    if not isinstance(actions, list) or len(actions) > 40:
        raise ValueError('At most 40 explicit bounded actions')
    ids = [a['state_id'] for a in actions if 'state_id' in a]
    if any(not isinstance(i, str) or not i or i in {'initial', 'final'} for i in ids) or len(ids) != len(set(ids)):
        raise ValueError('Explicit state IDs must be unique; initial/final are reserved')
    for action in actions:
        if action.get('type') == 'tap':
            validate_selector(action.get('target', {'identifier': action.get('identifier')}))
        if 'after_target' in action:
            validate_selector(action['after_target'])
        targets = action.get('after_targets')
        if targets is not None:
            if not isinstance(targets, list) or not 1 <= len(targets) <= 32:
                raise ValueError('after_targets needs 1 to 32 exact selectors')
            for target in targets:
                validate_selector(target)
            import json
            if len({json.dumps(t, sort_keys=True) for t in targets}) != len(targets):
                raise ValueError('Duplicate post-action selectors')
        if 'observation_max_scrolls' in action and (type(action['observation_max_scrolls']) is not int or not 0 <= action['observation_max_scrolls'] <= 40):
            raise ValueError('observation_max_scrolls must be an integer from 0 to 40 for the whole target set')
