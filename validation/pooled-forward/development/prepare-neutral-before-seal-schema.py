#!/usr/bin/env python3
"""Resolve sealed neutral ABI/config inputs without selecting any oracle value."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

R = Path(__file__).resolve().parent
sys.path.insert(0, str(R / 'baseline-v12.6/scripts'))
import design_contract as d


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f: f.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['workspace', 'resource-root', 'workflow-root', 'stores', 'profiles']:
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--variant', choices=['normal', 'repair-control'], default='normal')
    a = p.parse_args(); w = a.workspace.resolve(); profiles = a.profiles.resolve()
    fixture = R / 'qualification/spec/modular-fixture'
    design = R / 'qualification/neutral-design/executable-profile'
    for file in [design / 'SEAL.json', fixture / 'MODULAR-SEAL.json']:
        value = d.load(file)
        for relative, entry in value['files'].items():
            wanted = entry if isinstance(entry, str) else entry['sha256']
            assert sha(file.parent / relative) == wanted, str(file.parent / relative)
    shutil.copytree(R / 'cache/hosts', w, ignore=shutil.ignore_patterns('.git', 'build', '.gradle', '.kotlin', '.build', '__pycache__'))
    ownership = d.load(fixture / 'OWNERSHIP.json')['platforms']
    components = {}; bridges = {}
    for pl in ['ios', 'android']:
        entry = ownership[pl]
        host = w / ('alerttoast' if pl == 'ios' else 'reply/Reply')
        source = fixture / entry['production_artifact']['path']
        if a.variant == 'repair-control': source = fixture / 'repair-control' / entry['production_artifact']['path']
        target = host / entry['production_install_path']; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
        components[pl] = target
        bridge = w / 'bridges' / ('ObserverBridge.swift' if pl == 'ios' else 'ObserverBridge.kt')
        bridge.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(fixture / entry['bridge_artifact']['path'], bridge)
        assert sha(bridge) == entry['bridge_artifact']['sha256']; bridges[pl] = bridge
    roots = [str(w / 'alerttoast/Sources'), str(w / 'reply/Reply/app/src/main')]
    approval = d.load(design / 'approval.json')
    lock_sha = approval['canonical_sha256']['design_lock']
    assert d.digest(d.load(design / 'approved-lock.json')) == lock_sha
    for case in ['ios-cold', 'ios-warm', 'android']:
        pl = 'android' if case == 'android' else 'ios'
        resources = d.load(design / 'resources.json'); resources['root'] = str(a.resource_root.resolve() / pl)
        environment = design / ('environment.' + pl + '.json')
        config = {'plan': str(design / 'prepared' / case / 'plan.json'),
                  'design_lock': str(design / 'approved-lock.json'), 'design_sha256': lock_sha,
                  'routes': str(design / 'routes.json'), 'routes_sha256': approval['canonical_sha256']['routes'],
                  'fixtures': str(design / 'fixtures' / (case + '.json')), 'bridge': str(bridges[pl]),
                  'launch_ref': {'source': 'reference', 'pointer': '/launch/' + case},
                  'source_roots': roots, 'platform_source_roots': {'ios': [roots[0]], 'android': [roots[1]]},
                  'dependency_files': {'android': [str(w / 'reply/Reply/.native-ui/java-desktop.jar')]},
                  'policy': str(design / 'policy.json'), 'policy_sha256': approval['canonical_sha256']['policy'],
                  'environment': str(environment), 'environment_sha256': approval['canonical_sha256']['environment_' + pl],
                  'responsibility_ref': {'source': 'reference', 'pointer': '/responsibilities'},
                  'capture_validity_ref': {'source': 'reference', 'pointer': '/capture_validity'},
                  'evidence_subjects': {'thin-bridge': [str(bridges[pl])], 'probe-component': [str(components[pl])]},
                  'source_review_store': str(a.stores.resolve() / pl / 'source'),
                  'review_store': str(a.stores.resolve() / pl / 'images'),
                  'workflow': {'root': str(a.workflow_root.resolve())}, 'resources': resources,
                  'native_options': {'package': str(w / 'alerttoast'), 'simulator': 'managed',
                                     'developer-dir': '/Applications/Xcode.app/Contents/Developer'} if pl == 'ios' else
                                    {'project': str(w / 'reply/Reply'), 'java-home': '/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home',
                                     'android-sdk': '/Users/rex/Library/Android/sdk'}}
        save(profiles / (case + '.json'), config)
    native_files = {str(p.relative_to(w)): sha(p) for root in map(Path, roots) for p in sorted(root.rglob('*')) if p.is_file()}
    save(profiles / 'ADMISSION.json', {'at_unix': time.time(), 'variant': a.variant,
         'design_approval_sha256': sha(design / 'approval.json'), 'design_seal_sha256': sha(design / 'SEAL.json'),
         'modular_fixture_seal_sha256': sha(fixture / 'MODULAR-SEAL.json'), 'production_files': native_files,
         'bridges': {pl: {'path': str(v), 'sha256': sha(v)} for pl, v in bridges.items()},
         'configs': {p.name: sha(p) for p in sorted(profiles.glob('*.json'))},
         'scope': 'Pre-native concrete integration; expectations, native coverage, actions and approved policy are unchanged. No native or business result.'})
    print(json.dumps({'workspace': str(w), 'profiles': str(profiles), 'variant': a.variant}))


if __name__ == '__main__': main()
