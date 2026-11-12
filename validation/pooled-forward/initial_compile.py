#!/usr/bin/env python3
"""Compile a natural initial component and its fixed bridge; never render or test.

SDK compiler errors may be returned to the initial author before its source seal.
Both the original failed log and every subsequent attempt must remain available.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

R = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(workspace):
    roots = [workspace / 'alerttoast/Sources', workspace / 'reply/Reply/app/src/main']
    return {str(i) + '/' + p.relative_to(root).as_posix(): sha(p)
            for i, root in enumerate(roots) for p in sorted(root.rglob('*')) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--bridge-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--skill', type=Path, default=R / 'candidate-v13.9')
    parser.add_argument('--platform', choices=['ios', 'android', 'both'], default='both')
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    before = inventory(workspace)
    records = []
    for platform in (['ios', 'android'] if args.platform == 'both' else [args.platform]):
        folder = output / platform
        folder.mkdir()
        started = time.time()
        clock = time.clock_gettime(time.CLOCK_MONOTONIC)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        reserved = None
        if platform == 'ios':
            sys.path.insert(0, str(args.skill.resolve() / 'scripts'))
            import ios_observe
            project = ios_observe.generate_project(folder / 'project', args.bridge_root.resolve() / 'ObserverBridge.swift',
                                                  workspace / 'alerttoast', 'AlertToast')
            command = ['xcodebuild', 'build-for-testing', '-project', str(project), '-scheme', 'Observer',
                       '-configuration', 'Debug', '-sdk', 'iphonesimulator', '-destination',
                       'generic/platform=iOS Simulator', '-derivedDataPath', str(folder / 'DerivedData'),
                       '-resultBundlePath', str(folder / 'compile.xcresult'), 'CODE_SIGNING_ALLOWED=NO',
                       'ARCHS=arm64', 'ONLY_ACTIVE_ARCH=YES']
            env['DEVELOPER_DIR'] = '/Applications/Xcode.app/Contents/Developer'
            cwd = workspace / 'alerttoast'
            bridge = args.bridge_root.resolve() / 'ObserverBridge.swift'
        else:
            cwd = workspace / 'reply/Reply'
            reserved = cwd / 'app/src/test/java/org/nativeobserver'
            if reserved.exists():
                raise ValueError('Compile-only reserved bridge folder must be fresh')
            reserved.mkdir(parents=True)
            bridge = args.bridge_root.resolve() / 'ObserverBridge.kt'
            shutil.copy2(bridge, reserved / 'ObserverBridge.kt')
            shutil.copy2(args.skill.resolve() / 'assets/android-observer/NativeObserverTest.kt',
                         reserved / 'NativeObserverTest.kt')
            command = ['./gradlew', ':app:compileDebugUnitTestKotlin', '--console=plain', '--max-workers=2', '--no-daemon']
            env['JAVA_HOME'] = '/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home'
            env['ANDROID_HOME'] = '/Users/rex/Library/Android/sdk'
        record = {'platform': platform, 'argv': command, 'cwd': str(cwd), 'started_at_unix': started,
                  'source_before': before, 'bridge': str(bridge), 'bridge_sha256': sha(bridge),
                  'scope': 'Compiler only; no native test, UI launch, screenshot or simulator acquisition.'}
        with (folder / 'command.json').open('x') as stream:
            json.dump(record, stream, indent=2)
        try:
            with (folder / 'compiler.log').open('x') as stream:
                record['exit_code'] = subprocess.run(command, cwd=cwd, env=env, stdout=stream,
                                                     stderr=subprocess.STDOUT).returncode
        finally:
            if reserved:
                for name in ['ObserverBridge.kt', 'NativeObserverTest.kt']:
                    (reserved / name).unlink()
                reserved.rmdir()
        record.update(finished_at_unix=time.time(), wall_seconds=time.clock_gettime(time.CLOCK_MONOTONIC) - clock,
                      source_after=inventory(workspace))
        record['source_unchanged'] = record['source_before'] == record['source_after']
        with (folder / 'RESULT.json').open('x') as stream:
            json.dump(record, stream, indent=2)
        records.append(record)
    passed = all(r.get('exit_code') == 0 and r['source_unchanged'] for r in records)
    with (output / 'RESULT.json').open('x') as stream:
        json.dump({'passed': passed, 'records': records, 'no_native_test_or_render_requested': True}, stream, indent=2)
    print(json.dumps({'passed': passed, 'platforms': [{'platform': r['platform'], 'exit_code': r.get('exit_code'),
                                                    'wall_seconds': r['wall_seconds']} for r in records]}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
