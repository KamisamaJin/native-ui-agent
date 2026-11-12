"""Retained tiny synthetic controls; never run against actual replay/cache.

The frozen archive/cold code really packs, decodes and readonly-restores each
fixture. Its final consumer metadata is synthetic, explicitly not an actual
study success. Ordinary positive tests run the copied byte-exact helper CLI;
fault tests load the same bytes and schedule actual local namespace changes.
"""
import argparse
import contextlib
import errno
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time
import traceback
from unittest import mock


HERE = Path(__file__).resolve().parent
CODE_KEYS = ['cold', 'archive', 'preserve', 'session', 'session_replay', 'phase', 'projection', 'metric']
INPUT_KEYS = ['cause_index', 'alarm_index', 'correspondence_seal', 'mapping_reveal', 'coverage_registry', 'metric_inputs', 'metric_results', 'matcher_start']


def need(ok, message):
    if not ok: raise AssertionError(message)


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value, mode=0o444):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n'); path.chmod(mode)


def replace_json(path, callback):
    value = json.loads(path.read_bytes()); callback(value); path.chmod(0o644); write(path, value)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def raw_state(root):
    rows = {}
    for folder, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [n for n in dirs if not (Path(folder) / n).is_symlink()]
        for name in names:
            path = Path(folder) / name; value = path.lstat()
            if stat.S_ISREG(value.st_mode):
                rows[path.relative_to(root).as_posix()] = {'sha256': sha(path), 'inode': value.st_ino,
                    'device': value.st_dev, 'mode': stat.S_IMODE(value.st_mode), 'bytes': value.st_size,
                    'mtime_ns': value.st_mtime_ns}
    return rows


