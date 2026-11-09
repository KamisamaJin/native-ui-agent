#!/usr/bin/env python3
"""Bind every approved obligation to checks, then route findings to actions."""
from __future__ import annotations
import argparse
import copy
from pathlib import Path
import design_contract as design


def audit(lock, lock_sha, plan, routes, routes_sha):
    design.validate_lock(lock, lock_sha)
    design.verify_generated(plan, lock, lock_sha, plan['design_contract']['platform'])
    if design.digest(routes) != routes_sha or set(routes) != {'version', 'index', 'routes'} or routes['version'] != 1:
        raise ValueError('Separately approved exact requirement routes required')
    anchor = routes['index']
    if set(anchor) != {'source', 'pointer'}:
        raise ValueError('Approved obligation index needs an exact source pointer')
    obligations = design.pointer(lock['sources'][anchor['source']]['document'], anchor['pointer'])
    if not isinstance(obligations, list) or not obligations:
        raise ValueError('Nonempty independently authored obligation index required')
    ids = [o['id'] for o in obligations]
    if len(ids) != len(set(ids)) or set(routes['routes']) != set(ids):
        raise ValueError('Every approved obligation needs an explicit route disposition')
    states = set(plan['matrix_contract']['selected_states'])
    rules = set(plan['matrix_contract']['selected_requirements'])
    checked, rows, owned = set(), [], set()
    for obligation in obligations:
        if set(obligation) != {'id', 'clause', 'priority', 'states', 'risk'} or not obligation['clause'].strip():
            raise ValueError('Exact source-backed obligation identity, clause, priority, states and risk required')
        if obligation['priority'] not in {'must', 'advisory'} or obligation['risk'] not in {'layout', 'style', 'behavior', 'content'}:
            raise ValueError('Known independent priority and risk required')
        selected = obligation['states']
        if not selected or len(selected) != len(set(selected)) or not set(selected) <= states:
            raise ValueError('Obligation states must exist in the complete approved plan')
        route = routes['routes'][obligation['id']]
        if set(route) != {'rule_ids', 'reason', 'regression_obligations'} or not isinstance(route['reason'], str) or not route['reason'].strip():
            raise ValueError('Explicit check mapping or unavailable-route rationale required')
        rule_ids = route['rule_ids']
        if len(rule_ids) != len(set(rule_ids)) or not set(rule_ids) <= rules or not set(route['regression_obligations']) <= set(ids):
            raise ValueError('Unknown or duplicate rule/regression obligation')
        cells = [c for c in plan['matrix_contract']['cells'] if c['state'] in selected and c['requirement_id'] in rule_ids]
        applicable = [c['id'] for c in cells if c['disposition'] == 'required']
        missing = sorted(set(selected) - {c['state'] for c in cells}) if rule_ids else sorted(selected)
        # Independent N/A cells stay N/A; all-N/A cannot dispose a MUST clause.
        ready = bool(applicable) and not missing
        row = dict(copy.deepcopy(obligation), assertion_ids=applicable, route_available=ready,
                   missing_states=missing, route=copy.deepcopy(route))
        rows.append(row); owned.update(applicable)
        if ready: checked.add(obligation['id'])
    return {'version': 1, 'design_lock_sha256': lock_sha, 'plan_sha256': design.digest(plan),
            'routes_sha256': routes_sha, 'obligations': rows,
            'must_route_gaps': [o['id'] for o in rows if o['priority'] == 'must' and not o['route_available']],
            'unowned_assertions': sorted(set(plan['required_assertion_ids']) - owned),
            'scope': 'Completeness against the independently approved index, not proof that prose was completely translated or that any check passed.'}


def report_rows(report, plan):
    rows = report.get('rows', report.get('assertions'))
    if not isinstance(rows, list) or len(rows) != len({r['id'] for r in rows}) or {r['id'] for r in rows} != set(plan['required_assertion_ids']):
        raise ValueError('Evaluated report must retain the complete parent plan, including unknown cells')
    if any(r['status'] not in {'passed', 'failed', 'unassessed'} for r in rows):
        raise ValueError('Known evaluated status required')
    return {r['id']: r for r in rows}


