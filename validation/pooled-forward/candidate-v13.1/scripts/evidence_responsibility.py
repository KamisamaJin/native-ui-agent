#!/usr/bin/env python3
"""Compile source-backed evidence responsibilities before running native SDKs.

Type compatibility is not truth. Source review remains a bound human/agent
observation; a declaration cannot certify runtime styles, integration, or cause.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import design_contract as d

NATIVE = {'control': 'control', 'geometry': 'geometry', 'callback': 'event',
          'text_layout': 'text_layout', 'visual': 'manual'}
OWNERS = {'component', 'bridge', 'integration', 'host', 'system'}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compile_contract(config, plan, lock):
    d.validate_lock(lock, config['design_sha256'])
    d.verify_generated(plan, lock, config['design_sha256'], plan['design_contract']['platform'])
    ref = config.get('responsibility_ref')
    if ref is None:
        # Backward-compatible component/native scope. This does not certify
        # unlisted source, bridge, page, deployment, or integration requirements.
        return {'version': 1, 'explicit': False, 'plan_sha256': d.digest(plan), 'claims': [], 'issues': [],
                'scope': 'Native component plan only; no external/source/integration completeness claim.'}
    if set(ref) != {'source', 'pointer'}: raise ValueError('Exact independent responsibility source required')
    declared = d.pointer(lock['sources'][ref['source']]['document'], ref['pointer'])
    if not isinstance(declared, list) or not declared: raise ValueError('Nonempty independent evidence responsibility index required')
    if len({r['id'] for r in declared}) != len(declared): raise ValueError('Duplicate evidence claim identity')
    roots = [Path(v).resolve() for v in config['source_roots']]; bridge = Path(config['bridge']).resolve()
    if any(Path(v).resolve().is_relative_to(p) for v in [config.get('source_review_store', '')] if v for p in roots):
        raise ValueError('Source review store must be outside production roots')
    subjects = config.get('evidence_subjects', {}); rows = []; issues = []
    for claim in declared:
        if set(claim) != {'id', 'clause', 'priority', 'owner', 'method', 'subject', 'rule_ids'}:
            raise ValueError('Exact independent atomic evidence claim schema required')
        if claim['owner'] not in OWNERS or claim['priority'] not in {'must', 'advisory'} or not claim['clause'].strip():
            raise ValueError('Known responsibility, priority and explicit clause required')
        reason = None; files = {}; assertions = []
        if claim['method'] in NATIVE:
            assertions = [r['id'] for r in plan['assertions'] if r.get('requirement_id') in claim['rule_ids']]
            matching = [r for r in plan['assertions'] if r['id'] in assertions]
            owner_ok = claim['owner'] == 'component'
            if claim['method'] == 'visual':
                policy = d.load(Path(config['policy'])) if config.get('policy') else None
                if policy is None or d.digest(policy) != config.get('policy_sha256'):
                    owner_ok = False
                else:
                    logical = {r['id']: r.get('target') for r in lock['contract']['rules']}
                    owner_ok = all(policy['ownership'].get(logical.get(rid)) == claim['owner'] for rid in claim['rule_ids'])
            if (not owner_ok or not assertions or
                    {r.get('requirement_id') for r in matching} != set(claim['rule_ids']) or
                    any(r['kind'] != NATIVE[claim['method']] for r in matching)):
                reason = 'Native evidence type/subject does not establish the approved owner or claim kind'
        elif claim['method'] == 'source':
            paths = subjects.get(claim['subject'], [])
            if claim['owner'] in {'host', 'system'}:
                reason = 'No verified host/system source provider; responsibility declaration alone is insufficient'
            elif not isinstance(paths, list) or not paths or claim['rule_ids']:
                reason = 'Source claim needs actual subject files and cannot borrow native assertion IDs'
            else:
                for raw in paths:
                    p = Path(raw).resolve()
                    in_component = any(p == root or p.is_relative_to(root) for root in roots)
                    compatible = (in_component if claim['owner'] == 'component' else p == bridge if claim['owner'] == 'bridge' else not in_component and p != bridge)
                    if not p.is_file() or not compatible:
                        reason = 'Source subject responsibility differs from component/bridge/integration file boundary'; break
                    files[str(p)] = sha(p)
                if not config.get('source_review_store'): reason = 'Source review requires an integration-owned append-only store'
        else:
            reason = 'No verified provider for this evidence method; declarations/source/AX cannot prove computed runtime styles or executed integration'
        row = dict(claim, assertion_ids=assertions, files=files, expected=True, unit='bool',
                   provenance={'source': ref['source'], 'pointer': ref['pointer'], 'design_lock_sha256': config['design_sha256']},
                   supported=reason is None, unsupported_reason=reason)
        rows.append(row)
        if reason: issues.append({'id': claim['id'], 'priority': claim['priority'], 'reason': reason})
    return {'version': 1, 'explicit': True, 'design_lock_sha256': config['design_sha256'],
            'plan_sha256': d.digest(plan), 'source_ref': ref, 'claims': rows, 'issues': issues,
            'scope': 'Capability and subject-boundary checks, not source-review truth or causal attribution.'}


def stored(config):
    root = config.get('source_review_store')
    if not root or not Path(root).is_dir(): return []
    rows = []
    for p in sorted(Path(root).glob('*.json')):
        value = d.load(p)
        if value.get('format') != 'native-ui-source-review-v1': continue
        rows.append((p, value))
    return rows


def evaluate(config, compiled, report=None):
    by = {r['id']: r for r in (report or {}).get('rows', (report or {}).get('assertions', []))}
    saved = stored(config); results = []
    for claim in compiled['claims']:
        status = 'unassessed'; reason = claim['unsupported_reason']; actual = None; evidence = []
        if claim['supported'] and claim['method'] in NATIVE:
            native = [by.get(k, {'status': 'unassessed'})['status'] for k in claim['assertion_ids']]
            status = 'failed' if 'failed' in native else 'unassessed' if 'unassessed' in native else 'passed'
            reason = 'Native facts from the exact parent report; no extra attribution credit'
        elif claim['supported']:
            candidates = []
            for p, value in saved:
                if value.get('design_lock_sha256') != compiled['design_lock_sha256']: continue
                for row in value.get('observations', []):
                    if row['id'] == claim['id'] and row['claim_sha256'] == d.digest(claim) and row['files'] == claim['files']:
                        candidates.append((p, row))
            if candidates:
                actuals = {r['observed'] for _, r in candidates}
                if len(actuals) == 1:
                    actual = next(iter(actuals)); status = 'passed' if actual is True else 'failed' if actual is False else 'unassessed'
                    reason = candidates[0][1]['reason']; evidence = [{'path': str(p), 'sha256': sha(p)} for p, _ in candidates]
                else: reason = 'Conflicting original source reviews remain unresolved'
            else: reason = 'No current subject-bound original source observation'
        results.append({'id': claim['id'], 'priority': claim['priority'], 'owner': claim['owner'], 'method': claim['method'],
                        'status': status, 'expected': True, 'unit': 'bool', 'actual': actual, 'reason': reason,
                        'assertion_ids': claim['assertion_ids'], 'evidence': evidence,
                        'attribution': 'unassessed; evidence compatibility is not proof of defect responsibility'})
    blockers = [r['id'] for r in results if r['priority'] == 'must' and r['status'] != 'passed']
    return {'version': 1, 'explicit': compiled['explicit'], 'status': 'passed' if not blockers else 'unassessed_or_failed',
            'rows': results, 'blocking_claims': blockers, 'scope': compiled['scope']}


def template(compiled):
    return {'version': 1, 'observations': [{'id': c['id'], 'observed': None, 'reason': '', 'citations': []}
            for c in compiled['claims'] if c['method'] == 'source' and c['supported']]}


def bind(config, submission, output):
    plan = d.load(Path(config['plan'])); lock = d.load(Path(config['design_lock'])); compiled = compile_contract(config, plan, lock)
    if set(submission) != {'version', 'observations'} or submission['version'] != 1: raise ValueError('Original actual-only source observations required')
    claims = {c['id']: c for c in compiled['claims'] if c['method'] == 'source' and c['supported']}
    if len(submission['observations']) != len({r['id'] for r in submission['observations']}): raise ValueError('Duplicate source observations')
    rows = []
    for row in submission['observations']:
        if set(row) != {'id', 'observed', 'reason', 'citations'} or row['id'] not in claims or row['observed'] not in [True, False, None] or type(row['observed']) not in {bool, type(None)}:
            raise ValueError('Known source claim, actual Boolean/null and no expected override required')
        c = claims[row['id']]
        if not row['reason'].strip() or (row['observed'] is not None and not row['citations']): raise ValueError('Source observation needs rationale and actual citations')
        for ref in row['citations']:
            if set(ref) != {'path', 'line'} or str(Path(ref['path']).resolve()) not in c['files'] or type(ref['line']) is not int or not 1 <= ref['line'] <= len(Path(ref['path']).read_text().splitlines()):
                raise ValueError('Citation is outside the exact approved subject files')
        rows.append(dict(row, files=c['files'], claim_sha256=d.digest(c)))
    value = {'format': 'native-ui-source-review-v1', 'design_lock_sha256': config['design_sha256'], 'observations': rows,
             'scope': 'Bound actual source review; not computed runtime style or executed integration proof.'}
    root = Path(config['source_review_store']).resolve(); root.mkdir(parents=True, exist_ok=True)
    path = root / (d.digest(value) + '.json')
    if not path.exists():
        with path.open('x') as f: json.dump(value, f, indent=2)
    elif d.load(path) != value: raise ValueError('Existing source review identity differs')
    output = Path(output); output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as f: json.dump({'path': str(path), 'sha256': sha(path)}, f, indent=2)
    return {'path': str(path), 'sha256': sha(path)}


def main():
    p = argparse.ArgumentParser(); p.add_argument('command', choices=['audit', 'bind']); p.add_argument('--config', type=Path, required=True)
    p.add_argument('--submission', type=Path); p.add_argument('--output', type=Path, required=True); a = p.parse_args(); config = d.load(a.config)
    if a.command == 'bind': result = bind(config, d.load(a.submission), a.output)
    else:
        result = compile_contract(config, d.load(Path(config['plan'])), d.load(Path(config['design_lock'])))
        with a.output.open('x') as f: json.dump(result, f, indent=2)
    print(json.dumps(result))

if __name__ == '__main__': main()
