#!/usr/bin/env python3
"""Immutable review receipt: source + exact capture/image/state + original actuals."""
from pathlib import Path
import hashlib
import json
import design_contract as d
import review_contract as review
import native_checks


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, value):
    with Path(p).open('x') as stream: stream.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def original(config, capture_path, capture_sha):
    import feedback_loop
    plan = d.load(Path(config['plan'])); lock = d.load(Path(config['design_lock']))
    policy = d.load(Path(config['policy'])) if config.get('policy') else None
    packet = feedback_loop.load_previous(capture_path, capture_sha, plan, lock, config['design_sha256'],
                                        d.load(Path(config['fixtures'])), config['bridge'], config['source_roots'],
                                        policy, config.get('policy_sha256'), config.get('adoption'))
    return plan, lock, policy, packet


def evaluate_actuals(config, capture_path, capture_sha, submission):
    plan, lock, policy, packet = original(config, capture_path, capture_sha)
    before, _, observation, execution, receipt = packet
    if not observation or policy is None or receipt.get('evidence_error'):
        raise ValueError('A coherent original image packet and approved review policy are required')
    root = Path(capture_path).resolve().parent; op = root / 'native/observation.json'
    manual = review.bind(plan, lock, config['design_sha256'], policy, config['policy_sha256'], observation, sha(op), op.parent, submission, execution['platform'])
    evaluated = native_checks.evaluate(plan, observation, execution['platform'], manual, op.parent, sha(op), lock,
                                       config['design_sha256'], policy, config['policy_sha256'])
    if (root / 'environment-check.json').is_file(): evaluated['environment'] = d.load(root / 'environment-check.json')
    return before, observation, execution, receipt, manual, evaluated


def bind(config, capture_path, capture_sha, submission_path, submission_sha, output, *, supersedes=(), revision_reason=None):
    submission_path = Path(submission_path)
    if sha(submission_path) != submission_sha: raise ValueError('Pinned original actuals changed')
    submission = d.load(submission_path)
    before, observation, execution, receipt, manual, evaluated = evaluate_actuals(config, capture_path, capture_sha, submission)
    output = Path(output).resolve()
    original_root=Path(capture_path).resolve().parent
    if output.is_relative_to(original_root):raise ValueError('Review output cannot modify the original capture namespace')
    store=Path(config['review_store']).resolve()if config.get('review_store')else None
    if store and(not output.is_relative_to(store)or store.is_relative_to(original_root)):raise ValueError('Review output must live in its separate integration-owned store')
    if supersedes and(not store or not isinstance(revision_reason,str)or not revision_reason.strip()):raise ValueError('Review correction needs a store, explicit predecessor hashes and original rationale')
    previous=discover(config,capture_sha,all_entries=True)if store else []
    known={v['sha256']for v in previous}
    if not set(supersedes)<=known:raise ValueError('Unknown correction predecessor or foreign capture')
    if supersedes:
        effective=_inherit(config,capture_path,capture_sha,submission,supersedes)
        before,observation,execution,receipt,manual,evaluated=evaluate_actuals(config,capture_path,capture_sha,effective)
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'submission.json').open('xb') as stream: stream.write(submission_path.read_bytes())
    save(output / 'bound-manual.json', manual); save(output / 'evaluated.json', evaluated)
    value = {'version': 1, 'capture_sha256': capture_sha, 'plan_sha256': receipt['parent_plan_sha256'],
             'source_sha256': d.digest(before), 'observation_sha256': receipt['observation_sha256'],
             'image_hashes': receipt['image_hashes'], 'scope': execution['scope'],
             'supersedes':list(supersedes),'revision_reason':revision_reason,
             'files': {name: sha(output / name) for name in ['submission.json', 'bound-manual.json', 'evaluated.json']},
             'limits': 'Original actuals for these exact source/input/process/state/images. Historical review may guide repair scope, never certify edited source or a new capture.'}
    save(output / 'review-result.json', value)
    reference={'path':str(output/'review-result.json'),'sha256':sha(output/'review-result.json')}
    if store:
        directory=store/'index'/capture_sha;directory.mkdir(parents=True,exist_ok=True)
        save(directory/(reference['sha256']+'.json'),{'path':str((output/'review-result.json').relative_to(store)),'sha256':reference['sha256']})
    return reference


