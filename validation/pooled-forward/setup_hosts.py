#!/usr/bin/env python3
"""Pinned stock native hosts plus test dependencies; no business implementations."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import zipfile

R = Path(__file__).resolve().parent
PINS = {'reply': ('https://github.com/android/compose-samples.git', '53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79'),
        'alerttoast': ('https://github.com/elai950/AlertToast.git', '76a1c1793cd3443001c20c6033beb84453b25d9f')}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--java-home', type=Path, required=True)
    p.add_argument('--android-sdk', type=Path, required=True)
    a = p.parse_args(); root = a.workspace.resolve(); root.mkdir(parents=True, exist_ok=False)
    commands = []
    def run(argv, cwd=None):
        began = time.time(); r = subprocess.run(list(map(str, argv)), cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        commands.append({'argv': list(map(str, argv)), 'cwd': str(cwd) if cwd else None, 'started_at_unix': began,
                         'finished_at_unix': time.time(), 'exit_code': r.returncode, 'output': r.stdout})
        (root / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if r.returncode: raise RuntimeError('Pinned host setup failed; original commands retained')
        return r.stdout.strip()
    for name, (url, pin) in PINS.items():
        target = root / name
        run(['git', 'init', '-q', target]); run(['git', 'remote', 'add', 'origin', url], target)
        run(['git', 'fetch', '--quiet', '--depth', '1', 'origin', pin], target)
        run(['git', 'checkout', '--quiet', '--detach', 'FETCH_HEAD'], target)
        assert run(['git', 'rev-parse', 'HEAD'], target) == pin
    host_patch = R.parent / 'blind-comparison/harness/android-host.patch'
    run(['git', 'apply', '--check', host_patch], root / 'reply'); run(['git', 'apply', host_patch], root / 'reply')
    project = root / 'reply/Reply'
    (project / 'local.properties').write_text('sdk.dir=' + str(a.android_sdk.resolve()) + '\n')
    dest = project / '.native-ui/java-desktop.jar'; dest.parent.mkdir()
    source = a.java_home.resolve() / 'jmods/java.desktop.jmod'
    # Deterministic private build dependency, reconstructed from installed JDK.
    # It is not archived/published as original MIT code or an SDK distribution.
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(dest, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(src.namelist()):
            if not name.startswith('classes/') or name == 'classes/': continue
            entry = zipfile.ZipInfo(name[len('classes/'):], date_time=(2020, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED; entry.external_attr = (0o40755 if name.endswith('/') else 0o100644) << 16
            archive.writestr(entry, src.read(name))
    with (project / 'app/build.gradle.kts').open('a') as stream:
        stream.write('\ndependencies { testImplementation(files(rootProject.file(".native-ui/java-desktop.jar"))) }\n')
    receipt = {'at_unix': time.time(), 'pins': {k: {'url': v[0], 'revision': v[1]} for k, v in PINS.items()},
               'android_host_patch_sha256': sha(host_patch), 'jdk_module_sha256': sha(source), 'private_desktop_jar_sha256': sha(dest),
               'scope': 'Common pinned stock/source/test-host preparation, not treatment, native UI or business-quality credit. No unused iOS SnapshotTesting dependency added.'}
    (root / 'setup.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__': main()
