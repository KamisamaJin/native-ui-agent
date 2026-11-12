"""Explicit approved original-packet adoption; never relabel reuse as a new run."""
import hashlib
import math
import os
from pathlib import Path
import plistlib
import platform as host_platform
import re
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
    result = {'platform': platform, 'host_system': host_platform.platform(), 'host_architecture': host_platform.machine()}
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


def environment_dependencies(config, platform, environ=None):
    """Pin effective selectors without persisting their potentially secret values.

    Conventional selectors are a floor, not arbitrary build-script discovery.
    Integrations declare additional names under dependency_environment.
    """
    env = dict(os.environ if environ is None else environ)
    extra = config.get('dependency_environment', {})
    if not isinstance(extra, dict) or set(extra) - {'ios', 'android', 'shared'}:
        raise ValueError('Known per-platform dependency environment names required')
    names = {'LANG', 'LC_ALL', 'TZ'}
    names.update({'DEVELOPER_DIR', 'TOOLCHAINS', 'SWIFT_EXEC', 'XCODE_XCCONFIG_FILE', 'SDKROOT'} if platform == 'ios' else
                 {'JAVA_HOME', 'ANDROID_HOME', 'ANDROID_SDK_ROOT', 'COMPOSE_SNAPSHOT_ID',
                  'JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS', 'JDK_JAVA_OPTIONS', 'GRADLE_OPTS', 'GRADLE_USER_HOME'})
    if platform == 'android': names.update(k for k in env if k.startswith('ORG_GRADLE_PROJECT_'))
    for group in [platform, 'shared']:
        values = extra.get(group, [])
        if not isinstance(values, list) or any(not isinstance(n, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', n) for n in values):
            raise ValueError('Explicit dependency environment variable names required')
        names.update(values)
    options = config['native_options']
    overrides = [('developer-dir', 'DEVELOPER_DIR')] if platform == 'ios' else [('java-home', 'JAVA_HOME'), ('android-sdk', 'ANDROID_HOME')]
    for key, name in overrides:
        if options.get(key) is not None: env[name] = str(options[key])
    return {name: {'present': name in env, 'sha256': hashlib.sha256(env[name].encode()).hexdigest() if name in env else None}
            for name in sorted(names)}


def build_context(value):
    """Compilation inputs only: changing caller fixtures cannot force a rebuild."""
    keys = ['platform', 'native_options', 'tools', 'host_identity', 'build_dependencies', 'dependency_environment']
    return {**{k: value[k] for k in keys}, 'bridge_sha256': value['files']['bridge']}


def context(config, platform):
    files = {key: sha(config[key]) for key in ['plan', 'design_lock', 'fixtures', 'bridge', 'routes', 'environment']}
    if config.get('policy'):
        files['policy'] = sha(config['policy'])
    root = Path(__file__).resolve().parents[1]
    tools = {str(p.relative_to(root)): sha(p) for folder, suffix in [('scripts', '*.py'), ('assets/ios-observer', '*.swift'), ('assets/android-observer', '*.kt')]
             for p in sorted((root / folder).glob(suffix))}
    options = {k: v for k, v in config['native_options'].items() if k != 'build-cache'}
    domain = None
    if config.get('coverage_domain_ref'):
        import coverage_domain
        domain = {'policy_sha256': d.digest(coverage_domain.policy(coverage_domain.pinned(config['coverage_domain_ref']))),
                  'provider_sha256': d.digest(coverage_domain.pinned(config.get('coverage_provider_ref')))}
    return {'version': 2, 'platform': platform, 'files': files, 'coverage_domain_policy':domain,
            'design_sha256': config['design_sha256'], 'routes_sha256': config['routes_sha256'],
            'environment_sha256': config['environment_sha256'], 'policy_sha256': config.get('policy_sha256'),
            'launch_ref': config['launch_ref'], 'source_model': source_identity.model(config, platform),
            'native_options': options, 'tools': tools, 'capture_validity_ref': config.get('capture_validity_ref'),
            'host_identity': host_identity(config, platform), 'build_dependencies': build_dependencies(config, platform),
            'dependency_environment': environment_dependencies(config, platform)}


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
    if not receipt.get('packet_files'):
        proof['reason'] = 'Original complete native provenance inventory is absent'
        return proof
    import execution_plan
    execution_plan.verify_packet_files(receipt, path.parent)
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
    from resource_manager import lease_clock, boot_identity
    observed_clock = receipt.get('finishedLeaseClock')
    if (receipt.get('host_boot_id') != boot_identity() or type(observed_clock) not in {int, float}
            or not math.isfinite(observed_clock)):
        proof['reason'] = 'Original capture shared-clock/host-boot validity is unavailable'
        return proof
    elapsed = lease_clock() - observed_clock
    proof['monotonic_age_seconds'] = elapsed
    if elapsed < 0 or elapsed > policy['max_age_seconds']:
        proof['reason'] = 'Original capture is outside its shared monotonic validity window'
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
    if config.get('coverage_domain_ref'):
        import coverage_domain
        try: coverage_domain.prepare(config,d.load(Path(config['plan'])),lock)
        except coverage_domain.DomainReviewRequired:
            proof['reason'] = 'Current source lacks its required independent coverage-domain approval'
            return proof
    if receipt.get('reset_contract') != 'fresh_native_fixture':
        proof['reason'] = 'Actual original collector reset evidence is absent'
        return proof
    proof.update(eligible=True, reason='Original full packet remains current under independently approved validity')
    return proof
