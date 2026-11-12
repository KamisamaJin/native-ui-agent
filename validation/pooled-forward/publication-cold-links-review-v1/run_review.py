"""Retained, synthetic-only independent controls for frozen cold v2/v3.

Run in a fresh owned directory. No original datasets, SDK, network, cleanup,
selection authority, code edits, or product conclusions are part of this test.
Fault hooks schedule real local filesystem operations; they never replace the
frozen archive verification, hashing, byte comparison, or restore verdicts.
"""
import argparse
import contextlib
import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import sys
import time
import traceback
from unittest import mock
import zlib


HERE = Path(__file__).resolve().parent
REJECTIONS = (ValueError, OSError, EOFError, zlib.error)
PINNED = {
    'vendor/v2/publication-tools/cold_storage/cold.py': 'b5f8ad775e68312928b1d3cc9e2c5807edb47083a33929dd4f86611d459d0991',
    'vendor/v3/publication-tools/cold_storage/cold.py': '1df42e542466ff45db9fbc00c950be13f1bac2e1a1eb9ebb24e854068f0e8fda',
    'vendor/v3/AUTHOR-FREEZE.json': '7706084181c8082ac8f42987f9b0f17892fc04e6988db04f4ace674930f6c653',
    'vendor/v2/publication-tools/archive.py': 'c412b03c20c9c97b59a550bd5afa02c4c6fd58d0fbd6f9dc81a3bdf9b02796b8',
    'vendor/v3/publication-tools/archive.py': 'c412b03c20c9c97b59a550bd5afa02c4c6fd58d0fbd6f9dc81a3bdf9b02796b8',
    'vendor/resolver.py': '2a5ec0949b5a64cb3f1dc57df87b3954e1f5e1f21ea58defec3ced44b5ba8204',
    'vendor/session/session.py': '9502fc59697f039021a4a2c9f5046ea2f46d32a235613ceb2c719709573c425c',
}


def digest(raw): return hashlib.sha256(raw).hexdigest()
def file_sha(path): return digest(path.read_bytes())
def need(value, message):
    if not value: raise AssertionError(message)


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot(path):
    value = path.lstat()
    result = {'device': value.st_dev, 'inode': value.st_ino,
              'bytes': value.st_size, 'mode': format(stat.S_IMODE(value.st_mode), '04o'),
              'mtime_ns': value.st_mtime_ns, 'ctime_ns': value.st_ctime_ns,
              'nlink': value.st_nlink}
    if stat.S_ISREG(value.st_mode): result['sha256'] = file_sha(path)
    elif stat.S_ISLNK(value.st_mode): result['symlink'] = os.readlink(path)
    else: result['kind'] = 'directory' if stat.S_ISDIR(value.st_mode) else 'other'
    return result


def inode(path):
    value = path.lstat()
    return value.st_dev, value.st_ino


def change(path, raw, mode=None):
    old_mode = stat.S_IMODE(path.lstat().st_mode)
    path.chmod(0o600); path.write_bytes(raw)
    path.chmod(old_mode if mode is None else mode)


def rewrite_transport(folder, mutate):
    path = folder / 'TRANSPORT.json'
    value = json.loads(path.read_bytes()); mutate(value)
    change(path, (json.dumps(value, sort_keys=True, indent=2) + '\n').encode())
    return file_sha(path)


def rejected(call, *, before_output=None):
    try:
        result = call()
    except REJECTIONS as error:
        if before_output is not None:
            need(not before_output.exists(), 'Rejected input created an output before validation')
        return {'rejected': True, 'exception': type(error).__name__, 'message': str(error)}
    raise AssertionError('Frozen implementation accepted a hostile input: ' + repr(result))


