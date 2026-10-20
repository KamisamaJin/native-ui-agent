# Frozen exact-row matching and paired D0 reporting conventions

Prepared without opening submissions, assignment, native evidence, self-reviews,
root git status or results. Active grader remains sealed V3. This supplement only
joins already sealed grades; it cannot alter expectations, gates, matchers,
tolerances, grade outcomes or the phase barrier.

## Delivery and output order

1. Receive BOTH anonymous D0 common-v4 capsules, grade each using V3, and seal both.
2. Receive BOTH anonymous FINAL common-v4 capsules, grade each using V3, and seal both.
3. Receive anonymous original self-reviews; match to the sealed D0/FINAL exact rows
   and seal both matching reports.
4. Receive BOTH source-paired D0 corpus sets; grade them with the same V3, compare
   to their already sealed common-v4 anchor reports, and seal both paired reports.
5. Receive formal assignment release only after those seals.

Intended output base is design/private/evaluation/. Within it:

- d0/<anonymous_id>/grade.json and SEAL.json
- final/<anonymous_id>/grade.json and SEAL.json
- selfreview/<anonymous_id>/matching.json and SEAL.json
- paired-d0/<anonymous_id>/paired-grade.json, comparison.json and SEAL.json

These are future output conventions; no such grades are generated now. Each seal
commits the manifest, report, source/evidence capsule commitments, phase identity,
evaluator V3 commitment and timestamps. Preserve the incoming original capsules.

## Incoming capsule requirements

Use the frozen manifest-schema.json from initial preparation, V3 report-schema.json
and unchanged decision-format.md. Native observations and mapping files remain
per platform/case; original fixtures.json model pointers are /initial and /updates/0.
iOS pixel geometry additionally needs original app_frame and original PNG dimensions;
Android uses original logical_viewport_dp. Keep artifact paths relative to the
manifest directory and SHA-256 bound. Initial collection has four cases per
platform; FINAL has six. Missing evidence creates U, never omitted grade rows.

Self-review matching requires original review artifacts and exact quotes with
line-range/byte-range citations, plus the already sealed anonymous D0 and FINAL
report references. Report anonymous_id must agree across those phases.

A paired set requires:
- The already sealed common-v4 anchor grade and the paired corpus/grade, both D0.
- Equal anonymous source identity and the exact same D0 production-source capsule
  commitment. Retain collector/host integration commitments separately.
- Original manifests/artifact hashes and separate acquisition timing/cost records.
- Opaque corpus IDs. Do not include formal arm/assignment labels before release.

A source-pair mismatch is invalid pairing, not a component miss or observation U.
Do not run code, repair components, or collect additional business variants during
matching. A later source discrepancy is recorded separately.

## Exact atomic-row join

Join only exact frozen key, platform, case, checkpoint, category, denominator,
method and expected_sha256. D0 joins exactly 3,185 keys; FINAL contains the same D0
keys plus its frozen holdout keys. Missing/duplicate/unplanned keys and expectation
mismatches are hard errors. Do not fuzzy match labels, consolidate repeated symptoms
into an invented cause, or count input/source rows as runtime coverage.

The helper exact_rows.py checks joins and derives transition summaries; it never
grades native evidence. Its input reports must already be immutable V3-validated
reports whose raw evidence and common callback gate were checked at grading.

## Original self-review matching

Manually split the original review into atomic observed-problem claims. Preserve
the exact text and original artifact citation. For each mapped claim, record the
exact D0 row key and a short concrete explanation of the same requirement. A broad
claim may map multiple rows only with explicit justification for each row. Do not
infer a claim from a proposed repair alone. Separate claimed passes, limitations
and planned repairs in the review notes; they are not observed-problem detections.

For each observed-problem claim/row mapping:
- D0 F is a confirmed problem in that row's own denominator.
- D0 P contradicts that mapped problem claim.
- D0 U is unassessed and cannot count as a false positive, detected business miss
  or handler failure.
- Primary business detection requires a D0 runtime business F with a successfully
  established requested stimulus. Initial ungated business facts are descriptive.
- A primary D0 miss is repaired only when its same FINAL row is P after established
  requested stimulus; FINAL F means persisted, FINAL U means repair unassessed.

Deduplicate detections by exact row key across claims. Retain claim-level detail
separately. Report unmatched confirmed primary miss keys explicitly. Holdout rows
are excluded from matching because the original review did not receive holdouts.
Never change a frozen grade based on a review statement.

The review_citation objects are verified against the hash-bound original artifact
before calling the helper: an exact UTF-8 line or byte range must equal quote.
The matching report cites both input grade hashes and the original review hash.

## Paired D0 report

Compare the two observation corpora on identical D0 source. Retain every exact
row, both original outcomes, stimulus establishment and denominator. Emit all nine
P/F/U transitions per denominator and platform. P+F is assessed runtime coverage;
U remains required but unavailable. Input-member integration and source API have
their own denominators and never inflate runtime observation coverage.

Use the already sealed common-v4 grade as the explicit anchor, not an infallible
oracle. A confirmed anchor business F after requested stimulus is observed by the
paired corpus only if its same row is also a confirmed business F. A paired U
is a missed/unavailable observation of that anchor miss, never a business pass or
failure. Assessed P/F disagreement on identical source is retained as a conflict,
not silently resolved using source, review text, or collector identity.

Counts remain descriptive for these same-source observations. Do not infer a
causal tool effect, generalize beyond the corpus, or release assignment early.
Acquisition attempts, success/blocked/unavailable routes, retries, native durations
and costs remain separate original records; this row-join helper does not invent
timing or execution-success facts from counts.

## Schema and archival rules

matching-input.schema.json and paired-input.schema.json describe the compact
supplementary inputs. Output matching.json and comparison.json contain the helper
outputs plus immutable artifact references/input commitments. Every new report
seal lists those inputs, V3 and this convention commitment. No grade is produced
as part of preparation. Synthetic controls use only generic fabricated grade rows.
