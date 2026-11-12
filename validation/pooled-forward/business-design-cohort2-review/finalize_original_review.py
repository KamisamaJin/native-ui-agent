#!/usr/bin/env python3
"""Seal this rejected original review; no input mutation and no source approval."""
import hashlib
import json
from pathlib import Path
import sys
from run_pure_checks import C, O, R, MAPPING, SEAL, load, save, sha_bytes, identity_check

def file_record(path):
    return {'path': str(path), 'sha256': sha_bytes(path.read_bytes())}

def main():
    identity = identity_check()
    hosts = []
    for arm in ['candidate-v13.9', 'baseline-v12.6-common-6']:
        p = R / arm / 'assets/android-observer/NativeObserverTest.kt'
        lines = p.read_text().splitlines()
        hosts.append({**file_record(p), 'abi_only': True,
            'source_citations': [{'line': i, 'text': lines[i - 1]} for i in [29, 35, 39, 297]],
            'actual_parameter_type': 'kotlinx.serialization.json.JsonObject'})
    theme_path = R / 'cache/hosts/reply/Reply/app/src/main/java/com/example/reply/ui/theme/Theme.kt'
    theme_lines = theme_path.read_text().splitlines()
    theme = {**file_record(theme_path), 'abi_only': True,
             'source_citations': [{'line': i, 'text': theme_lines[i - 1]} for i in [295, 296, 298]],
             'admitted_environment_intent': {'darkTheme': False, 'dynamicColor': False}}
    mapping = load(C / 'APPROVAL-MAPPING.json')
    bridges = []
    for pid, profile in mapping['profiles'].items():
        if profile['intended_platform'] != 'android': continue
        p = C / profile['paths']['bridge']
        assert 'import com.google.gson.JsonObject' in p.read_text()
        bridges.append({'profile_id': pid, **file_record(p), 'declared_parameter_type': 'com.google.gson.JsonObject',
                        'actual_host_abi_compatible': False})
    save(O / 'bridge-abi-checks.json', {'passed': False, 'coordinator_identified_independently_confirmed': True,
        'hosts': hosts, 'theme': theme, 'bridges': bridges,
        'issue': 'All ten Android bridges use a distinct incompatible Gson JsonObject for a kotlinx.serialization host argument.',
        'source_compilation': False, 'native_execution': False, 'actual_provider_approval': 'PENDING'})
    incident = R / 'candidate-v13.9/assets/ios-observer/provider-conformance.json'
    save(O / 'REVIEWER-ERRORS.json', {'version': 1, 'errors_retained': [
        {'kind': 'discovery-path-error', 'command': 'cat scripts/action_guard.py public/tasks/catering-package/fixture.schema.json public/tasks/catering-package/ios/ObserverBridge.swift public/tasks/catering-package/android/ObserverBridge.kt',
         'cwd': str(C), 'exit_code': 1, 'stderr': 'cat: scripts/action_guard.py: No such file or directory',
         'correction': 'Read the named frozen candidate scripts/action_guard.py; no input changed.'},
        {'kind': 'reviewer-fixture-shape-assumption', 'exit_code': 1,
         'traceback': 'Traceback (most recent call last):\n  File "<stdin>", line 13, in <module>\nKeyError: \'fixtures\'\n',
         'correction': 'Use actual initial + updates fixture shape; finite evaluator then passed all ten families.'},
        {'kind': 'reviewer-line-bound-assumption', 'exit_code': 1,
         'traceback': 'Traceback (most recent call last):\n  File "' + str(O / 'check_additional_authored_metadata.py') + '", line 78, in <module>\n    if __name__ == \'__main__\': main()\n  File "' + str(O / 'check_additional_authored_metadata.py') + '", line 52, in main\n    assert state[target + \'-lines\'] == {\'value\': 1, \'unit\': \'count\'}\nAssertionError\n',
         'correction': 'Inspect and retain authored gte bounds: ordinary minimum1; long title2/context3. These are not exact native line predictions.'},
        {'kind': 'confirmed-cohort-api-type-mismatch', 'exit_code': 1,
         'traceback': 'Traceback (most recent call last):\n  File "' + str(O / 'check_additional_authored_metadata.py') + '", line 84, in <module>\n    if __name__ == \'__main__\': main()\n  File "' + str(O / 'check_additional_authored_metadata.py') + '", line 23, in main\n    assert swift_fields[key] == expected_swift and kotlin_fields[key] == expected_kotlin\nAssertionError\n',
         'disposition': 'All fields enumerated; three published Kotlin Bool errors retained as blocking design findings.'},
        {'kind': 'incidental-read-scope-incident', 'command': 'rg -n "ObserverBridge|make\\(fixture" assets/ios-observer',
         'cwd': str(R / 'candidate-v13.9'), **file_record(incident),
         'observed_content_scope': 'One matching bundled public frozen provider-conformance metadata line, containing historical generic source-conformance/qualification references; output was truncated.',
         'referenced_paths_followed': False, 'claims_used': False,
         'coordinator_notified_immediately': True,
         'disposition': 'Record explicitly, do not claim zero exposure. Further ABI reads restricted to named primary source files.'}
    ]})
    readset = {
        'version': 1, 'reviewer_context': '/root/v13_design_admission2',
        'cohort_input_root': str(C), 'cohort_seal_sha256': SEAL,
        'mapping_canonical_sha256': MAPPING,
        'cohort_all_bytes_identity_read': [{'path': str(C / p), 'sha256': h} for p, h in identity['files'].items()] + [file_record(C / 'SEAL.sha256'), file_record(C / 'SEAL-IDENTITY.json')],
        'cohort_content_scope': ['README/author/read-set/profile-admit declarations and canonical mapping',
            'All five public BRIEF/API/DESIGN/schema/tokens/structural SVG files and requirement maps',
            'All ten public/private family flows/outcomes and all20 locks/reference/actions/bindings/policy/routes/environment/fixtures/bridges/denominators/plans/catalogs/execution/capability outputs',
            'All40 labelled production/integration placeholder subjects and original120 pure receipts'],
        'frozen_public_bytes_identity_read': load(O / 'frozen-public-before.json'),
        'frozen_pure_content_scope': ['Public pure seal/compile/catalog/routes/execution/responsibility APIs and their imported public script dependencies',
            'Shared subprocess-forbidden preflight script and explicit freeze receipt',
            'Named action_guard.py and native_checks.py callback verification source',
            'Exactly named Android NativeObserverTest.kt source ABI/type call-site checks in both arms',
            'iOS factory-location matches in ObserverApp.swift/ProbeBridge.swift/CONTRACT.md, plus the explicitly recorded incidental provider-conformance metadata match'],
        'added_abi_only_stock_source': theme,
        'jsonschema_library_root': str(R / 'cache/design-schema-python'),
        'jsonschema_scope': 'Pure Draft202012 schema/instance validation only. No SDK tools, network, host execution, or native observations.',
        'incidental_scope_exposure': {'path': str(incident), 'sha256': sha_bytes(incident.read_bytes()),
            'scope': 'Historical generic frozen provider source-conformance metadata matching line only; not used. No references followed.'},
        'not_read': ['Other business cohorts/designs/sources', 'Actual UI implementation source', 'Prior hidden business outcomes',
            'Native screenshots/rendered results', 'Benchmark/performance results', 'SDK tools/caches', 'Git state'],
        'writes': 'Only business-design-cohort2-review/**', 'native_executions': 0, 'actual_source_approvals': 0,
        'source_domain_provider_approval': 'PENDING until real code and closed finite source review exist'
    }
    save(O / 'READSET.json', readset)
    public_profiles = {pid: p for pid, p in mapping['profiles'].items() if p['family'] == 'public'}
    private_profiles = {pid: p for pid, p in mapping['profiles'].items() if p['family'] == 'private'}
    save(O / 'PUBLIC-READY-ENTRY-MAP.json', {'version': 1, 'ready': False, 'admission_decision': 'reject',
        'input_seal_sha256': SEAL, 'worker_read_scope': 'Only public/tasks/<assigned-task>/**',
        'profiles': public_profiles, 'scope': 'Public-only original entry identities. Not approved to start UI/native work.'})
    save(O / 'HIDDEN-HASH-MAP.json', {'version': 1, 'withhold_from_implementation_workers': True,
        'input_seal_sha256': SEAL, 'canonical_mapping_sha256': MAPPING,
        'profiles': private_profiles, 'scope': 'Private original identities only. Original admission rejected.'})
    blocker_groups = ['unbounded schema Int transport domains across all five', 'three Kotlin Bool API declarations across two tasks',
                      'incompatible Gson bridge JsonObject versus actual kotlinx.serialization host JsonObject across all ten Android bridges']
    save(O / 'ADMISSION-DECISION.json', {'version': 1, 'scope': 'all-five-preimplementation-design', 'decision': 'reject',
        'cohort_seal_sha256': SEAL, 'canonical_approval_mapping_sha256': MAPPING,
        'tasks': [{'task': t['task'], 'admitted': False} for t in load(C / 'PUBLIC-PACKETS.json')['tasks']],
        'blocking_design_groups': blocker_groups, 'new_native_observation_items': 0,
        'finite_corpus_business_semantics_match': True, 'full_chain_capability_preflights_passed': 40,
        'native_runs': 0, 'production_source_approvals': 0, 'source_approval': 'PENDING',
        'review_report_sha256': sha_bytes((O / 'REPORT.md').read_bytes()),
        'readset_sha256': sha_bytes((O / 'READSET.json').read_bytes()),
        'fresh_revision_requires_separate_external_seal_and_admission': True,
        'read_scope_incident_explicitly_retained': True})
    assert not (O / 'APPROVAL-SEAL.json').exists()
    files = [p for p in O.rglob('*') if p.is_file() and 'revision-v2' not in p.parts and p.name != 'REVIEW-SEAL.sha256']
    seal = ''.join(sha_bytes(p.read_bytes()) + '  ' + str(p.relative_to(O)) + '\n' for p in sorted(files))
    (O / 'REVIEW-SEAL.sha256').write_text(seal)
    print(json.dumps({'decision': 'reject', 'report': str(O / 'REPORT.md'), 'review_files': len(files),
                      'review_inventory_sha256': sha_bytes(seal.encode()), 'input_unchanged': True}))

if __name__ == '__main__': main()
