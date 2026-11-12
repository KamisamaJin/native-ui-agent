#!/usr/bin/env python3
"""Pre-code capability admission using unchanged frozen public tool APIs.

Placeholder subjects check provider/owner compatibility, never source truth.
This shared study admission utility does not modify a contract or frozen tool.
Every subprocess boundary is forbidden during the check.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import traceback
from unittest.mock import patch


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill', required=True, type=Path)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--responsibility-source', default='reference')
    parser.add_argument('--responsibility-pointer', default='/responsibilities')
    args = parser.parse_args()
    skill = args.skill.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(skill / 'scripts'))
    import design_contract as design
    import evidence_responsibility as responsibility
    import execution_plan
    import requirement_routes
    import review_contract
    config = json.loads(args.config.read_text())
    ref = {'source': args.responsibility_source, 'pointer': args.responsibility_pointer}
    if config.get('responsibility_ref', ref) != ref:
        raise ValueError('Configuration responsibility source differs from explicit pre-code admission')
    result = {'kind': 'PURE_CAPABILITY_PREFLIGHT', 'preflight_script_sha256': sha(__file__),
              'config_file': str(args.config.resolve()),
              'config_sha256': sha(args.config), 'responsibility_ref': ref,
              'tool_files': {p.name: sha(p) for p in [Path(design.__file__), Path(responsibility.__file__),
                            Path(execution_plan.__file__), Path(requirement_routes.__file__), Path(review_contract.__file__)]},
              'source_truth_approved': False, 'runtime_truth_approved': False, 'native_execution': False,
              'scope': 'Compatibility/coverage/source provenance of approved inputs only. Placeholder files never prove production API, source behavior, compiled integration, native evidence or delivery.'}
    try:
        with patch('subprocess.run', side_effect=AssertionError('Subprocess forbidden in pure pre-code admission')), \
             patch('subprocess.Popen', side_effect=AssertionError('Subprocess forbidden in pure pre-code admission')):
            plan, lock, fixtures, policy, routes = [design.load(Path(config[k]))
                                                   for k in ['plan', 'design_lock', 'fixtures', 'policy', 'routes']]
            platform = plan['design_contract']['platform']
            declared = design.pointer(lock['sources'][ref['source']]['document'], ref['pointer'])
            source_root = output / 'PLACEHOLDER-SUBJECTS-NOT-IMPLEMENTATIONS'
            source_root.mkdir()
            component = source_root / 'production.placeholder'
            integration = output / 'integration.placeholder'
            component.write_text('PLACEHOLDER FOR CAPABILITY COMPATIBILITY ONLY. NOT A UI IMPLEMENTATION OR SOURCE APPROVAL.\n')
            integration.write_text('PLACEHOLDER FOR INTEGRATION SUBJECT BOUNDARY ONLY. NOT BUILD OR EXECUTION PROOF.\n')
            subjects = {}
            for claim in declared:
                if claim['method'] == 'source':
                    path = component if claim['owner'] == 'component' else Path(config['bridge']) if claim['owner'] == 'bridge' else integration
                    subjects[claim['subject']] = [str(path)]
            checked = dict(config, source_roots=[str(source_root)], evidence_subjects=subjects,
                           responsibility_ref=ref, source_review_store=str(output / 'unused-source-review-store'))
            claims = responsibility.compile_contract(checked, plan, lock)
            coverage = requirement_routes.audit(lock, config['design_sha256'], plan, routes, config['routes_sha256'])
            catalog = review_contract.catalog(plan, lock, config['design_sha256'], policy, config['policy_sha256'], platform)
            execution = execution_plan.compile_execution(plan, lock, config['design_sha256'], fixtures,
                                                        sha(config['bridge']), launch_ref=config['launch_ref'])
            execution_plan.verify_execution(execution, plan, lock, config['design_sha256'], fixtures, sha(config['bridge']))
            truth_unknowns = responsibility.evaluate(checked, claims)['blocking_claims']
            blockers = [row for row in claims['issues'] if row['priority'] == 'must']
            result.update(platform=platform, design_sha256=config['design_sha256'],
                          required_assertions=len(plan['required_assertion_ids']), states=len(plan['states']),
                          mandatory_capability_issues=blockers, must_route_gaps=coverage['must_route_gaps'],
                          unowned_assertions=coverage['unowned_assertions'],
                          evidence_truth_still_unassessed=truth_unknowns,
                          placeholder_subject_bindings=subjects,
                          passed=not blockers and not coverage['must_route_gaps'] and not coverage['unowned_assertions'])
            save(output / 'responsibility-capabilities.json', claims)
            save(output / 'requirement-coverage.json', coverage)
            save(output / 'atomic-catalog.json', catalog)
            save(output / 'execution.json', execution)
    except Exception as error:
        result.update(passed=False, error={'type': type(error).__name__, 'message': str(error)}, traceback=traceback.format_exc())
    save(output / 'RESULT.json', result)
    print(json.dumps({k: result.get(k) for k in ['kind', 'passed', 'platform', 'required_assertions',
                                              'mandatory_capability_issues', 'must_route_gaps', 'error']}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
