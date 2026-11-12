"""Read-only final ownership audit; never acquires SDKs or reclaims resources.

This joins the original public retirement receipts with current exact config
roots and every post-consensus supervisor. It does not turn a historical failed
operation into a success or judge product quality.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
COORD = ROOT / 'operators/cohort2/coordination'
CONTEXTS = COORD / 'post-consensus-validation-ops-v1/CONTEXTS.json'
CONTEXTS_SHA = '7d9e1665fd0be505e95b4edc6a661c609599b4262d43d64a44f5d90e5aea91ad'
FAILURE_AUDIT_SHA = '09de4f20407fd9279ee3d0889c682e84bbe8483272264a4973dd2ca21610454b'
FORMAT = 'native-ui-owned-resources-v1'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def regular(path):
    path = Path(path)
    need(path.is_absolute(), 'Absolute original path required')
    need(not any(p.is_symlink() for p in (path, *path.parents)), 'Symlink in original path')
    need(stat.S_ISREG(path.stat().st_mode), 'Original regular file required')
    return path


def sha(path):
    return hashlib.sha256(regular(path).read_bytes()).hexdigest()


def ref(path):
    return {'path': str(path), 'sha256': sha(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding-index', type=Path, required=True)
    parser.add_argument('--binding-index-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    readset = {}

    def read(reference):
        path = regular(Path(reference['path']))
        raw = path.read_bytes()
        need(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'Original resource ref differs: ' + str(path))
        need(str(path) not in readset or readset[str(path)] == reference['sha256'], 'One original key changed during audit')
        readset[str(path)] = reference['sha256']
        return json.loads(raw)

    contexts = read({'path': str(CONTEXTS), 'sha256': CONTEXTS_SHA})
    index_ref = {'path': str(args.binding_index), 'sha256': args.binding_index_sha256}
    index = read(index_ref)
    need(len(index['operations']) == 110 and not index['uncompleted_operation_ids'], 'All original operations must be terminal before final audit')
    need(all(x.get('outcome') and x.get('exit_code') is not None and x.get('error') is None
             and x.get('post_boundary_error') is None for x in index['operations']), 'Unresolved operation boundary')
    config_rows = contexts['private_contexts'] + contexts['final_public_contexts']
    need(len(config_rows) == 50, 'Original 30 private and 20 public contexts required')
    configs = {x['config']['path']: (x['config'], read(x['config'])) for x in config_rows}
    audited = {}

    def audit_root(root, config):
        root = Path(root)
        need(root.is_absolute() and not any(p.is_symlink() for p in (root, *root.parents)), 'Unsafe owned root')
        expected_key = hashlib.sha256(json.dumps([str(Path(p).resolve()) for p in config['source_roots']]).encode()).hexdigest()
        marker_ref = ref(root / 'owner.json')
        marker = read(marker_ref)
        need(marker.get('format') == FORMAT and marker.get('owner_key') == expected_key
             and isinstance(marker.get('token'), str) and len(marker['token']) == 32, 'Config source roots do not own this resource root')
        inode = {'device': root.stat().st_dev, 'inode': root.stat().st_ino}
        journals = []
        for name in ['journal.json', 'journal-backup.json']:
            reference = ref(root / name)
            journal = read(reference)
            need(journal.get('format') == FORMAT and journal.get('token') == marker['token']
                 and journal.get('root_identity') == inode, 'Owned journal token/root inode differs')
            need(journal.get('directories') == [] and journal.get('devices') == []
                 and not journal.get('lease') and not journal.get('process'), 'Resource root is still live or unresolved: ' + str(root))
            journals.append({'ref': reference, 'generation': journal.get('generation')})
        need(journals[0]['generation'] == journals[1]['generation'], 'Incomplete resource checkpoint')
        lease = regular(root / 'lease.lock')
        with lease.open('rb') as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        need({'device': root.stat().st_dev, 'inode': root.stat().st_ino} == inode, 'Resource root replaced during audit')
        for item in journals:
            need(sha(Path(item['ref']['path'])) == item['ref']['sha256'], 'Resource journal changed during audit')
        result = {'root': str(root), 'root_identity': inode, 'owner': marker, 'owner_ref': marker_ref,
                  'owner_key_recomputed_from_exact_source_roots': True, 'journals': journals,
                  'exclusive_lease_available': True, 'remaining_devices': 0, 'remaining_directories': 0,
                  'remaining_process_or_lease': False}
        if str(root) in audited:
            need(audited[str(root)] == result, 'Conflicting current root proof')
        audited[str(root)] = result
        return result

    for _, config in configs.values():
        audit_root(config['resources']['root'], config)

    envelope_rows = []
    for operation in index['operations']:
        outcome = read(operation['outcome'])
        config_ref = outcome['config']
        config = read(config_ref)
        need(config_ref['path'] in configs and configs[config_ref['path']][0] == config_ref, 'Unregistered original operation config')
        if operation['kind'] == 'final-public-source-only':
            argv = outcome['argv']
            need(argv.count('--record') == 1, 'Exact public envelope argument required')
            envelope = Path(argv[argv.index('--record') + 1])
        else:
            envelope = Path(outcome['envelope_record'])
        need(envelope.parent == Path(operation['record']) and envelope.name.startswith('envelope-'), 'Envelope belongs to another operation')
        result_ref = ref(envelope / 'result.json')
        result = read(result_ref)
        need(result['config_sha256'] == config_ref['sha256'] and result['source_unchanged'] is True
             and result.get('error') is None, 'Original supervisor integrity failed')
        retirement_ref = ref(envelope / 'supervision/resources.json')
        retirement = read(retirement_ref)
        need(retirement.get('final') is True and retirement.get('remaining_devices') == []
             and retirement.get('remaining_directories') == [] and retirement.get('cleanup_errors') == [], 'Original supervisor did not retire its owned resources')
        expected_root = ROOT / 'cache/supervision' / envelope.name
        need(retirement['root'] == str(expected_root), 'Supervisor root differs from exact record')
        current = audit_root(expected_root, config)
        need(retirement['owner'] == current['owner'], 'Current supervisor owner differs from original receipt')
        journal_copy_ref = ref(envelope / 'supervision/resource-journal.json')
        journal_copy = read(journal_copy_ref)
        need(journal_copy['root_identity'] == current['root_identity']
             and journal_copy['token'] == current['owner']['token'], 'Supervisor root inode differs from its recorded exit checkpoint')
        envelope_rows.append({'operation_id': operation['operation_id'], 'config': config_ref,
                              'result': result_ref, 'retirement': retirement_ref,
                              'recorded_exit_journal': journal_copy_ref, 'root': current['root']})

    # The unforwarded permission failure remains failed. Its separate audit
    # proves that the original child never started; it is not a successful bind.
    failed_audit_path = ROOT / 'cache/business/independent-evaluation/post-consensus-validation-v1/FIRST-ENVIRONMENT-FAILURE-AUDIT.json'
    failed_audit_ref = {'path': str(failed_audit_path), 'sha256': FAILURE_AUDIT_SHA}
    read(failed_audit_ref)
    failed_refs = []
    for operation in index['operations']:
        for old in operation.get('retained_failed_attempts', []):
            failed_outcome = read(old['outcome'])
            config = read(failed_outcome['config'])
            envelope = Path(failed_outcome['envelope_record'])
            audit_root(ROOT / 'cache/supervision' / envelope.name, config)
            failed_refs.append(old['outcome'])
    need(len(failed_refs) == 1, 'Exactly one retained unforwarded environment entry expected')

    # Only this study's live native/supervisor commands are relevant. Meters
    # continue running until after the first verified archive and bulk cleanup.
    process = subprocess.run(['ps', '-axo', 'pid,ppid,command'], text=True, capture_output=True, check=True)
    forbidden = ['independent_native_v3.py', 'native_envelope.py', 'source_only_binding_v2.py', '/scripts/resource_manager.py']
    live = [line for line in process.stdout.splitlines() if str(ROOT) in line and any(token in line for token in forbidden)]
    need(not live, 'Study operation process is still live')

    public_proofs = {}
    for task in ['T1', 'T2', 'T3', 'T4', 'T5']:
        public_proofs[task] = {}
        for arm in ['A', 'B']:
            path = COORD / ('%s-%s-closure-verification.json' % (task, arm))
            reference = ref(path)
            closure = read(reference)
            for platform, proof in closure['positive_resource_closure'].items():
                original = read(proof['original'])
                need(original['final'] is True and original['remaining_devices'] == []
                     and original['remaining_directories'] == [] and original['cleanup_errors'] == [], 'Original public retirement remains incomplete')
                current = audited[original['root']]
                need(original['owner'] == current['owner'], 'Original public retirement owner differs from exact current root')
                journal_copy_ref = ref(Path(proof['original']['path']).parent / 'resource-journal.json')
                journal_copy = read(journal_copy_ref)
                need(journal_copy['root_identity'] == current['root_identity']
                     and journal_copy['token'] == current['owner']['token'], 'Public root inode differs from original retirement checkpoint')
            public_proofs[task][arm] = reference

    output = args.output.absolute()
    need(not output.exists(), 'Fresh final resource audit namespace required')
    output.mkdir(parents=True)

    def save(path, value):
        with path.open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        path.chmod(0o444)
        return ref(path)

    roots_ref = save(output / 'OWNED-ROOTS.json', {'version': 1, 'kind': 'current-positive-owned-root-audit',
        'at_unix': time.time(), 'source': ref(Path(__file__)), 'contexts': {'path': str(CONTEXTS), 'sha256': CONTEXTS_SHA},
        'binding_index': index_ref, 'roots': list(audited.values()), 'envelopes': envelope_rows,
        'retained_failed_outcomes': failed_refs, 'unforwarded_failure_audit': failed_audit_ref,
        'forbidden_live_study_processes': live, 'readset': readset,
        'sdk_operations': 0, 'deleted_resources': 0, 'historic_failures_promoted': False})
    by_task_arm = {task: {arm: {'closed': True, 'evidence': [roots_ref, public_proofs[task][arm]]}
                         for arm in ['A', 'B']} for task in public_proofs}
    closure_ref = save(output / 'CLOSURE.json', {'version': 1, 'kind': 'final-owned-resource-closure',
        'at_unix': time.time(), 'pending': [], 'by_task_arm': by_task_arm,
        'scope': 'Exact current config/supervisor ownership, inode, token, source-root owner key, journals and available leases; original public retirements retained. No SDK acquisition, cleanup or quality judgment.'})
    print(json.dumps({'closure': closure_ref, 'owned_roots': roots_ref, 'audited_roots': len(audited)}))


if __name__ == '__main__':
    main()
