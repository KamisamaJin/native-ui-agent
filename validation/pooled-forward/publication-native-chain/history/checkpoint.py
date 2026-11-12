"""Author-only immutable history checkpoint. Reads originals; never locks or
changes them. Portable replay is history_view.HistoryReader over a Resolver.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import stat
import time

from history_view import EXPECTED_SCOPES, FORMAT, absolute, need, registered_record, requirements, sha, strict_json


HERE = Path(__file__).resolve().parent
RESOLVER_SHA = '2a5ec0949b5a64cb3f1dc57df87b3954e1f5e1f21ea58defec3ced44b5ba8204'


class LiveOriginal:
    """Explicit no-follow original access, only for author preservation.

    No fallback semantics, SDK calls, subprocesses or advisory locks.
    """
    def __init__(self):
        source = HERE / 'vendor/schema-code/resolver.py'
        need(sha(source.read_bytes()) == RESOLVER_SHA, 'Frozen no-follow reader changed')
        spec = importlib.util.spec_from_file_location('history_frozen_regular_reader', source)
        self.rm = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.rm)

    def observe(self, original):
        original = str(absolute(str(original))); started = time.time()
        raw, first, actual = self.rm.read_regular(original)
        _second_raw, second, second_sha = self.rm.read_regular(original)
        need(first == second and actual == second_sha, 'Original changed/rebound while checkpointing: '+original)
        keys = ['device','inode','bytes','mode','mtime_ns','ctime_ns']
        identity = dict(zip(keys, first))
        need(stat.S_ISREG(identity['mode']), 'Only a regular original checkpoint is readable')
        return raw, {'original_path':original,'sha256':actual,'stable_read':True,
                     'identity_before':identity,'identity_after':dict(zip(keys,second)),
                     'read_started_at_unix':started,'read_finished_at_unix':time.time(),
                     'observation_scope':'Two stable no-follow regular-file reads at checkpoint time; not historical emptiness/freshness proof.'}

    def read_bytes(self, original):
        return self.observe(original)[0]

    def read_json(self, original):
        return strict_json(self.read_bytes(original))

    def hash(self, original):
        return sha(self.read_bytes(original))


def save_json(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)+'\n').encode()
    save_raw(path, raw)
    return {'path':str(path),'sha256':sha(raw),'bytes':len(raw)}


def save_raw(path, raw):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd,'wb',closefd=False) as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.fchmod(fd,0o444)
    finally:
        os.close(fd)
    need(path.read_bytes() == raw, 'Checkpoint copy changed during preservation')


def create_checkpoint(reader, original_root, output):
    """Preserve the current raw bytes required by five registered B/android
    historical context-proof slots. Pending and failed slots remain explicit.
    """
    root = absolute(str(original_root)); output = Path(str(absolute(str(output))))
    need(output.is_relative_to(HERE) and output != HERE, 'Checkpoint outputs must remain inside the dedicated history directory')
    need(not output.exists(), 'A history checkpoint must use a fresh immutable output directory')
    for parent in output.parents:
        need(not parent.is_symlink(), 'Symlink in checkpoint output namespace')
    output.mkdir(parents=True,exist_ok=False)
    started = time.time(); registrations=[]; pending=[]; pending_details=[]; failures=[]; required={}
    def error(exc):return {'type':type(exc).__name__,'message':str(exc)}
    for scope in EXPECTED_SCOPES:
        task,arm,profile=scope.split('/')
        claim_path = str(root/f'cache/business/independent-evaluation/native-continuation-claims/{task}/{arm}/{profile}.json')
        stage='registered_claim'
        try:
            raw=reader.read_bytes(claim_path); claim=strict_json(raw)
            claim_ref={'path':claim_path,'sha256':sha(raw)}
            stage='registered_scope_validation'; record=registered_record(root,scope,claim['record'])
            stage='context_proof'; proof_path=str(record/'fresh-platform-context.json')
            raw=reader.read_bytes(proof_path); proof_ref={'path':proof_path,'sha256':sha(raw)}
            reg={'scope':scope,'claim':claim_ref,'proof':proof_ref}
            stage='registered_scope_validation'; refs=requirements(reader,root,reg)
            registrations.append(reg)
            for original,ref in refs.items():
                key=(original,ref['sha256'])
                required.setdefault(key,[]).append({'scope':scope,'proof':proof_ref,'claim':claim_ref})
        except (FileNotFoundError,KeyError) as exc:
            # A missing registry/proof slot is a declared pending snapshot slot,
            # never evidence of historical absence or permission to re-execute.
            if stage in {'registered_claim','context_proof'}:
                pending.append(scope);pending_details.append({'scope':scope,'stage':stage,'error':error(exc)})
            else:
                failures.append({'scope':scope,'stage':stage,'error':error(exc)})
        except (ValueError,TypeError,OSError) as exc:
            failures.append({'scope':scope,'stage':stage,'error':error(exc)})
    versions=[]
    for (original,expected),provenance in sorted(required.items()):
        stage='read_required_historical_bytes'
        try:
            raw,observation=reader.observe(original)
            if sha(raw) != expected:
                failures.append({'original_path':original,'required_sha256':expected,'observed_sha256':sha(raw),
                                 'stage':stage,'original_observation':observation,
                                 'error':{'type':'ValueError','message':'Required historical bytes are missing/changed; no substitution or fallback performed'}})
                continue
            stage='immutable_copy'
            copied=output/'versions'/sha(original.encode())/expected/absolute(original).name
            save_raw(copied,raw)
            versions.append({'original_path':original,'required_sha256':expected,'bytes':len(raw),
                'copy':{'path':str(copied),'sha256':expected,'bytes':len(raw)},'copy_mode':'0444','status':'preserved',
                'copied_at_unix':time.time(),'original_observation':observation,'proof_provenance':provenance})
        except (ValueError,TypeError,KeyError,OSError) as exc:
            failures.append({'original_path':original,'required_sha256':expected,'stage':stage,'error':error(exc)})
    # Recheck registrations after all copies. A changed proof cannot silently
    # become a newer selection while the checkpoint is being constructed.
    for reg in registrations:
        try:
            requirements(reader,root,reg)
        except (ValueError,TypeError,KeyError,OSError) as exc:
            failures.append({'scope':reg['scope'],'stage':'post_copy_registration_recheck','error':error(exc)})
    by_path={}
    for original,required_sha in required:by_path.setdefault(original,set()).add(required_sha)
    for original,versions_for_path in by_path.items():
        if len(versions_for_path)>1:
            failures.append({'original_path':original,'stage':'single_view_ambiguity','required_sha256':sorted(versions_for_path),
                             'error':{'type':'ValueError','message':'One path-only reader cannot select multiple historical versions'}})
    # Keep expected slots in declared order, including failed registration slots.
    missing=[scope for scope in EXPECTED_SCOPES if scope not in {r['scope'] for r in registrations}]
    value={'format':FORMAT,'version':1,'original_root':str(root),'checkpoint_root':str(output),
           'started_at_unix':started,'finished_at_unix':time.time(),
           'status':'failed' if failures else ('partial' if missing else 'complete'),
           'selection':{'expected_scopes':EXPECTED_SCOPES,'registered_proofs':registrations,'pending_scopes':missing,
                        'pending_details':pending_details},'versions':versions,'failures':failures,
           'scope':'Only exact raw shared-workflow sibling versions named by registered context proofs. No source/contract/native measurement substitution, SDK, locks, live workflow writes, or present freshness claim.',
           'native_collection_completion_claimed':False,'product_evaluated':False,'originals_modified':False}
    ledger=save_json(output/'LEDGER.json',value)
    for directory in sorted([p for p in output.rglob('*') if p.is_dir()],key=lambda p:len(p.parts),reverse=True):directory.chmod(0o555)
    output.chmod(0o555)
    return ledger,value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=str,required=True)
    parser.add_argument('--output',type=str,required=True)
    args=parser.parse_args()
    ledger,value=create_checkpoint(LiveOriginal(),args.root,args.output)
    print(json.dumps({'ledger':ledger,'status':value['status'],'registered_proofs':len(value['selection']['registered_proofs']),
                     'preserved_versions':len(value['versions']),'pending_scopes':value['selection']['pending_scopes'],
                     'failures':value['failures']},indent=2))
    return 1 if value['status']=='failed' else 0


if __name__=='__main__':raise SystemExit(main())
