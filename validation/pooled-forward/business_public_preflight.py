#!/usr/bin/env python3
"""Validate exact admitted public runtime bindings without launching SDKs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

R = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arm', choices=['A', 'B'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(R / 'business-tools-v4'))
    import blind_study as controller
    study = controller.Study(R / 'cache/business/run-cohort2')
    first = study.manifest['tasks'][0]['arms'][args.arm]
    tool = study.manifest['tools'][first['tool']]
    sys.path.insert(0, str(Path(tool['skill_root']) / 'scripts'))
    import design_contract as design
    import evidence_responsibility
    import coverage_domain
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    with patch('subprocess.run', side_effect=AssertionError('No SDK/subprocess in public runtime binding preflight')), \
         patch('subprocess.Popen', side_effect=AssertionError('No SDK/subprocess in public runtime binding preflight')):
        for task in study.manifest['tasks']:
            arm = task['arms'][args.arm]
            study.verify_pins(task['id'], args.arm)
            for platform, path in arm['public_configs'].items():
                output = args.output / (task['id'] + '-' + platform)
                output.mkdir()
                config = controller.load(path)
                admission = study.profile_admission(task['id'], args.arm, platform, path, output / 'profile-admission.json')
                plan = controller.load(config['plan'])
                lock = controller.load(config['design_lock'])
                claims = evidence_responsibility.compile_contract(config, plan, lock)
                assert not [v for v in claims['issues'] if v['priority'] == 'must'], claims['issues']
                source = [v for v in claims['claims'] if v['method'] == 'source' and v['priority'] == 'must']
                assert len(source) == 3 and all(v['supported'] for v in source)
                domain = coverage_domain.prepare(config, plan, lock) if platform == 'ios' else None
                if domain:
                    controller.save(output / 'coverage-domain-prepared.json', domain)
                controller.save(output / 'responsibility-capabilities.json', claims)
                rows.append({'task': task['id'], 'platform': platform, 'config_sha256': controller.sha(path),
                             'actual_default_profile_admitted': admission['verdict']['status'] == 'admitted_profile',
                             'source_must_capabilities': 3, 'source_truth_approved': False, 'native_truth_approved': False,
                             'ios_exact_source_shape_prepared': bool(domain),
                             'capture_adoption_approved': bool(config.get('capture_validity_ref'))})
    controller.save(args.output / 'RESULT.json', {'kind': 'HOST_PUBLIC_RUNTIME_BINDING', 'passed': True,
                    'arm': args.arm, 'rows': rows, 'sdk_or_native_execution': False,
                    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    'scope': 'Actual default guard, immutable profile/tool pins, current installed source/bridge/shape and provider compatibility only. Runtime/behavior/style truth still pending.'})
    print(json.dumps({'passed': True, 'arm': args.arm, 'profiles': len(rows), 'sdk_or_native_execution': False}))


if __name__ == '__main__':
    main()
