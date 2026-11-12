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
import re
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid


FORMAT = 'native-ui-owned-resources-v1'


def boot_identity():
    p = Path('/proc/sys/kernel/random/boot_id')
    if p.is_file(): return p.read_text().strip()
    value = subprocess.check_output(['sysctl', '-n', 'kern.boottime'], text=True)
    match = re.search(r'sec\s*=\s*(\d+)\s*,\s*usec\s*=\s*(\d+)', value)
    if not match: raise ValueError('Native pool requires a stable host boot identity')
    return ':'.join(match.groups())


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
    def __init__(self, config, output, *, final=False, _watch_token=None):
        self.config = config; self.output = Path(output).resolve(); self.final = final
        self._watch_token = _watch_token
        if self.output.exists(): raise ValueError('Fresh resource receipt output required')
        self.options = dict(config.get('resources', {}))
        allowed = {'root', 'max_bytes', 'min_free_bytes', 'max_simulators', 'sample_seconds', 'ttl_seconds', 'command_timeout_seconds', 'ios', 'pool'}
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
        self.command_timeout = self.options.get('command_timeout_seconds', 900)
        pool = self.options.get('pool', {})
        if pool is not False and (not isinstance(pool, dict) or set(pool) - {'idle_seconds', 'max_uses', 'max_age_seconds'}):
            raise ValueError('Bounded device pool policy required')
        self.pool_enabled = pool is not False
        self.pool_idle = pool.get('idle_seconds', 300) if pool is not False else 1
        self.pool_uses = pool.get('max_uses', 12) if pool is not False else 1
        self.pool_age = pool.get('max_age_seconds', 3600) if pool is not False else 1
        if (type(self.pool_idle) is not int or not 1 <= self.pool_idle <= 1800
                or type(self.pool_uses) is not int or not 1 <= self.pool_uses <= 100
                or type(self.pool_age) is not int or not 1 <= self.pool_age <= 7200):
            raise ValueError('Pool idle lifetime and acquisition count must be bounded')
        if any(type(v) is not int or v <= 0 for v in [self.max_bytes, self.max_simulators, self.ttl]):
            raise ValueError('Positive integral resource limits required')
        if type(self.min_free) is not int or self.min_free < 0 or type(self.sample_seconds) not in {int, float} or not .1 <= self.sample_seconds <= 60:
            raise ValueError('Invalid free space or sampling policy')
        if type(self.command_timeout) not in {int,float} or not 0 < self.command_timeout <= 86400:
            raise ValueError('Bounded native command timeout required')
        self.state = {}; self.peak = 0; self.samples = []; self.cleanup_errors = []
        self.borrowed_paths = []
        native = config.get('native_options', {})
        if native.get('build-cache'): self.borrowed_paths.append(Path(native['build-cache']).resolve())
        if native.get('project'):
            project = Path(native['project']).resolve()
            self.borrowed_paths.extend(project / p for p in ['build', 'app/build', '.gradle'])
        self.stream = None; self.process = None; self._stop = threading.Event(); self._thread = None
        self.command_exit_code = None
        self.finished = False

    def save(self):
        self.state['generation'] = self.state.get('generation', 0) + 1
        raw = json.dumps(self.state, indent=2) + '\n'
        # Two independent durable checkpoints. Recovery takes the newest valid
        # generation, including a crash between replacing the two copies.
        for name in ['journal-backup.json', 'journal.json']:
            temp = self.root / ('journal-' + uuid.uuid4().hex + '.tmp')
            with temp.open('x') as f: f.write(raw); f.flush(); os.fsync(f.fileno())
            os.replace(temp, self.root / name)

    def event(self, kind, **values):
        with (self.root / 'events.jsonl').open('a') as f:
            f.write(json.dumps({'at_unix': time.time(), 'kind': kind, **values}) + '\n')

    @staticmethod
    def process_identity(pid):
        p = subprocess.run(['ps', '-ww', '-p', str(pid), '-o', 'lstart=', '-o', 'pgid=', '-o', 'command='], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode: return None
        return Resources.parse_identity(p.stdout.strip(),pid)

    @staticmethod
    def parse_identity(value,pid):
        if isinstance(value,dict):return value
        if not isinstance(value,str):return None
        parts=value.split(None,6)
        if len(parts)!=7:return None
        try:pgid=int(parts[5])
        except ValueError:return None
        return {'pid':pid,'started': ' '.join(parts[:5]),'pgid':pgid,'command':parts[6]}

    @staticmethod
    def same_process(expected,actual,token,pid):
        expected=Resources.parse_identity(expected,pid) if expected is not None else None
        # The interpreter may legitimately canonicalize argv[0] during startup.
        # Stable birth/group identity and the opaque acquisition token, not the
        # presentation spelling of the executable, determine this exact lease.
        return bool(expected and actual and expected.get('pid')==actual.get('pid')==pid and
                    expected.get('started')==actual.get('started') and expected.get('pgid')==actual.get('pgid')==pid and
                    token in expected.get('command','') and token in actual.get('command',''))

    @staticmethod
    def stop_group(pgid):
        try: os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError: return
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            output = subprocess.check_output(['ps', '-ax', '-o', 'pid=', '-o', 'pgid=', '-o', 'state='], text=True)
            alive = [v for row in output.splitlines() if len(v := row.split()) >= 3 and v[1] == str(pgid) and not v[2].startswith('Z')]
            if not alive: return
            time.sleep(.1)
        try: os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError: pass

    def reconcile_process(self):
        row = self.state.get('process')
        if not row: return
        if (type(row.get('pid'))is not int or row['pid']<=1 or row.get('pgid')!=row['pid'] or
                not isinstance(row.get('token'),str)or len(row['token'])!=32):
            raise ValueError('Invalid owned process acquisition identity; no process/resource reclaimed')
        actual = self.process_identity(row['pid'])
        if actual:
            if not self.same_process(row['identity'],actual,row['token'],row['pid']):
                raise ValueError('Prior process identity changed; no process or resource reclaimed')
            self.stop_group(row['pid'])
        else:
            try: os.killpg(row['pid'], 0)
            except ProcessLookupError: pass
            else: raise RuntimeError('Prior launcher exited but process group remains; identity unresolved, scratch retained')
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
            candidates = []; invalid = []
            for name in ['journal.json', 'journal-backup.json']:
                journal = self.root / name
                if not journal.is_file(): continue
                try:
                    candidate = json.loads(journal.read_text())
                    if candidate.get('token') != identity['token']: raise ValueError('Journal token differs')
                    candidates.append(candidate)
                except (ValueError, TypeError) as error:
                    invalid.append({'path': name, 'sha256': hashlib.sha256(journal.read_bytes()).hexdigest(), 'error': str(error)})
            if invalid and not candidates: raise ValueError('No valid owned resource journal; originals retained')
            self.state = max(candidates, key=lambda r: r.get('generation', 0)) if candidates else {'format': FORMAT, 'token': identity['token'], 'directories': [], 'devices': []}
            if invalid: self.event('journal_recovered', invalid=invalid, selected_generation=self.state.get('generation', 0))
            if self.state.get('token') != identity['token']: raise ValueError('Resource journal ownership changed')
            actual_root = {'device': self.root.stat().st_dev, 'inode': self.root.stat().st_ino}
            if self.state.get('root_identity', actual_root) != actual_root: raise ValueError('Owned root was replaced')
            self.state['root_identity'] = actual_root
            interrupted = bool(self.state.get('lease') or self.state.get('process'))
            self.reconcile_process()
            # Lock acquisition proves no other managed session can be active.
            # Journaled devices from an interrupted process are recovered first.
            if interrupted or not self.pool_enabled or any(not self.reusable_device(r) for r in self.state.get('devices', [])):
                self.cleanup_devices()
            for row in list(self.state['directories']):
                if time.time() - row['last_used_unix'] > self.ttl: self.remove_directory(row)
            self.state['lease'] = {'pid': os.getpid(), 'started_at_unix': time.time()}; self.save()
            self.event('lease_acquired', pid=os.getpid()); self.sample()
            for row in sorted(list(self.state['directories']), key=lambda r: r['last_used_unix']):
                if self.samples[-1]['allocated_bytes'] <= self.max_bytes and self.samples[-1]['free_bytes'] >= self.min_free: break
                self.remove_directory(row); self.sample()
            if self.samples[-1]['allocated_bytes'] > self.max_bytes or self.samples[-1]['free_bytes'] < self.min_free:
                self.cleanup_devices(); self.sample()
            # Existing evidence can still be routed/reviewed on a low-disk
            # machine. Resource admission is enforced before acquiring native
            # handles or starting a command, not by forcing a redundant SDK run.
            return self
        except BaseException:
            fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN); self.stream.close(); self.stream = None
            raise

    def directory(self, name):
        self.require_lease()
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

    def require_lease(self):
        if self.stream is None or self.stream.closed or self.finished: raise RuntimeError('Active owned resource lease required')

    def release(self, name):
        self.require_lease()
        if self.state.get('process'): raise RuntimeError('Cannot release scratch used by an active managed process')
        row = next((r for r in self.state['directories'] if r['name'] == name), None)
        if row: self.remove_directory(row)
        return {'name': name, 'status': 'released' if row else 'not_acquired_or_already_released'}

    def finish(self):
        if not self.finished: self.__exit__(None, None, None)
        return {'status': 'finished', 'receipt': str(self.output/'resources.json')}

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
        argv = ['xcrun', 'simctl', *args]; started = time.time()
        result = subprocess.run(argv, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        self.event('simctl_command', argv=argv, started_at_unix=started, finished_at_unix=time.time(), exit_code=result.returncode,
                   stdout_sha256=hashlib.sha256(result.stdout.encode()).hexdigest(), stderr=result.stderr)
        if result.returncode: raise RuntimeError('Owned simulator command failed: '+result.stderr)
        return result.stdout.strip()

    def cleanup_devices(self):
        if not self.state.get('devices'): return
        devices = json.loads(self.simctl('list', 'devices', '--json'))['devices']
        all_devices = [d for rows in devices.values() for d in rows]
        for row in list(self.state['devices']):
            if (not isinstance(row.get('name'),str)or not row['name'].startswith('NativeUI-'+self.identity['token'][:12]+'-')or
                    type(row.get('created_at_unix'))not in {int,float}):
                raise ValueError('Simulator journal has no owned create identity')
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

    def reusable_device(self, row):
        at = row.get('last_used_unix', 0)
        return bool(self.pool_enabled and row.get('pool_idle') is True and row.get('pool_key')
                    and row.get('boot_id') == boot_identity()
                    and type(at) in {int, float} and 0 <= time.time() - at < self.pool_idle
                    and 0 <= time.monotonic() - row.get('last_used_monotonic', -1e30) < self.pool_idle
                    and type(row.get('uses')) is int and row['uses'] < self.pool_uses
                    and 0 <= time.time() - row['created_at_unix'] < min(self.ttl, self.pool_age)
                    and 0 <= time.monotonic() - row.get('created_monotonic', -1e30) < self.pool_age)

    def pool_key(self, ios):
        import capture_validity
        return hashlib.sha256(json.dumps({'ios': ios, 'host': capture_validity.host_identity(self.config, 'ios')}, sort_keys=True).encode()).hexdigest()

    def native_options(self,platform=None):
        self.require_lease()
        self.sample();self.check_budget()
        if platform not in {None,'ios','android'}:raise ValueError('Known native platform required')
        options = dict(self.config['native_options'])
        if self.state.get('process'): raise RuntimeError('Cannot acquire native handles during an active managed command')
        if platform=='ios' or (platform is None and (self.config.get('platform') == 'ios' or 'package' in options or 'simulator' in options)):
            # Supplied user devices and user build caches are borrowed. Only an
            # explicit managed simulator causes a create and an eventual delete.
            if options.get('simulator') in {None, 'managed'}:
                ios = self.options.get('ios')
                if not ios or set(ios) != {'device_type', 'runtime'}: raise ValueError('Managed simulator requires explicit installed device type/runtime')
                if getattr(self, '_checked_out', None):
                    if self._checked_out['spec'] != ios: raise RuntimeError('Cannot replace an active native device lease')
                    row = self._checked_out['row']
                else:
                    import pool_watch
                    pool_watch.ensure(self)
                    key = self.pool_key(ios) if self.pool_enabled and (not self.final or self.state['devices']) else None
                    row = next((r for r in self.state['devices'] if self.reusable_device(r) and r['pool_key'] == key), None)
                if getattr(self, '_checked_out', None):
                    pass
                elif row:
                    devices = json.loads(self.simctl('list', 'devices', '--json'))['devices']
                    found = [v for v in devices.get(ios['runtime'], []) if v['udid'] == row['udid'] and v['name'] == row['name'] and v.get('isAvailable', True)]
                    if len(found) != 1:
                        raise ValueError('Owned pooled device identity/runtime changed')
                    row.update(pool_idle=False, uses=row['uses'] + 1, last_used_unix=time.time(), last_used_monotonic=time.monotonic())
                    self.save(); self.event('simulator_pool_checkout', udid=row['udid'], uses=row['uses'])
                else:
                    # There is one exclusive native command per root. Retire
                    # mismatched idle slots before creating a replacement.
                    self.cleanup_devices()
                    if len(self.state['devices']) >= self.max_simulators: raise RuntimeError('Owned simulator limit reached')
                    row = {'name': 'NativeUI-' + self.identity['token'][:12] + '-' + uuid.uuid4().hex[:8],
                           'created_at_unix': time.time(), 'last_used_unix': time.time(), 'uses': 1,
                           'created_monotonic': time.monotonic(), 'last_used_monotonic': time.monotonic(),
                           'boot_id': boot_identity(), 'pool_idle': False, 'pool_key': key}
                    self.state['devices'].append(row); self.save(); self.event('simulator_create_intent', name=row['name'])
                    row['udid'] = self.simctl('create', row['name'], ios['device_type'], ios['runtime']); self.save()
                self._checked_out = {'spec': dict(ios), 'row': row}
                options['simulator'] = row['udid']
                options['reset-owned-app'] = '1'
            if not options.get('build-cache'): options['build-cache'] = str(self.directory('compiled-ios'))
            if options.get('simulator') != 'managed' and not any(v.get('udid') == options['simulator'] for v in self.state['devices']):
                devices = json.loads(self.simctl('list', 'devices', '--json'))['devices']
                found = [d for rows in devices.values() for d in rows if d['udid'] == options['simulator']]
                if len(found) != 1: raise ValueError('Borrowed simulator identity unavailable')
                self.event('borrowed_simulator', udid=found[0]['udid'], state=found[0]['state'], disposition='Borrowed device is never deleted or shut down; execution may boot it. No exclusive state-restoration authority declared.')
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

    def run(self, argv, *, env, stdout, timeout=None):
        self.require_lease()
        self.sample();self.check_budget()
        timeout = self.command_timeout if timeout is None else timeout
        if type(timeout) not in {int,float} or not 0 < timeout <= 86400: raise ValueError('Positive bounded command timeout required')
        deadline = time.monotonic() + timeout
        old_handlers = {}
        def interrupted(signum, _frame): raise InterruptedError('Managed native execution interrupted by signal ' + str(signum))
        if threading.current_thread() is threading.main_thread():
            for signum in [signal.SIGINT, signal.SIGTERM]: old_handlers[signum] = signal.signal(signum, interrupted)
        try:
            token = uuid.uuid4().hex; permit = self.root / ('permit-' + token);ready=permit.with_suffix('.ready')
            # The child cannot start an SDK until its durable ownership receipt
            # exists. SIGKILL in the spawn/journal window leaves only a bounded,
            # nonexecuting launcher, not an unregistered compiler process tree.
            launcher = [sys.executable, '-B', str(Path(__file__).resolve()), '_child', token, str(permit),str(os.getpid()),json.dumps(argv)]
            self.process = subprocess.Popen(launcher, env=env, stdout=stdout, stderr=subprocess.STDOUT, start_new_session=True)
            startup_deadline=min(deadline,time.monotonic()+5)
            while not ready.is_file() and self.process.poll() is None and time.monotonic()<startup_deadline:time.sleep(.02)
            if time.monotonic()>=deadline:raise subprocess.TimeoutExpired(argv,timeout)
            handshake=json.loads(ready.read_text())if ready.is_file()else{}
            identity = self.process_identity(self.process.pid)
            if (handshake!={'token':token,'pid':self.process.pid,'pgid':self.process.pid}or not identity or
                    identity.get('pgid')!=self.process.pid or token not in identity.get('command','')):
                raise RuntimeError('Owned process start identity unavailable')
            self.state['process'] = {'pid': self.process.pid, 'pgid': self.process.pid, 'token': token, 'identity': identity, 'argv': argv}
            self.save(); self.event('process_started', **self.state['process'])
            permit.write_text(token)
            while self.process.poll() is None:
                self.sample(); self.check_budget()
                if time.monotonic() >= deadline: raise subprocess.TimeoutExpired(argv, timeout)
                try: self.process.wait(timeout=min(self.sample_seconds, max(.001,deadline-time.monotonic())))
                except subprocess.TimeoutExpired: pass
            self.sample(); self.check_budget(); self.command_exit_code = self.process.returncode
            return self.process.returncode
        finally:
            if self.process:
                # The launcher can already have exited while a child still
                # holds the SDK/files. Its just-acquired group is still owned.
                try: self.stop_group(self.process.pid)
                except Exception as error: self.cleanup_errors.append('Process group cleanup: '+str(error))
                if self.process.poll() is None:
                    try: self.process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        self.process.kill(); self.process.wait()
            if 'permit' in locals() and permit.exists(): permit.unlink()
            if 'ready' in locals() and ready.exists(): ready.unlink()
            if not self.cleanup_errors: self.state.pop('process', None)
            self.save()
            for signum, handler in old_handlers.items(): signal.signal(signum, handler)

    def __exit__(self, exc_type, exc, tb):
        if self.finished: return False
        try:
            self.sample()
            retain = (self.pool_enabled and not self.final and not exc_type and self.command_exit_code in {None, 0}
                      and self.peak <= self.max_bytes and self.samples[-1]['free_bytes'] >= self.min_free)
            if not self.cleanup_errors:
                try:
                    if not retain or not self.state.get('devices'):
                        import pool_watch
                        pool_watch.stop(self)
                    if retain:
                        if self.state.get('devices'):
                            import pool_watch
                            pool_watch.ensure(self)
                        for row in self.state.get('devices', []):
                            if not row.get('pool_idle'):
                                row.update(pool_idle=True, last_used_unix=time.time(), last_used_monotonic=time.monotonic())
                                self.event('simulator_pool_return', udid=row.get('udid'), uses=row.get('uses'))
                        self.save()
                    else: self.cleanup_devices()
                except Exception as error: self.cleanup_errors.append(str(error))
            if not self.cleanup_errors and (self.final or exc_type or self.command_exit_code not in {None, 0} or self.peak > self.max_bytes):
                for row in list(self.state['directories']):
                    try: self.remove_directory(row)
                    except Exception as error: self.cleanup_errors.append(str(error))
            self.state.pop('lease', None); self.save()
            self.event('lease_released', cleanup_errors=self.cleanup_errors)
            self.output.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.root/'events.jsonl', self.output/'resource-events.jsonl')
            shutil.copyfile(self.root/'journal.json', self.output/'resource-journal.json')
            (self.output / 'resources.json').write_text(json.dumps({'version': 1, 'root': str(self.root), 'owner': self.identity,
                'policy': {'max_bytes': self.max_bytes, 'min_free_bytes': self.min_free, 'max_simulators': self.max_simulators},
                'sample_seconds': self.sample_seconds, 'observed_peak_allocated_bytes': self.peak,
                'samples': self.samples, 'cleanup_errors': self.cleanup_errors, 'remaining_directories': self.state['directories'],
                'remaining_devices': self.state['devices'], 'final': self.final,
                'primary_error': {'type': exc_type.__name__, 'message': str(exc)} if exc_type else None,
                'command_exit_code': self.command_exit_code,
                'pool': {'enabled': self.pool_enabled, 'idle_seconds': self.pool_idle, 'max_uses': self.pool_uses, 'max_age_seconds': self.pool_age,
                         'disposition': 'idle_owned_pool' if retain and self.state['devices'] else 'retired'},
                'borrowed_build_paths': list(map(str, self.borrowed_paths)),
                'scope': 'Sampled owned scratch plus borrowed project build paths and owned simulator data. Borrowed paths are measured and budgeted, never deleted. Not exact transient peak, APFS physical usage, shared SDK caches, or user devices.'}, indent=2) + '\n')
        finally:
            if self.stream:
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN); self.stream.close()
            self.finished = True
        if self.cleanup_errors and exc_type is None: raise RuntimeError('Managed cleanup incomplete: ' + '; '.join(self.cleanup_errors))
        return False


def main():
    p = argparse.ArgumentParser(); p.add_argument('--config', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('command', choices=['inspect', 'cleanup']); a = p.parse_args()
    with Resources(json.loads(a.config.read_text()), a.output, final=a.command == 'cleanup') as manager:
        print(json.dumps({'root': str(manager.root), 'state': manager.state, 'allocated_bytes': manager.sample()}))

def child():
    token, permit, manager_pid,raw = sys.argv[2:]; permit = Path(permit); deadline = time.monotonic() + 10
    permit.with_suffix('.ready').write_text(json.dumps({'token':token,'pid':os.getpid(),'pgid':os.getpgrp()}))
    while not permit.is_file():
        if os.getppid() != int(manager_pid) or time.monotonic() >= deadline: raise SystemExit(125)
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
