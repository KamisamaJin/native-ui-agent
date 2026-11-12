"""Scoped publication map session; unchanged per-payload hash/mode checks.

The complete externally pinned map is read/hash-verified at construction and
explicit session closure. Between accesses its no-follow regular-file identity
(device, inode, size, mode, mtime_ns, ctime_ns) and namespace identity must stay
identical. Replacing, rewriting, chmod or touching it invalidates the session.
This uses ordinary local POSIX ctime semantics, not an adversarial filesystem or
same-user sandbox. Original keys and JSON bytes are never rewritten or opened
as a fallback. This is common publication I/O, not native/SUT optimization.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import stat

HERE = Path(__file__).resolve().parent
PIN = '2a5ec0949b5a64cb3f1dc57df87b3954e1f5e1f21ea58defec3ced44b5ba8204'
_path = HERE/'vendor/resolver.py'
if hashlib.sha256(_path.read_bytes()).hexdigest() != PIN:
    raise ValueError('Frozen publication Resolver bytes differ')
_spec = importlib.util.spec_from_file_location('session_frozen_resolver', _path)
base = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(base)


class MapSessionReader(base.Resolver):
    def __init__(self, *args, **kwargs):
        self.closed = False
        super().__init__(*args, **kwargs)
        self.verify_map()

    def _check(self):
        if self.closed: raise ValueError('Publication map session is closed')
        parent = base.open_directory(self.mapping_file.parent)
        try:
            fd = os.open(self.mapping_file.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        finally: os.close(parent)
        try:
            value = os.fstat(fd)
            if not stat.S_ISREG(value.st_mode) or base.identity(value) != self._map_identity:
                raise ValueError('Pinned map identity changed during publication session')
        finally: os.close(fd)
        fd = base.open_directory(self.namespace)
        try:
            value = os.fstat(fd)
            if (value.st_dev, value.st_ino) != self._namespace_identity:
                raise ValueError('Restore namespace identity changed')
        finally: os.close(fd)

    def verify_map(self):
        self._check()
        _raw, identity, _sha = base.read_regular(self.mapping_file, expected_sha=self.map_sha256,
            expected_bytes=self._map_identity[2], collect=False)
        if identity != self._map_identity: raise ValueError('Pinned map identity changed')
        self._check()

    def verify_all(self):
        self.verify_map()
        for original in self._rows: self.hash(original)
        self.verify_map()
        return len(self._rows)

    def close(self):
        self.verify_map()
        self.closed = True

