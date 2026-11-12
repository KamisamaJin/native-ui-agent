"""Finite actual-study preservation selection/replay. No cleanup or SDK API.

Original JSON/absolute keys are never rewritten. A plan/closure pin is external
operator authority, not a product verdict or independent ownership certificate.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import stat

HERE = Path(__file__).resolve().parent
PINS = {
    'archive': 'c412b03c20c9c97b59a550bd5afa02c4c6fd58d0fbd6f9dc81a3bdf9b02796b8',
    'resolver': '2a5ec0949b5a64cb3f1dc57df87b3954e1f5e1f21ea58defec3ced44b5ba8204',
    'native_chain': '7c255b750389c5b5de2b90244e2952d4da55d0b3ff1819b9e0c2fbe8ce28028f',
    'history_view': '309ed801daca9f5ead0ccf0b7f9b956da4cf77a5d9d2f285d45548c441d8104b',
    'audit': 'c56cc5a59049f9016773415ba940f11281855646937decce05508179476e50e3',
    'replay_occurrences_v2': '690076c6375bad6568dc8ad0357db33166f8c7b9f1599563f363418653cec937',
}
PROOFS = {'final_binding', 'all30_alarm_contexts', 'correspondence_and_matcher',
          'actual_only_consensus', 'reveal_barrier', 'metric_input_seal',
          'positive_resource_closure', 'final_static_freeze'}


def need(value, message):
    if not value:raise ValueError(message)


def module(name):
    path = HERE/'vendor'/(name+'.py');raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == PINS[name], 'Frozen code pin differs: '+name)
    spec = importlib.util.spec_from_file_location('preservation_'+name, path)
    result = importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


A = module('archive')
R = module('resolver')


def sha(raw):return hashlib.sha256(raw).hexdigest()
def read_json(path):return A.strict_json(A.read_file(path))
def reference(path):return {'path': str(path), 'sha256': A.file_hash(path)}


def pinned(ref, parse=True):
    raw = A.read_file(A.absolute(ref['path']));need(sha(raw) == A.hexsha(ref['sha256']), 'External metadata pin differs')
    return A.strict_json(raw) if parse else raw


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    A.save(path, value);path.chmod(0o444)
    return reference(path)


def under(path, prefixes):return any(path == p or path.is_relative_to(p) for p in prefixes)


def merge_ref(refs, ref):
    original = str(A.absolute(ref['path']));expected = A.hexsha(ref['sha256'])
    need(original not in refs or refs[original] == expected, 'Conflicting required input pins')
    refs[original] = expected


def compile_scratch_exclusion(command_ref, study_root):
    """Only the exact compiler-declared DerivedData sibling, never logs/results."""
    path = A.absolute(command_ref['path']);study = A.absolute(str(study_root))
    need(path.is_relative_to(study/'cache/business') and path.name == 'command.json'
         and path.parent.name == 'ios' and path.parent.parent.name.startswith('compile-attempt-'), 'Unexpected compile-command namespace')
    record = pinned(command_ref);argv = record.get('argv')
    need(isinstance(argv, list) and all(isinstance(x, str) for x in argv) and argv[:2] == ['xcodebuild', 'build-for-testing']
         and argv.count('-derivedDataPath') == 1 and record.get('platform') == 'ios', 'Explicit iOS compiler scratch command required')
    at = argv.index('-derivedDataPath');need(at+1 < len(argv), 'Missing declared compiler scratch value')
    scratch = A.absolute(argv[at+1]);need(scratch == path.parent/'DerivedData', 'Only exact compile DerivedData sibling can be excluded')
    for option in ['-project', '-resultBundlePath']:
        need(argv.count(option) == 1 and argv.index(option)+1 < len(argv), 'Preserved compiler proof path is missing')
        proof = A.absolute(argv[argv.index(option)+1]);need(not under(proof, [scratch]), 'Compiler proof aliases excluded scratch')
    return {'path': str(scratch), 'command_ref': dict(command_ref), 'scope': 'Regenerable compiler DerivedData only; command/log/RESULT/project/xcresult remain selected'}


def validate_plan(plan):
    need(plan.get('kind') == 'finite-actual-preservation-plan-v1', 'Wrong finite plan')
    project, study = A.absolute(plan['project_root']), A.absolute(plan['study_root'])
    need(study.is_relative_to(project), 'Study must retain one project-relative namespace')
    for name in ['static_roots', 'cache_evidence_roots', 'workspace_exclusions', 'regenerable_cache_exclusions', 'already_cold_roots', 'source_roots', 'subject_files', 'plain_code_roots']:
        need(isinstance(plan[name], list), 'Explicit selection list required: '+name)
        for p in plan[name]:need(A.absolute(p).is_relative_to(project), 'Selection outside project; unresolved input must block')
    need(len(plan['active_streams']) == len({x['path'] for x in plan['active_streams']}), 'Duplicate active stream')
    for stream in plan['active_streams']:need(A.absolute(stream['path']).is_relative_to(project), 'External active stream unsupported')
    excluded = [A.absolute(x) for x in plan['regenerable_cache_exclusions']]
    need(not any(under(A.absolute(x), excluded) for x in plan['source_roots']+plan['subject_files']), 'Declared source/subject cannot be dropped as regenerable scratch')
    for record in plan.get('compile_scratch_exclusions', []):
        proof = compile_scratch_exclusion(record['command_ref'], study)
        need(record == proof and record['path'] in plan['regenerable_cache_exclusions'], 'Compile-scratch authority differs')
    return project, study


def gate(closure):
    need(closure.get('kind') == 'root-final-preservation-closure-v1' and type(closure.get('version')) is int and closure['version'] == 1
         and closure.get('closed') is True and closure.get('pending') == [], 'Final closure is pending; actual inventory/pack blocked')
    need(set(closure.get('proof_refs', {})) == PROOFS, 'Every finite final-stage proof ref required')
    for ref in closure['proof_refs'].values():pinned(ref, parse=False)
    need(closure.get('portable_source_domain_evaluation') == 'unsupported'
         and closure.get('portable_source_responsibility_evaluation') == 'unsupported', 'Unsupported evaluator boundaries must remain explicit')


def cleanup_scope_check(plan, target, *, meters_closed=False):
    """Scope rejection only, never deletion permission or an ownership claim."""
    target = A.absolute(str(target))
    protected = [A.absolute(x) for x in plan.get('protected_plain_code_roots', [])]
    need(not any(target == p or target.is_relative_to(p) or p.is_relative_to(target) for p in protected), 'Plain frozen/project code is protected')
    need(not any(A.absolute(x['path']) == target or A.absolute(x['path']).is_relative_to(target) for x in plan['active_streams']), 'Active/final meter streams are protected')
    if not meters_closed:
        need(not any(A.absolute(x) == target or A.absolute(x).is_relative_to(target) for x in plan.get('protected_active_shells', [])), 'Keep exact meter filesystem directory shells until both meters close')
    return {'scope_only': True, 'cleanup_authorized': False, 'positive_ownership_and_replay_still_required': True}


def walk(prefix, excluded, active, files, structure, unknown):
    prefix = Path(str(prefix))
    # archive.absolute intentionally rejects .git keys. Record this discovered
    # boundary before that stricter API; do not inspect Git contents or targets.
    if any(p.casefold() == '.git' for p in prefix.parts):
        need(prefix.is_absolute() and '..' not in prefix.parts, 'Unsafe discovery path')
        structure.append({'path': str(prefix), 'kind': 'excluded-Git-namespace; no target/content read'})
        unknown.append({'path': str(prefix), 'reason': 'unsafe fixture/Git bytes require explicit external cold membership or inert-copy admission'});return
    prefix = A.absolute(str(prefix))
    if under(prefix, excluded) or str(prefix) in active:return
    try:mode = prefix.lstat().st_mode
    except FileNotFoundError:
        unknown.append({'path': str(prefix), 'reason': 'declared root/member missing'});return
    if stat.S_ISLNK(mode):
        structure.append({'path': str(prefix), 'kind': 'symlink-metadata-only', 'target': os.readlink(prefix)});return
    if stat.S_ISDIR(mode):
        for entry in sorted(os.scandir(prefix), key=lambda x: x.name):walk(Path(entry.path), excluded, active, files, structure, unknown)
    elif stat.S_ISREG(mode):
        if any(p.casefold() == '.git' for p in prefix.parts) or '\\' in str(prefix) or stat.S_IMODE(mode) & 0o7000:
            unknown.append({'path': str(prefix), 'reason': 'unsafe ordinary bytes need declared safe-copy preservation'});return
        files.add(prefix)
    else:structure.append({'path': str(prefix), 'kind': 'special-metadata-only', 'mode': format(stat.S_IMODE(mode), '04o')})


def candidates(plan, output=None):
    project, study = validate_plan(plan)
    common_exclusions = [A.absolute(p) for p in plan['already_cold_roots']]
    if output is not None:common_exclusions.append(A.absolute(str(output)))
    active = {x['path'] for x in plan['active_streams']};files, structure, unknown = set(), [], []
    for p in plan['static_roots']:
        excluded = common_exclusions+[study/'cache', study/'publications', study/'qualification']
        walk(p, excluded, active, files, structure, unknown)
    for p in plan['cache_evidence_roots']:
        walk(p, common_exclusions+[A.absolute(x) for x in plan['workspace_exclusions']+plan['regenerable_cache_exclusions']], active, files, structure, unknown)
    for p in plan['plain_code_roots']+plan['source_roots']:
        walk(p, common_exclusions, active, files, structure, unknown)
    for p in plan['subject_files']:
        walk(p, [], active, files, structure, unknown)
    for raw in plan.get('transport_failure_input_roots', []):
        p = A.absolute(raw)
        walk(p, [p/'archive', p/'cold-decoded', p/'readonly-restore'], active, files, structure, unknown)
    return project, files, structure, unknown


def immutable_requirements(plan):
    value = pinned(plan['native_recorded_readset'])
    need(value['snapshot'] == plan['native_snapshot'] and value['code_sha256'] == PINS['native_chain'], 'Recorded native readset binding differs')
    history = pinned(plan['history_ledger'])
    need(history.get('status') == 'complete' and not history.get('failures') and len(history['versions']) == 20, 'Complete final20 historical versions required')
    historical = {r['original_path'] for r in history['versions']}
    # Recorded readsets discover inputs. Full global journals may legitimately
    # extend after a recorded bounded prefix; replay validates original ranges.
    prefix_journals = set(plan.get('recorded_prefix_journal_paths', []))
    refs = {p: h for p, h in value['files_read'].items() if p not in historical|prefix_journals}
    for key in ['native_snapshot', 'history_ledger', 'native_recorded_readset', 'occurrence_input', 'occurrence_recorded_result']:
        ref = plan.get(key);need(isinstance(ref, dict), 'Missing required final replay ref: '+key);merge_ref(refs, ref)
    for row in history['versions']:
        need(row['copy']['sha256'] == row['required_sha256'], 'Historical copy pin differs')
        merge_ref(refs, row['copy'])
    for ref in plan.get('additional_required_refs', []):merge_ref(refs, ref)
    for raw in prefix_journals:
        # Presence/full final bytes are selected separately, never truncated or
        # represented at the original key by a prefix copy.
        need(A.absolute(raw).is_file(), 'Required final journal is missing')
    return refs, historical


def capture_prefix(source, destination):
    """Owned immutable prefix copy, never substituted for a full original key."""
    source = A.absolute(str(source));destination = A.absolute(str(destination))
    fd = A.nofollow_open(source);before = os.fstat(fd);length = before.st_size;h = hashlib.sha256()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open('xb') as out:
            remaining = length
            while remaining:
                block = os.read(fd, min(1024*1024, remaining));need(block, 'Active stream truncated during prefix copy')
                out.write(block);h.update(block);remaining -= len(block)
            out.flush();os.fsync(out.fileno())
        after = os.fstat(fd)
    finally:os.close(fd)
    need((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino) and after.st_size >= length, 'Active stream identity/truncation changed')
    fd = A.nofollow_open(source);second = hashlib.sha256()
    try:
        remaining = length
        while remaining:
            block = os.read(fd, min(1024*1024, remaining));need(block, 'Prefix disappeared');second.update(block);remaining -= len(block)
    finally:os.close(fd)
    need(second.hexdigest() == h.hexdigest(), 'Active prefix bytes changed')
    destination.chmod(0o444)
    return {'original_path': str(source), 'range': {'start': 0, 'end': length, 'unit': 'byte'},
            'prefix_sha256': h.hexdigest(), 'copy': reference(destination), 'bytes': length,
            'full_original_complete': False, 'active_suffix_excluded': True,
            'terminal_supplement_required_after_cleanup': True}


def prepare(plan, closure, output, *, control_refs=()):
    """Select/hash only after explicit final authority. Does not pack/delete."""
    gate(closure);output = A.absolute(str(output));need(not output.exists(), 'Fresh selector output required')
    project, study = validate_plan(plan);need(output.is_relative_to(project), 'Control output must keep one project-relative layout')
    output.mkdir(parents=True)
    refs, historical = immutable_requirements(plan)
    for ref in [*control_refs, *closure['proof_refs'].values()]:
        pinned(ref, parse=False)
        merge_ref(refs, ref)
    excluded = [A.absolute(x) for x in plan['regenerable_cache_exclusions']]
    need(not any(under(A.absolute(raw), excluded) for raw in refs), 'Required verifier bytes lie in proposed scratch exclusion; pack blocked')
    project, paths, structure, unknown = candidates(plan, output)
    for raw in refs:
        p = A.absolute(raw);need(p.is_relative_to(project), 'Unknown required ref outside project; actual pack blocked')
        need(raw not in {x['path'] for x in plan['active_streams']}, 'Full active stream is required; cannot replace original with a prefix')
        walk(p, [], set(), paths, structure, unknown)
    for raw in plan.get('recorded_prefix_journal_paths', []):walk(raw, [], set(), paths, structure, unknown)
    need(not unknown, 'Unresolved selected bytes/unsafe refs block pack; inspect shape-only UNKNOWN metadata')
    prefixes = []
    for n, stream in enumerate(plan['active_streams']):
        prefix = capture_prefix(stream['path'], output/'prefixes'/('%02d.jsonl' % n));prefixes.append(prefix);paths.add(Path(prefix['copy']['path']))
    structural_ref = save(output/'STRUCTURE.json', {'version': 1, 'entries': structure, 'historical_original_keys': sorted(historical),
        'active_prefixes': prefixes, 'no_target_following': True, 'empty_directories_not_historical_absence_proof': True})
    paths.add(Path(structural_ref['path']))
    rows = []
    for p in sorted(paths):
        before = p.lstat();actual = A.file_hash(p);after = p.lstat()
        need(A.identity(before) == A.identity(after), 'Selected file changed during byte inventory')
        if str(p) in refs:need(actual == refs[str(p)], 'Required original changed; no rewriting or fallback')
        rows.append({'root': 'project', 'path': str(p), 'logical_path': 'project/'+p.relative_to(project).as_posix(),
                     'sha256': actual, 'bytes': before.st_size, 'mode': format(stat.S_IMODE(before.st_mode), '04o')})
    _project, again, _structure, again_unknown = candidates(plan, output)
    need(not again_unknown and again <= paths and paths-{Path(x['copy']['path']) for x in prefixes}-{Path(structural_ref['path'])} <= again|{Path(p) for p in refs}|{Path(p) for p in plan.get('recorded_prefix_journal_paths', [])}, 'Selection membership changed')
    spec = {'version': 1, 'roots': [{'id': 'project', 'kind': 'evidence', 'path': str(project)}], 'files': rows}
    A.spec_validate(spec);spec_ref = save(output/'SPEC.json', spec)
    save(output/'PREPARED.json', {'version': 1, 'kind': 'explicit-actual-archive-inputs', 'spec': spec_ref,
        'selected_files': len(rows), 'source_bytes': sum(r['bytes'] for r in rows), 'active_prefixes': prefixes,
        'closure_is_external_operator_authority_not_product_judgment': True, 'pack_performed': False, 'cleanup_performed': False,
        'scope': 'One project-relative original-key layout; final raw meter tails and terminal control records remain a separate mandatory supplement.'})
    return spec_ref


def replay(plan, archive, index_sha, restore_map, map_sha):
    """Frozen archive/Resolver + public/native-history/occurrence replay only."""
    A.verify(A.absolute(str(archive)), index_sha)
    base = R.Resolver(restore_map, map_sha256=map_sha, index_sha256=index_sha)
    need(all(int(row['restored_mode'], 8) & 0o222 == 0 for row in base._rows.values()), 'Readonly restore required')
    public = module('audit').verify_run(base, str(Path(plan['study_root'])/'cache/business/run-cohort2'), require_hidden_authorization=True)
    history = module('history_view').HistoryReader(base, plan['history_ledger'])
    native = module('native_chain').verify_chain(history, plan['study_root'], plan['native_snapshot'])
    occurrence = module('replay_occurrences_v2').replay(base, plan['occurrence_input'])
    need(public.get('status') == native.get('status') == occurrence.get('status') == 'verified', 'Recorded replay failed; preserve failure and block cleanup')
    need(native.get('terminal_scopes') == 30 and native.get('pending_scopes') == [], 'Whole thirty terminal scopes required, without inferring product pass')
    # Verify all mapped bytes again after the pure replays, not just returned Paths.
    for original in base._rows:base.hash(original)
    A.verify(A.absolute(str(archive)), index_sha)
    return {'version': 1, 'kind': 'readonly-recorded-provenance-replay-receipt', 'status': 'verified',
        'archive_index_sha256': index_sha, 'restore_map_sha256': map_sha, 'public_events': public.get('event_count'),
        'native_terminal_scopes': native.get('terminal_scopes'), 'native_acquired_scopes': native.get('acquired_scopes'),
        'native_acquisition_complete': native.get('acquisition_complete'), 'public_occurrence_windows': len(occurrence['records']),
        'source_domain_evaluation': 'unsupported', 'source_responsibility_evaluation': 'unsupported',
        'current_source_delivery_verified': False, 'cleanup_authorized': False,
        'meter_terminal_and_postcleanup_control_supplement_pending': True,
        'scope': 'Byte/record integrity only. Root must separately validate cold transports, positive ownership/closed resources and exact cleanup intent; no SDK or deletion here.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__);sub = parser.add_subparsers(dest='command', required=True)
    for name in ['shape', 'prepare', 'replay']:
        p = sub.add_parser(name);p.add_argument('--plan', type=Path, required=True);p.add_argument('--plan-sha256', required=True);p.add_argument('--output', type=Path, required=True)
        if name == 'prepare':p.add_argument('--closure', type=Path, required=True);p.add_argument('--closure-sha256', required=True)
        if name == 'replay':
            for key in ['archive', 'index-sha256', 'restore-map', 'map-sha256']:p.add_argument('--'+key, required=True)
    a = parser.parse_args();plan = pinned({'path': str(a.plan), 'sha256': a.plan_sha256})
    if a.command == 'prepare':
        try:result = prepare(plan, pinned({'path': str(a.closure), 'sha256': a.closure_sha256}), a.output,
                            control_refs=[{'path': str(a.plan), 'sha256': a.plan_sha256}, {'path': str(a.closure), 'sha256': a.closure_sha256}])
        except BaseException as error:
            if a.output.is_dir() and not (a.output/'FAILED.json').exists():
                save(a.output/'FAILED.json', {'kind': 'retained-preservation-selection-failure', 'error_type': type(error).__name__, 'message': str(error), 'pack_performed': False, 'cleanup_performed': False})
            raise
    elif a.command == 'shape':
        _project, files, structure, unknown = candidates(plan, a.output)
        result = {'kind': 'shape-only-pending-selection', 'files': len(files), 'logical_bytes_sampled_over_walk': sum(p.stat().st_size for p in files),
                  'structural_entries': structure, 'unresolved': unknown, 'actual_pack_ready': False, 'cleanup_authorized': False,
                  'all_file_byte_hashing_and_final_closure_pending': True}
        save(a.output, result)
    else:
        result = replay(plan, a.archive, a.index_sha256, a.restore_map, a.map_sha256);save(a.output, result)
    print(json.dumps(result if a.command == 'prepare' else {k: v for k, v in result.items() if k not in {'structural_entries', 'unresolved'}}))


if __name__ == '__main__':main()
