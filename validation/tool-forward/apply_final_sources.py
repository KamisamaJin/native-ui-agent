#!/usr/bin/env python3
"""Apply both sealed final source capsules to all fresh hosts before holdouts."""
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

R = Path(__file__).resolve().parent
SUBMISSIONS = ['submission-b2e249', 'submission-4f4364']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    capsules = {s: R / 'implementations/final' / s for s in SUBMISSIONS}
    assert all((p / 'manifest.json').is_file() for p in capsules.values())
    assert not (R / 'private/inputs/final').exists(), 'Apply final sources before revealing holdouts'
    output = R / 'final-source-application.json'
    assert not output.exists(), 'Preserve previous applications, no silent replacement'
    rows = []
    for submission, capsule in capsules.items():
        manifest = json.loads((capsule / 'manifest.json').read_text())
        for slot in ['odd', 'even']:
            workspace = R / 'cache/final-hosts' / submission / slot
            assert (workspace / 'bootstrap.json').is_file()
            applied = {}
            for relative, digest in manifest['files'].items():
                assert relative.startswith(('reply/Reply/app/src/main/', 'alerttoast/Sources/'))
                source = capsule / relative
                target = workspace / relative
                assert target.resolve().is_relative_to(workspace.resolve())
                assert sha(source) == digest
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                assert sha(target) == digest
                applied[relative] = digest
            # A missing upstream file must be represented explicitly, never
            # accidentally revived by applying an incomplete capsule.
            for repo, prefix in [('reply', 'Reply/app/src/main'), ('alerttoast', 'Sources')]:
                deleted = subprocess.check_output(['git', 'diff', '--name-only', '--diff-filter=D', '--', prefix],
                                                  cwd=workspace / repo, text=True).strip()
                assert not deleted, deleted
            rows.append({'submission': submission, 'slot': slot, 'workspace': str(workspace),
                         'source_manifest_sha256': sha(capsule / 'manifest.json'), 'files': applied})
    output.write_text(json.dumps({'applied_at': time.time(), 'hosts': rows,
                                  'scope': 'Byte-for-byte source application only. No business edits, hidden inputs or grading.'}, indent=2) + '\n')
    print(json.dumps({'final_source_hosts': len(rows), 'hidden_inputs_not_yet_created': True}))


if __name__ == '__main__':
    main()
