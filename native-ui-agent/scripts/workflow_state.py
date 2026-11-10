"""Default per-platform repair/capture state; agents never assemble previous paths."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

import capture_validity as validity
import design_contract as d
import execution_plan as xp
import source_identity


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        f.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
        f.flush(); os.fsync(f.fileno())


def reference(path):
    return {'path': str(Path(path).resolve()), 'sha256': validity.sha(path)}


def read_ref(ref):
    path = Path(ref['path'])
    if validity.sha(path) != ref['sha256']:
        raise ValueError('Pinned workflow artifact changed: ' + str(path))
    return d.load(path)


def capture_handle(path, expected):
    ref = {'path': str(Path(path).resolve()), 'sha256': expected}
    value = read_ref(ref)
    if 'capture_result' in value:
        if not value.get('capture_result') or not value.get('capture_sha256'):
            raise ValueError('Cycle has no original native capture handle')
        ref = {'path': value['capture_result'], 'sha256': value['capture_sha256']}
        value = read_ref(ref)
    elif value.get('kind') == 'native_workflow_handoff':
        ref = value['capture']; value = read_ref(ref)
    if not value.get('parent_plan_sha256') or 'source_unchanged' not in value:
        raise ValueError('Typed original native capture receipt required')
    return ref


class Session:
    def __init__(self, config, output):
        self.config = config; self.output = Path(output).resolve()
        self.platform = d.load(Path(config['plan']))['design_contract']['platform']
        options = config.get('workflow', {})
        if not isinstance(options, dict) or set(options) - {'root', 'max_cycles'}:
            raise ValueError('Known bounded workflow policy required')
        resource = Path(config.get('resources', {}).get('root', self.output.parent / 'cache/native-ui-resources'))
        from resource_manager import no_symlinks
        self.root = no_symlinks(options.get('root', resource.with_name(resource.name + '-workflow')))
        roots = [Path(p).resolve() for p in config['source_roots']]
        if any(self.root == p or self.root.is_relative_to(p) or p.is_relative_to(self.root) for p in roots + [self.output]):
            raise ValueError('Workflow state must be disjoint from production and original evidence')
        self.owner = d.digest(list(map(str, roots)))
        self.max_cycles = options.get('max_cycles', 30)
        if type(self.max_cycles) is not int or not 1 <= self.max_cycles <= 100:
            raise ValueError('Bounded workflow cycle count required')

    def __enter__(self):
        created = False
        try: self.root.mkdir(parents=True, exist_ok=False); created = True
        except FileExistsError: pass
        marker = self.root / 'owner.json'
        actual = {'format': 'native-ui-workflow-v1', 'owner': self.owner,
                  'root_identity': {'device': self.root.stat().st_dev, 'inode': self.root.stat().st_ino}}
        if created: save(marker, actual)
        if d.load(marker) != actual:
            raise ValueError('Workflow root ownership or inode changed')
        self.stream = (self.root / (self.platform + '.lock')).open('a')
        try: fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.stream.close(); raise RuntimeError('This platform workflow is already active')
        try:
            states = []
            for name in [self.platform + '.json', self.platform + '-backup.json']:
                p = self.root / name
                if p.is_file():
                    try:
                        value = d.load(p)
                        if value.get('owner') != self.owner or value.get('platform') != self.platform:
                            raise ValueError('Foreign workflow checkpoint')
                        states.append(value)
                    except (ValueError, KeyError):
                        continue
            if not states and any((self.root / n).exists() for n in [self.platform + '.json', self.platform + '-backup.json']):
                raise ValueError('No valid workflow checkpoint; original files retained')
            self.state = max(states, key=lambda v: v['generation']) if states else {
                'version': 1, 'owner': self.owner, 'platform': self.platform, 'generation': 0,
                'cycles': [], 'capture': None, 'task': None, 'completion': None}
            self.recover_publish()
            self.context = validity.context(self.config, self.platform)
            self.context_sha = d.digest(self.context)
            return self
        except BaseException:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN); self.stream.close(); raise

    def checkpoint(self):
        self.state['generation'] += 1
        for name in [self.platform + '-backup.json', self.platform + '.json']:
            p = self.root / (uuid.uuid4().hex + '.tmp')
            save(p, self.state); os.replace(p, self.root / name)

    def recover_publish(self):
        transaction = self.state.get('pending_publish')
        if not transaction: return
        payload = Path(transaction['payload']['path'])
        cycle = Path(transaction['cycle']['path'])
        if payload.name != 'cycle-payload.json' or cycle != payload.with_name('cycle.json'):
            raise ValueError('Invalid owned workflow publication namespace')
        if any(cycle.is_relative_to(Path(r).resolve()) for r in self.config['source_roots']):
            raise ValueError('Workflow publication cannot write production')
        read_ref(transaction['payload'])
        for ref in transaction['files']: read_ref(ref)
        if transaction.get('capture'):
            receipt = read_ref(transaction['capture'])
            if receipt.get('packet_files'): xp.verify_packet_files(receipt, Path(transaction['capture']['path']).parent)
        if transaction['payload']['sha256'] != transaction['cycle']['sha256']:
            raise ValueError('Workflow publication payload differs from original cycle')
        if cycle.exists():
            read_ref(transaction['cycle'])
        else:
            with cycle.open('xb') as f:
                f.write(payload.read_bytes()); f.flush(); os.fsync(f.fileno())
        self.state.pop('pending_publish'); self.checkpoint()

    def complete(self, task_ref, *, explicit=False):
        if self.state.get('task') != task_ref:
            raise ValueError('Repair task is foreign, stale or already completed')
        task = read_ref(task_ref)
        read_ref(task['capture'])
        if task['context_sha256'] != self.context_sha:
            raise ValueError('Oracle/bridge/tool/environment changed during a source repair')
        now = source_identity.fingerprint(self.config, self.platform)
        before = task['source_map']
        prior = read_ref(self.state['completion']) if self.state.get('completion') else None
        if prior and prior['context_sha256'] != self.context_sha:
            raise ValueError('Pending native retest context changed; independent new-scope admission is required')
        if prior and prior['task'] == task_ref and prior['source_after_sha256'] == d.digest(now):
            raise ValueError('Repair completion already recorded; native retest is still pending')
        if prior and prior['task'] == task_ref:
            before = prior.get('source_after_map', before)
        changed = sorted(k for k in set(before) | set(now) if before.get(k) != now.get(k))
        if not changed:
            raise ValueError('Claimed repair has no actual platform source change')
        from resource_manager import lease_clock, boot_identity
        value = {'version': 1, 'status': 'patched_needs_native_retest', 'task': task_ref,
                 'capture': task['capture'], 'context_sha256': self.context_sha,
                 'source_before_sha256': d.digest(before), 'source_after_sha256': d.digest(now),
                 'source_after_map': now, 'origin_source_sha256': d.digest(task['source_map']),
                 'measured_changed_files': changed, 'at_unix': time.time(), 'explicit_worker_completion': explicit,
                 'submittedLeaseClock': lease_clock(), 'host_boot_id': boot_identity(),
                 'previous_completion': self.state.get('completion'),
                 'scope': 'Measured patch handoff only, not a repaired-product or test-pass claim.'}
        target = self.root / 'completions' / (uuid.uuid4().hex + '.json')
        save(target, value); self.state['completion'] = reference(target); self.checkpoint()
        return value

    def __exit__(self, *args):
        fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN); self.stream.close()


def run_cycle(config, output, *, previous=None, previous_sha=None, final=False, history=(), intake=False, review_result=None, force_native=False):
    import feedback_loop as loop
    output = Path(output).resolve()
    if output.exists(): raise ValueError('Fresh default-cycle output required')
    # Invalid legacy inputs still reach the original validation/error/cleanup
    # path; a real execution cannot proceed without its plan.
    if 'plan' not in config:
        return loop._managed_cycle(config, output, previous=previous, previous_sha=previous_sha, final=final,
                                   history=history, intake=intake, review_result=review_result)
    with Session(config, output) as session:
        if len(session.state['cycles']) >= session.max_cycles:
            raise RuntimeError('Workflow cycle budget exhausted; explicit owned cleanup required')
        if bool(previous) != bool(previous_sha): raise ValueError('Previous receipt and digest required together')
        handle = capture_handle(previous, previous_sha) if previous else None
        captured_context = None
        registered = session.state.get('capture')
        if registered:
            read_ref(registered['cycle'])
            if registered['context_sha256'] == session.context_sha:
                if handle is None: handle = registered['capture']
                if handle == registered['capture']:
                    captured_context = read_ref(registered['context'])
        patch = None
        pending = read_ref(session.state['completion']) if session.state.get('completion') else None
        if pending and pending['context_sha256'] != session.context_sha:
            raise ValueError('Pending native retest oracle/bridge/environment changed; independent new-scope admission is required')
        if session.state.get('task'):
            task = read_ref(session.state['task'])
            if task['context_sha256'] != session.context_sha:
                raise ValueError('Open repair oracle/bridge/environment changed; independent new-scope admission is required')
            current = source_identity.fingerprint(config, session.platform)
            baseline = pending.get('source_after_map', task['source_map']) if pending and pending['task'] == session.state['task'] else task['source_map']
            if baseline != current:
                patch = session.complete(session.state['task'])
        pending_ref = session.state.get('completion')
        pending = read_ref(pending_ref) if pending_ref else None
        needs_retest = False
        if pending:
            prior_receipt = read_ref(handle) if handle else {}
            needs_retest = (prior_receipt.get('status') != 'verified_capture'
                            or prior_receipt.get('source_sha256') != pending['source_after_sha256']
                            or prior_receipt.get('finishedLeaseClock', -1) < pending['submittedLeaseClock'])
        refs = list(history) + [v['cycle'] for v in session.state['cycles'] if v['context_sha256'] == session.context_sha]
        # A current explicit handle remains valid for historical diagnosis; only
        # registry-bound exact contexts may adopt it for final delivery.
        proof = validity.assess(config, handle['path'], handle['sha256'], captured_context=captured_context) if final and handle and not force_native else None
        if proof and needs_retest:
            proof.update(eligible=False, reason='Measured patch still requires fresh affected-code native retest')
        result = loop._managed_cycle(config, output, previous=handle['path'] if handle else None,
                previous_sha=handle['sha256'] if handle else None, final=final, history=refs,
                intake=intake, review_result=review_result, reuse_proof=proof, capture_context=session.context, force_native=force_native,
                repair_completion=pending_ref, ensure_native=needs_retest)
        payload_ref = reference(output / 'cycle-payload.json')
        cycle_ref = {'path': str(output / 'cycle.json'), 'sha256': payload_ref['sha256']}
        save(output / 'workflow-context.json', session.context)
        if patch: save(output / 'patch-completion.json', patch)
        if proof: save(output / 'capture-validity.json', proof)
        capture = {'path': result['capture_result'], 'sha256': result['capture_sha256']} if result.get('capture_result') else handle
        handoff = {'kind': 'native_workflow_handoff', 'version': 1, 'cycle': cycle_ref,
                   'capture': capture, 'context_sha256': session.context_sha,
                   'source_sha256': result['source_sha256'], 'next_work': result['status'],
                   'native_executed': result['native_executed'], 'capture_reused': result.get('capture_reused', False)}
        save(output / 'handoff.json', handoff)
        row = {'cycle': cycle_ref, 'context_sha256': session.context_sha}
        session.state['cycles'].append(row)
        if capture:
            receipt = read_ref(capture)
            if receipt.get('parent_plan_sha256') and receipt.get('source_unchanged') and receipt.get('inputs_unchanged'):
                session.state['capture'] = dict(row, capture=capture, context=reference(output / 'workflow-context.json'))
            close_retest(session, result, capture, output)
        dispatch_path = output / ('after-dispatch.json' if (output / 'after-dispatch.json').is_file() else 'retest-plan.json')
        dispatch = d.load(dispatch_path)
        repair_jobs = [v for v in dispatch.get('jobs', []) if v['kind'] == 'repair_source']
        if (result['status'] in {'repair_source', 'awaiting_source_repair'} or repair_jobs) and capture:
            report_path = output / ('after-evaluated.json' if result['native_executed'] else 'before-evaluated.json')
            report = d.load(report_path)
            diagnostics_path = output / ('after-diagnostics.json' if result['native_executed'] else 'before-diagnostics.json')
            task = {'version': 1, 'kind': 'repair_source', 'context_sha256': session.context_sha,
                    'capture': capture, 'cycle': row['cycle'], 'source_map': source_identity.fingerprint(config, session.platform),
                    'failed_assertions': [v for v in report.get('assertions', report.get('rows', [])) if v['status'] == 'failed'],
                    'source_tasks': result.get('source_tasks', []), 'diagnostics': reference(diagnostics_path),
                    'repair_jobs': repair_jobs,
                    'scope': 'Source occurrences are candidates, not confirmed causes. A patch requires measured change and new native evidence.'}
            save(output / 'repair-task.json', task); session.state['task'] = reference(output / 'repair-task.json')
        elif result['status'] == 'accepted' and not session.state.get('completion'):
            session.state['task'] = None
        save(output / 'workflow-state.json', session.state)
        session.state['pending_publish'] = {'payload': payload_ref, 'cycle': cycle_ref, 'capture': capture,
               'files': [reference(output / name) for name in ['handoff.json','workflow-context.json','workflow-state.json']]}
        session.checkpoint(); session.recover_publish()
        return dict(result, handoff=reference(output / 'handoff.json'), repair_task=session.state.get('task'), workflowFinishedAtUnix=time.time())


def close_retest(session, result, capture, output):
    """A durable patch stays pending until its original affected rows are proven."""
    ref = session.state.get('completion')
    if not ref: return
    pending = read_ref(ref); receipt = read_ref(capture)
    report_path = output / ('after-evaluated.json' if (output / 'after-evaluated.json').is_file() else 'before-evaluated.json')
    report = d.load(report_path)
    gate = retest_gate(ref, receipt, report, result.get('evidence_responsibility', {}), result['source_sha256'])
    if gate['status'] != 'passed': return
    save(output / 'patch-retest.json', {'status': 'origin_rows_retested_passed_pending_final_delivery',
         'completion': ref, 'task': pending['task'], 'current_capture': capture,
         'assertion_ids': gate['assertion_ids'], 'source_claim_ids': gate['source_claim_ids'],
         'scope': 'Closes only the measured patch/retest handoff; full delivery and regression gates remain required.'})
    if session.state.get('task') == pending['task']: session.state['task'] = None
    session.state['completion'] = None


def retest_gate(completion, receipt, report, source_results, current_source_sha):
    pending = read_ref(completion); task = read_ref(pending['task'])
    from resource_manager import boot_identity, lease_clock
    wanted = {v['id'] for v in task.get('failed_assertions', [])}
    wanted.update(k for job in task.get('repair_jobs', []) for k in job['assertion_ids'])
    source_wanted = {v['id'] for v in task.get('source_tasks', []) if v['status'] != 'passed'}
    value = {'status': 'unassessed', 'completion': completion, 'assertion_ids': sorted(wanted),
             'source_claim_ids': sorted(source_wanted), 'reason': 'Fresh current-source original-obligation retest is pending'}
    if (receipt.get('status') != 'verified_capture' or not receipt.get('source_unchanged')
            or receipt.get('source_sha256') != current_source_sha or current_source_sha != pending['source_after_sha256']
            or receipt.get('capture_context_sha256') != pending['context_sha256']
            or receipt.get('host_boot_id') != pending['host_boot_id'] or pending['host_boot_id'] != boot_identity()
            or not pending['submittedLeaseClock'] <= receipt.get('finishedLeaseClock', -1) <= lease_clock()):
        return value
    rows = {v['id']: v['status'] for v in report.get('assertions', report.get('rows', []))}
    sources = {v['id']: v['status'] for v in source_results.get('rows', [])}
    if (wanted or source_wanted) and all(rows.get(k) == 'passed' for k in wanted) and all(sources.get(k) == 'passed' for k in source_wanted):
        value.update(status='passed', reason='Original affected obligations passed on fresh measured-patch evidence')
    return value


def finish_review(config, cycle, cycle_ref, result, output):
    completion = cycle.get('repair_completion')
    if not completion or result['status'] != 'accepted': return
    with Session(config, output) as session:
        if session.state.get('completion') == completion:
            pending = read_ref(completion)
            if session.state.get('task') == pending['task']: session.state['task'] = None
            session.state['completion'] = None
            session.checkpoint(); save(Path(output) / 'workflow-final-state.json', session.state)


def complete_repair(config, task_path, task_sha, output):
    output = Path(output).resolve()
    if output.exists(): raise ValueError('Fresh repair completion output required')
    with Session(config, output) as session:
        result = session.complete({'path': str(Path(task_path).resolve()), 'sha256': task_sha}, explicit=True)
        save(output / 'completion.json', result)
        return result
