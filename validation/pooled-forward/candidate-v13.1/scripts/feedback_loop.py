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


def load_previous(path, expected_sha, plan, lock, lock_sha, fixtures, bridge, roots, policy=None, policy_sha=None, adoption=None, source_config=None):
    path = Path(path).resolve(); base = path.parent
    if sha(path) != expected_sha: raise ValueError('Pinned previous receipt changed')
    receipt = d.load(path)
    if receipt.get('packet_files') is not None: xp.verify_packet_files(receipt, base)
    if receipt.get('source_unchanged') is not True or receipt.get('inputs_unchanged') is not True:
        raise ValueError('Source/input drift cannot supply retest evidence')
    if receipt.get('parent_plan_sha256') != d.digest(plan): raise ValueError('Foreign previous parent plan')
    if source_config is not None:
        import source_identity
        source_identity.verify_model(source_config, receipt, base, plan['design_contract']['platform'])
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


def review_methods(config, plan, lock):
    if not config.get('policy'): return set()
    import review_contract
    cat = review_contract.catalog(plan, lock, config['design_sha256'], d.load(Path(config['policy'])), config['policy_sha256'], plan['design_contract']['platform'])
    return {v['id'] for v in cat['rows'] if v['method'] == 'visual'}


def calibrated(config, plan, observation, report):
    if not config.get('calibration'): return report
    import ax_calibration
    ref = config['calibration']; path = Path(ref['path'])
    if sha(path) != ref['sha256']: raise ValueError('Pinned calibration profile changed')
    return ax_calibration.annotate(plan, observation, report, d.load(path))


def run_cycle(config, output, *, previous=None, previous_sha=None, final=False, history=(), intake=False, review_result=None, force_native=False):
    import workflow_state
    return workflow_state.run_cycle(config, output, previous=previous, previous_sha=previous_sha, final=final,
                history=history, intake=intake, review_result=review_result, force_native=force_native)


def _managed_cycle(config, output, *, previous=None, previous_sha=None, final=False, history=(), intake=False, review_result=None, reuse_proof=None, capture_context=None, force_native=False):
    from resource_manager import Resources
    output=Path(output).resolve()
    if output.exists()or any(output==Path(r).resolve()or output.is_relative_to(Path(r).resolve())for r in config['source_roots']):
        raise ValueError('Fresh default-cycle output outside production source required')
    resources=Resources(config,output,final=final)
    try:
        with resources:
            result = _run_cycle(config, output, previous=previous, previous_sha=previous_sha, final=final,
                                history=history, intake=intake, review_result=review_result, resources=resources,
                                reuse_proof=reuse_proof, capture_context=capture_context, force_native=force_native)
            if capture_context is not None:
                import capture_validity
                if capture_validity.context(config, capture_context['platform']) != capture_context:
                    raise ValueError('Native execution context changed during the cycle')
    except BaseException as error:
        # No accepted cycle is published before resource finalization succeeds.
        root=Path(output);root.mkdir(parents=True,exist_ok=True)
        path=root/'service-error.json'
        if not path.exists():write(path,{'type':type(error).__name__,'message':str(error),'at_unix':time.time(),'status':'not_accepted'})
        raise
    result['controllerFinishedAtUnix']=result['finishedAtUnix'];result['finishedAtUnix']=time.time()
    result['resources_sha256']=sha(Path(output)/'resources.json')
    write(Path(output)/'cycle.json',result)
    return result