def admission(coverage, plan, report, *, execution_scope='full', capture=None, environment=None):
    if design.digest(plan) != coverage['plan_sha256']:
        raise ValueError('Coverage belongs to another parent plan')
    by = report_rows(report, plan)
    results = []
    for o in coverage['obligations']:
        statuses = [by[k]['status'] for k in o['assertion_ids']]
        disposition = ('coverage_gap' if not o['route_available'] else
                       'failed' if 'failed' in statuses else
                       'unverified' if 'unassessed' in statuses else 'passed')
        results.append({'id': o['id'], 'priority': o['priority'], 'status': disposition,
                        'assertion_ids': o['assertion_ids']})
    blockers = [v['id'] for v in results if v['priority'] == 'must' and v['status'] != 'passed']
    bound = bool(capture and capture.get('status') == 'verified_capture' and capture.get('scope') == 'full' and
                 capture.get('parent_plan_sha256') == design.digest(plan) and capture.get('native_exit_code') == 0 and
                 capture.get('source_unchanged') is True and capture.get('inputs_unchanged') is True and capture.get('coverage_satisfied') is True)
    valid_environment = bool(environment and environment.get('status') == 'P')
    return {'status': 'accepted' if execution_scope == 'full' and not blockers and bound and valid_environment else 'not_accepted',
            'execution_scope': execution_scope, 'blocking_obligations': blockers, 'obligations': results,
            'source_bound_full_capture': bound, 'environment_verified': valid_environment,
            'scope': 'Consumes evaluated evidence; does not certify a caller-entered report or subjective observation. Targeted feedback never establishes complete PR acceptance.'}


def route_findings(coverage, plan, report, observation, *, discoveries=(), execution=None):
    from native_checks import bound_state_evidence
    if design.digest(plan) != coverage['plan_sha256']:
        raise ValueError('Coverage belongs to another parent plan')
    rows = report_rows(report, plan); states = {s['id']: s for s in plan['states']}
    selected = set(states); scoped = observation.get('execution_scope') == 'targeted'
    if execution is not None:
        if (execution.get('parent_plan_sha256') != design.digest(plan) or
                execution.get('design_lock_sha256') != coverage['design_lock_sha256']):
            raise ValueError('Execution scope belongs to another independently approved plan')
        selected = set(execution['selected_states'])
        if not selected or not selected <= set(states): raise ValueError('Known nonempty execution-state scope required')
        scoped = execution.get('scope') == 'targeted'
        if scoped == (selected == set(states)): raise ValueError('Declared execution scope contradicts selected states')
    planned = {v['id']: v for v in plan['assertions']}; tasks = []
    for obligation in coverage['obligations']:
        if not obligation['route_available']:
            tasks.append({'obligation_id': obligation['id'], 'action': 'repair_contract_route', 'assertion_ids': [],
                          'priority': obligation['priority'], 'reason': 'Approved source obligation lacks applicable verification coverage'})
            continue
        for rid in obligation['assertion_ids']:
            row = rows[rid]
            if row['status'] == 'passed': continue
            if row['status'] == 'unassessed' and scoped:
                if execution is None:
                    action, why = 'validate_execution_scope', 'Targeted observation needs its verified manifest before missing-state diagnosis'
                elif row['state'] not in selected:
                    action, why = 'defer_to_full_verification', 'State deliberately outside this targeted capture; not a new locator or capability failure'
                else: action = why = None
                if action:
                    tasks.append({'obligation_id': obligation['id'], 'priority': obligation['priority'], 'action': action,
                                  'assertion_ids': [rid], 'state': row['state'], 'risk': obligation['risk'],
                                  'status': row['status'], 'reason': why})
                    continue
            rule = planned[rid]; found, complete, reason, _ = bound_state_evidence(observation, states[rule['state']])
            if report.get('environment', {}).get('status', 'P') != 'P': action = 'repair_environment'
            elif row.get('panel_disagreement'): action = 'clarify_oracle'
            elif row.get('measurement_calibration', {}).get('classification') in {'boundary_overlap', 'outside_calibrated_scope'}: action = 'review_calibrated_measurement'
            elif not found or (states[rule['state']].get('coverage') == 'full_content' and not complete): action = 'acquire_evidence'
            elif row['status'] == 'failed':
                owner = row.get('responsibility', 'component')
                cause = row.get('cause_category')
                action = ('repair_environment' if owner in {'host', 'system'} or cause in {'infrastructure', 'system'} else
                          'diagnose_product' if cause in {None, 'product'} else 'investigate_attribution')
            elif rule['kind'] == 'manual': action = 'review_measurement_or_visual'
            else: action = 'investigate_capability_or_locator'
            tasks.append({'obligation_id': obligation['id'], 'priority': obligation['priority'], 'action': action,
                          'assertion_ids': [rid], 'state': rule['state'], 'risk': obligation['risk'],
                          'status': row['status'], 'reason': row.get('reason', reason)})
    obligations = {o['id']: o for o in coverage['obligations']}
    for discovery in discoveries:
        if set(discovery) != {'obligation_id', 'reason', 'evidence'} or not discovery['reason'].strip() or not discovery['evidence']:
            raise ValueError('Original discovery needs a source obligation, rationale and original evidence references')
        oid = discovery['obligation_id']; known = obligations.get(oid)
        tasks.append({'obligation_id': oid, 'priority': known['priority'] if known else 'unresolved',
                      'action': 'repair_contract_route' if known and not known['route_available'] else 'review_original_discovery',
                      'assertion_ids': [], 'original': copy.deepcopy(discovery),
                      'scope': 'No retrospective TP/FP or cross-state detection credit is generated'})
    return {'version': 1, 'plan_sha256': coverage['plan_sha256'], 'tasks': tasks,
            'execution_scope': execution['scope'] if execution else 'targeted_scope_unverified' if scoped else 'parent_plan',
            'deferred_assertions': sorted({rid for task in tasks if task['action'] == 'defer_to_full_verification' for rid in task['assertion_ids']}),
            'scope': 'Next actions, not extra observations or automatic root-cause truth. A strict failure still needs source diagnosis.'}


