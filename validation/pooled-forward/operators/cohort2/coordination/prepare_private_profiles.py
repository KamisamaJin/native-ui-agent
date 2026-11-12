#!/usr/bin/env python3
"""Bind exact approved private inputs to sealed final or genuine initial source."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import time


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


def ref(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


SEMANTIC = ['plan', 'design_lock', 'design_sha256', 'fixtures', 'bridge', 'launch_ref', 'policy', 'policy_sha256',
            'routes', 'routes_sha256', 'environment', 'environment_sha256', 'responsibility_ref', 'profile_admission']
PHYSICAL = ['source_roots', 'native_options', 'resources', 'dependency_files', 'dependency_environment']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--domain-admission', type=Path, required=True)
    parser.add_argument('--domain-admission-sha256', required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    run = root / 'cache/business/run-cohort2'
    cohort = load(run / 'COHORT-SEAL.json')
    assert len(cohort['members']) == 10
    assert (root / 'operators/cohort2/coordination/PRIVATE-PREPARATION-AUTHORIZATION.json').is_file()
    assert not (run / 'HIDDEN-AUTHORIZATION.json').exists()
    assert sha(args.domain_admission) == args.domain_admission_sha256
    domains = load(args.domain_admission)
    assert domains['cohort'] == ref(run / 'COHORT-SEAL.json')
    manifest = load(run / 'manifest.json')
    case_map = {c['id']: c for c in load(root / 'operators/cohort2/INITIAL-AUTHOR-ADMISSION.json')['cases']}
    design_root = root / 'business-design-cohort2-v2'
    approvals = load(design_root / 'APPROVAL-MAPPING.json')
    initial_pins, profiles = {}, {}
    for task in manifest['tasks']:
        task_id = task['id']
        case = case_map[task_id]
        initial_pins[task_id] = {}
        profiles[task_id] = {}
        for platform in ['ios', 'android']:
            approved = approvals['profiles'][f"private-{case['design_task']}-{platform}"]
            authored_path = design_root / approved['profile_path']
            original = load(authored_path)
            for arm in ['A', 'B', 'I']:
                public_arm = 'A' if arm == 'I' else arm
                self_seal = load(run / f'arms/{task_id}/{public_arm}/SELF-SEAL.json')
                public_ref = self_seal['active_configs'][platform]
                assert sha(public_ref['path']) == public_ref['sha256']
                public = load(public_ref['path'])
                config = copy.deepcopy(original)
                config['purpose'] = 'actual_independent_private_initial_reference_runtime' if arm == 'I' else 'actual_independent_private_final_source_runtime'
                for key in PHYSICAL:
                    if key in public:
                        config[key] = copy.deepcopy(public[key])
                    else:
                        config.pop(key, None)
                if arm == 'I':
                    base = root / f'cache/business/initial-reference/{task_id}'
                    workspace = base / 'workspace'
                    source_manifest = base / 'source.json'
                    source = load(source_manifest)
                    config['source_roots'] = [v['path'] for v in source['roots']]
                    config['resources']['root'] = str(base / 'resources' / platform)
                    config['native_options']['package' if platform == 'ios' else 'project'] = str(workspace / ('alerttoast' if platform == 'ios' else 'reply/Reply'))
                    if platform == 'android':
                        config['dependency_files']['android'] = [str(workspace / 'reply/Reply/.native-ui/java-desktop.jar'), str(workspace / 'reply/Reply/gradlew')]
                    path = base / 'profiles' / f'{platform}.json'
                    review_base = base / 'reviews' / platform
                else:
                    base = Path(task['arms'][arm]['workspace']).parent
                    workspace = Path(task['arms'][arm]['workspace'])
                    source_manifest = run / f'arms/{task_id}/{arm}/final-source/source.json'
                    path = Path(task['arms'][arm]['hidden_configs'][platform])
                    review_base = base / 'hidden-reviews' / platform
                    assert config['source_roots'] == task['arms'][arm]['source_roots']
                    assert config['resources']['root'] in task['arms'][arm]['resource_roots']
                component_path = workspace / ('alerttoast/Sources/AlertToast/' + case['component'] + '.swift' if platform == 'ios'
                                               else 'reply/Reply/app/src/main/java/com/example/reply/ui/components/business/' + case['component'] + '.kt')
                config['evidence_subjects'] = {
                    'production_api': [str(component_path)],
                    'thin_bridge': [config['bridge']],
                    'production_placement': [str(workspace / ('alerttoast/Package.swift' if platform == 'ios' else 'reply/Reply/app/build.gradle.kts'))],
                }
                config['source_review_store'] = str(review_base / 'source')
                config['review_store'] = str(review_base / 'images')
                if platform == 'ios':
                    for key in ['coverage_domain_ref', 'coverage_provider_ref']:
                        item = domains['tasks'][task_id][key]
                        assert digest(load(item['path'])) == item['sha256']
                        config[key] = copy.deepcopy(item)
                else:
                    config.pop('coverage_domain_ref', None)
                    config.pop('coverage_provider_ref', None)
                if arm == 'B':
                    config['platform_source_roots'] = {'ios': [config['source_roots'][0]], 'android': [config['source_roots'][1]]}
                    config['workflow'] = {'root': str(base / 'hidden-workflow')}
                else:
                    config.pop('platform_source_roots', None)
                    config.pop('workflow', None)
                assert config['resources']['max_simulators'] == 1
                assert all(config[key] == original[key] for key in SEMANTIC)
                assert config.get('capture_validity_ref') == original.get('capture_validity_ref')
                assert 'pool' not in config['resources']
                context_roots = [config['source_review_store'], config['review_store']]
                if arm == 'B':
                    context_roots.append(config['workflow']['root'])
                assert all(not Path(v).exists() or not any(Path(v).iterdir()) for v in context_roots)
                save(path, config)
                pin = {'config': ref(path), 'source_manifest': ref(source_manifest), 'resource_root': config['resources']['root'], 'source_roots': config['source_roots']}
                if arm == 'I':
                    initial_pins[task_id][platform] = pin
                profiles[task_id].setdefault(arm, {})[platform] = {
                    **pin, 'authored_private_profile': ref(authored_path),
                    'changed_physical_fields': sorted(k for k in set(original) | set(config) if original.get(k) != config.get(k)),
                    'immutable_semantic_fields_equal': True, 'capture_adoption_approved': bool(config.get('capture_validity_ref')),
                    'context_roots': context_roots,
                }
    initial_seal = root / 'cache/business/initial-reference/PREPARATION-SEAL.json'
    save(initial_seal, {'version': 1, 'kind': 'canonical-initial-reference-preparation', 'tasks': initial_pins})
    output = root / 'operators/cohort2/coordination/EVALUATION-PREPARATION.json'
    save(output, {'version': 1, 'kind': 'independent-profile-physical-binding-preparation', 'at_unix': time.time(),
                  'cohort': ref(run / 'COHORT-SEAL.json'), 'domain_admission': ref(args.domain_admission),
                  'initial_preparation_seal': ref(initial_seal), 'profiles': profiles,
                  'scope': 'Exact authored private contracts, new review/workflow contexts, unchanged final source or verified genuine initial source; no SDK or product/quality verdict. No capture-validity policy added.'})
    print(json.dumps({'preparation': ref(output), 'initial_preparation_seal': ref(initial_seal), 'profile_count': 30, 'native_executed': False}))


if __name__ == '__main__':
    main()