def _run_cycle(config, output, *, previous=None, previous_sha=None, final=False, history=(), intake=False, review_result=None, resources=None, reuse_proof=None, capture_context=None, force_native=False):
    import evidence_review
    import evidence_responsibility as er
    output = Path(output).resolve()
    plan, lock, fixtures = (d.load(Path(config[k])) for k in ['plan', 'design_lock', 'fixtures'])
    lock_sha = config['design_sha256']; bridge = Path(config['bridge']); roots = config['source_roots']
    coverage = routes.audit(lock, lock_sha, plan, d.load(Path(config['routes'])), config['routes_sha256'])
    import source_identity
    source_model = source_identity.model(config, plan['design_contract']['platform'])
    now = source_identity.fingerprint(config, plan['design_contract']['platform']); before = now; started = time.time(); trace = []
    responsibility = er.compile_contract(config, plan, lock)
    trace.append('evidence_responsibility.compile_contract')
    if bool(previous) != bool(previous_sha): raise ValueError('Previous receipt and digest required together')
    if review_result and not previous: raise ValueError('Review requires its original capture')
    policy = d.load(Path(config['policy'])) if config.get('policy') else None
    visual = review_methods(config, plan, lock)
    if visual and not config.get('review_store'):raise ValueError('Default visual workflow requires an integration-owned append-only review_store')
    if config.get('review_store')and any(Path(config['review_store']).resolve().is_relative_to(Path(root).resolve())for root in roots):raise ValueError('Review store must be outside production roots')
    available = False; execution = None; receipt = None; observation = {}
    if previous:
        before, report, observation, execution, receipt = load_previous(previous, previous_sha, plan, lock, lock_sha, fixtures, bridge, roots, policy, config.get('policy_sha256'), config.get('adoption'), config)
        trace.append('reconstruct_original_evidence'); available = bool(observation)
        registered=evidence_review.discover(config,previous_sha)
        if registered:
            if review_result and {v['sha256']for v in (review_result if isinstance(review_result,list)else[review_result])}!={v['sha256']for v in registered}:raise ValueError('Explicit review cannot bypass current registry heads')
            review_result=registered
        if review_result:
            report = evidence_review.reconstruct(config, previous, previous_sha, review_result)
            trace.append('reconstruct_bound_review')
    else:
        report = {'rows': [{'id':r['id'],'state':r['state'],'status':'unassessed','reason':'No original source-bound packet'}for r in plan['assertions']]}
    report = calibrated(config, plan, observation, report)
    routed = routes.route_findings(coverage, plan, report, observation, execution=execution)
    selected = execution['selected_states'] if execution else None
    diagnostics = locator_diagnostics.diagnose(plan, report, observation, roots, selected)
    trace.extend(['route_findings', 'locator_diagnostics'])
    planning = retest_plan.dispatch(coverage, plan, report, routed, changed_files=sorted(k for k in set(before)|set(now) if before.get(k)!=now.get(k)),
                    source_before=d.digest(before), source_after=d.digest(now), final=final, selected_states=selected, visual_ids=visual, capture_available=available)
    trace.append('retest_plan.dispatch')
    if intake and force_native: raise ValueError('Diagnostic intake and explicit fresh acquisition are distinct work')
    if force_native:
        planning = dict(planning, states=[s['id'] for s in plan['states']], status='capture_required',
                        reason='Explicit fresh full native packet requested')
    incompatible = [i for i in responsibility['issues'] if i['priority'] == 'must']
    if incompatible:
        planning = dict(planning, status='blocked_evidence_responsibility', states=[],
                        responsibility_issues=incompatible)
    if intake and final: raise ValueError('Diagnostic intake cannot be final')
    output.mkdir(parents=True, exist_ok=False)
    for name,value in [('coverage.json',coverage),('before-evaluated.json',report),('before-routes.json',routed),('before-diagnostics.json',diagnostics),('retest-plan.json',planning)]: write(output/name,value)
    write(output/'evidence-responsibility.json', responsibility)
    write(output/'source-review-template.json', er.template(responsibility))
    request = evidence_review.requests(config, previous, previous_sha, report) if previous and available and d.digest(before)==d.digest(now) else None
    if request: write(output/'review-request.json',request)
    signature = d.digest({'source':now,'plan':d.digest(plan),'states':planning['states'],
                          'failed':planning['original_failed_ids'],'unknown':planning['original_unknown_ids']})
    prior = []
    for item in history:
        path=Path(item['path'])
        if sha(path)!=item['sha256']:raise ValueError('Pinned history changed')
        h=d.load(path)
        if h.get('parent_plan_sha256')!=d.digest(plan):raise ValueError('Foreign history')
        prior.append(h)
    blocked=not final and not intake and not force_native and sum(h.get('signature')==signature and not h.get('intake') for h in prior)>=2
    result=None; value=None
    reused = bool(reuse_proof and reuse_proof.get('eligible'))
    if reused:
        import capture_validity
        original_context = d.load(Path(previous).parent / 'capture-context.json')
        reuse_proof = capture_validity.assess(config, previous, previous_sha, captured_context=original_context)
        reused = bool(reuse_proof['eligible'] and before == now and final and not incompatible)
    execute=bool(planning['states']) and not intake and not blocked and not reused
    status='blocked_repeated_unchanged_evidence'if blocked else planning['status']
    if execute or reused:
        if execute:
            value=xp.compile_execution(plan,lock,lock_sha,fixtures,sha(bridge),launch_ref=config['launch_ref'],states=planning['states'])
            trace.append('execution_plan.compile_execution')
            result=xp.run_execution(value,plan,lock,lock_sha,fixtures,bridge,output/'capture',roots,config['native_options'],
                     policy=policy,policy_sha=config.get('policy_sha256'),expected_environment=d.load(Path(config['environment'])),environment_sha=config['environment_sha256'],resources=resources,
                     source_model=source_model, capture_context=capture_context)
            trace.append('execution_plan.run_execution')
            if result.get('automatic_sha256') and not result.get('evidence_error'):
                report=d.load(output/'capture/automatic.json');observation=d.load(output/'capture/native/observation.json')
            else:
                report={'rows':[{'id':r['id'],'state':r['state'],'status':'unassessed','reason':'Native acquisition incomplete'}for r in plan['assertions']]};observation={}
        else:
            value=execution; result=receipt
            trace.append('adopt_original_full_capture')
        report=calibrated(config,plan,observation,report)
        after=routes.route_findings(coverage,plan,report,observation,execution=value)
        after_diag=locator_diagnostics.diagnose(plan,report,observation,roots,value['selected_states'])
        write(output/'after-evaluated.json',report);write(output/'after-routes.json',after);write(output/'after-diagnostics.json',after_diag)
        trace.extend(['route_findings_after','locator_diagnostics_after'])
        request=None
        if observation:
            cp=output/'capture/result.json' if execute else Path(previous)
            request=evidence_review.requests(config,cp,sha(cp),report)
            if request:write(output/'after-review-request.json',request)
        import acceptance
        env=acceptance.environment(observation,d.load(Path(config['environment'])),value['platform']) if observation else {'status':'U'}
        admitted=routes.admission(coverage,plan,report,execution_scope=value['scope'],capture=result,environment=env)
        responsibilities = er.evaluate(config, responsibility, report)
        admitted['evidence_responsibility'] = responsibilities
        if responsibilities['blocking_claims']: admitted['status'] = 'not_accepted'
        write(output/'admission.json',admitted);trace.append('admission')
        post=retest_plan.dispatch(coverage,plan,report,after,changed_files=[],source_before=d.digest(now),source_after=d.digest(now),selected_states=value['selected_states'],visual_ids=visual,capture_available=bool(observation))
        write(output/'after-dispatch.json',post);trace.append('retest_plan.dispatch_after')
        status='accepted'if final and admitted['status']=='accepted'else post['status']
    responsibilities = er.evaluate(config, responsibility, report)
    write(output/'responsibility-results.json', responsibilities)
    source_tasks = [r for r in responsibilities['rows'] if r['method'] == 'source' and r['status'] != 'passed']
    if source_tasks and not incompatible and status in {'accepted', 'feedback_complete', 'awaiting_full_final'}:
        status = 'review_source' if all(r['status'] == 'unassessed' for r in source_tasks) else 'repair_source'
    decision={'version':2,'parent_plan_sha256':d.digest(plan),'startedAtUnix':started,'finishedAtUnix':time.time(),
              'signature':signature,'native_executed':execute,'trace':trace,'final':final,'intake':intake,'status':status,
              'capture_result':str(output/'capture/result.json')if execute else(str(Path(previous).resolve())if reused else None),
              'capture_sha256':sha(output/'capture/result.json')if execute else(previous_sha if reused else None),
              'capture_reused':reused,'capture_reuse':reuse_proof if reused else None,
              'review_result':review_result,'source_sha256':d.digest(now),'review_current_source':bool(review_result and d.digest(before)==d.digest(now)),
              'evidence_responsibility':responsibilities, 'source_tasks':source_tasks,
              'scope':'Work-kind dispatch is mandatory. Historical reviews guide scope only; current acceptance requires fresh full-final native evidence plus exact bound actuals.'}
    return decision


