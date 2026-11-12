"""Preserve terminal evidence not already byte-identical in a closed transport.

No product judgment, original-path rewriting or recursive transport inclusion.
Regular original keys keep their bytes and mode; links/specials stay inert.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'operators/terminal-preservation-v1'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def save(name, value):
    with (OUT / name).open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2)
        f.write('\n')


def main():
    assert not OUT.exists()
    closure = ROOT / 'operators/final-meter-closure-v1/CLOSED.json'
    assert json.loads(closure.read_text())['status'] == 'closed'
    covered, raw_shards, bases = {}, {}, []
    for cold in sorted((ROOT / 'publications').iterdir()):
        if not cold.is_dir():
            continue
        transport = json.loads((cold / 'TRANSPORT.json').read_text())
        spec_member = transport['files']['SPEC.json']
        raw = gzip.decompress((cold / spec_member['stored']).read_bytes())
        assert len(raw) == spec_member['bytes'] and hashlib.sha256(raw).hexdigest() == spec_member['sha256']
        spec = json.loads(raw)
        for row in spec['files']:
            covered.setdefault(row['path'], set()).add((row['sha256'], row['bytes'], row['mode']))
        for name, row in transport['files'].items():
            if name.startswith('shard-'):
                raw_shards[(row['sha256'], row['bytes'])] = str(cold / row['stored'])
        bases.append({'path': str(cold / 'TRANSPORT.json'), 'sha256': sha(cold / 'TRANSPORT.json')})
    rows, structures, exclusions = [], [], []
    skipped_existing = 0
    for directory, dirs, files in os.walk(ROOT, followlinks=False):
        parent = Path(directory)
        for name in list(dirs):
            p = parent / name
            if p.is_symlink():
                structures.append({'path': str(p), 'kind': 'symlink', 'target': os.readlink(p)})
                dirs.remove(name)
            elif p == ROOT / 'publications' or name in {'.git', '__pycache__'}:
                exclusions.append({'path': str(p), 'reason': 'No recursive cold transport/Git or regenerable Python bytecode'})
                dirs.remove(name)
        # The two small tool-validation venvs contain only regenerated packages.
        if parent == ROOT / 'cache':
            for name in ['design-schema-python', 'skill-validation-python']:
                if name in dirs:
                    exclusions.append({'path': str(parent / name), 'reason': 'Regenerable validation interpreter packages; commands and results retained'})
                    dirs.remove(name)
        for name in files:
            p = parent / name
            st = p.lstat()
            if stat.S_ISLNK(st.st_mode):
                structures.append({'path': str(p), 'kind': 'symlink', 'target': os.readlink(p)})
                continue
            if not stat.S_ISREG(st.st_mode):
                structures.append({'path': str(p), 'kind': 'special', 'file_type': stat.S_IFMT(st.st_mode), 'mode': stat.S_IMODE(st.st_mode)})
                continue
            digest = sha(p)
            mode = format(stat.S_IMODE(st.st_mode), '04o')
            if (digest, st.st_size, mode) in covered.get(str(p), set()):
                skipped_existing += 1
                continue
            if p.is_relative_to(ROOT / 'cache/publication-archives') and (digest, st.st_size) in raw_shards:
                exclusions.append({'path': str(p), 'sha256': digest, 'bytes': st.st_size,
                    'reason': 'Exact verified derived raw transport duplicate', 'retained_cold': raw_shards[(digest, st.st_size)]})
                continue
            assert p.lstat().st_ino == st.st_ino and p.lstat().st_size == st.st_size and p.lstat().st_mtime_ns == st.st_mtime_ns
            rows.append({'root': 'study', 'path': str(p), 'logical_path': 'terminal/' + p.relative_to(ROOT).as_posix(),
                         'sha256': digest, 'bytes': st.st_size, 'mode': mode})
    repo = ROOT.parents[1]
    for rel in ['.github/workflows/test.yml', '.github/workflows/pooled-runtime-preflight.yml', '.gitignore', 'README.md', 'THIRD_PARTY_NOTICES.md']:
        p = repo / rel
        rows.append({'root': 'repository', 'path': str(p), 'logical_path': 'repository/' + rel,
                     'sha256': sha(p), 'bytes': p.stat().st_size, 'mode': format(stat.S_IMODE(p.stat().st_mode), '04o')})
    OUT.mkdir()
    save('SPEC.json', {'version': 1, 'roots': [{'id': 'study', 'kind': 'evidence', 'path': str(ROOT)},
        {'id': 'repository', 'kind': 'evidence', 'path': str(repo)}], 'files': rows})
    save('STRUCTURE.json', {'version': 1, 'entries': structures, 'scope': 'Inert structural metadata only, no targets followed/recreated'})
    save('EXCLUSIONS.json', {'version': 1, 'entries': exclusions, 'unchanged_existing_originals': skipped_existing})
    save('INVENTORY.json', {'version': 1, 'at_unix': time.time(), 'kind': 'terminal-additive-original-byte-preservation',
        'source_sha256': sha(Path(__file__)), 'meter_closure_sha256': sha(closure), 'existing_transports': bases,
        'files': len(rows), 'source_bytes': sum(r['bytes'] for r in rows),
        'pins': {p.name: sha(p) for p in OUT.iterdir()},
        'scope': 'Finite snapshot after original meters and bulk cleanup close, before final scratch disposal. Already preserved exact original-key/hash/size/mode tuples are not duplicated. New/changed original bytes, final streams/maps, controls, failures and receipts are retained; terminal cleanup/publication receipts follow in plain Git. No original status or product grading changed.'})
    print(json.dumps({'files': len(rows), 'source_bytes': sum(r['bytes'] for r in rows), 'already_preserved': skipped_existing, 'structural_members': len(structures)}))


if __name__ == '__main__':
    main()
