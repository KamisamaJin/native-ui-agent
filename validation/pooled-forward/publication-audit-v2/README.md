# Recorded paired-controller chain replay

This is publication verifier v2, a separate correction of the frozen v1. Its
first actual application exposed a verifier schema error: v1 treated the frozen
controller's fixed acquisition `scope` string as a file reference. V2 accepts
that exact metadata string and exactly four named evidence slots, validates each
original byte pin and canonical capture-relative filename, and rejects unknown
members, altered scope text, missing logs and a substituted capture receipt.
The frozen controller, native tools, study records, criteria and deadlines are
unchanged. V1's failed replay and diagnosis remain in its HOST directory. These
are publication infrastructure failures, not product defects or treatment
benefits. V2 has 39 author synthetic controls, including the original 31 described
below. Its actual ten-arm live replay is separate from synthetic checks and
independent product grading.

`audit.py` is a shared publication verifier for the exact `business-tools-v4`
controller and domain transport SHA values declared in its source. It does not
modify or import `Study`, initialize a run, start a guard, execute commands, change
permissions, grant time, rewrite an expected value, grade a UI or adopt a packet.

Load the helper and the separate pinned read-only resolver by explicit module
paths. After archive byte verification and virtual restore:

```python
result = verify_run(resolver, ORIGINAL_RUN_ROOT)
assert result['status'] == 'verified', result
```

`require_hidden_authorization=False` can verify the completed public cohort before
one-shot hidden authorization exists. The default requires the recorded complete
authorization. Hidden config bodies are read only after all ten source/claim
seals, the cohort pin, authorization and context-validation ordering have passed.
The original hidden paths must be outside the controller directory. The verifier
first verifies the complete restored controller subtree, uses exact original
keys for explicit external references, caches immutable bytes, and rechecks its
verified directories and external references after replay.

Checks include:

- The manifest/prerequisite/tool/public-input pins and original paired nonempty
  source capsules; all source files use original byte counts and SHA256 values.
- Event filenames, sequences and previous-file SHA links; FIFO, no hidden retry,
  terminal outcome/result pins and the two-diagnostic limit. Pre-enqueue residues
  remain listed; unregistered terminal/native artifacts cannot be dropped.
- The immutable first D0 write-ahead/outcome proof and its exact `+1200` anchors;
  unlocks cannot create a replacement repair window. Failed SDK/guard/collector
  outcomes with intact integrity are valid terminal D0s. Original exception
  traceback sidecars remain required when the outcome records an exception.
- Source locks, final capsules, immutable original output inventories, final
  profile selection, self-claim/seal pointers, accepted-flag consistency, owned
  retirement proof and the recorded own-delivery endpoint interval.
- Appended source-domain request, independently registered review/provenance,
  actual component bytes, unchanged policy, exactly one revision and config
  lineage. This checks recorded shape-review authority, not behavioral truth.
- All ten seals before the cohort, one-shot hidden authorization and distinct
  public/hidden/other-arm context namespaces at the original final source.

Honest F/U, terminal failures, `not_accepted` and disclosed late source records
remain valid study records. They are returned in the summary; they are never
excluded to manufacture acceptance. Structural corruption returns `status: failed`
with the original error. This verifier does not turn missing evidence into pass.

This is recorded-procedure integrity, not a sandbox or cryptographic proof of a
human/AI identity or that no one bypassed the controller. A populated restore
cannot independently prove historical empty context directories. Native/source/
image judgment replay, independent design and initial-author admission, anonymous
grader/cause/reveal barriers, operator arm ordering and final quality metrics
remain separate required checks. It does not reevaluate present host clocks,
SDKs or current-source eligibility.

`test_audit.py` uses deterministic in-memory synthetic files with valid outer pins,
so its negative controls reach semantic invariants rather than only a bad map
hash. Fixtures and their digests reconstruct from the frozen test source; compact
HOST results/logs retain every author attempt. The final 31-control result belongs
to the frozen source. Earlier 23/28/29-control results are unsealed development
attempts with retained original summaries/digests, not extra independent tests or
contemporaneous source freezes. They are not native executions,
business tasks, independent reviews or product quality credit. Filesystem mapping
and no-fallback controls are in the separate resolver tests; actual archive/map
application and pure frozen judgment replay must still be performed independently.
