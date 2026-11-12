#!/usr/bin/env python3
"""CI-only disposal of a verified, owned, single-use publication replay.

No SDK, code execution/import, source cleanup, original-key fallback or product
evaluation. Only this checkout's externally pinned manifest can declare scopes.
Ordinary quiescent local POSIX CI is required; environment is not remote CI
attestation and unlink is not a same-user adversarial filesystem transaction.
"""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import time


CODE_KEYS = {'cold', 'archive', 'preserve', 'session', 'session_replay', 'phase', 'projection', 'metric'}
INPUT_KEYS = {'cause_index', 'alarm_index', 'correspondence_seal', 'mapping_reveal',
              'coverage_registry', 'metric_inputs', 'metric_results', 'matcher_start'}
NAME = 'pooled-v13-replay'
RECEIPTS = {'CLEANUP-INVENTORY.json', 'CLEANUP-INTENT.json', 'CLEANUP-FAILED.json', 'CLEANUP.json'}
META_LIMIT = 512 * 1024 * 1024
UID = os.geteuid()


def need(ok, why):
    if not ok: raise ValueError(why)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def hexsha(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'Exact external SHA256 required')
    return value


def strict_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, 'Duplicate metadata key'); value[key] = item
        return value
    def bad(_): raise ValueError('Nonfinite metadata')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def absolute(raw):
    need(type(raw) is str and raw.startswith('/') and '\\' not in raw and '\x00' not in raw, 'Canonical absolute path required')
    path = PurePosixPath(raw)
    need(str(path) == raw and '..' not in path.parts and '.' not in path.parts, 'Noncanonical absolute path')
    return Path(raw)


def relative(raw):
    need(type(raw) is str and raw and '\\' not in raw and '\x00' not in raw, 'Canonical relative path required')
    path = PurePosixPath(raw)
    need(not path.is_absolute() and str(path) == raw and '..' not in path.parts
         and not any(v.casefold() == '.git' for v in path.parts), 'Unsafe relative member')
    return path


def identity(value):
    return {'device': value.st_dev, 'inode': value.st_ino, 'uid': value.st_uid,
            'mode': stat.S_IMODE(value.st_mode), 'kind': 'directory' if stat.S_ISDIR(value.st_mode) else 'regular',
            'bytes': value.st_size, 'mtime_ns': value.st_mtime_ns, 'ctime_ns': value.st_ctime_ns,
            'nlink': value.st_nlink, 'allocated_bytes': value.st_blocks * 512}


def stable(value):
    fields = ['device', 'inode', 'uid', 'mode', 'kind']
    if value['kind'] == 'regular': fields += ['bytes', 'mtime_ns']
    # Directory time/size changes and link ctime/nlink changes are intentional.
    return tuple(value[key] for key in fields)


def owned(value, *, device=None):
    need((stat.S_ISREG(value.st_mode) or stat.S_ISDIR(value.st_mode)) and value.st_uid == UID,
         'Only current-uid regular generated files/directories allowed')
    need(device is None or value.st_dev == device, 'Generated namespace crosses filesystem')


@contextlib.contextmanager
def absolute_dir(path):
    path = absolute(str(path)); fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = new
        yield fd
    finally: os.close(fd)


@contextlib.contextmanager
def descend(root_fd, parts, rows=None):
    fd = os.dup(root_fd); prefix = []
    try:
        if rows is not None:
            need(stable(identity(os.fstat(fd))) == stable(rows['']), 'Replay root identity changed')
        for part in parts:
            prefix.append(part)
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = new
            if rows is not None:
                key = '/'.join(prefix)
                need(key in rows and stable(identity(os.fstat(fd))) == stable(rows[key]), 'Generated ancestor identity changed')
        yield fd
    finally: os.close(fd)


