Frozen candidate-v13.0 is blocked by three demonstrated controller/host issues: ignored ordinary `--fresh`, incomplete binding of original inner artifacts, and unsafe cross-process pooled timestamps on this host’s Python3.9.6. See [open issues](OPEN-ISSUES.md) and [structured review](review.json).

47 primary probes produced 36 raw P and 11 raw F. The raw failures retain their original assertions; triage separates confirmed issues, a disputed completion interpretation, and unavailable/harness evidence. Five additional initial-path reproduction probes confirm the same B01 failure.

HOST checks passed for actual exclusive locks, owner separation, private process timeout/interruption recovery, borrowed-path preservation, and copied-root rejection. SIMULATED checks passed for platform-only/shared/deleted input invalidation, unrelated-output preservation, required source review gates and source-only layer separation, missing/tampered completion-proof rejection, and retaining mandatory U for missing/torn coverage. These establish only the demonstrated decisions under supplied inputs.

No real SDK command, native project, device, business task or performance episode ran. All native facts and the >=20% same-code/same-coverage gate remain U / not evaluated. The 41-root private cleanup audit has no cleanup errors or simulated inventory leftovers; later coverage/reproduction roots also closed through final/cleanup receipts. Candidate file hashes remain unchanged.

Original commands/stdout/stderr, source hashes, controlled inputs, packet archives, raw failures and cleanup receipts are indexed in [raw-artifact-index.json](raw-artifact-index.json), bound by [SEAL.json](SEAL.json). The original sandbox denial and both harness setup errors are retained as environment/harness evidence.

To rerun an executable suite, use `checks/reproduce.py --suite initial --output <fresh review-1/work child>`; it creates a positive ownership marker, copies checks and preserves all prior evidence. `work/reproductions/initial-proof` validates that handoff.
