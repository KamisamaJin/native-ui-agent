"""Owned idle/crash guardian. It never deletes under an active resource lock."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

_CHILDREN = {}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stop(manager):
    row = manager.state.get('pool_watch')
    if not row:
        return
    local = _CHILDREN.get(row['pid'])
    if local is not None: local.poll()
    if row['pid'] == os.getpid() and row['token'] == getattr(manager, '_watch_token', None):
        manager.state.pop('pool_watch'); manager.save(); return
    actual = manager.process_identity(row['pid'])
    if actual:
        if not manager.same_process(row['identity'], actual, row['token'], row['pid']):
            raise ValueError('Pool guardian identity changed; no foreign process reclaimed')
        manager.stop_group(row['pid'])
    else:
        try: os.killpg(row['pid'], 0)
        except ProcessLookupError: pass
        else: raise RuntimeError('Pool guardian group identity is unresolved')
    manager.state.pop('pool_watch'); manager.save()
    if local is not None:
        local.wait(timeout=5); _CHILDREN.pop(row['pid'], None)
    manager.event('pool_guardian_stopped', pid=row['pid'])


def ensure(manager):
    manager.require_lease()
    for pid, child in list(_CHILDREN.items()):
        if child.poll() is not None: _CHILDREN.pop(pid)
    versions = {str(p): digest(p) for p in [Path(__file__), Path(__file__).with_name('resource_manager.py')]}
    row = manager.state.get('pool_watch')
    if row:
        actual = manager.process_identity(row['pid'])
        if actual and not manager.same_process(row['identity'], actual, row['token'], row['pid']):
            raise ValueError('Pool guardian identity changed')
        if not actual or row.get('versions') != versions:
            stop(manager); row = None
    if not getattr(manager, '_watch_config_saved', False):
        config_path = manager.root / ('pool-config-' + uuid.uuid4().hex + '.json')
        with config_path.open('x') as f:
            f.write(json.dumps(manager.config) + '\n'); f.flush(); os.fsync(f.fileno())
        manager.state['pool_config'] = {'path': str(config_path), 'sha256': digest(config_path)}
        manager.save(); manager._watch_config_saved = True
    if row:
        return
    token = uuid.uuid4().hex
    permit = manager.root / ('watch-permit-' + token)
    ready = permit.with_suffix('.ready')
    output = manager.output / ('pool-retirement-' + token)
    argv = [sys.executable, '-B', str(Path(__file__).resolve()), token, str(manager.root),
            str(permit), str(os.getpid()), str(output)]
    with (manager.root / ('pool-watch-' + token + '.log')).open('x') as log:
        process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        _CHILDREN[process.pid] = process
    try:
        deadline = time.monotonic() + 5
        while not ready.is_file() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.02)
        handshake = json.loads(ready.read_text()) if ready.is_file() else {}
        identity = manager.process_identity(process.pid)
        if (handshake != {'token': token, 'pid': process.pid, 'pgid': process.pid}
                or not identity or identity['pgid'] != process.pid or token not in identity['command']):
            raise RuntimeError('Pool guardian startup identity unavailable')
        manager.state['pool_watch'] = {'pid': process.pid, 'token': token, 'identity': identity,
                                       'versions': versions, 'retirement_output': str(output)}
        manager.save(); manager.event('pool_guardian_started', **manager.state['pool_watch'])
        permit.write_text(token)
    except BaseException:
        manager.stop_group(process.pid); process.wait(timeout=5)
        _CHILDREN.pop(process.pid, None)
        raise
    finally:
        if ready.exists(): ready.unlink()


def watch(token, root, permit, manager_pid, output):
    from resource_manager import Resources, no_symlinks, boot_identity, lease_clock
    root = no_symlinks(root); permit = Path(permit)
    permit.with_suffix('.ready').write_text(json.dumps({'token': token, 'pid': os.getpid(), 'pgid': os.getpgrp()}))
    startup = time.monotonic() + 10
    while not permit.is_file():
        if os.getppid() != int(manager_pid) or time.monotonic() >= startup:
            return 125
        time.sleep(.02)
    if permit.read_text() != token: return 125
    permit.unlink()
    began = time.monotonic()
    while time.monotonic() - began <= 90000:
        no_symlinks(root)
        with (root / 'lease.lock').open('a') as stream:
            try: fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                time.sleep(.25); continue
            identity = json.loads((root / 'owner.json').read_text())
            states = []
            for name in ['journal.json', 'journal-backup.json']:
                try:
                    value = json.loads((root / name).read_text())
                    if value.get('token') == identity['token']: states.append(value)
                except (ValueError, OSError): pass
            if not states: return 125
            state = max(states, key=lambda v: v['generation'])
            actual_root = {'device': root.stat().st_dev, 'inode': root.stat().st_ino}
            if state.get('root_identity') != actual_root: return 125
            row = state.get('pool_watch', {})
            if row.get('pid') != os.getpid() or row.get('token') != token: return 0
            ref = state['pool_config']; config_path = Path(ref['path'])
            if config_path.parent != root or config_path.is_symlink() or digest(config_path) != ref['sha256']: return 125
            config = json.loads(config_path.read_text())
            devices = state.get('devices', [])
            pool = config.get('resources', {}).get('pool', {})
            idle = pool.get('idle_seconds', 300) if isinstance(pool, dict) else 0
            ttl = config.get('resources', {}).get('ttl_seconds', 86400)
            max_age = min(ttl, pool.get('max_age_seconds', 3600)) if isinstance(pool, dict) else 0
            now = time.time()
            expired = any(not (0 <= now - d.get('last_used_unix', 0) < idle)
                          or not (0 <= now - d['created_at_unix'] < max_age)
                          or d.get('boot_id') != boot_identity()
                          or not (0 <= lease_clock() - d.get('last_used_monotonic', -1e30) < idle)
                          or not (0 <= lease_clock() - d.get('created_monotonic', -1e30) < max_age) for d in devices)
            retire = bool(state.get('lease') or state.get('process') or not devices or expired)
        if retire:
            try:
                with Resources(config, output, final=True, _watch_token=token): pass
                return 0
            except RuntimeError as error:
                if 'lease is active' not in str(error): raise
        time.sleep(.25)
    raise RuntimeError('Pool guardian lifetime exceeded; owned root retained for explicit reconciliation')


if __name__ == '__main__':
    raise SystemExit(watch(*sys.argv[1:]))