class Controls:
    def __init__(self, run):
        self.run = run; (run / 'CASES').mkdir(); self.results = []
        need(sha(HERE / 'vendor/archive.py') == 'c412b03c20c9c97b59a550bd5afa02c4c6fd58d0fbd6f9dc81a3bdf9b02796b8', 'Frozen archive differs')
        need(sha(HERE / 'vendor/cold_storage/cold.py') == '1df42e542466ff45db9fbc00c950be13f1bac2e1a1eb9ebb24e854068f0e8fda', 'Frozen decoder differs')
        self.cold = load(HERE / 'vendor/cold_storage/cold.py', 'cleanup_fixture_cold')
        self.archive = self.cold.archive_module()
        base = run / 'BASE'; base.mkdir(); source = base / 'original-source'; source.mkdir()
        files = []
        for name, raw in [('original.json', b'{"value":9007199254740993.0,"unknown":null}\r\n'),
                          ('same-a.bin', b'\x00equal\xff'), ('same-b.bin', b'\x00equal\xff'), ('empty.bin', b'')]:
            p = source / name; p.write_bytes(raw); p.chmod(0o644)
            files.append({'root': 'generic', 'path': str(p), 'logical_path': 'generic/' + name,
                          'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'mode': '0644'})
        spec = base / 'SPEC.json'; write(spec, {'version': 1, 'roots': [{'id': 'generic', 'kind': 'evidence', 'path': str(source)}], 'files': files})
        packed = self.archive.pack(spec, base / 'archive', 1)
        self.index = packed['index_sha256']; self.base_cold = base / 'cold'
        transported = self.cold.pack(str(base / 'archive'), self.index, str(self.base_cold))
        self.transport = transported['transport_sha256']; source.rename(base / 'retained-original-source')
        self.original_state = raw_state(base / 'retained-original-source')
        self.originals = files

    def fixture(self, case):
        workspace = case / 'checkout'; repo = workspace / 'validation/pooled-forward'
        helper = repo / 'publication-replay-cleanup/cleanup.py'; helper.parent.mkdir(parents=True)
        shutil.copyfile(HERE / 'cleanup.py', helper)
        temp = case / 'runner-temp'; temp.mkdir(); replay = temp / 'pooled-v13-replay'; replay.mkdir()
        code = {}
        for key in CODE_KEYS:
            path = repo / ('pinned-' + key + '.py')
            if key == 'archive': shutil.copyfile(HERE / 'vendor/archive.py', path)
            elif key == 'cold': shutil.copyfile(HERE / 'vendor/cold_storage/cold.py', path)
            else: path.write_bytes(('# synthetic authenticated metadata role: ' + key + '\n').encode())
            path.chmod(0o444); code[key] = {'path': path.name, 'sha256': sha(path)}
        transports = []
        for key, restore in [('main', True), ('auxiliary', False)]:
            directory = 'publications/' + key; source = repo / directory; source.mkdir(parents=True)
            for p in self.base_cold.iterdir(): shutil.copyfile(p, source / p.name); (source / p.name).chmod(0o444)
            transport = {'id': key, 'directory': directory, 'transport_sha256': self.transport,
                         'index_sha256': self.index, 'restore': restore}; transports.append(transport)
            output = replay / key; output.mkdir()
            decoded = self.cold.decode(str(source), self.transport, str(output / 'decoded'))
            inner = self.archive.verify(output / 'decoded', self.index)
            write(output / 'DECODED.json', {'transport': decoded, 'inner': inner})
            if restore:
                result = self.archive.restore(output / 'decoded', output / 'readonly-restore', self.index, True)
                write(output / 'RESTORED.json', result)
        manifest = {'version': 1, 'kind': 'pooled-forward-published-study', 'study_closed': True,
            'code': code, 'inputs': {key: {'path': '/synthetic-unopened-original/' + key, 'sha256': '0' * 64} for key in INPUT_KEYS},
            'preservation_plan': {'path': '/synthetic-unopened-original/plan', 'sha256': '1' * 64},
            'transports': transports, 'main_transport': 'main'}
        write(repo / 'PUBLICATION.json', manifest)
        (repo / 'PUBLICATION.sha256').write_text(sha(repo / 'PUBLICATION.json') + '\n')
        (repo / 'PUBLICATION.sha256').chmod(0o444)
        write(replay / 'ENTRY.json', {'manifest': str(repo / 'PUBLICATION.json'), 'manifest_sha256': sha(repo / 'PUBLICATION.json'),
                                     'started_at_unix': time.time(), 'native_sdk_execution': False})
        write(replay / 'RESULT.json', {'version': 1, 'kind': 'pooled-forward-publication-replay', 'status': 'verified',
             'cold_transports_verified': ['auxiliary', 'main'], 'readonly_original_key_payloads_verified': len(self.originals),
             'cause_contexts': 30, 'alarm_contexts': 30, 'independent_consensus_members': 1,
             'five_case_fixed_metrics_identical': True, 'source_domain_evaluation': 'unsupported',
             'source_responsibility_evaluation': 'unsupported', 'current_source_delivery_verified': False, 'native_sdk_execution': False})
        (replay / 'METRIC-REPLAY.json').write_bytes(b'{"synthetic_opaque_receipt":"keep unchanged","unknown":null}\n')
        (replay / 'RECORDED-PROVENANCE.json').write_bytes(b'{"synthetic":"keep"}\n')
        (replay / 'operator-failure-history.txt').write_bytes(b'preserved generic failure history\n')
        env = dict(os.environ, GITHUB_ACTIONS='true', RUNNER_TEMP=str(temp), GITHUB_WORKSPACE=str(workspace))
        return {'case': case, 'workspace': workspace, 'repo': repo, 'helper': helper, 'temp': temp, 'replay': replay, 'env': env}

    def case(self, name, callback):
        case = self.run / 'CASES' / name; case.mkdir()
        write(case / 'ENTRY.json', {'name': name, 'helper_sha256': sha(HERE / 'cleanup.py'), 'at_unix': time.time()})
        try: result = {'name': name, 'status': 'passed', 'evidence': callback(self.fixture(case))}
        except BaseException as error:
            result = {'name': name, 'status': 'failed', 'exception': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()}
        write(case / 'RESULT.json', result); self.results.append(result)
        print(json.dumps({'case': name, 'status': result['status'], 'message': result.get('message')}), flush=True)

    def invoke(self, ctx):
        command = [sys.executable, '-B', str(ctx['helper']), '--replay', str(ctx['replay'])]
        write(ctx['case'] / 'COMMAND.json', {'argv': command, 'ci_env': {k: ctx['env'][k] for k in ['GITHUB_ACTIONS', 'RUNNER_TEMP', 'GITHUB_WORKSPACE']}})
        completed = subprocess.run(command, env=ctx['env'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        (ctx['case'] / 'stdout.txt').write_bytes(completed.stdout); (ctx['case'] / 'stderr.txt').write_bytes(completed.stderr)
        return completed.returncode

    def positive(self, ctx, readonly=False):
        if readonly:
            for p in sorted(ctx['replay'].rglob('*'), reverse=True):
                if p.is_dir(): p.chmod(0o500)
        before_repo = raw_state(ctx['repo']); before_receipts = {p.relative_to(ctx['replay']).as_posix(): sha(p)
            for p in ctx['replay'].rglob('*') if p.is_file() and '/decoded/' not in str(p) and '/files/' not in str(p)}
        source = ctx['repo'] / 'publications/main/SEAL.json'; alias = ctx['replay'] / 'main/decoded/SEAL.json'
        need(source.stat().st_ino == alias.stat().st_ino, 'Fixture must exercise real shared raw transport alias')
        source_links = source.stat().st_nlink
        need(self.invoke(ctx) == 0, 'Positive CLI cleanup failed')
        need(before_repo == raw_state(ctx['repo']), 'Cleanup changed repository/cold bytes, mode or identity')
        need(source.stat().st_nlink == source_links - 1 and stat.S_IMODE(source.stat().st_mode) == 0o444, 'Unlink polluted shared cold source mode/link accounting')
        for key in ['main', 'auxiliary']: need(not (ctx['replay'] / key / 'decoded').exists(), 'Decoded scope remains')
        need(not (ctx['replay'] / 'main/readonly-restore/files').exists(), 'Readonly payload remains')
        for name, expected in before_receipts.items(): need(sha(ctx['replay'] / name) == expected, 'Compact metadata/map/failure history changed')
        result = json.loads((ctx['replay'] / 'CLEANUP.json').read_bytes())
        need(result['status'] == 'completed' and result['file_chmod_calls'] == 0 and not result['physical_bytes_freed_measured'], 'Invalid cleanup scope receipt')
        need(result['files_unlinked'] == len(self.originals) + 2 * len(json.loads((self.base_cold / 'TRANSPORT.json').read_bytes())['files']), 'Removed file count differs')
        if readonly:
            need(stat.S_IMODE((ctx['replay'] / 'main').stat().st_mode) == 0o500, 'Retained generated directory mode not restored')
        # Existing CLEANUP is an immutable one-shot barrier, never an auto retry.
        completed_state = raw_state(ctx['replay'])
        again = subprocess.run([sys.executable, '-B', str(ctx['helper']), '--replay', str(ctx['replay'])], env=ctx['env'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (ctx['case'] / 'repeat.stderr.txt').write_bytes(again.stderr)
        need(again.returncode != 0 and completed_state == raw_state(ctx['replay']), 'Repeated cleanup mutated a completed output')
        return {'cleanup': result, 'all_repo_cold_bytes_modes_unchanged': True, 'all_compact_receipts_retained': True,
                'readonly_directories': readonly, 'repeat_rejected_unchanged': True, 'cleanup_sha256': sha(ctx['replay'] / 'CLEANUP.json')}

    def negative(self, ctx, attack):
        replay = ctx['replay']; repo = ctx['repo']
        if attack == 'non-ci': ctx['env']['GITHUB_ACTIONS'] = 'false'
        elif attack == 'wrong-temp':
            p = ctx['case'] / 'other-temp'; p.mkdir(); ctx['env']['RUNNER_TEMP'] = str(p)
        elif attack == 'wrong-workspace': ctx['env']['GITHUB_WORKSPACE'] = str(ctx['case'] / 'other-checkout')
        elif attack == 'unsafe-prefix-suffix': ctx['replay'] = ctx['temp'] / 'pooled-v13-replay-extra'
        elif attack == 'missing-result': (replay / 'RESULT.json').rename(ctx['case'] / 'retained-result.json')
        elif attack == 'failed-result': replace_json(replay / 'RESULT.json', lambda v: v.update(status='failed'))
        elif attack == 'wrong-entry-pin': replace_json(replay / 'ENTRY.json', lambda v: v.update(manifest_sha256='0' * 64))
        elif attack == 'wrong-entry-path': replace_json(replay / 'ENTRY.json', lambda v: v.update(manifest=str(repo / 'OTHER.json')))
        elif attack == 'wrong-repo-external-pin':
            p = repo / 'PUBLICATION.sha256'; p.chmod(0o644); p.write_text('0' * 64 + '\n'); p.chmod(0o444)
        elif attack == 'extra-output-directory': (replay / 'unregistered-transport').mkdir()
        elif attack == 'readonly-source-violated': (repo / 'publications/main/SEAL.json').chmod(0o644)
        elif attack == 'duplicate-logical-inode':
            files = replay / 'main/readonly-restore/files/generic'; (files / 'same-b.bin').unlink(); os.link(files / 'same-a.bin', files / 'same-b.bin')
        elif attack == 'unmapped-payload': (replay / 'main/readonly-restore/files/unlisted').write_bytes(b'not mapped')
        elif attack == 'fifo': os.mkfifo(replay / 'main/readonly-restore/files/fifo', 0o400)
        elif attack == 'symlink-payload':
            p = replay / 'main/readonly-restore/files/generic/original.json'; p.unlink(); p.symlink_to(ctx['case'] / 'outside-do-not-follow')
        elif attack == 'symlink-temp':
            link = ctx['case'] / 'temp-alias'; link.symlink_to(ctx['temp'], target_is_directory=True)
            ctx['env']['RUNNER_TEMP'] = str(link); ctx['replay'] = link / 'pooled-v13-replay'
        elif attack == 'symlink-replay':
            replay.rename(ctx['case'] / 'retained-replay'); replay.symlink_to(ctx['case'] / 'retained-replay', target_is_directory=True)
        elif attack == 'malformed-authoritative-restore':
            replace_json(repo / 'PUBLICATION.json', lambda v: v['transports'][1].update(restore=True))
            self.repin(ctx)
        elif attack == 'unicode-authoritative-id':
            replace_json(repo / 'PUBLICATION.json', lambda v: v['transports'][1].update(id='Δ'))
            self.repin(ctx)
        elif attack == 'false-readonly-map':
            p = replay / 'main/readonly-restore/RESTORED-MAP.json'
            replace_json(p, lambda v: next(iter(v['mappings'].values())).update(restored_mode='0644'))
        elif attack == 'altered-map-original-key':
            p = replay / 'main/readonly-restore/RESTORED-MAP.json'
            def alter(value):
                original = next(iter(value['mappings'])); row = value['mappings'].pop(original)
                value['mappings']['/different-unopened-original/' + Path(original).name] = row
            replace_json(p, alter)
        elif attack == 'altered-map-logical-path':
            p = replay / 'main/readonly-restore/RESTORED-MAP.json'
            def alter(value):
                row = next(iter(value['mappings'].values())); old = Path(row['physical_path'])
                new = old.parent.parent / 'other' / old.name; new.parent.mkdir(); old.rename(new)
                row.update(logical_path='other/' + old.name, physical_path=str(new))
            replace_json(p, alter)
        else: raise AssertionError('Unknown fixture')
        before_repo = raw_state(repo); before_output = raw_state(replay if not replay.is_symlink() else ctx['case'] / 'retained-replay')
        result = self.invoke(ctx)
        need(result != 0, 'Hostile cleanup gate accepted')
        need(before_repo == raw_state(repo), 'Rejected cleanup changed cold/repo source')
        physical = replay if not replay.is_symlink() else ctx['case'] / 'retained-replay'
        need(before_output == raw_state(physical), 'Rejected gate changed generated regular bytes/modes')
        need(not list(physical.glob('CLEANUP*')), 'Preflight rejection created cleanup records')
        return {'attack': attack, 'rejected': True, 'replay_repo_cold_unchanged': True, 'returncode': result}

    def repin(self, ctx):
        p = ctx['repo'] / 'PUBLICATION.sha256'; p.chmod(0o644); p.write_text(sha(ctx['repo'] / 'PUBLICATION.json') + '\n'); p.chmod(0o444)
        replace_json(ctx['replay'] / 'ENTRY.json', lambda v: v.update(manifest_sha256=sha(ctx['repo'] / 'PUBLICATION.json')))

    def fault(self, ctx, attack):
        subject = load(ctx['helper'], 'cleanup_fault_' + attack.replace('-', '_'))
        before_repo = raw_state(ctx['repo']); caught = None; calls = []; real_chmod = os.fchmod; real_unlink = os.unlink
        def checked_chmod(fd, mode):
            need(stat.S_ISDIR(os.fstat(fd).st_mode), 'Helper attempted chmod on a regular file')
            calls.append({'kind': 'directory-fchmod', 'inode': os.fstat(fd).st_ino, 'mode': mode}); return real_chmod(fd, mode)
        def point(name):
            if attack == 'receipt-preempt' and name == 'before_intent': (ctx['replay'] / 'CLEANUP-INTENT.json').write_bytes(b'keep preempting receipt')
            elif attack == 'member-preempt' and name == 'before_remove':
                p = ctx['replay'] / 'main/readonly-restore/files/generic/empty.bin'
                p.rename(ctx['case'] / 'retained-member'); p.write_bytes(b'keep competing member'); p.chmod(0o444)
            elif attack == 'parent-symlink-preempt' and name == 'after_intent':
                p = ctx['replay'] / 'main'; p.rename(ctx['case'] / 'retained-main'); p.symlink_to(ctx['case'] / 'retained-main', target_is_directory=True)
            elif attack == 'root-symlink-preempt' and name == 'after_intent':
                p = ctx['replay']; p.rename(ctx['case'] / 'retained-output'); p.symlink_to(ctx['case'] / 'retained-output', target_is_directory=True)
        unlink_count = 0
        def interrupted_unlink(*args, **kwargs):
            nonlocal unlink_count
            unlink_count += 1
            if unlink_count == 2: raise OSError(errno.EIO, 'synthetic interrupted CI deletion')
            return real_unlink(*args, **kwargs)
        patches = [mock.patch.dict(os.environ, ctx['env'], clear=True), mock.patch.object(subject, 'checkpoint', side_effect=point),
                   mock.patch.object(subject.os, 'fchmod', side_effect=checked_chmod),
                   mock.patch.object(subject.os, 'chmod', side_effect=AssertionError('Path chmod forbidden'))]
        if attack == 'partial-unlink-failure': patches.append(mock.patch.object(subject.os, 'unlink', side_effect=interrupted_unlink))
        if attack == 'wrong-uid': patches.append(mock.patch.object(subject, 'UID', os.geteuid() + 1))
        with contextlib.ExitStack() as stack:
            for patch in patches: stack.enter_context(patch)
            try: receipt = subject.cleanup(str(ctx['replay']))
            except (ValueError, OSError) as error: caught = {'type': type(error).__name__, 'message': str(error)}
        need(before_repo == raw_state(ctx['repo']), 'Faulted cleanup changed cold/repository sources')
        if attack == 'directory-chmod-only':
            need(caught is None and receipt['file_chmod_calls'] == 0, 'Instrumented normal cleanup failed')
        else: need(caught is not None, 'Preemption/failure/uid fault did not block cleanup')
        physical = ctx['case'] / 'retained-output' if attack == 'root-symlink-preempt' else ctx['replay']
        if attack == 'member-preempt': need((ctx['replay'] / 'main/readonly-restore/files/generic/empty.bin').read_bytes() == b'keep competing member', 'Preempting member deleted')
        if attack == 'receipt-preempt': need((ctx['replay'] / 'CLEANUP-INTENT.json').read_bytes() == b'keep preempting receipt', 'Preempting receipt overwritten')
        if attack == 'partial-unlink-failure':
            failed = json.loads((physical / 'CLEANUP-FAILED.json').read_bytes())
            need(failed['files_unlinked'] == 1 and not (physical / 'CLEANUP.json').exists(), 'Partial failure was hidden or rolled back')
        return {'attack': attack, 'caught': caught, 'directory_chmod_calls': calls, 'source_unchanged': True,
                'intent_exists': (physical / 'CLEANUP-INTENT.json').exists(), 'failure_exists': (physical / 'CLEANUP-FAILED.json').exists(),
                'success_exists': (physical / 'CLEANUP.json').exists()}

    def run_all(self):
        self.case('positive-cli-shared-alias-one-shot', self.positive)
        self.case('positive-readonly-generated-directories', lambda c: self.positive(c, readonly=True))
        for attack in ['non-ci', 'wrong-temp', 'wrong-workspace', 'unsafe-prefix-suffix', 'missing-result', 'failed-result',
                       'wrong-entry-pin', 'wrong-entry-path', 'wrong-repo-external-pin', 'extra-output-directory',
                       'readonly-source-violated', 'duplicate-logical-inode', 'unmapped-payload', 'fifo', 'symlink-payload',
                       'symlink-temp', 'symlink-replay', 'malformed-authoritative-restore', 'unicode-authoritative-id', 'false-readonly-map',
                       'altered-map-original-key', 'altered-map-logical-path']:
            self.case(attack, lambda c, a=attack: self.negative(c, a))
        for attack in ['directory-chmod-only', 'receipt-preempt', 'member-preempt', 'parent-symlink-preempt', 'root-symlink-preempt',
                       'partial-unlink-failure', 'wrong-uid']:
            self.case(attack, lambda c, a=attack: self.fault(c, a))
        unchanged = self.original_state == raw_state(self.run / 'BASE/retained-original-source')
        result = {'version': 1, 'kind': 'synthetic-ci-only-replay-cleanup-controls',
                  'helper_sha256': sha(HERE / 'cleanup.py'), 'test_source_sha256': sha(Path(__file__)),
                  'passed': sum(r['status'] == 'passed' for r in self.results), 'failed': sum(r['status'] == 'failed' for r in self.results),
                  'results': self.results, 'generic_original_dataset_unchanged': unchanged,
                  'scope': 'Only tiny synthetic CI namespaces were deleted. Environment is simulated, actual archive/SDK/cache/grades were never accessed.'}
        write(self.run / 'RESULT.json', result); need(unchanged, 'Generic original source changed')
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--run-dir', required=True); args = parser.parse_args()
    run = Path(args.run_dir); need(run.is_absolute() and run.is_relative_to(HERE) and not run.exists(), 'Fresh retained synthetic output within own root required')
    run.mkdir(); write(run / 'ENTRY.json', {'test_source_sha256': sha(Path(__file__)), 'helper_sha256': sha(HERE / 'cleanup.py'), 'at_unix': time.time()})
    result = Controls(run).run_all()
    print(json.dumps({'result': str(run / 'RESULT.json'), 'sha256': sha(run / 'RESULT.json'), 'passed': result['passed'], 'failed': result['failed']}))
    return result['failed'] != 0


if __name__ == '__main__': raise SystemExit(main())