def regular(parent, name, *, collect=False, limit=None, readonly=False):
    need('/' not in name and name not in {'', '.', '..'}, 'One exact filename required')
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    try:
        before = os.fstat(fd); owned(before)
        need(stat.S_ISREG(before.st_mode), 'Regular file required')
        need(not readonly or not stat.S_IMODE(before.st_mode) & 0o7222, 'Readonly ordinary file required')
        need(limit is None or before.st_size <= limit, 'Bounded metadata required')
        h = hashlib.sha256(); pieces = []; size = 0
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block: break
            size += len(block); h.update(block)
            if collect: pieces.append(block)
            need(limit is None or size <= limit, 'Metadata grew beyond limit')
        after = os.fstat(fd)
        need(identity(before) == identity(after) and size == after.st_size, 'File changed while reading')
        named = os.stat(name, dir_fd=parent, follow_symlinks=False)
        need(stat.S_ISREG(named.st_mode) and identity(named) == identity(after), 'Named file replaced while reading')
        row = identity(after); row['sha256'] = h.hexdigest()
        return b''.join(pieces) if collect else None, row
    finally: os.close(fd)


def read_path(root_fd, raw, **kwargs):
    path = relative(raw)
    with descend(root_fd, path.parts[:-1]) as fd: return regular(fd, path.name, **kwargs)


def metadata(root_fd, raw):
    data, row = read_path(root_fd, raw, collect=True, limit=META_LIMIT)
    return strict_json(data), row


def exact_ref(value, *, repo=False):
    need(type(value) is dict and set(value) == {'path', 'sha256'}, 'Exact metadata reference required')
    hexsha(value['sha256'])
    relative(value['path']) if repo else absolute(value['path'])
    return value


def verified_inner(value, index_sha):
    need(type(value) is dict and set(value) == {'status', 'index_sha256', 'files', 'chunks', 'shards', 'source_bytes'}
         and value['status'] == 'verified' and value['index_sha256'] == index_sha, 'Exact verified inner receipt required')
    for key in ['files', 'chunks', 'shards', 'source_bytes']:
        need(type(value[key]) is int and value[key] >= 0, 'Exact finite archive counts required')


def checkpoint(_name):
    """No-op fault-scheduling point for independent generic tests; no CLI hook."""


def scan(root_fd):
    rows = {'': identity(os.fstat(root_fd))}; owned(os.fstat(root_fd)); device = rows['']['device']
    def walk(fd, prefix, depth):
        need(depth <= 128, 'Finite generated directory depth required')
        for name in sorted(os.listdir(fd)):
            need(name not in {'', '.', '..'} and '/' not in name, 'Unsafe generated filename')
            key = prefix + name
            value = os.stat(name, dir_fd=fd, follow_symlinks=False); owned(value, device=device)
            if stat.S_ISDIR(value.st_mode):
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                try:
                    need(identity(os.fstat(child)) == identity(value), 'Directory replaced during inventory')
                    rows[key] = identity(value); walk(child, key + '/', depth + 1)
                    need(stable(identity(os.stat(name, dir_fd=fd, follow_symlinks=False))) == stable(rows[key]), 'Directory changed during inventory')
                finally: os.close(child)
            else:
                _raw, rows[key] = regular(fd, name)
    walk(root_fd, '', 0)
    return rows


def shape(root_fd, ids, main):
    def check(fd, required_dirs, required_files):
        seen = set(os.listdir(fd))
        need(required_dirs | required_files <= seen, 'Missing required generated metadata/scope')
        for name in seen:
            value = os.stat(name, dir_fd=fd, follow_symlinks=False); owned(value)
            need(stat.S_ISREG(value.st_mode) or name in required_dirs, 'Unexpected generated directory')
            if name in required_dirs: need(stat.S_ISDIR(value.st_mode), 'Declared generated scope is not a directory')
    check(root_fd, set(ids), {'ENTRY.json', 'RESULT.json'})
    need(not (set(os.listdir(root_fd)) & (RECEIPTS | {'FAILURE.json'})), 'Failed/already-attempted replay cannot be cleaned')
    for key in ids:
        with descend(root_fd, [key]) as fd:
            check(fd, {'decoded'} | ({'readonly-restore'} if key == main else set()),
                  {'DECODED.json'} | ({'RESTORED.json'} if key == main else set()))
        if key == main:
            with descend(root_fd, [key, 'readonly-restore']) as fd:
                check(fd, {'files'}, {'RESTORED-MAP.json'})
                need('RESTORE-FAILED.json' not in os.listdir(fd), 'Failed restore cannot be cleaned')


