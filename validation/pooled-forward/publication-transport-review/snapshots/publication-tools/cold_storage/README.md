# Lossless archive transport

Large synthetic fixture namespaces can have a larger JSON provenance index than
compressed payload. This optional transport layer compresses the frozen archive's
`INDEX.json` and `SPEC.json` byte-for-byte and copies its other members unchanged.
It does not select files, rewrite JSON, judge evidence or delete anything.

Use `cold.py pack --archive ABS --index-sha256 EXTERNAL --output FRESH_ABS` only
after constructing an explicit archive with the frozen parent utility. Record
the returned external `transport_sha256`. To recover it, use `cold.py decode
--cold ABS --transport-sha256 EXTERNAL --output FRESH_ABS`. Decoding checks exact
compressed and expanded bytes, bounded size, names, physical namespaces and the
external seal, then runs the unchanged frozen archive verifier. Its ordinary
`restore` can then create the separate read-only virtual namespace. Decoding
never reads original dataset paths embedded in the index.

Original packed/decoded scratch is retained until the independent byte checks
and required replay finish. Ownership and later cleanup are separate operator
decisions. Partial failures are retained as fresh output directories without a
successful transport seal. Source/cold namespaces must remain immutable under
the operator's exclusive control during use; this utility is not an OS sandbox.

Run `python3 -B -m unittest -v test_cold` in this directory. The eight small
author controls include lossless numeric/binary/empty bytes, absent originals,
frozen restoration, corruption, expansion, traversal, symlink and namespace
rejection. They earn no product, independent-review or native execution credit.
