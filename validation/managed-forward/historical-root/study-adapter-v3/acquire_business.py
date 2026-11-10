#!/usr/bin/env python3
"""Common study adapter. Expectations and actions come only from sealed design."""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import business

R = Path(__file__).resolve().parent
STUDY = R / 'cache/study'
sys.path.insert(0, str(R / 'candidate-v12.6/scripts'))
import resource_manager as rm


def verify_release():
    for rel, expected in business.read(R / 'RELEASE.json')['files'].items():
        if business.sha(R / rel) != expected:
            raise ValueError('Frozen business tool/method changed: ' + rel)


def verify_host(workspace, seal):
    for rel, expected in business.read(seal)['files'].items():
        path = (workspace / rel).resolve()
        if not path.is_relative_to(workspace.resolve()) or business.sha(path) != expected:
            raise ValueError('Pinned common host input changed: ' + rel)


def configuration(workspace, scope, case, platform, arm, simulator):
    approval = business.read(scope / 'approval.json')
    integration = business.read(scope / 'integration.json')
    component_files = integration['component_files'][platform]
    if isinstance(component_files, str):
        component_files = [component_files]
    if not component_files or any(not isinstance(v, str) or Path(v).is_absolute() or '..' in Path(v).parts for v in component_files):
        raise ValueError('Explicit workspace-relative component subject files required')
    compiled = scope / 'compiled' / case / platform
    prefix = STUDY / 'arms' / arm
    native = ({'package': str(workspace / 'alerttoast'), 'simulator': simulator,
               'developer-dir': '/Applications/Xcode.app/Contents/Developer'} if platform == 'ios' else
              {'project': str(workspace / 'reply/Reply'),
               'java-home': '/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home',
               'android-sdk': '/Users/rex/Library/Android/sdk'})
    if platform == 'ios' and simulator != 'managed':
        native['build-cache'] = str(prefix / 'ios-build-cache')
    value = {'plan': str(compiled / 'plan.json'), 'design_lock': str(scope / 'design-lock.json'),
             'design_sha256': approval['design_lock_sha256'], 'routes': str(scope / 'routes.json'),
             'routes_sha256': approval['routes_sha256'], 'fixtures': str(scope / 'cases' / case / 'fixtures.json'),
             'bridge': str(scope / ('Bridge.swift' if platform == 'ios' else 'ObserverBridge.kt')),
             'launch_ref': approval['launch_ref'][case][platform],
             'source_roots': [str(workspace / rel) for rel in business.ROOTS], 'native_options': native,
             'environment': str(scope / 'cases' / case / ('environment.' + platform + '.json')),
             'environment_sha256': approval['environment_sha256'][case][platform],
             'policy': str(scope / 'policy.json'), 'policy_sha256': approval['policy_sha256'],
             'review_store': str(prefix / 'reviews' / scope.name / case / platform),
             'responsibility_ref': integration['responsibility_ref'],
             'evidence_subjects': {'component': [str(workspace / rel) for rel in component_files],
                                   'bridge': [str(scope / ('Bridge.swift' if platform == 'ios' else 'ObserverBridge.kt'))]},
             'source_review_store': str(prefix / 'source-reviews' / scope.name / case / platform),
             'resources': {'root': str(prefix / 'native-resources' / platform), 'max_bytes': 20 * 2**30,
                           'min_free_bytes': 5 * 2**30, 'sample_seconds': 1, 'command_timeout_seconds': 900}}
    if platform == 'ios':
        value['resources']['ios'] = {'device_type': 'com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro',
                                     'runtime': 'com.apple.CoreSimulator.SimRuntime.iOS-26-5'}
    return value


class CommonSafety(rm.Resources):
    """Identical outer budget/backstop, not either arm's default behavior."""
    def sample(self):
        paths = [STUDY]
        for path in [*(STUDY / 'arms').glob('*/native-resources/ios/journal.json'),
                     STUDY / 'control-device/journal.json']:
            if path.is_file():
                value = business.read(path)
                if value.get('format') != rm.FORMAT:
                    raise ValueError('Foreign study journal')
                paths.extend(Path.home() / 'Library/Developer/CoreSimulator/Devices' / row['udid']
                             for row in value.get('devices', []) if row.get('udid'))
        self.borrowed_paths = paths
        return super().sample()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--scope', type=Path, required=True)
    parser.add_argument('--case', required=True)
    parser.add_argument('--platform', choices=['ios', 'android'], required=True)
    parser.add_argument('--arm', choices=['A', 'B'], required=True)
    parser.add_argument('--tool', type=Path, required=True)
    parser.add_argument('--simulator', required=True)
    parser.add_argument('--stage', choices=['initial', 'self-finals'], required=True)
    parser.add_argument('--source-seal', type=Path, required=True)
    parser.add_argument('--host-seal', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--history', type=Path)
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    started = time.time()
    verify_release()
    verify_host(args.workspace, args.host_seal)
    authorization = business.authorize(args.stage, args.workspace, args.source_seal)
    if args.scope.name == 'private' and args.stage != 'self-finals':
        raise ValueError('Hidden acquisition requires both complete final source/self-evidence cohorts')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    config = configuration(args.workspace.resolve(), args.scope.resolve(), args.case, args.platform, args.arm, args.simulator)
    business.save(output / 'config.json', config)
    argv = [sys.executable, '-B', str(args.tool.resolve() / 'scripts/ui_loop.py'), 'native',
            '--config', str(output / 'config.json'), '--output', str(output / 'cycle')]
    if args.final:
        argv.append('--final')
    if args.previous:
        argv.extend(['--previous', str(args.previous.resolve()), '--previous-sha256', business.sha(args.previous)])
    if args.history:
        argv.extend(['--history', str(args.history.resolve())])
    # The safety wrapper has no product assertions, no selectors, no state
    # selection and no per-arm cache/device cleanup policy. Both tools remain
    # complete frozen bundles. Its group budget/timeout is separately reported.
    safety = {'source_roots': config['source_roots'], 'native_options': {},
              'resources': {'root': str(STUDY / 'outer-safety' / args.arm / args.platform),
                            'max_bytes': 32 * 2**30, 'min_free_bytes': 5 * 2**30,
                            'sample_seconds': 1, 'command_timeout_seconds': 1200}}
    business.save(output / 'started.json', {'started_at_unix': started, 'authorization': authorization,
                                          'argv': argv, 'tool': str(args.tool.resolve()),
                                          'host_seal_sha256': business.sha(args.host_seal),
                                          'acquisition_adapter_sha256': business.sha(Path(__file__))})
    code = None
    try:
        with CommonSafety(safety, output / 'common-safety', final=True) as resources:
            with (output / 'controller.log').open('wb') as stream:
                code = resources.run(argv, env=dict(os.environ), stdout=stream)
    finally:
        business.save(output / 'command.json', {'argv': argv, 'started_at_unix': started,
                                               'finished_at_unix': time.time(), 'exit_code': code,
                                               'source_unchanged': business.fingerprint(args.workspace) == business.read(args.source_seal)['files'],
                                               'scope': 'Whole actual command plus identical common safety overhead. No product verdict inferred from exit status.'})
    return code


if __name__ == '__main__':
    raise SystemExit(main())
