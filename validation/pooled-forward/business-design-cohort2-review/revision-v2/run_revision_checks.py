#!/usr/bin/env python3
"""Scoped admission of the separately sealed pre-code correction, with no SDK."""
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
OR = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward/business-design-cohort2-review')
sys.path.insert(0, str(OR))
import run_pure_checks as pure
OLD = pure.C
R = pure.R
C = R / 'business-design-cohort2-v2'
O = OR / 'revision-v2'
SEAL = '4f6d6e60331bcc58d17b30443b5f48fc1156636d82322ce7f678660e2e47d818'
MAPPING = '82b98c4d5d33699ff85de02f86b2813f9df9022fbc70680a78ac2a0058b8081f'
MAP_FILE = '904acc7f3e29fa20d96e96db2c65c2c6cb5a2c773cbf24366865a18a29e622a0'
pure.C, pure.O, pure.SEAL, pure.MAPPING = C, O, SEAL, MAPPING
load, save, digest, sha = pure.load, pure.save, pure.digest, pure.sha_bytes

def identity_check():
    assert sha((C / 'SEAL.sha256').read_bytes()) == SEAL
    assert sha((C / 'APPROVAL-MAPPING.json').read_bytes()) == MAP_FILE
    files = {}
    for line in (C / 'SEAL.sha256').read_text().splitlines():
        expected, relative = line.split('  ', 1)
        p = C / relative
        assert p.resolve().is_relative_to(C)
        actual = sha(p.read_bytes())
        assert expected == actual, relative
        assert relative not in files
        files[relative] = actual
    assert len(files) == 2108
    existing = {str(p.relative_to(C)) for p in C.rglob('*') if p.is_file()}
    assert existing - set(files) == {'SEAL-IDENTITY.json', 'SEAL.sha256'}
    assert digest(load(C / 'APPROVAL-MAPPING.json')) == MAPPING
    old = load(OR / 'identity-check.json')
    assert sha((OLD / 'SEAL.sha256').read_bytes()) == old['inventory_sha256']
    assert all(sha((OLD / p).read_bytes()) == h for p, h in old['files'].items())
    return {'passed': True, 'inventory_sha256': SEAL, 'inventory_count': 2108,
            'mapping_canonical_sha256': MAPPING, 'mapping_file_sha256': MAP_FILE,
            'original_829_file_cohort_unchanged': True, 'files': files,
            'preserved_staging_scope': 'private/_drafts identity hashes only; not selected for execution or business semantics.'}

def snapshot_sources():
    # Named pure API dependencies and explicitly authorized primary ABI sources.
    names = ['design_contract.py', 'evidence_responsibility.py', 'execution_plan.py', 'requirement_routes.py',
             'review_contract.py', 'action_guard.py', 'native_checks.py', 'observation_contract.py', 'source_identity.py',
             'native_geometry.py', 'native_pixels.py', 'native_environment.py', 'coverage_domain.py']
    paths = [R / 'design_capability_preflight.py', R / 'operators/design-capability-preflight-freeze.json']
    for arm in ['candidate-v13.9', 'baseline-v12.6-common-6']:
        paths += [R / arm / 'scripts' / n for n in names]
        paths += [R / arm / 'assets/android-observer/NativeObserverTest.kt',
                  R / arm / 'assets/ios-observer/ObserverApp.swift', R / arm / 'assets/ios-observer/CONTRACT.md']
    paths += [R / 'cache/hosts/reply/Reply/app/src/main/java/com/example/reply/ui/theme/Theme.kt']
    result = {str(p.relative_to(R)): sha(p.read_bytes()) for p in paths if p.is_file()}
    original = load(OR / 'frozen-public-before.json')
    for relative, value in result.items():
        if relative in original: assert original[relative] == value, relative
    assert result['design_capability_preflight.py'] == 'd26f767d88f53a9f1c4afa0a42ec2be76bbd4685418b0661f7060e78f24d4a83'
    return result

pure.identity_check = identity_check
pure.snapshot_sources = snapshot_sources

# This import uses the original independent evaluator read-only, now bound to the
# new explicitly authorized C/O roots. The original source and review stay sealed.
import check_business_and_scope as business
from jsonschema import Draft202012Validator

def normalize_plan(plan):
    p = copy.deepcopy(plan)
    p['design_contract']['lock_sha256'] = 'LOCK-IDENTITY'
    for assertion in p['assertions']: assertion['source'] = 'design-lock:LOCK-IDENTITY'
    return p

