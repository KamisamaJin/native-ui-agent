# Pinned read-only restore resolver

This shared publication helper does not change a frozen tool or its verdicts.
It consumes `publication-tools/archive.py`'s `RESTORED-MAP.json` after independent
archive verification and virtual restore. The operator supplies externally pinned
SHA256 values for both the map bytes and its archive index.

```python
from resolver import Resolver

r = Resolver('/ABS/virtual/RESTORED-MAP.json',
             map_sha256=EXTERNAL_MAP_SHA, index_sha256=EXTERNAL_INDEX_SHA)
raw = r.read_bytes('/ORIGINAL/packet/result.json')
value = r.read_json('/ORIGINAL/packet/result.json')
path = r.file('/ORIGINAL/packet/result.json')
native_dir = r.directory('/ORIGINAL/packet/native')
```

The helper reads only the pinned map and mapped regular files under its sibling
`files/` namespace. Each access checks map/namespace identity, original pins,
content SHA/byte count and recorded restored mode. No original file is opened as
a fallback. JSON is parsed without changing embedded original paths or bytes.
Duplicate keys, aliases, traversal, symlinks, missing files, changed data and
unmapped subtree entries fail closed. `directory()` returns a directory only when
every mapped descendant preserves the same relative layout and that complete
physical subtree contains exactly those mapped files and parent directories.

There are no writes, environment patches, monkeypatches, SDK calls, subprocesses,
cleanup or current-source validity claims. A pinned map is not a substitute for
verifying the archive against its external index pin. The resolver does not check
archive shards, create a restore or authenticate who chose the pins.

Returned `Path` objects are verified at return, not OS-enforced immutable handles.
Keep the restore read-only during frozen pure evaluation, and verify the accessed
subtree again afterwards. The resolver is not an adversarial same-user filesystem
sandbox or an assertion that the historical packet can be adopted by a current
live PR. Pure replay must retain original source, contract, image, environment,
failure and U bindings at their recorded scope/time.
