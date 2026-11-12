#!/usr/bin/env python3
"""Separate post-seal source observations without changing an original gate.

This operator has no native, image, repair or final-delivery entry point. The
caller must authenticate the original contract, complete source capsule and
independent consensus before using it. Only source_review_store is replaced;
the unchanged frozen evidence_responsibility backend supplies expectations,
units, subject hashes and P/F/U. Original worker observations remain untouched.
"""
import argparse
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time


def need(ok, why):
    if not ok: raise ValueError(why)


def safe(raw):
    path = Path(raw)
    need(path.is_absolute() and str(path) == os.path.normpath(str(path)), 'Canonical absolute path required')
    for part in [path, *path.parents]: need(not part.is_symlink(), 'Symlink is not a source authority')
    return path


def sha(path): return hashlib.sha256(safe(path).read_bytes()).hexdigest()


def write(path, value):
    with safe(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
    Path(path).chmod(0o444)


def isolated_config(config, output):
    """Only a fresh, integration-owned source store may differ."""
    output = safe(output); store = output/'source-review-store'
    roots = [safe(raw) for raw in config['source_roots']]
    protected = roots + [safe(config[key]) for key in ['source_review_store', 'review_store'] if config.get(key)]
    need(all(store != root and not store.is_relative_to(root) and not root.is_relative_to(store)
             for root in protected), 'Separate source store must not overlap production or original reviews')
    result = copy.deepcopy(config); result['source_review_store'] = str(store)
    need({key for key in set(config) | set(result) if config.get(key) != result.get(key)} <= {'source_review_store'},
         'Only source_review_store may change')
    return result


def bind_source(config, submission, output, backend):
    output = safe(output); need(not output.exists(), 'A fresh source-only output is required')
    derived = isolated_config(config, output)
    plan = backend.d.load(Path(config['plan'])); lock = backend.d.load(Path(config['design_lock']))
    before = backend.compile_contract(config, plan, lock)
    need(backend.compile_contract(derived, plan, lock) == before, 'Source store cannot change the compiled contract')
    output.mkdir(parents=True, exist_ok=False)
    write(output/'source-only-config.json', derived)
    write(output/'compiled-original.json', before)
    bound = backend.bind(derived, submission, output/'source-review-ref.json')
    current = backend.compile_contract(config, backend.d.load(Path(config['plan'])), backend.d.load(Path(config['design_lock'])))
    need(current == before and backend.compile_contract(derived, plan, lock) == before,
         'Original contract or approved subject bytes changed during binding')
    evaluation = backend.evaluate(derived, before)
    rows = [row for row in evaluation['rows'] if row['method'] == 'source']
    write(output/'source-only-evaluation.json', {
        'version': 1, 'kind': 'independent-post-seal-source-only-evaluation',
        'rows': rows, 'source_review': bound,
        'blocking_source_claims': [row['id'] for row in rows if row['priority'] == 'must' and row['status'] != 'passed'],
        'native_evaluation': 'not-performed', 'original_public_gate_promoted': False,
        'current_delivery_verified': False,
        'scope': 'Unchanged source responsibility evaluator with a separate append-only observation store. No native/image facts, historical source rebinding, repair, worker detection credit or original delivery-gate replacement.'})
    return {'config': str(output/'source-only-config.json'), 'source_review': bound,
            'evaluation': str(output/'source-only-evaluation.json')}


def verify_tool(tool):
    root = safe(tool['skill_root'])
    for name, digest in tool['files'].items():
        relative = Path(name)
        need(not relative.is_absolute() and '..' not in relative.parts, 'Safe frozen tool member required')
        need(sha(root/relative) == digest, 'Frozen source evaluator member changed: ' + name)
    need('scripts/evidence_responsibility.py' in tool['files'] and 'scripts/design_contract.py' in tool['files'],
         'Frozen evaluator and contract compiler inventory required')
    return root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['config', 'submission', 'tool_manifest', 'output']:
        parser.add_argument('--' + key.replace('_', '-'), required=True, type=Path)
    for key in ['config', 'submission', 'tool_manifest']:
        parser.add_argument('--' + key.replace('_', '-') + '-sha256', required=True)
    args = parser.parse_args(); start_unix = time.time(); start_clock = time.clock_gettime(time.CLOCK_MONOTONIC)
    for key in ['config', 'submission', 'tool_manifest']:
        need(sha(getattr(args, key)) == getattr(args, key + '_sha256'), 'External original input pin differs: ' + key)
    tool = json.loads(safe(args.tool_manifest).read_bytes()); root = verify_tool(tool)
    sys.path.insert(0, str(root/'scripts'))
    backend = importlib.import_module('evidence_responsibility')
    need(Path(backend.__file__).resolve() == root/'scripts/evidence_responsibility.py', 'Wrong source evaluator imported')
    result = bind_source(json.loads(safe(args.config).read_bytes()), json.loads(safe(args.submission).read_bytes()), args.output, backend)
    verify_tool(tool)
    for key in ['config', 'submission', 'tool_manifest']:
        need(sha(getattr(args, key)) == getattr(args, key + '_sha256'), 'Original input changed during binding: ' + key)
    write(args.output/'operation.json', {
        'version': 1, 'kind': 'common-post-seal-source-only-binding',
        'started_at_unix': start_unix, 'finished_at_unix': time.time(),
        'started_at_clock_gettime': start_clock, 'finished_at_clock_gettime': time.clock_gettime(time.CLOCK_MONOTONIC),
        'shared_clock_basis': 'clock_gettime(CLOCK_MONOTONIC)',
        'inputs': {key: {'path': str(safe(getattr(args, key))), 'sha256': getattr(args, key + '_sha256')}
                   for key in ['config', 'submission', 'tool_manifest']},
        'outputs': result, 'current_delivery_verified': False, 'common_infrastructure_not_treatment_benefit': True})
    print(json.dumps({'operation': str(args.output/'operation.json'), 'sha256': sha(args.output/'operation.json')}))
    return 0


if __name__ == '__main__': raise SystemExit(main())
