"""Exact semantic claim-to-row annotations; never changes sealed grades.

The explicit map below is the independent manual matching judgment. All remaining
original findings and related observations remain in the full claim inventory.
"""
import sys
sys.dont_write_bytecode = True
import json, hashlib, importlib.util, datetime, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE.parents[3]
REPO = R.parents[1]
CONVENTIONS = R / 'design/private/evaluator-prep/report-conventions'
spec = importlib.util.spec_from_file_location('frozen_exact_rows', CONVENTIONS / 'exact_rows.py')
exact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exact)

def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path): return {'path': str(path.relative_to(REPO)), 'sha256': sha(path)}
def write(path, value):
    assert not (path.parent / 'SEAL.json').exists(), path
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

MAP = {
    'sample-716d41': {
        'WR4-01': [('ios/C04/initial/style.color.submit.fill', 'The claim specifies the disabled submit interior surface RGB in this exact initial state; this is the frozen submit-fill pixel comparison.')],
        'WR4-02': [('ios/C04/initial/style.color.submit.foreground', 'The claim specifies the disabled submit glyph-core RGB in this exact initial state; this is the frozen submit-foreground pixel comparison.')],
        'WR4-03': [('ios/C04/initial/style.color.selected.fill', 'The claim specifies the selected drip control interior RGB in this exact initial state; the selected-fill target is waterRound.method.drip.')],
        'WR4-06': [('android/C02/a03/consent.text', 'The claim specifies the complete observable consent label at the caller-replaced a03 checkpoint. The frozen native-text row compares precisely this label, including absence of a decorative checkmark. The review category is retained; the frozen row has the runtime-business denominator.')],
        'WR4-07': [('android/C03/a03/consent.text', 'The claim separately specifies the complete observable consent label at C03 caller-replaced a03. It is the exact frozen native-text row for the 8 L label, not an inferred repetition from C02.')],
    },
    'sample-e318ec': {
        'R001': [('ios/C04/initial/style.color.submit.fill', 'The claim explicitly identifies the disabled submit surface RGB in C04 initial; the same opaque interior is compared by the frozen submit-fill pixel row.')],
        'R002': [('ios/C04/initial/style.color.submit.foreground', 'The claim explicitly identifies disabled submit glyph-core RGB in C04 initial; this is the frozen submit-foreground pixel row.')],
        'R003': [('ios/C04/initial/style.color.selected.fill', 'The claim explicitly identifies the selected drip surface RGB in C04 initial; the selected-fill row has this exact target and palette token.')],
        'R005': [('ios/C04/initial/style.color.selected.border', 'The claim explicitly identifies selected drip border RGB in C04 initial; this is the selected-border pixel row, independently of its root-cause hypothesis.')],
        'R007': [('ios/C04/initial/style.color.unselected.border', 'The claim explicitly identifies unselected soak border RGB in C04 initial; this is the unselected-border pixel row with the exact soak target.')],
    },
}
UNMAPPED_FOREGROUND = ('No frozen D0 atomic pixel row compares method-name or method-rate foreground color for this target. The frozen method typography rows compare runtime font attributes, and selected/unselected fill/border rows compare other parts. A title foreground row has a different target. No such row is substituted and no new row is created.')
UNMAPPED_BIDI = ('No frozen D0 atomic visual row asserts intra-string bidirectional ordering of fixed English glyph runs, number/unit order, or punctuation. layout.direction asserts leading/trailing alignment, method indicator/summary arrangement and preserved vertical order; native text/accessible-label rows compare semantic strings. Neither is the same as this pixel glyph-order claim. No correlated or broader row is inferred.')
UNRESOLVED = {
    'sample-716d41': {'WR4-04': UNMAPPED_FOREGROUND, 'WR4-05': UNMAPPED_BIDI},
    'sample-e318ec': {**{k: UNMAPPED_FOREGROUND for k in ['R004', 'R006', 'R008', 'R009']}, **{k: UNMAPPED_BIDI for k in ['R010', 'R011', 'R012']}},
}

