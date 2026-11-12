#!/usr/bin/env python3
"""Reconstruct genuine canonical initial bytes without rendering or SDK work."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import time

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    run = ROOT / 'cache/business/run-cohort2'
    cohort = load(run / 'COHORT-SEAL.json')
    assert len(cohort['members']) == 10
    assert (ROOT / 'operators/cohort2/coordination/PRIVATE-PREPARATION-AUTHORIZATION.json').is_file()
    for ref in cohort['members'].values():
        assert sha(ref['path']) == ref['sha256']
    helper = module(ROOT / 'business-tools-v4/blind_study.py', 'initial_reference_frozen_helpers')
    original = module(ROOT / 'business_workspace.py', 'initial_reference_original_stock_copy')
    manifest = load(run / 'manifest.json')
    initial_cohort = load(run / 'INITIAL-COHORT.json')
    records = {}
    for task in manifest['tasks']:
        began = time.time()
        task_id = task['id']
        first_ref, second_ref = (initial_cohort[task_id][arm] for arm in ['A', 'B'])
        assert sha(first_ref['path']) == first_ref['sha256']
        assert sha(second_ref['path']) == second_ref['sha256']
        first, second = load(first_ref['path']), load(second_ref['path'])
        assert first['files'] == second['files'] and len(first['files']) == 85
        assert helper.digest(first['files']) == first['content_sha256']
        folder = ROOT / f'cache/business/initial-reference/{task_id}'
        workspace = folder / 'workspace'
        result = original.clone(ROOT / 'cache/hosts', workspace)
        roots = list(map(Path, result['production_source_roots']))
        before = helper.source(list(map(str, roots)))
        assert set(before['files']) <= set(first['files'])
        assert all(first['files'][key] == row for key, row in before['files'].items())
        for relative, row in first['files'].items():
            index, tail = relative.split('/', 1)
            source = Path(first_ref['path']).parent / 'files' / relative
            assert source.is_file() and not source.is_symlink()
            assert sha(source) == row['sha256'] and source.stat().st_size == row['bytes']
            destination = roots[int(index)] / tail
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        observed = helper.source(list(map(str, roots)))
        assert observed['files'] == first['files']
        assert observed['content_sha256'] == first['content_sha256']
        helper.protect(list(map(str, roots)))
        source_manifest = folder / 'source.json'
        save(source_manifest, observed)
        record = {
            'version': 1, 'kind': 'canonical-genuine-initial-source-reconstruction',
            'task': task_id, 'started_at_unix': began, 'finished_at_unix': time.time(),
            'cohort': {'path': str(run / 'COHORT-SEAL.json'), 'sha256': sha(run / 'COHORT-SEAL.json')},
            'paired_initial_capsules': {'A': first_ref, 'B': second_ref},
            'stock_copy_helper': {'path': str(ROOT / 'business_workspace.py'), 'sha256': sha(ROOT / 'business_workspace.py')},
            'stock_copy_receipt': {'path': str(workspace / 'STOCK-COPY.json'), 'sha256': sha(workspace / 'STOCK-COPY.json')},
            'source_manifest': {'path': str(source_manifest), 'sha256': sha(source_manifest)},
            'controller_content_sha256': observed['content_sha256'], 'file_count': len(observed['files']),
            'source_roots': list(map(str, roots)), 'workspace': str(workspace),
            'all_source_read_only': all(not (p.stat().st_mode & 0o222) for root in roots for p in [root, *root.rglob('*')]),
            'scope': 'Exact original initial bytes in a new canonical namespace. No native rendering, SDK, final-arm edits, product repair, source-domain verdict or quality pass.',
        }
        path = folder / 'SOURCE-RECONSTRUCTION.json'
        save(path, record)
        records[task_id] = {'path': str(path), 'sha256': sha(path), 'source_manifest': record['source_manifest']}
    out = ROOT / 'cache/business/initial-reference/SOURCE-RECONSTRUCTION-INDEX.json'
    save(out, {'version': 1, 'kind': 'canonical-initial-source-reconstruction-index', 'at_unix': time.time(), 'tasks': records})
    print(json.dumps({'index': str(out), 'sha256': sha(out), 'tasks': len(records), 'native_executed': False}))


if __name__ == '__main__':
    main()
