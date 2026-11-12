#!/usr/bin/env python3
"""Bind admitted public designs to actual paired production/source hosts.

Only physical host/source/store/resource bindings change. Authored plan, lock,
fixtures, expected values, routes, policy, bridge and environment remain exact.
No missing capture-adoption approval is supplied by this integration utility.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

R = Path(__file__).resolve().parent
DESIGN = R / 'business-design-cohort2-v2'


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def prepare(task, arm, domain_path, provider_path):
    admission = load(R / 'operators/cohort2/INITIAL-AUTHOR-ADMISSION.json')
    case = next(v for v in admission['cases'] if v['id'] == task)
    base = R / 'cache/business' / task / arm
    workspace = base / 'workspace'
    pair = load(R / 'cache/business/initial' / task / 'source-seal/SEAL.json')
    if str(workspace) != pair['arms'][arm]['workspace']:
        raise ValueError('Actual paired workspace differs from initial seal')
    roots = [workspace / 'alerttoast/Sources', workspace / 'reply/Reply/app/src/main']
    actual = {str(i) + '/' + p.relative_to(root).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size}
              for i, root in enumerate(roots) for p in sorted(root.rglob('*')) if p.is_file()}
    if actual != pair['source_files']:
        raise ValueError('Initial arm source changed before public binding')
    profiles = {}
    for platform in ['ios', 'android']:
        original = Path(case['public_root']) / platform / 'profile.json'
        config = load(original)
        config['purpose'] = 'actual_sealed_paired_component_public_runtime'
        config['source_roots'] = list(map(str, roots))
        config['source_review_store'] = str(base / 'public-reviews' / platform / 'source')
        config['review_store'] = str(base / 'public-reviews' / platform / 'images')
        config['evidence_subjects'] = {
            'production_api': [str(workspace / ('alerttoast/Sources/AlertToast/' + case['component'] + '.swift'
                                               if platform == 'ios' else 'reply/Reply/app/src/main/java/com/example/reply/ui/components/business/' + case['component'] + '.kt'))],
            'thin_bridge': [config['bridge']],
            'production_placement': [str(workspace / ('alerttoast/Package.swift' if platform == 'ios' else 'reply/Reply/app/build.gradle.kts'))]}
        config['resources'] = {'root': str(base / 'resources' / platform), 'max_bytes': 20 * 2**30,
                               'min_free_bytes': 5 * 2**30, 'max_simulators': 1, 'sample_seconds': 2,
                               'ttl_seconds': 86400, 'command_timeout_seconds': 900,
                               'ios': {'device_type': 'com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro',
                                       'runtime': 'com.apple.CoreSimulator.SimRuntime.iOS-26-5'}}
        if platform == 'ios':
            config['native_options'] = {'package': str(workspace / 'alerttoast'), 'product': 'AlertToast',
                                        'simulator': 'managed', 'developer-dir': '/Applications/Xcode.app/Contents/Developer'}
            config['coverage_domain_ref'] = {'path': str(domain_path.resolve()), 'sha256': digest(load(domain_path))}
            config['coverage_provider_ref'] = {'path': str(provider_path.resolve()), 'sha256': digest(load(provider_path))}
        else:
            config['native_options'] = {'project': str(workspace / 'reply/Reply'),
                                        'java-home': '/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home',
                                        'android-sdk': '/Users/rex/Library/Android/sdk'}
            config['dependency_files'] = {'android': [str(workspace / 'reply/Reply/.native-ui/java-desktop.jar'),
                                                       str(workspace / 'reply/Reply/gradlew')]}
            config['dependency_environment'] = {'android': ['COMPOSE_SNAPSHOT_ID']}
        if arm == 'B':
            config['platform_source_roots'] = {'ios': [str(roots[0])], 'android': [str(roots[1])]}
            config['workflow'] = {'root': str(base / 'public-workflow')}
        elif arm != 'A':
            raise ValueError('Exact predeclared A/B binding required')
        for field in ['plan', 'design_lock', 'design_sha256', 'fixtures', 'bridge', 'launch_ref',
                      'policy', 'policy_sha256', 'routes', 'routes_sha256', 'environment',
                      'environment_sha256', 'responsibility_ref']:
            if config[field] != load(original)[field]:
                raise ValueError('Authored public input changed: ' + field)
        if config.get('capture_validity_ref') != load(original).get('capture_validity_ref'):
            raise ValueError('Integration cannot supply an unapproved reuse window')
        path = base / 'public-profiles' / (platform + '.json')
        save(path, config)
        profiles[platform] = {'path': str(path), 'sha256': sha(path), 'authored_profile_sha256': sha(original),
                              'capture_adoption_approved': bool(config.get('capture_validity_ref'))}
    save(base / 'PUBLIC-BINDING.json', {'at_unix': time.time(), 'task': task, 'arm': arm,
                                      'initial_pair_seal_sha256': sha(R / 'cache/business/initial' / task / 'source-seal/SEAL.json'),
                                      'profiles': profiles, 'native_UI_acquisitions': 0})
    return profiles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True)
    parser.add_argument('--arm', choices=['A', 'B'], required=True)
    parser.add_argument('--domain', required=True, type=Path)
    parser.add_argument('--provider', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.task, args.arm, args.domain, args.provider)))


if __name__ == '__main__':
    main()
