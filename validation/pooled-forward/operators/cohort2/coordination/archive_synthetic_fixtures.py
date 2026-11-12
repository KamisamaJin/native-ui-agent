#!/usr/bin/env python3
"""Preserve closed synthetic fixtures explicitly; never read business evidence.

All selection roots are the closed tool authors' synthetic HOST prefixes.
No deletion, source/grade/oracle change, SDK, or actual alarm access occurs.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import time


ARCHIVE_SHA = 'c412b03c20c9c97b59a550bd5afa02c4c6fd58d0fbd6f9dc81a3bdf9b02796b8'


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def save(p, value):
    with p.open('x') as f:
        json.dump(value, f, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    p.chmod(0o444)


def ref(p): return {'path': str(p), 'sha256': sha(p)}


def main():
    a = argparse.ArgumentParser(); a.add_argument('--root', type=Path, required=True)
    a.add_argument('--id', required=True); args = a.parse_args()
    assert args.id.isascii() and args.id.replace('-', '').isalnum()
    root = args.root.resolve()
    output = root / 'operators/archive-selection' / args.id
    output.mkdir(parents=True, exist_ok=False)
    scratch = root / 'cache/publication-archives' / args.id
    scratch.mkdir(parents=True, exist_ok=False)
    exceptions = scratch / 'preserved-exceptions'; exceptions.mkdir()
    meta_dir = scratch / 'metadata'; meta_dir.mkdir()
    selected = []
    for parent, prefix in [
            ('publication-native-chain/HOST', 'synthetic'),
            ('publication-native-chain/history/HOST', 'synthetic'),
            ('publication-tools/HOST', 'attempt-'),
            ('publication-resolver/HOST', 'synthetic-')]:
        selected.extend(p for p in sorted((root / parent).iterdir())
                        if p.name.startswith(prefix) and p.is_dir() and not p.is_symlink())
    assert selected and all('/cache/business/' not in str(p) for p in selected)
    roots = [{'id': 'preserved-exceptions', 'kind': 'evidence', 'path': str(exceptions)},
             {'id': 'fixture-metadata', 'kind': 'evidence', 'path': str(meta_dir)}]
    files, metadata, links, directories = [], [], [], []
    allocations = logical = 0
    started = time.clock_gettime(time.CLOCK_MONOTONIC)
    save(output / 'ENTRY.json', {'version': 1, 'kind': 'explicit-closed-synthetic-fixture-archive-entry',
        'at_unix': time.time(), 'selection': [str(p) for p in selected],
        'frozen_archiver': ref(root / 'publication-tools/archive.py'),
        'author_freezes': [ref(root / p) for p in ['publication-native-chain/FREEZE.json',
            'publication-native-chain/history/FREEZE.json', 'publication-tools/FREEZE.json',
            'publication-resolver/FREEZE.json']],
        'scope': 'Closed synthetic prefixes only, including development failures. No actual business source/grade/alarm/map/native evidence; no cleanup.'})
    assert sha(root / 'publication-tools/archive.py') == ARCHIVE_SHA
    for i, source_root in enumerate(selected):
        key = f'host-{i:03d}'; s = source_root.lstat()
        roots.append({'id': key, 'kind': 'evidence', 'path': str(source_root)})
        directories.append({'path': str(source_root), 'device': s.st_dev, 'inode': s.st_ino,
                            'mode': format(stat.S_IMODE(s.st_mode), '04o')})
        for cur, ds, fs in os.walk(source_root, followlinks=False):
            for name in list(ds):
                p = Path(cur, name); s = p.lstat()
                if stat.S_ISLNK(s.st_mode): ds.remove(name); fs.append(name)
                else:
                    assert stat.S_ISDIR(s.st_mode)
                    directories.append({'path': str(p), 'device': s.st_dev, 'inode': s.st_ino,
                                        'mode': format(stat.S_IMODE(s.st_mode), '04o')})
            for name in sorted(fs):
                original = Path(cur, name); s = original.lstat()
                if not stat.S_ISREG(s.st_mode):
                    links.append({'path': str(original), 'kind': 'symlink' if stat.S_ISLNK(s.st_mode) else 'special',
                                  'mode': format(stat.S_IMODE(s.st_mode), '04o'),
                                  **({'target': os.readlink(original)} if stat.S_ISLNK(s.st_mode) else {})})
                    continue
                h = sha(original); destination = original; root_id = key
                copy_needed = (any(v.casefold() == '.git' for v in original.parts)
                               or '\\' in str(original) or stat.S_IMODE(s.st_mode) & 0o7000)
                if copy_needed:
                    destination = exceptions / h; root_id = 'preserved-exceptions'
                    if not destination.exists():
                        with original.open('rb') as src, destination.open('xb') as dst:
                            for block in iter(lambda: src.read(1024 * 1024), b''): dst.write(block)
                            dst.flush(); os.fsync(dst.fileno())
                        destination.chmod(0o444)
                    assert sha(destination) == h
                after = original.lstat()
                assert (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns) == (
                    after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                n = len(metadata); logical += s.st_size; allocations += s.st_blocks * 512
                row = {'id': n, 'original': str(original), 'source_root': str(source_root),
                       'relative': original.relative_to(source_root).as_posix(), 'sha256': h,
                       'bytes': s.st_size, 'mode': format(stat.S_IMODE(s.st_mode), '04o'),
                       'device': s.st_dev, 'inode': s.st_ino, 'stored_input': str(destination),
                       'safe_copy_for_negative_path_or_mode': bool(copy_needed)}
                metadata.append(row)
                # Multiple unsafe-path files with identical bytes need one safe
                # input member; every original alias remains in metadata.
                if not copy_needed or not any(r['path'] == str(destination) for r in files if r['root'] == 'preserved-exceptions'):
                    logical_name = f'{root_id}/file-{n:08d}'
                    files.append({'root': root_id, 'path': str(destination), 'logical_path': logical_name,
                                  'sha256': h, 'bytes': s.st_size,
                                  'mode': format(stat.S_IMODE(destination.lstat().st_mode), '04o')})
    meta_path = meta_dir / 'FIXTURE-METADATA.json'
    save(meta_path, {'version': 1, 'kind': 'closed-synthetic-fixture-raw-and-structural-inventory',
                    'files': metadata, 'directories': directories, 'symlink_or_special_metadata_only': links,
                    'scope': 'Regular original bytes are archived; negative symlink targets/special entries are structural metadata only and were never followed/opened. Safe copies preserve forbidden negative path/mode bytes plus their original mapping. No restore aliases or live namespace reconstruction is implied.'})
    files.append({'root': 'fixture-metadata', 'path': str(meta_path), 'logical_path': 'fixture-metadata/FIXTURE-METADATA.json',
                  'sha256': sha(meta_path), 'bytes': meta_path.stat().st_size, 'mode': '0444'})
    spec = scratch / 'SPEC.json'; save(spec, {'version': 1, 'roots': roots, 'files': files})
    prepared = {'version': 1, 'kind': 'closed-synthetic-fixture-explicit-selection',
                'entry': ref(output / 'ENTRY.json'), 'spec': ref(spec), 'metadata': ref(meta_path),
                'selected_roots': len(selected), 'original_regular_files': len(metadata),
                'structural_links_or_special': len(links), 'original_logical_bytes': logical,
                'original_sampled_allocated_bytes': allocations,
                'preparation_wall_seconds': time.clock_gettime(time.CLOCK_MONOTONIC) - started}
    save(output / 'PREPARED.json', prepared)
    module_spec = importlib.util.spec_from_file_location('pinned_archive_synthetic', root / 'publication-tools/archive.py')
    archive = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(archive)
    result = archive.pack(spec, scratch / 'archive', 64)
    verified = archive.verify(scratch / 'archive', sha(scratch / 'archive/INDEX.json'))
    save(output / 'PACKED.json', {'version': 1, 'prepared': ref(output / 'PREPARED.json'),
         'archive': str(scratch / 'archive'), 'index': ref(scratch / 'archive/INDEX.json'),
         'result': result, 'verified': verified, 'actual_business_access': False,
         'scope': 'Frozen archiver original-byte verification only; not virtual restore, cold transport acceptance, quality inference or permission to clean.'})
    print(json.dumps({'selection': str(output), 'regular_files': len(metadata),
                      'structural_only': len(links), 'index_sha256': sha(scratch / 'archive/INDEX.json'),
                      'status': verified['status']}))


if __name__ == '__main__': main()
