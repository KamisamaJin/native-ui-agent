#!/usr/bin/env python3
"""Explicit-file lossless publication archives. No selection, cleanup or execution.

POSIX / Python 3.9+ stdlib only. Root declarations are inventory boundaries, not
independent ownership proof. The caller supplies and authenticates the inventory.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import time
import traceback
import unicodedata
import zlib

BLOCK = 1024 * 1024
MAX_LOGICAL = 64 * 1024 * 1024
MAX_COMPRESSED = 95 * 1024 * 1024  # every shard must be strictly below this
FORMAT = 'explicit-file-lossless-v1'


def strict_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value: raise ValueError('Duplicate JSON key: ' + key)
            value[key] = item
        return value
    def constant(value): raise ValueError('Nonfinite JSON value: ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def sha_bytes(raw): return hashlib.sha256(raw).hexdigest()
def hexsha(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value): raise ValueError('Exact SHA256 required')
    return value


def absolute(raw):
    if not isinstance(raw, str) or not raw.startswith('/') or '\x00' in raw or str(PurePosixPath(raw)) != raw:
        raise ValueError('Normalized absolute POSIX path required')
    if any(p in {'.', '..'} or p.casefold() == '.git' for p in raw.split('/')):
        raise ValueError('Traversal and .git paths are forbidden')
    return Path(raw)


def logical(raw):
    if not isinstance(raw, str) or not raw or raw.startswith('/') or '\\' in raw or '\x00' in raw or str(PurePosixPath(raw)) != raw:
        raise ValueError('Safe normalized relative POSIX logical path required')
    if any(p in {'.', '..'} or p.casefold() == '.git' for p in raw.split('/')):
        raise ValueError('Traversal and .git logical paths are forbidden')
    return raw


def nofollow_open(path, directory=False):
    """Open each absolute path component through a pinned no-symlink dirfd."""
    path = absolute(str(path))
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY'):
        raise RuntimeError('POSIX O_NOFOLLOW/O_DIRECTORY support required')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        parts = path.parts[1:]
        for i, part in enumerate(parts):
            flags = os.O_RDONLY | os.O_NOFOLLOW
            if i < len(parts) - 1 or directory: flags |= os.O_DIRECTORY
            new = os.open(part, flags, dir_fd=fd); os.close(fd); fd = new
        expected = stat.S_ISDIR if directory else stat.S_ISREG
        if not expected(os.fstat(fd).st_mode): raise ValueError('Expected regular file/directory: ' + str(path))
        return fd
    except BaseException:
        os.close(fd); raise


def identity(st):
    return {'device': st.st_dev, 'inode': st.st_ino, 'bytes': st.st_size,
            'mode': format(stat.S_IMODE(st.st_mode), '04o'), 'mtime_ns': st.st_mtime_ns, 'ctime_ns': st.st_ctime_ns}


def read_file(path):
    fd = nofollow_open(path)
    with os.fdopen(fd, 'rb') as stream: return stream.read()


def file_hash(path):
    fd = nofollow_open(path); digest = hashlib.sha256()
    with os.fdopen(fd, 'rb') as stream:
        for data in iter(lambda: stream.read(BLOCK), b''): digest.update(data)
    return digest.hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def spec_validate(value):
    if not isinstance(value, dict) or set(value) != {'version', 'roots', 'files'} or value['version'] != 1:
        raise ValueError('Version1 explicit roots/files spec required')
    roots = {}
    for row in value['roots']:
        if set(row) != {'id', 'kind', 'path'} or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,63}', row['id']) or row['kind'] not in {'positive_owned', 'evidence'}:
            raise ValueError('Explicit named positive_owned/evidence inventory root required')
        absolute(row['path'])
        if row['id'] in roots or any(v['path'] == row['path'] for v in roots.values()): raise ValueError('Duplicate declared root')
        roots[row['id']] = row
    if not roots or not isinstance(value['files'], list) or not value['files']: raise ValueError('Nonempty explicit inventory required')
    originals = set(); names = set(); folded = {}
    for row in value['files']:
        if set(row) != {'root', 'path', 'logical_path', 'sha256', 'bytes', 'mode'} or row['root'] not in roots:
            raise ValueError('Exact explicit file metadata and known root required')
        p = absolute(row['path']); root = absolute(roots[row['root']]['path']); name = logical(row['logical_path'])
        if p == root or not p.is_relative_to(root): raise ValueError('Original file is outside its declared prefix')
        if PurePosixPath(name).name != p.name: raise ValueError('Logical path must preserve original filename')
        hexsha(row['sha256'])
        if type(row['bytes']) is not int or row['bytes'] < 0 or not isinstance(row['mode'], str) or not re.fullmatch('0[0-7]{3}', row['mode']):
            raise ValueError('Exact nonnegative byte count and ordinary octal file mode required')
        if row['path'] in originals or name in names: raise ValueError('Duplicate original/logical file')
        originals.add(row['path']); names.add(name)
        parts = name.split('/')
        for i in range(1, len(parts) + 1):
            prefix = '/'.join(parts[:i]); key = unicodedata.normalize('NFC', prefix).casefold()
            if key in folded and folded[key] != prefix: raise ValueError('Portable case/Unicode logical path collision')
            folded[key] = prefix
    for name in names:
        if any('/'.join(name.split('/')[:i]) in names for i in range(1, len(name.split('/')))):
            raise ValueError('Logical file/directory collision')
    return roots


def root_snapshot(roots):
    result = {}
    for key, row in roots.items():
        fd = nofollow_open(row['path'], directory=True)
        try:
            st = os.fstat(fd); result[key] = {'device': st.st_dev, 'inode': st.st_ino}
        finally: os.close(fd)
    return result


def check_source(row, roots, root_ids, previous=None):
    current_roots = root_snapshot({row['root']: roots[row['root']]})
    if current_roots[row['root']] != root_ids[row['root']]: raise ValueError('Declared root identity changed')
    fd = nofollow_open(row['path']); digest = hashlib.sha256(); count = 0
    with os.fdopen(fd, 'rb') as stream:
        before = identity(os.fstat(stream.fileno()))
        for data in iter(lambda: stream.read(BLOCK), b''): digest.update(data); count += len(data)
        after = identity(os.fstat(stream.fileno()))
    if before != after or (previous is not None and before != previous): raise ValueError('Source changed during archival: ' + row['path'])
    if count != row['bytes'] or digest.hexdigest() != row['sha256'] or before['mode'] != row['mode']:
        raise ValueError('Source SHA/bytes/mode differ from explicit spec: ' + row['path'])
    return before


class Shards:
    def __init__(self, root, limit):
        self.root = root; self.limit = limit; self.parts = []; self.raw = self.gz = self.tar = None
        self.used = self.count = self.payload = 0
    def close(self):
        if self.tar is None: return
        self.tar.close(); self.gz.close(); self.raw.flush(); os.fsync(self.raw.fileno()); self.raw.close()
        path = self.root / self.parts[-1]['file']; size = path.stat().st_size
        if size >= MAX_COMPRESSED: raise ValueError('Compressed shard exceeds strict 95MiB ceiling')
        self.parts[-1].update(bytes=size, sha256=file_hash(path), payload_bytes=self.payload, members=self.count,
                              tar_bytes=((self.used + 1024 + tarfile.RECORDSIZE - 1) // tarfile.RECORDSIZE) * tarfile.RECORDSIZE)
        self.raw = self.gz = self.tar = None
    def add(self, member, data):
        cost = 512 + ((len(data) + 511) // 512) * 512
        if self.tar is not None and self.used + cost + tarfile.RECORDSIZE > self.limit: self.close()
        if self.tar is None:
            name = 'shard-%05d.tar.gz' % len(self.parts); self.parts.append({'file': name})
            self.raw = (self.root / name).open('xb'); self.gz = gzip.GzipFile(filename='', fileobj=self.raw, mode='wb', mtime=0, compresslevel=6)
            self.tar = tarfile.open(fileobj=self.gz, mode='w|', format=tarfile.USTAR_FORMAT)
            self.used = self.count = self.payload = 0
        import io
        header = tarfile.TarInfo(member); header.size = len(data); header.mode = 0o600; header.mtime = 0
        self.tar.addfile(header, io.BytesIO(data)); self.used += cost; self.count += 1; self.payload += len(data)
        return self.parts[-1]['file']


def pack(spec_path, output, shard_mib=64):
    spec_path = absolute(str(spec_path)); output = absolute(str(output))
    raw_spec = read_file(spec_path); spec = strict_json(raw_spec); roots = spec_validate(spec)
    if type(shard_mib) is not int or not 1 <= shard_mib <= 64: raise ValueError('Shard logical limit must be 1..64 MiB')
    if output.exists(): raise ValueError('Fresh archive output directory required')
    parent_fd = nofollow_open(output.parent, directory=True); os.close(parent_fd)
    output.mkdir(mode=0o700)
    writer = None
    try:
        root_ids = root_snapshot(roots)
        before = [check_source(row, roots, root_ids) for row in spec['files']]
        with (output / 'SPEC.json').open('xb') as stream: stream.write(raw_spec); stream.flush(); os.fsync(stream.fileno())
        limit = shard_mib * 1024 * 1024; max_chunk = limit - tarfile.RECORDSIZE - 512
        writer = Shards(output, limit); entries = []
        for index, row in enumerate(spec['files']):
            entry = dict(row); entry['source_identity'] = before[index]; entry['chunks'] = []
            digest = hashlib.sha256(); offset = 0; chunk_index = 0
            fd = nofollow_open(row['path'])
            with os.fdopen(fd, 'rb') as stream:
                if identity(os.fstat(stream.fileno())) != before[index]: raise ValueError('Source changed before pack stream')
                while offset < row['bytes'] or (row['bytes'] == 0 and chunk_index == 0):
                    data = stream.read(min(max_chunk, row['bytes'] - offset)) if row['bytes'] else b''
                    if not data and row['bytes']: raise ValueError('Source truncated during pack')
                    member = 'chunks/%08d/%08d' % (index, chunk_index)
                    shard = writer.add(member, data); digest.update(data)
                    entry['chunks'].append({'shard': shard, 'member': member, 'offset': offset, 'bytes': len(data), 'sha256': sha_bytes(data)})
                    offset += len(data); chunk_index += 1
                if stream.read(1) or identity(os.fstat(stream.fileno())) != before[index]: raise ValueError('Source changed during pack stream')
            if digest.hexdigest() != row['sha256']: raise ValueError('Source content changed during pack stream')
            entries.append(entry)
        writer.close()
        for i, row in enumerate(spec['files']): check_source(row, roots, root_ids, before[i])
        if root_snapshot(roots) != root_ids or read_file(spec_path) != raw_spec: raise ValueError('Root/spec changed during pack')
        index = {'format': FORMAT, 'version': 1, 'created_at_unix': time.time(), 'logical_shard_limit': limit,
                 'compressed_shard_ceiling': MAX_COMPRESSED, 'spec': {'file': 'SPEC.json', 'original_path': str(spec_path), 'sha256': sha_bytes(raw_spec), 'bytes': len(raw_spec)},
                 'roots': [{'id': key, **root_ids[key]} for key in roots], 'files': entries, 'shards': writer.parts,
                 'counts': {'files': len(entries), 'chunks': sum(len(e['chunks']) for e in entries), 'shards': len(writer.parts), 'source_bytes': sum(e['bytes'] for e in entries)},
                 'authority_scope': 'Operator-declared explicit inventory boundaries; ownership/provenance authorization is external. No discovery, cleanup or source execution.'}
        save(output / 'INDEX.json', index)
        save(output / 'SEAL.json', {'format': FORMAT, 'version': 1, 'index_sha256': file_hash(output / 'INDEX.json'), 'spec_sha256': sha_bytes(raw_spec)})
        result = verify(output)
        return {'status': 'packed', 'archive': str(output), **result}
    except BaseException as error:
        if writer is not None:
            try: writer.close()
            except BaseException: pass
        save(output / 'FAILED.json', {'status': 'failed', 'error': {'type': type(error).__name__, 'message': str(error)}, 'traceback': traceback.format_exc(),
                                    'scope': 'Partial output retained; no retry/overwrite, source edits or cleanup performed'})
        raise


class StrictGzip:
    """Bounded streaming one-member gzip with CRC/truncation/trailing rejection."""
    def __init__(self, raw, limit):
        self.raw = raw; self.limit = limit; self.z = zlib.decompressobj(31); self.pending = b''
        self.hash = hashlib.sha256(); self.compressed = self.plain = 0; self.done = False
    def read(self, size):
        result = bytearray()
        while len(result) < size and not self.done:
            if not self.pending:
                self.pending = self.raw.read(65536)
                if not self.pending:
                    if not self.z.eof: raise ValueError('Truncated gzip shard')
                    self.done = True; break
                self.hash.update(self.pending); self.compressed += len(self.pending)
            data = self.z.decompress(self.pending, size - len(result)); self.pending = self.z.unconsumed_tail
            result.extend(data); self.plain += len(data)
            if self.plain > self.limit: raise ValueError('Expanded tar exceeds logical shard limit')
            if self.z.eof:
                if self.z.unused_data or self.pending or self.raw.read(1): raise ValueError('Extra compressed member/trailing bytes')
                self.done = True
        return bytes(result)
    def exact(self, size):
        value = self.read(size)
        if len(value) != size: raise ValueError('Truncated tar member/header')
        return value


def archive_metadata(archive, expected_index=None):
    archive = absolute(str(archive)); fd = nofollow_open(archive, directory=True); os.close(fd)
    seal = strict_json(read_file(archive / 'SEAL.json')); raw_index = read_file(archive / 'INDEX.json')
    if seal.get('format') != FORMAT or seal.get('version') != 1 or set(seal) != {'format', 'version', 'index_sha256', 'spec_sha256'}:
        raise ValueError('Exact archive seal required')
    actual_sha = sha_bytes(raw_index)
    if hexsha(seal['index_sha256']) != actual_sha or (expected_index is not None and hexsha(expected_index) != actual_sha): raise ValueError('Index SHA seal differs')
    index = strict_json(raw_index); raw_spec = read_file(archive / 'SPEC.json'); spec = strict_json(raw_spec); roots = spec_validate(spec)
    if index.get('format') != FORMAT or index.get('version') != 1: raise ValueError('Unknown archive index format')
    if set(index) != {'format', 'version', 'created_at_unix', 'logical_shard_limit', 'compressed_shard_ceiling', 'spec', 'roots', 'files', 'shards', 'counts', 'authority_scope'}:
        raise ValueError('Unexpected index fields')
    if index['spec'] != {'file': 'SPEC.json', 'original_path': index['spec']['original_path'], 'sha256': sha_bytes(raw_spec), 'bytes': len(raw_spec)} or seal['spec_sha256'] != sha_bytes(raw_spec):
        raise ValueError('Original explicit spec SHA/bytes changed')
    absolute(index['spec']['original_path'])  # lexical only; NEVER open originals
    limit = index['logical_shard_limit']
    if type(limit) is not int or not 1024 * 1024 <= limit <= MAX_LOGICAL or limit % (1024 * 1024) or index['compressed_shard_ceiling'] != MAX_COMPRESSED:
        raise ValueError('Invalid bounded shard limits')
    if len(index['files']) != len(spec['files']) or len(index['roots']) != len(roots) or {r['id'] for r in index['roots']} != set(roots): raise ValueError('Index file/root count differs from explicit spec')
    for root in index['roots']:
        if set(root) != {'id', 'device', 'inode'} or any(type(root[k]) is not int or root[k] < 0 for k in ['device', 'inode']): raise ValueError('Invalid packed root provenance')
    expected = {}; chunk_count = 0; last_shard = -1
    for i, (entry, original) in enumerate(zip(index['files'], spec['files'])):
        if any(entry.get(k) != v for k, v in original.items()) or set(entry) != set(original) | {'source_identity', 'chunks'}:
            raise ValueError('Index selected-file metadata differs from original spec')
        source = entry['source_identity']
        if set(source) != {'device', 'inode', 'bytes', 'mode', 'mtime_ns', 'ctime_ns'} or source['bytes'] != entry['bytes'] or source['mode'] != entry['mode'] or any(type(source[k]) is not int or source[k] < 0 for k in ['device', 'inode', 'bytes', 'mtime_ns', 'ctime_ns']):
            raise ValueError('Invalid source provenance metadata')
        offset = 0
        if not entry['chunks']: raise ValueError('Missing file chunks')
        for j, chunk in enumerate(entry['chunks']):
            if set(chunk) != {'shard', 'member', 'offset', 'bytes', 'sha256'} or chunk['member'] != 'chunks/%08d/%08d' % (i, j): raise ValueError('Unsafe/duplicate/foreign member identity')
            if not re.fullmatch('shard-[0-9]{5}\.tar\.gz', chunk['shard']): raise ValueError('Unsafe shard path')
            number = int(chunk['shard'][6:11])
            if number < last_shard: raise ValueError('Reordered file chunks')
            last_shard = number
            if type(chunk['offset']) is not int or chunk['offset'] != offset or type(chunk['bytes']) is not int or not 0 <= chunk['bytes'] <= limit - tarfile.RECORDSIZE - 512:
                raise ValueError('Invalid chunk offsets/lengths')
            if chunk['bytes'] == 0 and not (entry['bytes'] == 0 and len(entry['chunks']) == 1): raise ValueError('Invalid empty chunk')
            hexsha(chunk['sha256']); offset += chunk['bytes']; chunk_count += 1
            expected.setdefault(chunk['shard'], []).append((i, chunk))
        if offset != entry['bytes']: raise ValueError('Missing/extra reconstructed file bytes')
    shard_names = []
    for n, row in enumerate(index['shards']):
        name = 'shard-%05d.tar.gz' % n
        if row.get('file') != name or set(row) != {'file', 'bytes', 'sha256', 'payload_bytes', 'members', 'tar_bytes'} or name not in expected: raise ValueError('Missing/extra/duplicate shard')
        hexsha(row['sha256'])
        if any(type(row[k]) is not int or row[k] < 0 for k in ['payload_bytes', 'members', 'tar_bytes']): raise ValueError('Invalid shard counts')
        if type(row['bytes']) is not int or not 0 < row['bytes'] < MAX_COMPRESSED: raise ValueError('Compressed shard ceiling violated')
        chunks = expected[name]; cost = sum(512 + ((c['bytes'] + 511) // 512) * 512 for _, c in chunks)
        total_tar = ((cost + 1024 + tarfile.RECORDSIZE - 1) // tarfile.RECORDSIZE) * tarfile.RECORDSIZE
        if row['members'] != len(chunks) or row['payload_bytes'] != sum(c['bytes'] for _, c in chunks) or row['tar_bytes'] != total_tar or total_tar > limit:
            raise ValueError('Shard member/payload/logical counts differ')
        shard_names.append(name)
    if set(expected) != set(shard_names): raise ValueError('Unlisted/missing shard reference')
    counts = {'files': len(index['files']), 'chunks': chunk_count, 'shards': len(shard_names), 'source_bytes': sum(e['bytes'] for e in index['files'])}
    if index['counts'] != counts or any(type(v) is not int for v in index['counts'].values()): raise ValueError('Archive counts differ')
    allowed = {'INDEX.json', 'SPEC.json', 'SEAL.json', *shard_names}
    if {p.name for p in archive.iterdir()} != allowed: raise ValueError('Extra/missing archive files')
    for p in archive.iterdir():
        fd = nofollow_open(p); os.close(fd)
    return archive, index, expected, actual_sha


def verify(archive, expected_index=None, sink=None):
    archive, index, expected, index_sha = archive_metadata(archive, expected_index)
    full = [hashlib.sha256() for _ in index['files']]; sizes = [0] * len(full)
    for row in index['shards']:
        fd = nofollow_open(archive / row['file'])
        with os.fdopen(fd, 'rb') as raw:
            if os.fstat(raw.fileno()).st_size != row['bytes']: raise ValueError('Shard compressed size differs')
            gz = StrictGzip(raw, index['logical_shard_limit']); used = 0
            for file_id, chunk in expected[row['file']]:
                header = gz.exact(512); used += 512
                info = tarfile.TarInfo.frombuf(header, 'utf-8', 'strict')
                if header[257:265] != tarfile.POSIX_MAGIC or info.type != tarfile.REGTYPE or info.name != chunk['member'] or info.size != chunk['bytes']:
                    raise ValueError('Extra/missing/duplicate/traversal/non-regular tar member')
                if info.mode != 0o600 or info.uid or info.gid or info.mtime or info.linkname or info.uname or info.gname: raise ValueError('Unexpected tar metadata')
                part = hashlib.sha256(); remaining = info.size
                if sink is not None: sink.begin(file_id, chunk['offset'])
                while remaining:
                    data = gz.exact(min(BLOCK, remaining)); remaining -= len(data); used += len(data)
                    part.update(data); full[file_id].update(data); sizes[file_id] += len(data)
                    if sink is not None: sink.write(file_id, data)
                padding = (-info.size) % 512
                if gz.exact(padding) != b'\0' * padding: raise ValueError('Corrupt tar padding')
                used += padding
                if part.hexdigest() != chunk['sha256']: raise ValueError('Chunk SHA differs')
                if sink is not None: sink.end(file_id, chunk['offset'] + chunk['bytes'])
            tail = row['tar_bytes'] - used
            if tail < 1024 or gz.exact(tail) != b'\0' * tail or gz.read(1): raise ValueError('Extra/truncated tar members or trailer')
            if not gz.done or gz.plain != row['tar_bytes'] or gz.compressed != row['bytes'] or gz.hash.hexdigest() != row['sha256']:
                raise ValueError('Compressed/logical shard SHA/count differs')
    for i, entry in enumerate(index['files']):
        if sizes[i] != entry['bytes'] or full[i].hexdigest() != entry['sha256']: raise ValueError('Full reconstructed file SHA/bytes differ')
    # Catch metadata changes while the stream was being verified.
    _, again, _, after_sha = archive_metadata(archive, index_sha)
    if again != index or after_sha != index_sha: raise ValueError('Archive changed during verification')
    return {'status': 'verified', 'index_sha256': index_sha, **index['counts']}


class RestoreSink:
    def __init__(self, root, entries, readonly): self.root = root; self.entries = entries; self.readonly = readonly; self.current = None; self.stream = None; self.mapping = {}
    def begin(self, file_id, offset):
        if self.current == file_id: return
        if self.stream is not None: raise ValueError('Non-sequential restore file')
        entry = self.entries[file_id]; parts = entry['logical_path'].split('/'); fd = nofollow_open(self.root, directory=True)
        try:
            for part in parts[:-1]:
                try: os.mkdir(part, 0o700, dir_fd=fd)
                except FileExistsError: pass
                new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd); os.close(fd); fd = new
            out = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
        finally: os.close(fd)
        if offset != 0: os.close(out); raise ValueError('Restore file did not start at offset zero')
        self.stream = os.fdopen(out, 'wb'); self.current = file_id
    def write(self, file_id, data): self.stream.write(data)
    def end(self, file_id, offset):
        entry = self.entries[file_id]
        if offset != entry['bytes']: return
        mode = int(entry['mode'], 8); mode = mode & ~0o222 if self.readonly else mode
        self.stream.flush(); os.fsync(self.stream.fileno()); os.fchmod(self.stream.fileno(), mode); self.stream.close(); self.stream = None; self.current = None
        self.mapping[entry['path']] = {'physical_path': str(self.root / entry['logical_path']), 'logical_path': entry['logical_path'],
                                       'sha256': entry['sha256'], 'bytes': entry['bytes'], 'original_mode': entry['mode'], 'restored_mode': format(mode, '04o')}
    def close(self):
        if self.stream is not None: self.stream.close(); self.stream = None


def restore(archive, dest, expected_index=None, readonly=False):
    dest = absolute(str(dest)); archive = absolute(str(archive))
    if dest.exists() or dest == archive or dest.is_relative_to(archive): raise ValueError('Fresh disposable restore directory outside archive required')
    verify(archive, expected_index); _, index, _, index_sha = archive_metadata(archive, expected_index)
    original_paths = {e['path'] for e in index['files']}
    targets = {str(dest / 'files' / e['logical_path']) for e in index['files']} | {str(dest / 'RESTORED-MAP.json'), str(dest / 'RESTORE-FAILED.json')}
    if original_paths & targets: raise ValueError('Restore may NEVER target an original absolute file path')
    fd = nofollow_open(dest.parent, directory=True); os.close(fd)
    dest.mkdir(mode=0o700); (dest / 'files').mkdir(mode=0o700); sink = RestoreSink(dest / 'files', index['files'], readonly)
    try:
        result = verify(archive, index_sha, sink)
        mapping = {'format': FORMAT, 'version': 1, 'index_sha256': index_sha, 'namespace': str(dest / 'files'), 'mappings': sink.mapping,
                   'scope': 'Virtual restore only; original absolute paths and original JSON/data bytes are not rewritten or used as destinations'}
        save(dest / 'RESTORED-MAP.json', mapping)
        return {'status': 'restored', 'dest': str(dest), 'mapping': str(dest / 'RESTORED-MAP.json'), **{k: v for k, v in result.items() if k != 'status'}}
    except BaseException as error:
        sink.close(); save(dest / 'RESTORE-FAILED.json', {'status': 'failed', 'error': {'type': type(error).__name__, 'message': str(error)}, 'scope': 'Partial virtual restore retained; no original changes or cleanup'})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('pack'); p.add_argument('--spec', type=Path, required=True); p.add_argument('--output', type=Path, required=True); p.add_argument('--shard-mib', type=int, default=64)
    for name in ['verify', 'restore']:
        p = sub.add_parser(name); p.add_argument('--archive', type=Path, required=True); p.add_argument('--index-sha256')
        if name == 'restore': p.add_argument('--dest', type=Path, required=True); p.add_argument('--read-only', action='store_true')
    args = parser.parse_args()
    if args.command == 'pack': result = pack(args.spec, args.output, args.shard_mib)
    elif args.command == 'verify': result = verify(args.archive, args.index_sha256)
    else: result = restore(args.archive, args.dest, args.index_sha256, args.read_only)
    print(json.dumps(result, indent=2, sort_keys=True)); return 0


if __name__ == '__main__':
    try: raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status': 'rejected', 'error': type(error).__name__, 'message': str(error)}), file=__import__('sys').stderr)
        raise SystemExit(2)