def bounded_revision_checks():
    rows, range_rows, abi_rows, source_citations = [], [], [], []
    mapping = load(C / 'APPROVAL-MAPPING.json')
    same_paths = ['MASTER-DENOMINATOR.json', 'MASTER-REQUIREMENT-INDEX.json', 'scripts/admit_profile.py', 'scripts/native_entry.py']
    # The semantic master index can contain no path-dependent design hash.
    for p in same_paths: assert (OLD / p).read_bytes() == (C / p).read_bytes(), p
    normative_unchanged = []
    for task in business.SPECS:
        old_public, new_public = OLD / 'public/tasks' / task, C / 'public/tasks' / task
        for name in ['DESIGN.md', 'tokens.json', 'flow.json', 'outcomes.json', 'REQUIREMENT-MAP.json',
                     'reference-blank.svg', 'reference-ready.svg', 'reference-long.svg']:
            assert (old_public / name).read_bytes() == (new_public / name).read_bytes(), (task, name)
            normative_unchanged.append('public/tasks/' + task + '/' + name)
        before, schema = load(old_public / 'fixture.schema.json'), load(new_public / 'fixture.schema.json')
        corrected = copy.deepcopy(before)
        for field, prop in corrected['properties'].items():
            if prop['type'] != 'integer': continue
            prop['minimum'] = max(prop.get('minimum', -2147483648), -2147483648)
            prop['maximum'] = min(prop.get('maximum', 2147483647), 2147483647)
            actual = schema['properties'][field]
            assert actual == prop
            fixture = load(new_public / 'ios/fixtures.json')['initial']
            validator = Draft202012Validator(schema)
            for v in [prop['minimum'], prop['maximum']]:
                assert validator.is_valid(dict(fixture, **{field: v}))
            for v in [prop['minimum'] - 1, prop['maximum'] + 1]:
                assert not validator.is_valid(dict(fixture, **{field: v}))
            range_rows.append({'task': task, 'field': field, 'minimum': prop['minimum'], 'maximum': prop['maximum'],
                               'bounded_schema_scalars_checked_only': True})
        assert schema == corrected
        api = (new_public / 'API.md').read_text()
        before_api = (old_public / 'API.md').read_text()
        kotlin = re.search(r'```kotlin\n(.*?)```', api, re.S)[1]
        swift = re.search(r'```swift\n(.*?)```', api, re.S)[1]
        before_kotlin = re.search(r'```kotlin\n(.*?)```', before_api, re.S)[1]
        before_swift = re.search(r'```swift\n(.*?)```', before_api, re.S)[1]
        assert swift == before_swift
        assert kotlin == before_kotlin.replace(': Bool', ': Boolean')
        fields = dict(re.findall(r'val (\w+): (List<String>|\w+)', kotlin))
        for key, prop in schema['properties'].items():
            assert fields[key] == {'string': 'String', 'integer': 'Int', 'boolean': 'Boolean', 'array': 'List<String>'}[prop['type']]
        # The original prose remains intact when the exact new domain paragraphs
        # and declared ABI correction are removed; no business predicate changed.
        before_brief = (old_public / 'BRIEF.md').read_text()
        new_brief = (new_public / 'BRIEF.md').read_text()
        addition = ('All Int fields are restricted to the shared signed32-bit transport domain; tighter\n'
                    'positive/nonnegative minima and portfolioScore\'s maximum100 remain normative.\n'
                    'The component compares the caller\'s revision key and never computes its successor.\n'
                    'No published rule requires an integer sum or product. The finite corpus provides\n'
                    'no blanket implementation-overflow guarantee outside its listed inputs.\n')
        assert new_brief.replace(addition, '', 1) == before_brief
        assert 'no sums or products' in api
        assert '2147483647' in api and '-2147483648' in api
        for family in ['public', 'private']:
            old_family, new_family = OLD / family / 'tasks' / task, C / family / 'tasks' / task
            for name in ['flow.json', 'outcomes.json']:
                assert (old_family / name).read_bytes() == (new_family / name).read_bytes()
            for platform in ['ios', 'android']:
                a, b = old_family / platform, new_family / platform
                for name in ['fixtures.json', 'actions.json', 'bindings.json', 'reference.json', 'environment.json', 'denominator.json', 'routes.json']:
                    assert (a / name).read_bytes() == (b / name).read_bytes(), (family, task, platform, name)
                    normative_unchanged.append(str((b / name).relative_to(C)))
                old_contract, new_contract = load(a / 'contract.json'), load(b / 'contract.json')
                for key in ['rules', 'required_rule_ids', 'scenarios', 'design_owner']:
                    assert old_contract[key] == new_contract[key]
                old_policy, new_policy = load(a / 'policy.json'), load(b / 'policy.json')
                old_policy['design_lock_sha256'] = 'LOCK-IDENTITY'; new_policy['design_lock_sha256'] = 'LOCK-IDENTITY'
                assert old_policy == new_policy
                assert normalize_plan(load(a / 'generated/plan.json')) == normalize_plan(load(b / 'generated/plan.json'))
                if platform == 'ios':
                    assert (a / 'ObserverBridge.swift').read_bytes() == (b / 'ObserverBridge.swift').read_bytes()
                else:
                    bridge = (b / 'ObserverBridge.kt').read_text()
                    assert 'import kotlinx.serialization.json.JsonObject' in bridge and 'com.google.gson' not in bridge
                    assert 'fun Content(fixture: JsonObject, onEvent: (String) -> Unit)' in bridge
                    for key, prop in schema['properties'].items():
                        accessor = {'string': '!!.jsonPrimitive.content', 'integer': '!!.jsonPrimitive.int',
                                    'boolean': '!!.jsonPrimitive.boolean', 'array': '!!.jsonArray.map { it.jsonPrimitive.content }'}[prop['type']]
                        assert 'fixture["' + key + '"]' + accessor in bridge, (task, family, key)
                    assert bridge.count('fixture[') == len(schema['properties'])
                    assert 'ContrastAwareReplyTheme(darkTheme = false, dynamicColor = false) {' in bridge
                    assert 'input = input, onEvent = onEvent' in bridge
                    code = '\n'.join(line for line in bridge.splitlines() if not line.startswith('//'))
                    assert not re.search(r'\b(if|when|remember|State|Column|Button|Text|LazyColumn|LaunchedEffect)\b', code)
                    abi_rows.append({'task': task, 'family': family, 'path': str((b / 'ObserverBridge.kt').relative_to(C)),
                                     'host_parameter_type': 'kotlinx.serialization.json.JsonObject',
                                     'all_schema_typed_accessors_match': True, 'theme_arguments': {'darkTheme': False, 'dynamicColor': False},
                                     'direct_callback_and_production_call': True})
        rows.append({'task': task, 'business_semantics_actions_styles_units_unchanged': True,
                     'schema_bounds_and_API_spelling_corrected': True, 'actual_source_approval': 'PENDING'})
    assert len(range_rows) == 34 and len(abi_rows) == 10
    for arm in ['candidate-v13.9', 'baseline-v12.6-common-6']:
        source = R / arm / 'assets/android-observer/NativeObserverTest.kt'
        lines = source.read_text().splitlines()
        assert 'import kotlinx.serialization.json.*' == lines[28]
        assert '.jsonObject' in lines[38]
        assert 'ObserverBridge.Content(current)' in lines[296]
        source_citations.append({'path': str(source), 'sha256': sha(source.read_bytes()),
            'lines': [{'line': n, 'text': lines[n - 1]} for n in [29, 35, 39, 297]]})
        ios = R / arm / 'assets/ios-observer/ObserverApp.swift'
        contract = R / arm / 'assets/ios-observer/CONTRACT.md'
        assert 'ObserverBridge.make(fixture: fixtures[index])' in ios.read_text()
        assert 'static func make(fixture: [String: Any],' in contract.read_text()
        for path in [ios, contract]: source_citations.append({'path': str(path), 'sha256': sha(path.read_bytes()), 'scope': 'named iOS factory ABI only'})
    theme = R / 'cache/hosts/reply/Reply/app/src/main/java/com/example/reply/ui/theme/Theme.kt'
    theme_source = theme.read_text()
    assert 'darkTheme: Boolean = isSystemInDarkTheme()' in theme_source and 'dynamicColor: Boolean = false' in theme_source
    source_citations.append({'path': str(theme), 'sha256': sha(theme.read_bytes()), 'lines': [295, 296, 298], 'scope': 'named theme parameter ABI only'})
    save(O / 'bounded-revision-ABI-checks.json', {'passed': True, 'tasks': rows, 'integer_ranges': range_rows,
        'corrected_Kotlin_Boolean_fields': ['visitor-preclearance.sponsorActive', 'visitor-preclearance.badgeTrainingComplete', 'candidate-disposition.legalHold'],
        'android_bridges': abi_rows, 'named_primary_ABI_sources': source_citations,
        'unchanged_normative_paths': normative_unchanged, 'denominator_all_10332_cells_byte_identical': True,
        'source_compilation': False, 'native_execution': False, 'actual_source_API_domain_provider_approvals': 'PENDING'})

def main():
    assert pure.main() == 0
    assert business.main() == 0
    bounded_revision_checks()
    assert identity_check()['original_829_file_cohort_unchanged']
    print(json.dumps({'all_twenty_profiles_both_frozen_arms_passed': True, 'shared_preflights': 40,
        'finite_semantic_states': 120, 'ranges': 34, 'Boolean_corrections': 3, 'Android_ABI_bridges': 10, 'native_runs': 0}))

if __name__ == '__main__': main()
