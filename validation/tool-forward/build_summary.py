#!/usr/bin/env python3
"""Recompute report statistics after independent grades/matches and unblinding."""
import argparse
import csv
import hashlib
import json
from itertools import zip_longest
from pathlib import Path

from metrics import (discovery_stats, grade_stats, paired_observation_stats,
                     stratified_stats, transitions)
from timings import captures, engineering_costs, phases

R = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sealed(entry):
    path = R / entry['path']
    assert sha(path) == entry['sha256'], str(path)
    return read(path)


def build(index):
    assert index['blindness_complete'] is True
    plans = {phase: read(R / 'private' / (phase + '-required-assessments.json'))
             for phase in ['d0', 'final']}
    result = {'schema_version': 1, 'report_index_sha256': sha(R / 'report-index.json'),
              'arms': {}, 'engineering_native_costs': engineering_costs(),
              'scope': 'Arithmetic over independently sealed grades/matches; one task and correlated platforms. Calendar durations are not exact active reasoning time.'}
    grades = {}
    for submission, entries in index['grades'].items():
        grade = {phase: sealed(entry) for phase, entry in entries.items()}
        grades[submission] = grade
        matching = sealed(index['matching'][submission])
        data = {'submission': submission, 'grades': {},
                'self_review': discovery_stats(grade['d0'], matching),
                'repair': transitions(grade['d0'], grade['final']),
                'phase_times': phases(submission),
                'native_capture_times': {phase: captures(R / 'evidence' / phase / submission)
                                         for phase in ['d0', 'final']},
                'independent_defect_clusters': matching.get('defectClusters', [])}
        for phase in ['d0', 'final']:
            data['grades'][phase] = {**grade_stats(grade[phase]),
                                     **stratified_stats(grade[phase], plans[phase])}
        result['arms'][index['arm_labels'][submission]] = data
    paired_submission = index['paired_submission']
    result['paired_observation'] = paired_observation_stats(sealed(index['paired_grade']),
                                                          grades[paired_submission]['d0'])
    result['paired_observation']['native_capture_times'] = captures(R / 'paired-evidence/d0')
    result['paired_observation']['current_native_capture_times'] = captures(R / 'evidence/d0' / paired_submission)
    for label, arm in result['arms'].items():
        root = R / ('paired-evidence/d0' if label == 'baseline_v2'
                    else 'evidence/d0/' + arm['submission'])
        arm['self_review_evidence_corpus'] = {
            'path': str(root.relative_to(R)), 'cost': captures(root),
            'scope': 'Actual corpus supplied before the timed read-only review. Candidate reuses its main D0 grading captures; baseline uses the old-collector paired corpus. Production/grade evidence is not an extra free source of complete feedback, and overlapping/reused costs must not be counted twice.'}
    return result, grades, plans


def csv_rows(grades, plans):
    for submission, phases in grades.items():
        for phase, grade in phases.items():
            metadata = {(r['platform'], r['key']): r for r in plans[phase]['assessments']}
            for row in grade['results']:
                m = metadata[(row['platform'], row['key'])]
                yield {'submission': submission, 'phase': phase, 'platform': row['platform'],
                       'case': m['caseId'], 'state': m['stateId'], 'key': row['key'],
                       'aspect': row['aspect'], 'source_only': row['sourceOnly'],
                       'outcome': row['outcome'], 'reason': row['reason'],
                       'binding_status': row['bindingStatus'],
                       'missing_methods': json.dumps(row['missingEvidenceMethod'], ensure_ascii=False),
                       'exact_sources': json.dumps(row['exactSources'], ensure_ascii=False, sort_keys=True)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--check', action='store_true')
    a = p.parse_args()
    index = read(R / 'report-index.json')
    result, grades, plans = build(index)
    encoded = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + '\n'
    output = R / 'result-summary.json'
    if a.check:
        assert output.read_text() == encoded, 'Published statistics do not reproduce'
        with (R / 'assessment-ledger.csv').open(newline='') as file:
            for actual, expected in zip_longest(csv.DictReader(file), csv_rows(grades, plans)):
                assert actual is not None and expected is not None, 'Atomic ledger row count differs'
                assert actual == {key: '' if value is None else str(value)
                                  for key, value in expected.items()}, 'Atomic ledger differs from sealed grade'
        print(json.dumps({'status': 'passed_report_arithmetic_recomputation'}))
        return
    assert not output.exists(), 'Preserve the prior result; no silent overwrite'
    output.write_text(encoded)
    rows = list(csv_rows(grades, plans))
    with (R / 'assessment-ledger.csv').open('x', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({'written': str(output), 'atomic_ledger_rows': len(rows)}))


if __name__ == '__main__':
    main()
