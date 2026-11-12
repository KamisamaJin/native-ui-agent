#!/usr/bin/env python3
"""Binding-only correction of a retained explicit synthetic archive spec.

Preserve the complete selection and source pins; the frozen archiver requires
each logical leaf filename to equal its original selected input filename.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import time
import traceback


ARCHIVE_SHA = 'c412b03c20c9c97b59a550bd5afa02c4c6fd58d0fbd6f9dc81a3bdf9b02796b8'


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()


def ref(p): return {'path': str(p), 'sha256': sha(p)}


def save(p, v):
    with p.open('x') as f:
        json.dump(v, f, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    p.chmod(0o444)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, required=True)
    p.add_argument('--prepared', type=Path, required=True); p.add_argument('--prepared-sha256', required=True)
    p.add_argument('--id', required=True); a = p.parse_args()
    root = a.root.resolve(); assert a.id.isascii() and a.id.replace('-', '').isalnum()
    record = root / 'operators/archive-selection' / a.id; record.mkdir(parents=True, exist_ok=False)
    output = root / 'cache/publication-archives' / a.id; output.mkdir(parents=True, exist_ok=False)
    started, kernel = time.time(), time.clock_gettime(time.CLOCK_MONOTONIC)
    try:
        assert a.prepared.is_absolute() and a.prepared.is_relative_to(root / 'operators/archive-selection')
        assert sha(a.prepared) == a.prepared_sha256
        prior = json.loads(a.prepared.read_text()); entry = json.loads(Path(prior['entry']['path']).read_text())
        assert sha(Path(prior['entry']['path'])) == prior['entry']['sha256']
        assert entry['kind'] == 'explicit-closed-synthetic-fixture-archive-entry'
        assert all('/cache/business/' not in raw and any(part.startswith(('synthetic', 'attempt-')) for part in Path(raw).parts)
                   for raw in entry['selection'])
        old_spec = Path(prior['spec']['path']); assert sha(old_spec) == prior['spec']['sha256']
        value = json.loads(old_spec.read_text()); changed = 0
        for row in value['files']:
            old = row['logical_path']; name = Path(row['path']).name
            if PurePosixPath(old).name != name:
                row['logical_path'] = str(PurePosixPath(old) / name); changed += 1
        assert changed
        spec = output / 'SPEC.json'; save(spec, value)
        code = root / 'publication-tools/archive.py'; assert sha(code) == ARCHIVE_SHA
        save(record / 'ENTRY.json', {'version': 1, 'kind': 'synthetic-archive-logical-leaf-binding-correction',
             'started_at_unix': started, 'started_at_clock_gettime': kernel,
             'prior_prepared': ref(a.prepared), 'original_spec': ref(old_spec), 'corrected_spec': ref(spec),
             'changed_logical_leaves': changed, 'all_original_source_roots_paths_hashes_sizes_modes_preserved': True,
             'archiver': ref(code), 'source': ref(Path(__file__).resolve()),
             'scope': 'No second data selection or source transformation. Original rejected spec/raw metadata and complete source hashes remain retained. Logical leaf correction only, no SDK or actual business evidence.'})
        module_spec = importlib.util.spec_from_file_location('frozen_archive_name_binding', code)
        archive = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(archive)
        result = archive.pack(spec, output / 'archive', 64)
        verified = archive.verify(output / 'archive', sha(output / 'archive/INDEX.json'))
        save(record / 'PACKED.json', {'version': 1, 'entry': ref(record / 'ENTRY.json'),
             'archive': str(output / 'archive'), 'index': ref(output / 'archive/INDEX.json'),
             'result': result, 'verified': verified, 'finished_at_unix': time.time(),
             'wall_seconds': time.clock_gettime(time.CLOCK_MONOTONIC) - kernel,
             'actual_business_or_native_or_grade_access': False, 'cleaned': False})
        print(json.dumps({'status': verified['status'], 'record': str(record),
                          'index_sha256': sha(output / 'archive/INDEX.json')}))
    except BaseException as error:
        save(record / 'FAILED.json', {'version': 1, 'error': {'type': type(error).__name__, 'message': str(error)},
             'traceback': traceback.format_exc(), 'started_at_unix': started, 'finished_at_unix': time.time(),
             'wall_seconds': time.clock_gettime(time.CLOCK_MONOTONIC) - kernel, 'cleaned': False})
        raise


if __name__ == '__main__': main()
