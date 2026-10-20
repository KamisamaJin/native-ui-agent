# Common infrastructure and retained failures

These changes apply to the experiment, not to the Skill treatment. None is
credited as a v5 benefit. Original bytes and unsuccessful attempts are retained.

- Before either builder, design v1's nested component scroller was corrected to
  an intrinsic-height component in the existing host-owned scroller. Design v2's
  Android bridge was corrected to the actual `ObserverBridge.Content(JsonObject,
  onEvent)` entry point. Histories retain both versions; business acceptance and
  the denominator did not change. Internal component reset subtrees are allowed;
  the common caller must not recreate the component to fake model replacement.
- QuickLook produced a square, cropped reference preview. Its PNG, command and
  provenance remain under `reference/`. The full SVG was rendered with Sharp,
  inspected and delivered equally to both builders before implementation. The
  annotated SVG is a schematic reference, not a pixel golden.
- Static grader schema audits before any source/raw delivery corrected integer
  snapshot indices, native checked-state interpretation, and actual-value union
  across different native paths. Grader-v1 is preserved in design history.
- Grader-v2 removed expected-selector-as-proof: actual raw requested selector,
  state identity and fixture binding must establish the gate. A separate mapping
  derivative supplies explicit actual step pointers; original actions stay
  unchanged. No callback helper, successful-dispatch policy or oracle changed.
- Grader-v3 reads Android semantic dimensions from the actual unclipped layout
  rectangle. Expanded touch bounds remain in provenance. Frozen uncertainty and
  thresholds did not change. This was a static field audit before independent
  raw delivery, while builders were reviewing their own captures. Grader-v2 is
  preserved; the preregistered v2/v3 replay reports this common change separately.
- Common selectors exclude declared absent/N/A targets before execution. Those
  requirements remain in the fixed denominator and need proper absence evidence.
  The operator supports separate original iOS/Android action files. These are
  collection plumbing, not native observer changes.
- Own-D0 operator copies are explicitly retrospective. Each native invocation
  independently attests its actual inputs and native sources. Subsequent
  acquisitions additionally copy/hash the operator before spawning processes.
  No launch-time operator witness is backdated onto earlier captures.
- A root inspection initially requested the wrong `files` key from the grader
  seal; its actual key is `gradingFiles`. This inspection failure changed no
  native source, evidence, expectation or score.
- The first native-normalization verifier compared in-memory candidate tuples
  directly against their archived JSON arrays and failed. Comparing the exact
  JSON serialization round trip fixed that verifier; frozen normalization,
  grader, raw evidence and scores were unchanged. All 32 D0 case/version
  normalizations and 10 full grades then reproduced.

Raw paired-v4 acquisition ran after all common captures, overlapping independent
earlier-stage grading. The timestamped scheduling record preserves this choice;
paired results remain withheld until both self-review outputs seal. Frozen
source/holdout barriers and scoring delivery order are unchanged. This reduces
experiment waiting only and does not alter either primary development endpoint.

The candidate arm's own iOS P2 D0 acquisition exited 1. Its original native JSON,
screenshots, exact command, logs and failure remain archived. Acquisition success
is separate from product correctness. Any eventual diagnosis must distinguish
an observer/session failure from an exercised product defect; no silent retry
replaces this attempt.
