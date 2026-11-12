#!/usr/bin/env python3
"""Finite read-only current-byte qualification and pristine-stock comparison."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import stat
import time

R = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward')
O = R / 'operators/regenerable-headroom-independent-v1'
EXCLUDED = {'.git', 'build', '.gradle', '.kotlin', '.build', '.swiftpm', '__pycache__'}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def ident(st):
    return [st.st_dev, st.st_ino, stat.S_IMODE(st.st_mode), st.st_uid, st.st_gid,
            st.st_nlink, st.st_size, st.st_blocks * 512, st.st_mtime_ns, st.st_ctime_ns]


def physical(p):
    need(p.is_absolute() and str(p) == os.path.normpath(str(p)), 'Noncanonical path')
    for q in [p, *p.parents]:
        need(not q.is_symlink(), 'Symlink ancestor')
    return p


def digest(p):
    before = p.lstat()
    need(stat.S_ISREG(before.st_mode), 'Not an ordinary file')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        need(ident(os.fstat(fd)) == ident(before), 'File identity changed before hash')
        h = hashlib.sha256()
        while True:
            b = os.read(fd, 1024 * 1024)
            if not b:
                break
            h.update(b)
        need(ident(os.fstat(fd)) == ident(before), 'File changed during hash')
    finally:
        os.close(fd)
    need(ident(p.lstat()) == ident(before), 'Path changed during hash')
    return h.hexdigest(), ident(before)


def ref(p, expected=None):
    h, _ = digest(p)
    need(expected is None or h == expected, 'Pin differs: ' + str(p))
    return {'path': str(p), 'sha256': h}


def load(p):
    return json.loads(p.read_bytes())


def write(name, data):
    p = O / name
    with p.open('x') as f:
        json.dump(data, f, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    p.chmod(0o444)
    return ref(p)


def under(p, root):
    return p == root or p.is_relative_to(root)


def tree(root):
    stack = [root]
    rows = []
    while stack:
        p = stack.pop()
        st = p.lstat()
        if stat.S_ISDIR(st.st_mode):
            rows.append([str(p), 'directory', ident(st)])
            stack.extend(Path(e.path) for e in os.scandir(p))
        elif stat.S_ISREG(st.st_mode):
            rows.append([str(p), 'regular', ident(st)])
        elif stat.S_ISLNK(st.st_mode):
            rows.append([str(p), 'symlink-metadata-only', ident(st)])
        else:
            rows.append([str(p), 'special-metadata-only', ident(st)])
    return sorted(rows)


def main():
    start = time.time()
    inv = load(O / 'INVENTORY.json')
    for k in ['main_spec', 'main_plan', 'owner', 'cache_identity_authority']:
        x = inv[k]; physical(Path(x['path'])); ref(Path(x['path']), x['sha256'])
    need((R / 'cache').lstat().st_dev == 16777232 and (R / 'cache').lstat().st_ino == 26682812,
         'Cache owner namespace differs')
    spec = load(Path(inv['main_spec']['path']))
    plan = load(Path(inv['main_plan']['path']))
    protected = {Path(x['path']) for x in spec['files']}
    protected.update(Path(x) for x in plan['subject_files'])
    protected.update(Path(x['path']) for x in plan['additional_required_refs'])
    protected_roots = {Path(x) for x in plan['source_roots'] + plan['protected_plain_code_roots']}
    for w in inv['workspace_proofs']:
        protected.update(Path(x['path']) for x in w['metadata_refs_retained'].values())
        protected_roots.update(Path(x) for x in w['production_source_roots_preserved'])
        stock = load(Path(w['metadata_refs_retained']['STOCK-COPY.json']['path']))
        dep = stock.get('private_jdk_dependency', {}).get('path')
        if dep:
            protected.add(Path(w['path']) / Path(dep).relative_to(Path(stock['workspace'])))
    for root in protected_roots:
        if root.is_dir() and under(root, R / 'cache'):
            protected.update(Path(p) for p, kind, meta in tree(root) if kind == 'regular')
    protected_inodes = set()
    for p in protected:
        st = p.lstat()
        if stat.S_ISREG(st.st_mode):
            protected_inodes.add((st.st_dev, st.st_ino))

    qspec_path = R / 'operators/archive-selection/closed-qualification-v1/SPEC.json'
    qspec_ref = ref(qspec_path, '6e0800372b4b3ee2db5af1c64177a733ab56ac54d754eaf8da8e35606fe1a187')
    qspec = load(qspec_path)
    mp = R / 'cache/publication-archives/closed-qualification-v1/readonly-restore/RESTORED-MAP.json'
    map_ref = ref(mp, '5c6d03b7d31fa586b010081f5f8017d1905e6fcb92e0f89ecd27202630f0c4d1')
    oldmap = load(mp)
    maprows = oldmap['mappings']
    need(set(maprows) == {x['path'] for x in qspec['files']}, 'Original SPEC/map keys differ')
    qroot = physical(R / 'qualification')
    qidentity = ident(qroot.lstat())
    qtree = tree(qroot)
    qregular = {p for p, kind, meta in qtree if kind == 'regular'}
    qexpected = {p for p in maprows if under(Path(p), qroot)}
    need(qregular == qexpected, 'Qualification current regular membership differs from original MAP')
    qnonregular = [row for row in qtree if row[1] not in {'directory', 'regular'}]
    byte_failures = []
    mode_failures = []
    qrows = []
    sha_members = {}
    for n, item in enumerate(sorted(qspec['files'], key=lambda x: x['path'])):
        path = physical(Path(item['path']))
        row = maprows[str(path)]
        need(row['sha256'] == item['sha256'] and row['bytes'] == item['bytes'], 'SPEC/map byte metadata differs')
        h, meta = digest(path)
        sha_members.setdefault((h, meta[6]), []).append(str(path))
        original_mode = row['original_mode']
        if isinstance(original_mode, str):
            original_mode = int(original_mode, 8)
        byte_ok = h == row['sha256'] and meta[6] == row['bytes']
        mode_ok = meta[2] == original_mode
        if not byte_ok:
            byte_failures.append(str(path))
        if not mode_ok:
            mode_failures.append(str(path))
        qrows.append([str(path), h, meta, row['sha256'], row['bytes'], original_mode, byte_ok, mode_ok])
        if (n + 1) % 20000 == 0:
            print(json.dumps({'qualification_members_hashed': n + 1}), flush=True)
    need(ident(qroot.lstat()) == qidentity, 'Qualification root changed during inventory')
    # Nonordinary hostile-test fixtures are retained as metadata and never followed
    # or proposed for cleanup. They do not invalidate the ordinary-file byte gate.
    need(not byte_failures and not mode_failures, 'Qualification current bytes/modes differ')
    qref = write('QUALIFICATION-CURRENT.json', {
        'version': 1, 'kind': 'actual-current-qualification-original-byte-mode-physical-inventory',
        'spec': qspec_ref, 'old_map': map_ref, 'root': str(qroot), 'root_identity': qidentity,
        'root_identity_unchanged': True, 'current_regular_membership_exact': True,
        'identity_fields': ['device', 'inode', 'mode_int', 'uid', 'gid', 'nlink', 'size_bytes', 'allocated_file_bytes', 'mtime_ns', 'ctime_ns'],
        'row_fields': ['path', 'current_sha256', 'current_identity', 'map_sha256', 'map_bytes', 'original_mode_int', 'byte_equal', 'mode_equal'],
        'rows': qrows, 'verified_files': len(qrows), 'byte_failures': byte_failures,
        'mode_failures': mode_failures, 'nonregular_members_metadata': qnonregular,
        'scope': 'Every original SPEC member hashed; qualification exact current ordinary membership. All loose qualification code/reports and runtimegolden/vendor/baseline/candidate remain preserved.'})

    # Exact old-map-pinned duplicate archive containers only; all other qualification originals are kept.
    archive_candidates = []
    for n in range(2, 11):
        basename = 'PRE-CLEANUP.tar' if n in {2, 3, 4} else 'RAW-EVIDENCE.tar' if n == 5 else 'RAW-EVIDENCE.tar.gz'
        p = qroot / f'review-{n}/archives/{basename}'
        need(str(p) in maprows, 'Exact intermediate archive not in original MAP')
        st = p.lstat()
        need(p not in protected and (st.st_dev, st.st_ino) not in protected_inodes,
             'Qualification archive intersects protected file/inode')
        need(not any(under(p, root) for root in protected_roots), 'Archive within protected Source root')
        need(st.st_nlink == 1 and st.st_uid == qroot.stat().st_uid, 'Archive physical ownership/link count differs')
        with p.open('rb') as f:
            head = f.read(512)
        need(head[:2] == b'\x1f\x8b' if p.suffix == '.gz' else head[257:262] == b'ustar', 'Not declared archive-container encoding')
        archive_candidates.append({'path': str(p), 'current_sha256': maprows[str(p)]['sha256'],
            'identity': ident(st), 'original_map': map_ref, 'original_mode': maprows[str(p)]['original_mode'],
            'role': 'Exact intermediate archive container, itself byte-preserved in verified cold qualification archive; all loose code/report/control/manifest originals remain.',
            'protected_path_or_inode_intersections': [], 'deletion_authorized': False})

    # Hash benchmark current members, but do not equate bytes with namespace/provenance preservation.
    broot = physical(R / 'cache/benchmark')
    bidentity = ident(broot.lstat())
    brows = []
    bmatches = 0
    for path, kind, meta in tree(broot):
        if kind == 'regular':
            h, meta = digest(Path(path))
            matches = sha_members.get((h, meta[6]), [])
            bmatches += bool(matches)
            brows.append([path, h, meta, path in maprows, matches])
    need(ident(broot.lstat()) == bidentity, 'Benchmark root changed')
    bref = write('BENCHMARK-CURRENT.json', {
        'version': 1, 'kind': 'current-benchmark-byte-identity-inventory-no-cleanup-admission',
        'root': str(broot), 'root_identity': bidentity, 'old_map': map_ref,
        'row_fields': ['path', 'current_sha256', 'current_identity', 'exact_old_map_original_key', 'equal_byte_old_map_original_keys'],
        'rows': brows, 'current_regular_files': len(brows),
        'exact_old_map_original_keys': sum(x[3] for x in brows), 'equal_byte_members': bmatches,
        'cleanup_candidate_files': 0, 'cleanup_admitted': False,
        'blocker': 'No benchmark original namespace in old MAP/SPEC. Byte equality alone does not preserve benchmark locator/provenance/history. Entire benchmark remains protected, including all code, reports and benchmark-report.'})

    stock_root = physical(R / 'cache/hosts')
    stock_id = ident(stock_root.lstat())
    stock_cache = {}
    workspace_rows = []
    workspace_summary = []
    copy_source = ref(R / 'business_workspace.py')
    main = [w for w in inv['workspace_proofs'] if w['scope'] == 'main-explicit-workspace-exclusion']
    need(len(main) == 20, 'Need exact20 explicit workspaces')
    for w in main:
        root = physical(Path(w['path']))
        root_before = ident(root.lstat())
        sr = w['metadata_refs_retained']['STOCK-COPY.json']
        ref(Path(sr['path']), sr['sha256'])
        receipt = load(Path(sr['path']))
        need(Path(receipt['source']) == stock_root, 'Foreign stock source')
        setup_ref = ref(stock_root / 'setup.json', receipt['stock_setup_sha256'])
        roots = [Path(x) for x in w['production_source_roots_preserved']]
        copied = 0; preserved = Counter(); local_rows = []
        for raw, kind, meta in tree(root):
            p = Path(raw)
            if kind != 'regular':
                continue
            rel = p.relative_to(root)
            if p in protected or any(under(p, x) for x in roots) or (meta[0], meta[1]) in protected_inodes:
                preserved['protected_Source_metadata_or_inode'] += 1; continue
            if any(part in EXCLUDED for part in rel.parts):
                preserved['copy_producer_excluded_or_regenerated'] += 1; continue
            source = stock_root / rel
            if not source.is_file() or source.is_symlink():
                preserved['unknown_not_current_stock_file'] += 1; continue
            if meta[5] != 1:
                preserved['hardlink_or_shared_dependency'] += 1; continue
            physical(source)
            if source not in stock_cache:
                stock_cache[source] = digest(source)
            sh, smeta = stock_cache[source]
            h, actual = digest(p)
            if h != sh or actual[6] != smeta[6] or actual[2] != smeta[2]:
                preserved['modified_or_mode_different_from_current_stock'] += 1; continue
            need(p not in protected and (actual[0], actual[1]) not in protected_inodes, 'Pristine target protected')
            row = [str(p), h, actual, str(source), sh, smeta]
            local_rows.append(row); copied += 1
        need(ident(root.lstat()) == root_before, 'Workspace root changed')
        workspace_rows.extend(local_rows)
        workspace_summary.append({'workspace': str(root), 'identity': root_before, 'stock_copy_receipt': sr,
            'stock_setup': setup_ref, 'pristine_current_stock_equal_files': copied,
            'allocated_file_bytes': sum(x[2][7] for x in local_rows), 'preserved_other_regular_members': dict(preserved),
            'production_Source_roots_preserved': list(map(str, roots)), 'deletion_authorized': False})
        print(json.dumps({'workspaces_current_stock_compared': len(workspace_summary), 'pristine_files': len(workspace_rows)}), flush=True)
    need(ident(stock_root.lstat()) == stock_id, 'Retained stock namespace changed')
    wref = write('WORKSPACE-PRISTINE.json', {
        'version': 1, 'kind': 'explicit20-workspace-current-pristine-stock-replica-inventory',
        'main_plan': inv['main_plan'], 'cache_owner': inv['owner'], 'copy_producer': copy_source,
        'retained_stock_root': str(stock_root), 'retained_stock_root_identity': stock_id,
        'row_fields': ['workspace_path', 'workspace_sha256', 'workspace_identity', 'retained_stock_path', 'stock_sha256', 'stock_identity'],
        'rows': workspace_rows, 'workspaces': workspace_summary, 'candidate_files': len(workspace_rows),
        'protected_intersections': [], 'deletion_authorized': False,
        'proof': 'Exact original STOCK-COPY receipt admits stock source/setup and fixed producer copy semantics; each proposed non-Source ordinary file now has exact size/SHA/mode equality with retained independent stock member. All unknown/modified/copier-excluded/Source/metadata/shared members remain.',
        'limit': 'Current retained-stock equality is explicitly proved; STOCK-COPY originally pins only setup and production Source hashes, not a full non-Source tree manifest. This review does not claim a fresh Git commit-object replay. Root must decide whether prospective explicit upstream-exclusion policy plus this current equality is sufficient; no deletion authority is granted.'})

    previous_inodes = {}
    for target in inv['targets']:
        for row in load(Path(target['inventory']['path']))['entries']:
            if row['kind'] == 'regular':
                previous_inodes.setdefault((row['device'], row['inode']), row['allocated_file_bytes'])
    qualification_added = {}
    for x in archive_candidates:
        meta = x['identity']; qualification_added.setdefault((meta[0], meta[1]), meta[7])
    workspace_added = {}
    for x in workspace_rows:
        meta = x[2]; workspace_added.setdefault((meta[0], meta[1]), meta[7])
    all_inodes = {**previous_inodes, **qualification_added, **workspace_added}
    result = {
        'version': 1, 'kind': 'bounded-expanded-current-byte-regenerable-review',
        'qualification_current': qref, 'benchmark_current': bref, 'workspace_pristine': wref,
        'qualification_verified_files': len(qrows), 'qualification_byte_or_mode_failures': 0,
        'qualification_preservation_policy': 'All qualification originals retained except the nine explicitly listed original-map-pinned duplicate intermediate archive containers proposed for root review. Every loose code/report/control/manifest/golden/vendor/baseline/candidate member is retained.',
        'qualification_archive_candidates': archive_candidates,
        'qualification_archive_allocated_bytes': sum(qualification_added.values()),
        'benchmark_candidate_files': 0, 'benchmark_blocked_no_original_namespace_proof': True,
        'workspace_pristine_candidate_files': len(workspace_rows),
        'workspace_pristine_allocated_bytes': sum(workspace_added.values()),
        'prior49_candidate_allocated_bytes': sum(previous_inodes.values()),
        'combined_candidate_allocated_unique_inode_bytes': sum(all_inodes.values()),
        'combined_candidate_protected_path_or_inode_intersections': 0,
        'deletion_performed': False, 'sdk_git_or_device_commands_executed': False,
        'stock_original_full_nonSource_tree_pin_absent_limit': True,
        'current_budget_or_cleanup_admitted': False,
        'started_at_unix': start, 'finished_at_unix': time.time()}
    er = write('EXPANDED-RESULT.json', result)
    print(json.dumps({'expanded_result': er, 'qualification_files_verified': len(qrows),
                      'qualification_archive_allocated_bytes': result['qualification_archive_allocated_bytes'],
                      'workspace_pristine_files': len(workspace_rows),
                      'workspace_pristine_allocated_bytes': result['workspace_pristine_allocated_bytes'],
                      'combined_allocated_bytes': result['combined_candidate_allocated_unique_inode_bytes'],
                      'benchmark_candidate_files': 0}), flush=True)


if __name__ == '__main__':
    main()