def complete_review(config, cycle_path, cycle_sha, review_result, output):
    import evidence_review,acceptance,evidence_responsibility as er
    cycle_path=Path(cycle_path).resolve()
    if sha(cycle_path)!=cycle_sha:raise ValueError('Pinned final cycle changed')
    cycle=d.load(cycle_path)
    if not cycle.get('final') or not (cycle.get('native_executed') or cycle.get('capture_reused')):raise ValueError('Only a completed full final native or verified adoption cycle can establish delivery acceptance')
    resource_path=cycle_path.parent/'resources.json'
    if cycle.get('resources_sha256'):
        if sha(resource_path)!=cycle['resources_sha256']:raise ValueError('Final managed resource receipt changed')
        resource=d.load(resource_path)
        if resource['cleanup_errors']or resource['remaining_devices']or resource['remaining_directories']:
            raise ValueError('Final owned resource cleanup incomplete; delivery cannot be accepted')
    capture=Path(cycle['capture_result']) if cycle.get('capture_result') else cycle_path.parent/'capture/result.json'
    if sha(capture)!=cycle['capture_sha256']:raise ValueError('Final capture changed')
    plan,lock,policy,packet=evidence_review.original(config,capture,cycle['capture_sha256'])
    before,original_report,observation,execution,receipt=packet
    import source_identity
    if source_identity.receipt_fingerprint(config['source_roots'],receipt.get('source_model'))!=before:raise ValueError('Review of old source cannot accept edited source')
    if cycle.get('capture_reused'):
        import capture_validity
        context=d.load(capture.parent/'capture-context.json')
        proof=capture_validity.assess(config,capture,cycle['capture_sha256'],captured_context=context)
        if not proof['eligible'] or cycle['capture_reuse']['context_sha256'] != proof['context_sha256']:
            raise ValueError('Original adopted packet is no longer current or valid')
    registered=evidence_review.discover(config,cycle['capture_sha256'])
    if registered:
        if review_result and {v['sha256']for v in (review_result if isinstance(review_result,list)else[review_result])}!={v['sha256']for v in registered}:raise ValueError('Final review cannot bypass registry heads')
        review_result=registered
    if not review_result and review_methods(config,plan,lock):
        raise ValueError('Original final review actuals are still queued')
    if review_result:
        report=evidence_review.reconstruct(config,capture,cycle['capture_sha256'],review_result)
        review_trace='reconstruct_bound_review'
    else:
        report=original_report
        review_trace='reconstruct_native_source_evidence'
    report=calibrated(config,plan,observation,report)
    cov=routes.audit(lock,config['design_sha256'],plan,d.load(Path(config['routes'])),config['routes_sha256'])
    routed=routes.route_findings(cov,plan,report,observation,execution=execution)
    planning=retest_plan.dispatch(cov,plan,report,routed,changed_files=[],source_before=d.digest(before),source_after=d.digest(before),selected_states=execution['selected_states'],visual_ids=review_methods(config,plan,lock))
    env=acceptance.environment(observation,d.load(Path(config['environment'])),execution['platform'])
    admitted=routes.admission(cov,plan,report,execution_scope=execution['scope'],capture=receipt,environment=env)
    responsibility = er.compile_contract(config, plan, lock)
    admitted['evidence_responsibility'] = er.evaluate(config, responsibility, report)
    if admitted['evidence_responsibility']['blocking_claims']: admitted['status'] = 'not_accepted'
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    for name,value in [('evaluated.json',report),('routes.json',routed),('retest-plan.json',planning),('admission.json',admitted)]:write(output/name,value)
    result={'version':1,'status':admitted['status'],'final_cycle_sha256':cycle_sha,'review_result':review_result,'source_sha256':d.digest(before),
            'finishedAtUnix':time.time(),'native_executed':False,'trace':[review_trace,'route_findings','retest_plan.dispatch','admission'],
            'scope':'Original final native evidence and required current source/image reviews; no SDK execution, expected override or edited-source acceptance.'}
    write(output/'completion.json',result);return result


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
    p.add_argument('--fresh', action='store_true')
    p.add_argument('--review-result',type=Path);p.add_argument('--review-result-sha256')
    p.add_argument('--intake', action='store_true', help='Mandatory integration handoff diagnosis; no acceptance or native capture')
    p.add_argument('--history', type=Path, help='Pinned prior cycle list: path and sha256, retained by the integration')
    a = p.parse_args()
    result = run_cycle(d.load(a.config), a.output, previous=a.previous, previous_sha=a.previous_sha256, final=a.final,
                       history=d.load(a.history) if a.history else [], intake=a.intake, review_result={'path':str(a.review_result),'sha256':a.review_result_sha256}if a.review_result else None, force_native=a.fresh)
    print(json.dumps(result, indent=2))
if __name__ == '__main__': main()
