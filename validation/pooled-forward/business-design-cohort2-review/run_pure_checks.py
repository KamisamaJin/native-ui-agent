#!/usr/bin/env python3
"""Independent, pure replay; writes only this review directory. Never runs a SDK."""
import concurrent.futures
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
R = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward')
C = R / 'business-design-cohort2'
O = R / 'business-design-cohort2-review'
SEAL = 'f0d623acb5abb528536e4ac126ecacac020dd835bb6f784f73fe3b1c1245930d'
MAPPING = '8a498576e7c7397ad783fa5c6038496e901e1d44eaa6965a3db15a9c8785652e'

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()

def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()

def digest(value):
    return sha_bytes(canonical(value))

def load(path):
    return json.loads(Path(path).read_text())

def save(path, value):
    path = Path(path)
    assert path.is_relative_to(O)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def snapshot_sources():
    paths = [R / 'design_capability_preflight.py', R / 'operators/design-capability-preflight-freeze.json']
    for arm in ['candidate-v13.9', 'baseline-v12.6-common-6']:
        for folder in ['scripts', 'references', 'assets']:
            paths += [p for p in (R / arm / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    return {str(p.relative_to(R)): sha_bytes(p.read_bytes()) for p in sorted(paths)}

def identity_check():
    assert sha_bytes((C / 'SEAL.sha256').read_bytes()) == SEAL
    lines = (C / 'SEAL.sha256').read_text().splitlines()
    files = {}
    errors = []
    for line in lines:
        expected, relative = line.split('  ', 1)
        p = C / relative
        assert p.resolve().is_relative_to(C)
        actual = sha_bytes(p.read_bytes())
        files[relative] = actual
        if actual != expected:
            errors.append({'path': relative, 'expected': expected, 'actual': actual})
    assert len(files) == len(lines) == 829
    existing = {str(p.relative_to(C)) for p in C.rglob('*') if p.is_file()}
    unlisted = sorted(existing - set(files))
    assert unlisted == ['SEAL-IDENTITY.json', 'SEAL.sha256'], unlisted
    assert not errors, errors
    mapping = load(C / 'APPROVAL-MAPPING.json')
    assert digest(mapping) == MAPPING
    assert len(mapping['profiles']) == 20
    return {'passed': True, 'inventory_sha256': SEAL, 'inventory_count': len(files), 'unlisted_seal_metadata': unlisted,
            'mapping_canonical_sha256': MAPPING, 'files': files}

def command(argv, receipt_path):
    argv = [str(a) for a in argv]
    assert argv[0] == sys.executable and argv[1] == '-B'
    allowed_scripts = [R / a / 'scripts' for a in ['candidate-v13.9', 'baseline-v12.6-common-6']]
    script = Path(argv[2]).resolve()
    allowed = script == R / 'design_capability_preflight.py' or script in [C / 'scripts/admit_profile.py', C / 'scripts/native_entry.py']
    allowed |= any(script.is_relative_to(s) and script.name in {'design_contract.py', 'review_contract.py', 'requirement_routes.py', 'execution_plan.py', 'evidence_responsibility.py'} for s in allowed_scripts)
    assert allowed, script
    assert '--run' not in argv
    if '--output' in argv:
        assert Path(argv[argv.index('--output') + 1]).is_relative_to(O)
    result = subprocess.run(argv, capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    receipt = {'argv': argv, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr,
               'native_execution': False}
    save(receipt_path, receipt)
    return receipt

def replay_profile(arm, profile_id, profile):
    source = C / Path(profile['profile_path']).parent
    out = O / 'pure-rebuild' / arm / profile_id
    replacements = {}
    results = []
    originals = []
    for stage in ['seal', 'compile', 'catalog', 'routes', 'execution', 'responsibility']:
        found = list((C / 'pure-receipts').glob('*-' + profile_id + '-' + stage + '.json'))
        assert len(found) == 1, found
        original = load(found[0])
        originals.append(str(found[0].relative_to(C)))
        argv = original['argv'][:]
        argv[0] = sys.executable
        argv[2] = str(R / arm / 'scripts' / Path(argv[2]).name)
        position = argv.index('--output') + 1
        old_output = argv[position]
        relative = Path(old_output).relative_to(source)
        new_output = out / relative
        argv = [replacements.get(a, a) for a in argv]
        argv[position] = str(new_output)
        new_output.parent.mkdir(parents=True, exist_ok=True)
        result = command(argv, out / 'receipts' / (stage + '.json'))
        assert result['exit_code'] == 0, (profile_id, arm, stage, result)
        pairs = []
        if Path(old_output).is_dir():
            pairs = [(p, new_output / p.relative_to(old_output)) for p in Path(old_output).rglob('*') if p.is_file()]
        else:
            pairs = [(Path(old_output), new_output)]
        for old, new in pairs:
            assert load(old) == load(new), (arm, profile_id, stage, 'changed rebuild', old, new)
            replacements[str(old)] = str(new)
        results.append({'stage': stage, 'exit_code': result['exit_code'], 'exact_rebuild': True,
                        'files': [{'authored': str(a.relative_to(C)), 'rebuilt': str(b.relative_to(O)),
                                   'file_sha256': sha_bytes(b.read_bytes()), 'canonical_sha256': digest(load(b))} for a, b in pairs]})
        replacements[old_output] = str(new_output)
    config = load(C / profile['profile_path'])
    assert load(config['plan']) == load(out / 'generated/plan.json')
    assert config['design_sha256'] == digest(load(out / 'lock.json'))
    return {'arm': arm, 'profile_id': profile_id, 'passed': True, 'same_active_config_plan': True, 'stages': results,
            'original_receipts_read': originals}

def shared_profile(arm, profile_id, profile):
    output = O / 'shared-preflight' / arm / profile_id
    result = command([sys.executable, '-B', R / 'design_capability_preflight.py', '--skill', R / arm,
                      '--config', C / profile['profile_path'], '--output', output],
                     O / 'shared-preflight-receipts' / arm / (profile_id + '.json'))
    value = load(output / 'RESULT.json')
    assert result['exit_code'] == 0 and value['passed'], (profile_id, arm, value)
    assert not value['mandatory_capability_issues'] and not value['must_route_gaps'] and not value['unowned_assertions']
    claims = load(output / 'responsibility-capabilities.json')
    return {'arm': arm, 'profile_id': profile_id, 'passed': True, 'result_sha256': sha_bytes((output / 'RESULT.json').read_bytes()),
            'result_path': str((output / 'RESULT.json').relative_to(O)), 'truth_unassessed': value['evidence_truth_still_unassessed']}

def guarded_profiles(mapping):
    spec = importlib.util.spec_from_file_location('independent_profile_admit', C / 'scripts/admit_profile.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    results = []
    for profile_id, profile in mapping['profiles'].items():
        config = load(C / profile['profile_path'])
        accepted = module.verify(C, mapping, MAPPING, profile['intended_platform'], profile_id, config)
        mutations = []
        cases = []
        opposite = 'ios' if profile['intended_platform'] == 'android' else 'android'
        cases.append(('actual-opposite-platform', config, opposite, MAPPING))
        for field in ['design_lock', 'plan', 'policy', 'routes', 'environment', 'fixtures', 'bridge']:
            other = next(p for p in mapping['profiles'].values() if p['intended_platform'] != profile['intended_platform'] and p['task'] == profile['task'] and p['family'] == profile['family'])
            changed = copy.deepcopy(config)
            changed[field] = str(C / other['paths'][field])
            cases.append(('wrong-' + field + '-path', changed, profile['intended_platform'], MAPPING))
        for field in ['design_sha256', 'policy_sha256', 'routes_sha256', 'environment_sha256']:
            changed = copy.deepcopy(config); changed[field] = '0' * 64
            cases.append(('wrong-' + field, changed, profile['intended_platform'], MAPPING))
        for field in ['launch_ref', 'responsibility_ref']:
            changed = copy.deepcopy(config); changed[field]['pointer'] = '/wrong'
            cases.append(('wrong-' + field, changed, profile['intended_platform'], MAPPING))
        cases.append(('wrong-canonical-approval-mapping', config, profile['intended_platform'], '0' * 64))
        for name, changed, platform, trusted in cases:
            try:
                module.verify(C, mapping, trusted, platform, profile_id, changed)
            except ValueError as e:
                mutations.append({'mutation': name, 'rejected': True, 'error': str(e)})
            else:
                raise AssertionError((profile_id, name, 'guard accepted mutation'))
        try:
            module.verify(C, mapping, MAPPING, profile['intended_platform'], profile_id, config, runtime=True)
        except ValueError as e:
            mutations.append({'mutation': 'placeholder-runtime', 'rejected': True, 'error': str(e)})
        else:
            raise AssertionError('placeholder runtime permitted')
        # Exercise the mandatory external entry itself. Placeholder validation is
        # first; a deliberately absent review file cannot be reached, nor SDK code.
        receipt = command([sys.executable, '-B', C / 'scripts/native_entry.py', '--root', C,
                           '--approval', C / 'APPROVAL-MAPPING.json', '--approval-sha256', MAPPING,
                           '--platform', profile['intended_platform'], '--profile-id', profile_id,
                           '--config', C / profile['profile_path'], '--review-receipt', O / 'DOES-NOT-EXIST',
                           '--output', O / 'FORBIDDEN-NATIVE-OUTPUT' / profile_id],
                          O / 'guard-native-entry-rejections' / (profile_id + '.json'))
        assert receipt['exit_code'] != 0 and 'Pure placeholders cannot launch native work' in receipt['stderr']
        assert not (O / 'FORBIDDEN-NATIVE-OUTPUT').exists()
        results.append({'profile_id': profile_id, 'accepted': accepted, 'negative_cases': mutations,
                        'external_entry_placeholder_rejected_before_sdk': True})
    return {'passed': True, 'profiles': results, 'positive_count': len(results),
            'negative_count': sum(len(r['negative_cases']) for r in results), 'external_entry_rejections': len(results)}

def main():
    identity = identity_check()
    save(O / 'identity-check.json', identity)
    before = snapshot_sources()
    save(O / 'frozen-public-before.json', before)
    mapping = load(C / 'APPROVAL-MAPPING.json')
    guards = guarded_profiles(mapping)
    save(O / 'profile-guard-checks.json', guards)
    jobs = [('rebuild', arm, pid, p) for arm in ['candidate-v13.9', 'baseline-v12.6-common-6'] for pid, p in mapping['profiles'].items()]
    jobs += [('shared', arm, pid, p) for arm in ['candidate-v13.9', 'baseline-v12.6-common-6'] for pid, p in mapping['profiles'].items()]
    rows, errors = [], []
    def run(job):
        kind, arm, pid, profile = job
        try:
            value = replay_profile(arm, pid, profile) if kind == 'rebuild' else shared_profile(arm, pid, profile)
            return {'kind': kind, **value}
        except Exception as error:
            return {'kind': kind, 'arm': arm, 'profile_id': pid, 'passed': False,
                    'error': repr(error), 'traceback': traceback.format_exc()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(run, jobs):
            rows.append(result)
            if not result['passed']: errors.append(result)
    after = snapshot_sources()
    assert before == after, 'Frozen public source mutation'
    assert identity_check() == identity, 'Cohort input mutation'
    save(O / 'PURE-CHECKS.json', {'passed': not errors, 'rows': rows, 'errors': errors,
         'rebuild_count': sum(r['kind'] == 'rebuild' and r['passed'] for r in rows),
         'shared_preflight_count': sum(r['kind'] == 'shared' and r['passed'] for r in rows),
         'frozen_public_unchanged': True, 'cohort_unchanged': True, 'native_executions': 0, 'source_approvals': 0})
    print(json.dumps({'passed': not errors, 'jobs': len(rows), 'errors': errors[:3]}))
    return 0 if not errors else 1

if __name__ == '__main__':
    raise SystemExit(main())
