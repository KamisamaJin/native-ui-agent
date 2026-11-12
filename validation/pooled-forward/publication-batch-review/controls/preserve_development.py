#!/usr/bin/env python3
"""Losslessly retain the closed first synthetic run before reducing duplication.

Only this review's generated fixtures/results are removed after archive verify.
Production sources, snapshots, prior reviews and current source files stay put.
"""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

root = Path(__file__).resolve().parent.parent
archive = root / 'DEVELOPMENT-ROUND1.tar.gz'
members = sorted(p for p in root.rglob('*') if p.is_file() and not p.is_symlink())
pins = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in members}
with tarfile.open(archive, 'x:gz') as out:
    for path in members: out.add(path, arcname=path.relative_to(root).as_posix(), recursive=False)
with tarfile.open(archive, 'r:gz') as source:
    assert {entry.name for entry in source.getmembers()} == set(pins)
    for entry in source.getmembers():
        assert entry.isfile() and hashlib.sha256(source.extractfile(entry).read()).hexdigest() == pins[entry.name]
record = {'version': 1, 'kind': 'retained-closed-synthetic-development-run',
          'observed_original_run_file_count': 2059, 'archive_members_including_preservation_utility': len(pins),
          'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'members_sha256': pins,
          'scope': 'All first-run bytes retained. Two candidate teardown failures were review-generator file-budget failures; functional controls passed. No actual data or earlier freeze cleanup.',
          'removed_live_namespaces_after_verified_archive': ['fixtures', 'results/v1', 'results/v2']}
(root / 'DEVELOPMENT-ROUND1.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
for name in record['removed_live_namespaces_after_verified_archive']:
    target = root / name
    assert target.is_relative_to(root) and not target.is_symlink()
    shutil.rmtree(target)
(root / 'results/RUN-independent.log').rename(root / 'results/RUN-development-round1.log')
print(json.dumps({'archive_members': len(pins), 'archive_sha256': record['archive_sha256'],
                  'all_member_bytes_verified': True, 'live_files_after': sum(1 for p in root.rglob('*') if p.is_file())}))
