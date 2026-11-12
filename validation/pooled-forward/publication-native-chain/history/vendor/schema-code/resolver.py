"""Explicit read-only access to an externally pinned lossless virtual restore.

No original-path fallback, path rewriting, SDK execution or current-source claim.
Returned Paths are verified at return, not OS-enforced immutable handles; callers
must keep the restore read-only and verify again after a frozen pure replay.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import unicodedata


FORMAT = 'explicit-file-lossless-v1'
BLOCK = 1024 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def hexsha(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('An external exact SHA256 pin is required')
    return value


def absolute(value):
    if not isinstance(value, str) or not value.startswith('/') or '\x00' in value:
        raise ValueError('A canonical absolute POSIX path is required')
    p = PurePosixPath(value)
    if str(p) != value or any(v in {'.', '..'} or v.casefold() == '.git' for v in value.split('/')):
        raise ValueError('Noncanonical or forbidden absolute path')
    return Path(value)


def logical(value):
    if not isinstance(value, str) or not value or '\\' in value or '\x00' in value:
        raise ValueError('A canonical relative logical path is required')
    p = PurePosixPath(value)
    if p.is_absolute() or str(p) != value or any(v in {'.', '..'} or v.casefold() == '.git' for v in value.split('/')):
        raise ValueError('Unsafe logical path')
    return p


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    def constant(_value):
        raise ValueError('Nonfinite JSON is forbidden')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def identity(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mode, s.st_mtime_ns, s.st_ctime_ns)


def open_directory(path):
    """Walk from / using no-follow directory descriptors, never resolve aliases."""
    path = absolute(str(path))
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        return fd
    except BaseException:
        os.close(fd)
        raise


def read_regular(path, *, expected_sha=None, expected_bytes=None, expected_mode=None, collect=True):
    path = absolute(str(path))
    parent = open_directory(path.parent)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally:
        os.close(parent)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('Only regular restored files are readable')
        if expected_bytes is not None and before.st_size != expected_bytes:
            raise ValueError('Restored file byte count differs')
        if expected_mode is not None and stat.S_IMODE(before.st_mode) != expected_mode:
            raise ValueError('Restored file mode differs')
        h = hashlib.sha256(); size = 0; chunks = []
        while True:
            block = os.read(fd, BLOCK)
            if not block:
                break
            h.update(block); size += len(block)
            if collect:
                chunks.append(block)
        after = os.fstat(fd)
        if identity(before) != identity(after) or size != after.st_size:
            raise ValueError('Restored file changed while reading')
        if expected_sha is not None and h.hexdigest() != expected_sha:
            raise ValueError('Restored file SHA256 differs')
        if expected_bytes is not None and size != expected_bytes:
            raise ValueError('Restored file byte count differs')
        return (b''.join(chunks) if collect else None), identity(after), h.hexdigest()
    finally:
        os.close(fd)


class Resolver:
    def __init__(self, mapping_file, *, map_sha256, index_sha256):
        self.mapping_file = absolute(str(mapping_file))
        self.map_sha256 = hexsha(map_sha256)
        self.index_sha256 = hexsha(index_sha256)
        raw, self._map_identity, _ = read_regular(self.mapping_file, expected_sha=self.map_sha256)
        value = strict_json(raw)
        fields = {'format', 'version', 'index_sha256', 'namespace', 'mappings', 'scope'}
        if not isinstance(value, dict) or set(value) != fields or value['format'] != FORMAT or type(value['version']) is not int or value['version'] != 1:
            raise ValueError('An exact lossless-v1 restore map is required')
        if value['index_sha256'] != self.index_sha256:
            raise ValueError('Restore map index pin differs')
        self.namespace = absolute(value['namespace'])
        if self.namespace != self.mapping_file.parent / 'files':
            raise ValueError('Restore namespace must be the map sibling files directory')
        if not isinstance(value['scope'], str) or not isinstance(value['mappings'], dict) or not value['mappings']:
            raise ValueError('Explicit nonempty restored mappings are required')
        fd = open_directory(self.namespace)
        try:
            s = os.fstat(fd); self._namespace_identity = (s.st_dev, s.st_ino)
        finally:
            os.close(fd)
        self._rows = {}; physicals = set(); folded = set()
        row_fields = {'physical_path', 'logical_path', 'sha256', 'bytes', 'original_mode', 'restored_mode'}
        for original, row in value['mappings'].items():
            original_path = absolute(original)
            if not isinstance(row, dict) or set(row) != row_fields:
                raise ValueError('Unexpected restored mapping fields')
            relative = logical(row['logical_path']); physical = absolute(row['physical_path'])
            if physical != self.namespace.joinpath(*relative.parts) or relative.name != original_path.name:
                raise ValueError('Restored logical/physical path or original filename differs')
            folded_path = unicodedata.normalize('NFC', str(relative)).casefold()
            if physical in physicals or folded_path in folded:
                raise ValueError('Conflicting restored file aliases')
            physicals.add(physical); folded.add(folded_path)
            hexsha(row['sha256'])
            if type(row['bytes']) is not int or row['bytes'] < 0:
                raise ValueError('Exact nonnegative byte count required')
            for key in ['original_mode', 'restored_mode']:
                if not isinstance(row[key], str) or not re.fullmatch('0[0-7]{3}', row[key]):
                    raise ValueError('Ordinary POSIX file modes required')
            self._rows[original] = dict(row)
        if set(map(Path, self._rows)) & physicals:
            raise ValueError('A restore must never target an original file')
        if any(any(parent in physicals for parent in p.parents) for p in physicals):
            raise ValueError('Restored file/directory collision')
        self._check()

    def _check(self):
        _raw, current, _sha = read_regular(self.mapping_file, expected_sha=self.map_sha256,
                                          expected_bytes=self._map_identity[2], collect=False)
        if current != self._map_identity:
            raise ValueError('Restore map identity changed')
        fd = open_directory(self.namespace)
        try:
            s = os.fstat(fd)
            if (s.st_dev, s.st_ino) != self._namespace_identity:
                raise ValueError('Restore namespace identity changed')
        finally:
            os.close(fd)

    def _row(self, original):
        original = str(absolute(str(original)))
        if original not in self._rows:
            raise KeyError('Original path is absent from the pinned restore map: ' + original)
        return self._rows[original]

    def _read(self, row, *, collect):
        return read_regular(row['physical_path'], expected_sha=row['sha256'], expected_bytes=row['bytes'],
                            expected_mode=int(row['restored_mode'], 8), collect=collect)

    def file(self, original):
        self._check(); row = self._row(original)
        self._read(row, collect=False); self._check()
        return Path(row['physical_path'])

    def read_bytes(self, original):
        self._check(); row = self._row(original)
        raw, _identity, _sha = self._read(row, collect=True); self._check()
        return raw

    def read_json(self, original):
        return strict_json(self.read_bytes(original))

    def hash(self, original):
        self._check(); row = self._row(original)
        _raw, _identity, actual = self._read(row, collect=False); self._check()
        return actual

    def directory(self, original):
        self._check(); original = absolute(str(original))
        if str(original) in self._rows:
            raise ValueError('Mapped original is a file, not a directory')
        descendants = [(Path(key).relative_to(original), row) for key, row in self._rows.items()
                       if Path(key).is_relative_to(original)]
        if not descendants:
            raise KeyError('Original directory has no mapped descendants: ' + str(original))
        candidates = {Path(row['physical_path']).parents[len(relative.parts) - 1] for relative, row in descendants}
        if len(candidates) != 1:
            raise ValueError('Mapped descendants do not preserve one relative directory layout')
        physical = candidates.pop()
        if not physical.is_relative_to(self.namespace):
            raise ValueError('Mapped directory escapes the virtual namespace')
        expected_files = {str(relative) for relative, _row in descendants}
        expected_dirs = {'.'}
        for relative, row in descendants:
            if physical / relative != Path(row['physical_path']):
                raise ValueError('Mapped descendant relative path differs')
            expected_dirs.update(str(parent) for parent in relative.parents)
            self._read(row, collect=False)
        seen_files = set(); seen_dirs = {'.'}
        def walk(fd, prefix):
            for name in os.listdir(fd):
                relative = prefix / name; s = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if stat.S_ISDIR(s.st_mode):
                    if str(relative) not in expected_dirs:
                        raise ValueError('Unmapped directory in restored subtree')
                    seen_dirs.add(str(relative))
                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    try:
                        walk(child, relative)
                    finally:
                        os.close(child)
                elif stat.S_ISREG(s.st_mode):
                    if str(relative) not in expected_files:
                        raise ValueError('Unmapped file in restored subtree')
                    seen_files.add(str(relative))
                else:
                    raise ValueError('Symlink or unsupported entry in restored subtree')
        fd = open_directory(physical)
        try:
            walk(fd, Path('.'))
        finally:
            os.close(fd)
        if seen_files != expected_files or seen_dirs != expected_dirs:
            raise ValueError('Restored subtree is incomplete')
        self._check()
        return physical
