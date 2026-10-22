#!/usr/bin/env python3
"""Shared acceptance: native wire preflight, authoritative facts and explicit panel disagreement."""
from __future__ import annotations

import argparse
import copy
import json
import math
import struct
from pathlib import Path

import design_contract as design
from native_environment import direction, ENCODING


def environment(observation, expected, platform):
    fields = {'width', 'height', 'direction', 'theme', 'font_scale' if platform == 'android' else 'dynamic_type'}
    extras = {'dimension_encoding'} if platform == 'android' else set()
    if set(expected) - extras != fields or platform not in {'ios', 'android'}:
        raise ValueError('Explicit platform-native environment contract required')
    if expected['direction'] not in {'ltr', 'rtl'} or expected['theme'] not in {'light', 'dark'}:
        raise ValueError('Unknown approved native environment identifiers')
    if any(type(expected[k]) not in {int, float} or not math.isfinite(expected[k]) or expected[k] <= 0 for k in ['width', 'height']):
        raise ValueError('Positive finite requested/native dimensions required')
    mode = expected.get('dimension_encoding', 'exact-native-units')
    if mode not in {'exact-native-units', 'paparazzi-float32-screen-config-v1'}:
        raise ValueError('Unknown native dimension encoding')
    f32 = lambda v: struct.unpack('!f', struct.pack('!f', v))[0]
    snapshots = observation.get('snapshots', [])
    actual = []
    for index, snapshot in enumerate(snapshots):
        if platform == 'android':
            config, viewport = observation.get('configuration', {}), snapshot.get('logical_viewport_dp', {})
            proof = direction(config.get('direction'), encoding=ENCODING)
            value = {'width': viewport.get('width'), 'height': viewport.get('height'), 'direction': proof['canonical'],
                     'theme': {16: 'light', 32: 'dark'}.get(config.get('night_mode_mask')),
                     'font_scale': config.get('font_scale')}
        else:
            runtime = snapshot.get('runtime', {})
            config, viewport = runtime.get('actual_environment', {}), snapshot.get('viewport', {})
            proof = {'raw': config.get('direction'), 'canonical': config.get('direction'), 'encoding': 'ios-actual-environment-v1'}
            value = {'width': viewport.get('width'), 'height': viewport.get('height'),
                     **{k: config.get(k) for k in ['direction', 'theme', 'dynamic_type']}}
        comparison_expected = {k: expected[k] for k in fields}
        dimensions = None
        dimension_ok = True
        if mode == 'paparazzi-float32-screen-config-v1':
            # This version names the exact host implementation, not a general dp tolerance.
            # Paparazzi's pinned device sets screen pixels with Kotlin Float operations.
            native = snapshot.get('native_viewport_px', {})
            px = [int(f32(f32(expected[k]) * f32(2.75))) for k in ['width', 'height']]
            density = native.get('density')
            dimensions = {'encoding': mode, 'requested_dp': [expected['width'], expected['height']],
                          'expected_native_px': px, 'actual_native_viewport': native,
                          'reported_logical_dp': [value['width'], value['height']]}
            dimension_ok = (config.get('dimension_encoding') == mode and
                            [native.get('width'), native.get('height')] == px and density == 2.75 and
                            config.get('density') == density and
                            config.get('requested_width_dp') == f32(expected['width']) and
                            config.get('requested_height_dp') == f32(expected['height']))
            if density == 2.75:
                # Verify even the serialized Float division, without equality to an ideal dp request.
                logical = [f32(p / density) for p in px]
                dimension_ok = dimension_ok and all(f32(value[k]) == v for k, v in zip(['width', 'height'], logical) if value[k] is not None)
            for key in ['width', 'height']:
                comparison_expected[key] = value[key]
        missing = any(value[k] is None for k in fields) or (mode != 'exact-native-units' and not snapshot.get('native_viewport_px'))
        actual.append({'snapshot_index': index, 'actual': value, 'direction_encoding': proof,
                       'native_dimensions': dimensions,
                       'status': 'U' if missing else 'P' if value == comparison_expected and dimension_ok else 'F'})
    status = 'U' if not actual or any(v['status'] == 'U' for v in actual) else 'P' if all(v['status'] == 'P' for v in actual) else 'F'
    return {'status': status, 'expected': expected, 'frames': actual,
            'scope': 'Actual native wire values. Unknown format is not guessed or counted as valid input.'}


