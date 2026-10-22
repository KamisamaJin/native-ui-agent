# Preserved failures and evidence limits

[FAILURES.json](FAILURES.json) is the generated, checkable index of all main native
commands, nonzero exits, strict acceptance failures, unknown rows, original check
commands and preserved engineering attempts. [TABLES.md](TABLES.md) separates product
causes, observation limits, original alarm semantics and repair outcomes. A green
integrity/CI result never means that every UI assertion passed.

The main run retains **9 nonzero native exits out of 108 commands**: own D0 1,
common D0 1, own FINAL 2 and common FINAL 5. Merged D0 acceptance has 36 confirmed
product manifestations; FINAL has 0 F and 148 U across both arms. There is one D0
and six FINAL qualitative panel disagreements, exposed in
[DISAGREEMENTS.md](DISAGREEMENTS.md), including unchanged source/launch/PNG evidence
with different model interpretations across stages. No later pass replaces an
earlier failure, and unknown is not a repaired or passing cell.

Original unscored grid-column discoveries are supported by both claim reviewers:
one broad v7 finding and seven per-state v8 findings. They remain outside the
prospective ledger rather than being counted as unrelated-atom TP or FP. Three
additional v8 natural-wrapping alarms retain explicit original support and disputed
acceptance; they stay unresolved. [The result interpretation](RESULTS.md) explains
why the 1-versus-10 unresolved alarm counts are not independent bug counts or a
measured false-positive-rate advantage.

## Native collection and original discoveries

The own and common corpora preserve original command arguments, input/source hashes,
UTC/Unix timings, native summaries, observations and PNGs. Some iOS long-content
sweeps fail their overlapping full-content coverage check while still producing
state-bound observations. Those exits are retained. A target-local fact can only
be used within its own evidence scope; an incomplete sweep cannot prove a whole
state has no clipping or overlap. No retry replaces a failed benchmark acquisition.

Every original self-review remains under `submissions/<unit>/original-review`.
Generated bound findings and their original requests are retained alongside free
descriptions, uncertain concerns, machine failures and explicit duplicates. A later
repair does not backfill an original detection. Discoveries outside the selected
ledger remain visible but do not retrospectively enlarge the scored universe;
unmapped or unresolved semantics are not automatically false product alarms.

The common acquisition package uses sealed base action routes without four
after-target observation extensions present in the own generated routes. Fixtures,
bridges and the business route otherwise agree. Both arms share this harness scope
gap; missing common evidence remains unknown. [The launch-input audit](action-scope.json)
retains exact hashes. No mid-study route replacement, extra capture or new passing
evidence is introduced; own/common cost differences cannot prove collector speed.

Unsupported iOS computed font styles remain unknown. Rendered-color results concern
the approved native-box sampling regions, not all canvas pixels, generic padding,
computed font properties or physical hit areas. Independent qualitative or cause
disagreements remain unknown. AI agreement is not human ground truth.

## Engineering attempts before product scoring

- The [independent neutral probe](independent-probe/REPORT.md) preserves its failed
  lazy-content coverage sweep, original exact-width environment mismatch, separate
  eager probe and fresh provider-encoding acquisitions. Later passes do not replace
  those original failures. Current frozen-tool replays preserve their original
  requests and reject pre-release bundles whose generated format no longer matches.
- `operators/unit-attempt-*.log` retains tool development failures before the
  tested release freeze. Neutral schema/metrology negative controls intentionally
  submit invalid evidence; they are engineering tests, never seeded product bugs.
- [The preseal launch control](operators/preseal-launch-control.json) confirms that
  SDK acquisition was refused before the complete cohort barrier. The SDK was not
  launched to manufacture a product failure.
- Both design proposals and their separate reviews are preserved. The first design
  was revised for specification/sampling ambiguities before any product candidate
  existed. [Scope deviations](operators/design-scope-deviation.json), the failed
  initial design-closure attempt and preimplementation adapter revisions remain
  available. They are shared process work, not exclusive v8 detections.
- [The historical verification deviation](operators/historical-parser-deviation.json)
  preserves an auxiliary YAML parser error and a failed reporting-path retry. The
  corrected 73-check plan passed: 68 unchanged successful records were explicitly
  reused and five omitted checks were actually executed. No product, evaluator,
  expectation or original verdict changed to obtain that result.

The exact publication inventory includes these attempts and raw artifacts while
excluding SDK/build caches. [REPRODUCE.md](REPRODUCE.md) describes SDK-free replay;
the write-once producer directories cannot be reused for a new native experiment.
