"""Join sealed decisions, original result rows and measured clocks; no oracle.

Requires all original operations to terminate and a separately pinned positive
resource closure. Missing mandatory observations become U, never disappear.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
COORD = ROOT / 'operators/cohort2/coordination'
CODE_PINS = {
    'consumer': ('verify_publication.py', 'e9fc84f457129ea014a40e78a53a29778862468a524d2c84ae184e3d5b11c25b'),
    'archive': ('publication-tools/archive.py', 'c412b03c20c9c97b59a550bd5afa02c4c6fd58d0fbd6f9dc81a3bdf9b02796b8'),
    'metric': ('publication-cost-metrics-v3/metric_rules_v3.py', '34a98a6b2be408c3261616b2eab931ca2116d7f47036b719728899e0eeeb9ff6'),
}
PINS = {
    'registry': ('FROZEN-MANDATORY-COVERAGE-REGISTRY-v2.json', 'bf0b28d507c9fa1f638e0233980ddaf4d4293745e0ac59e63205ef7d43f57baa'),
    'reveal': ('ROOT-MAPPING-REVEAL-v1.json', 'cd108d543160faa2f59a06d744dc8fa9e4d8bd0b2774ff8fcfde8731c53ff179'),
    'facts': ('SEALED-PRODUCT-FACTS-FOR-METRICS-v1.json', '803d3cd7449fa7f5e2ed900b5385e63fb8794674caa554de7a67c14803f8fd44'),
    'costs': ('AUDITED-COST-BASES-v1.json', 'cafa92b9b78fb48f2f2720fdcd3594e886ba2a2c5a2209f580f450674cb5cc57'),
    'alarms': ('ALARM-COST-CHECKPOINT-v2.json', 'cfcde4341a07b4e4265dc8674d5f0a31ba0aa48c32de352db3ca0d822b545649'),
    'matcher': ('MATCHER-END-VERIFIED-v1.json', 'd6ba689984ba88d9b64e256111f9f9fefe9f1817af2a507472009ab8faa4a210'),
    'plan': ('post-consensus-validation-ops-v1/PLAN.json', '9ba0c2d48165c74ae01796fb2aa79d9d046d43a6a6a55ae1409d2ccd953a7a04'),
}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def ref(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def module(name, relative, expected):
    p = ROOT / relative
    need(ref(p)['sha256'] == expected, 'Frozen code differs: ' + name)
    spec = importlib.util.spec_from_file_location('metric_join_' + name, p)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def unique(rows, field):
    need(type(rows) is list and all(type(x) is dict and type(x.get(field)) is str for x in rows), 'Explicit identified result rows required')
    result = {x[field]: x for x in rows}
    need(len(result) == len(rows), 'Duplicate original result identity')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['binding-index', 'resource-closure', 'output']:
        parser.add_argument('--' + key, type=Path, required=True)
    for key in ['binding-index', 'resource-closure']:
        parser.add_argument('--' + key + '-sha256', required=True)
    args = parser.parse_args()
    modules = {k: module(k, *v) for k, v in CODE_PINS.items()}
    archive, metric, consumer = modules['archive'], modules['metric'], modules['consumer']
    readset = {}

    def read(reference):
        need(type(reference) is dict and set(reference) == {'path', 'sha256'}, 'Exact original reference required')
        p = archive.absolute(reference['path'])
        raw = archive.read_file(p)
        need(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'Original result or authority bytes differ: ' + str(p))
        need(str(p) not in readset or readset[str(p)] == reference['sha256'], 'Mutable reference at one original key')
        readset[str(p)] = reference['sha256']
        return consumer.strict_json(raw)

    values = {k: read({'path': str(COORD / p), 'sha256': h}) for k, (p, h) in PINS.items()}
    binding_ref = {'path': str(args.binding_index), 'sha256': args.binding_index_sha256}
    resource_ref = {'path': str(args.resource_closure), 'sha256': args.resource_closure_sha256}
    index, resources = read(binding_ref), read(resource_ref)
    need(resources.get('kind') == 'final-owned-resource-closure' and resources.get('pending') == [], 'Separately measured final resource closure required')
    ops = unique(index['operations'], 'operation_id')
    planned = unique(values['plan']['operations'], 'id')
    need(set(ops) == set(planned) and len(ops) == 110, 'All 110 original planned operations required')
    for key, op in ops.items():
        plan = planned[key]
        need(op['action'] == plan['action'] and op['kind'] == plan['kind'], 'Original operation scope/action differs')
        need(op.get('outcome') is not None and op.get('wall_seconds') is not None and op.get('exit_code') is not None, 'Original operation is unfinished: ' + key)
        need(op.get('error') is None and op.get('post_boundary_error') is None and not op.get('preservation_errors'), 'Original operation integrity failed: ' + key)
        read(op['outcome'])
        metric.seconds(op['wall_seconds'])
        if op['action'] == 'finish-native-review':
            completion = read(op['completion'])
            need((op['exit_code'], completion['status']) in {(0, 'accepted'), (1, 'not_accepted')}, 'Unclassified original finish result')
        else:
            need(op['exit_code'] == 0, 'Source/image binding did not complete: ' + key)
    need(index.get('original_public_gate_promoted') is False and index.get('product_quality_rejudged') is False, 'Mechanical binding cannot replace product judgment or original gates')

    # Every charged old failed entry is counted once in its recorded arm/task.
    failures_seen = set()
    binding_costs = {}
    for op in ops.values():
        bucket = binding_costs.setdefault((op['task'], op['arm']), [])
        bucket.append(metric.seconds(op['wall_seconds']))
        for old in op.get('retained_failed_attempts', []):
            read(old['outcome'])
            identity = (old['outcome']['path'], old['outcome']['sha256'])
            need(identity not in failures_seen and old['count_as_success'] is False, 'Failed entry is duplicated or relabeled')
            failures_seen.add(identity)
            bucket.append(metric.seconds(old['runner_wall_seconds']))

    reveal = values['reveal']
    mapping = read(reveal['mapping'])['mapping']
    cases = copy.deepcopy(values['facts']['cases'])
    registry = values['registry']['coverage_denominators']
    native_costs = {(x['task'], x['arm']): metric.seconds(x['selected_active_native_seconds']) for x in values['costs']['private_native']}
    public_costs = {(x['task'], x['arm']): metric.seconds(x['original_own_wall_seconds']) for x in values['costs']['public']}
    coverage_receipts = []
    gate_receipts = []

    def rows_index(rows):
        result = unique(rows, 'id')
        need(all(x.get('status') in {'passed', 'failed', 'unassessed', 'not_applicable'} for x in result.values()), 'Unknown original result status')
        return result

    for case in cases:
        case_id = case['case_id']
        task = mapping[case_id]['task']
        for arm in ['A', 'B']:
            version = reveal['assignment'][case_id][arm]
            final = case['versions'][version]
            closure_path = COORD / ('%s-%s-closure-verification.json' % (task, arm))
            closure_ref = ref(closure_path)
            closure = read(closure_ref)
            original_self = read(closure['self_seal'])
            need(original_self['task'] == task and original_self['arm'] == arm, 'Original public self-seal belongs to another PR')
            need(original_self['own_delivery_wall_seconds'] == public_costs[(task, arm)] == closure['own_delivery_wall_seconds'], 'Original public wall changed')
            need(type(original_self['public_service_accepted']) is bool and original_self['public_service_accepted'] == closure['public_service_accepted'], 'Original public acceptance changed')
            sources, native, scope_refs, private_ok = {}, {}, {}, []
            for platform in ['ios', 'android']:
                public = original_self['final_outcomes'][platform]
                inventory = read(public['inventory'])
                native_path = str(Path(public['service_output']) / 'evaluated.json')
                need(native_path in inventory, 'Original final public native rows are unregistered')
                native_ref = {'path': native_path, 'sha256': inventory[native_path]}
                native[('public_native_image', platform)] = rows_index(read(native_ref)['assertions'])
                scope_refs[('public_native_image', platform)] = native_ref
                private = ops['%s-%s-%s-finish-native-review' % (task, arm, platform)]
                private_native_ref = private['full_native_image_assertion_rows']
                native[('private_native_image', platform)] = rows_index(read(private_native_ref)['assertions'])
                scope_refs[('private_native_image', platform)] = private_native_ref
                admission = read(private['full_admission_responsibility_rows'])
                completion = read(private['completion'])
                private_ok.append(admission['status'] == 'accepted' and completion['status'] == 'accepted')
                sources[('private/source-boundary', platform)] = rows_index([x for x in admission['evidence_responsibility']['rows'] if x['method'] == 'source'])
                scope_refs[('private/source-boundary', platform)] = private['full_admission_responsibility_rows']
                public_op = ops['%s-%s-%s-public-source-only' % (task, arm, platform)]
                source_ref = public_op['source_only_rows']
                public_source = read(source_ref)
                need(public_source['original_public_gate_promoted'] is False and public_source['current_delivery_verified'] is False, 'Source-only record may not authorize complete delivery')
                sources[('public/source-boundary', platform)] = rows_index(public_source['rows'])
                scope_refs[('public/source-boundary', platform)] = source_ref

            # A new assertion cannot disappear merely because the frozen
            # denominator has no corresponding slot. Keep the join blocked.
            for (family, platform), actual_rows in native.items():
                allowed = {identity for spec in registry[case_id][version]
                    if spec['family'] == family and spec['platform'] == platform
                    for identity in spec['applicable_ids'] + spec['not_applicable_ids']}
                need(set(actual_rows) <= allowed, 'Unregistered extra native assertion requires an explicit audit')
            for (state, platform), actual_rows in sources.items():
                allowed = {identity[len(state) + 1:] for spec in registry[case_id][version]
                    if spec['family'] == 'source' and spec['platform'] == platform and spec['state'] == state
                    for identity in spec['applicable_ids']}
                need(set(actual_rows) <= allowed, 'Unregistered extra source assertion requires an explicit audit')

            coverage_rows = []
            for spec in registry[case_id][version]:
                family, state, platform = spec['family'], spec['state'], spec['platform']
                if family == 'source':
                    raw = sources[(state, platform)]
                    observed = {state + '/' + k: v for k, v in raw.items()}
                    source_ref = scope_refs[(state, platform)]
                else:
                    observed = native[(family, platform)]
                    source_ref = scope_refs[(family, platform)]
                row = dict(platform=platform, state=state, family=family,
                    frozen_applicable_ids=copy.deepcopy(spec['applicable_ids']),
                    passed_ids=[], failed_ids=[], unassessed_ids=[],
                    not_applicable_ids=copy.deepcopy(spec['not_applicable_ids']),
                    denominator_evidence=copy.deepcopy(spec['evidence']))
                dispositions = []
                for identity in spec['applicable_ids']:
                    original = observed.get(identity)
                    status = original.get('status') if original is not None else None
                    bucket = {'passed': 'passed_ids', 'failed': 'failed_ids'}.get(status, 'unassessed_ids')
                    row[bucket].append(identity)
                    dispositions.append({'id': identity, 'original_status': status,
                        'partition': bucket, 'missing': original is None})
                coverage_rows.append(row)
                coverage_receipts.append({'case_id': case_id, 'arm': arm, 'anonymous_version': version,
                    'platform': platform, 'state': state, 'family': family,
                    'source': source_ref, 'dispositions': dispositions,
                    'frozen_NA_never_counted_as_pass': True})
            cov = metric.coverage({'mandatory_coverage': coverage_rows}, registry[case_id][version])
            resource = resources['by_task_arm'][task][arm]
            need(type(resource['closed']) is bool and type(resource.get('evidence')) is list and resource['evidence'], 'Positive per-PR resource result required')
            for proof in resource['evidence']:
                read(proof)
            final['mandatory_coverage'] = coverage_rows
            final['delivery_obligations'] = {
                'public_current_all_must_passed': original_self['public_service_accepted'],
                'private_current_all_must_passed': all(private_ok),
                'source_all_must_passed': cov['families']['source']['failed'] == cov['families']['source']['unassessed'] == 0,
                'owned_resources_closed': resource['closed'],
                'independent_quality_complete': final['independent_quality_complete'],
            }
            final['public_wall_seconds'] = public_costs[(task, arm)]
            final['hidden_validation_wall_seconds'] = metric.total([native_costs[(task, arm)], metric.total(binding_costs[(task, arm)])])
            gate_receipts.append({'case_id': case_id, 'arm': arm, 'anonymous_version': version,
                'original_public_self_seal': closure['self_seal'], 'closure_metadata': closure_ref,
                'resource_closure': resource_ref, 'original_public_gate_unchanged': True,
                'delivery_obligations': final['delivery_obligations']})

    # The only changes to the sealed product-fact copy are these four joins.
    without_joins = copy.deepcopy(cases)
    for case in without_joins:
        for final in case['versions'].values():
            for key in ['mandatory_coverage', 'delivery_obligations', 'public_wall_seconds', 'hidden_validation_wall_seconds']:
                del final[key]
    need(without_joins == values['facts']['cases'], 'A sealed product judgment changed during mechanical joining')
    initial = metric.total([x for (task, arm), x in native_costs.items() if arm == 'I'] +
                           [metric.total(v) for (task, arm), v in binding_costs.items() if arm == 'I'])
    cause = values['costs']['shared_cause_grading_by_anonymous_label']
    need(set(cause) == {'I', 'X', 'Y'}, 'All original shared cause-grading scopes required')
    grading = metric.total([metric.seconds(x['active_seconds_nonoverlapping']) for x in cause.values()] +
                          [values['alarms']['closed_pair_wall_seconds_sum'], values['matcher']['wall_seconds']])
    shared = {'initial_oracle_seconds': initial, 'design_preparation_seconds': None,
              'common_infrastructure_seconds': None, 'independent_grading_matcher_seconds': grading}
    output = archive.absolute(str(args.output))
    need(not output.exists(), 'Fresh final metric namespace required')
    output.mkdir(parents=True)
    metric_input = {'version': 1, 'kind': 'sealed-five-case-metric-input',
        'cases': cases, 'assignment': reveal['assignment'], 'shared_costs': shared,
        'coverage_denominators': registry,
        'provenance': {'correspondence_seal': reveal['correspondence_seal'],
                      'mapping_reveal': {'path': str(COORD / PINS['reveal'][0]), 'sha256': PINS['reveal'][1]},
                      'coverage_registry': {'path': str(COORD / PINS['registry'][0]), 'sha256': PINS['registry'][1]}}}
    results = {'version': 1, 'kind': 'five-case-fixed-metric-results', 'arms': {
        arm: metric.summarize(cases, arm, reveal['assignment'], shared_costs=shared, coverage_denominators=registry)
        for arm in ['A', 'B']}}
    # Diagnose this common post-seal harness without subtracting it from any
    # arm's original clocks or assigning it to a treatment feature.
    binding_diagnostic = []
    for op in ops.values():
        if op['kind'] != 'final-public-source-only':
            continue
        caller = read(op['outcome'])
        operation_ref = caller['source_only_operation']
        backend = read(operation_ref)
        need(backend['shared_clock_basis'] == 'clock_gettime(CLOCK_MONOTONIC)', 'Explicit source-only kernel clock required')
        start = metric.seconds(backend['started_at_clock_gettime'])
        finish = metric.seconds(backend['finished_at_clock_gettime'])
        duration = metric.seconds(finish - start)
        outer = metric.seconds(op['wall_seconds'])
        need(outer == caller['full_outer_wall_seconds'] and duration <= outer,
             'Source-only clock nesting differs')
        binding_diagnostic.append({'operation_id': op['operation_id'], 'arm': op['arm'],
            'caller_outcome': op['outcome'], 'source_only_operation': operation_ref,
            'full_outer_wall_seconds': outer, 'direct_source_only_backend_seconds': duration,
            'outside_direct_backend_seconds': outer - duration,
            'scope': 'Includes caller/source/profile/tool checks, full-study measurement, external resource supervision and retirement; not isolated CPU time or a treatment benefit.'})
    need(len(binding_diagnostic) == 20, 'All original final public source-only calls required for diagnostic')
    archive.save(output / 'METRIC-INPUT.json', metric_input)
    archive.save(output / 'METRIC-RESULTS.json', results)
    receipt = {'version': 1, 'kind': 'fixed-metric-original-row-and-clock-join', 'at_unix': time.time(),
        'source': ref(Path(__file__)), 'binding_index': binding_ref, 'resource_closure': resource_ref,
        'readset': readset, 'coverage_dispositions': coverage_receipts, 'gate_receipts': gate_receipts,
        'common_post_seal_source_only_cost_diagnostic': binding_diagnostic,
        'all_sealed_product_fields_unchanged': True, 'old_failed_entries_charged_once': len(failures_seen),
        'public_original_gates_and_walls_unchanged': True,
        'scope': 'Mechanical original-row/clock/coverage join only. Unsupported/missing required results are U; frozen N/A is separate. Source-only cannot promote an old public gate. Shared incomplete development/preparation cost remains unknown.'}
    archive.save(output / 'JOIN-RECEIPT.json', receipt)
    for p in output.iterdir():
        p.chmod(0o444)
    print(json.dumps({'metric_input': ref(output / 'METRIC-INPUT.json'),
                      'metric_results': ref(output / 'METRIC-RESULTS.json'),
                      'join_receipt': ref(output / 'JOIN-RECEIPT.json')}, sort_keys=True))


if __name__ == '__main__':
    main()
