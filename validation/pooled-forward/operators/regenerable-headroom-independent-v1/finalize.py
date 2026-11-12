#!/usr/bin/env python3
"""Seal the finite read-only inventory and metadata-only qualification entry."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import stat
import time

R = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward')
O = R / 'operators/regenerable-headroom-independent-v1'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def ref(path, expected=None):
    actual = sha(path)
    need(expected is None or actual == expected, 'Pin differs: ' + str(path))
    return {'path': str(path), 'sha256': actual}


def load(path):
    return json.loads(path.read_bytes())


def write(name, value):
    p = O / name
    with p.open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    p.chmod(0o444)
    return ref(p)


def under(p, root):
    return p == root or p.is_relative_to(root)


def main():
    inventory_ref = ref(O / 'INVENTORY.json')
    inv = load(O / 'INVENTORY.json')
    for item in inv['targets']:
        ref(Path(item['inventory']['path']), item['inventory']['sha256'])
    expanded_ref = ref(O / 'EXPANDED-RESULT.json', '63c0f53ac938557ecfb48d59be2f6545e4132b4cf5b1269100294345a7a51b1f')
    expanded = load(O / 'EXPANDED-RESULT.json')
    for key in ['qualification_current', 'benchmark_current', 'workspace_pristine']:
        item = expanded[key]
        ref(Path(item['path']), item['sha256'])
    for key in ['main_spec', 'main_plan', 'owner', 'cache_identity_authority']:
        item = inv[key]
        ref(Path(item['path']), item['sha256'])
    spec = load(Path(inv['main_spec']['path']))
    plan = load(Path(inv['main_plan']['path']))
    protected = {Path(x['path']) for x in spec['files']}
    protected.update(Path(x) for x in plan['subject_files'])
    protected.update(Path(x['path']) for x in plan['additional_required_refs'])
    roots = {Path(x) for x in plan['source_roots'] + plan['protected_plain_code_roots']}
    for w in inv['workspace_proofs']:
        protected.update(Path(x['path']) for x in w['metadata_refs_retained'].values())
        roots.update(Path(x) for x in w['production_source_roots_preserved'])
        stock_path = Path(w['metadata_refs_retained']['STOCK-COPY.json']['path'])
        ref(stock_path, w['metadata_refs_retained']['STOCK-COPY.json']['sha256'])
        stock = load(stock_path)
        dep = stock.get('private_jdk_dependency', {}).get('path')
        if dep:
            protected.add(Path(w['path']) / Path(dep).relative_to(Path(stock['workspace'])))
    for root in roots:
        if root.is_dir() and under(root, R / 'cache'):
            stack = [root]
            while stack:
                p = stack.pop()
                s = p.lstat()
                if stat.S_ISDIR(s.st_mode):
                    stack.extend(Path(e.path) for e in os.scandir(p))
                elif stat.S_ISREG(s.st_mode):
                    protected.add(p)
    rows = []
    inodes = set()
    for p in sorted(protected):
        need(p.exists(), 'Current protected path absent: ' + str(p))
        s = p.lstat()
        if stat.S_ISREG(s.st_mode):
            inodes.add((s.st_dev, s.st_ino))
        rows.append([str(p), s.st_dev, s.st_ino, format(stat.S_IMODE(s.st_mode), '04o'),
                     stat.S_ISREG(s.st_mode), s.st_size, s.st_mtime_ns, s.st_ctime_ns])
    need(len(rows) == inv['protected_paths_count'], 'Protection membership changed')
    lexical_hits = []
    inode_hits = []
    for target in inv['targets']:
        root = Path(target['path'])
        lexical_hits.extend(str(p) for p in protected if under(p, root))
        member_rows = load(Path(target['inventory']['path']))['entries']
        inode_hits.extend(x['path'] for x in member_rows
                          if x['kind'] == 'regular' and (x['device'], x['inode']) in inodes)
    workspace_pristine = load(Path(expanded['workspace_pristine']['path']))
    new_candidates = [(x['path'], x['identity']) for x in expanded['qualification_archive_candidates']]
    new_candidates.extend((x[0], x[2]) for x in workspace_pristine['rows'])
    for raw, expected in new_candidates:
        p = Path(raw)
        st = p.lstat()
        actual = [st.st_dev, st.st_ino, stat.S_IMODE(st.st_mode), st.st_uid, st.st_gid,
                  st.st_nlink, st.st_size, st.st_blocks * 512, st.st_mtime_ns, st.st_ctime_ns]
        need(actual == expected, 'Expanded candidate changed after byte verification: ' + raw)
        need(st.st_dev == 16777232 and st.st_uid == 501 and st.st_nlink == 1,
             'Expanded candidate physical ownership differs')
        if p in protected or any(under(p, root) for root in roots):
            lexical_hits.append(raw)
        if (st.st_dev, st.st_ino) in inodes:
            inode_hits.append(raw)
    need(not lexical_hits and not inode_hits, 'Protected membership intersects candidate inventory')
    protection_ref = write('PROTECTION.json', {
        'version': 1, 'kind': 'point-in-time-protected-path-and-physical-inode-metadata',
        'main_spec': inv['main_spec'], 'main_plan': inv['main_plan'],
        'row_fields': ['path', 'device', 'inode', 'mode', 'regular_file', 'size_bytes', 'mtime_ns', 'ctime_ns'],
        'rows': rows, 'path_count': len(rows), 'regular_inode_count': len(inodes),
        'candidate_path_intersections': lexical_hits, 'candidate_inode_intersections': inode_hits,
        'current_file_bytes_verified': False,
        'expanded_current_byte_result': expanded_ref,
        'expanded_candidates_current_identity_unchanged': len(new_candidates),
        'scope': 'Metadata-only second intersection against all retained old and expanded candidate snapshots; not deletion authority.',
        'recorded_at_unix': time.time()})

    qspec_path = R / 'operators/archive-selection/closed-qualification-v1/SPEC.json'
    qspec_ref = ref(qspec_path, '6e0800372b4b3ee2db5af1c64177a733ab56ac54d754eaf8da8e35606fe1a187')
    qspec = load(qspec_path)
    map_path = R / 'cache/publication-archives/closed-qualification-v1/readonly-restore/RESTORED-MAP.json'
    map_ref = ref(map_path, '5c6d03b7d31fa586b010081f5f8017d1905e6fcb92e0f89ecd27202630f0c4d1')
    oldmap = load(map_path)
    need(len(oldmap['mappings']) == 82407, 'Qualification old-map count differs')
    expected_keys = {x['path'] for x in qspec['files']}
    need(set(oldmap['mappings']) == expected_keys, 'Qualification SPEC/map original-key set differs')
    oldmap_checks = []
    for item in qspec['files']:
        row = oldmap['mappings'][item['path']]
        need(row['sha256'] == item['sha256'] and row['bytes'] == item['bytes'],
             'Qualification map/SPEC byte metadata differs')
    root_counts = Counter()
    for key in oldmap['mappings']:
        matches = [x['id'] for x in qspec['roots'] if under(Path(key), Path(x['path']))]
        need(len(matches) == 1, 'Qualification original-key root ambiguity')
        root_counts[matches[0]] += 1
    transport = R / 'publications/closed-qualification-v1/TRANSPORT.json'
    transport_ref = ref(transport, '941790690a13b58d05e6a4823f73d954eb441dd8c7958e7b2ae9478b84983ef8')
    t = load(transport)
    need(oldmap['index_sha256'] == t['index_sha256'], 'Qualification transport/map index differs')
    prior_end = R / 'operators/qualification-restore-cleanup-v1/END.json'
    prior = load(prior_end)
    need(prior['status'] == 'closed' and prior['original_map_retained'] is True
         and prior['original_qualification_deleted'] is False, 'Prior restore cleanup status differs')
    cold_end = R / 'operators/cold-revalidation-v1/END.json'
    cold_end_ref = ref(cold_end, 'fefef4b2fb333a4a9a0c81c8e75f43bd45335922e9789a64ce10f6d84f2aa214')
    qualification_ref = write('QUALIFICATION-ENTRY.json', {
        'version': 1, 'kind': 'qualification-originals-future-cleanup-entry-only',
        'spec': qspec_ref, 'old_map': map_ref, 'transport': transport_ref,
        'inner_index_sha256': oldmap['index_sha256'],
        'prior_restore_cleanup_end': ref(prior_end),
        'prior_cold_member_and_inner_revalidation_end': cold_end_ref,
        'current_original_byte_mode_physical_proof': expanded['qualification_current'],
        'archived_original_file_count': len(qspec['files']),
        'original_key_scope_counts': dict(root_counts), 'source_roots': qspec['roots'],
        'spec_and_old_map_exact_original_keys_sizes_hashes_agree': True,
        'transport_stored_member_count': len(t['files']),
        'old_map_retained': True, 'benchmark_namespace_archived_by_this_spec': False,
        'current_original_file_bytes_reverified_this_review': True,
        'current_cold_member_bytes_reverified_this_review': False,
        'current_original_physical_ownership_reverified_this_review': True,
        'all_82407_current_bytes_sizes_original_modes_match': True,
        'all_7_original_fixture_symlinks_preserved_not_followed': True,
        'cleanup_admitted': False, 'deletion_performed': False,
        'required_before_any_original_cleanup': [
            'Fresh explicit root authorization for exact original targets; archive/replay closure alone is not deletion authority.',
            'Preserve external old-map, transport and inner-index pins, readonly seals/control records, and exact stored cold-member size/SHA verification.',
            'Revalidate sealed current-byte proof and fresh exact identity/membership before authorized cleanup; this review has hashed all 82407 originals against exact MAP/SPEC size/SHA/original mode.',
            'Recheck all current main-SPEC/required-ref/production-Source/subject/seal/command/log/xcresult/active-meter protections and physical aliases; any intersection blocks cleanup.',
            'Retain the old MAP and all cold/control evidence; retain source-metadata history. Do not stop either original active meter prematurely.',
            'cache/benchmark requires its own exact archived-member and current-byte/physical-owner proof; this qualification SPEC contains no benchmark namespace.'
        ],
        'scope': 'Reports actual 82407 current-original byte/mode proof and candidate entry. Does not decode, delete or grant cleanup permission. All loose code/reports and original links stay.'})

    execution_freeze = R / 'cache/business/independent-evaluation/post-consensus-validation-v1/EXECUTION-FREEZE.json'
    unchanged_execution = ref(execution_freeze, '1218884d892a56feda04b6480e6ab78c42f52a3790ec187ba28303713201de0e')
    sources = [
        R / 'publication-actual-preservation-review/preserve.py',
        R / 'operators/include_rejected_precode_evidence_v2.py',
        R / 'business_workspace.py', R / 'setup_hosts.py',
        R / 'operators/archive_closed_qualification.py',
        R / 'operators/cleanup_qualification_restore_v1.py']
    source_pins = write('SOURCE-PINS.json', {
        'version': 1, 'sources_read_only': [ref(p) for p in sources],
        'authority_refs': [inv[x] for x in ['main_spec', 'main_plan', 'owner', 'cache_identity_authority']],
        'original_110_execution_freeze_unchanged': unchanged_execution,
        'existing_source_or_production_tool_modified': False})
    category = {}
    for item in inv['targets']:
        row = category.setdefault(item['kind'], {'targets': 0, 'regular_files': 0, 'logical_file_bytes': 0,
                                                   'allocated_file_bytes_unique_inodes': 0})
        row['targets'] += 1
        for key in ['regular_files', 'logical_file_bytes', 'allocated_file_bytes_unique_inodes']:
            row[key] += item[key]
    sample = inv['latest_existing_meter_sample']['last_complete_sample']
    budget_remaining = inv['fixed_budget_bytes'] - sample['total_allocated_bytes']
    restore = inv['restore_additional_bytes_estimate_from_root']
    result = {
        'version': 1, 'kind': 'independent-read-only-regenerable-headroom-review', 'status': 'inventory-complete-no-deletion-authority',
        'inventory': inventory_ref, 'protection': protection_ref, 'qualification_entry': qualification_ref,
        'expanded_current_byte_review': expanded_ref,
        'source_pins': source_pins, 'category_totals': category,
        'candidate_targets': len(inv['targets']), 'candidate_regular_file_paths': inv['all_candidate_regular_file_paths'],
        'candidate_allocated_file_bytes_unique_inodes': inv['all_candidate_allocated_file_bytes_unique_inodes'],
        'expanded_workspace_pristine_candidate_files': expanded['workspace_pristine_candidate_files'],
        'expanded_workspace_pristine_allocated_bytes': expanded['workspace_pristine_allocated_bytes'],
        'expanded_qualification_archive_candidates': len(expanded['qualification_archive_candidates']),
        'expanded_qualification_archive_allocated_bytes': expanded['qualification_archive_allocated_bytes'],
        'combined_candidate_allocated_unique_inode_bytes': expanded['combined_candidate_allocated_unique_inode_bytes'],
        'root_latest_approximate_requested_cleanup_headroom_bytes': 3600000000,
        'shortfall_against_latest_approximate_cleanup_goal_before_review_new_output_bytes': max(0, 3600000000 - expanded['combined_candidate_allocated_unique_inode_bytes']),
        'candidate_protected_path_or_inode_intersections': 0,
        'candidate_symlink_or_special_or_hardlinked_regular_files': 0,
        'protected_paths': len(rows), 'protected_regular_inodes': len(inodes),
        'no_git_or_swift_build_targets_present': True,
        'fixed_budget_bytes': inv['fixed_budget_bytes'], 'existing_meter_sample': inv['latest_existing_meter_sample'],
        'sample_budget_remaining_bytes': budget_remaining, 'root_estimated_additional_restore_bytes': restore,
        'sample_restore_shortfall_without_any_cleanup_bytes': max(0, restore - budget_remaining),
        'sample_initial_restore_shortfall_even_if_all_combined_candidate_allocation_released_bytes': max(0, restore - budget_remaining - expanded['combined_candidate_allocated_unique_inode_bytes']),
        'all_candidate_cleanup_would_suffice': False, 'qualification_or_benchmark_cleanup_admitted': False,
        'current_resource_budget_admission': False, 'deletion_performed': False,
        'sdk_git_or_device_commands_executed': False,
        'original_110_freeze_unchanged': unchanged_execution,
        'limits': inv['limitations'] + [
            'Existing meter sample is not terminal; both original meters remain active. No repeated whole-R sample was initiated.',
            'Initial49 regenerable-cache content was not hashed; expanded qualification/stock candidates were. Every retained snapshot requires fresh exact identity/membership admission before deletion.',
            'Initial arithmetic uses root\'s approximate 12.5e9-byte restore estimate; directory allocation, new outputs and shared APFS allocation may change headroom.',
            'Root subsequently plans a reader/share change and approximately 3.6e9-byte cleanup goal. Neither historical sample arithmetic nor totals admit that revised plan or a current budget.',
            'Workspace non-Source proof is exact current retained-stock equality. Original STOCK-COPY did not pin the whole historical non-Source tree; no Git replay is claimed. Unknown/modified/protected/hardlinked files stay.'
        ]}
    result_ref = write('RESULT.json', result)
    lines = ['kind\tpath\tregular_files\tlogical_file_bytes\tallocated_file_bytes_unique_inodes\tinventory_sha256']
    lines.extend('\t'.join([x['kind'], x['path'], str(x['regular_files']), str(x['logical_file_bytes']),
                            str(x['allocated_file_bytes_unique_inodes']), x['inventory']['sha256']]) for x in inv['targets'])
    p = O / 'TARGETS.tsv'
    with p.open('x') as f:
        f.write('\n'.join(lines) + '\n')
        f.flush(); os.fsync(f.fileno())
    p.chmod(0o444)
    readme = '''Read-only regenerable headroom review

No deletion, SDK/Git/device operation, SUT/input/result edit, native recapture or product judgment occurred. The original 110-operation freeze is unchanged. All writes are confined to this review.

INVENTORY.json and TARGETS.tsv list the initial 49 exact candidates and positive cache ownership/build receipts; target-000.json through target-048.json retain no-follow member metadata. Five compiler-declared DerivedData targets account for 805154816 allocated file bytes, 40 main-workspace caches for 362061824, and four rejected-workspace caches for 30900224. Initial total: 1198116864 bytes across 26659 ordinary file paths. No Git/.build targets, symlinks, special members or hardlinked ordinary files occur in these candidates. Setup/STOCK-COPY/commands, production Source roles, seals, main-SPEC files and subjects stay protected.

EXPANDED-RESULT.json adds actual current qualification and workspace proof. All 82407 old-MAP/SPEC originals have equal current SHA/bytes/original mode and no-follow physical identity, with exact qualification ordinary membership. NONREGULAR-PRESERVATION.json proves the seven original hostile-fixture symlinks match frozen STRUCTURE metadata; all are retained without following. Nine exact intermediate tar/gz containers themselves preserved in that verified archive contribute 306053120 allocated bytes. Every loose qualification code/report/control/manifest/golden/vendor/baseline/candidate remains. All benchmark files were hashed, but the old MAP contains no benchmark original namespace; byte equality alone grants no provenance/preservation authority, so all benchmark remains.

The exact20 explicitly excluded workspaces add 17720 non-Source ordinary files with exact current retained-stock size/SHA/mode equality, totaling 1966837760 allocated bytes. Unknown, modified, Source, metadata, copier-excluded cache and shared members stay. STOCK-COPY pins setup and production Source hashes rather than a complete historical non-Source tree. This proves current independent stock replicas, not a Git commit replay; root must review sufficiency under the prospective upstream-exclusion policy.

Combined candidate allocation is 3471007744 bytes: still 128992256 below the latest approximate 3.6e9-byte goal, before this review's additional evidence allocation. st_blocks does not guarantee freed APFS physical storage; directory allocation, clones and snapshots matter. The prior active-meter sample is not terminal. No current budget or cleanup is admitted.

PROTECTION.json records a second complete path/inode intersection against main-SPEC/Source/subject/required refs and all candidates. QUALIFICATION-ENTRY.json pins old MAP, matching SPEC, cold TRANSPORT, prior cold revalidation and prior restore cleanup. Current originals were byte/mode verified here; current cold members are cited from the separately pinned existing revalidation, not rehashed here. These proofs require fresh exact identity/membership and root admission before any cleanup. No archive was decoded or actual publication consumer run.

EXPANDED-FIRST-FAILURE.json and expanded-first-attempt.py retain the first audit's overly strict assertion rejecting any nonordinary member. The recorder now preserves the exact seven known hostile-test links as noncandidates. The ordinary-file byte/mode gate remains intact. No production helper was changed.
'''
    p = O / 'README.md'
    with p.open('x') as f:
        f.write(readme); f.flush(); os.fsync(f.fileno())
    p.chmod(0o444)
    for member in O.iterdir():
        need(member.is_file() and not member.is_symlink(), 'Unexpected output member')
        member.chmod(0o444)
    artifacts = []
    for p in sorted(O.iterdir()):
        need(p.is_file() and not p.is_symlink(), 'Unexpected review member')
        need(stat.S_IMODE(p.stat().st_mode) == 0o444, 'Unsealed review member')
        artifacts.append({'path': str(p), 'sha256': sha(p), 'size_bytes': p.stat().st_size, 'sealed_mode': '0444'})
    freeze_ref = write('REVIEW-FREEZE.json', {
        'version': 1, 'kind': 'independent-regenerable-headroom-review-freeze',
        'result': result_ref, 'artifact_count': len(artifacts), 'artifact_manifest': artifacts,
        'scope': 'Read-only candidate inventory and cleanup-entry conditions only; no deletion or current budget admission.'})
    print(json.dumps({'freeze': freeze_ref, 'result': result_ref, 'inventory': inventory_ref,
                      'protection': protection_ref, 'qualification_entry': qualification_ref,
                      'artifact_count': len(artifacts), 'candidate_targets': len(inv['targets']),
                      'candidate_allocated_bytes': inv['all_candidate_allocated_file_bytes_unique_inodes']}))


if __name__ == '__main__':
    main()