def save_at(root_fd, name, value):
    # Create readonly metadata directly; never chmod any regular file.
    raw = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o444, dir_fd=root_fd)
    try:
        owned(os.fstat(fd)); offset = 0
        while offset < len(raw): offset += os.write(fd, raw[offset:])
        os.fsync(fd)
    finally: os.close(fd)
    os.fsync(root_fd)
    return {'path': name, 'sha256': sha(raw), 'bytes': len(raw)}


def source_check(repo_fd, sources):
    for path, expected in sources.items():
        _raw, current = read_path(repo_fd, path, readonly=expected.get('readonly', False))
        need(stable(current) == stable(expected) and current['sha256'] == expected['sha256'], 'Pinned repo/cold input changed')


def prepare(repo_fd, root_fd, repo, replay):
    pin_raw, pin_row = read_path(repo_fd, 'PUBLICATION.sha256', collect=True, limit=128)
    need(re.fullmatch(b'[0-9a-f]{64}\n?', pin_raw), 'One exact repo publication pin required')
    manifest_sha = pin_raw.decode().strip()
    raw, manifest_row = read_path(repo_fd, 'PUBLICATION.json', collect=True, limit=META_LIMIT)
    need(sha(raw) == manifest_sha, 'Repo PUBLICATION external SHA differs')
    manifest = strict_json(raw)
    need(manifest.get('kind') == 'pooled-forward-published-study' and type(manifest.get('version')) is int
         and manifest['version'] == 1 and manifest.get('study_closed') is True, 'Closed pinned publication manifest required')
    need(type(manifest.get('code')) is dict and set(manifest['code']) == CODE_KEYS
         and type(manifest.get('inputs')) is dict and set(manifest['inputs']) == INPUT_KEYS, 'Exact publication registries required')
    sources = {'PUBLICATION.sha256': pin_row, 'PUBLICATION.json': manifest_row}
    for value in manifest['code'].values():
        exact_ref(value, repo=True); _raw, row = read_path(repo_fd, value['path'])
        need(row['sha256'] == value['sha256'], 'Pinned producer code differs'); sources[value['path']] = row
    for value in manifest['inputs'].values(): exact_ref(value)  # Never open these original keys.
    exact_ref(manifest['preservation_plan'])
    transports = manifest.get('transports')
    need(type(transports) is list and 1 <= len(transports) <= 64, 'Finite explicit transport registry required')
    ids = []; folders = set(); main = manifest.get('main_transport'); by_id = {}
    for item in transports:
        need(type(item) is dict and set(item) == {'id', 'directory', 'transport_sha256', 'index_sha256', 'restore'}, 'Exact transport declaration required')
        key = item['id']; need(type(key) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9-]{0,63}', key) and key not in ids, 'Unique ASCII transport id required')
        folder = str(relative(item['directory'])); need(folder not in folders, 'Duplicate cold directory')
        folders.add(folder); hexsha(item['transport_sha256']); hexsha(item['index_sha256'])
        need(type(item['restore']) is bool, 'Explicit restore bool required')
        ids.append(key); by_id[key] = item
    need(main in ids and [v['id'] for v in transports if v['restore']] == [main], 'Exactly main transport may restore')
    entry, _ = metadata(root_fd, 'ENTRY.json'); result, _ = metadata(root_fd, 'RESULT.json')
    need(entry.get('manifest') == str(repo / 'PUBLICATION.json') and entry.get('manifest_sha256') == manifest_sha
         and entry.get('native_sdk_execution') is False, 'Replay ENTRY is not this externally pinned checkout manifest')
    need(type(result.get('version')) is int and result['version'] == 1 and result.get('kind') == 'pooled-forward-publication-replay'
         and result.get('status') == 'verified' and result.get('cold_transports_verified') == sorted(ids)
         and result.get('native_sdk_execution') is False and result.get('current_source_delivery_verified') is False,
         'Actual complete verified replay RESULT required')
    need(result.get('source_domain_evaluation') == 'unsupported' and result.get('source_responsibility_evaluation') == 'unsupported'
         and result.get('five_case_fixed_metrics_identical') is True, 'Replay scope/arithmetic completion differs')
    shape(root_fd, ids, main)
    rows = scan(root_fd); scopes = []; payload_inodes = set(); transport_inodes = set()
    for key in ids:
        item = by_id[key]; prefix = item['directory']
        seal_raw, seal_row = read_path(repo_fd, prefix + '/TRANSPORT.json', collect=True, limit=4 * 1024 * 1024, readonly=False)
        need(seal_row['sha256'] == item['transport_sha256'], 'External cold transport pin differs')
        seal = strict_json(seal_raw)
        need(type(seal.get('version')) is int and seal['version'] == 1 and seal.get('kind') == 'lossless-frozen-archive-transport'
             and seal.get('index_sha256') == item['index_sha256'] and seal.get('archive_code_sha256') == manifest['code']['archive']['sha256'], 'Cold provenance differs')
        sources[prefix + '/TRANSPORT.json'] = dict(seal_row, readonly=False)
        inventory = seal.get('files'); need(type(inventory) is dict and {'INDEX.json', 'SPEC.json', 'SEAL.json'} <= set(inventory), 'Cold inventory missing')
        stored_names = {'TRANSPORT.json'}
        for name, row in inventory.items():
            need(name in {'INDEX.json', 'SPEC.json', 'SEAL.json'} or re.fullmatch(r'shard-[0-9]{5}\.tar\.gz', name), 'Unsafe decoded member')
            need(type(row) is dict and set(row) == {'stored', 'sha256', 'bytes', 'stored_sha256', 'stored_bytes'}, 'Exact cold member metadata required')
            expected = name + '.gz' if name in {'INDEX.json', 'SPEC.json'} else name
            need(row['stored'] == expected and expected not in stored_names, 'Unsafe stored cold name')
            stored_names.add(expected)
            for value in [row['bytes'], row['stored_bytes']]: need(type(value) is int and value >= 0, 'Exact cold byte count required')
            hexsha(row['sha256']); hexsha(row['stored_sha256'])
            _raw, cold_row = read_path(repo_fd, prefix + '/' + expected, readonly=False)
            need(cold_row['sha256'] == row['stored_sha256'] and cold_row['bytes'] == row['stored_bytes'], 'Pinned cold source bytes differ')
            sources[prefix + '/' + expected] = dict(cold_row, readonly=False)
            target = rows.get(key + '/decoded/' + name)
            need(target and target['kind'] == 'regular' and not target['mode'] & 0o7222
                 and target['sha256'] == row['sha256'] and target['bytes'] == row['bytes'], 'Verified readonly decoded member differs')
            transport_inodes.add((target['device'], target['inode']))
        with descend(repo_fd, relative(prefix).parts) as fd: need(set(os.listdir(fd)) == stored_names, 'Cold namespace differs')
        actual = {p[len(key + '/decoded/'):] for p in rows if p.startswith(key + '/decoded/')}
        need(actual == set(inventory), 'Decoded namespace differs')
        need(rows[key + '/decoded/INDEX.json']['sha256'] == item['index_sha256'], 'Actual decoded INDEX external pin differs')
        decoded, _ = metadata(root_fd, key + '/DECODED.json')
        need(type(decoded) is dict and set(decoded) == {'transport', 'inner'}, 'Exact DECODED receipt required')
        verified_inner(decoded['inner'], item['index_sha256'])
        need(decoded['transport'].get('status') == 'verified' and decoded['transport'].get('transport_sha256') == item['transport_sha256']
             and decoded['transport'].get('inner_verified') == decoded['inner'], 'DECODED transport provenance differs')
        scopes.append(key + '/decoded')
        if key == main:
            restored, _ = metadata(root_fd, key + '/RESTORED.json')
            base = replay / key / 'readonly-restore'
            need(restored.get('status') == 'restored' and restored.get('dest') == str(base)
                 and restored.get('mapping') == str(base / 'RESTORED-MAP.json')
                 and restored.get('index_sha256') == item['index_sha256'], 'Readonly restore provenance differs')
            for field in ['files', 'chunks', 'shards', 'source_bytes']:
                need(type(restored.get(field)) is int and restored[field] == decoded['inner'][field], 'Restore counts differ')
            mapping, _ = metadata(root_fd, key + '/readonly-restore/RESTORED-MAP.json')
            need(type(mapping) is dict and set(mapping) == {'format', 'version', 'index_sha256', 'namespace', 'mappings', 'scope'}
                 and mapping['format'] == 'explicit-file-lossless-v1' and type(mapping['version']) is int and mapping['version'] == 1
                 and mapping['index_sha256'] == item['index_sha256'] and mapping['namespace'] == str(base / 'files')
                 and type(mapping['mappings']) is dict and mapping['mappings'], 'Original readonly map provenance differs')
            index, _ = metadata(root_fd, key + '/decoded/INDEX.json')
            need(index.get('format') == 'explicit-file-lossless-v1' and type(index.get('version')) is int and index['version'] == 1
                 and type(index.get('files')) is list, 'Authenticated INDEX inventory required')
            for field in ['files', 'chunks', 'shards', 'source_bytes']:
                need(index.get('counts', {}).get(field) == decoded['inner'][field], 'Authenticated INDEX counts differ')
            original_rows = {}
            for item_row in index['files']:
                need(type(item_row) is dict and {'path', 'logical_path', 'sha256', 'bytes', 'mode'} <= set(item_row), 'Explicit original INDEX row required')
                need(item_row['path'] not in original_rows, 'Duplicate original INDEX row')
                original_rows[item_row['path']] = item_row
            need(set(mapping['mappings']) == set(original_rows), 'MAP original keys differ from pinned INDEX')
            expected_files = set(); expected_dirs = {key + '/readonly-restore/files'}
            for original, row in mapping['mappings'].items():
                origin = absolute(original)
                need(type(row) is dict and set(row) == {'physical_path', 'logical_path', 'sha256', 'bytes', 'original_mode', 'restored_mode'}, 'Exact map row required')
                logical = relative(row['logical_path']); physical = base / 'files' / logical
                need(row['physical_path'] == str(physical) and physical != origin and logical.name == origin.name, 'Mapped scope differs')
                original_row = original_rows[original]
                need(row['logical_path'] == original_row['logical_path'] and row['sha256'] == original_row['sha256']
                     and type(row['bytes']) is int and row['bytes'] == original_row['bytes']
                     and row['original_mode'] == original_row['mode'], 'MAP provenance differs from pinned INDEX')
                for field in ['original_mode', 'restored_mode']:
                    need(type(row[field]) is str and re.fullmatch('0[0-7]{3}', row[field]), 'Ordinary mapped modes required')
                need(int(row['restored_mode'], 8) == int(row['original_mode'], 8) & ~0o222, 'Map does not prove readonly restore mode')
                name = key + '/readonly-restore/files/' + str(logical)
                need(name not in expected_files, 'Duplicate mapped logical payload'); expected_files.add(name)
                parent = PurePosixPath(name).parent
                while str(parent).startswith(key + '/readonly-restore/files'):
                    expected_dirs.add(str(parent)); parent = parent.parent
                current = rows.get(name)
                need(current and current['kind'] == 'regular' and current['sha256'] == hexsha(row['sha256'])
                     and type(row['bytes']) is int and row['bytes'] >= 0 and current['bytes'] == row['bytes']
                     and current['mode'] == int(row['restored_mode'], 8) and current['nlink'] == 1, 'Mapped readonly payload differs or is aliased')
                token = (current['device'], current['inode']); need(token not in payload_inodes, 'Logical payload inode duplicated'); payload_inodes.add(token)
            prefix_files = key + '/readonly-restore/files'
            need({p for p in rows if p == prefix_files or p.startswith(prefix_files + '/')} == expected_files | expected_dirs,
                 'Unmapped payload file/directory')
            need(not set(original_rows) & {str(replay / p) for p in expected_files}, 'Restore scope overlaps an original key')
            need(len(expected_files) == restored['files'] == result.get('readonly_original_key_payloads_verified')
                 and type(result.get('readonly_original_key_payloads_verified')) is int, 'Complete readonly payload coverage differs')
            scopes.append(prefix_files)
    need(not payload_inodes & transport_inodes, 'Logical payload shares a transport inode')
    protected = {p: row for p, row in rows.items() if row['kind'] == 'regular'
                 and not any(p == scope or p.startswith(scope + '/') for scope in scopes)}
    return {'manifest_sha256': manifest_sha, 'rows': rows, 'scopes': scopes, 'protected': protected, 'sources': sources}


