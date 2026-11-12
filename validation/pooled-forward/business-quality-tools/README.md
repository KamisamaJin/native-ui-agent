# Grade seal and timing ledgers

These operator helpers do not judge product quality, invent consensus, start an
SDK, change the frozen tools, or reset a source window.

`quality_clock.point()` records both shared kernel and Unix timestamps and retains
process-relative monotonic values as diagnostics. `interval()` prefers recorded
`clock_gettime(CLOCK_MONOTONIC)` endpoints. Earlier independently written Python
3.9/macOS endpoints use their original Unix times with an explicit wall-clock
fallback limitation. Negative raw monotonic differences are never clamped into
low costs. The frozen speed benchmark, core lease/capture validity and public
source-budget controller already use the shared kernel clock.

`grade_records.py close-pair` verifies two original output seals and input pins,
then closes their concurrent episode once. It reads only grade identity for this
operation; sealed output is not a product pass. `correct-clock` and
`correct-split-cause-clock` append corrected timing files while preserving every
earlier START/END, grade, unknown and raw duration. Active original/supplement
review intervals and intervening research wait remain distinct.

The new `operators/cohort2/coordination/prepare_cause_dispatch_v2.py` keeps the
original prompts, two independent contexts per version, serial version order and
global cause/alarm/matcher/reveal barriers. Only new START clock fields differ.
The already-started Case03-I keeps its original START and uses Unix fallback at
closure; it does not receive a replacement start.

Fifteen author HOST controls cover independent Python clock probes, corrupted or
incomplete seals, one-context closure, readonly outputs, non-overwriting writes,
parallel pair accounting and retained legacy/split timing corrections. These are
synthetic ledger checks, separate from independent native product reviews.
