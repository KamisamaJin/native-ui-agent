#!/usr/bin/env python3
"""Use original failed checks and approved dependencies to choose diagnostic feedback."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import design_contract as design
from requirement_routes import report_rows


def propose(coverage, parent, report, failed_ids, *, changed_files, source_before, source_after):
    if (design.digest(parent) != coverage['plan_sha256'] or source_before == source_after or
            any(not isinstance(v, str) or len(v) != 64 or any(c not in '0123456789abcdef' for c in v) for v in [source_before, source_after])):
        raise ValueError('Exact parent plan and a changed source version required')
    if not changed_files or any(not v or Path(v).is_absolute() or '..' in Path(v).parts for v in changed_files):
        raise ValueError('Explicit relative changed production paths required')
    rows = report_rows(report, parent)
    if not failed_ids or len(failed_ids) != len(set(failed_ids)) or any(k not in rows or rows[k]['status'] != 'failed' for k in failed_ids):
        raise ValueError('Feedback must start from original failed checks, never invented failures')
    owners = [o for o in coverage['obligations'] if set(o['assertion_ids']) & set(failed_ids)]
    if not owners: raise ValueError('Failure has no approved requirement route')
    selected = {o['id'] for o in owners}
    # All independently declared regression obligations are closed transitively.
    while True:
        expanded = selected | {r for o in coverage['obligations'] if o['id'] in selected for r in o['route']['regression_obligations']}
        if expanded == selected: break
        selected = expanded
    obligations = [o for o in coverage['obligations'] if o['id'] in selected]
    states = [s['id'] for s in parent['states'] if any(s['id'] in o['states'] for o in obligations)]
    return {'version': 1, 'parent_plan_sha256': coverage['plan_sha256'], 'source_before': source_before, 'source_after': source_after,
            'changed_files': changed_files, 'original_failed_ids': failed_ids, 'obligations': sorted(selected), 'states': states,
            'assertion_ids': sorted({r for o in obligations for r in o['assertion_ids']}),
            'requires_fresh_capture': True, 'full_final_required': True,
            'unverified_obligations': [o['id'] for o in coverage['obligations'] if o['id'] not in selected],
            'scope': 'Diagnostic feedback only. Dependencies express approved regression checks, not a proven source-impact graph. Full fresh final verification remains mandatory.'}


def from_capture(coverage, parent, failed_ids, result_path, result_sha, source_roots, *,
                 review_submission=None, review_sha=None, lock=None, lock_sha=None, policy=None, policy_sha=None):
    """Derive change identity from an immutable original capture and actual files."""
    from execution_plan import source_fingerprint
    result_path = Path(result_path).resolve()
    if hashlib.sha256(result_path.read_bytes()).hexdigest() != result_sha:
        raise ValueError('Original independently pinned capture-result digest differs')
    receipt = design.load(result_path); root = result_path.parent
    if receipt.get('status') != 'verified_capture' or receipt.get('parent_plan_sha256') != design.digest(parent):
        raise ValueError('Verified source-bound capture for this exact parent required')
    report_path = root / 'automatic.json'
    if hashlib.sha256(report_path.read_bytes()).hexdigest() != receipt.get('automatic_sha256'):
        raise ValueError('Original automatic report changed')
    before = design.load(root / 'source-before.json')
    if design.digest(before) != receipt['source_sha256'] or before != design.load(root / 'source-after.json'):
        raise ValueError('Original captured production source changed or drifted')
    # Same root identities/order preserve the relative source-key namespace.
    if [str(Path(p).resolve()) for p in source_roots] != receipt['source_roots']:
        raise ValueError('Actual production roots differ from the captured source namespace')
    after = source_fingerprint(source_roots)
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    report = design.load(report_path)
    if review_submission is not None:
        # Rebuild judgments from original actuals and native pixels. A different
        # arbitrary evaluated report is never accepted as an automatic override.
        import review_contract
        import native_checks
        from execution_plan import verify_capture_images
        review_submission = Path(review_submission)
        if any(v is None for v in [review_sha, lock, lock_sha, policy, policy_sha]):
            raise ValueError('Original review, independent lock and policy identities required')
        if hashlib.sha256(review_submission.read_bytes()).hexdigest() != review_sha or lock_sha != coverage['design_lock_sha256']:
            raise ValueError('Pinned original review actuals and the same independent design required')
        op = root / 'native/observation.json'
        obs_sha = hashlib.sha256(op.read_bytes()).hexdigest()
        if obs_sha != receipt.get('observation_sha256'):
            raise ValueError('Original capture observation changed')
        observation = design.load(op); platform = parent['design_contract']['platform']
        verify_capture_images(receipt, op.parent)
        manual = review_contract.bind(parent, lock, lock_sha, policy, policy_sha, observation, obs_sha,
                                      op.parent, design.load(review_submission), platform)
        report = native_checks.evaluate(parent, observation, platform, manual, op.parent, obs_sha,
                                        lock, lock_sha, policy, policy_sha)
    elif any(v is not None for v in [review_sha, lock, lock_sha, policy, policy_sha]):
        raise ValueError('Review reconstruction needs its original submission')
    value = propose(coverage, parent, report, failed_ids, changed_files=changed,
                    source_before=design.digest(before), source_after=design.digest(after))
    value['original_capture_sha256'] = result_sha
    value['change_basis'] = 'Original immutable capture source map versus current production files, not caller-entered hashes or paths'
    if review_submission is not None:
        value['review_submission_sha256'] = review_sha
        value['finding_basis'] = 'Recomputed approved-contract review of original state-bound actuals, not an overridden automatic report'
    return value


def main():
    p = argparse.ArgumentParser()
    for name in ['coverage', 'plan', 'output']: p.add_argument('--' + name, type=Path, required=True)
    for name in ['report', 'change', 'capture-result']: p.add_argument('--' + name, type=Path)
    p.add_argument('--capture-result-sha256'); p.add_argument('--source-root', type=Path, action='append')
    for name in ['review-submission', 'design-lock', 'policy']: p.add_argument('--' + name, type=Path)
    for name in ['review-sha256', 'design-sha256', 'policy-sha256']: p.add_argument('--' + name)
    p.add_argument('--failed-id', action='append', required=True); a = p.parse_args()
    if a.capture_result:
        if not a.capture_result_sha256 or not a.source_root or a.report or a.change:
            raise ValueError('Capture mode needs original result digest and actual roots, without caller change/report overrides')
        value = from_capture(design.load(a.coverage), design.load(a.plan), a.failed_id,
                             a.capture_result, a.capture_result_sha256, a.source_root,
                             review_submission=a.review_submission, review_sha=a.review_sha256,
                             lock=design.load(a.design_lock) if a.design_lock else None, lock_sha=a.design_sha256,
                             policy=design.load(a.policy) if a.policy else None, policy_sha=a.policy_sha256)
    else:
        if not a.report or not a.change: raise ValueError('Original report and explicit change declaration required')
        change = design.load(a.change)
        value = propose(design.load(a.coverage), design.load(a.plan), design.load(a.report), a.failed_id,
                        changed_files=change['changed_files'], source_before=change['source_before'], source_after=change['source_after'])
        value['change_basis'] = 'Caller-declared source changes; not independently measured. Prefer capture-result mode.'
    with a.output.open('x') as stream: stream.write(__import__('json').dumps(value, indent=2, ensure_ascii=False) + '\n')
if __name__ == '__main__': main()


def unresolved(coverage, parent, report, *, changed_files, source_before, source_after, final=False, selected_states=None):
    """Default planner accepts honest unknowns, including incomplete native packets.

    It does not convert an unknown to a failure. Its caller must reconstruct the
    original report from pinned raw evidence, and measure the source maps.
    """
    if design.digest(parent) != coverage['plan_sha256']:
        raise ValueError('Retest coverage belongs to another plan')
    rows = report_rows(report, parent)
    allowed = set(selected_states or [s['id'] for s in parent['states']])
    issues = {k for k, row in rows.items() if row['state'] in allowed and row['status'] != 'passed'}
    owners = {o['id'] for o in coverage['obligations'] if set(o['assertion_ids']) & issues or (o['priority'] == 'must' and not o['route_available'])}
    while True:
        expanded = owners | {r for o in coverage['obligations'] if o['id'] in owners for r in o['route']['regression_obligations']}
        if expanded == owners: break
        owners = expanded
    full = final or not owners or bool(coverage['must_route_gaps'])
    states = [s['id'] for s in parent['states'] if full or any(o['id'] in owners and s['id'] in o['states'] for o in coverage['obligations'])]
    return {'version': 2, 'parent_plan_sha256': coverage['plan_sha256'], 'states': states,
            'original_failed_ids': sorted(k for k in issues if rows[k]['status'] == 'failed'),
            'original_unknown_ids': sorted(k for k in issues if rows[k]['status'] == 'unassessed'),
            'changed_files': changed_files, 'source_before': source_before, 'source_after': source_after,
            'source_changed': source_before != source_after, 'obligations': sorted(owners),
            'reason': 'mandatory full final' if final else 'unresolved checks and approved regression closure' if not full else 'scope unavailable or no supported issue; full fallback',
            'full_final_required': True,
            'scope': 'Diagnostic scope only; approved regression edges are not a source-impact proof. Unknowns retain their status. Fresh full final capture is required.'}


def dispatch(coverage, parent, report, routed, *, changed_files, source_before, source_after,
             final=False, selected_states=None, visual_ids=(), capture_available=True):
    """Route by required work, not merely by every non-passing row.

    Historical bound actuals may choose repair scope. No historical result
    establishes acceptance for edited source, and final still captures fully.
    """
    if design.digest(parent) != coverage['plan_sha256']: raise ValueError('Foreign dispatch plan')
    rows = report_rows(report, parent); rules = {v['id']: v for v in parent['assertions']}
    visual = set(visual_ids); selected = set(selected_states or [s['id'] for s in parent['states']])
    changed = source_before != source_after
    if changed != bool(changed_files): raise ValueError('Measured source change and file delta disagree')
    jobs = []; seeds = set(); acquisition = set()
    for task in routed['tasks']:
        ids = task['assertion_ids']; action = task['action']
        if action == 'defer_to_full_verification': kind = 'deferred_full_coverage'
        elif action == 'repair_contract_route': kind = 'repair_contract'
        elif action in {'clarify_oracle', 'validate_execution_scope'}: kind = 'resolve_oracle_or_scope'
        elif action == 'repair_environment': kind = 'repair_environment'
        elif action == 'acquire_evidence': kind = 'acquire_native'; acquisition.update(ids)
        elif action == 'review_calibrated_measurement': kind = 'review_measurement'
        elif any(key in visual and rows[key]['status'] == 'unassessed' for key in ids): kind = 'review_images'
        elif any(key in visual and rows[key]['status'] == 'failed' for key in ids): kind = 'repair_source'
        elif action in {'diagnose_product', 'investigate_attribution'}: kind = 'repair_source'
        else: kind = 'diagnose_capability_or_locator'
        if kind in {'repair_source', 'diagnose_capability_or_locator', 'review_measurement', 'acquire_native'}: seeds.update(ids)
        jobs.append(dict(task, kind=kind, source_basis='historical' if changed else 'current',
                         needs_new_capture=kind == 'acquire_native'))
    all_states = [v['id'] for v in parent['states']]
    owners={o['id']for o in coverage['obligations']if set(o['assertion_ids'])&seeds}
    while True:
        expanded=owners|{v for o in coverage['obligations']if o['id']in owners for v in o['route']['regression_obligations']}
        if expanded==owners:break
        owners=expanded
    impact_states=[v for v in all_states if any(o['id']in owners and v in o['states']for o in coverage['obligations'])]
    repair_states=[v for v in all_states if any(j['kind']=='repair_source'and j.get('state')==v for j in jobs)]
    states = []
    if final or not capture_available: states = all_states
    elif changed:
        # A repaired visual finding also needs a new image; an unresolved old
        # visual judgment is not fabricated for edited source.
        seeds.update(k for k, row in rows.items() if k in visual and row['status'] == 'failed')
        states=all_states if selected!=set(all_states)or not seeds else impact_states
    elif acquisition:
        states = [v for v in all_states if any(rows[k]['state'] == v for k in acquisition)]
    if coverage['must_route_gaps']: states = []
    actionable = [v for v in jobs if v['kind'] != 'deferred_full_coverage' and v.get('priority') != 'advisory']
    status = ('blocked_contract' if coverage['must_route_gaps'] else 'capture_required' if states else
              'awaiting_review' if any(v['kind'] == 'review_images' for v in actionable) else
              'awaiting_measurement' if any(v['kind'] == 'review_measurement' for v in actionable) else
              'awaiting_source_repair' if any(v['kind'] == 'repair_source' for v in actionable) else
              'awaiting_diagnosis' if actionable else 'awaiting_full_final' if selected!=set(all_states) else 'feedback_complete')
    return {'version': 3, 'parent_plan_sha256': coverage['plan_sha256'], 'source_before': source_before,
            'source_after': source_after, 'source_changed': changed, 'changed_files': changed_files,
            'status': status, 'states': states, 'jobs': jobs, 'repair_states':repair_states,'retest_states_after_edit':impact_states,
            'full_coverage_pending':selected!=set(all_states),'delivery_complete':False,
            'original_failed_ids': sorted(k for k,r in rows.items() if r['status']=='failed'),
            'original_unknown_ids': sorted(k for k,r in rows.items() if r['status']=='unassessed'),
            'review_only_ids': sorted(k for k in visual if rows[k]['status']=='unassessed' and rows[k]['state'] in selected),
            'requires_fresh_capture': bool(states), 'full_final_required': True,
            'scope': 'Unchanged-source review/repair/measurement jobs do not launch SDKs. Changed source invalidates acceptance; only historical problem scope is reused. Full final remains fresh.'}
