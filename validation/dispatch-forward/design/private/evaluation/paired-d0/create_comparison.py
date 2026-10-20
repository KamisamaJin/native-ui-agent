"""Join immutable same-source D0 grades with the frozen exact-row helper."""
import sys
sys.dont_write_bytecode = True
import json, hashlib, importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
R = HERE.parents[3]
REPO = R.parents[1]
P = R / 'design/private/evaluator-prep/report-conventions/exact_rows.py'
spec = importlib.util.spec_from_file_location('frozen_paired_exact_rows', P)
exact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exact)
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path': str(p.relative_to(REPO)), 'sha256': sha(p)}
def write(p, v):
    assert not p.exists(), p
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n')
for aid in ['sample-716d41', 'sample-e318ec']:
    out = HERE / aid
    cap = R / 'private/grade-capsules/paired-d0' / aid
    anchor_cap = R / 'private/grade-capsules/d0' / aid
    anchor_path = R / 'design/private/evaluation/d0' / aid / 'grade.json'
    paired_path = out / 'paired-grade.json'
    anchor, paired = read(anchor_path), read(paired_path)
    assert len(anchor['rows']) == len(paired['rows']) == 3185
    identities = [read(c / 'source-identity.json') for c in [anchor_cap, cap]]
    commitments = [i['sourceFilesCommitment'] for i in identities]
    for c, identity in zip([anchor_cap, cap], identities):
        source_seal = c / 'source-seal.json'
        assert sha(source_seal) == identity['sourceSealSHA256']
        assert hashlib.sha256(exact.canonical(read(source_seal)['files']).encode()).hexdigest() == identity['sourceFilesCommitment']
    assert commitments[0] == commitments[1]
    data = {'version': 1, 'phase': 'd0', 'anonymous_id': aid, 'anchor_report': ref(anchor_path), 'paired_report': ref(paired_path),
            'source_commitments': commitments, 'source_seals': [ref(c / 'source-seal.json') for c in [anchor_cap, cap]],
            'acquisition_records': [ref(c / 'acquisition-records.json') for c in [anchor_cap, cap]]}
    result = exact.paired_d0(anchor, paired, commitments)
    aidx = {r['key']: i for i, r in enumerate(anchor['rows'])}
    pidx = {r['key']: i for i, r in enumerate(paired['rows'])}
    platform_counts = {}
    for platform in ['ios', 'android']:
        platform_counts[platform] = {}
        for bucket in exact.BUCKETS:
            selected = [r for r in result['rows'] if r['platform'] == platform and r['denominator'] == bucket]
            platform_counts[platform][bucket] = {'required': len(selected),
                'matrix': {x + '->' + y: sum(r['anchor'] == x and r['paired'] == y for r in selected) for x in exact.OUTCOMES for y in exact.OUTCOMES},
                'anchor_assessed': sum(r['anchor'] in ['P', 'F'] for r in selected),
                'paired_assessed': sum(r['paired'] in ['P', 'F'] for r in selected)}
    changes = {}
    for bucket in exact.BUCKETS:
        selected = [r for r in result['rows'] if r['denominator'] == bucket]
        changes[bucket] = {
            'gained_assessment_keys': [r['key'] for r in selected if r['anchor'] == 'U' and r['paired'] in ['P', 'F']],
            'lost_assessment_keys': [r['key'] for r in selected if r['anchor'] in ['P', 'F'] and r['paired'] == 'U'],
            'conflicting_assessed_keys': [r['key'] for r in selected if r['conflicting_assessed_outcomes']],
        }
    conflicts = [{'key': r['key'], 'anchor_outcome': r['anchor'], 'paired_outcome': r['paired'],
                  'anchor_grade_pointer': '/rows/' + str(aidx[r['key']]), 'paired_grade_pointer': '/rows/' + str(pidx[r['key']]),
                  'resolution': 'Retained assessed disagreement; neither original grade is changed or selected as infallible gold.'}
                 for r in result['rows'] if r['conflicting_assessed_outcomes']]
    write(out / 'paired-input.json', data)
    result.update({'stage': 'paired-d0', 'paired_input': ref(out / 'paired-input.json'),
                   'input_commitments': {'anchor_grade': ref(anchor_path), 'paired_grade': ref(paired_path),
                                        'anchor_source_identity': ref(anchor_cap / 'source-identity.json'), 'paired_source_identity': ref(cap / 'source-identity.json'),
                                        'anchor_capsule_seal': ref(anchor_cap / 'capsule-seal.json'), 'paired_capsule_seal': ref(cap / 'capsule-seal.json'),
                                        'reviewed_paired_manifest': ref(cap / 'manifest-reviewed.json')},
                   'platform_counts': platform_counts, 'observation_coverage_changes': changes,
                   'conflict_records': conflicts, 'raw_capability_availability': ref(out / 'raw-capability-availability.json'),
                   'administrative_limitations': 'COMMON frozen capability-origin format constraints and exact-decoder overhead are evaluation infrastructure, not tool gains/losses. Raw Android field availability is separately retained. All native text/control/bounds and measured pixel evidence supported by V3 was evaluated. Original acquisition records remain separate; no duration, success, causal effect or assignment is inferred from row counts.'})
    write(out / 'comparison.json', result)
    print(json.dumps({'anonymous_id': aid, 'comparison_path': str((out / 'comparison.json').relative_to(REPO)), 'comparison_sha256': sha(out / 'comparison.json'), 'completed': True}))
