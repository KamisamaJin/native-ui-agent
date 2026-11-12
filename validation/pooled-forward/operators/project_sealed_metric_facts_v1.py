"""Copy sealed product decisions; add only explicit metric provenance fields.

No coverage, delivery, cost, expected value or product decision is supplied.
The final join must add authenticated original binding results separately.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
COORDINATION = ROOT / 'operators/cohort2/coordination'
SEALED = ROOT / 'cache/business/blind-quality/correspondence/original-v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {'path': str(path), 'sha256': digest(path)}


def main():
    seal = SEALED / 'SEAL.json'
    assert digest(seal) == '3883e7c43288190c4cf1c075913ee85c7d85e52c236ad48d69dce2d296f8ea60'
    reveal = COORDINATION / 'ROOT-MAPPING-REVEAL-v1.json'
    assert digest(reveal) == 'cd108d543160faa2f59a06d744dc8fa9e4d8bd0b2774ff8fcfde8731c53ff179'
    source = SEALED / 'correspondence.json'
    assert digest(source) == json.loads(seal.read_text())['files']['correspondence.json']
    consumer_path = ROOT / 'verify_publication.py'
    assert digest(consumer_path) == 'e9fc84f457129ea014a40e78a53a29778862468a524d2c84ae184e3d5b11c25b'
    consumer_spec = importlib.util.spec_from_file_location('sealed_fact_strict_metadata', consumer_path)
    consumer = importlib.util.module_from_spec(consumer_spec)
    consumer_spec.loader.exec_module(consumer)
    raw = consumer.strict_json(source.read_bytes())
    assert raw['kind'] == 'independent-anonymous-five-case-correspondence'
    cases = copy.deepcopy(raw['cases'])
    assert len(cases) == 5 and {x['case_id'] for x in cases} == {'Case%02d' % i for i in range(1, 6)}
    path = ROOT / 'publication-cost-metrics-v3/metric_rules_v3.py'
    assert digest(path) == '34a98a6b2be408c3261616b2eab931ca2116d7f47036b719728899e0eeeb9ff6'
    spec = importlib.util.spec_from_file_location('sealed_fact_metric_rules', path)
    metric = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metric)
    additions = []
    for ci, case in enumerate(cases):
        assert set(case['versions']) == {'X', 'Y'}
        for version, final in case['versions'].items():
            for field, repair in [('defect_alarms', False), ('attempted_repairs', True)]:
                for i, row in enumerate(final[field]):
                    assert 'provenance' not in row
                    version_field = 'source_before' if repair else 'source_version'
                    original_pointer = '/cases/%d/versions/%s/%s/%d' % (ci, version, field, i)
                    evidence = copy.deepcopy(row['evidence'])
                    row['provenance'] = {
                        'phase': row['visibility'],
                        'source_version': row[version_field],
                        'evidence': evidence + [dict(ref(source), pointer=original_pointer)],
                    }
                    metric.provenance(row, repair=repair)
                    additions.append({'case_id': case['case_id'], 'version': version, 'field': field,
                        'id': row['id'], 'source_pointer': original_pointer,
                        'phase_copied_from': original_pointer + '/visibility',
                        'source_version_copied_from': original_pointer + '/' + version_field})
    # Removing exactly the newly added metadata recovers every original product
    # field, original order, Boolean/null actual, uncertainty and evidence.
    restored = copy.deepcopy(cases)
    for case in restored:
        for final in case['versions'].values():
            for field in ['defect_alarms', 'attempted_repairs']:
                for row in final[field]:
                    del row['provenance']
    assert restored == raw['cases']
    output = COORDINATION / 'SEALED-PRODUCT-FACTS-FOR-METRICS-v1.json'
    value = {'version': 1, 'kind': 'exact-sealed-correspondence-product-facts-for-metrics',
        'at_unix': time.time(), 'cases': cases,
        'source_correspondence': ref(source), 'correspondence_seal': ref(seal), 'mapping_reveal': ref(reveal),
        'projection': {'only_added_fields': 'Explicit phase/source-version/evidence provenance on alarm/repair rows',
            'field_pointer_receipts': additions, 'all_original_product_fields_retained': True,
            'repair_context_uses_explicit_original_source_before': True,
            'source': ref(Path(__file__)), 'metric_rules': ref(path)},
        'pending': ['Authenticated current original coverage rows, five delivery gates and measured own/hidden costs'],
        'scope': 'Exact sealed product decisions with provenance formatting only; no new adjudication, metric result, source/image actual, delivery or cost is inferred.'}
    with output.open('x') as f:
        json.dump(value, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    output.chmod(0o444)
    print(json.dumps({'output': ref(output), 'cases': len(cases), 'metadata_additions': len(additions),
                      'all_original_product_fields_retained': True}, sort_keys=True))


if __name__ == '__main__':
    main()