def cleanup(replay_raw):
    need(os.environ.get('GITHUB_ACTIONS') == 'true', 'CI-only: GITHUB_ACTIONS must be exactly true')
    code = absolute(os.path.abspath(__file__)); repo = code.parent.parent
    workspace = absolute(os.environ.get('GITHUB_WORKSPACE', ''))
    need(repo == workspace / 'validation/pooled-forward', 'Helper must belong to this GITHUB_WORKSPACE checkout')
    temp = absolute(os.environ.get('RUNNER_TEMP', '')); replay = absolute(replay_raw)
    need(replay == temp / NAME and not temp.is_relative_to(workspace) and not workspace.is_relative_to(temp),
         'Only exact RUNNER_TEMP/pooled-v13-replay outside checkout is eligible')
    with absolute_dir(code.parent) as fd: regular(fd, code.name, collect=False)
    with absolute_dir(repo) as repo_fd, absolute_dir(temp) as temp_fd:
        owned(os.fstat(temp_fd)); root_fd = os.open(NAME, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=temp_fd)
        try:
            owned(os.fstat(root_fd)); need(os.fstat(root_fd).st_mode & stat.S_IWUSR, 'Receipt directory must already be owner-writable')
            plan = prepare(repo_fd, root_fd, repo, replay); rows = plan['rows']; original_modes = {p: v['mode'] for p, v in rows.items() if v['kind'] == 'directory'}
            def bound_root():
                with absolute_dir(temp) as current_temp:
                    need(stable(identity(os.fstat(current_temp))) == stable(identity(os.fstat(temp_fd))), 'RUNNER_TEMP namespace changed')
                need(stable(identity(os.stat(NAME, dir_fd=temp_fd, follow_symlinks=False))) == stable(rows['']), 'Replay root replaced')
            source_check(repo_fd, plan['sources'])
            checkpoint('before_intent')
            bound_root()
            inventory = save_at(root_fd, 'CLEANUP-INVENTORY.json', {'version': 1, 'kind': 'fresh-owned-ci-replay-namespace-inventory',
                'at_unix': time.time(), 'uid': UID, 'manifest_sha256': plan['manifest_sha256'], 'rows': rows})
            intent = save_at(root_fd, 'CLEANUP-INTENT.json', {'version': 1, 'kind': 'verified-ci-replay-disposal-intent',
                'at_unix': time.time(), 'manifest_sha256': plan['manifest_sha256'], 'inventory': inventory,
                'exact_scopes': plan['scopes'], 'source_files_untouched': True, 'file_chmod_forbidden': True})
            removed_files = removed_dirs = logical_bytes = 0; removed_inodes = {}; changed_dirs = []
            try:
                checkpoint('after_intent')
                bound_root()
                # Chmod only held no-follow descriptors of inventoried, owned directories.
                for path in sorted(original_modes, key=lambda p: (p.count('/'), p)):
                    with descend(root_fd, PurePosixPath(path).parts if path else (), rows) as fd:
                        value = os.fstat(fd); owned(value, device=rows['']['device']); need(stat.S_ISDIR(value.st_mode), 'Only directories may be chmod')
                        if stat.S_IMODE(value.st_mode) & 0o700 != 0o700:
                            os.fchmod(fd, stat.S_IMODE(value.st_mode) | 0o700)
                            rows[path]['mode'] = stat.S_IMODE(os.fstat(fd).st_mode); changed_dirs.append(path)
                targets = {p: v for p, v in rows.items() if any(p == scope or p.startswith(scope + '/') for scope in plan['scopes'])}
                checkpoint('before_remove')
                bound_root()
                for path, row in sorted(targets.items(), key=lambda item: (-item[0].count('/'), item[0])):
                    bound_root()
                    member = PurePosixPath(path)
                    with descend(root_fd, member.parts[:-1], rows) as parent:
                        current = os.stat(member.name, dir_fd=parent, follow_symlinks=False); owned(current, device=rows['']['device'])
                        need(stable(identity(current)) == stable(row), 'Inventoried removal member was replaced')
                        if row['kind'] == 'regular':
                            need(stat.S_ISREG(current.st_mode), 'Only exact regular payloads can be unlinked')
                            os.unlink(member.name, dir_fd=parent); removed_files += 1; logical_bytes += row['bytes']
                            removed_inodes[(row['device'], row['inode'])] = row['allocated_bytes']
                        else:
                            need(stat.S_ISDIR(current.st_mode), 'Only exact generated directories can be removed')
                            os.rmdir(member.name, dir_fd=parent); removed_dirs += 1
                for path in reversed(changed_dirs):
                    if path in targets: continue
                    with descend(root_fd, PurePosixPath(path).parts if path else (), rows) as fd:
                        need(stat.S_ISDIR(os.fstat(fd).st_mode), 'Directory descriptor changed')
                        os.fchmod(fd, original_modes[path]); rows[path]['mode'] = original_modes[path]
                for path, expected in plan['protected'].items():
                    _raw, value = read_path(root_fd, path)
                    need(stable(value) == stable(expected) and value['sha256'] == expected['sha256'], 'Preserved compact metadata changed')
                source_check(repo_fd, plan['sources'])
                remaining = scan(root_fd)
                need(set(remaining) == (set(rows) - set(targets)) | {'CLEANUP-INVENTORY.json', 'CLEANUP-INTENT.json'},
                     'Unexpected surviving/generated namespace member')
                for reference in [inventory, intent]:
                    _raw, current = read_path(root_fd, reference['path'])
                    need(current['sha256'] == reference['sha256'], 'Cleanup provenance receipt was replaced')
                need(stable(identity(os.stat(NAME, dir_fd=temp_fd, follow_symlinks=False))) == stable(rows['']), 'Replay root changed during cleanup')
                checkpoint('before_complete')
                receipt = {'version': 1, 'kind': 'verified-ci-replay-payload-disposal', 'status': 'completed',
                    'at_unix': time.time(), 'intent': intent, 'manifest_sha256': plan['manifest_sha256'],
                    'exact_scopes_removed': plan['scopes'], 'files_unlinked': removed_files, 'directories_removed': removed_dirs,
                    'removed_namespace_logical_file_bytes': logical_bytes,
                    'removed_namespace_unique_inode_allocated_bytes_before': sum(removed_inodes.values()),
                    'physical_bytes_freed_measured': False, 'file_chmod_calls': 0,
                    'protected_metadata_files_reverified': len(plan['protected']), 'repo_cold_inputs_reverified_unchanged': len(plan['sources']),
                    'original_dataset_or_repository_files_deleted': 0, 'current_delivery_or_historical_product_graded': False,
                    'scope': 'Owned single-use CI replay disposal only. Namespace allocation is not physical freed space. No SDK, grading, original-key fallback, source cleanup or permanent immutable-handle claim.'}
                save_at(root_fd, 'CLEANUP.json', receipt)
                return receipt
            except BaseException as error:
                # Never retry/rollback/expand deletion after a failure.
                failure = {'version': 1, 'status': 'failed', 'kind': 'ci-replay-disposal-partial-failure', 'intent': intent,
                    'error_type': type(error).__name__, 'message': str(error), 'files_unlinked': removed_files,
                    'directories_removed': removed_dirs, 'partial_outputs_retained': True, 'file_chmod_calls': 0}
                try: save_at(root_fd, 'CLEANUP-FAILED.json', failure)
                except OSError: pass  # Preempted receipt is retained; never overwritten.
                raise
        finally: os.close(root_fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--replay', required=True)
    args = parser.parse_args(); result = cleanup(args.replay)
    print(json.dumps({key: result[key] for key in ['status', 'files_unlinked', 'directories_removed', 'manifest_sha256']}, sort_keys=True))


if __name__ == '__main__': main()
