"""Authenticate independent disclosure responsibility data before actual use.

This operator step never opens a referenced claim target, judges a proposition,
or grants native/source/image evidence credit.
"""
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
C = ROOT / 'operators/cohort2/coordination'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ref(path):
    path = path.resolve()
    return {'path': str(path), 'sha256': sha(path.read_bytes())}


def read_pinned(path, digest):
    assert path.is_file() and not path.is_symlink()
    raw = path.read_bytes()
    assert sha(raw) == digest, str(path)
    return json.loads(raw)


def verify_manifest(path, digest):
    data = read_pinned(path, digest)
    for entry in data['artifact_manifest']:
        p = Path(entry['path'])
        assert not p.is_symlink() and p.is_file()
        raw = p.read_bytes()
        assert sha(raw) == entry['sha256'] and len(raw) == entry['size_bytes']
        assert os.stat(p).st_mode & 0o222 == 0
    return data


def main():
    cat_seal = ROOT / 'publication-claim-format-catalog/SEAL.json'
    approval_seal = ROOT / 'publication-claim-format-review/SEAL.json'
    cat_seal_sha = 'd2e42ebceecc9949751a6df1497d36ae9d5730a48deaf30095d4ee633c7c5695'
    approval_seal_sha = '9ea9f8bb968a677c09a33581a1645524046a0f566c71fa415955b3d20a5dd764'
    cat_env = verify_manifest(cat_seal, cat_seal_sha)
    app_env = verify_manifest(approval_seal, approval_seal_sha)
    catalog_path = ROOT / 'publication-claim-format-catalog/CATALOG.json'
    catalog_ref = ref(catalog_path)
    assert catalog_ref['sha256'] == '60c2b7544b469c7731ab615512d20a537b489d9b439ece3546908ac6cc559e6f'
    approval_path = ROOT / 'publication-claim-format-review/APPROVAL.json'
    approval = read_pinned(approval_path, '8c4d9cd820e938f1b2e28248dd16e1f8e22bdd43b075459de6e36637bf6234b7')
    assert app_env['approval_ref'] == ref(approval_path)
    assert approval['catalog_ref'] == catalog_ref and approval['catalog_seal'] == ref(cat_seal)
    assert approval['all_originals_reverified_unchanged'] is True
    assert approval['unapproved_locations'] == []
    catalog = json.loads(catalog_path.read_text())
    originals = [d['original_ref'] for d in catalog['documents']]
    assert len(originals) == 10 and len({r['path'] for r in originals}) == 10
    assert originals == approval['original_document_refs']
    for original in originals:
        assert ref(Path(original['path'])) == original
    locations = []
    for document in catalog['documents']:
        for location in document['locations']:
            assert location['original_ref'] == document['original_ref']
            raw = json.dumps(location, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
            locations.append({'original_ref': document['original_ref'], 'pointer': location['pointer'],
                              'member_kind': location['member_kind'], 'location_sha256': sha(raw)})
    assert len(locations) == 271
    canon = lambda row: json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    assert sorted(map(canon, locations)) == sorted(map(canon, approval['approved_locations']))
    lens = ROOT / 'claim-metadata-lens-v1/lens.py'
    lens_freeze = ROOT / 'claim-metadata-lens-v1/AUTHOR-FREEZE.json'
    read_pinned(lens_freeze, '91c59ca7c925c09a2e4fef326ab4f88672715317d3f23f7c1b1f4908e5c90f0a')
    authority = {
        'version': 1, 'kind': 'externally-pinned-worker-metadata-disclosure-authority',
        'original_root': str(ROOT), 'catalog_seal': ref(cat_seal), 'catalog_ref': catalog_ref,
        'approval_seal': ref(approval_seal), 'approval_ref': ref(approval_path),
        'original_document_refs': originals, 'lens_ref': ref(lens), 'lens_author_freeze': ref(lens_freeze),
        'reference_validated': False, 'evidence_credit': False, 'quality_credit': False,
        'scope': 'Disclosure metadata only; no fact edits, target validation or product/treatment credit.'}
    out = C / 'WORKER-METADATA-AUTHORITY-v1.json'
    raw = (json.dumps(authority, indent=2, sort_keys=True) + '\n').encode()
    with out.open('xb') as stream: stream.write(raw)
    out.chmod(0o444)
    print(json.dumps({'authority': ref(out), 'original_documents': len(originals),
                      'independently_approved_locations': len(locations),
                      'all_originals_reverified': True, 'target_access': False,
                      'quality_credit': False}))


if __name__ == '__main__': main()
