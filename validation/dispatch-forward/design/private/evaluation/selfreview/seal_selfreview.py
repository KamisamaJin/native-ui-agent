"""Seal both self-review joins after exact helper and original-byte validation."""
import sys
sys.dont_write_bytecode = True
import json, hashlib, datetime, importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
R = HERE.parents[3]
REPO = R.parents[1]
CONVENTIONS = R / 'design/private/evaluator-prep/report-conventions'
ACTIVE = 'af39b8846cf1da53d777f9f031b00a61661dd4fbc336d55214af1db4c9119d55'
CONVENTION = 'a1d7c014b70422b75ab60278cf9799440982a14524d6cfde1982bad00fa71c1f'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
def ref(p, base): return {'path': str(p.relative_to(base)), 'sha256': sha(p)}
def verify_ref(value):
    p = REPO / value['path']
    assert sha(p) == value['sha256'], value['path']
    return p
def verify_phase_seal(p):
    v = read(p)
    assert hashlib.sha256(canonical(v['payload']).encode()).hexdigest() == v['commitment_sha256']
    for f in v['payload']['files']: assert sha(p.parent / f['path']) == f['sha256'], f['path']
    for f in v['payload']['inputs']: verify_ref(f)
    return v
def verify_quote(quote, cite):
    path = verify_ref(cite['artifact'])
    if cite['range_type'] == 'utf8_bytes': actual = path.read_bytes()[cite['start']:cite['end']].decode('utf-8')
    else: actual = '\n'.join(path.read_text().splitlines()[cite['start']-1:cite['end']])
    assert actual == quote

spec = importlib.util.spec_from_file_location('sealed_exact_rows', CONVENTIONS / 'exact_rows.py')
exact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exact)
convention_seal = read(CONVENTIONS / 'CONVENTIONS-SEAL.json')
assert convention_seal['commitment_sha256'] == CONVENTION
assert hashlib.sha256(canonical(convention_seal['payload']).encode()).hexdigest() == CONVENTION
for f in convention_seal['payload']['files']: assert sha(CONVENTIONS / f['path']) == f['sha256']
delivery_path = R / 'private/grade-deliveries/selfreview.json'
delivery = read(delivery_path)
for capsule in delivery['capsules']:
    aid = capsule['anonymous_id']
    out = HERE / aid
    cap = R / capsule['capsule']
    assert sha(cap / 'SEAL.json') == capsule['sealSHA256']
    for rel, digest in read(cap / 'SEAL.json')['files'].items(): assert sha(cap / rel) == digest, rel
    for phase in ['d0', 'final']: verify_phase_seal(R / 'design/private/evaluation' / phase / aid / 'SEAL.json')
    data = read(out / 'matching-input.json')
    assert data['anonymous_id'] == aid
    assert set(data) == {'version', 'anonymous_id', 'd0_report', 'final_report', 'original_review', 'observed_problem_matches'}
    d0_path, final_path, review_path = [verify_ref(data[k]) for k in ['d0_report', 'final_report', 'original_review']]
    review = read(review_path)
    match_ids = {f['id'] for f in review['findings']}
    for match in data['observed_problem_matches']:
        assert match['claim_id'] in match_ids
        verify_quote(match['quote'], match['review_citation'])
    expected = exact.review_match(read(d0_path), read(final_path), data['observed_problem_matches'])
    actual = read(out / 'matching.json')
    assert {k: actual[k] for k in expected} == expected
    verify_ref(actual['matching_input'])
    inventory_path = verify_ref(actual['claim_inventory'])
    inventory = read(inventory_path)
    assert [i['original_finding'] for i in inventory['findings']] == review['findings']
    assert [i['claim_id'] for i in inventory['findings']] == [f['id'] for f in review['findings']]
    assert inventory['original_related_clusters'] == review.get('related_clusters', [])
    assert inventory['original_duplicates'] == review.get('duplicates', [])
    for item in inventory['findings']: verify_quote(item['claim_quote'], item['review_citation'])
    for item in inventory['related_observations']: verify_quote(item['quote'], item['review_citation'])
    original_related_count = sum(len(c.get('related_observed_occurrences', [])) + len(c.get('related_observed_recurrences', [])) for c in review.get('related_clusters', []))
    assert len(inventory['related_observations']) == original_related_count
    failed_count = sum(len(pc.get('failed', [])) for pc in review.get('typed_checks', {}).get('per_case', []))
    assert len(inventory['duplicate_claim_occurrences']) == failed_count
    for item in inventory['duplicate_claim_occurrences']:
        assert item['claim_id'] in match_ids
        assert any(m['claim_id'] == item['claim_id'] and m['row_key'] == item['row_key'] for m in actual['matches'])
    inputs = [delivery_path, cap / 'SEAL.json', cap / 'projection-provenance.json', cap / 'review.json', cap / 'own/capsule-seal.json', cap / 'own/manifest.json',
              d0_path, final_path, out / 'matching-input.json', out / 'claim-inventory.json',
              R / 'design/private/evaluation/d0' / aid / 'SEAL.json', R / 'design/private/evaluation/final' / aid / 'SEAL.json',
              R / 'private/grade-capsules/d0' / aid / 'capsule-seal.json', R / 'private/grade-capsules/final' / aid / 'capsule-seal.json',
              R / 'evaluator-v3-commitment.json', R / 'matching-conventions-commitment.json',
              R / 'design/private/evaluator-prep/v3/V3-SEAL.json', R / 'design/private/evaluator-prep/normalized-d0.json', R / 'design/private/evaluator-prep/normalized-final.json']
    inputs += [p for p in CONVENTIONS.iterdir() if p.is_file()]
    inputs += [p for p in HERE.iterdir() if p.is_file()]
    for finding in review['findings']:
        for evidence in finding.get('evidence', []):
            p = cap / evidence['path']
            assert sha(p) == evidence['sha256']
            inputs.append(p)
    inputs = sorted(set(inputs))
    output_files = sorted(p for p in out.iterdir() if p.is_file() and p.name != 'SEAL.json')
    payload = {'phase': 'selfreview', 'anonymous_id': aid, 'sealed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'active_evaluator_commitment': ACTIVE, 'report_conventions_commitment': CONVENTION,
               'files': [ref(p, out) for p in output_files], 'inputs': [ref(p, REPO) for p in inputs],
               'matching_input_sha256': sha(out / 'matching-input.json'), 'original_selfreview_capsule_seal_sha256': sha(cap / 'SEAL.json'),
               'all_original_claims_accounted_for': True, 'd0_final_grade_changes': False,
               'later_paired_or_assignment_material_opened': False}
    result = {'commitment_sha256': hashlib.sha256(canonical(payload).encode()).hexdigest(), 'payload': payload}
    dest = out / 'SEAL.json'
    assert not dest.exists()
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'anonymous_id': aid, 'matching_path': str((out / 'matching.json').relative_to(REPO)), 'matching_sha256': sha(out / 'matching.json'),
                      'seal_path': str(dest.relative_to(REPO)), 'seal_sha256': sha(dest), 'commitment_sha256': result['commitment_sha256'], 'completed': True}))
