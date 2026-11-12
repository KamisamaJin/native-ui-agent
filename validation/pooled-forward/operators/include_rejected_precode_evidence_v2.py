"""Add relocated, rejected pre-D0 originals to preservation; no grading change.

The original finite plan selected the failure metadata but missed the relocated
raw source seals/compiler evidence. This additive revision selects exact current
physical keys without rewriting their historical embedded paths. SDK scratch and
complete cloned workspaces remain outside the publication obligation.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'publication-actual-preservation-review/HOST/FINAL-PLAN.json'
BASE_SHA = '50ea2874d6afb65e80ccf6927f2b930243444d7be0b9c704431945283a45d9e8'
CACHE_OWNER_SHA = 'd62df53bd1dee9691e40e34e02b6e8006e07258b8dff46053b656ec9ceb18a55'
PRESERVE_SHA = '4a1e18ebb43d1cddf82a02f69666d2ec9b898204c131469905b6a96646657a83'


def sha(path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Symlink in selected evidence key')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference(path):
    return {'path': str(path), 'sha256': sha(path)}


def main():
    if sha(BASE) != BASE_SHA or sha(ROOT / 'cache/OWNER.json') != CACHE_OWNER_SHA:
        raise ValueError('Original plan/cache ownership differs')
    cache_id = json.loads((ROOT / 'operators/cache-current-identity.json').read_text())
    cache_stat = (ROOT / 'cache').stat()
    if (cache_stat.st_dev, cache_stat.st_ino) != (cache_id['device'], cache_id['inode']):
        raise ValueError('Task-owned cache replaced')
    base = json.loads(BASE.read_text())
    plan = copy.deepcopy(base)
    additions, checked_seals = [], []
    for task in ['T1', 'T2']:
        root = ROOT / 'cache/business-rejected-cohort1/initial' / task
        seal_path = root / 'source-seal/SEAL.json'
        seal = json.loads(seal_path.read_text())
        if seal['task'] != task or len(seal['source_files']) != 85:
            raise ValueError('Original rejected-cohort source seal differs')
        for member, meta in seal['source_files'].items():
            path = root / 'source-seal/files' / member
            if sha(path) != meta['sha256'] or path.stat().st_size != meta['bytes']:
                raise ValueError('Relocated rejected-cohort source bytes differ')
        checked_seals.append(reference(seal_path))
        for directory in [root / 'source-seal', root / 'author-records', root / 'compile-attempt-1']:
            for base_path, dirs, files in os.walk(directory, followlinks=False):
                # This is the exact compiler scratch sibling, not a name-only
                # cleanup selection. No deletion is performed by this script.
                if Path(base_path) == root / 'compile-attempt-1/ios':
                    dirs[:] = [name for name in dirs if name != 'DerivedData']
                for name in dirs:
                    if (Path(base_path) / name).is_symlink():
                        raise ValueError('Unexpected relocated evidence symlink')
                for name in files:
                    path = Path(base_path) / name
                    if not path.is_file():
                        raise ValueError('Unexpected nonregular relocated evidence')
                    additions.append(reference(path))
    additions = sorted(additions, key=lambda x: x['path'])
    if len({x['path'] for x in additions}) != len(additions):
        raise ValueError('Repeated supplement member')
    existing_subjects = set(plan['subject_files'])
    existing_required = {x['path']: x['sha256'] for x in plan.get('additional_required_refs', [])}
    for item in additions:
        if item['path'] in existing_subjects or item['path'] in existing_required:
            raise ValueError('Additive failure member unexpectedly already selected')
        plan['subject_files'].append(item['path'])
        plan['additional_required_refs'].append(item)
    old = copy.deepcopy(plan)
    old['subject_files'] = old['subject_files'][:-len(additions)]
    old['additional_required_refs'] = old['additional_required_refs'][:-len(additions)]
    if old != base:
        raise ValueError('Original preservation selection changed')
    helper = ROOT / 'publication-actual-preservation-review/preserve.py'
    if sha(helper) != PRESERVE_SHA:
        raise ValueError('Original preservation helper changed')
    spec = importlib.util.spec_from_file_location('failure_supplement_preserve', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.validate_plan(plan)
    output = ROOT / 'operators/rejected-precode-preservation-v2'
    output.mkdir(exist_ok=False)

    def save(path, value):
        with path.open('x') as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        path.chmod(0o444)
        return reference(path)

    plan_ref = save(output / 'PLAN.json', plan)
    receipt = {'version': 1, 'kind': 'additive-rejected-precode-evidence-preservation',
        'base_plan': {'path': str(BASE), 'sha256': BASE_SHA}, 'revised_plan': plan_ref,
        'source': reference(Path(__file__)), 'checked_relocated_source_seals': checked_seals,
        'added_exact_original_refs': additions, 'original_plan_fields_otherwise_unchanged': True,
        'historical_embedded_paths_rewritten': False, 'product_judgments_changed': False,
        'sdk_scratch_and_complete_workspace_selected': False,
        'scope': 'Only relocated pre-D0 source copies, source seals, author/compiler logs, commands, statuses, generated compiler host and xcresult. Physical relocated keys are retained; no alias to now-reused historical input keys and no historical grading/replay claim.'}
    receipt_ref = save(output / 'ADDITION.json', receipt)
    print(json.dumps({'plan': plan_ref, 'addition_receipt': receipt_ref, 'added_files': len(additions)}))


if __name__ == '__main__':
    main()
