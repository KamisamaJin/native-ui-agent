#!/usr/bin/env python3
"""Replay sealed neutral iOS facts without Xcode or a live resource operation."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

R = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(name):
    positive = name != 'v12.4-negative'
    latest = name == 'v12.6-positive'
    capsule = R / 'evidence' / ('ios-qualification-v12.6' if latest else 'ios-neutral-v12.4')
    root = capsule / ('positive' if positive else 'negative')
    capture = root / 'capture'
    native = capture / 'native'
    receipt = read(capture / 'result.json')
    runtime = capture / 'tool-runtime'
    freeze = read(R / ('CANDIDATE-FREEZE-7.json' if latest else 'CANDIDATE-FREEZE-5.json'))
    for rel, expected in receipt['tool_files'].items():
        assert sha(runtime / rel) == expected == freeze['files'][rel], rel
    sys.path.insert(0, str(runtime / 'scripts'))
    import acceptance as ac
    import action_guard as ag
    import design_contract as d
    import evidence_responsibility as er
    import execution_plan as xp
    import native_checks as nc

    scope = R / 'probes/native' / ('prepared-positive' if positive else 'prepared')
    config = read(scope / 'ios/config.json')
    lock = read(scope / 'ios/lock.json')
    plan = read(capture / 'parent-plan.json')
    execution = read(capture / 'execution.json')
    xp.verify_execution(execution, plan, lock, config['design_sha256'], read(scope / 'fixtures.json'), sha(R / 'probes/native/Bridge.swift'))
    observation = read(native / 'observation.json')
    xp.verify_capture_images(receipt, native)
    assert ag.verify_observation(execution['actions'], observation, 'ios') == receipt['action_prerequisites']
    report = nc.evaluate(plan, observation, 'ios', root=native, observation_sha256=sha(native / 'observation.json'), design_lock=lock, design_sha256=config['design_sha256'])
    report['environment'] = ac.environment(observation, read(scope / 'ios/environment.json'), 'ios')
    assert report == read(capture / 'automatic.json')
    assert report['counts'] == ({'passed': 6, 'failed': 0, 'unassessed': 0} if positive else {'passed': 8, 'failed': 0, 'unassessed': 6})
    before = read(capture / 'source-before.json')
    assert before == read(capture / 'source-after.json')
    assert before['0/NeutralCounter.swift'] == sha(R / 'evidence/probes/production/alerttoast/Sources/AlertToast/NeutralCounter.swift')
    assert before['1/NeutralCounter.kt'] == sha(R / 'evidence/probes/production/reply/Reply/app/src/main/java/com/example/reply/ui/components/NeutralCounter.kt')
    manifest = read(native / 'manifest.json')
    summary = read(native / 'native-summary.json')
    assert summary['totalTestCount'] == manifest['native_test_count'] == 1
    assert summary['failedTests'] == (0 if positive else 1)
    assert summary['passedTests'] == (1 if positive else 0)
    assert (native / 'test.xcresult').is_dir()
    for rel, expected in manifest['image_hashes'].items():
        assert sha(native / rel) == expected
        with Image.open(native / rel) as image:
            image.load()
    inner = manifest['execution_coverage']
    # Retain the original v12.4 namespace fault; never treat it as plan proof.
    assert inner['request_sha256' if latest else 'execution_sha256'] == sha(capture / 'fixtures.json')
    assert receipt['execution_sha256'] == execution['execution_sha256']
    assert receipt['execution_sha256'] != sha(capture / 'fixtures.json')
    if latest:
        assert 'execution_sha256' not in inner and inner['identity_scope'] == 'native_request'
        assert inner == xp.request_coverage_receipt(read(capture / 'fixtures.json'), observation, 'ios', sha(capture / 'fixtures.json'))
    cycle = read(root / 'cycle.json')
    resources = read(root / 'resources.json')
    assert cycle['resources_sha256'] == sha(root / 'resources.json')
    assert not resources['cleanup_errors'] and not resources['remaining_devices'] and not resources['remaining_directories']
    assert cycle['status'] == ('accepted' if latest else 'review_source' if positive else 'awaiting_diagnosis')
    compiled = read(root / 'evidence-responsibility.json')
    closed = er.evaluate({'source_review_store': str(capsule / 'source-reviews/ios')}, compiled, report)
    expected = read(root / 'responsibility-results.json')
    if latest:
        assert not closed['blocking_claims']
        for actual, old in zip(closed['rows'], expected['rows']):
            assert {k: v for k, v in actual.items() if k != 'evidence'} == {k: v for k, v in old.items() if k != 'evidence'}
            assert {v['sha256'] for v in actual['evidence']} == {v['sha256'] for v in old['evidence']}
    else:
        assert len(expected['blocking_claims']) == 2  # Original cycles precede source binding.
    print(json.dumps({'status': 'PASS', 'case': name, 'counts': report['counts'], 'scope': 'Original neutral iOS packet replay only; no new SDK or business-quality credit.'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=['v12.4-positive', 'v12.4-negative', 'v12.6-positive'])
    replay(parser.parse_args().case)
