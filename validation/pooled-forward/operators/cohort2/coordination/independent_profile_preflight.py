#!/usr/bin/env python3
"""Pure physical/profile/domain compatibility, never runtime or product grading."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write('\n')
    path.chmod(0o444)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--scope', choices=['A', 'B', 'I'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    run = root / 'cache/business/run-cohort2'
    manifest = load(run / 'manifest.json')
    helper = module(root / 'business-tools-v4/blind_study.py', 'pure_independent_profile_controller')
    cohort = load(run / 'COHORT-SEAL.json')
    assert len(cohort['members']) == 10
    original_arm = 'A' if args.scope == 'I' else args.scope
    tool = manifest['tools'][manifest['tasks'][0]['arms'][original_arm]['tool']]
    helper.frozen_files(tool)
    sys.path.insert(0, str(Path(tool['skill_root']) / 'scripts'))
    import coverage_domain
    import evidence_responsibility
    adapter = module(root / 'business_profile_admission.py', 'pure_independent_actual_profile_adapter')
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    with patch('subprocess.run', side_effect=AssertionError('Pure compatibility preflight cannot execute a subprocess')), \
         patch('subprocess.Popen', side_effect=AssertionError('Pure compatibility preflight cannot execute a subprocess')):
        for task in manifest['tasks']:
            task_id = task['id']
            arm = task['arms'][original_arm]
            initial_pins = load(root / 'cache/business/initial-reference/PREPARATION-SEAL.json')['tasks']
            public_pins = load(run / f'arms/{task_id}/{original_arm}/public-inputs.json')
            for platform in ['ios', 'android']:
                path = Path(initial_pins[task_id][platform]['config']['path'] if args.scope == 'I' else arm['hidden_configs'][platform])
                config = load(path)
                hook = arm['profile_admissions'][platform]
                for dependency in [hook['script'], hook['approval'], *hook.get('dependencies', [])]:
                    assert sha(dependency) == public_pins[dependency]
                approval = load(hook['approval'])
                admitted = adapter.verify(Path(hook['root']), approval, hook['approval_sha256'], platform, config)
                assert admitted['status'] == 'admitted_profile' and admitted['platform'] == platform
                plan, lock = load(config['plan']), load(config['design_lock'])
                claims = evidence_responsibility.compile_contract(config, plan, lock)
                assert not [v for v in claims['issues'] if v['priority'] == 'must'], claims['issues']
                source = [v for v in claims['claims'] if v['method'] == 'source' and v['priority'] == 'must']
                assert len(source) == 3 and all(v['supported'] for v in source)
                domain = coverage_domain.prepare(config, plan, lock) if platform == 'ios' else None
                folder = args.output / f'{task_id}-{platform}'
                folder.mkdir()
                save(folder / 'profile-admission.json', admitted)
                save(folder / 'responsibility-capabilities.json', claims)
                if domain:
                    save(folder / 'coverage-domain-prepared.json', domain)
                rows.append({'task': task_id, 'scope': args.scope, 'platform': platform, 'config': {'path': str(path), 'sha256': sha(path)},
                             'source_must_capabilities': len(source), 'source_truth_approved': False, 'native_truth_approved': False,
                             'ios_exact_source_shape_prepared': bool(domain), 'capture_adoption_approved': bool(config.get('capture_validity_ref'))})
    save(args.output / 'RESULT.json', {'version': 1, 'kind': 'pure-independent-runtime-binding-compatibility', 'passed': True,
                                     'scope': args.scope, 'rows': rows, 'sdk_or_native_execution': False,
                                     'script_sha256': sha(__file__), 'scope_limit': 'Exact actual profile/source/bridge/provider compatibility and supported default source duties only; no source truth, runtime, behavior, visual or coverage P.'})
    print(json.dumps({'scope': args.scope, 'profiles': len(rows), 'passed': True, 'sdk_or_native_execution': False}))


if __name__ == '__main__':
    main()
