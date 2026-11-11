# Explicit lossless publication archives

`archive.py` is a POSIX Python 3.9+ standard-library utility for an operator's
explicit file inventory. It performs no dataset discovery, file selection,
ownership inference, source/cache deletion, cleanup, original-path remapping or
code/SDK execution. The operator separately establishes ownership/authorization,
pins the inventory and later pins the returned index SHA. Root declarations are
selection boundaries, not independent ownership proof.

## Exact interface

```sh
python3 -B archive.py pack --spec /ABS/inventory.json --output /ABS/FRESH-archive
python3 -B archive.py verify --archive /ABS/FRESH-archive --index-sha256 INDEX_SHA256
python3 -B archive.py restore --archive /ABS/FRESH-archive \
  --index-sha256 INDEX_SHA256 --dest /ABS/FRESH-virtual-restore
```

`pack` defaults to a 64 MiB logical tar limit per shard. `--shard-mib 1..64`
can lower it. Every compressed shard is strictly below 95 MiB. `restore
--read-only` clears restored write bits while retaining original/requested modes
in the mapping. Nothing is executed, including restored executable files.

Both output directories must be fresh. Archive verification is read-only.
Restore verifies the complete archive before creating its destination, then
verifies it again while streaming data into the fresh virtual namespace.
It never needs to open the original roots/files and can operate after originals
have been moved away. An external index SHA is optional in the syntax but should
be supplied for independently pinned provenance.

## Inventory schema

See `spec.schema.json` and `spec.example.json`. The example contains placeholders,
not selected study data. Version 1 has exactly `version`, `roots` and `files`:

```json
{
  "version": 1,
  "roots": [
    {"id": "evidence", "kind": "evidence", "path": "/ABS/owned/evidence"}
  ],
  "files": [
    {
      "root": "evidence",
      "path": "/ABS/owned/evidence/task/original.json",
      "logical_path": "evidence/task/original.json",
      "sha256": "EXACT_FILE_SHA256",
      "bytes": 123,
      "mode": "0644"
    }
  ]
}
```

`kind` is `positive_owned` or `evidence`. File paths must be normalized absolute
POSIX paths below the named declared prefix. Logical paths are normalized relative
POSIX paths and retain the original filename. Ordinary permission bits are exact
four-character octal strings; special permission bits are excluded. Duplicate
files, logical case/Unicode collisions, file/directory collisions, traversal,
backslash logical paths, symlinks at any traversed path component, non-regular
files and any `.git` component are rejected. No implicit globs or recursion exist.

Pack validates every selected file's declared SHA/byte count/mode before copying,
checks file identities/content while streaming, and validates all files and root
identities again after copying. It also retains and rechecks the inventory's exact
original JSON bytes. A changed source aborts packing; it is never silently retried
or edited. Validation observes stable inode/metadata/content before/after, not an
OS write lock against a deliberately changing same-user owner.

## Archive layout and limits

The fresh directory contains exactly:

* `SPEC.json`: exact original inventory bytes.
* `INDEX.json`: file provenance, original absolute/logical paths, hashes, bytes,
  modes, source/root identity observations, exact offset chunks, shard hashes and
  complete counts.
* `SEAL.json`: exact index/spec file SHA values.
* `shard-00000.tar.gz`, etc.: lossless gzip-compressed USTAR members.

Tar members have generated identities `chunks/FILE_ID/CHUNK_ID`. Original filenames
and provenance remain in the index; member names never become restore paths.
Files larger than one shard are split into ordered chunks with exact offsets,
per-chunk SHA and a full-file SHA. Empty files retain an explicit empty member.
The 64 MiB logical budget includes tar headers, padding and trailer, so a single
payload chunk is slightly smaller than 64 MiB. Gzip expansion is bounded during
verification, and each compressed shard is checked against the strict 95 MiB cap.

Verify streams every shard/member and every reconstructed file hash/count. It
rejects changed index/spec seals, extra/missing files, extra/missing/duplicate/
traversal/non-regular tar members, reordered/overlapping/gapped chunks, corrupt
headers or padding, truncated gzip/tar, CRC failures, concatenated compressed
members/trailing bytes, and mismatched full-file hashes/counts. No tar extraction
API is used. The seal detects changes relative to its recorded hashes; protection
against coherent replacement of the entire directory requires the operator's
external `--index-sha256` pin. It is not a cryptographic signature or independent
authorization proof.

## Virtual restoration

All payloads go to `DEST/files/<logical_path>` through no-symlink, exclusive file
creation. A destination under the archive or a target equal to any original
absolute file path is rejected. Original JSON/packet contents are never parsed
or rewritten. `DEST/RESTORED-MAP.json` provides:

```json
{
  "mappings": {
    "/ORIGINAL/absolute/file.json": {
      "physical_path": "/FRESH/DEST/files/logical/file.json",
      "logical_path": "logical/file.json",
      "sha256": "EXACT_FILE_SHA256",
      "bytes": 123,
      "original_mode": "0644",
      "restored_mode": "0644"
    }
  }
}
```

The mapping is a separate lookup artifact. It does not install filesystem aliases,
rewrite embedded paths, run old packets, or claim replay/adoption/quality success.

## Failures and HOST validation

Failed pack output remains in its fresh directory with `FAILED.json`; failed
virtual restore remains with `RESTORE-FAILED.json`. There is no automatic retry,
overwrite or deletion. Invalid preflight specs may reject before creating output.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B test_archive.py
```

All test attempts remain under `HOST/attempt-*` with `ATTEMPT.json`, including
expected corruption/source-change failures and their raw artifacts. Each run
writes a new timestamped `HOST/RESULT-*.json`. Tests cover exact JSON/name/mode
round trips, a 65 MiB oversized file across default shards, incompressible multi-
shard data, source changes, symlinks, path escape, `.git`, index/shard/member
tampering, extra/duplicate/missing members, chunk offset errors and truncation.
Subprocess/SDK execution is forbidden. No actual cohort inventory is selected,
packed, inspected or deleted by this implementation task.