def citation(path, value, after=0):
    raw = path.read_text()
    literal = json.dumps(value, ensure_ascii=False)[1:-1]
    start = raw.index(literal, after)
    end = start + len(literal)
    quote = raw[start:end]
    out = {'artifact': ref(path), 'range_type': 'utf8_bytes',
           'start': len(raw[:start].encode('utf-8')), 'end': len(raw[:end].encode('utf-8'))}
    assert path.read_bytes()[out['start']:out['end']].decode('utf-8') == quote
    return quote, out

def main():
    delivery = read(R / 'private/grade-deliveries/selfreview.json')
    plan = read(R / 'design/private/evaluator-prep/normalized-d0.json')
    required = {row['key']: row for row in plan['rows']}
    for capsule in delivery['capsules']:
        aid = capsule['anonymous_id']
        cap = R / capsule['capsule']
        seal = cap / 'SEAL.json'
        assert sha(seal) == capsule['sealSHA256']
        original_seal = read(seal)
        for rel, digest in original_seal['files'].items(): assert sha(cap / rel) == digest, rel
        review_path = cap / 'review.json'
        review = read(review_path)
        provenance = read(cap / 'projection-provenance.json')
        assert sha(review_path) == provenance['projectedReviewSHA256']
        findings = review['findings']
        assert len(findings) == provenance['allFindingsPreserved']
        assert len({f['id'] for f in findings}) == len(findings)
        d0_path = R / 'design/private/evaluation/d0' / aid / 'grade.json'
        final_path = R / 'design/private/evaluation/final' / aid / 'grade.json'
        d0, final = read(d0_path), read(final_path)
        assert len(d0['rows']) == 3185 and len(final['rows']) == 4843
        d0_rows, final_rows = exact.align(d0, final, allow_right_extra=True)
        assert set(d0_rows) == set(plan['required_keys'])
        # The self-review must refer to the same D0 production implementation.
        d0_cap = R / 'private/grade-capsules/d0' / aid
        own_source_comparisons = []
        for rel in ['source/alerttoast/Sources/AlertToast/WaterRound.swift', 'source/reply/Reply/app/src/main/java/com/example/reply/ui/waterround/WaterRound.kt']:
            assert sha(cap / 'own' / rel) == sha(d0_cap / rel)
            own_source_comparisons.append({'own': ref(cap / 'own' / rel), 'sealed_d0': ref(d0_cap / rel)})
        matches, inventory = [], []
        raw = review_path.read_text()
        for i, finding in enumerate(findings):
            cid = finding['id']
            after = raw.index(json.dumps(cid, ensure_ascii=False))
            quote, cite = citation(review_path, finding['claim'], after)
            uncertain = finding['certainty'] != 'confirmed'
            mappings = MAP[aid].get(cid, [])
            item = {'claim_id': cid, 'original_pointer': '/findings/' + str(i),
                    'original_finding': finding, 'claim_quote': quote, 'review_citation': cite,
                    'mapping_status': 'uncertain' if uncertain else 'mapped' if mappings else 'unmapped',
                    'mapped_rows': [], 'related_rows': [], 'duplicate_of': None}
            if uncertain:
                assert cid == 'U001'
                item['reason'] = ('The original explicitly does not assert clipped glyphs or a confirmed defect. It reports a native overflow flag and says the complete string appears visible. It is retained as uncertain, not passed to the helper as a problem claim and not counted as a false positive.')
                item['related_rows'] = [{'row_key': 'android/C01/initial/layout.noTextTruncation', 'relation': 'Related visible-clipping criterion only; the original does not claim that this criterion fails.'}]
            elif mappings:
                for key, reason in mappings:
                    assert key in required and required[key]['platform'] == finding['platform'] and required[key]['caseId'] == finding['case']
                    match = {'claim_id': cid, 'row_key': key, 'quote': quote, 'reason': reason, 'review_citation': cite}
                    matches.append(match)
                    item['mapped_rows'].append({'row_key': key, 'reason': reason})
            else:
                assert cid in UNRESOLVED[aid], cid
                item['reason'] = UNRESOLVED[aid][cid]
            inventory.append(item)
        # Related observations are retained separately, with original IDs only.
        related = []
        if aid == 'sample-716d41':
            explicit = [
                (0, 0, [('WR4-01', 'ios/C02/initial/style.color.submit.fill', 'This occurrence explicitly reports the submit background RGB in C02 initial, and is linked to original surface claim WR4-01.'),
                         ('WR4-02', 'ios/C02/initial/style.color.submit.foreground', 'This same occurrence separately explicitly reports flat glyph-interior RGB in C02 initial; it is linked to original label claim WR4-02 rather than inferred from the fade hypothesis.')]),
                (0, 1, [('WR4-01', 'ios/C04/a03/style.color.submit.fill', 'This occurrence explicitly has aspect disabled_surface_color, the submit target and C04 a03. It maps only that surface facet; no label/method facets are inferred from the shared palette or cause.')]),
                (1, 0, []),
            ]
            for cluster_index, occurrence_index, mapping in explicit:
                cluster = review['related_clusters'][cluster_index]
                occurrence = cluster['related_observed_occurrences'][occurrence_index]
                quote, cite = citation(review_path, occurrence['observed'])
                entry = {'original_pointer': f'/related_clusters/{cluster_index}/related_observed_occurrences/{occurrence_index}',
                         'linked_original_claim_ids': cluster['findings'], 'original_occurrence': occurrence,
                         'quote': quote, 'review_citation': cite, 'mapped_rows': []}
                for cid, key, reason in mapping:
                    assert key in required and cid in cluster['findings']
                    matches.append({'claim_id': cid, 'row_key': key, 'quote': quote, 'reason': reason, 'review_citation': cite})
                    entry['mapped_rows'].append({'claim_id': cid, 'row_key': key, 'reason': reason})
                if not mapping: entry['reason'] = UNMAPPED_BIDI
                related.append(entry)
        else:
            for ci, cluster in enumerate(review['related_clusters']):
                for oi, occurrence in enumerate(cluster.get('related_observed_recurrences', [])):
                    quote, cite = citation(review_path, occurrence)
                    related.append({'original_pointer': f'/related_clusters/{ci}/related_observed_recurrences/{oi}',
                                    'linked_original_claim_ids': cluster['findings'], 'original_occurrence': occurrence,
                                    'quote': quote, 'review_citation': cite, 'mapped_rows': [],
                                    'reason': 'This recurrence note names only a state/image (and disabled release for one occurrence); it does not independently specify which color facets were observed there. The root-cause cluster is not expanded into new exact-row detections.'})
        matching_input = {'version': 1, 'anonymous_id': aid, 'd0_report': ref(d0_path), 'final_report': ref(final_path),
                          'original_review': ref(review_path), 'observed_problem_matches': matches}
        result = exact.review_match(d0, final, matches)
        assessments = []
        for item in inventory:
            mapped = [m for m in result['matches'] if m['claim_id'] == item['claim_id']]
            states = sorted({m['match_state'] for m in mapped})
            status = ('uncertain_original_observation' if item['mapping_status'] == 'uncertain' else
                      'undetermined_no_exact_row' if not mapped else
                      'confirmed_on_mapped_D0_row' if any(m['d0_outcome'] == 'F' for m in mapped) else
                      'contradicted_on_assessed_mapped_D0_row' if any(m['d0_outcome'] == 'P' for m in mapped) else
                      'undetermined_D0_unassessed')
            assessments.append({'claim_id': item['claim_id'], 'original_certainty': item['original_finding']['certainty'],
                                'status': status, 'mapped_match_states': states,
                                'row_keys': sorted({m['row_key'] for m in mapped}),
                                'false_positive_assessable': status in ['confirmed_on_mapped_D0_row', 'contradicted_on_assessed_mapped_D0_row'],
                                'false_positive': status == 'contradicted_on_assessed_mapped_D0_row'})
        output = HERE / aid
        output.mkdir(exist_ok=True)
        write(output / 'matching-input.json', matching_input)
        duplicate_occurrences = []
        for pci, pc in enumerate(review.get('typed_checks', {}).get('per_case', [])):
            for fi, failure in enumerate(pc.get('failed', [])):
                assert aid == 'sample-716d41' and pc['platform'] == 'android' and pc['case'] in ['C02', 'C03']
                assert failure[0] == 'cp-a03.full:reserveConsent:label'
                cid = 'WR4-06' if pc['case'] == 'C02' else 'WR4-07'
                key = f'android/{pc["case"]}/a03/consent.text'
                assert any(m['claim_id'] == cid and m['row_key'] == key for m in matches)
                duplicate_occurrences.append({'original_pointer': f'/typed_checks/per_case/{pci}/failed/{fi}',
                                              'original_occurrence': failure, 'claim_id': cid, 'row_key': key,
                                              'reason': 'This explicit typed-check failure repeats the same observable-label claim already retained under its original finding ID. It is preserved as a duplicate occurrence and does not create a second identical claim-row helper mapping.'})
        claim_inventory = {'version': 1, 'anonymous_id': aid, 'original_review': ref(review_path),
                           'findings': inventory, 'related_observations': related,
                           'original_related_clusters': review.get('related_clusters', []),
                           'original_duplicates': review.get('duplicates', []),
                           'duplicate_claim_occurrences': duplicate_occurrences,
                           'review_scope_notes': {key: review[key] for key in ['checked_scope', 'unassessed_scope', 'review_limits', 'summary', 'typed_checks', 'typed_check_reports', 'read_only_attestation'] if key in review},
                           'accounting_rule': 'Every original finding is retained exactly once with original ID and semantic values. Related occurrences are explicit original observations only. Uncertain or unmapped claims are never silently discarded or classified as false positives. Detection arithmetic deduplicates exact frozen row keys; root-cause clustering is not a row multiplier.'}
        assert {x['claim_id'] for x in inventory} == {x['id'] for x in findings}
        assert [x['original_finding'] for x in inventory] == findings
        write(output / 'claim-inventory.json', claim_inventory)
        result.update({'phase': 'selfreview', 'matching_input': ref(output / 'matching-input.json'),
                       'claim_inventory': ref(output / 'claim-inventory.json'),
                       'input_commitments': {'d0_grade': ref(d0_path), 'final_grade': ref(final_path), 'original_review': ref(review_path),
                                             'original_capsule_seal': ref(seal), 'projection_provenance': ref(cap / 'projection-provenance.json')},
                       'claim_assessments': assessments,
                       'claim_status_counts': dict(collections.Counter(x['status'] for x in assessments)),
                       'limitations': 'Frozen grades remain unchanged. Unmapped color/glyph-order details have no comparable exact atomic grade; U is not a false positive. An uncertain non-defect observation is retained separately. No holdout key is matched and no detection is multiplied by a root-cause inference.'})
        write(output / 'matching.json', result)
        write(output / 'verification.json', {'anonymous_id': aid, 'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                            'original_capsule_files_verified': len(original_seal['files']),
                                            'original_review_sha256': sha(review_path), 'original_findings_equal_inventory': True,
                                            'all_main_claims_accounted_for': True, 'all_related_occurrences_retained': True,
                                            'citations_verified': True, 'same_d0_production_sources': own_source_comparisons,
                                            'helper': ref(CONVENTIONS / 'exact_rows.py'), 'no_grade_changes': True})
        print(json.dumps({'anonymous_id': aid, 'matching_path': str((output / 'matching.json').relative_to(REPO)), 'matching_sha256': sha(output / 'matching.json'), 'completed': True}))

if __name__ == '__main__': main()