def _reconstruct_one(config, capture_path, capture_sha, reference):
    path = Path(reference['path']).resolve()
    if sha(path) != reference['sha256']: raise ValueError('Pinned review receipt changed')
    value = d.load(path)
    if value.get('version') != 1 or value.get('capture_sha256') != capture_sha: raise ValueError('Review belongs to a different original capture')
    if set(value.get('files', {})) != {'submission.json', 'bound-manual.json', 'evaluated.json'}: raise ValueError('Exact review file inventory required')
    for name, expected in value['files'].items():
        if sha(path.parent / name) != expected: raise ValueError('Original review file changed: ' + name)
    submission=d.load(path.parent/'submission.json')
    effective=_inherit(config,capture_path,capture_sha,submission,value.get('supersedes',[]))
    packet = evaluate_actuals(config,capture_path,capture_sha,effective)
    before, observation, execution, receipt, manual, evaluated = packet
    expected = {'plan_sha256': receipt['parent_plan_sha256'], 'source_sha256': d.digest(before),
                'observation_sha256': receipt['observation_sha256'], 'image_hashes': receipt['image_hashes'], 'scope': execution['scope']}
    if any(value.get(k) != v for k, v in expected.items()): raise ValueError('Review source/image/state identity differs')
    if manual != d.load(path.parent / 'bound-manual.json') or evaluated != d.load(path.parent / 'evaluated.json'):
        raise ValueError('Review no longer reconstructs from original actuals')
    return evaluated, effective


def _inherit(config,capture_path,capture_sha,submission,supersedes):
    if not supersedes:return submission
    refs={v['sha256']:v for v in discover(config,capture_sha,all_entries=True)}
    merged={};conflicts=set()
    for key in supersedes:
        if key not in refs:raise ValueError('Missing original correction predecessor')
        _,old=_reconstruct_one(config,capture_path,capture_sha,refs[key])
        if (old['catalog_sha256'],old['observation_sha256'])!=(submission['catalog_sha256'],submission['observation_sha256']):raise ValueError('Correction crosses source/image identity')
        for row in old['decisions']:
            rid=row['review_id']
            if rid in merged and merged[rid]!=row:conflicts.add(rid)
            merged[rid]=row
    for row in submission['decisions']:
        merged[row['review_id']]=row;conflicts.discard(row['review_id'])
    if conflicts:raise ValueError('Correction leaves contradictory original judgments unresolved')
    return dict(submission,decisions=list(merged.values()))


def reconstruct(config, capture_path, capture_sha, reference):
    references = reference if isinstance(reference, list) else [reference]
    if not references: raise ValueError('Nonempty pinned review references required')
    submissions = []; seen = {}
    for ref in references:
        _, submission = _reconstruct_one(config, capture_path, capture_sha, ref)
        submissions.append(submission)
        for row in submission['decisions']:
            key=row['review_id']
            if key in seen and seen[key]!=row: raise ValueError('Conflicting parallel actuals require an explicit original correction, not last-wins merge')
            seen[key]=row
    first=submissions[0]
    if any((v['catalog_sha256'],v['observation_sha256'])!=(first['catalog_sha256'],first['observation_sha256'])for v in submissions):raise ValueError('Different review evidence queues')
    combined=dict(first,decisions=list(seen.values()))
    return evaluate_actuals(config,capture_path,capture_sha,combined)[-1]


def discover(config, capture_sha, *, all_entries=False):
    if not config.get('review_store'):return []
    store=Path(config['review_store']).resolve();directory=store/'index'/capture_sha
    if not directory.exists():return []
    entries=[];replaced=set()
    for entry in sorted(directory.glob('*.json')):
        ref=d.load(entry);path=(store/ref['path']).resolve()
        if not path.is_relative_to(store)or not path.is_file()or sha(path)!=ref['sha256']or entry.stem!=ref['sha256']:raise ValueError('Review registry identity changed')
        value=d.load(path)
        if value.get('capture_sha256')!=capture_sha:raise ValueError('Registry points to foreign capture')
        entries.append({'path':str(path),'sha256':ref['sha256']});replaced.update(value.get('supersedes',[]))
    known={v['sha256']for v in entries}
    if not replaced<=known:raise ValueError('Missing original review correction history')
    return entries if all_entries else[v for v in entries if v['sha256']not in replaced]


def requests(config, capture_path, capture_sha, report):
    plan, lock, policy, packet = original(config, capture_path, capture_sha)
    before, _, observation, execution, receipt = packet
    if not policy or not observation or receipt.get('evidence_error'): return None
    cat = review.catalog(plan, lock, config['design_sha256'], policy, config['policy_sha256'], execution['platform'])
    rows = {r['id']: r for r in report.get('assertions', report.get('rows', []))}
    wanted = [r for r in cat['rows'] if r['method'] == 'visual' and r['state'] in execution['selected_states'] and rows[r['id']]['status'] == 'unassessed']
    if not wanted: return None
    return {'kind': 'review_images', 'capture_sha256': capture_sha, 'source_sha256': d.digest(before),
            'plan_sha256': d.digest(plan), 'image_hashes': receipt['image_hashes'], 'catalog': cat,
            'submission_template': {'version': 1, 'catalog_sha256': d.digest(cat), 'observation_sha256': receipt['observation_sha256'],
                                    'decisions': [{'review_id': r['review_id'], 'actual': None, 'reason': 'Original observation or honest unknown required', 'snapshot_indices': []} for r in wanted]},
            'rows': [{'id': r['id'], 'state': r['state'], 'proposition': r.get('proposition'), 'review_id': r['review_id']} for r in wanted],
            'scope': 'Complete original state frames must be read. No expected values or units are entered by the reviewer.'}
