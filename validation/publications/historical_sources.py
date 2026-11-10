"""Resolve changed live-file aliases to exact, archived publication bytes.

Call only after the preferred live alias fails its original digest. Frozen
baselines and explicit immutable aliases still fail their own hash checks.
"""
import hashlib
from pathlib import Path, PurePosixPath


def archived_source(repository, relative, expected):
    logical = PurePosixPath(relative)
    if not logical.parts or logical.is_absolute() or '..' in logical.parts or str(logical) != relative:
        raise ValueError('Canonical repository-relative publication path required')
    if not isinstance(expected, str) or len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
        raise ValueError('Original SHA256 required for archived source lookup')
    repository = Path(repository).resolve()
    for root in sorted((repository/'validation').glob('*/historical-root')):
        source = root.joinpath(*logical.parts)
        if source.is_symlink() or not source.is_file():
            continue
        if not source.resolve().is_relative_to(root.resolve()):
            continue
        if hashlib.sha256(source.read_bytes()).hexdigest() == expected:
            return source
    raise AssertionError('No archived source matches original digest: '+relative)
