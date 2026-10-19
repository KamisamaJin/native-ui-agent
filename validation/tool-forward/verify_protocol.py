#!/usr/bin/env python3
"""Recheck recorded blind-phase chronology, without judging business UI."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

R = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def portable(path):
    path = str(path)
    marker = 'validation/tool-forward/'
    return R / path.split(marker, 1)[1] if marker in path else R / path


def timestamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def verify_references(value):
    count = 0
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            path = portable(value['path'])
            assert path.is_file() and sha(path) == value['sha256'], str(path)
            if 'bytes' in value:
                assert path.stat().st_size == value['bytes'], str(path)
            count += 1
        for child in value.values():
            count += verify_references(child)
    elif isinstance(value, list):
        count += sum(verify_references(child) for child in value)
    return count


def main():
    index = read(R / 'report-index.json')
    assert index['blindness_complete'] is True
    seals = {}
    checked = 0
    for phase, entry in index['protocol']['seals'].items():
        checked += verify_references(entry)
        seals[phase] = read(portable(entry['path']))
        checked += verify_references(seals[phase])
    dispatch = read(R / 'private/phase-dispatch.json')
    assert sha(portable(index['protocol']['seals']['d0']['path'])) == dispatch['readonly_review']['joint_d0_seal_sha256']
    d0_time = timestamp(seals['d0']['sealedAtUTC'])
    preparation_path = R / 'design/size-revision/private/evaluator/preparation-manifest.json'
    assert sha(preparation_path) == seals['d0']['preparationManifestSHA256']
    preparation = read(preparation_path)
    checked += verify_references(preparation)
    assert timestamp(preparation['preparedAtUTC']) <= d0_time
    assert preparation['candidateSourcesReadBeforePreparationSeal'] == 0
    assert preparation['rawCandidateEvidenceReadBeforePreparationSeal'] == 0
    final_time = timestamp(seals['final']['sealedAtUTC'])
    matching_time = timestamp(seals['matching']['sealedAtUTC'])
    paired_time = timestamp(seals['paired']['sealedAtUTC'])
    unblinding = read(R / 'unblinding.json')
    assert final_time <= matching_time <= paired_time <= timestamp(unblinding['releasedAtUTC'])
    assignment = R / 'private/assignment.json'
    assert sha(assignment) == read(R / 'assignment-commitment.json')['sha256']
    assert unblinding['assignmentSHA256'] == sha(assignment)
    for arm in read(assignment)['arms']:
        label = {'tool-v2': 'baseline_v2', 'tool-v3': 'candidate_v3'}[arm['capability']]
        assert index['arm_labels'][arm['submission']] == label
    final_sources = []
    for submission in index['grades']:
        review_root = R / 'phase-reports' / submission / 'readonly-review'
        review_manifest = read(review_root / 'manifest.json')
        assert sha(review_root / 'manifest.json') == dispatch['repair']['both_self_review_manifest_sha256'][submission]
        review = read(review_root / 'reports/self-review.json')
        repair = read(R / 'phase-reports' / submission / 'repair/reports/repair.json')
        assert d0_time <= dispatch['readonly_review']['prepared_at'] <= timestamp(review['startedAt'])
        assert timestamp(review['startedAt']) <= timestamp(review['finishedAt']) <= review_manifest['sealed_at']
        assert 0 <= review['elapsedSeconds'] <= review['budgetSeconds'] == 720
        assert review_manifest['sealed_at'] <= dispatch['repair']['prepared_at'] <= timestamp(repair['startedAt'])
        source_time = read(R / 'implementations/final' / submission / 'manifest.json')['sealed_at']
        assert timestamp(repair['startedAt']) <= timestamp(repair['finishedAt']) <= source_time
        assert 0 <= repair['elapsedSeconds'] <= repair['budgetSeconds'] == 900
        final_sources.append(source_time)
        for path in (R / 'evidence/final' / submission).glob('*/*/manifest.json'):
            assert read(path)['finished_at'] <= final_time
    application = read(R / 'final-source-application.json')
    final_inputs = read(R / 'private/inputs/final/manifest.json')
    assert max(final_sources) <= application['applied_at'] <= final_inputs['created_at'] <= final_time
    for host in application['hosts']:
        path = R / 'implementations/final' / host['submission'] / 'manifest.json'
        assert sha(path) == host['source_manifest_sha256']
        assert read(path)['files'] == host['files']
    print(json.dumps({'status': 'passed_recorded_blind_protocol',
                      'sealed_references_checked': checked,
                      'scope': 'Recorded chronology, commitments and byte integrity. Shared-filesystem procedural blindness is not adversarial access isolation or proof of unread files.'}))


if __name__ == '__main__':
    main()
