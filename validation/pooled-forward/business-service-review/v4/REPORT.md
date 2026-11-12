# Independent v4 first-D0 recovery review

**Verdict: PASS for the bounded shared-controller crash-recovery delta (HOST/SIM only).** The original v3 lost-anchor counterexample is closed for both arms. This qualifies the reviewed controller delta; it does not approve actual business inputs, native results, quality, performance, or any other study gate.

Frozen helper SHA-256: `1a52cc62be5cee0bad34fefe8b54a7479761ca5ea5e8981937a8a1ad11ae6b05`. Freeze file: `9a24b9eca414f1bb91e92695b7e74d1b7cd384d7596456c08c78758559fba114`.

All thirteen frozen recovery-cut tests and six independent targeted checks pass: **19 checks, no failures or errors**. The original forty inherited tests and the author's fifty-three-test QA are retained frozen artifacts; this bounded independent run executes the focused recovery suite and independent cases, without re-auditing the SUT.

The exact original v3 boundary was replayed independently for A and B: complete terminal failed-D0 outcomes and immutable result exist; execution stops immediately before `repair_started`; the controller restarts at original readiness +1301 seconds. V4 recovers only the original first request ID and aggregate hash, original monotonic/wall finish times, and their fixed +1200 deadline. Before a D1 enqueue or source unlock can proceed, it freezes the unchanged initial source. D1 is rejected, no unlock event appears, and no other arm starts a clock. The preserved v3 failure remains untouched; `observations.json` records the new v4 passing replay and its exact artifacts.

Further independent checks establish:

- A cut immediately after complete aggregate persistence but before `request_finished` recovers the finish event and original anchor. Acknowledgment at +275 leaves exactly 925 source seconds. Both APIs can then perform an actual synthetic source-only repair, D1 and final collection without resetting the anchor. Baseline retains original previous/SHA/history transport; treatment uses its default transport. A final source lock remains irrevocable.
- Cuts before write-ahead preparation, after preparation with no aggregate, and during truncated aggregate persistence stay pending/locked. Recovery does not create a clock, overwrite retained bytes, continue, or silently retry. The aggregate must match its original prepared SHA and every originally pinned profile outcome.
- An outcome explicitly missing when the aggregate was prepared cannot be added later to upgrade the first D0. Even a successful D1 cannot create a source window from that incomplete first proof.
- Corrupting an existing anchor's original-result hash rejects both foreground acknowledgment and a restarted watchdog. A stable watchdog cache, after validating the original proof, freezes at the same original deadline on its next cached iteration; it does not derive time from guard startup or cache refresh.

The frozen thirteen additionally cover before/after result, completion and anchor publication, guard startup failure, finite original timestamp/hash binding, the exact late-D1 extension, correct remaining time, tampered aggregate/outcome proofs, and a legitimate D1 queued within the original window but served after expiry. Honest terminal failed D0 remains a repair opportunity, with failure logs and F/U retained; no native success, image, accepted status or delivery is invented.

AST verification confirms source-domain admission, configured profile admission, both API command builders/forwarding, current request-integrity checks and `feedback_ready` remain unchanged from v3. `source_domain.py`, manifest schema/example and the old three test sources are byte-identical. The changed functions are limited to first-D0 proof/recovery, deadline enforcement, aggregate preparation, watchdog validation and status recovery; exact names/digests are in `FUNCTION-DELTA.json`. No responsibility filtering, frozen service, oracle, ownership, resource or study-policy rewrite occurred.

All four candidate freezes and all three earlier sealed independent reviews remain byte-identical, including the v3 failure/counterexample. `READSET.json` records exact checks. The v4 drivers, all independent synthetic fixtures, test outputs and report are retained under this directory and bound by `SEAL.json`.

All evidence is HOST/SIM. Helper `execute()` and subprocess forwarding were blocked; no SDK, simulator, native/render execution, actual business source/design/oracle, real timing outcome or Git access occurred. The optional business profile adapter metadata was not needed and was not read. Service packets are synthetic transport fixtures. Actual business D0 continues to require all its other independently approved preconditions and all-ten initial-source admission.
