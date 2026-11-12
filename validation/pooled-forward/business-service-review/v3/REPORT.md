# Independent v3 terminal-D0 delta review

**Verdict: CHANGES REQUIRED.** A process stop after the durable first-D0 result/event but before the source-window anchor lets D1 create a later deadline. The independent synthetic reproduction extended the deadline by **1301 seconds** and unlocked source after its original D0 deadline. V3 must remain excluded from study execution pending a new frozen candidate.

Reviewed helper: `d25c9be1bb0e1db2af2370a21553e8ba3a1bb32a8d318d115ea13bed5e027014`. Freeze file: `6c2142e16901cdc2fcb8a24c752829be4a6dddbc50fb6ed4ff8b25ab61ea68ea`.

## Blocking durability finding

`serve()` durably saves every profile outcome, the aggregate result, and `request_finished`, then appends `repair_started` separately. The counterexample injects an `OSError` only at that final anchor append, representing a process stop at the exact write boundary. All first-D0 profile outcomes/result/finished event and initial source/input/tool integrity remain valid. The first D0 is complete; source is read-only and no ticket remains pending, but the anchor is absent.

The reproduction restarts the controller at original D0 readiness +1301 seconds, beyond the required original +1200 deadline. D1 can enqueue and finish. The anchor condition checks that the first D0 is complete, but uses the **current D1** request ID, result-readiness clock and wall time to create `repair_started`. `feedback_ready` then unlocks the unchanged initial tree against that later clock. `LOST-ANCHOR-COUNTEREXAMPLE.json` retains the original first result path/hash, both request IDs, required original deadline, observed later anchor, unlock event and exact extension. The full synthetic event/result/outcome/log chain is retained under `lost-anchor-fixture`.

Recovery must derive any missing first-D0 completion/anchor bookkeeping solely from an independently durable exact first-D0 aggregate-result and per-profile proof: original first request ID, immutable hashes, `result.finished_at_clock` and `finished_at_unix`. A current or D1 clock must never supply the source-window start. If its original 1200 seconds have elapsed, freeze the unchanged source immediately before queue or unlock operations. Missing/truncated/unbound results and interrupted/integrity-invalid tickets stay pending/locked. A new candidate should test cuts before and after result preparation, result persistence, finished-event persistence, anchor persistence and guard startup. Original v3 files and failures must remain unchanged.

## Bounded positive checks

The frozen twelve terminal-D0 tests pass. Four additional independent checks pass: 16 positive checks plus the separate reproduced protocol violation. The frozen author's forty-test QA remains a historical artifact; it is not independent coverage of the lost-anchor durability boundary.

The independent flow runs complete synthetic arm A followed by arm B. A starts from an honest runtime crash, B from a blocked source-shape status; all terminal failures remain unaccepted with no invented native facts. Complete durable D0 automatically anchors +1200, and source remains read-only until explicit acknowledgment. Source-only repair then D1 and final collection use the ordinary APIs. D1 remains the second and last diagnostic and cannot reset a normally present anchor. Control final transport retains program-selected previous/SHA/history; treatment uses its default transport. Final source lock and self-seal remain irrevocable, initial cohort/capsules remain unchanged, and inactive B starts no clock while A completes.

Further independent checks establish that late acknowledgment of a normally anchored failed D0 freezes the initial source without unlocking; SystemExit, negative supervisor return and an explicit envelope interruption retain one partial profile/outcome/log and a pending ticket without continuing or retrying; explicit envelope/capture drift reports and tampering in a remote fifth-pair initial capsule prevent the first anchor. A successful D1 cannot upgrade an integrity-invalid first D0. The frozen twelve also cover missing/empty/non-durable profile outcomes, source/config/tool drift, current integrity at unlock, unchanged v2 source-domain approval after blocked D0 and guard-startup failure after a durable normal anchor.

AST comparison proves the only changed/added helper functions from v2 are `feedback_ready`, `d0_complete`, `check_request_integrity`, and `serve`. Source-domain transport and all source-domain/profile admission method ASTs remain unchanged; `source_domain.py` is byte-identical. There was no responsibility filtering, SUT/SDK/oracle rewrite or study policy adjustment.

All v1/v2/v3 frozen candidate files and both prior sealed independent reviews remain unchanged; exact hashes and AST checks are in `READSET.json` and `FUNCTION-DELTA.json`. Every new artifact is under this `v3` directory. The reproduction and test drivers are included in the sealed inventory.

This is HOST/SIM only. All service receipts/logs are synthetic. Helper `execute()`, subprocess/SDK forwarding, actual business source/design/oracles, native/render execution, real timing outcomes and Git operations were excluded. No native, business-quality or performance result follows. `REVIEW.json` records the effective changes-required verdict; `SEAL.json` binds the complete retained counterexample and positive-test artifacts.
