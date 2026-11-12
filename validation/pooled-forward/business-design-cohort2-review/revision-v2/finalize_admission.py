#!/usr/bin/env python3
"""Write a bounded design-intent approval only after all independent checks pass."""
import json
from pathlib import Path
import sys
from run_revision_checks import C, O, OLD, OR, R, SEAL, MAPPING, MAP_FILE, identity_check, snapshot_sources, load, save, sha

def record(path):
    return {'path': str(path), 'sha256': sha(path.read_bytes())}

def main():
    identity = identity_check()
    checks = load(O / 'PURE-CHECKS.json')
    business = load(O / 'business-state-checks.json')
    metadata = load(O / 'metadata-denominator-checks.json')
    boundary = load(O / 'public-private-boundary-checks.json')
    domain = load(O / 'input-domain-checks.json')
    correction = load(O / 'bounded-revision-ABI-checks.json')
    guards = load(O / 'profile-guard-checks.json')
    assert all(x['passed'] for x in [checks, business, metadata, boundary, domain, correction, guards])
    assert checks['rebuild_count'] == checks['shared_preflight_count'] == 40
    assert not checks['errors'] and not business['errors'] and not metadata['errors']
    assert sum(x['state_count'] for x in business['families']) == 120
    assert sum(x['original_action_count'] for x in business['families']) == 195
    assert metadata['counts'] == {'required': 8172, 'N/A': 2100, 'required-source-review': 60}
    assert guards['positive_count'] == 20 and guards['negative_count'] == 320 and guards['external_entry_rejections'] == 20
    assert snapshot_sources() == load(O / 'frozen-public-before.json')
    original_seal = OR / 'REVIEW-SEAL.sha256'
    assert sha(original_seal.read_bytes()) == 'c95dc9ee8bd2f29575270612ebb91bea2916c82463184b2d70fd16c61e9d265c'
    for line in original_seal.read_text().splitlines():
        expected, relative = line.split('  ', 1)
        assert sha((OR / relative).read_bytes()) == expected
    # Actual production subjects remain labelled comment-only placeholders.
    placeholder_count = 0
    for family in ['public', 'private']:
        for task in ['catering-package', 'training-pathway', 'subscription-capacity', 'visitor-preclearance', 'candidate-disposition']:
            for platform in ['ios', 'android']:
                for path in (C / family / 'tasks' / task / platform / 'pure-subjects').rglob('*'):
                    if not path.is_file(): continue
                    assert path.read_bytes() == (OLD / path.relative_to(C)).read_bytes()
                    if path.suffix in {'.swift', '.kt'}:
                        assert all(line.startswith('//') for line in path.read_text().splitlines())
                    else:
                        assert 'PURE CAPABILITY PLACEHOLDER' in load(path)['purpose']
                    placeholder_count += 1
    assert placeholder_count == 40
    mapping = load(C / 'APPROVAL-MAPPING.json')
    public = {pid: p for pid, p in mapping['profiles'].items() if p['family'] == 'public'}
    private = {pid: p for pid, p in mapping['profiles'].items() if p['family'] == 'private'}
    packets = load(C / 'PUBLIC-PACKETS.json')['tasks']
    task_entries = []
    for packet in packets:
        task = packet['task']
        task_entries.append({'task': task, 'public_namespace': 'public/tasks/' + task,
            'worker_read_scope': 'public/tasks/' + task + '/**', 'swift_api': packet['swift_api'], 'kotlin_api': packet['kotlin_api'],
            'platform_profiles': {platform: {'profile_id': 'public-' + task + '-' + platform,
                'config_path': public['public-' + task + '-' + platform]['profile_path'],
                'intended_platform': platform} for platform in ['ios', 'android']},
            'admitted_as_authored_intent': True})
    public_files = {path: value for path, value in identity['files'].items() if path.startswith('public/tasks/')}
    hidden_files = {path: value for path, value in identity['files'].items() if path.startswith('private/tasks/')}
    save(O / 'PUBLIC-READY-ENTRY-MAP.json', {'version': 1, 'ready_for_initial_implementation': True,
        'scope': 'Only final admitted public task packets. No private inputs, expected states, profiles or retained drafts.',
        'cohort_seal_sha256': SEAL, 'canonical_mapping_sha256': MAPPING,
        'tasks': task_entries, 'profiles': public, 'public_packet_file_sha256': public_files,
        'actual_source_and_native_approvals': 'PENDING'})
    save(O / 'HIDDEN-HASH-MAP.json', {'version': 1, 'withhold_from_implementation_workers': True,
        'cohort_seal_sha256': SEAL, 'canonical_mapping_sha256': MAPPING,
        'profiles': private, 'private_final_packet_file_sha256': hidden_files,
        'retained_staging_excluded_from_active_profiles': True,
        'scope': 'Coordinator/evaluator identity map only, physically separate from public worker packets.'})
    prior_readset = load(OR / 'READSET.json')
    library = R / 'cache/design-schema-python'
    module_files = sorted({Path(m.__file__).resolve() for m in list(sys.modules.values())
                           if getattr(m, '__file__', None) and Path(m.__file__).resolve().is_relative_to(library)})
    schema_resources = sorted(p for p in (library / 'jsonschema_specifications').rglob('*') if p.is_file() and p.suffix == '.json')
    save(O / 'READSET.json', {'version': 1, 'reviewer_context': '/root/v13_design_admission2',
        'cohort_input_root': str(C), 'cohort_seal_sha256': SEAL, 'inventory_file_count': 2108,
        'canonical_mapping_sha256': MAPPING, 'mapping_file_sha256': MAP_FILE,
        'all_input_bytes_identity_read': [{'path': str(C / p), 'sha256': h} for p, h in identity['files'].items()] + [record(C / 'SEAL.sha256'), record(C / 'SEAL-IDENTITY.json')],
        'semantically_read_scope': ['Final public/tasks/<task> and private/tasks/<task> authored flow/outcome/schema/API/brief/tokens/lock/plan/action/binding/reference/policy/routes/environment/fixtures/bridge/denominator/profile and placeholder boundaries',
            'Named root README/correction/status/mapping/public-packet/master denominator/master requirement metadata and final pure receipts',
            'Original independently authored review/evaluator scripts and exact original corpus comparison bytes',
            'Unchanged public frozen pure generator APIs and their named script dependencies',
            'Exactly named NativeObserverTest.kt, ObserverApp.swift and CONTRACT.md in both frozen arms, plus stock Theme.kt, for primary ABI only'],
        'staging_scope': 'private/_drafts identity hashes only; no staging expectation, draft bridge or prior receipt used as final truth.',
        'named_frozen_and_ABI_source_identities': load(O / 'frozen-public-before.json'),
        'pure_jsonschema_module_identities': [record(p) for p in module_files],
        'pure_jsonschema_resource_identities': [record(p) for p in schema_resources],
        'schema_library_scope': 'Pure schema/instance/scalar-bound checks only; no SDK or native behavior.',
        'original_review_identity': record(original_seal),
        'independent_evaluator_identity': record(OR / 'check_business_and_scope.py'),
        'original_rejection': record(OR / 'ADMISSION-DECISION.json'),
        'prior_incidental_scope_exposure_retained': prior_readset['incidental_scope_exposure'],
        'v2_repeated_incidental_metadata_read': False, 'referenced_qualification_paths_followed': False,
        'v2_reviewer_errors': ['reviewer-errors/attempt-1.json', 'reviewer-errors/attempt-1.stderr.txt'],
        'not_read': ['Actual new business UI/source workspaces', 'Other business designs/cohorts', 'Native screenshots/rendered results',
            'Benchmark/performance history', 'SDK tools/caches', 'Git state', 'Source-helper D0/host operational logs'],
        'writes': 'Only business-design-cohort2-review/revision-v2/**',
        'native_executions': 0, 'source_approvals': 0,
        'actual_production_API_domain_provider_approval': 'PENDING until real code and source closure are reviewed'})
    check_paths = ['identity-check.json', 'PURE-CHECKS.json', 'business-state-checks.json', 'metadata-denominator-checks.json',
                   'public-private-boundary-checks.json', 'input-domain-checks.json', 'bounded-revision-ABI-checks.json', 'profile-guard-checks.json']
    raw_receipts = [p for folder in ['pure-rebuild', 'shared-preflight-receipts', 'guard-native-entry-rejections']
                    for p in (O / folder).rglob('*.json') if 'receipts' in p.parts or folder != 'pure-rebuild']
    save(O / 'RAW-CHECK-INDEX.json', {'version': 1, 'checks': [record(O / p) for p in check_paths],
        'successful_pure_CLI_stages': 240, 'successful_shared_subprocess_forbidden_preflights': 40,
        'placeholder_external_entry_rejections': 20, 'raw_receipts': [record(p) for p in sorted(raw_receipts)],
        'native_executions': 0, 'actual_source_approvals': 0})
    approval = {'version': 1, 'scope': 'all-five-preimplementation-design', 'decision': 'admit',
        'cohort_root': str(C), 'cohort_seal_sha256': SEAL, 'cohort_inventory_files': 2108,
        'canonical_approval_mapping_sha256': MAPPING, 'approval_mapping_file_sha256': MAP_FILE,
        'all_five_admitted_before_initial_UI_code': True,
        'tasks': [{'task': t['task'], 'public_namespace': t['public_namespace'], 'admitted': True,
                   'ios_public_profile': t['platform_profiles']['ios']['profile_id'],
                   'android_public_profile': t['platform_profiles']['android']['profile_id']} for t in task_entries],
        'profile_count': 20, 'all_intended_platform_projections_rebuilt': True,
        'pure_CLI_exact_rebuild_stages': 240, 'shared_full_capability_preflights': 40,
        'must_capability_issues': [], 'must_route_gaps': [], 'unowned_assertions': [],
        'independently_recomputed_logical_states': 120, 'denominator_cells_retained': 10332,
        'denominator_counts': metadata['counts'], 'changed_native_observation_items': 0,
        'correction_scope': {'integer_fields': 34, 'Kotlin_Boolean_fields': 3, 'Android_bridge_ABI_copies': 10,
                             'theme_arguments': {'darkTheme': False, 'dynamicColor': False}},
        'source_duties_each_profile': {'production-api': 'PENDING', 'thin-bridge': 'PENDING', 'production-placement': 'PENDING'},
        'actual_production_API_approval': 'PENDING', 'actual_domain_interpretation_approval': 'PENDING',
        'actual_provider_truth_approval': 'PENDING', 'source_approvals': 0, 'native_runs': 0,
        'source_truth_approved': False, 'runtime_truth_approved': False,
        'approval_limit': 'Authored design intent and pure coverage/capability/primary-source ABI compatibility only. Initial UI implementation may start. Actual source closure and native evidence remain unassessed; later acquisition requires source-bound configuration, source review and exact intended-platform guard.',
        'shared_template_correlation_disclosed': True, 'prior_incidental_metadata_exposure_retained': True,
        'original_rejection_retained': True,
        'artifacts': {p: sha((O / p).read_bytes()) for p in ['REPORT.md', 'READSET.json', 'PUBLIC-READY-ENTRY-MAP.json',
            'HIDDEN-HASH-MAP.json', 'SOURCE-REVIEW-RUBRIC.md', 'RAW-CHECK-INDEX.json']}}
    save(O / 'APPROVAL-SEAL.json', approval)
    files = sorted(p for p in O.rglob('*') if p.is_file() and p.name != 'REVIEW-SEAL.sha256')
    inventory = ''.join(sha(p.read_bytes()) + '  ' + str(p.relative_to(O)) + '\n' for p in files)
    (O / 'REVIEW-SEAL.sha256').write_text(inventory)
    print(json.dumps({'decision': 'admit', 'approval_seal': str(O / 'APPROVAL-SEAL.json'),
        'approval_file_sha256': sha((O / 'APPROVAL-SEAL.json').read_bytes()),
        'review_inventory_sha256': sha(inventory.encode()), 'review_files': len(files),
        'initial_implementation_allowed': True, 'source_and_native_truth': 'PENDING'}))

if __name__ == '__main__': main()
