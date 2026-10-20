# Exact evidence-locator and manual decision format

All artifact paths are relative to the manifest's directory. The evaluator rejects
paths outside that capsule, missing files, or changed SHA-256 hashes. A JSON pointer
is RFC 6901 and addresses original raw content; it is a locator, not proof by itself.
Original native images are resolved relative to observation.json's directory, then
cited relative to the manifest directory. Source code is never imported or executed.

The manifest follows manifest-schema.json. Each observation entry pairs platform
and case exactly once. It references the original observation.json, its mapping.json,
and the exact native fixture input artifact. A JSON pointer on the mapping artifact
may select the checkpoint dictionary if wrapped. model_pointers locate the two
public model objects inside that original native input artifact. They must equal
the sealed model objects. A platform/case entry may be omitted: all affected rows
remain present and U. D0 rejects holdout entries.

A checkpoint mapping has the following fields:

~~~json
{
  "state_id":"native_state_id",
  "input_index":0,
  "trigger_action_index":0,
  "state_action_index":0,
  "after_action":0,
  "dispatch_target_pointer":"/steps/0/selector"
}
~~~

initial needs only state_id and input_index. Post-stimulus checkpoints need the
original trigger_action_index plus native state_action_index or after_action;
if both are supplied they must agree. An optional dispatch_target_pointer can
select only /steps/N/selector, /steps/N/target, /steps/N/query, or the corresponding
/steps/N/dispatch/selector, target, or query. A raw selector is either the exact
identifier string or an object with an identifier member. Without an explicit
pointer, only those six exact native fields are examined; their retained selector
values must agree. No text search or arbitrary input field is accepted as dispatch
proof. In particular the dispatch selector is not fabricated from the plan.

A visual_review artifact is an object with a decisions array. Each decision is:

~~~json
{
  "key":"ios/CASE/CHECKPOINT/FROZEN_ID",
  "outcome":"P",
  "method":"pixels",
  "reason":"Concrete measured finding.",
  "observation_sha256":"64 lower-case hex characters",
  "snapshot_indices":[0],
  "evidence":[{"path":"corpus/ios/CASE/frame.png","sha256":"64 lower-case hex characters"}],
  "target_region":{"0":[10,20,100,200]},
  "witness":"Identifies the corresponding native target and its visible region.",
  "local_counterexample":false,
  "measurement":{
    "patches":[
      {"snapshot":0,"x":20,"y":30,"size":3},
      {"snapshot":0,"x":30,"y":30,"size":3},
      {"snapshot":0,"x":40,"y":30,"size":3}
    ]
  }
}
~~~

For qualitative visual rows method is visual and measurement is omitted. For
corner-radius/border-width pixel rows, replace patches with segments:

~~~json
{
  "segments":[
    {"snapshot":0,"a":[30,30],"b":[33,30],"native_pixels_per_logical_unit":3}
  ]
}
~~~

Coordinates are original native PNG pixels. target_region maps each relevant raw
snapshot index (string key) to [left,top,right,bottom]. Measurement is not a font,
padding, or physical hit-region assertion. Native capability rows cannot receive
a visual/manual substitution. Exact measurement and qualitative criteria are in
manual-protocol.md.

A source_review artifact is an object with a decisions array. Each decision has
key, outcome (P/F/U), method (source_api), expected_sha256 copied unchanged from
the normalized row, reason, fact, and citations. Each citation contains artifact
(path/sha256), line_start, line_end, and quote equal to the exact joined source
lines, without a terminal newline. The source artifact must appear in source_files
in the manifest. U may omit citations. A P/F reviewer states exactly which frozen
source/API requirement the cited source establishes or contradicts; declarations
never stand in for runtime behavior, typography, padding, colors, or hit regions.

Original native runtime capability facts, if a future observer actually provides
them, must be part of the original snapshot.native_facts array:

~~~json
{
  "kind":"native_runtime_fact",
  "target":{"identifier":"the.exact.public.identifier"},
  "field":"the_exact_frozen_native_field",
  "value":44,
  "origin":{
    "method":"native_physical_hit_region",
    "platform":"ios",
    "binding":{"same":"exact original snapshot binding object"},
    "source_kind":"runtime_inspection",
    "native_probe":"named original runtime inspection probe"
  }
}
~~~

The method equals the row's capability. For applied scaling the field is
applied_accessibility_scaling and value contains dynamic_type (iOS) or font_scale
(Android). A synthesized companion JSON claiming source/AX facts is not original
runtime inspection evidence and cannot satisfy this format.

The output follows report-schema.json and must cover exactly normalized plan
required_keys. P/F requires compact original native/source/image evidence locators.
Actual values remain compact scalars/lists or a visual witness; entire snapshots
are not copied per row. Archive audit recomputes common callback preconditions,
requested-target binding and actual native/capability matchers. Missing evidence
stays U. Negative controls exercise false P and false F rejection and omission
rejection without any candidate.