class Review:
    def __init__(self, run):
        self.run = run; self.cases = run / 'CASES'; self.cases.mkdir()
        self.results = []
        source_pins = json.loads((HERE / 'SOURCE-PINS.json').read_bytes())
        for relative, row in source_pins.items():
            need(file_sha(HERE / relative) == row['sha256'], 'Vendored source pin differs: ' + relative)
        for relative, sha in PINNED.items():
            need(source_pins[relative]['sha256'] == sha and file_sha(HERE / relative) == sha,
                 'Externally fixed source pin differs: ' + relative)
        freeze = json.loads((HERE / 'vendor/v3/AUTHOR-FREEZE.json').read_bytes())
        for relative, sha in freeze['files'].items():
            need(file_sha(HERE / 'vendor/v3' / relative) == sha, 'Author source inventory differs')
        self.modules = {version: load_module('review_cold_' + version,
                           HERE / 'vendor' / version / 'publication-tools/cold_storage/cold.py')
                        for version in ['v2', 'v3']}
        self.archive = self.modules['v3'].archive_module()
        self.resolver = load_module('review_resolver', HERE / 'vendor/resolver.py')
        self.session = load_module('review_map_session', HERE / 'vendor/session/session.py')
        self.make_fixture()

    def make_fixture(self):
        fixture = self.run / 'FIXTURE'; fixture.mkdir()
        source = fixture / 'source'; source.mkdir()
        # One multi-chunk file; two distinct logical files with equal bytes;
        # unparsed JSON lexical precision/Unicode/CRLF and an empty payload.
        raw_json = '{"actual":9007199254740993.0,"unknown":null,"text":"한글/é/🧪"}\r\n'.encode('utf-8')
        self.payloads = {'original.json': raw_json, 'same-a.bin': b'\x00same logical bytes\xff\n',
                         'same-b.bin': b'\x00same logical bytes\xff\n', 'empty.bin': b'',
                         'multi-chunk.bin': bytes(range(256)) * 4500}
        rows = []
        self.originals = {}
        for name, raw in self.payloads.items():
            path = source / name; path.write_bytes(raw); path.chmod(0o644)
            self.originals[name] = str(path)
            rows.append({'root': 'source', 'path': str(path), 'logical_path': 'source/' + name,
                         'sha256': digest(raw), 'bytes': len(raw), 'mode': '0644'})
        spec = fixture / 'SPEC.original.json'
        save(spec, {'version': 1, 'roots': [{'id': 'source', 'kind': 'evidence', 'path': str(source)}], 'files': rows})
        original_archive = fixture / 'archive'
        packed = self.archive.pack(spec, original_archive, 1)
        self.index_sha = packed['index_sha256']
        self.archive_members = {path.name: {'sha256': file_sha(path), 'bytes': path.stat().st_size}
                                for path in original_archive.iterdir()}
        self.cold = fixture / 'cold'
        transported = self.modules['v3'].pack(str(original_archive), self.index_sha, str(self.cold))
        self.transport_sha = transported['transport_sha256']
        self.raw_names = sorted(name for name in self.archive_members
                                if name == 'SEAL.json' or name.startswith('shard-'))
        need(len(self.raw_names) >= 3, 'Fixture must exercise at least two raw shards')
        # No original-key fallback is possible on the real positive path.
        source.rename(fixture / 'retained-original-source')
        original_archive.rename(fixture / 'retained-original-archive')
        self.fixture_record = {'kind': 'generic-retained-synthetic-fixture', 'version': 1,
            'index_sha256': self.index_sha, 'transport_sha256': self.transport_sha,
            'original_paths_absent_during_replay': list(self.originals.values()),
            'source_bytes': sum(map(len, self.payloads.values())),
            'files': rows, 'archive_members': self.archive_members,
            'archive_result': packed, 'transport_result': transported,
            'scope': 'Synthetic generic bytes only; no actual study inputs or outcomes.'}
        save(fixture / 'FIXTURE.json', self.fixture_record)

    def case(self, name, callback, *, kind='required-control'):
        folder = self.cases / name; folder.mkdir()
        save(folder / 'ENTRY.json', {'name': name, 'kind': kind, 'started_at_unix': time.time(),
                                     'source_pins_sha256': file_sha(HERE / 'SOURCE-PINS.json')})
        try:
            evidence = callback(folder)
            result = {'name': name, 'kind': kind, 'status': 'passed', 'evidence': evidence}
        except BaseException as error:
            result = {'name': name, 'kind': kind, 'status': 'failed',
                      'exception': type(error).__name__, 'message': str(error),
                      'traceback': traceback.format_exc()}
        result['finished_at_unix'] = time.time()
        save(folder / 'RESULT.json', result)
        self.results.append(result)
        print(json.dumps({'case': name, 'status': result['status'],
                          'message': result.get('message')}, ensure_ascii=False), flush=True)

    def clone(self, case, name='cold'):
        folder = case / name; folder.mkdir()
        for path in self.cold.iterdir():
            target = folder / path.name
            shutil.copyfile(path, target); target.chmod(stat.S_IMODE(path.lstat().st_mode))
            need(inode(path) != inode(target), 'Fixture cloning must not share mutable test inodes')
        return folder

    def decode(self, case, version='v3', *, cold=None, pin=None, name='decoded'):
        return self.modules[version].decode(str(cold or self.clone(case)), pin or self.transport_sha,
                                            str(case / name))

    def positive(self, case, version):
        cold = self.clone(case); before = {p.name: snapshot(p) for p in cold.iterdir()}
        result = self.decode(case, version, cold=cold)
        decoded = case / 'decoded'
        need(result['status'] == 'verified', 'Decode did not verify')
        need({p.name for p in decoded.iterdir()} == set(self.archive_members), 'Decoded namespace differs')
        shared = []
        for name, expected in self.archive_members.items():
            path = decoded / name
            need(file_sha(path) == expected['sha256'] and path.stat().st_size == expected['bytes'],
                 'Decoded bytes differ from original archive')
            stored = cold / (name + '.gz' if name in {'INDEX.json', 'SPEC.json'} else name)
            if inode(stored) == inode(path): shared.append(name)
        need(sorted(shared) == self.raw_names if version == 'v3' else not shared,
             'Only v3 raw transport members may share storage')
        for name, old in before.items():
            now = snapshot(cold / name)
            for key in ['device', 'inode', 'bytes', 'mode', 'mtime_ns', 'sha256']:
                need(old[key] == now[key], 'Decode polluted cold input: ' + name + '/' + key)
            if version == 'v2': need(old['ctime_ns'] == now['ctime_ns'] and old['nlink'] == now['nlink'], 'v2 mutated input identity')
        restored = case / 'restored'
        restore_result = self.archive.restore(decoded, restored, self.index_sha, True)
        mapping = restored / 'RESTORED-MAP.json'; map_sha = file_sha(mapping)
        reader = self.resolver.Resolver(mapping, map_sha256=map_sha, index_sha256=self.index_sha)
        for name, raw in self.payloads.items():
            need(not Path(self.originals[name]).exists(), 'Original study-key path is unexpectedly present')
            need(reader.read_bytes(self.originals[name]) == raw, 'Original JSON/payload bytes were altered')
            need(reader.hash(self.originals[name]) == digest(raw), 'Reader hash differs')
            need(stat.S_IMODE(reader.file(self.originals[name]).stat().st_mode) == 0o444, 'Payload is not readonly')
        first, second = [reader.file(self.originals[name]) for name in ['same-a.bin', 'same-b.bin']]
        need(first.read_bytes() == second.read_bytes() and inode(first) != inode(second),
             'Equal logical payloads were physically deduplicated')
        transport_inodes = {inode(path) for path in cold.iterdir()} | {inode(path) for path in decoded.iterdir()}
        payload_inodes = {inode(reader.file(original)) for original in self.originals.values()}
        need(len(payload_inodes) == len(self.payloads) and not transport_inodes & payload_inodes,
             'Logical payload inode isolation differs')
        directory = reader.directory(str(Path(self.originals['original.json']).parent))
        need(directory == restored / 'files/source', 'Original directory structure differs')
        # Even an existing file cannot become an unregistered original fallback.
        unlisted = case / 'unlisted-original.json'; unlisted.write_bytes(b'not in the restore map')
        try: reader.read_bytes(str(unlisted))
        except KeyError: pass
        else: raise AssertionError('Resolver fell back to a live unregistered original')
        session = self.session.MapSessionReader(mapping, map_sha256=map_sha, index_sha256=self.index_sha)
        need(session.verify_all() == len(self.payloads), 'Map session coverage differs')
        need(session.read_bytes(self.originals['original.json']) == self.payloads['original.json'], 'Session changed JSON bytes')
        session.close()
        need(rejected(lambda: session.read_bytes(self.originals['original.json']))['rejected'], 'Closed session remained usable')
        return {'decode': result, 'restore': restore_result, 'map_sha256': map_sha,
                'shared_transport_members': shared, 'payloads': len(payload_inodes),
                'originals_absent': True, 'equal_logical_payloads_distinct_inodes': True,
                'cold_before': before, 'cold_after': {p.name: snapshot(p) for p in cold.iterdir()},
                'raw_json_sha256': digest(self.payloads['original.json']), 'map_session_closed': True}

    def fallback(self, case, mode=None, error=None):
        cold = self.clone(case)
        if mode is not None:
            for name in self.raw_names: (cold / name).chmod(mode)
        before = {p.name: snapshot(p) for p in cold.iterdir()}
        context = mock.patch.object(self.modules['v3'].os, 'link',
            side_effect=OSError(error, 'synthetic link errno admission')) if error is not None else contextlib.nullcontext()
        with context: result = self.decode(case, cold=cold)
        output = case / 'decoded'
        for name, old in before.items():
            now = snapshot(cold / name)
            need(old == now, 'Fallback changed original cold input metadata/bytes')
        need(result['transport_storage']['readonly_linked_members'] == 0, 'Fallback unexpectedly shared storage')
        for name in self.raw_names:
            need(inode(cold / name) != inode(output / name), 'Fallback reused source inode')
            need(stat.S_IMODE((output / name).stat().st_mode) == 0o444, 'Copied output mode differs')
        return {'decode': result, 'input_unchanged': True, 'raw_inodes_independent': True,
                'mode_before_after': {name: before[name]['mode'] for name in self.raw_names},
                'errno_injection': error, 'real_cross_filesystem_test': False if error else None}

    def readonly_0400(self, case):
        cold = self.clone(case)
        for name in self.raw_names: (cold / name).chmod(0o400)
        before = {name: snapshot(cold / name) for name in self.raw_names}
        result = self.decode(case, cold=cold)
        for name in self.raw_names:
            now = snapshot(cold / name)
            need(now['mode'] == '0400' and (case / 'decoded' / name).stat().st_mode & 0o777 == 0o400,
                 'Decoder chmod polluted linked input')
            for key in ['device', 'inode', 'bytes', 'mode', 'mtime_ns', 'sha256']:
                need(now[key] == before[name][key], 'Input changed outside legitimate ctime/nlink')
            need(inode(cold / name) == inode(case / 'decoded' / name), '0400 raw member was not linked')
        return {'decode': result, 'before': before,
                'after': {name: snapshot(cold / name) for name in self.raw_names}}

    def negative(self, case, version, attack):
        cold = self.clone(case); pin = self.transport_sha; output = case / 'decoded'
        early = False
        if attack == 'stored-corruption':
            path = cold / 'INDEX.json.gz'; change(path, path.read_bytes()[:-3])
        elif attack == 'wrong-external-pin': pin = '0' * 64; early = True
        elif attack in {'seal-symlink', 'raw-symlink'}:
            name = 'TRANSPORT.json' if attack == 'seal-symlink' else self.raw_names[0]
            path = cold / name; outside = case / 'same-bytes-reference'
            outside.write_bytes(path.read_bytes()); outside.chmod(0o444)
            path.unlink(); path.symlink_to(outside); early = True
        elif attack == 'nested-output': output = cold / 'inside'; early = True
        elif attack == 'existing-output':
            output.mkdir(); (output / 'sentinel').write_bytes(b'keep original target'); early = False
        elif attack == 'path-traversal':
            pin = rewrite_transport(cold, lambda v: v['files']['INDEX.json'].update(stored='../outside.json')); early = True
        elif attack == 'exact-expansion':
            pin = rewrite_transport(cold, lambda v: v['files']['INDEX.json'].update(bytes=v['files']['INDEX.json']['bytes'] - 1))
        elif attack == 'extra-member': (cold / 'extra').write_bytes(b'unregistered'); early = True
        elif attack == 'missing-member': (cold / self.raw_names[-1]).unlink(); early = True
        elif attack == 'raw-decoded-pin':
            pin = rewrite_transport(cold, lambda v: v['files'][self.raw_names[0]].update(sha256='0' * 64))
        elif attack == 'raw-decoded-length':
            pin = rewrite_transport(cold, lambda v: v['files'][self.raw_names[0]].update(bytes=v['files'][self.raw_names[0]]['bytes'] + 1))
        elif attack == 'gzip-crc-repinned':
            path = cold / 'INDEX.json.gz'; raw = bytearray(path.read_bytes()); raw[-8] ^= 1; change(path, raw)
            pin = rewrite_transport(cold, lambda v: v['files']['INDEX.json'].update(stored_sha256=file_sha(path)))
        elif attack == 'parent-symlink':
            alias = case / 'cold-parent-alias'; alias.symlink_to(cold, target_is_directory=True); cold = alias; early = True
        elif attack == 'output-parent-symlink':
            real = case / 'real-output-parent'; real.mkdir()
            alias = case / 'output-parent-alias'; alias.symlink_to(real, target_is_directory=True)
            output = alias / 'decoded'; early = True
        else: raise AssertionError('Unknown hostile fixture')
        evidence = rejected(lambda: self.modules[version].decode(str(cold), pin, str(output)),
                            before_output=output if early else None)
        if attack == 'existing-output': need((output / 'sentinel').read_bytes() == b'keep original target', 'Target overwritten')
        return {'version': version, 'attack': attack, 'external_transport_sha256': pin,
                'output_exists': output.exists(), **evidence}

    def unlink_alias(self, case):
        cold = self.clone(case); self.decode(case, cold=cold)
        source = cold / self.raw_names[0]; target = case / 'decoded' / source.name
        before = snapshot(source); target.unlink()
        need(file_sha(source) == before['sha256'], 'Unlinking one alias damaged the retained transport')
        second = self.decode(case, cold=cold, name='decoded-again')
        return {'cold_hash_after_unlink': file_sha(source), 'second_decode': second}

    def alias_mutation(self, case):
        cold = self.clone(case); self.decode(case, cold=cold)
        name = next(name for name in self.raw_names if name.startswith('shard-'))
        source = cold / name; alias = case / 'decoded' / name
        before = snapshot(source); raw = bytearray(alias.read_bytes()); raw[-1] ^= 1
        change(alias, raw, 0o444)
        need(file_sha(alias) == file_sha(source) != before['sha256'], 'Shared alias mutation was not exercised')
        inner = rejected(lambda: self.archive.verify(case / 'decoded', self.index_sha))
        outer = rejected(lambda: self.decode(case, cold=cold, name='rejected-second-decode'))
        return {'same_size': len(raw) == before['bytes'], 'cold_before': before,
                'cold_after': snapshot(source), 'inner': inner, 'outer': outer,
                'note': 'Readonly POSIX mode is not same-user immutability; byte checks reject later mutation.'}

    def link_race(self, case, attack):
        cold = self.clone(case); module = self.modules['v3']; real_link = os.link
        called = []; sentinel = b'preexisting target bytes'
        # Only the earliest raw member is intercepted; metadata decoding remains real.
        def racing_link(source, target, **kwargs):
            source, target = Path(source), Path(target)
            called.append({'source': str(source), 'target': str(target)})
            if len(called) != 1: return real_link(source, target, **kwargs)
            if attack in {'source-replacement', 'fallback-source-replacement'}:
                source.rename(case / 'retained-original-raw')
                source.write_bytes(b'replaced input bytes'); source.chmod(0o444)
                if attack.startswith('fallback-'): raise OSError(errno.EXDEV, 'synthetic EXDEV after source replacement')
            elif attack == 'target-preemption':
                target.write_bytes(sentinel); target.chmod(0o444)
            elif attack == 'target-replacement':
                real_link(source, target, **kwargs)
                target.rename(case / 'retained-linked-target')
                target.write_bytes(sentinel); target.chmod(0o444)
                return None
            elif attack == 'parent-symlink-swap':
                cold.rename(case / 'retained-cold-directory')
                cold.symlink_to(case / 'retained-cold-directory', target_is_directory=True)
            else: raise AssertionError('Unknown scheduled race')
            return real_link(source, target, **kwargs)
        with mock.patch.object(module.os, 'link', side_effect=racing_link):
            evidence = rejected(lambda: self.decode(case, cold=cold))
        need(len(called) == 1, 'Race did not reach actual link boundary')
        if attack in {'target-preemption', 'target-replacement'}:
            need(Path(called[0]['target']).read_bytes() == sentinel, 'Competing target was overwritten')
        return {'attack': attack, 'schedule': called, **evidence,
                'partial_files_retained': True, 'hash_or_verifier_mocked': False}

    def late_source_observation(self, case, version):
        # Scope probe: replace a cold member only after every per-member check,
        # immediately before the real final inner verification. The verifier
        # still runs unchanged against the actually decoded output.
        cold = self.clone(case); module = self.modules[version]
        original_factory = module.archive_module; observations = []
        real_archive = original_factory()
        class Delegate:
            def verify(_self, decoded, expected_index):
                name = self.raw_names[-1]; path = cold / name
                before = snapshot(path); path.rename(case / 'retained-late-original')
                path.write_bytes(b'changed after last outer-member check'); path.chmod(0o444)
                observations.append({'name': name, 'before': before, 'after': snapshot(path)})
                return real_archive.verify(decoded, expected_index)
        with mock.patch.object(module, 'archive_module', return_value=Delegate()):
            result = self.decode(case, version, cold=cold)
        need(result['status'] == 'verified', 'Late-source observation did not reach the described boundary')
        later = rejected(lambda: self.decode(case, version, cold=cold, name='later-cold-recheck'))
        need(self.archive.verify(case / 'decoded', self.index_sha)['status'] == 'verified', 'Decoded snapshot is not valid')
        return {'decode': result, 'observation': observations, 'later_cold_recheck': later,
                'decoded_snapshot_still_valid': True,
                'limitation': 'Decode proves consumed decoded bytes, not continued current cold-path identity after its last member read. This preexisting v2 boundary is not OS-enforced immutability.'}

    def run_all(self):
        for version in ['v2', 'v3']:
            self.case(version + '-real-archive-readonly-restore-resolver', lambda c, v=version: self.positive(c, v))
            for attack in ['stored-corruption', 'wrong-external-pin', 'seal-symlink', 'nested-output',
                           'existing-output', 'path-traversal', 'exact-expansion', 'extra-member']:
                self.case(version + '-legacy-' + attack, lambda c, v=version, a=attack: self.negative(c, v, a))
        self.case('v3-writable-copy-fallback', lambda c: self.fallback(c, mode=0o644))
        self.case('v3-exdev-copy-fallback', lambda c: self.fallback(c, error=errno.EXDEV))
        self.case('v3-eperm-copy-fallback', lambda c: self.fallback(c, error=errno.EPERM))
        self.case('v3-readonly-0400-no-input-chmod', self.readonly_0400)
        self.case('v3-unlink-one-shared-alias', self.unlink_alias)
        self.case('v3-mutate-shared-alias-outer-inner-reject', self.alias_mutation)
        for attack in ['raw-symlink', 'parent-symlink', 'output-parent-symlink', 'missing-member',
                       'raw-decoded-pin', 'raw-decoded-length', 'gzip-crc-repinned']:
            self.case('v3-' + attack, lambda c, a=attack: self.negative(c, 'v3', a))
        for attack in ['source-replacement', 'fallback-source-replacement', 'target-preemption',
                       'target-replacement', 'parent-symlink-swap']:
            self.case('v3-scheduled-' + attack, lambda c, a=attack: self.link_race(c, a))
        for version in ['v2', 'v3']:
            self.case(version + '-late-source-lifetime-observation',
                      lambda c, v=version: self.late_source_observation(c, v), kind='documented-scope-probe')
        summary = {'version': 1, 'kind': 'independent-generic-cold-link-review',
            'runtime': {'python': sys.version, 'platform': platform.platform(), 'executable': sys.executable},
            'source_pins_sha256': file_sha(HERE / 'SOURCE-PINS.json'),
            'test_source_sha256': file_sha(Path(__file__)),
            'fixture': {'path': str(self.run / 'FIXTURE/FIXTURE.json'),
                        'sha256': file_sha(self.run / 'FIXTURE/FIXTURE.json')},
            'passed': sum(row['status'] == 'passed' for row in self.results),
            'failed': sum(row['status'] == 'failed' for row in self.results),
            'required_controls': sum(row['kind'] == 'required-control' for row in self.results),
            'scope_probes': sum(row['kind'] == 'documented-scope-probe' for row in self.results),
            'results': self.results,
            'scope': 'Synthetic publication transport only. No actual study pack, data, cleanup, ownership, physical disk reclamation or budget claim.'}
        save(self.run / 'RESULT.json', summary)
        return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True)
    args = parser.parse_args()
    run = Path(args.run_dir)
    need(run.is_absolute() and str(run) == args.run_dir and not run.exists(), 'Fresh canonical run directory required')
    need(run.is_relative_to(HERE), 'Retained review runs must stay within the explicitly owned output root')
    run.mkdir()
    save(run / 'ENTRY.json', {'started_at_unix': time.time(), 'test_source_sha256': file_sha(Path(__file__)),
                            'kind': 'synthetic-only-independent-review-entry'})
    try:
        result = Review(run).run_all()
    except BaseException as error:
        save(run / 'FAILED.json', {'exception': type(error).__name__, 'message': str(error),
                                 'traceback': traceback.format_exc(), 'partial_outputs_retained': True})
        raise
    print(json.dumps({'result': str(run / 'RESULT.json'), 'sha256': file_sha(run / 'RESULT.json'),
                      'passed': result['passed'], 'failed': result['failed']}), flush=True)
    return 1 if result['failed'] else 0


if __name__ == '__main__': raise SystemExit(main())
