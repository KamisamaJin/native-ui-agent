#!/usr/bin/env python3
"""Retain the closed v2 positive run before source-driven layout admission."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

root = Path(__file__).resolve().parent.parent
prefixes = ['fixtures/rich', 'results/v2', 'revision-v2', 'controls']
members = sorted({p for name in prefixes for p in (root / name).rglob('*') if p.is_file() and not p.is_symlink()})
pins = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in members}
archive = root / 'DEVELOPMENT-CANDIDATE2.tar.gz'
with tarfile.open(archive, 'x:gz') as out:
    for path in members: out.add(path, arcname=path.relative_to(root).as_posix(), recursive=False)
with tarfile.open(archive, 'r:gz') as source:
    assert {entry.name for entry in source.getmembers()} == set(pins)
    for entry in source.getmembers():
        assert entry.isfile() and hashlib.sha256(source.extractfile(entry).read()).hexdigest() == pins[entry.name]
(root / 'DEVELOPMENT-CANDIDATE2.json').write_text(json.dumps({'version': 1,
    'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'members_sha256': pins,
    'scope': 'Closed synthetic v2 positive and source snapshots retained; known frozen artifact layout requires explicit subsequent admission.',
    'removed_live_namespaces_after_verified_archive': ['fixtures/rich', 'results/v2']}, indent=2, sort_keys=True) + '\n')
for name in ['fixtures/rich', 'results/v2']: shutil.rmtree(root / name)
print(json.dumps({'members_verified': len(pins), 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}))
