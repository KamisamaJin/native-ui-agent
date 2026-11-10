#!/usr/bin/env python3
"""Read-only offline reconstruction; writes solely to this new review directory."""
import copy
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
BASE = OUT.parents[2]
sys.path.insert(0, str(BASE / 'candidate-v12.6/scripts'))
import design_contract as d
import execution_plan as xp
import feedback_loop as feedback
import evidence_responsibility as er
import requirement_routes as routes
import acceptance


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p):
    return json.loads(Path(p).read_text())


def save(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


cfg = load(BASE / 'probes/native/prepared-positive/ios/config.json')
plan = load(cfg['plan'])
lock = load(cfg['design_lock'])
fixtures = load(cfg['fixtures'])
production = BASE / 'evidence/probes/production'
archived_sources = [production / 'alerttoast/Sources/AlertToast/NeutralCounter.swift',
                    production / 'reply/Reply/app/src/main/java/com/example/reply/ui/components/NeutralCounter.kt']
fingerprint = xp.source_fingerprint(archived_sources)
checks = {}
packets = {}
for version, bundle in [('v12.4', 'ios-neutral-v12.4'), ('v12.6', 'ios-qualification-v12.6')]:
    root = BASE / 'evidence' / bundle / 'positive'
    capture = root / 'capture/result.json'
    # This public reader resolves original source namespace strings but never
    # reads source content from cache. All current-content checks below use the
    # explicitly supplied archived Counter files, with that limit recorded.
    packet = feedback.load_previous(capture, sha(capture), plan, lock,
              cfg['design_sha256'], fixtures, cfg['bridge'], cfg['source_roots'])
    before, report, observation, execution, receipt = packet
    packets[version] = packet
    cycle = load(root / 'cycle.json')
    resource = load(root / 'resources.json')
    cov = routes.audit(lock, cfg['design_sha256'], plan, load(cfg['routes']), cfg['routes_sha256'])
    environment = acceptance.environment(observation, load(cfg['environment']), 'ios')
    admitted = routes.admission(cov, plan, report, execution_scope=execution['scope'], capture=receipt, environment=environment)
    save('offline-native-admission-' + version + '.json', admitted)
    save('offline-native-report-' + version + '.json', report)
    checks[version] = {
        'original_native_runtime_version': version,
        'reader_version': 'candidate-v12.6',
        'public_load_previous_passed': True,
        'cycle_sha256': sha(root / 'cycle.json'),
        'cycle_native_executed': cycle['native_executed'], 'cycle_final': cycle['final'],
        'cycle_pins_original_capture': cycle['capture_sha256'] == sha(capture),
        'cycle_pins_original_final_resources': cycle['resources_sha256'] == sha(root / 'resources.json'),
        'final_resource_cleanup_empty': not resource['cleanup_errors'] and not resource['remaining_devices'] and not resource['remaining_directories'],
        'archived_source_fingerprint_matches_recorded_before': fingerprint == before,
        'source_canonical_sha256': d.digest(fingerprint),
        'counts': report['counts'],
        'native_admission_status_before_source_claims': admitted['status'],
        'source_namespaces_preserved': receipt['source_roots'] == cfg['source_roots'],
    }

newroot = BASE / 'evidence/ios-qualification-v12.6'
native = newroot / 'positive/capture/native'
observation = packets['v12.6'][2]
execution = packets['v12.6'][3]
request = load(newroot / 'positive/capture/fixtures.json')
request_receipt = xp.request_coverage_receipt(request, observation, 'ios', sha(newroot / 'positive/capture/fixtures.json'))
outer_receipt = xp.coverage_receipt(execution, observation)
save('request-identity.json', {
    'request_receipt': request_receipt,
    'outer_execution_receipt': outer_receipt,
    'native_manifest_request_receipt_exact_match': request_receipt == load(native / 'manifest.json')['execution_coverage'],
    'outer_execution_receipt_exact_match': outer_receipt == load(newroot / 'positive/capture/execution-coverage.json'),
    'request_contains_no_execution_identity': 'execution_sha256' not in request_receipt,
    'distinct_identity_values': request_receipt['request_sha256'] != outer_receipt['execution_sha256'],
    'scope': 'Native raw request bytes and independently rebuilt approved execution are different identity domains. No old v12.4 inner field was rewritten.'})

compiled = load(newroot / 'positive/evidence-responsibility.json')
store = newroot / 'source-reviews/ios'
source_cfg = copy.deepcopy(cfg)
source_cfg['source_review_store'] = str(store)
source_report = er.evaluate(source_cfg, compiled, packets['v12.6'][1])
save('offline-source-responsibility.json', source_report)
bound_path = next(store.glob('*.json'))
bound = load(bound_path)
actual_by_id = {row['id']: row for row in bound['observations']}
file_aliases = {original: archived for original, archived in zip(cfg['source_roots'], archived_sources)}
file_aliases[cfg['bridge']] = Path(cfg['bridge'])
source_checks = []
for claim in compiled['claims']:
    actual = actual_by_id[claim['id']]
    source_checks.append({
        'id': claim['id'],
        'actual_bool': actual['observed'],
        'bound_claim_digest_matches': actual['claim_sha256'] == d.digest(claim),
        'exact_subject_file_map_matches': actual['files'] == claim['files'],
        'archived_subject_bytes_match': all(sha(file_aliases[path]) == digest for path, digest in actual['files'].items()),
        'citations_inside_approved_subject': all(ref['path'] in claim['files'] and 1 <= ref['line'] <= len(file_aliases[ref['path']].read_text().splitlines()) for ref in actual['citations']),
    })

oldroot = BASE / 'evidence/ios-neutral-v12.4/positive'
completion = load(newroot / 'source-only-completion/completion.json')
operator = load(BASE / 'operators/source-only-finalization-v12.6.json')
old_failure = load(BASE / 'operators/source-only-finalization-v12.4.json')
saved_admission = load(newroot / 'source-only-completion/admission.json')
save('source-only-completion-audit.json', {
    'old_v12_4_failure_exit': old_failure['exit_code'], 'old_failure_stderr': old_failure['stderr'],
    'v12_6_completion_operator_exit': operator['exit_code'],
    'operator_stdout_matches_sealed_completion': json.loads(operator['stdout']) == completion,
    'completion_result': completion,
    'completion_pins_actual_v12_4_cycle': completion['final_cycle_sha256'] == sha(oldroot / 'cycle.json'),
    'completion_is_not_a_new_sdk_run': completion['native_executed'] is False,
    'original_v12_4_report_recomputed_with_v12_6_matches_final_evaluated': packets['v12.4'][1] == load(newroot / 'source-only-completion/evaluated.json'),
    'no_required_image_policy_in_this_approved_config': not cfg.get('policy'),
    'source_checks': source_checks,
    'required_source_claims_unblocked': source_report['blocking_claims'] == [],
    'saved_source_claim_statuses': [(r['id'], r['status'], r['actual']) for r in saved_admission['evidence_responsibility']['rows']],
    'scope': 'Actual successful v12.6 API completion of a pinned prior v12.4 full/final native packet plus exact subject-bound source observations, without a dummy image review. The source-store path is only remapped to the sealed archive for read-only evaluation. Source content is compared against supplied archived production bytes, not a claim to inspect current cache. This audit does not execute completion, mutate the store, or independently run visual/source-drift/resource-error negative gates.'})
save('archive-source-namespace.json', {
    'original_namespace_to_archived_content': {original: {'archive': str(archived), 'sha256': sha(archived)} for original, archived in file_aliases.items()},
    'fingerprint': fingerprint,
    'positive_audit_field_scope': 'The inherited positive audit field names source_before_matches_current/source_after_matches_current refer here to the archived production files passed explicitly in audit_positive.py. They are not a current-cache observation or evidence of a later source revision.',
    'source_runtime_boundary': 'Counter @State is initialized from seed; bridge .id(seed) keys component identity. Current evidence qualifies this caller-keyed path only.'})
save('binding-checks.json', checks)
print(json.dumps({'native_reports': {k: x['counts'] for k, x in checks.items()}, 'source_checks': source_checks,
                  'v12_6_request_identity_matches': request_receipt == load(native / 'manifest.json')['execution_coverage'],
                  'source_only_completion_status': completion['status']}, indent=2))
