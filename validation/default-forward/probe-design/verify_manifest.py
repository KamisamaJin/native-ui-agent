#!/usr/bin/env python3
"""Check the frozen fixture bytes using only the Python standard library."""
from pathlib import Path
import hashlib

root = Path(__file__).resolve().parent
entries = (root / "SHA256SUMS").read_text().splitlines()
listed = set()
for entry in entries:
    digest, relative = entry.split("  ", 1)
    path = root / relative
    assert path.is_file() and root in path.resolve().parents, relative
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, relative
    listed.add(relative)
actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS"}
assert actual == listed, {"unlisted": sorted(actual - listed), "missing": sorted(listed - actual)}
print(f"PASS: {len(listed)} frozen files")