def consensus(plan, authoritative, first, second, review_catalog, env, attributions=None):
    """Inputs are reports recomputed from original observations, never caller-entered truth."""
    planned = {r['id']: r for r in plan['assertions']}
    atoms = {r['id']: r for r in review_catalog['rows']}
    reports = []
    for report in [authoritative, first, second]:
        rows = {r['id']: r for r in report['assertions']}
        if len(rows) != len(report['assertions']) or set(rows) != set(planned):
            raise ValueError('Acceptance panel omitted, duplicated or invented a contract cell')
        reports.append(rows)
    attributions = attributions or [{}, {}]
    rows = []
    for rid, rule in planned.items():
        base, a, b = [r[rid] for r in reports]
        native = rule['kind'] != 'manual' or atoms[rid]['method'] == 'native_pixels'
        if native:
            status = base['status']
            reason = 'Recomputed native/pixel fact; qualitative opinions cannot override it'
        elif a['status'] == b['status'] and a['status'] in {'passed', 'failed'}:
            status, reason = a['status'], 'Two independently scoped visual judgments agree'
        else:
            status, reason = 'unassessed', 'Visual panel disagreement or insufficient evidence retained'
        fact_status = status
        if env['status'] != 'P':
            status, reason = 'unassessed', 'Native environment contract invalid or unobserved; raw facts retained'
        owner = atoms.get(rid, {}).get('responsibility', 'component')
        attributed = [panel.get(rid) for panel in attributions]
        cause = None
        if status == 'failed':
            if owner in {'host', 'system'}:
                cause = 'infrastructure' if owner == 'host' else 'system'
            elif all(p is not None for p in attributed) and attributed[0]['cause'] == attributed[1]['cause']:
                cause = attributed[0]['cause']
            else:
                cause = 'uncertain'
        rows.append({'id': rid, 'state': rule['state'], 'requirement_id': rule['requirement_id'],
                     'expected': rule['expected'], 'unit': rule['unit'], 'op': rule.get('op', 'eq'),
                     'expectation_provenance': rule['expectation_provenance'], 'status': status,
                     'ungated_fact_status': fact_status, 'responsibility': owner,
                     'cause_category': cause, 'cause_assessments': copy.deepcopy(attributed),
                     'method': 'authoritative_fact' if native else 'independent_visual_consensus', 'reason': reason,
                     'authoritative': copy.deepcopy(base), 'judges': [copy.deepcopy(a), copy.deepcopy(b)],
                     'panel_disagreement': not native and a['status'] != b['status']})
    return {'version': 1, 'rows': rows, 'counts': {s: sum(r['status'] == s for r in rows) for s in ['passed', 'failed', 'unassessed']},
            'environment': env, 'matrix_contract': copy.deepcopy(plan['matrix_contract']),
            'scope': 'Deterministic native/pixel evidence plus two independent AI judgments. Agreement is not human gold; disagreements and unsupported facts remain unknown.'}


def evaluate(plan, lock, lock_sha, policy, policy_sha, observation, observation_sha, root, platform, expected_environment, first, second):
    import native_checks
    import review_contract
    cat = review_contract.catalog(plan, lock, lock_sha, policy, policy_sha, platform)
    blank = {'version': 1, 'catalog_sha256': design.digest(cat), 'observation_sha256': observation_sha, 'decisions': []}
    panels, attributions = [], []
    submissions = [blank]
    for panel in [first, second]:
        if set(panel) != {'review', 'attributions'}:
            raise ValueError('Independent judge must provide scoped review and separate failure-cause assessments')
        submissions.append(panel['review'])
        scoped = {}
        for item in panel['attributions']:
            if set(item) != {'id', 'cause', 'reason', 'snapshot_indices'} or item['id'] in scoped:
                raise ValueError('Unique original rule-based cause assessment required')
            if item['cause'] not in {'product', 'infrastructure', 'observation', 'uncertain'} or not isinstance(item['reason'], str) or not item['reason'].strip():
                raise ValueError('Explicit supported failure cause or uncertainty required')
            rule = next((r for r in plan['assertions'] if r['id'] == item['id']), None)
            if rule is None:
                raise ValueError('Cause assessment references an unplanned assertion')
            state = next(s for s in plan['states'] if s['id'] == rule['state'])
            allowed = {i for i, _ in native_checks.state_evidence(observation, state)[0]}
            indices = item['snapshot_indices']
            if not isinstance(indices, list) or not indices or any(type(i) is not int for i in indices) or len(set(indices)) != len(indices) or not set(indices) <= allowed:
                raise ValueError('Failure cause lacks original state-scoped screenshots')
            evidence = []
            for i in indices:
                path = (root / observation['snapshots'][i]['screenshot']).resolve()
                if not path.is_relative_to(root.resolve()) or not path.is_file():
                    raise ValueError('Cause assessment screenshot missing or outside root')
                evidence.append({'path': str(path.relative_to(root.resolve())), 'sha256': __import__('native_pixels').sha(path)})
            scoped[item['id']] = dict(item, evidence=evidence)
        attributions.append(scoped)
    for submission in submissions:
        manual = review_contract.bind(plan, lock, lock_sha, policy, policy_sha, observation, observation_sha, root, submission, platform)
        report = native_checks.evaluate(plan, observation, platform, manual, root, observation_sha, lock, lock_sha, policy, policy_sha)
        panels.append(report)
    return consensus(plan, *panels, cat, environment(observation, expected_environment, platform), attributions)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ['plan', 'design-lock', 'policy', 'observation', 'environment', 'judge-one', 'judge-two', 'output']:
        p.add_argument('--' + flag, type=Path, required=True)
    for flag in ['design-sha256', 'policy-sha256', 'environment-sha256']:
        p.add_argument('--' + flag, required=True)
    p.add_argument('--platform', choices=['ios', 'android'], required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('Fresh acceptance output required')
    expected = design.load(a.environment)
    if design.digest(expected) != a.environment_sha256:
        raise ValueError('Environment expectation changed after independent approval')
    report = evaluate(design.load(a.plan), design.load(a.design_lock), a.design_sha256, design.load(a.policy), a.policy_sha256,
                      design.load(a.observation), __import__('native_pixels').sha(a.observation), a.observation.parent, a.platform,
                      expected, design.load(a.judge_one), design.load(a.judge_two))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report['counts']))


if __name__ == '__main__':
    main()
