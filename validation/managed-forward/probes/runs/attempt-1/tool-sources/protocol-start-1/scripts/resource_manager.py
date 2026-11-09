#!/usr/bin/env python3
"""Owned, bounded native scratch space. Evidence and user devices are never owned.

An OS lock protects a live lease; the append-only journal survives interruption.
Only a directory created with this owner's marker or a journaled simctl create
intent can be reclaimed. A PID alone is never sufficient evidence of ownership.
"""
from __future__ import annotations
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid


FORMAT = 'native-ui-owned-resources-v1'


def allocated(path):
    """Allocated filesystem bytes; APFS sharing means these are not net disk use."""
    path = Path(path)
    if not path.exists(): return 0
    total = 0; seen = set()
    for base, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(base) / d).is_symlink()]
        for name in files:
            try:
                st = (Path(base) / name).lstat(); key = (st.st_dev, st.st_ino)
                if key not in seen: total += st.st_blocks * 512; seen.add(key)
            except FileNotFoundError: pass
    return total


def no_symlinks(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError('Resource path may not traverse a symlink')
    return path


class Resources:
    def __init__(self, config, output, *, final=False):
        self.config = config; self.output = Path(output).resolve(); self.final = final
        self.options = dict(config.get('resources', {}))
        allowed = {'root', 'max_bytes', 'min_free_bytes', 'max_simulators', 'sample_seconds', 'ttl_seconds', 'ios'}
        if set(self.options) - allowed: raise ValueError('Unknown resource policy field')
        self.root = no_symlinks(self.options.get('root', self.output.parent / 'cache/native-ui-resources'))
        self.protected = [Path(p).resolve() for p in config['source_roots']] + [self.output]
        if any(p == self.root or p.is_relative_to(self.root) or self.root.is_relative_to(p) for p in self.protected):
            raise ValueError('Owned scratch must be disjoint from source and evidence')
        self.owner_key = hashlib.sha256(json.dumps([str(p.resolve()) for p in map(Path, config['source_roots'])]).encode()).hexdigest()
        self.max_bytes = self.options.get('max_bytes', 20 * 2**30)
        self.min_free = self.options.get('min_free_bytes', 5 * 2**30)
        self.max_simulators = self.options.get('max_simulators', 1)
        self.sample_seconds = self.options.get('sample_seconds', 2)
        self.ttl = self.options.get('ttl_seconds', 86400)
        if any(type(v) is not int or v <= 0 for v in [self.max_bytes, self.max_simulators, self.ttl]):
            raise ValueError('Positive integral resource limits required')
        if type(self.min_free) is not int or self.min_free < 0 or type(self.sample_seconds) not in {int, float} or not .1 <= self.sample_seconds <= 60:
            raise ValueError('Invalid free space or sampling policy')
        self.state = {}; self.peak = 0; self.samples = []; self.cleanup_errors = []
        self.borrowed_paths = []
        native = config.get('native_options', {})
        if native.get('build-cache'): self.borrowed_paths.append(Path(native['build-cache']).resolve())
        if native.get('project'):
            project = Path(native['project']).resolve()
            self.borrowed_paths.extend(project / p for p in ['build', 'app/build', '.gradle'])
        self.stream = None; self.process = None; self._stop = threading.Event(); self._thread = None
        self.command_exit_code = None

    def save(self):
        temp = self.root / ('journal-' + uuid.uuid4().hex + '.tmp')
        temp.write_text(json.dumps(self.state, indent=2) + '\n'); os.replace(temp, self.root / 'journal.json')

    def event(self, kind, **values):
        with (self.root / 'events.jsonl').open('a') as f:
            f.write(json.dumps({'at_unix': time.time(), 'kind': kind, **values}) + '\n')

    @staticmethod
    def process_identity(pid):
        p = subprocess.run(['ps', '-p', str(pid), '-o', 'lstart=', '-o', 'pgid=', '-o', 'command='], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p.stdout.strip() if p.returncode == 0 else None

    def reconcile_process(self):
        row = self.state.get('process')
        if not row: return
        actual = self.process_identity(row['pid'])
        if actual:
            if actual != row['identity'] or row['token'] not in actual:
                raise ValueError('Prior process identity changed; no process or resource reclaimed')
            os.killpg(row['pid'], signal.SIGTERM)
            for _ in range(50):
                if self.process_identity(row['pid']) is None: break
                time.sleep(.1)
            if self.process_identity(row['pid']) is not None:
                os.killpg(row['pid'], signal.SIGKILL)
        self.event('interrupted_process_reconciled', pid=row['pid'])
        self.state.pop('process', None); self.save()

    def __enter__(self):
        created = False
        try: self.root.mkdir(parents=True, exist_ok=False); created = True
        except FileExistsError: pass
        marker = self.root / 'owner.json'
        if created:
            marker.write_text(json.dumps({'format': FORMAT, 'owner_key': self.owner_key, 'token': uuid.uuid4().hex}) + '\n')
        if not marker.is_file(): raise ValueError('Existing resource root has no ownership marker')
        identity = json.loads(marker.read_text())
        if identity.get('format') != FORMAT or identity.get('owner_key') != self.owner_key:
            raise ValueError('Resource ownership differs from this project')
        self.identity = identity
        self.stream = (self.root / 'lease.lock').open('a')
        try: fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.stream.close(); self.stream = None
            raise RuntimeError('Resource lease is active; concurrent acquisition refused')
        try:
            journal = self.root / 'journal.json'
            self.state = json.loads(journal.read_text()) if journal.is_file() else {'format': FORMAT, 'token': identity['token'], 'directories': [], 'devices': []}
            if self.state.get('token') != identity['token']: raise ValueError('Resource journal ownership changed')
            actual_root = {'device': self.root.stat().st_dev, 'inode': self.root.stat().st_ino}
            if self.state.get('root_identity', actual_root) != actual_root: raise ValueError('Owned root was replaced')
            self.state['root_identity'] = actual_root
            self.reconcile_process()
            # Lock acquisition proves no other managed session can be active.
            # Journaled devices from an interrupted process are recovered first.
            self.cleanup_devices()
            for row in list(self.state['directories']):
                if time.time() - row['last_used_unix'] > self.ttl: self.remove_directory(row)
            self.state['lease'] = {'pid': os.getpid(), 'started_at_unix': time.time()}; self.save()
            self.event('lease_acquired', pid=os.getpid()); self.sample()
            for row in sorted(list(self.state['directories']), key=lambda r: r['last_used_unix']):
                if self.samples[-1]['allocated_bytes'] <= self.max_bytes and self.samples[-1]['free_bytes'] >= self.min_free: break
                self.remove_directory(row); self.sample()
            self.check_budget()
            return self
        except BaseException:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN); self.stream.close(); self.stream = None
            raise

    def directory(self, name):
        if not name or Path(name).name != name or name in {'.', '..'}: raise ValueError('One scratch directory name required')
        p = no_symlinks(self.root / name)
        row = next((r for r in self.state['directories'] if r['name'] == name), None)
        if row is None:
            p.mkdir(exist_ok=False)
            (p / '.native-ui-owner.json').write_text(json.dumps(self.identity) + '\n')
            row = {'name': name, 'created_at_unix': time.time(), 'last_used_unix': time.time(),
                   'device': p.stat().st_dev, 'inode': p.stat().st_ino}; self.state['directories'].append(row)
        elif json.loads((p / '.native-ui-owner.json').read_text()) != self.identity:
            raise ValueError('Scratch ownership marker changed')
        if row.get('inode', p.stat().st_ino) != p.stat().st_ino or row.get('device', p.stat().st_dev) != p.stat().st_dev:
            raise ValueError('Owned directory was replaced')
        row['last_used_unix'] = time.time(); self.save(); return p

    def remove_directory(self, row):
        p = no_symlinks(self.root / row['name'])
        if p.exists():
            if p.parent != self.root or json.loads((p / '.native-ui-owner.json').read_text()) != self.identity:
                raise ValueError('Refusing to delete unowned scratch')
            if row.get('inode', p.stat().st_ino) != p.stat().st_ino or row.get('device', p.stat().st_dev) != p.stat().st_dev:
                raise ValueError('Refusing to delete a replaced directory')
            shutil.rmtree(p)
        self.state['directories'].remove(row); self.save(); self.event('directory_removed', name=row['name'])

    def simctl(self, *args):
        env = dict(os.environ, DEVELOPER_DIR=self.config.get('native_options', {}).get('developer-dir', '/Applications/Xcode.app/Contents/Developer'))
        return subprocess.check_output(['xcrun', 'simctl', *args], env=env, text=True).strip()

    def cleanup_devices(self):
        if not self.state.get('devices'): return
        devices = json.loads(self.simctl('list', 'devices', '--json'))['devices']
        all_devices = [d for rows in devices.values() for d in rows]
        for row in list(self.state['devices']):
            # A create intent is durable before simctl runs; exact unique name
            # recovers the narrow crash window before its returned UUID is saved.
            found = [d for d in all_devices if d['name'] == row['name']]
            if len(found) > 1: raise ValueError('Duplicate owned simulator name; manual diagnosis required')
            if found:
                d = found[0]
                if row.get('udid') and row['udid'] != d['udid']: raise ValueError('Simulator identity changed')
                if d['state'] != 'Shutdown': self.simctl('shutdown', d['udid'])
                self.simctl('delete', d['udid']); self.event('simulator_removed', udid=d['udid'])
            self.state['devices'].remove(row); self.save()

    def native_options(self):
        options = dict(self.config['native_options'])
        if self.config.get('platform') == 'ios' or 'package' in options:
            # Supplied user devices and user build caches are borrowed. Only an
            # explicit managed simulator causes a create and an eventual delete.
            if options.get('simulator') in {None, 'managed'}:
                ios = self.options.get('ios')
                if not ios or set(ios) != {'device_type', 'runtime'}: raise ValueError('Managed simulator requires explicit installed device type/runtime')
                if len(self.state['devices']) >= self.max_simulators: raise RuntimeError('Owned simulator limit reached')
                row = {'name': 'NativeUI-' + self.identity['token'][:12] + '-' + uuid.uuid4().hex[:8], 'created_at_unix': time.time()}
                self.state['devices'].append(row); self.save(); self.event('simulator_create_intent', name=row['name'])
                row['udid'] = self.simctl('create', row['name'], ios['device_type'], ios['runtime']); self.save()
                options['simulator'] = row['udid']
            if not options.get('build-cache'): options['build-cache'] = str(self.directory('compiled-ios'))
        return options

    def sample(self):
        paths = [self.root] + self.borrowed_paths + [Path.home() / 'Library/Developer/CoreSimulator/Devices' / d['udid'] for d in self.state.get('devices', []) if d.get('udid')]
        paths = [p for p in set(paths) if not any(p != q and p.is_relative_to(q) for q in paths)]
        measured = sum(allocated(p) for p in paths); self.peak = max(self.peak, measured)
        self.samples.append({'at_unix': time.time(), 'allocated_bytes': measured, 'free_bytes': shutil.disk_usage(self.root).free})
        return measured

    def check_budget(self):
        if self.samples[-1]['allocated_bytes'] > self.max_bytes: raise RuntimeError('Owned native scratch exceeds byte budget')
        if self.samples[-1]['free_bytes'] < self.min_free: raise RuntimeError('Native execution blocked by minimum free space')

    def run(self, argv, *, env, stdout):
        old_handlers = {}
        def interrupted(signum, _frame): raise InterruptedError('Managed native execution interrupted by signal ' + str(signum))
        if threading.current_thread() is threading.main_thread():
            for signum in [signal.SIGINT, signal.SIGTERM]: old_handlers[signum] = signal.signal(signum, interrupted)
        try:
            token = uuid.uuid4().hex; permit = self.root / ('permit-' + token)
            # The child cannot start an SDK until its durable ownership receipt
            # exists. SIGKILL in the spawn/journal window leaves only a bounded,
            # nonexecuting launcher, not an unregistered compiler process tree.
            launcher = [sys.executable, '-B', str(Path(__file__).resolve()), '_child', token, str(permit), json.dumps(argv)]
            self.process = subprocess.Popen(launcher, env=env, stdout=stdout, stderr=subprocess.STDOUT, start_new_session=True)
            identity = self.process_identity(self.process.pid)
            if not identity or token not in identity: raise RuntimeError('Owned process start identity unavailable')
            self.state['process'] = {'pid': self.process.pid, 'pgid': self.process.pid, 'token': token, 'identity': identity, 'argv': argv}
            self.save(); self.event('process_started', **self.state['process'])
            permit.write_text(token)
            while self.process.poll() is None:
                self.sample(); self.check_budget()
                try: self.process.wait(timeout=self.sample_seconds)
                except subprocess.TimeoutExpired: pass
            self.sample(); self.check_budget(); self.command_exit_code = self.process.returncode
            return self.process.returncode
        finally:
            if self.process and self.process.poll() is None:
                os.killpg(self.process.pid, signal.SIGTERM)
                try: self.process.wait(timeout=5)
                except subprocess.TimeoutExpired: os.killpg(self.process.pid, signal.SIGKILL); self.process.wait()
            if 'permit' in locals() and permit.exists(): permit.unlink()
            self.state.pop('process', None); self.save()
            for signum, handler in old_handlers.items(): signal.signal(signum, handler)

    def __exit__(self, exc_type, exc, tb):
        try:
            self.sample()
            try: self.cleanup_devices()
            except Exception as error: self.cleanup_errors.append(str(error))
            if self.final or exc_type or self.command_exit_code not in {None, 0} or self.peak > self.max_bytes:
                for row in list(self.state['directories']):
                    try: self.remove_directory(row)
                    except Exception as error: self.cleanup_errors.append(str(error))
            self.state.pop('lease', None); self.save()
            self.event('lease_released', cleanup_errors=self.cleanup_errors)
            self.output.mkdir(parents=True, exist_ok=True)
            (self.output / 'resources.json').write_text(json.dumps({'version': 1, 'root': str(self.root), 'owner': self.identity,
                'policy': {'max_bytes': self.max_bytes, 'min_free_bytes': self.min_free, 'max_simulators': self.max_simulators},
                'sample_seconds': self.sample_seconds, 'observed_peak_allocated_bytes': self.peak,
                'samples': self.samples, 'cleanup_errors': self.cleanup_errors, 'remaining_directories': self.state['directories'],
                'remaining_devices': self.state['devices'], 'final': self.final,
                'primary_error': {'type': exc_type.__name__, 'message': str(exc)} if exc_type else None,
                'command_exit_code': self.command_exit_code,
                'borrowed_build_paths': list(map(str, self.borrowed_paths)),
                'scope': 'Sampled owned scratch plus borrowed project build paths and owned simulator data. Borrowed paths are measured and budgeted, never deleted. Not exact transient peak, APFS physical usage, shared SDK caches, or user devices.'}, indent=2) + '\n')
        finally:
            if self.stream:
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN); self.stream.close()
        if self.cleanup_errors and exc_type is None: raise RuntimeError('Managed cleanup incomplete: ' + '; '.join(self.cleanup_errors))
        return False


def main():
    p = argparse.ArgumentParser(); p.add_argument('--config', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('command', choices=['inspect', 'cleanup']); a = p.parse_args()
    with Resources(json.loads(a.config.read_text()), a.output, final=a.command == 'cleanup') as manager:
        print(json.dumps({'root': str(manager.root), 'state': manager.state, 'allocated_bytes': manager.sample()}))

def child():
    token, permit, raw = sys.argv[2:]; permit = Path(permit); deadline = time.monotonic() + 10
    while not permit.is_file():
        if os.getppid() == 1 or time.monotonic() >= deadline: raise SystemExit(125)
        time.sleep(.02)
    if permit.read_text() != token: raise SystemExit(125)
    permit.unlink()
    # Keep the token-bearing launcher alive: recovery verifies PID + start time
    # + process group + opaque acquisition token, never a bare reused PID.
    process = subprocess.Popen(json.loads(raw))
    raise SystemExit(process.wait())

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '_child': child()
    else: main()
