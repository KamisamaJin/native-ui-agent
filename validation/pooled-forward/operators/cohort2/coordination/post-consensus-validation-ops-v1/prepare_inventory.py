#!/usr/bin/env python3
"""Prepare finite commands and mechanical pins only. No operation execution."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

R = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward')
C = R/'operators/cohort2/coordination'
OUT = Path(__file__).resolve().parent
RUN = R/'cache/business/run-cohort2'
EVIDENCE = R/'cache/business/independent-evaluation'
FUTURE = EVIDENCE/'post-consensus-validation-v1'
PINS = {
    'runner': (C/'independent_native_v3.py', '7672ec99ca986a149d303eb8e37fb81da71edf1826c6eb1273da534945ddf722'),
    'source_only': (R/'publication-source-only-binding-review/revision-v2/source_only_binding_v2.py', 'b31332d4e845b969c2a076e88721d293c8dd20b580046d38cf70d8d4e5272ced'),
    'source_aliases': (R/'publication-source-alias-review/source_aliases_v2.py', '3cebfbbf2974d96e607d0b5689c93b96a0d3823e1fe91b37505380189eee02e1'),
    'actual_projection': (R/'publication-actual-projection-review/actual_projection_v2.py', 'e9bb0e321d79c107356875ed78660901b361a358efa11717116c741b4f49cd36'),
    'initial_preparation': (R/'cache/business/initial-reference/PREPARATION-SEAL.json', '178b49172cee5c10f9101650e2adfe1c193b54c0720884fa8e4e587f37a10c79'),
    'source_policy': (C/'INDEPENDENT-SOURCE-BINDING-POLICY-v1.json', '8d631ad511f7f097403e954651cbeacb0d1bd9e628e9cda22e133f229598070b'),
    'controller': (R/'business-tools-v4/blind_study.py', '1a52cc62be5cee0bad34fefe8b54a7479761ca5ea5e8981937a8a1ad11ae6b05'),
}


def need(ok, why):
    if not ok: raise ValueError(why)


def safe(raw):
    p = Path(raw)
    need(p.is_absolute() and str(p) == os.path.normpath(str(p)), 'Canonical absolute path required')
    need(not any(q.is_symlink() for q in [p, *p.parents]), 'Symlink rejected')
    return p


def sha(raw):
    h = hashlib.sha256()
    with safe(raw).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): h.update(block)
    return h.hexdigest()


def ref(path): return {'path': str(safe(path)), 'sha256': sha(path)}


def load(path):
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'Duplicate metadata key'); out[key] = value
        return out
    return json.loads(safe(path).read_bytes(), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite metadata')))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def digest(value): return hashlib.sha256(canonical(value)).hexdigest()


def check(pin):
    need(set(pin) == {'path', 'sha256'} and sha(pin['path']) == pin['sha256'], 'Original pin changed')
    return pin


def write(name, value):
    path = OUT/name
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False); stream.write('\n')
    path.chmod(0o444)
    return ref(path)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value


def config_context(pin):
    check(pin); value = load(pin['path']); inputs = {}
    for key in ['plan', 'design_lock', 'policy', 'routes', 'environment', 'fixtures', 'bridge']:
        if value.get(key): inputs[key] = ref(value[key])
    for key in ['coverage_domain_ref', 'coverage_provider_ref']:
        if key in value:
            entry = value[key]
            need(digest(load(entry['path'])) == entry['sha256'], 'Canonical coverage input pin changed')
            inputs[key] = {**ref(entry['path']), 'canonical_sha256': entry['sha256']}
    return value, {'config': pin, 'source_roots': value['source_roots'], 'input_refs': inputs,
                   'original_review_store': value.get('review_store'), 'original_source_review_store': value.get('source_review_store')}


def main():
    need(not FUTURE.exists(), 'Reserved future namespace already exists; do not reuse')
    pinned = {}
    for name, (path, wanted) in PINS.items():
        pinned[name] = ref(path); need(pinned[name]['sha256'] == wanted, 'Admitted helper pin differs: '+name)
    runner = module(PINS['runner'][0], 'post_consensus_prepare_original_runner')
    helper = module(PINS['controller'][0], 'post_consensus_prepare_original_controller')
    study = helper.Study(RUN)  # Constructor verifies metadata/file pins; no cohort/grade call.
    manifest = study.manifest; events = study.events()
    manifest_ref = ref(RUN/'manifest.json'); initial = load(PINS['initial_preparation'][0])
    authorization = load(RUN/'HIDDEN-AUTHORIZATION.json')
    closure_path = R/'publication-native-chain/HOST/actual-whole-pre-binding-v1/RESULT.json'
    closure = load(closure_path)['result']
    need(closure['status'] == 'verified' and closure['terminal_scopes'] == closure['acquired_scopes'] == 30
         and closure['pending_scopes'] == [], 'All30 original native closure required')
    for path_key, hash_key in [('path', 'sha256'), ('meter_path', 'meter_sha256'), ('meter_spec_path', 'meter_spec_sha256')]:
        need(sha(manifest['envelope'][path_key]) == manifest['envelope'][hash_key], 'Original supervision pin changed')
    tool_refs = {name: write('tool-manifest-'+name+'.json', value) for name, value in manifest['tools'].items()}
    monitors = {}
    for key, name in [('original', 'INITIAL-REFERENCE-MONITOR-START.json'), ('continuation', 'INITIAL-REFERENCE-MONITOR-CONTINUATION-START.json')]:
        start = C/name; record = Path(load(start)['record'])
        need((record/'CLOSED.json').is_file(), 'Initial monitor not positively closed')
        command, closed = runner.monitor_gate(R, record, False)
        need(command is None and closed, 'Closed monitor would require a live preflight')
        monitors[key] = {'start': ref(start), 'record': str(record), 'closed': closed}
    locks = {}
    for event in events:
        if event['kind'] == 'source_locked':
            key = (event['task'], event['arm']); need(key not in locks, 'Duplicate source lock')
            locks[key] = {'path': event['source_manifest'], 'sha256': event['source_manifest_sha256']}
    private = []; public = []; operations = []; chain_count = 0
    for task in manifest['tasks']:
        t = task['id']
        for arm in ['I', 'A', 'B']:
            alias = 'A' if arm == 'I' else arm
            arm_info = task['arms'][alias]; tool = manifest['tools'][arm_info['tool']]
            for platform in ['ios', 'android']:
                cfg_pin = initial['tasks'][t][platform]['config'] if arm == 'I' else {
                    k: authorization['hidden_configs'][t][arm][platform][k] for k in ['path', 'sha256']}
                capsule = initial['tasks'][t][platform]['source_manifest'] if arm == 'I' else locks[(t, arm)]
                check(capsule); config, context = config_context(cfg_pin)
                need(helper.source(config['source_roots']) == load(capsule['path']), 'Full current private source differs from original capsule')
                claim = runner.continuation_claim_path(EVIDENCE, t, arm, platform)
                if not claim.exists(): claim = runner.scope_path(EVIDENCE, t, arm, platform)
                claim_value = load(claim); outcome_path = Path(claim_value['record'])/'outcome.json'
                native, native_pin = runner.native_reference(EVIDENCE, t, arm, platform, cfg_pin, capsule, outcome_path, sha(outcome_path))
                capture = native['capture']; cycle = native['cycle']; cap = load(capture['path'])
                cap_root = Path(capture['path']).parent; observation = ref(cap_root/'native/observation.json')
                need(observation['sha256'] == cap['observation_sha256'], 'Original observation pin differs')
                request_path = Path(native['service_output'])/'after-review-request.json'; request = load(request_path)
                catalog = request['catalog']; template = request['submission_template']
                need(request['capture_sha256'] == capture['sha256'] and template['observation_sha256'] == observation['sha256']
                     and template['catalog_sha256'] == digest(catalog), 'Original review/catalog context differs')
                catalog_rows = [{'id': row['id'], 'review_id': row['review_id'], 'state': row['state'], 'method': row['method']}
                                for row in catalog['rows']]
                need(len({row['review_id'] for row in catalog_rows}) == len(catalog_rows), 'Catalog IDs are not unique')
                scope = '/'.join([t, arm, platform]); monitor = monitors['original' if t == 'T1' else 'continuation'] if arm == 'I' else None
                context.update(scope=scope, task=t, arm=arm, platform=platform, tool_key=arm_info['tool'], tool_root=tool['skill_root'],
                    original_claim=ref(claim), native_operation=native_pin, source_capsule=capsule,
                    full_current_source_matches_original_capsule=True, capture=capture, cycle=cycle,
                    original_observation=observation, review_request=ref(request_path),
                    catalog_sha256=template['catalog_sha256'], catalog_rows=catalog_rows,
                    requested_visual_review_ids=[row['review_id'] for row in template['decisions']],
                    allowed_frames='MUST recompute from frozen bound_state_evidence for each exact original state before projection; not inferred here',
                    compiled_responsibility_ref=ref(Path(native['service_output'])/'evidence-responsibility.json'),
                    initial_monitor=monitor)
                private.append(context)
                previous = []
                for action in ['bind-source-review', 'bind-native-review', 'finish-native-review']:
                    opid = '-'.join([t, arm, platform, action]); record = FUTURE/'private'/t/arm/platform/(opid+'-v1')
                    argv = [sys.executable, '-B', str(PINS['runner'][0]), '--root', str(R), '--config', cfg_pin['path'],
                            '--record', str(record), '--task', t, '--arm', arm, '--profile', platform, '--action', action]
                    if arm == 'I': argv += ['--initial-seal', str(PINS['initial_preparation'][0]), '--initial-seal-sha256', PINS['initial_preparation'][1], '--initial-monitor', monitor['record']]
                    if action == 'bind-source-review': argv += ['--submission', '@SUBMISSION@']
                    elif action == 'bind-native-review': argv += ['--native-outcome', native_pin['path'], '--native-outcome-sha256', native_pin['sha256'], '--capture', capture['path'], '--submission', '@SUBMISSION@']
                    else: argv += ['--native-outcome', native_pin['path'], '--native-outcome-sha256', native_pin['sha256'], '--cycle', cycle['path']]
                    operations.append({'id': opid, 'scope': scope, 'kind': 'original-private', 'action': action,
                        'depends_on': list(previous), 'record': str(record), 'argv': argv,
                        'submission_ref': None, 'execution_authorized': False,
                        'wall_source': str(record/'outcome.json')+' :: wall_seconds; shared CLOCK_MONOTONIC endpoints; full original runner entry-to-finally wall',
                        'cost_category': 'post-seal per-arm hidden-binding; preserve separate per-operation wall'})
                    previous.append(opid)
        for arm in ['A', 'B']:
            arm_info = task['arms'][arm]; tool = manifest['tools'][arm_info['tool']]
            for platform in ['ios', 'android']:
                initial_public = ref(arm_info['public_configs'][platform]); active = initial_public; chain = []
                for event in events:
                    if (event['kind'], event.get('task'), event.get('arm'), event.get('profile')) != ('domain_review_admitted', t, arm, platform): continue
                    need(event['parent_config'] == active, 'Nonlinear/stale public config append')
                    check(event['config']); old = load(active['path']); new = load(event['config']['path'])
                    need({k:v for k,v in old.items() if k != 'coverage_domain_ref'} == {k:v for k,v in new.items() if k != 'coverage_domain_ref'}, 'Public config change exceeds frozen append boundary')
                    for key in ['request', 'review_seal', 'provenance']: check(event[key])
                    chain.append({'event': ref(RUN/'events'/f"{event['sequence']:06d}.json"),
                                  **{key: event[key] for key in ['parent_config', 'config', 'request', 'review_seal', 'provenance']}})
                    active = event['config']
                seals = [e for e in events if (e['kind'], e.get('task'), e.get('arm')) == ('self_sealed', t, arm)]
                need(len(seals) == 1 and seals[0]['active_configs'][platform] == active, 'Final self-sealed public config differs')
                config, context = config_context(active); capsule = check(locks[(t, arm)])
                need(helper.source(config['source_roots']) == load(capsule['path']), 'Full current public source differs from original locked capsule')
                scope = '/'.join([t, arm, platform]); record = FUTURE/'public'/t/arm/platform/('-'.join([t, arm, platform, 'source-only-v1']))
                context.update(scope=scope, task=t, arm=arm, platform=platform, original_public_config=initial_public,
                    source_domain_append_chain=chain, final_self_seal_event=ref(RUN/'events'/f"{seals[0]['sequence']:06d}.json"),
                    source_capsule=capsule, full_current_source_matches_original_capsule=True,
                    tool_manifest=tool_refs[arm_info['tool']], tool_key=arm_info['tool'], profile_admission=arm_info['profile_admissions'][platform],
                    full_source_domain_admission_replay='PENDING before execution; only event/config/ref byte chain checked during prepare-only, no review judgments read')
                public.append(context); chain_count += len(chain)
                inner = [sys.executable, '-B', str(PINS['source_only'][0]), '--config', active['path'], '--config-sha256', active['sha256'],
                         '--submission', '@SUBMISSION@', '--submission-sha256', '@SUBMISSION_SHA256@',
                         '--tool-manifest', tool_refs[arm_info['tool']]['path'], '--tool-manifest-sha256', tool_refs[arm_info['tool']]['sha256'], '--output', str(record/'service')]
                argv = runner.forwarding_command(manifest['envelope'], tool['skill_root'], Path(active['path']), record, record/'service', 'source-only', inner)
                operations.append({'id': '-'.join([t, arm, platform, 'public-source-only']), 'scope': scope, 'kind': 'final-public-source-only',
                    'action': 'source-only', 'depends_on': [], 'record': str(record), 'argv': argv,
                    'submission_ref': None, 'execution_authorized': False,
                    'wall_source': 'external whole invocation CLOCK_MONOTONIC wall + original envelope/result.json wall + service/operation.json endpoints + meter.jsonl; keep distinct',
                    'cost_category': 'post-seal common public source-only; never alter original public PR/source-window wall'})
    need(len(private) == 30 and len(public) == 20 and len(operations) == 110, 'Exact finite operation denominator differs')
    need(len({op['id'] for op in operations}) == len({op['record'] for op in operations}) == 110, 'Operation/namespace collision')
    metadata = {'version': 1, 'kind': 'prepare-only-post-consensus-mechanical-context-inventory', 'prepared_at_unix': time.time(),
        'pins': pinned, 'manifest': manifest_ref, 'hidden_authorization': ref(RUN/'HIDDEN-AUTHORIZATION.json'),
        'native_all30_closure': ref(closure_path), 'native_all30_closure_summary': {k:closure[k] for k in ['status','terminal_scopes','acquired_scopes','pending_scopes']},
        'event_chain': {'count': len(events), 'head': ref(RUN/'events'/f"{events[-1]['sequence']:06d}.json")},
        'coordination_context_refs': [ref(C/f'ROOT-CONTINUATION-DELTA-v{i}.json') for i in range(7,14)]+[ref(C/'ROOT-OPERATIONS-HANDOFF-v3.json')],
        'envelope': manifest['envelope'], 'private_contexts': private, 'final_public_contexts': public,
        'verified_public_config_append_steps': chain_count,
        'no_bind_finish_sdk_or_quality_operation_executed': True,
        'no_grade_consensus_assignment_or_actual_mapping_body_read': True,
        'limits': ['Metadata preparation is not operation admission, independent consensus/reveal or a product judgment.',
                   'Public source-domain full admission and every original barrier/profile/full source/tool/config/contract boundary must be reverified at execution.',
                   'No allowed-frame membership or actual citation is invented; frozen state-frame eligibility is still required before projection.',
                   'Initial I public historical review is retained but has no source-only rebind or final denominator entry.']}
    inventory_ref = write('CONTEXTS.json', metadata)
    plan = {'version': 1, 'kind': 'finite-prepare-only-post-consensus-operation-plan', 'root': str(R),
        'contexts': inventory_ref, 'future_namespace': str(FUTURE), 'operation_count': 110,
        'private_context_count': 30, 'private_operation_count': 90, 'final_public_source_only_count': 20,
        'mandatory_per_arm': 8232, 'not_applicable_per_arm': 2100,
        'execution_authorized': False, 'operations': operations,
        'unresolved_execution_gates': ['Root-issued externally pinned sealed independent consensus and reveal/join authority; no matcher substitution.',
            'Exact original cause/alarm/matcher/consensus/reveal/config/source-capsule full caller authentication, without using helper proof as self-authorization.',
            'Per-context source actual-only submission from sealed consensus via pinned source_aliases_v2 and actual_projection_v2, with raw/projection/alias proofs retained.',
            'Per-private-context visual actual-only submission with exact original catalog/observation hashes, original review IDs, and frozen bound_state_evidence frame sets.',
            'Full original public source-domain admission replay, profile admission/tool/config/contract/full source capsule checks immediately before and after each public source-only operation.',
            'Root resource/envelope readiness; retain slow whole-R SourceGuard work and failures, do not replace guards/cleanup/resample.',
            'Root explicit execution release; each operation separately recorded, no multi-action batch.']}
    plan_ref = write('PLAN.json', plan)
    write('PREPARED.json', {'version':1, 'kind':'mechanical-operations-prepare-only-result', 'contexts':inventory_ref, 'plan':plan_ref,
        'private_contexts':30, 'private_operations':90, 'public_source_only_operations':20, 'public_config_append_steps':chain_count,
        'native_reference_validations':30, 'bind_finish_sdk_operations_executed':0, 'execution_authorized':False,
        'future_namespace_created':False, 'status':'prepared-with-explicit-pending-authority-and-caller-gates'})
    print(json.dumps({'status':'prepared-only', 'plan':plan_ref, 'contexts':inventory_ref, 'operations':110, 'execution_authorized':False}))


if __name__ == '__main__': main()