def main():
    p = argparse.ArgumentParser(); p.add_argument('command', choices=['audit', 'route', 'admit'])
    for name in ['plan', 'design-lock', 'routes', 'output']: p.add_argument('--' + name, type=Path, required=True)
    for name in ['design-sha256', 'routes-sha256']: p.add_argument('--' + name, required=True)
    p.add_argument('--report', type=Path); p.add_argument('--observation', type=Path); p.add_argument('--discoveries', type=Path)
    p.add_argument('--capture-result', type=Path); p.add_argument('--capture-result-sha256')
    p.add_argument('--environment', type=Path); p.add_argument('--environment-sha256')
    p.add_argument('--execution', type=Path); p.add_argument('--fixtures', type=Path); p.add_argument('--bridge', type=Path)
    p.add_argument('--scope', choices=['full', 'targeted'], default='full'); a = p.parse_args()
    plan = design.load(a.plan); cov = audit(design.load(a.design_lock), a.design_sha256, plan, design.load(a.routes), a.routes_sha256)
    if a.command == 'audit': result = cov
    elif a.command == 'admit':
        capture = env = None
        if a.capture_result:
            import hashlib
            import acceptance
            if hashlib.sha256(a.capture_result.read_bytes()).hexdigest() != a.capture_result_sha256:
                raise ValueError('Independently retained capture-result digest required')
            capture = design.load(a.capture_result)
            if not a.environment or design.digest(design.load(a.environment)) != a.environment_sha256:
                raise ValueError('Independently approved native environment required')
            op = a.capture_result.parent / 'native/observation.json'
            if hashlib.sha256(op.read_bytes()).hexdigest() != capture.get('observation_sha256') or hashlib.sha256(a.report.read_bytes()).hexdigest() != capture.get('automatic_sha256'):
                raise ValueError('Original native observation or automatic report differs from capture receipt')
            env = acceptance.environment(design.load(op), design.load(a.environment), plan['design_contract']['platform'])
        result = admission(cov, plan, design.load(a.report), execution_scope=a.scope, capture=capture, environment=env)
    else:
        execution = None
        if a.execution:
            import execution_plan
            import hashlib
            if not a.fixtures or not a.bridge: raise ValueError('Original approved fixture/bridge required to verify execution scope')
            execution = design.load(a.execution)
            execution_plan.verify_execution(execution, plan, design.load(a.design_lock), a.design_sha256,
                                            design.load(a.fixtures), hashlib.sha256(a.bridge.read_bytes()).hexdigest())
        result = route_findings(cov, plan, design.load(a.report), design.load(a.observation), discoveries=design.load(a.discoveries) if a.discoveries else [], execution=execution)
    with a.output.open('x') as stream: stream.write(__import__('json').dumps(result, indent=2, ensure_ascii=False) + '\n')
if __name__ == '__main__': main()
