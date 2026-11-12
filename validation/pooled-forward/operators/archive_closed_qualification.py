#!/usr/bin/env python3
"""Explicitly inventory/preserve the closed qualification tree, without cleanup.

Raw synthetic symlink structure is metadata only. The frozen inner archive and
reviewed lossless transport verify every selected ordinary file's exact bytes.
This entry does not select business results or infer quality.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import time
import traceback


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
    path.chmod(0o444)


def module(path, wanted, name):
    if sha(path) != wanted: raise ValueError('Frozen archive source differs')
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result


def main():
    root = Path(__file__).resolve().parents[1]
    source = root / 'qualification'; control = root / 'operators/archive-selection/closed-qualification-v1'
    scratch = root / 'cache/publication-archives/closed-qualification-v1'
    cold = root / 'publications/closed-qualification-v1'
    for p in [control, scratch, cold]:
        if p.exists(): raise ValueError('Fresh closed qualification namespaces required')
    control.mkdir(parents=True); scratch.mkdir(parents=True)
    started = time.clock_gettime(time.CLOCK_MONOTONIC)
    save(control / 'ENTRY.json', {'version': 1, 'source': str(source), 'source_device': source.stat().st_dev,
        'source_inode': source.stat().st_ino, 'script_sha256': sha(Path(__file__)),
        'started_at_unix': time.time(), 'started_at_clock_gettime': started,
        'scope': 'Every ordinary closed qualification file, all outcomes and failures; no quality filtering, SDK, business input, original mutation or cleanup.'})
    files, structure = [], []
    try:
        for base, dirs, names in os.walk(source, followlinks=False):
            dirs.sort(); names.sort()
            for name in dirs + names:
                p = Path(base) / name; s = p.lstat(); rel = p.relative_to(source).as_posix()
                if '\\' in rel or any(v.casefold() == '.git' for v in p.relative_to(source).parts):
                    raise ValueError('Unsafe synthetic path requires separate byte-copy admission: ' + rel)
                common = {'relative': rel, 'device': s.st_dev, 'inode': s.st_ino, 'mode': format(stat.S_IMODE(s.st_mode), '04o')}
                if stat.S_ISLNK(s.st_mode):
                    structure.append(dict(common, kind='symlink-metadata-only', target=os.readlink(p)))
                    if name in dirs: dirs.remove(name)
                elif stat.S_ISDIR(s.st_mode):
                    structure.append(dict(common, kind='directory'))
                elif stat.S_ISREG(s.st_mode):
                    if stat.S_IMODE(s.st_mode) > 0o777: raise ValueError('Special mode requires explicit admission')
                    digest = sha(p); after = p.lstat()
                    if (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                        raise ValueError('Closed qualification input changed')
                    files.append({'root': 'qualification', 'path': str(p), 'logical_path': 'qualification/' + rel,
                                  'sha256': digest, 'bytes': s.st_size, 'mode': common['mode']})
                else:
                    structure.append(dict(common, kind='special-metadata-only', size=s.st_size))
        metadata = control / 'STRUCTURE.json'
        save(metadata, {'version': 1, 'source': str(source), 'entries': structure,
            'scope': 'Original directories/symlink/special metadata only. No external target read or active link recreation.'})
        files.append({'root': 'selection', 'path': str(metadata), 'logical_path': 'selection/STRUCTURE.json',
                      'sha256': sha(metadata), 'bytes': metadata.stat().st_size, 'mode': '0444'})
        spec_path = control / 'SPEC.json'
        save(spec_path, {'version': 1, 'roots': [{'id': 'qualification', 'kind': 'evidence', 'path': str(source)},
                                              {'id': 'selection', 'kind': 'evidence', 'path': str(control)}], 'files': files})
        save(control / 'PREPARED.json', {'version': 1, 'spec_sha256': sha(spec_path),
            'regular_files_including_structure': len(files), 'source_bytes': sum(f['bytes'] for f in files),
            'structural_entries': len(structure), 'symlink_targets_followed': 0})
        archive = module(root / 'publication-tools/archive.py',
            'c412b03c20c9c97b59a550bd5afa02c4c6fd58d0fbd6f9dc81a3bdf9b02796b8', 'closed_qualification_archive')
        packed = archive.pack(spec_path, scratch / 'archive')
        save(control / 'PACKED.json', packed)
        cold_module = module(root / 'publication-transport-review/revision-v2/publication-tools/cold_storage/cold.py',
            'b5f8ad775e68312928b1d3cc9e2c5807edb47083a33929dd4f86611d459d0991', 'closed_qualification_transport')
        transported = cold_module.pack(scratch / 'archive', sha(scratch / 'archive/INDEX.json'), cold)
        save(control / 'TRANSPORTED.json', transported)
        save(control / 'END.json', {'version': 1, 'status': 'packed-and-transport-verified',
            'finished_at_unix': time.time(), 'finished_at_clock_gettime': time.clock_gettime(time.CLOCK_MONOTONIC),
            'wall_seconds': time.clock_gettime(time.CLOCK_MONOTONIC) - started,
            'cold': str(cold), 'transport_sha256': transported['transport_sha256'],
            'originals_retained': True, 'virtual_restore_pending': True,
            'scope': 'Preservation only; no native or product quality credit. No cleanup performed.'})
        print(json.dumps({'status': 'preserved', 'files': len(files), 'cold': str(cold),
                          'transport_sha256': transported['transport_sha256']}))
    except BaseException as error:
        save(control / 'FAILED.json', {'version': 1, 'error': {'type': type(error).__name__, 'message': str(error)},
            'traceback': traceback.format_exc(), 'originals_retained': True, 'cleanup_performed': False})
        raise


if __name__ == '__main__': main()
