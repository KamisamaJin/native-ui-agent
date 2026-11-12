"""Bounded synthetic selection/transport controls; no actual study application.

The tiny synthetic readset/history metadata tests selection boundaries only.
It is deliberately not a new native/controller/history proof generator.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import traceback

import preserve as p


def run(output):
    output = Path(output).absolute();p.need(not output.exists(), 'Fresh synthetic output required')
    output.mkdir(parents=True);project = output/'project';study = project/'study';study.mkdir(parents=True)
    records = []
    def put(path, data=b'fixture\n'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False, sort_keys=True).encode())
        return path
    def ref(path):return p.reference(path)
    def case(name, fn):
        try:
            details = fn();records.append({'name': name, 'status': 'passed', 'evidence': details})
        except BaseException as error:
            records.append({'name': name, 'status': 'failed', 'error_type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()})
    def rejected(fn, message):
        try:fn()
        except (ValueError, KeyError) as error:
            p.need(message in str(error), 'Wrong rejection boundary: '+str(error));return str(error)
        raise AssertionError('Hostile input was accepted')
    retained = put(study/'HOST/native/retained.json', {'transport_failed': True, 'scope': 'synthetic preserved failure'})
    ignored = put(study/'review/fixtures/raw.json', {'opaque': 'ignored generic input'})
    result = put(study/'results/failed.json', {'failed': True})
    cold = put(study/'cold-fixture/item.json');near_cold = put(study/'cold-fixture-sibling/keep.txt')
    failed = put(study/'cache/business/run-cohort2/failed-request.json', {'failed': True})
    workspace = study/'cache/business/workspace'
    subject = put(workspace/'reply/src/subject.kt', b'// exact selected subject\n')
    placement = put(workspace/'reply/build.gradle.kts', b'// exact declared placement\n')
    license_file = put(workspace/'reply/LICENSE', b'Synthetic stock license\n')
    unselected_upstream = put(workspace/'reply/unselected-upstream.txt')
    sdk = put(study/'cache/business/regenerable/sdk-module.bin')
    plain = put(project/'plain/tool.py', b'# exact frozen code\n')
    active = put(study/'operators/meter.jsonl', b'{"n":1}\n')
    journal = put(study/'journals/owned.jsonl', b'{"n":1}\n')
    journal_old_pin = ref(journal);journal.write_bytes(journal.read_bytes()+b'{"n":2}\n')
    raw_original = ('{\n  "path": "'+str(subject)+'",\n  "text": "π unchanged"\n}\n').encode()
    original_json = put(study/'request.json', raw_original)
    snapshot = put(study/'snapshot.json', {'synthetic_selection_only': True})
    versions = []
    for n in range(20):
        archived = put(study/'history/versions'/('%02d.txt' % n), ('historical bytes %02d\n' % n).encode())
        versions.append({'original_path': str(study/'cache/business/T1/B/hidden-workflow'/('%02d.json' % n)),
                         'copy': ref(archived), 'required_sha256': ref(archived)['sha256']})
    history = put(study/'history/LEDGER.json', {'status': 'complete', 'failures': [], 'versions': versions,
                    'scope': 'Selector-only metadata; frozen HistoryReader still independently validates full proofs during real replay'})
    native = put(study/'native-result.json', {'snapshot': ref(snapshot), 'code_sha256': p.PINS['native_chain'],
                 'files_read': {str(original_json): ref(original_json)['sha256'], str(subject): ref(subject)['sha256'],
                                str(journal): journal_old_pin['sha256'], **{v['original_path']: v['required_sha256'] for v in versions}}})
    feature = put(study/'feature.json', {'synthetic_selection_only': True})
    feature_result = put(study/'feature-result.json', {'synthetic_selection_only': True})
    proof = put(project/'controls/closed-proof.json', {'synthetic_authority_only': True})
    closure = {'kind': 'root-final-preservation-closure-v1', 'version': 1, 'closed': True, 'pending': [],
               'proof_refs': {name: ref(proof) for name in p.PROOFS}, 'portable_source_domain_evaluation': 'unsupported',
               'portable_source_responsibility_evaluation': 'unsupported'}
    compile_dir = study/'cache/business/initial/T1/compile-attempt-1/ios'
    command = put(compile_dir/'command.json', {'platform': 'ios', 'argv': ['xcodebuild', 'build-for-testing', '-project',
                 str(compile_dir/'project/Observer.xcodeproj'), '-derivedDataPath', str(compile_dir/'DerivedData'),
                 '-resultBundlePath', str(compile_dir/'compile.xcresult')]})
    derived = put(compile_dir/'DerivedData/SDKModule.bin');xcresult = put(compile_dir/'compile.xcresult/record.bin')
    compiler_log = put(compile_dir/'compiler.log');compile_result = put(compile_dir/'RESULT.json', {'synthetic_compiler_metadata': True})
    compile_project = put(compile_dir/'project/Observer.xcodeproj/project.pbxproj')
    scratch = p.compile_scratch_exclusion(ref(command), study)
    plan = {'kind': 'finite-actual-preservation-plan-v1', 'version': 1, 'project_root': str(project), 'study_root': str(study),
        'static_roots': [str(study)], 'cache_evidence_roots': [str(study/'cache/business')], 'workspace_exclusions': [str(workspace)],
        'regenerable_cache_exclusions': [str(sdk.parent), scratch['path']], 'compile_scratch_exclusions': [scratch],
        'already_cold_roots': [str(cold.parent)], 'source_roots': [str(subject.parent)], 'subject_files': [str(placement), str(license_file)],
        'plain_code_roots': [str(plain.parent)], 'active_streams': [{'path': str(active), 'stop_path': None}],
        'recorded_prefix_journal_paths': [str(journal)], 'native_recorded_readset': ref(native), 'native_snapshot': ref(snapshot),
        'history_ledger': ref(history), 'occurrence_input': ref(feature), 'occurrence_recorded_result': ref(feature_result),
        'additional_required_refs': [ref(command)], 'protected_active_shells': [str(study/'cache/business/run-cohort2'), str(study/'cache/business'), str(study/'cache')],
        'protected_plain_code_roots': [str(plain.parent)]}
    plan_path = put(project/'controls/PLAN.json', plan);closure_path = put(project/'controls/CLOSURE.json', closure)
    selected = p.candidates(plan)[1]
    def inclusion():
        p.need({retained, ignored, result, failed, near_cold, subject, placement, license_file, plain} <= selected, 'Required category missing')
        return {'required_parallel_categories': 9, 'retained_failed_inputs': 3}
    case('static HOST/results/fixtures and actual native failures are selected', inclusion)
    def exclusions():
        p.need(not {cold, unselected_upstream, sdk, active, derived} & selected, 'Excluded upstream/cache/active bytes selected')
        p.need({xcresult, compiler_log, compile_result, compile_project, command} <= selected, 'Compiler proof accidentally dropped')
        return {'excluded_categories': 5, 'compiler_proof_members_retained': 5}
    case('exact cold/workspace/DerivedData exclusions retain compiler proofs', exclusions)
    def pending():
        incomplete = copy.deepcopy(closure);incomplete['closed'] = False
        error = rejected(lambda: p.prepare(plan, incomplete, project/'blocked-pending'), 'Final closure is pending')
        p.need(not (project/'blocked-pending').exists(), 'Pending closure created output')
        return error
    case('pending final closure rejects before output creation', pending)
    def gate_errors():
        missing = copy.deepcopy(closure);missing['proof_refs'].pop('final_binding')
        boolean = copy.deepcopy(closure);boolean['version'] = True
        bad_pin = copy.deepcopy(closure);bad_pin['proof_refs']['final_binding']['sha256'] = '0'*64
        manufactured = copy.deepcopy(closure);manufactured['portable_source_domain_evaluation'] = 'P'
        return [rejected(lambda: p.gate(missing), 'Every finite'), rejected(lambda: p.gate(boolean), 'Final closure'),
                rejected(lambda: p.gate(bad_pin), 'External metadata pin'), rejected(lambda: p.gate(manufactured), 'Unsupported evaluator')]
    case('missing proof/int-bool/bad pin/manufactured source P reject', gate_errors)
    def requirements():
        refs, historical = p.immutable_requirements(plan)
        p.need(len(historical) == 20 and str(journal) not in refs and not (set(refs) & historical), 'Historical/current journal versions confused')
        p.need(all(row['copy']['path'] in refs for row in versions), 'Historical copy missing')
        return {'historical_copy_refs': 20, 'full_final_journal_old_prefix_not_substituted': True}
    case('historical copies and extending full journals remain distinct', requirements)
    def exclusions_refusal():
        mutant = copy.deepcopy(plan);mutant['additional_required_refs'].append(ref(derived))
        return rejected(lambda: p.prepare(mutant, closure, project/'blocked-required-scratch'), 'Required verifier bytes lie')
    case('required immutable bytes forbid compiler scratch exclusion', exclusions_refusal)
    def exclusion_retarget():
        wrong = p.read_json(command);wrong['argv'][wrong['argv'].index('-derivedDataPath')+1] = str(compile_dir/'compile.xcresult')
        changed = put(project/'controls/retarget-command.json', wrong)
        return rejected(lambda: p.compile_scratch_exclusion(ref(changed), study), 'Unexpected compile-command namespace')
    case('undeclared command path cannot authorize scratch exclusion', exclusion_retarget)
    def missing_ref():
        mutant = copy.deepcopy(plan);mutant['additional_required_refs'].append({'path': str(study/'missing.bin'), 'sha256': '0'*64})
        return rejected(lambda: p.prepare(mutant, closure, project/'blocked-missing'), 'Unresolved selected bytes')
    case('missing required original blocks inventory', missing_ref)
    def changed_ref():
        mutant = copy.deepcopy(plan);mutant['additional_required_refs'].append({'path': str(original_json), 'sha256': '0'*64})
        return rejected(lambda: p.prepare(mutant, closure, project/'blocked-changed'), 'Conflicting required input pins')
    case('changed required original pin blocks inventory', changed_ref)
    def outside_ref():
        outside = put(output/'outside-project.bin')
        mutant = copy.deepcopy(plan);mutant['additional_required_refs'].append(ref(outside))
        return rejected(lambda: p.prepare(mutant, closure, project/'blocked-external'), 'Unknown required ref outside project')
    case('unknown required input outside project blocks instead of broadening', outside_ref)
    def prefix():
        old = active.read_bytes();row = p.capture_prefix(active, output/'single-prefix.jsonl')
        with active.open('ab') as stream:stream.write(b'{"n":2}\n')
        p.need(Path(row['copy']['path']).read_bytes() == old and p.sha(old) == row['prefix_sha256'] and not row['full_original_complete'], 'Prefix/currentsuffix confused')
        p.need(row['copy']['path'] != row['original_path'], 'Prefix aliases original key')
        return row
    case('active prefix immutable despite suffix append; never original alias', prefix)
    def cleanup():
        rejections = []
        for target in [study/'cache', study/'cache/business', study/'cache/business/run-cohort2', plain.parent, project, active.parent]:
            try:p.cleanup_scope_check(plan, target)
            except ValueError as error:rejections.append(str(error))
            else:raise AssertionError('Protected cleanup scope accepted')
        permitted = p.cleanup_scope_check(plan, failed)
        p.need(permitted['cleanup_authorized'] is False, 'Scope check grants deletion')
        p.need(p.cleanup_scope_check(plan, study/'cache/business/run-cohort2', meters_closed=True)['cleanup_authorized'] is False, 'Closed meter grants deletion')
        return {'protected_scopes_rejected': len(rejections), 'child_scope_only_never_ownership_or_delete_permission': True}
    case('active meter shells and plain code protected; child scope grants no cleanup', cleanup)
    def symlink():
        link = output/'link-to-selected.txt';link.symlink_to(subject)
        files, structural, unknown = set(), [], []
        p.walk(link, [], set(), files, structural, unknown)
        p.need(not files and not unknown and structural[0]['kind'] == 'symlink-metadata-only', 'Symlink followed')
        return {'no_target_bytes_read': True}
    case('symlink recorded structurally without target following', symlink)
    def unsafe_git():
        unsafe = put(output/'unsafe-fixture/.git/not-a-live-repo', b'opaque hostile fixture\n')
        files, structural, unknown = set(), [], []
        p.walk(unsafe.parent.parent, [], set(), files, structural, unknown)
        p.need(not files and len(unknown) == 1 and 'unsafe fixture/Git bytes' in unknown[0]['reason'], 'Unsafe namespace silently lost/read')
        old = str(unsafe);unsafe.parent.rename(unsafe.parent.parent/'inert-git-fixture')
        inert = unsafe.parent.parent/'inert-git-fixture'/unsafe.name
        p.need(ref(inert)['sha256'] == p.sha(b'opaque hostile fixture\n'), 'Synthetic hostile bytes lost during inert preservation')
        return {'unresolved_safe_copy_or_cold_proof_required': True,
                'synthetic_hostile_input_inert_preservation': {'original_unsafe_key': old, 'copy': ref(inert), 'same_bytes': True,
                    'not_an_ordinary_original_key_Resolver_override': True}}
    case('unsafe Git fixture yields explicit unresolved boundary', unsafe_git)
    transport = {}
    def positive_prepare():
        spec_ref = p.prepare(plan, closure, project/'selection', control_refs=[ref(plan_path), ref(closure_path)])
        spec = p.pinned(spec_ref);names = {row['path'] for row in spec['files']}
        p.need(str(active) not in names and {str(plan_path), str(closure_path), str(proof), str(journal)} <= names, 'Controls/full journals missing or active key substituted')
        p.need(all(row['logical_path'] == 'project/'+Path(row['path']).relative_to(project).as_posix() for row in spec['files']), 'Original namespace rewritten')
        transport.update(spec=spec_ref)
        return {'spec': spec_ref, 'files': len(spec['files']), 'scope': 'Selection only; full recorded native/controller replay deliberately not fabricated'}
    case('successful finite selection preserves controls and original relative namespace', positive_prepare)
    def roundtrip():
        p.need(transport.get('spec'), 'Positive selector prerequisite failed')
        packed = p.A.pack(Path(transport['spec']['path']), output/'archive', 1)
        restored = p.A.restore(output/'archive', output/'readonly-restore', packed['index_sha256'], readonly=True)
        mapping = Path(restored['mapping']);map_pin = p.sha(mapping.read_bytes())
        base = p.R.Resolver(mapping, map_sha256=map_pin, index_sha256=packed['index_sha256'])
        project.rename(output/'removed-original-project')
        p.need(not original_json.exists() and not subject.exists(), 'Original paths still present')
        p.need(base.read_bytes(str(original_json)) == raw_original, 'JSON rewritten or original-path fallback')
        directory = base.directory(str(subject.parent));p.need((directory/subject.name).read_bytes() == b'// exact selected subject\n', 'Directory does not preserve namespace')
        p.need(all(int(row['restored_mode'], 8) & 0o222 == 0 for row in base._rows.values()), 'Restore not readonly')
        live = put(project/'unregistered-live.json', b'live original must not be consulted\n')
        absent_error = rejected(lambda: base.read_bytes(str(live)), 'absent')
        pin_error = rejected(lambda: p.R.Resolver(mapping, map_sha256='0'*64, index_sha256=packed['index_sha256']), 'differs')
        target = base.file(str(original_json));target.chmod(0o644);target.write_bytes(b'X'+raw_original[1:]);target.chmod(0o444)
        corrupted_error = rejected(lambda: base.read_bytes(str(original_json)), 'differs')
        transport.update(index_sha256=packed['index_sha256'], restore_map_sha256=map_pin, selected_files=restored['files'])
        return {'archive_index_sha256': packed['index_sha256'], 'restore_map_sha256': map_pin, 'original_keys_absent': True,
                'JSON_bytes_preserved_before_intentional_corruption': True, 'readonly_files': restored['files'],
                'unregistered_original_rejected': absent_error, 'wrong_map_pin_rejected': pin_error,
                'retained_restored_corruption_rejected': corrupted_error,
                'final_fixture_restore_intentionally_corrupted_after_verified_roundtrip': True}
    case('real archive/Resolver readonly roundtrip then no-fallback and corruption controls', roundtrip)
    report = {'version': 1, 'kind': 'bounded-independent-preservation-host-controls', 'synthetic_only': True,
              'actual_archive_or_cleanup_performed': False, 'passed': sum(row['status'] == 'passed' for row in records),
              'failed': sum(row['status'] == 'failed' for row in records), 'controls': records,
              'limits': ['No newly invented full native/controller cohort fixture; their exact frozen APIs and original recorded readsets are pinned separately.',
                         'Synthetic native/history metadata exercises selector authority only; real replay must still pass the unchanged complete verifiers.',
                         'Source-domain/source-responsibility grading unsupported; no source delivery/product conclusion.',
                         'All failed/corrupt fixture bytes retained; final synthetic restore intentionally contains a rejected corruption.']}
    p.save(output/'RESULT.json', report)
    print(json.dumps({'passed': report['passed'], 'failed': report['failed'], 'result': ref(output/'RESULT.json')}))
    return report['failed'] == 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('--output', type=Path, required=True)
    raise SystemExit(0 if run(parser.parse_args().output) else 1)
