#!/usr/bin/env python3
"""One finite no-delete audit of the healthy-v2 derived SPEC duplicate."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import time

R = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward')
O = R / 'operators/regenerable-derived-spec-supplement-independent-v1'
T = R / 'cache/publication-archives/closed-synthetic-host-v2/SPEC.json'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def ident(st):
    return {'device': st.st_dev, 'inode': st.st_ino, 'mode': format(stat.S_IMODE(st.st_mode), '04o'),
            'uid': st.st_uid, 'gid': st.st_gid, 'nlink': st.st_nlink, 'size_bytes': st.st_size,
            'allocated_file_bytes': st.st_blocks * 512, 'mtime_ns': st.st_mtime_ns, 'ctime_ns': st.st_ctime_ns}


def physical(p):
    need(p.is_absolute() and str(p) == os.path.normpath(str(p)), 'Canonical absolute path required')
    for q in [p, *p.parents]:
        need(not q.is_symlink(), 'No symlink ancestors permitted')
    return p


def opened(p):
    physical(p)
    before = ident(p.lstat())
    need(stat.S_ISREG(p.lstat().st_mode), 'Ordinary file required')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    need(ident(os.fstat(fd)) == before, 'Open changed identity')
    return fd, before


def digest(p):
    fd, before = opened(p)
    try:
        h = hashlib.sha256()
        while True:
            b = os.read(fd, 1024 * 1024)
            if not b:
                break
            h.update(b)
        need(ident(os.fstat(fd)) == before, 'File changed during hash')
    finally:
        os.close(fd)
    need(ident(p.lstat()) == before, 'Hashed path changed')
    return h.hexdigest(), before


def ref(p, expected=None):
    actual, _ = digest(p)
    need(expected is None or actual == expected, 'External byte pin differs: ' + str(p))
    return {'path': str(p), 'sha256': actual}


def pinned(p, expected):
    r = ref(p, expected)
    return json.loads(p.read_bytes()), r


def write(name, value):
    p = O / name
    with p.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    p.chmod(0o444)
    return ref(p)


def under(p, root):
    return p == root or p.is_relative_to(root)


def main():
    start = time.time()
    cache = physical(R / 'cache')
    cache_before = ident(cache.lstat())
    need((cache_before['device'], cache_before['inode']) == (16777232, 26682812), 'Wrong cache namespace')
    owner_ref = ref(cache / 'OWNER.json', 'd62df53bd1dee9691e40e34e02b6e8006e07258b8dff46053b656ec9ceb18a55')
    owner_authority = ref(R / 'operators/cache-current-identity.json', '009fca95e7793f750b8cca67efaa1abf46f15f9c54b7501c70e3cb442ba1c210')
    ancestry = {str(p): ident(p.lstat()) for p in [T.parent, *T.parent.parents] if under(p, cache)}
    target_sha, target_id = digest(T)
    need(target_id['device'] == cache_before['device'] and target_id['uid'] == cache_before['uid']
         and target_id['gid'] == cache_before['gid'] and target_id['mode'] == '0444' and target_id['nlink'] == 1,
         'Target ordinary ownership/mode/link count differs')

    transport, transport_ref = pinned(R / 'publications/closed-synthetic-host-v1/TRANSPORT.json',
        'a6641b4e42d8ea542db0cafa91d5677c7b344ad6de79b10ff512fdf7e1bc9a21')
    need(transport['index_sha256'] == '375b0c2a638a73ccf813b45531a6a9ec0f6f82093bf502fa007cdc3277d1a273', 'Wrong healthy inner archive')
    entry = transport['files']['SPEC.json']
    need(entry['stored'] == 'SPEC.json.gz', 'Only the literal frozen SPEC member is audited')
    need(target_sha == entry['sha256'] and target_id['size_bytes'] == entry['bytes'], 'Current input SPEC differs from transported bytes')
    compressed = Path(transport_ref['path']).parent / entry['stored']
    stored_sha, stored_id = digest(compressed)
    need(stored_sha == entry['stored_sha256'] and stored_id['size_bytes'] == entry['stored_bytes'], 'Stored gzip pin differs')
    fd, gzip_before = opened(compressed)
    raw_hash = hashlib.sha256(); raw_length = 0
    with os.fdopen(fd, 'rb') as original:
        with gzip.GzipFile(fileobj=original, mode='rb') as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                raw_hash.update(chunk); raw_length += len(chunk)
                need(raw_length <= entry['bytes'], 'Expansion exceeds declared raw bytes')
        need(ident(os.fstat(original.fileno())) == gzip_before, 'Gzip file changed during decode')
    need(ident(compressed.lstat()) == gzip_before, 'Gzip path changed')
    need(raw_hash.hexdigest() == entry['sha256'] and raw_length == entry['bytes'], 'Complete gzip restoration differs')

    main_spec, main_spec_ref = pinned(R / 'cache/publication-archives/closed-business-main-v2/SPEC.json',
        '01d572c64bc51a8e905b0eeb57b694f4ef2f9f395ead373f3163439ed08f9e10')
    plan, plan_ref = pinned(R / 'operators/main-preservation-plan-v3/PLAN.json',
        'ff9568246013be8bb2962543be256bb2203fb4ed7145108c292c44321e52c558')
    native, native_ref = pinned(Path(plan['native_recorded_readset']['path']), plan['native_recorded_readset']['sha256'])
    history, history_ref = pinned(Path(plan['history_ledger']['path']), plan['history_ledger']['sha256'])
    need(native['snapshot'] == plan['native_snapshot'], 'Native readset snapshot binding differs')
    need(history['status'] == 'complete' and not history.get('failures') and len(history['versions']) == 20, 'History metadata incomplete')
    historical = {x['original_path'] for x in history['versions']}
    prefix_journals = set(plan['recorded_prefix_journal_paths'])
    required = {p for p in native['files_read'] if p not in historical | prefix_journals}
    required.update(x['path'] for x in plan['additional_required_refs'])
    required.update(x['copy']['path'] for x in history['versions'])
    required.update(plan[k]['path'] for k in ['native_snapshot', 'history_ledger', 'native_recorded_readset', 'occurrence_input', 'occurrence_recorded_result'])
    protected = {x['path'] for x in main_spec['files']} | required | set(plan['subject_files']) | prefix_journals
    roots = [Path(x) for x in plan['source_roots'] + plan['protected_plain_code_roots']]
    path_hits = [p for p in protected if p == str(T)]
    root_hits = [str(p) for p in roots if under(T, p)]
    inode_hits = []
    missing = []
    for raw in sorted(protected):
        p = Path(raw)
        if not p.exists():
            missing.append(raw); continue
        s = p.lstat()
        if (s.st_dev, s.st_ino) == (target_id['device'], target_id['inode']):
            inode_hits.append(raw)
    need(not path_hits and not root_hits and not inode_hits and not missing, 'Declared evidence/readset protection intersection or missing protected input')

    cold_end, cold_end_ref = pinned(R / 'operators/cold-revalidation-v1/END.json',
        'fefef4b2fb333a4a9a0c81c8e75f43bd45335922e9789a64ce10f6d84f2aa214')
    synthetic = [x for x in cold_end['inner_archive_stream_verifications'] if x['name'] == 'synthetic']
    need(cold_end['status'] == 'verified' and len(synthetic) == 1 and synthetic[0]['result']['status'] == 'verified'
         and synthetic[0]['result']['index_sha256'] == transport['index_sha256'], 'Prior complete inner verification differs')
    inner_receipt = synthetic[0]['receipt']; ref(Path(inner_receipt['path']), inner_receipt['sha256'])
    qualify, qualify_ref = pinned(R / 'operators/qualification-restore-cleanup-v1/INTENT.json',
        '01bfd090862644f90b099ad632082f09a386279717c17e500a7df428903b72c4')
    qualify_end, qualify_end_ref = pinned(R / 'operators/qualification-restore-cleanup-v1/END.json',
        'b5c81d26999dd4c19e7987c6fd63de2bcee421579c3289c62e2aaa78db82903d')
    need(qualify['all_mapped_files_reverified'] == 82407 and qualify['exact_member_set'] is True
         and qualify_end['status'] == 'closed' and qualify_end['original_map_retained'] is True,
         'Prior full qualification restore proof differs')
    old_map = ref(Path(qualify['map']['path']), '5c6d03b7d31fa586b010081f5f8017d1905e6fcb92e0f89ecd27202630f0c4d1')
    previous_freeze = ref(R / 'operators/regenerable-headroom-independent-v1/REVIEW-FREEZE.json',
        'be58b48b5e775fc0f7513fd8c570ae6db798b953c93f7201b404f0533c3ff394')
    need(ident(T.lstat()) == target_id and ident(cache.lstat()) == cache_before, 'Target/cache changed')
    need(all(ident(Path(p).lstat()) == v for p, v in ancestry.items()), 'Target ancestry changed')
    absent = R / 'cache/publication-archives/closed-qualification-v1/SPEC.json'
    need(not absent.exists() and not absent.is_symlink(), 'Previously absent second target now exists; scope must be reviewed')

    result = write('RESULT.json', {
        'version': 1, 'kind': 'independent-one-derived-input-spec-duplicate-audit', 'status': 'current-byte-proof-complete-no-deletion-authority',
        'target': {'path': str(T), 'sha256': target_sha, 'identity': target_id},
        'cache_owner': owner_ref, 'cache_identity_authority': owner_authority, 'cache_identity': cache_before,
        'target_ancestry': ancestry, 'transport': transport_ref, 'literal_spec_member': entry,
        'stored_gzip': {'path': str(compressed), 'sha256': stored_sha, 'identity': stored_id},
        'complete_gzip_eof_crc_and_isize_verified': True, 'expanded_sha256': raw_hash.hexdigest(), 'expanded_bytes': raw_length,
        'main_spec': main_spec_ref, 'main_plan': plan_ref, 'main_spec_file_count': len(main_spec['files']),
        'native_readset': native_ref, 'history_metadata': history_ref, 'immutable_required_refs_checked': len(required),
        'all_protected_paths_checked': len(protected), 'path_intersections': path_hits, 'protected_root_intersections': root_hits,
        'physical_inode_intersections': inode_hits, 'missing_protected_paths': missing,
        'grade_or_readset_dependency_found': False,
        'dependency_scope': 'Exact declared main-SPEC, native recorded files_read, frozen preserve.immutable_requirements composition, subjects, history-copy and prefix-journal metadata. No grade product body was read; arbitrary unregistered prose references are not claimed audited.',
        'prior_complete_cold_inner_revalidation': cold_end_ref, 'prior_synthetic_inner_verification': synthetic[0],
        'prior_full_82407_qualification_restore_intent': qualify_ref, 'prior_qualification_restore_cleanup_end': qualify_end_ref, 'old_map_preserved': old_map,
        'prior_66_member_freeze_unchanged': previous_freeze,
        'absent_second_target': {'path': str(absent), 'exists': False, 'counted_reclaimable_bytes': 0, 'substitute_control_original_selected': False},
        'additional_candidate_allocated_file_bytes': target_id['allocated_file_bytes'],
        'candidate_only': True, 'deletion_authorized': False, 'deletion_performed': False,
        'sdk_git_or_device_commands_executed': False, 'archive_decoded_to_disk': False, 'existing_source_or_results_modified': False,
        'limits': ['Point-in-time ordinary POSIX identity/byte proof; root must independently admit exact current inode/mode before any cleanup.',
                   'st_blocks*512 is allocated-file accounting, not guaranteed freed APFS physical storage.',
                   'Only the exact healthy-v2 cache input SPEC is proposed. Failed synthetic-v1 SPEC, main SPEC, cold bytes and operator selection/control originals remain protected.'],
        'started_at_unix': start, 'finished_at_unix': time.time()})
    readme = ('Only closed-synthetic-host-v2 cache input SPEC is proposed for independent root cleanup admission. '
              'It is the exact literal SPEC.json recovered from externally pinned closed-synthetic-host-v1 cold: '
              'current no-follow SHA/length, stored gzip SHA/length, complete gzip EOF CRC/ISIZE and expanded SHA/length agree. '
              'Main-SPEC, declared original native/history/required-ref and physical-inode intersections are zero. '
              'Existing full inner revalidation and qualification 82407 full restore proofs remain pinned. '
              'The qualification cache SPEC is absent and contributes zero bytes; no operator control substitute was selected. '
              'No deletion/SDK/Git/grade judgment/archive-on-disk decode occurred. Previous 66-member seal remains unchanged.\n')
    p = O / 'README.md'
    with p.open('x') as f:
        f.write(readme); f.flush(); os.fsync(f.fileno())
    p.chmod(0o444); (O / 'audit.py').chmod(0o444)
    artifacts = [{'path': str(p), 'sha256': digest(p)[0], 'size_bytes': p.stat().st_size, 'sealed_mode': '0444'} for p in sorted(O.iterdir())]
    freeze = write('REVIEW-FREEZE.json', {'version': 1, 'kind': 'one-derived-spec-independent-supplement-freeze',
        'result': result, 'artifact_count': len(artifacts), 'artifact_manifest': artifacts,
        'scope': 'Exact no-delete source/byte/identity audit only; does not change or enlarge prior sealed candidates.'})
    print(json.dumps({'result': result, 'freeze': freeze, 'additional_candidate_allocated_bytes': target_id['allocated_file_bytes'],
                      'immutable_required_refs_checked': len(required), 'all_protected_paths_checked': len(protected),
                      'no_deletion': True}), flush=True)


if __name__ == '__main__':
    main()
