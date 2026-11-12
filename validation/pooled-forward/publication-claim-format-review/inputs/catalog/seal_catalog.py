#!/usr/bin/env python3
"""One-time seal of only this new output directory; no projector or grading."""
from pathlib import Path
import hashlib
import json
import stat

HERE = Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    target = HERE / 'SEAL.json'
    if target.exists():
        raise ValueError('A sealed catalog cannot be overwritten')
    inspection = json.loads((HERE / 'INSPECTION.json').read_bytes())
    validation = json.loads((HERE / 'VALIDATION.json').read_bytes())
    catalog = json.loads((HERE / 'CATALOG.json').read_bytes())
    if not validation['passed'] or validation['documents'] != 10 or catalog['coverage_counts']['cataloged_locations'] != validation['cataloged_locations']:
        raise ValueError('Complete validated all-ten catalog required')
    input_refs = [inspection['survey_ref']] + inspection['reference_source_refs'] + [doc['original_ref'] for doc in inspection['documents']]
    for ref in input_refs:
        if sha(Path(ref['path']).read_bytes()) != ref['sha256']:
            raise ValueError('Original or authorized process input changed before seal')
    files = sorted(path for path in HERE.rglob('*') if path.is_file())
    if len(files) + 1 > 100 or any(path.is_symlink() for path in HERE.rglob('*')):
        raise ValueError('Output file limit or no-symlink constraint failed')
    manifest = [{'path': str(path), 'sha256': sha(path.read_bytes()),
                 'size_bytes': path.stat().st_size, 'sealed_mode': '0444'} for path in files]
    seal = {
        'version': 1, 'kind': 'independent-selfclaim-format-responsibility-catalog-seal',
        'scope': 'Disclosure-format responsibility DATA only; no actual-material projection, product findings, grade, comparison or dispatch.',
        'independent_review_required_before_use': True,
        'sealed_output_directory': str(HERE), 'sealed_directory_mode': '0555',
        'output_file_count_including_seal': len(files) + 1,
        'input_refs': input_refs, 'artifact_manifest': manifest,
        'coverage_counts': catalog['coverage_counts'],
        'all_original_inputs_reverified_unchanged': True,
        'cataloged_references_validated': False, 'no_projection_or_dispatch_performed': True,
        'self_digest': 'External SHA256 of these exact SEAL.json bytes is returned separately to the coordinating agent; self-reference is excluded from the artifact manifest.'
    }
    raw = (json.dumps(seal, ensure_ascii=False, indent=2) + '\n').encode()
    target.write_bytes(raw)
    for path in files + [target]:
        path.chmod(0o444)
    for directory in sorted((path for path in HERE.rglob('*') if path.is_dir()), reverse=True):
        directory.chmod(0o555)
    HERE.chmod(0o555)
    readonly = all(stat.S_IMODE(path.stat().st_mode) == 0o444 for path in files + [target]) and stat.S_IMODE(HERE.stat().st_mode) == 0o555
    if not readonly or sha(target.read_bytes()) != sha(raw):
        raise ValueError('Read-only seal verification failed')
    print(json.dumps({'seal_path': str(target), 'seal_sha256': sha(raw), 'files': len(files) + 1, 'readonly_verified': readonly, 'coverage_counts': catalog['coverage_counts']}))


if __name__ == '__main__':
    main()
