#!/usr/bin/env python3
"""Bind original visual observations to approved atomic contracts without expectation entry."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import design_contract as design
import native_pixels

PIXEL_ASPECTS = {'rendered_fill', 'rendered_canvas', 'rendered_border', 'rendered_ink'}
VISUAL_ASPECTS = {'wrapping', 'overlap', 'hierarchy', 'clipping', 'content_presence'}


def catalog(plan, lock, lock_sha, policy, policy_sha, platform):
    design.verify_generated(plan, lock, lock_sha, platform)
    if design.digest(policy) != policy_sha or set(policy) != {'version', 'design_lock_sha256', 'approval_reference', 'ownership', 'atoms'}:
        raise ValueError('Atomic review policy must match an independently pinned digest and schema')
    if policy['version'] != 1 or policy['design_lock_sha256'] != lock_sha or not policy['approval_reference']:
        raise ValueError('Atomic policy must bind the approved independent design')
    targets = {r['id']: r.get('target') for r in lock['contract']['rules']}
    manual_rules = {r['id'] for r in lock['contract']['rules'] if r['kind'] == 'manual'}
    atoms = {}
    for atom in policy['atoms']:
        if not isinstance(atom, dict) or set(atom) - {'rule_id', 'aspect', 'method', 'sampling', 'question'} or not {'rule_id', 'aspect', 'method'} <= set(atom):
            raise ValueError('Unknown atom metadata or attempted expected/unit override')
        rid = atom['rule_id']
        if rid in atoms or rid not in manual_rules:
            raise ValueError('Each manual design rule needs one unique atomic policy')
        target = targets[rid]
        if policy['ownership'].get(target) not in {'component', 'host', 'system'}:
            raise ValueError('Responsibility must be fixed for each visual target before implementation')
        if atom['method'] == 'native_pixels' and atom['aspect'] in PIXEL_ASPECTS:
            native_pixels.validate_sampling(atom.get('sampling', {}))
        elif atom['method'] == 'visual' and atom['aspect'] in VISUAL_ASPECTS and 'sampling' not in atom:
            question, _ = design.expression(atom.get('question'), lock['sources'])
            if question['unit'] != 'string' or not question['value'].strip():
                raise ValueError('Qualitative actual must answer one source-backed independent proposition')
        else:
            raise ValueError('One supported aspect and evidence method required; compound visual checks are rejected')
        atoms[rid] = atom
    if set(atoms) != manual_rules:
        raise ValueError('Atomic policy must disposition every manual rule, without omission')
    rows = []
    for rule in plan['assertions']:
        if rule['kind'] != 'manual':
            continue
        atom = atoms[rule['requirement_id']]
        if atom['method'] not in rule.get('allowed_methods', ['visual']) or rule.get('op', 'eq') != 'eq':
            raise ValueError('Atomic review method/operator differs from the approved contract')
        if atom['method'] == 'native_pixels' and (rule['unit'] != 'argb' or type(rule['expected']) is not int or rule['expected'] >> 24 != 255):
            raise ValueError('Rendered color atoms require opaque source-backed ARGB')
        if atom['method'] == 'visual' and (rule['unit'] != 'bool' or type(rule['expected']) is not bool):
            raise ValueError('Qualitative atoms require one source-backed Boolean proposition')
        identity = {'design_lock_sha256': lock_sha, 'policy_sha256': policy_sha,
                    'scenario': plan['design_contract']['scenario'], 'platform': platform, 'assertion_id': rule['id']}
        proposition = {}
        if atom['method'] == 'visual':
            question, proof = design.expression(atom['question'], lock['sources'])
            proposition = {'proposition': question['value'], 'proposition_provenance': proof}
        rows.append(dict(copy.deepcopy(rule), review_id=design.digest(identity), identity=identity, **proposition,
                         aspect=atom['aspect'], method=atom['method'], responsibility=policy['ownership'][targets[rule['requirement_id']]],
                         **({'sampling': copy.deepcopy(atom['sampling'])} if 'sampling' in atom else {})))
    return {'version': 1, 'design_lock_sha256': lock_sha, 'policy_sha256': policy_sha,
            'plan_sha256': design.digest(plan), 'platform': platform, 'rows': rows}


def bind(plan, lock, lock_sha, policy, policy_sha, observation, observation_sha, root, submission, platform):
    from native_checks import state_evidence
    root = root.resolve()
    cat = catalog(plan, lock, lock_sha, policy, policy_sha, platform)
    if set(submission) != {'version', 'catalog_sha256', 'observation_sha256', 'decisions'} or submission['version'] != 1:
        raise ValueError('Review submission contains unsupported fields or expectation overrides')
    if submission['catalog_sha256'] != design.digest(cat) or submission['observation_sha256'] != observation_sha:
        raise ValueError('Review submission belongs to another design, plan or native observation')
    # Canonical object digest is carried in addition to exact original-file SHA.
    if len(observation_sha) != 64:
        raise ValueError('Original observation file SHA256 required')
    by_review = {r['review_id']: r for r in cat['rows']}
    requests = {}
    for request in submission['decisions']:
        if set(request) != {'review_id', 'actual', 'reason', 'snapshot_indices'}:
            raise ValueError('Submit only rule identity, actual proposition, reason and original frame indices')
        rid = request['review_id']
        if rid not in by_review or rid in requests or by_review[rid]['method'] != 'visual':
            raise ValueError('Unknown, duplicate or inappropriate review decision')
        if request['actual'] is not None and type(request['actual']) is not bool:
            raise ValueError('Visual actual must be Boolean or explicitly unknown')
        if not isinstance(request['reason'], str) or not request['reason'].strip():
            raise ValueError('Original visual observation rationale required')
        indices = request['snapshot_indices']
        if not isinstance(indices, list) or any(type(i) is not int for i in indices) or len(set(indices)) != len(indices):
            raise ValueError('Unique original native snapshot indices required')
        requests[rid] = request
    states = {s['id']: state_evidence(observation, s) for s in plan['states']}
    decisions, findings = [], []
    for row in cat['rows']:
        found, complete, why, capture = states[row['state']]
        allowed = {i for i, _ in found}
        status, actual, indices, proofs = 'unassessed', None, [], []
        reason = why
        if row['method'] == 'native_pixels':
            samples = []
            for index, snapshot in found:
                sample = native_pixels.sample(snapshot, row['target'], platform, root, row['sampling'])
                samples.append(dict(sample, snapshot_index=index))
            measured = [s for s in samples if s['status'] == 'measured']
            actual = {'samples': samples, 'scope': 'Rendered original pixels, not computed UI properties'}
            if measured:
                indices = [s['snapshot_index'] for s in measured]
                verdicts = [native_pixels.matches(s['argb'], row['expected'], row['sampling']['channel_tolerance']) for s in measured]
                # Missing/offscreen targets in other sweep frames are not conflicts.
                # Present targets whose color cannot be measured block a pass.
                incomplete = any(s['status'] != 'measured' and 'proof' in s for s in samples)
                if not any(verdicts):
                    status, reason = 'failed', 'Original rendered color contradicts approved atomic role'
                elif all(verdicts) and not incomplete:
                    status, reason = 'passed', 'Original rendered color matches approved atomic role'
                else:
                    reason = 'Conflicting or insufficient rendered-color evidence within the state'
                proofs = [s['proof'] for s in measured]
        elif row['review_id'] in requests:
            request = requests[row['review_id']]
            indices = request['snapshot_indices']
            if not set(indices) <= allowed:
                raise ValueError('Review cites a frame outside this exact input/action state')
            actual, reason = request['actual'], request['reason']
            if actual is not None and indices:
                status = 'passed' if actual == row['expected'] else 'failed'
        if status == 'passed' and row.get('coverage', 'full_content') == 'full_content' and not complete:
            status, reason = 'unassessed', 'Atomic pass withheld: required full-content coverage unavailable'
        evidence = []
        for index in indices:
            path = (root / observation['snapshots'][index]['screenshot']).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise ValueError('Original visual screenshot is missing or outside observation root')
            proof = {'path': str(path.relative_to(root)), 'sha256': native_pixels.sha(path)}
            if proof not in evidence:
                evidence.append(proof)
        decision = {'id': row['id'], 'status': status, 'method': row['method'], 'snapshot_indices': indices,
                    'reason': reason, 'evidence': evidence}
        decisions.append(decision)
        findings.append({'id': row['id'], 'review_id': row['review_id'], 'state': row['state'],
                         'requirement_id': row['requirement_id'], 'aspect': row['aspect'], 'target': row['target'],
                         'expected': row['expected'], 'unit': row['unit'], 'op': row.get('op', 'eq'),
                         'expectation_provenance': row['expectation_provenance'], 'status': status, 'actual': actual,
                         'responsibility': row['responsibility'], 'reason': reason, 'evidence': evidence,
                         'snapshot_indices': indices, 'pixel_proofs': proofs})
    return {'observation_sha256': observation_sha, 'decisions': decisions,
            'review_contract': {'version': 1, 'catalog_sha256': design.digest(cat), 'policy_sha256': policy_sha,
                                'design_lock_sha256': lock_sha, 'observation_object_sha256': design.digest(observation),
                                'submission': copy.deepcopy(submission), 'findings': findings}}


def verify_manual(manual, plan, lock, lock_sha, policy, policy_sha, observation, observation_sha, root, platform):
    rebuilt = bind(plan, lock, lock_sha, policy, policy_sha, observation, observation_sha, root,
                   manual['review_contract']['submission'], platform)
    if design.canonical(rebuilt) != design.canonical(manual):
        raise ValueError('Bound review changed after generation: verdict, expected, evidence or provenance differs')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['catalog', 'review'])
    for flag in ['plan', 'design-lock', 'policy', 'output']:
        p.add_argument('--' + flag, type=Path, required=True)
    p.add_argument('--design-sha256', required=True)
    p.add_argument('--policy-sha256', required=True)
    p.add_argument('--platform', choices=['ios', 'android'], required=True)
    p.add_argument('--observation', type=Path)
    p.add_argument('--submission', type=Path)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError('Fresh output required; original review is never replaced')
    plan, lock, policy = [design.load(v) for v in [args.plan, args.design_lock, args.policy]]
    cat = catalog(plan, lock, args.design_sha256, policy, args.policy_sha256, args.platform)
    if args.command == 'catalog':
        value = dict(cat, catalog_sha256=design.digest(cat))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        return
    if args.observation is None:
        raise ValueError('Original observation required')
    import native_checks
    observation, observation_sha = design.load(args.observation), native_pixels.sha(args.observation)
    submission = design.load(args.submission) if args.submission else {'version': 1, 'catalog_sha256': design.digest(cat), 'observation_sha256': observation_sha, 'decisions': []}
    manual = bind(plan, lock, args.design_sha256, policy, args.policy_sha256, observation, observation_sha,
                  args.observation.parent, submission, args.platform)
    report = native_checks.evaluate(plan, observation, args.platform, manual, args.observation.parent,
                                    observation_sha, lock, args.design_sha256, policy, args.policy_sha256)
    args.output.mkdir(parents=True)
    for name, value in [('catalog.json', dict(cat, catalog_sha256=design.digest(cat))), ('manual.json', manual), ('report.json', report),
                        ('findings.json', manual['review_contract']['findings'])]:
        (args.output / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'counts': report['counts'], 'catalog_sha256': design.digest(cat)}))


if __name__ == '__main__':
    main()
