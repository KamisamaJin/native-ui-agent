"""Explicit approved original-packet adoption; never relabel reuse as a new run."""
import hashlib
import math
import os
from pathlib import Path
import plistlib
import subprocess
import time
import design_contract as d
import source_identity


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def host_identity(config, platform):
    """Current installed toolchain version identity, not a binary attestation."""
    options = config['native_options']
    files = []
    result = {'platform': platform}
    if platform == 'ios':
        developer = Path(options.get('developer-dir', '/Applications/Xcode.app/Contents/Developer')).resolve()
        for name in ['version.plist', 'Info.plist']:
            p = developer.parent / name
            if p.is_file(): files.append(p)
        runtime = config.get('resources', {}).get('ios', {}).get('runtime')
        if runtime:
            env = dict(os.environ, DEVELOPER_DIR=str(developer))
            r = subprocess.run(['xcrun', 'simctl', 'list', 'runtimes', '--json'], env=env, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
            rows = [v for v in d.strict_json(r.stdout)['runtimes'] if v['identifier'] == runtime]
            if len(rows) != 1 or not rows[0].get('isAvailable', False):
                raise ValueError('Exact installed runtime identity unavailable')
            result['runtime'] = {k: rows[0].get(k) for k in ['identifier', 'version', 'buildversion', 'bundlePath']}
    else:
        if options.get('java-home'):
            files.append(Path(options['java-home']) / 'release')
        if options.get('android-sdk'):
            sdk = Path(options['android-sdk'])
            for pattern in ['platforms/*/source.properties', 'build-tools/*/source.properties', 'platform-tools/source.properties']:
                files.extend(sdk.glob(pattern))
    result['version_files'] = {str(p.resolve()): sha(p) for p in sorted(set(files)) if p.is_file()}
    return result


def build_dependencies(config, platform):
    """Include project inputs outside declared production roots; omit only outputs."""
    options = config['native_options']
    project = options.get('package' if platform == 'ios' else 'project')
    extra = config.get('dependency_files', {})
    if not isinstance(extra, dict) or set(extra) - {'ios', 'android', 'shared'}:
        raise ValueError('Known per-platform explicit dependency files required')
    found = {}
    for key in [platform, 'shared']:
        if not isinstance(extra.get(key, []), list): raise ValueError('Dependency file list required')
        for item in extra.get(key, []):
            p = Path(item).resolve(); found[str(p)] = sha(p)
    if not project:
        return found
    project = Path(project).resolve()
    roots = [Path(v).resolve() for v in config['source_roots']]
    ignored = {'.git', '.build', '.gradle', '.kotlin', 'build', 'DerivedData', '__pycache__', '.idea', '.vscode', 'xcuserdata'}
    names_of_inputs = {'Package.swift', 'Package.resolved', 'gradle.properties', 'local.properties', 'gradle.lockfile',
                       'gradle-wrapper.properties', 'gradle-wrapper.jar', 'verification-metadata.xml', 'Info.plist', 'project.pbxproj'}
    for base, dirs, names in os.walk(project, followlinks=False):
        dirs[:] = [v for v in dirs if v not in ignored and not (Path(base) / v).is_symlink()
                   and not any((Path(base) / v).resolve() == r for r in roots)]
        for name in names:
            p = Path(base) / name
            relative = p.relative_to(project)
            build_input = (name in names_of_inputs or name.endswith(('.gradle', '.gradle.kts', '.xcconfig', '.xcscheme'))
                           or (name.endswith('.toml') and 'gradle' in relative.parts)
                           or relative.parts[0] in {'buildSrc', 'build-logic'})
            if build_input and not any(p == r or p.is_relative_to(r) for r in roots):
                if p.is_symlink(): raise ValueError('Build input symlink needs an explicit dependency provider')
                found[str(p.relative_to(project))] = sha(p)
    return found


def context(config, platform):
    files = {key: sha(config[key]) for key in ['plan', 'design_lock', 'fixtures', 'bridge', 'routes', 'environment']}
    if config.get('policy'):
        files['policy'] = sha(config['policy'])
    root = Path(__file__).resolve().parents[1]
    tools = {str(p.relative_to(root)): sha(p) for folder, suffix in [('scripts', '*.py'), ('assets/ios-observer', '*.swift'), ('assets/android-observer', '*.kt')]
             for p in sorted((root / folder).glob(suffix))}
    options = {k: v for k, v in config['native_options'].items() if k != 'build-cache'}
    return {'version': 1, 'platform': platform, 'files': files,
            'design_sha256': config['design_sha256'], 'routes_sha256': config['routes_sha256'],
            'environment_sha256': config['environment_sha256'], 'policy_sha256': config.get('policy_sha256'),
            'launch_ref': config['launch_ref'], 'source_model': source_identity.model(config, platform),
            'native_options': options, 'tools': tools, 'capture_validity_ref': config.get('capture_validity_ref'),
            'host_identity': host_identity(config, platform), 'build_dependencies': build_dependencies(config, platform)}


def approved_policy(config, lock):
    ref = config.get('capture_validity_ref')
    if not ref:
        return None
    if set(ref) != {'source', 'pointer'} or d.digest(lock) != config['design_sha256']:
        raise ValueError('Capture validity needs a pinned independent source reference')
    value = d.pointer(lock['sources'][ref['source']]['document'], ref['pointer'])
    if (not isinstance(value, dict) or set(value) != {'scope', 'max_age_seconds', 'reset', 'external_state'}
            or value['scope'] != 'deterministic_component_fixture'
            or value['reset'] != 'fresh_native_fixture'
            or value['external_state'] != 'all_dependencies_pinned'
            or type(value['max_age_seconds']) is not int or not 1 <= value['max_age_seconds'] <= 3600):
        raise ValueError('Unsupported or unbounded approved capture validity')
    return value


def assess(config, path, expected_sha, *, captured_context=None, now=None):
    """Identity rejection is not a fabricated product failure; caller reacquires."""
    path = Path(path).resolve()
    if sha(path) != expected_sha:
        raise ValueError('Original capture receipt changed')
    receipt = d.load(path)
    lock = d.load(Path(config['design_lock']))
    policy = approved_policy(config, lock)
    proof = {'version': 1, 'eligible': False, 'original_capture': {'path': str(path), 'sha256': expected_sha},
             'checked_at_unix': time.time() if now is None else now,
             'native_executed': False, 'reason': 'Independent deterministic reuse policy is absent'}
    if policy is None:
        return proof
    platform = d.load(Path(config['plan']))['design_contract']['platform']
    actual_context = context(config, platform)
    proof.update(context_sha256=d.digest(actual_context), approved_policy=policy)
    if captured_context != actual_context:
        proof['reason'] = 'Source-independent capture context differs or is not registered'
        return proof
    if (receipt.get('capture_context_sha256') != d.digest(captured_context)
            or d.load(path.parent / 'capture-context.json') != captured_context):
        raise ValueError('Original capture context file/receipt binding changed')
    at = receipt.get('finishedAtUnix')
    if (type(at) not in {int, float} or not math.isfinite(at)
            or type(proof['checked_at_unix']) not in {int, float} or not math.isfinite(proof['checked_at_unix'])):
        raise ValueError('Finite original capture and current timestamps required')
    age = proof['checked_at_unix'] - at
    proof['age_seconds'] = age
    if age < 0 or age > policy['max_age_seconds']:
        proof['reason'] = 'Original capture is future-dated or expired'
        return proof
    if (receipt.get('status') != 'verified_capture' or receipt.get('native_exit_code') != 0
            or receipt.get('scope') != 'full' or not receipt.get('coverage_satisfied')
            or receipt.get('environment_status') != 'P' or receipt.get('evidence_error')):
        proof['reason'] = 'A complete successful full native/environment packet is required'
        return proof
    source_identity.verify_model(config, receipt, path.parent, platform)
    before = d.load(path.parent / 'source-before.json')
    if source_identity.fingerprint(config, platform) != before:
        proof['reason'] = 'Actual platform production dependencies changed'
        return proof
    if receipt.get('reset_contract') != 'fresh_native_fixture':
        proof['reason'] = 'Actual original collector reset evidence is absent'
        return proof
    proof.update(eligible=True, reason='Original full packet remains current under independently approved validity')
    return proof
