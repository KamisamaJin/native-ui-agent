"""Small retained controls for the frozen derived-transport sharing operator.

Only the previously sealed generic synthetic fixture is consumed. Ordinary
controls run the exact pinned CLI. Fault controls load that same byte-exact
module and schedule real link failures/mode changes, without replacing its
frozen v2/archive verification or permission/hash checks.
"""
import argparse
import contextlib
import errno
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

from run_review import HERE, digest, file_sha, inode, load_module, need, save, snapshot, change


OPERATOR = HERE / 'vendor/operator-project/operators/share_transport_copies_v1.py'
OPERATOR_PIN = '548a4c00c864533b6dfb4cfe0cade6da4471eb20126641096e38cc9282942582'
FIXTURE_RUN = HERE / 'HOST/attempt-1'
FIXTURE_RESULT_SHA = '3fe5d46dcda4ad7c04701c0e67736ef6a6af0cfd316697d57ef4a9293f08cf4c'


class OperatorReview:
    def __init__(self, run):
        self.run = run; (run / 'CASES').mkdir(); self.results = []
        need(file_sha(OPERATOR) == OPERATOR_PIN, 'Frozen sharing operator pin differs')
        for relative, row in json.loads((HERE / 'OPERATOR-SOURCE-PINS.json').read_bytes()).items():
            need(file_sha(HERE / relative) == row['sha256'], 'Frozen sharing dependency pin differs')
        need(file_sha(FIXTURE_RUN / 'RESULT.json') == FIXTURE_RESULT_SHA, 'External generic fixture result pin differs')
        self.fixture = json.loads((FIXTURE_RUN / 'FIXTURE/FIXTURE.json').read_bytes())
        fixture_result = json.loads((FIXTURE_RUN / 'RESULT.json').read_bytes())
        need(file_sha(FIXTURE_RUN / 'FIXTURE/FIXTURE.json') == fixture_result['fixture']['sha256'], 'Fixture pin differs')
        self.fixture_dir = FIXTURE_RUN / 'FIXTURE'
        self.raw_names = sorted(n for n in self.fixture['archive_members'] if n == 'SEAL.json' or n.startswith('shard-'))
        self.archive_module = load_module('operator_review_archive', HERE / 'vendor/v3/publication-tools/archive.py')
        self.resolver_module = load_module('operator_review_resolver', HERE / 'vendor/resolver.py')
        self.retained_source = self.fixture_dir / 'retained-original-source'
        self.retained_source_before = {p.name: snapshot(p) for p in self.retained_source.iterdir()}

    def fixture_copy(self, case):
        cache = case / 'cache'; cache.mkdir()
        publication = cache / 'publication-archives'; publication.mkdir()
        archive = publication / 'derived-archive'; archive.mkdir()
        cold = case / 'cold'; cold.mkdir()
        for src, target in [(self.fixture_dir / 'retained-original-archive', archive), (self.fixture_dir / 'cold', cold)]:
            for path in src.iterdir():
                copied = target / path.name; shutil.copyfile(path, copied)
                copied.chmod(stat.S_IMODE(path.lstat().st_mode))
                need(inode(copied) != inode(path), 'Test fixture copy unexpectedly shared input storage')
        marker = cache / 'OWNER.json'
        save(marker, {'version': 1, 'kind': 'generic-synthetic-owned-cache', 'owner_token': case.name})
        authority = case / 'OWNER-AUTHORITY.json'
        save(authority, {'path': str(cache), 'device': cache.stat().st_dev,
                         'inode': cache.stat().st_ino, 'marker_sha256': file_sha(marker)})
        return {'case': case, 'cache': cache, 'archive': archive, 'cold': cold,
                'authority': authority, 'authority_pin': file_sha(authority),
                'transport_pin': self.fixture['transport_sha256'], 'output': case / 'receipts'}

    def arguments(self, ctx):
        return ['--archive', str(ctx['archive']), '--cold', str(ctx['cold']),
                '--owner-authority', str(ctx['authority']), '--output', str(ctx['output']),
                '--transport-sha256', ctx['transport_pin'], '--owner-authority-sha256', ctx['authority_pin']]

    def invoke(self, ctx, *, label='command'):
        command = [sys.executable, '-B', str(OPERATOR), *self.arguments(ctx)]
        save(ctx['case'] / (label + '.json'), {'argv': command, 'operator_sha256': OPERATOR_PIN,
                                             'kind': 'synthetic-only-subprocess-invocation'})
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        (ctx['case'] / (label + '.stdout.txt')).write_bytes(result.stdout)
        (ctx['case'] / (label + '.stderr.txt')).write_bytes(result.stderr)
        return {'returncode': result.returncode, 'stdout_sha256': digest(result.stdout),
                'stderr_sha256': digest(result.stderr)}

    def case(self, name, callback):
        case = self.run / 'CASES' / name; case.mkdir()
        save(case / 'ENTRY.json', {'name': name, 'operator_sha256': OPERATOR_PIN,
                                  'started_at_unix': time.time(), 'kind': 'synthetic-only-operator-control'})
        try:
            result = {'name': name, 'status': 'passed', 'evidence': callback(case)}
        except BaseException as error:
            result = {'name': name, 'status': 'failed', 'exception': type(error).__name__,
                      'message': str(error), 'traceback': traceback.format_exc()}
        result['finished_at_unix'] = time.time()
        save(case / 'RESULT.json', result); self.results.append(result)
        print(json.dumps({'case': name, 'status': result['status'], 'message': result.get('message')}), flush=True)

    def archive_snapshot(self, folder): return {p.name: snapshot(p) for p in folder.iterdir()}

    def positive(self, case):
        ctx = self.fixture_copy(case)
        archive_before = self.archive_snapshot(ctx['archive']); cold_before = self.archive_snapshot(ctx['cold'])
        first = self.invoke(ctx)
        need(first['returncode'] == 0, 'Positive sharing CLI failed')
        end = json.loads((ctx['output'] / 'END.json').read_bytes())
        need(end['status'] == 'verified' and not end['logical_dataset_payload_deduplicated'], 'Invalid sharing receipt')
        need(self.archive_module.verify(ctx['archive'], self.fixture['index_sha256'])['files'] == 5,
             'Logical archive file count changed')
        archive_after = self.archive_snapshot(ctx['archive']); cold_after = self.archive_snapshot(ctx['cold'])
        need(set(archive_before) == set(archive_after), 'Archive names changed')
        need(set(cold_before) == set(cold_after), 'Cold names changed')
        for name, old in archive_before.items():
            need(old['sha256'] == archive_after[name]['sha256'], 'Derived archive byte content changed')
            if name in self.raw_names:
                need(inode(ctx['archive'] / name) == inode(ctx['cold'] / name), 'Raw derived copy did not share cold inode')
                need(archive_before[name]['inode'] != archive_after[name]['inode'], 'Fresh raw target inode was not replaced')
            else:
                need(old == archive_after[name], 'INDEX/SPEC metadata was modified or shared')
        for name, old in cold_before.items():
            for key in ['device', 'inode', 'bytes', 'mode', 'mtime_ns', 'sha256']:
                need(old[key] == cold_after[name][key], 'Cold input changed outside intentional link ctime/nlink')
        after_ids = {name: inode(ctx['archive'] / name) for name in self.raw_names}
        nlinks = {name: (ctx['cold'] / name).stat().st_nlink for name in self.raw_names}
        ctx['output'] = case / 'second-receipts'
        second = self.invoke(ctx, label='second-command')
        need(second['returncode'] == 0, 'Idempotent sharing CLI failed')
        need(after_ids == {name: inode(ctx['archive'] / name) for name in self.raw_names}, 'Idempotent run replaced existing aliases')
        need(nlinks == {name: (ctx['cold'] / name).stat().st_nlink for name in self.raw_names}, 'Idempotent run leaked links')
        second_end = json.loads((ctx['output'] / 'END.json').read_bytes())
        need(second_end['namespace_allocation_difference_bytes'] == 0, 'Idempotent run reported nonexistent namespace allocation change')
        restored = case / 'restored'
        restored_result = self.archive_module.restore(ctx['archive'], restored, self.fixture['index_sha256'], True)
        mapping = restored / 'RESTORED-MAP.json'
        reader = self.resolver_module.Resolver(mapping, map_sha256=file_sha(mapping), index_sha256=self.fixture['index_sha256'])
        for row in self.fixture['files']:
            need(not Path(row['path']).exists(), 'Original logical key unexpectedly exists')
            need(reader.hash(row['path']) == row['sha256'], 'Restored logical bytes changed')
        first_payload, second_payload = [reader.file(row['path']) for row in self.fixture['files']
                                         if Path(row['path']).name in {'same-a.bin', 'same-b.bin'}]
        need(first_payload.read_bytes() == second_payload.read_bytes() and inode(first_payload) != inode(second_payload),
             'Sharing operator deduplicated logical dataset payloads')
        return {'first_cli': first, 'second_cli': second,
                'first_receipt_sha256': file_sha(case / 'receipts/END.json'),
                'second_receipt_sha256': file_sha(case / 'second-receipts/END.json'),
                'restored': restored_result, 'map_sha256': file_sha(mapping),
                'archive_before': archive_before, 'archive_after': archive_after,
                'cold_before': cold_before, 'cold_after': cold_after,
                'all_names_bytes_preserved': True, 'logical_payloads_distinct_inodes': True}

    def negative(self, case, attack):
        ctx = self.fixture_copy(case)
        if attack == 'wrong-owner-pin': ctx['authority_pin'] = '0' * 64
        elif attack == 'wrong-transport-pin': ctx['transport_pin'] = '0' * 64
        elif attack == 'wrong-owner-inode':
            value = json.loads(ctx['authority'].read_bytes()); value['inode'] += 1
            change(ctx['authority'], json.dumps(value).encode()); ctx['authority_pin'] = file_sha(ctx['authority'])
        elif attack == 'changed-owner-marker': change(ctx['cache'] / 'OWNER.json', b'changed owner marker')
        elif attack == 'outside-owned-derived-prefix':
            moved = case / 'unowned-derived-copy'; ctx['archive'].rename(moved); ctx['archive'] = moved
        elif attack == 'changed-derived-bytes':
            path = ctx['archive'] / self.raw_names[0]; change(path, path.read_bytes() + b'wrong')
        elif attack == 'changed-cold-bytes':
            path = ctx['cold'] / self.raw_names[0]; change(path, path.read_bytes() + b'wrong')
        elif attack == 'writable-cold-source': (ctx['cold'] / self.raw_names[0]).chmod(0o644)
        elif attack == 'raw-cold-symlink':
            path = ctx['cold'] / self.raw_names[0]; outside = case / 'same-raw-bytes'
            outside.write_bytes(path.read_bytes()); path.unlink(); path.symlink_to(outside)
        elif attack == 'extra-cold-member': (ctx['cold'] / 'extra-member').write_bytes(b'not authorized')
        else: raise AssertionError('Unknown operator hostile fixture')
        before = self.archive_snapshot(ctx['archive'])
        result = self.invoke(ctx)
        need(result['returncode'] != 0, 'Operator accepted hostile authority/pin/bytes/namespace')
        need(not ctx['output'].exists(), 'Preflight rejection created a mutation receipt directory')
        need(before == self.archive_snapshot(ctx['archive']), 'Rejected preflight altered derived archive')
        need(not list(ctx['archive'].parent.glob('transport-share-*')), 'Rejected preflight created a staging directory')
        return {'attack': attack, 'cli': result, 'derived_archive_unchanged': True, 'rejected_before_output': True}

    def scheduled(self, case, attack):
        ctx = self.fixture_copy(case)
        module = load_module('review_sharing_' + attack.replace('-', '_'), OPERATOR)
        real_link = os.link; calls = []
        def hook(source, target, **kwargs):
            source, target = Path(source), Path(target)
            calls.append({'source': str(source), 'target': str(target)})
            if attack == 'exdev': raise OSError(errno.EXDEV, 'synthetic unsupported link filesystem')
            if attack == 'mode-change-during-link' and len(calls) == 1:
                source.chmod(0o644)
            result = real_link(source, target, **kwargs)
            if attack == 'later-cold-corruption' and len(calls) == 1:
                future = ctx['cold'] / self.raw_names[-1]
                change(future, future.read_bytes() + b'after initial inventory')
            return result
        stdout = io.StringIO(); error = None
        command = [str(OPERATOR), *self.arguments(ctx)]
        save(case / 'FAULT-SCHEDULE.json', {'argv': command, 'attack': attack,
             'operator_sha256': OPERATOR_PIN, 'fault_boundary': 'real os.link',
             'archive_verifier_hashing_and_permission_checks_unchanged': True})
        with mock.patch.object(sys, 'argv', command), mock.patch.object(module.os, 'link', side_effect=hook), contextlib.redirect_stdout(stdout):
            try: module.main()
            except (ValueError, OSError) as caught: error = {'type': type(caught).__name__, 'message': str(caught)}
        (case / 'fault.stdout.txt').write_text(stdout.getvalue())
        writable = [str(path) for folder in [ctx['cold'], ctx['archive']] for path in folder.iterdir()
                    if path.name in self.raw_names and stat.S_IMODE(path.lstat().st_mode) & 0o222]
        observation = {'attack': attack, 'calls': calls, 'caught_error': error,
                       'intent_exists': (ctx['output'] / 'INTENT.json').is_file(),
                       'end_exists': (ctx['output'] / 'END.json').is_file(),
                       'failed_exists': (ctx['output'] / 'FAILED.json').is_file(),
                       'writable_raw_paths_after': writable,
                       'stages_retained': [str(p) for p in ctx['archive'].parent.glob('transport-share-*')],
                       'cold_after': self.archive_snapshot(ctx['cold']),
                       'archive_after': self.archive_snapshot(ctx['archive'])}
        save(case / 'OBSERVATION.json', observation)
        need(len(calls) >= 1 and observation['intent_exists'], 'Fault did not reach the intended semantic mutation boundary')
        need(error is not None and observation['failed_exists'] and not observation['end_exists'],
             'Operator accepted changed/unsupported source state instead of retaining a failure')
        need(observation['stages_retained'], 'Operator deleted its partial-failure staging proof')
        if attack == 'later-cold-corruption':
            need(inode(ctx['cold'] / self.raw_names[0]) == inode(ctx['archive'] / self.raw_names[0]),
                 'Partial success was not preserved before the subsequent failure')
        return observation

    def run_all(self):
        self.case('positive-cli-idempotence-restore-resolver', self.positive)
        for attack in ['wrong-owner-pin', 'wrong-transport-pin', 'wrong-owner-inode', 'changed-owner-marker',
                       'outside-owned-derived-prefix', 'changed-derived-bytes', 'changed-cold-bytes',
                       'writable-cold-source', 'raw-cold-symlink', 'extra-cold-member']:
            self.case(attack, lambda c, a=attack: self.negative(c, a))
        for attack in ['exdev', 'later-cold-corruption', 'mode-change-during-link']:
            self.case('scheduled-' + attack, lambda c, a=attack: self.scheduled(c, a))
        retained_source_after = {p.name: snapshot(p) for p in self.retained_source.iterdir()}
        unchanged = retained_source_after == self.retained_source_before
        result = {'version': 1, 'kind': 'independent-synthetic-derived-transport-sharing-review',
            'operator_sha256': OPERATOR_PIN, 'test_source_sha256': file_sha(Path(__file__)),
            'operator_source_pins_sha256': file_sha(HERE / 'OPERATOR-SOURCE-PINS.json'),
            'fixture_result_sha256': FIXTURE_RESULT_SHA,
            'passed': sum(r['status'] == 'passed' for r in self.results),
            'failed': sum(r['status'] == 'failed' for r in self.results), 'results': self.results,
            'generic_original_dataset_source_identity_bytes_unchanged': unchanged,
            'retained_source_before': self.retained_source_before, 'retained_source_after': retained_source_after,
            'scope': 'No actual archive/data/cleanup. Allocation fields refer only to this small synthetic namespace; no APFS freed-space, budget or treatment-benefit claim.'}
        save(self.run / 'RESULT.json', result)
        need(unchanged, 'Generic original dataset source was changed by the operator controls')
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--run-dir', required=True)
    args = parser.parse_args(); run = Path(args.run_dir)
    need(run.is_absolute() and str(run) == args.run_dir and not run.exists() and run.is_relative_to(HERE),
         'Fresh retained run directory within the exclusive review root required')
    run.mkdir()
    save(run / 'ENTRY.json', {'test_source_sha256': file_sha(Path(__file__)), 'started_at_unix': time.time(),
                             'kind': 'synthetic-only-operator-review-entry'})
    result = OperatorReview(run).run_all()
    print(json.dumps({'result': str(run / 'RESULT.json'), 'sha256': file_sha(run / 'RESULT.json'),
                      'passed': result['passed'], 'failed': result['failed']}), flush=True)
    return 1 if result['failed'] else 0


if __name__ == '__main__': raise SystemExit(main())
