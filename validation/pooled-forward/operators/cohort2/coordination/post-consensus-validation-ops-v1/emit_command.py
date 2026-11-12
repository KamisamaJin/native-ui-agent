#!/usr/bin/env python3
"""Print one pinned operation argv. Never execute or authorize an operation."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def need(ok, why):
    if not ok: raise ValueError(why)


def safe(raw):
    p = Path(raw)
    need(p.is_absolute() and str(p) == os.path.normpath(str(p)), 'Canonical absolute path required')
    need(not any(q.is_symlink() for q in [p, *p.parents]), 'Symlink rejected')
    return p


def sha(path):
    h = hashlib.sha256()
    with safe(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): h.update(block)
    return h.hexdigest()


def load(path):
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, 'Duplicate plan metadata key'); value[key] = item
        return value
    return json.loads(safe(path).read_bytes(), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite metadata')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--operation-id')
    parser.add_argument('--submission', type=Path)
    parser.add_argument('--submission-sha256')
    args = parser.parse_args()
    plan_path = Path(__file__).resolve().parent/'PLAN.json'
    need(sha(plan_path) == args.plan_sha256, 'External plan pin differs')
    plan = load(plan_path)
    need(sha(plan['contexts']['path']) == plan['contexts']['sha256'], 'Prepared context pin differs')
    if args.operation_id is None:
        need(args.submission is None and args.submission_sha256 is None, 'Choose one operation before supplying a submission')
        print(json.dumps({'operation_ids':[op['id'] for op in plan['operations']], 'execution_authorized':False})); return
    selected = [op for op in plan['operations'] if op['id'] == args.operation_id]
    need(len(selected) == 1, 'Exact unique prepared operation ID required')
    op = selected[0]; argv = list(op['argv']); pin = None
    if '@SUBMISSION@' in argv:
        need(args.submission is not None and args.submission_sha256, 'Externally pinned actual-only submission required')
        path = safe(args.submission)
        need(sha(path) == args.submission_sha256, 'Submission byte pin differs')
        pin = {'path':str(path), 'sha256':args.submission_sha256}
        argv = [str(path) if a == '@SUBMISSION@' else args.submission_sha256 if a == '@SUBMISSION_SHA256@' else a for a in argv]
    else:
        need(args.submission is None and args.submission_sha256 is None, 'Finish consumes its exact original cycle, not a submission')
    need(not Path(op['record']).exists(), 'A prepared record already exists; retain it and do not reuse')
    print(json.dumps({'operation_id':op['id'], 'argv':argv, 'submission_ref':pin,
        'execution_authorized':False, 'executes_process':False,
        'required_external_gates':plan['unresolved_execution_gates'],
        'scope':'Formatting one command only. Root must authenticate and release execution separately; input SHA is not evidence or consensus validity.'}))


if __name__ == '__main__': main()
