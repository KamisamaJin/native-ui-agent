#!/usr/bin/env python3
"""Default non-optional route -> diagnose -> plan -> execute -> route chain.

The project integration supplies approved inputs and native launch options once.
The agent supplies neither assertion IDs, expected values nor selected states.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import time
from pathlib import Path
import design_contract as d
import execution_plan as xp
import native_checks
import requirement_routes as routes
import retest_plan
import locator_diagnostics


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path, value):
    with Path(path).open('x') as stream: stream.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def load_previous(path, expected_sha, plan, lock, lock_sha, fixtures, bridge, roots, policy=None, policy_sha=None, adoption=None):
    path = Path(path).resolve(); base = path.parent
    if sha(path) != expected_sha: raise ValueError('Pinned previous receipt changed')
    receipt = d.load(path)
    if receipt.get('source_unchanged') is not True or receipt.get('inputs_unchanged') is not True:
        raise ValueError('Source/input drift cannot supply retest evidence')
    if receipt.get('parent_plan_sha256') != d.digest(plan): raise ValueError('Foreign previous parent plan')
    actual_roots = [str(Path(v).resolve()) for v in roots]
    if receipt.get('source_roots') != actual_roots:
        if not adoption or sha(adoption['path']) != adoption['sha256']: raise ValueError('Foreign source namespace without pinned clone adoption')
        ticket = d.load(Path(adoption['path']))
        if ticket.get('original_receipt_sha256') != expected_sha or ticket.get('new_source_roots') != actual_roots or ticket.get('source_sha256') != receipt['source_sha256']:
            raise ValueError('Clone adoption differs from original source identity')
    before = d.load(base / 'source-before.json')
    if before != d.load(base / 'source-after.json') or d.digest(before) != receipt['source_sha256']: raise ValueError('Previous source map drift')
    execution = d.load(base / 'execution.json')
    xp.verify_execution(execution, plan, lock, lock_sha, fixtures, sha(bridge))
    if receipt.get('execution_sha256') != execution['execution_sha256']: raise ValueError('Foreign execution receipt')
    for name in ['fixtures.json', 'actions.json']:
        if sha(base / name) != receipt.get('input_hashes', {}).get(name): raise ValueError('Previous launch bytes changed')
    op = base / 'native/observation.json'
    if not op.is_file():
        if receipt.get('automatic_sha256') or receipt.get('observation_sha256'): raise ValueError('Missing pinned original evidence')
        report = {'rows': [{'id': r['id'], 'state': r['state'], 'status': 'unassessed', 'reason': 'Original native acquisition produced no packet'} for r in plan['assertions']]}
        return before, report, {}, execution, receipt
    if receipt.get('evidence_error'):
        if sha(op) != receipt.get('observation_sha256'): raise ValueError('Original incomplete packet changed')
        for relative, expected in receipt.get('image_hashes', {}).items():
            image = (op.parent / relative).resolve()
            if not image.is_relative_to(op.parent) or sha(image) != expected: raise ValueError('Incomplete packet image changed')
        report = {'rows': [{'id': r['id'], 'state': r['state'], 'status': 'unassessed', 'reason': 'Incomplete original packet: ' + receipt['evidence_error']['message']} for r in plan['assertions']]}
        return before, report, {}, execution, receipt
    if sha(op) != receipt.get('observation_sha256') or sha(base / 'automatic.json') != receipt.get('automatic_sha256'):
        raise ValueError('Original evidence/report changed')
    xp.verify_capture_images(receipt, op.parent)
    observation = d.load(op); manual = None
    if policy is not None:
        import review_contract as review
        catalog = review.catalog(plan, lock, lock_sha, policy, policy_sha, plan['design_contract']['platform'])
        manual = review.bind(plan, lock, lock_sha, policy, policy_sha, observation, sha(op), op.parent,
                             {'version': 1, 'catalog_sha256': d.digest(catalog), 'observation_sha256': sha(op), 'decisions': []}, plan['design_contract']['platform'])
    report = native_checks.evaluate(plan, observation, plan['design_contract']['platform'], manual, op.parent, sha(op), lock, lock_sha, policy, policy_sha)
    if (base / 'environment-check.json').is_file(): report['environment'] = d.load(base / 'environment-check.json')
    if report != d.load(base / 'automatic.json'): raise ValueError('Previous automatic report does not reproduce')
    return before, report, observation, execution, receipt


def run_cycle(config, output, *, previous=None, previous_sha=None, final=False, history=(), intake=False):
    """One default entry point. It is also the integration API for MCP/E2E adapters."""
    output = Path(output).resolve()
    plan, lock, fixtures = (d.load(Path(config[k])) for k in ['plan', 'design_lock', 'fixtures'])
    lock_sha = config['design_sha256']; bridge = Path(config['bridge'])
    route_doc = d.load(Path(config['routes']))
    coverage = routes.audit(lock, lock_sha, plan, route_doc, config['routes_sha256'])
    roots = config['source_roots']; now = xp.source_fingerprint(roots)
    policy = d.load(Path(config['policy'])) if config.get('policy') else None
    policy_sha = config.get('policy_sha256')
    if bool(previous) != bool(previous_sha): raise ValueError('Previous receipt and pinned digest required together')
    trace = []; before = now
    if previous:
        before, report, observation, execution, receipt = load_previous(previous, previous_sha, plan, lock, lock_sha, fixtures, bridge, roots, policy, policy_sha, config.get('adoption'))
        trace.append('reconstruct_original_evidence')
        routed = routes.route_findings(coverage, plan, report, observation, execution=execution)
        diagnostics = locator_diagnostics.diagnose(plan, report, observation, roots, execution['selected_states'])
        trace.extend(['route_findings', 'locator_diagnostics'])
        planning = retest_plan.unresolved(coverage, plan, report, changed_files=sorted(k for k in set(before) | set(now) if before.get(k) != now.get(k)),
                                         source_before=d.digest(before), source_after=d.digest(now), final=final, selected_states=execution['selected_states'])
    else:
        # Initial/final acquisition also records a planner decision, even without
        # an earlier packet. Missing evidence is explicit, not a silent skip.
        report = {'rows': [{'id': r['id'], 'state': r['state'], 'status': 'unassessed', 'reason': 'No previous source-bound evidence'} for r in plan['assertions']]}
        routed = routes.route_findings(coverage, plan, report, {})
        diagnostics = locator_diagnostics.diagnose(plan, report, {}, roots)
        trace.extend(['route_findings', 'locator_diagnostics'])
        planning = retest_plan.unresolved(coverage, plan, report, changed_files=[], source_before=d.digest(now), source_after=d.digest(now), final=True)
    if previous and execution['scope'] == 'targeted':
        planning['states'] = [s['id'] for s in plan['states']]
        planning['reason'] = 'previous capture was partial; full fallback preserves unclosed prior states'
    trace.append('retest_plan.unresolved')
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'coverage.json', coverage); write(output / 'before-routes.json', routed)
    write(output / 'before-diagnostics.json', diagnostics); write(output / 'retest-plan.json', planning)
    signature = d.digest({'source': now, 'plan': d.digest(plan), 'states': planning['states'], 'issues': planning['original_failed_ids'] + planning['original_unknown_ids']})
    # Repeated unchanged-source scans need explicit cause intervention. This is
    # bounded feedback, not automatic acceptance, and final is never cached.
    prior = []
    for item in history:
        hpath = Path(item['path'])
        if sha(hpath) != item['sha256']: raise ValueError('Pinned service history changed')
        h = d.load(hpath)
        if h.get('parent_plan_sha256') != d.digest(plan): raise ValueError('Foreign service history')
        prior.append(h)
    blocked = not final and sum(h.get('signature') == signature and h.get('native_executed') is True for h in prior) >= 2
    started = time.time(); result = None
    if intake and final: raise ValueError('Intake is diagnostic only and cannot be final acceptance')
    if not blocked and not intake:
        value = xp.compile_execution(plan, lock, lock_sha, fixtures, sha(bridge), launch_ref=config['launch_ref'], states=planning['states'])
        trace.append('execution_plan.compile_execution')
        result = xp.run_execution(value, plan, lock, lock_sha, fixtures, bridge, output / 'capture', roots, config['native_options'],
                                  policy=policy, policy_sha=policy_sha, expected_environment=d.load(Path(config['environment'])), environment_sha=config['environment_sha256'])
        trace.append('execution_plan.run_execution')
        if result.get('automatic_sha256') and not result.get('evidence_error'):
            fresh_report = d.load(output / 'capture/automatic.json'); obs = d.load(output / 'capture/native/observation.json')
        else:
            fresh_report = {'rows': [{'id': r['id'], 'state': r['state'], 'status': 'unassessed', 'reason': 'Native acquisition incomplete: ' + str(result.get('evidence_error', result.get('native_exit_code')))} for r in plan['assertions']]}
            obs = {}
        after_route = routes.route_findings(coverage, plan, fresh_report, obs, execution=value)
        after_diag = locator_diagnostics.diagnose(plan, fresh_report, obs, roots, value['selected_states'])
        write(output / 'after-routes.json', after_route); write(output / 'after-diagnostics.json', after_diag)
        env_path = output / 'capture/environment-check.json'
        admission = routes.admission(coverage, plan, fresh_report, execution_scope=value['scope'], capture=result, environment=d.load(env_path) if env_path.is_file() else {'status': 'U'})
        write(output / 'admission.json', admission); trace.extend(['route_findings_after', 'locator_diagnostics_after', 'admission'])
    decision = {'version': 1, 'parent_plan_sha256': d.digest(plan), 'startedAtUnix': started, 'finishedAtUnix': time.time(),
                'signature': signature, 'native_executed': not blocked and not intake, 'trace': trace, 'final': final, 'intake': intake,
                'status': 'intake_open_tasks' if intake else 'blocked_repeated_unchanged_evidence' if blocked else result['status'],
                'capture_result': str(output / 'capture/result.json') if result else None,
                'capture_sha256': sha(output / 'capture/result.json') if result else None,
                'scope': 'Default execution enforces tool invocation. Missing evidence remains open; final admission still requires full fresh evidence. Native evidence does not establish independent product quality.'}
    write(output / 'cycle.json', decision)
    return decision


def adopt_capture(receipt_path, receipt_sha, roots, output):
    """Integration-only handoff: prove identical clone bytes before any edit.

    This writes a new pinned identity ticket; it never alters the original
    acquisition receipt, source maps, screenshots or verdicts.
    """
    path = Path(receipt_path).resolve()
    if sha(path) != receipt_sha: raise ValueError('Original receipt changed')
    receipt = d.load(path); before = d.load(path.parent / 'source-before.json')
    if (not receipt.get('source_unchanged') or before != d.load(path.parent / 'source-after.json') or
            d.digest(before) != receipt['source_sha256'] or xp.source_fingerprint(roots) != before):
        raise ValueError('Clone must match original captured production bytes before edits')
    value = {'version': 1, 'original_receipt_sha256': receipt_sha, 'source_sha256': d.digest(before),
             'new_source_roots': [str(Path(v).resolve()) for v in roots], 'adoptedAtUnix': time.time(),
             'scope': 'Identical source clone handoff only; no new native execution or validation credit.'}
    write(output, value); return value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--previous', type=Path); p.add_argument('--previous-sha256'); p.add_argument('--final', action='store_true')
    p.add_argument('--intake', action='store_true', help='Mandatory integration handoff diagnosis; no acceptance or native capture')
    p.add_argument('--history', type=Path, help='Pinned prior cycle list: path and sha256, retained by the integration')
    a = p.parse_args()
    result = run_cycle(d.load(a.config), a.output, previous=a.previous, previous_sha=a.previous_sha256, final=a.final,
                       history=d.load(a.history) if a.history else [], intake=a.intake)
    print(json.dumps(result, indent=2))
if __name__ == '__main__': main()
