#!/usr/bin/env python3
"""Offline replay with the original frozen bundle; no source namespace or SDK."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(value, roots):
    if isinstance(value, dict):
        return {k: normalize(v, roots) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v, roots) for v in value]
    if isinstance(value, str):
        for root in roots:
            if value.startswith(root + '/'):
                return '<native>/' + value[len(root) + 1:]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', choices=['A', 'B', 'initial'], required=True)
    parser.add_argument('--platform', choices=['ios', 'android'], required=True)
    parser.add_argument('--scope', choices=['public', 'private'], default='private')
    parser.add_argument('--reviewer', choices=['1', '2'])
    args = parser.parse_args()
    initial = args.candidate == 'initial'
    if initial and args.scope == 'private':
        root = R / 'business-evidence/initial/private-reference' / args.platform
    else:
        root = R / 'business-evidence' / ('A' if initial else args.candidate) / args.scope / ('D0' if initial else 'Final' if args.scope == 'public' else 'Hidden') / args.platform
    scope = R / 'business-design' / args.scope
    capture = root / 'cycle/capture'
    receipt = read(capture / 'result.json')
    bundle = R / ('baseline-v11' if args.candidate == 'A' or initial and args.scope == 'public' else 'candidate-v12.6')
    for rel, expected in receipt.get('tool_files', {}).items():
        assert sha(bundle / rel) == expected, rel
    sys.path.insert(0, str(bundle / 'scripts'))
    import acceptance as ac
    import design_contract as d
    import execution_plan as xp
    import native_checks as nc
    import review_contract as rc

    approval = read(scope / 'approval.json')
    case = 'cedar-lunch' if args.scope == 'public' else 'evening-service'
    lock = read(scope / 'design-lock.json')
    policy = read(scope / 'policy.json')
    plan = read(capture / 'parent-plan.json')
    execution = read(capture / 'execution.json')
    xp.verify_execution(execution, plan, lock, approval['design_lock_sha256'], read(scope / 'cases' / case / 'fixtures.json'), sha(scope / ('Bridge.swift' if args.platform == 'ios' else 'ObserverBridge.kt')))
    native = capture / 'native'
    observation = read(native / 'observation.json')
    xp.verify_capture_images(receipt, native)
    assert read(capture / 'source-before.json') == read(capture / 'source-after.json')
    catalog = rc.catalog(plan, lock, approval['design_lock_sha256'], policy, approval['policy_sha256'], args.platform)
    submission = {'version': 1, 'catalog_sha256': d.digest(catalog), 'observation_sha256': sha(native / 'observation.json'), 'decisions': []}
    manual = rc.bind(plan, lock, approval['design_lock_sha256'], policy, approval['policy_sha256'], observation, sha(native / 'observation.json'), native, submission, args.platform)
    report = nc.evaluate(plan, observation, args.platform, manual, native, sha(native / 'observation.json'), lock, approval['design_lock_sha256'], policy, approval['policy_sha256'])
    report['environment'] = ac.environment(observation, read(scope / 'cases' / case / ('environment.' + args.platform + '.json')), args.platform)
    original_native = str(Path(receipt['argv'][receipt['argv'].index('--output') + 1]))
    assert normalize(report, [str(native)]) == normalize(read(capture / 'automatic.json'), [original_native])
    if args.reviewer:
        if args.scope != 'private':
            raise ValueError('Independent submission projection is defined for the hidden packets')
        bound = R / 'business-evidence/independent-evaluation/independent-bindings-v3' / ('reviewer-' + args.reviewer) / args.candidate / args.platform
        manual = rc.bind(plan, lock, approval['design_lock_sha256'], policy, approval['policy_sha256'], observation, sha(native / 'observation.json'), native, read(bound / 'image-store/original-review/submission.json'), args.platform)
        checked = nc.evaluate(plan, observation, args.platform, manual, native, sha(native / 'observation.json'), lock, approval['design_lock_sha256'], policy, approval['policy_sha256'])
        checked['environment'] = report['environment']
        assert normalize(checked, [str(native)]) == normalize(read(bound / 'completion/evaluated.json'), [original_native])
        report = checked
    print(json.dumps({'status': 'PASS', 'candidate': args.candidate, 'scope': args.scope, 'platform': args.platform,
                      'reviewer': args.reviewer, 'counts': report['counts'], 'execution_scope': execution['scope'],
                      'scope_limit': 'Original sealed facts and independent actuals only; no SDK, edited expected values, current-source revalidation or new PR quality claim.'}))


if __name__ == '__main__':
    main()
