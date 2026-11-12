"""Lossless transport compression for the frozen archive's large JSON indexes.

No dataset selection, original-path access, cleanup, extraction or SDK execution.
The frozen inner archive remains authoritative; decoded bytes must verify there.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat


ARCHIVE_SHA = 'c412b03c20c9c97b59a550bd5afa02c4c6fd58d0fbd6f9dc81a3bdf9b02796b8'
LIMIT = 32 * 1024 ** 3
SEAL_LIMIT = 4 * 1024 ** 2


def need(value, message):
    if not value: raise ValueError(message)


def physical(raw, *, fresh=False):
    raw = os.fspath(raw); p = Path(raw)
    need(p.is_absolute() and str(p) == raw and '..' not in p.parts and '\\' not in raw,
         'Canonical absolute physical path required')
    for part in [p, *p.parents]:
        need(not part.is_symlink(), 'Symlink in archive transport path')
    if fresh: need(not p.exists(), 'Fresh output directory required')
    return p


def hash_file(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()


def strict_json(raw):
    def pairs(rows):
        value = {}
        for k, v in rows:
            need(k not in value, 'Duplicate transport metadata member'); value[k] = v
        return value
    def bad(_): raise ValueError('Nonfinite transport metadata')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def archive_module():
    p = Path(__file__).resolve().parent.parent / 'archive.py'
    need(hash_file(p) == ARCHIVE_SHA, 'Frozen inner archive code differs')
    spec = importlib.util.spec_from_file_location('transport_frozen_archive', p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def write(path, raw):
    with path.open('xb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    path.chmod(0o444)


def disjoint(source, output):
    need(source != output and source not in output.parents and output not in source.parents,
         'Fresh disjoint archive transport output required')
    identity = (source.stat().st_dev, source.stat().st_ino)
    for parent in output.parents:
        if parent.exists():
            s = parent.stat()
            need((s.st_dev, s.st_ino) != identity, 'Output aliases a source descendant')


def source_files(folder):
    names = set()
    for p in folder.iterdir():
        need(stat.S_ISREG(p.lstat().st_mode), 'Only regular inner archive members allowed')
        need(p.name in {'INDEX.json', 'SPEC.json', 'SEAL.json'} or re.fullmatch(r'shard-\d{5}\.tar\.gz', p.name),
             'Unexpected inner archive member')
        names.add(p.name)
    need({'INDEX.json', 'SPEC.json', 'SEAL.json'} <= names, 'Missing inner archive metadata')
    return sorted(names)


def pack(archive, index_sha256, output):
    need(isinstance(index_sha256, str) and re.fullmatch('[0-9a-f]{64}', index_sha256),
         'Exact external original index SHA256 required')
    source, output = physical(archive), physical(output, fresh=True)
    disjoint(source, output)
    module = archive_module(); verified = module.verify(source, index_sha256)
    names = source_files(source); output.mkdir(parents=True)
    rows = {}
    for name in names:
        p = source / name; before = p.stat(); wanted = hash_file(p)
        stored = name + '.gz' if name in {'INDEX.json', 'SPEC.json'} else name
        target = output / stored
        with p.open('rb') as src, target.open('xb') as dst:
            if stored != name:
                with gzip.GzipFile(filename='', mode='wb', fileobj=dst, mtime=0) as zipped:
                    shutil.copyfileobj(src, zipped, 1024 * 1024)
            else: shutil.copyfileobj(src, dst, 1024 * 1024)
            dst.flush(); os.fsync(dst.fileno())
        target.chmod(0o444)
        after = p.stat()
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) and hash_file(p) == wanted,
             'Inner archive changed during transport compression')
        rows[name] = {'stored': stored, 'sha256': wanted, 'bytes': before.st_size,
                      'stored_sha256': hash_file(target), 'stored_bytes': target.stat().st_size}
    need(source_files(source) == names, 'Inner archive namespace changed')
    module.verify(source, index_sha256)
    seal = {'version': 1, 'kind': 'lossless-frozen-archive-transport', 'index_sha256': index_sha256,
            'archive_code_sha256': ARCHIVE_SHA, 'files': rows,
            'scope': 'INDEX/SPEC are gzip-compressed original bytes. Other members are exact copies. No original dataset path is read during decoding or inner verification; no quality inference.'}
    raw = (json.dumps(seal, sort_keys=True, indent=2) + '\n').encode()
    need(len(raw) <= SEAL_LIMIT, 'Bounded transport seal required')
    write(output / 'TRANSPORT.json', raw)
    return {'transport_sha256': hash_file(output / 'TRANSPORT.json'), 'inner_verified': verified,
            'original_member_bytes': sum(r['bytes'] for r in rows.values()),
            'stored_member_bytes': sum(r['stored_bytes'] for r in rows.values())}


def decode(cold, seal_sha256, output):
    cold, output = physical(cold), physical(output, fresh=True)
    disjoint(cold, output)
    need(all(stat.S_ISREG(p.lstat().st_mode) for p in cold.iterdir()), 'Only regular transport members allowed')
    need((cold / 'TRANSPORT.json').lstat().st_size <= SEAL_LIMIT, 'Transport seal is too large')
    need(re.fullmatch('[0-9a-f]{64}', seal_sha256) and hash_file(cold / 'TRANSPORT.json') == seal_sha256,
         'External transport pin differs')
    seal = strict_json((cold / 'TRANSPORT.json').read_bytes())
    need(type(seal.get('version')) is int and seal['version'] == 1 and
         seal.get('kind') == 'lossless-frozen-archive-transport' and seal['archive_code_sha256'] == ARCHIVE_SHA,
         'Wrong transport schema/code pin')
    need(isinstance(seal.get('index_sha256'), str) and re.fullmatch('[0-9a-f]{64}', seal['index_sha256']),
         'Exact external original index SHA256 required')
    rows = seal['files']; need(isinstance(rows, dict), 'Explicit transport inventory required')
    need({'INDEX.json', 'SPEC.json', 'SEAL.json'} <= set(rows), 'Missing transported inner metadata')
    stored_names = {'TRANSPORT.json'}
    for name, row in rows.items():
        need(name in {'INDEX.json', 'SPEC.json', 'SEAL.json'} or re.fullmatch(r'shard-\d{5}\.tar\.gz', name),
             'Unsafe inner archive filename')
        expected = name + '.gz' if name in {'INDEX.json', 'SPEC.json'} else name
        need(row['stored'] == expected and expected not in stored_names, 'Unsafe or aliased stored filename')
        need(type(row['bytes']) is int and 0 <= row['bytes'] <= LIMIT and
             type(row['stored_bytes']) is int and 0 <= row['stored_bytes'] <= LIMIT,
             'Bounded exact byte counts required')
        for key in ['sha256', 'stored_sha256']:
            need(isinstance(row[key], str) and re.fullmatch('[0-9a-f]{64}', row[key]), 'Exact member SHA required')
        stored_names.add(expected)
    need({p.name for p in cold.iterdir()} == stored_names and
         all(stat.S_ISREG(p.lstat().st_mode) for p in cold.iterdir()), 'Transport member namespace differs')
    output.mkdir(parents=True)
    for name, row in rows.items():
        source, target = cold / row['stored'], output / name
        need(source.stat().st_size == row['stored_bytes'] and hash_file(source) == row['stored_sha256'],
             'Stored original member differs')
        h = hashlib.sha256(); size = 0
        with source.open('rb') as src, target.open('xb') as dst:
            stream = gzip.GzipFile(fileobj=src, mode='rb') if row['stored'] != name else src
            try:
                while True:
                    block = stream.read(min(1024 * 1024, row['bytes'] - size + 1))
                    if not block: break
                    size += len(block); need(size <= row['bytes'], 'Transport expansion exceeds declared bytes')
                    h.update(block); dst.write(block)
            finally:
                if stream is not src: stream.close()
            dst.flush(); os.fsync(dst.fileno())
        target.chmod(0o444)
        need(size == row['bytes'] and h.hexdigest() == row['sha256'], 'Decoded original bytes differ')
        need(hash_file(source) == row['stored_sha256'], 'Transport changed while decoding')
    need(hash_file(cold / 'TRANSPORT.json') == seal_sha256, 'Transport seal changed during decode')
    result = archive_module().verify(output, seal['index_sha256'])
    return {'status': 'verified', 'transport_sha256': seal_sha256, 'inner_verified': result}


def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('pack'); a.add_argument('--archive', required=True); a.add_argument('--index-sha256', required=True); a.add_argument('--output', required=True)
    a = sub.add_parser('decode'); a.add_argument('--cold', required=True); a.add_argument('--transport-sha256', required=True); a.add_argument('--output', required=True)
    a = p.parse_args()
    print(json.dumps(pack(a.archive, a.index_sha256, a.output) if a.command == 'pack' else decode(a.cold, a.transport_sha256, a.output), sort_keys=True))


if __name__ == '__main__': main()
