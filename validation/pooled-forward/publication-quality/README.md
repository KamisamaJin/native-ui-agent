# Anonymous input integrity

`integrity.verify_packet(reader, original_packet_root, original_ledger_path,
packet_seal_sha256=..., ledger_sha256=...)` rechecks one sealed anonymous input.
It reads neither the X/Y mapping nor judge outputs and starts no SDK process.

The checks cover exact packet membership, original source/placement/contract/image
copies, all native fields except the prospectively omitted cost/alarm fields,
all automatic measured actual rows, full visual questions, stable source-root
indices and capture source before/after. Missing facts remain missing. Identity
checks reject the original arm/tool names and machine-local paths.

Supply externally recorded exact byte pins. `verify.py` requires either explicit
`--live-read-only` original access or `--restore-map` with its external map/index
pins. A virtual restore never falls back to original files. The original JSON
bytes and embedded paths are preserved; the pinned Resolver translates reads.

This checks integrity of supplied inputs, not completeness of normative API
documents, implementation correctness, independent review, visual truth,
delivery, or resource ownership. Source-contract supplements and their original
provenance require separate completeness review. Use the frozen run audit to
validate the capture/outcome/controller provenance chain before interpreting a
packet. Returned filesystem paths are verified at read time; rerun after replay
and keep the restored namespace read-only.

Run synthetic HOST checks with:

```sh
python3 -B -m unittest discover -s validation/pooled-forward/publication-quality -p 'test_*.py' -v
```

The tests include hostile resealing of changed/dropped measured facts, omitted
images and visual questions, symlinks, wrong external pins, source changes,
concealed available facts, and a restore whose original paths no longer exist.
Synthetic image bytes are not native PNGs. HOST test timings and live integrity
passes are separate from independent product grades and native collection costs.
