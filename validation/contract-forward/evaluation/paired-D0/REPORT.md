# Same-source paired D0 collector comparison

Both anonymous arms use the same D0 production component and exact common fixture/action hashes. V5 captures are new actual acquisitions. V6 raw/native-base grades are exact reuse of supplied common D0 evidence. Eight V5 grades were generated with the unchanged frozen grader and manual=None/source_root=None/api_review=None. Eight supplied V6 per-case grade files were copied byte for byte, with a hash ledger.

Aggregate grade.json files retain all528 public runtime rows plus separate checks per arm/version. Comparison uses only506 rows in native_content, business_current, business_transition, style_native and native_geometry. No visual/API/input judgment contributes a collector gain.

| Arm | Version | Native P | F | U | N/A |
|---|---|---:|---:|---:|---:|
| source-a | V5 |442|3|35|26|
| source-a | V6 |439|3|38|26|
| source-b | V5 |445|0|35|26|
| source-b | V6 |445|0|35|26|

There are no V6 U-to-P/F gains in either arm. Source-a has three V6 P-to-U losses: P2 Android blocked/reserve-height, course-changed/reserve-height and reserved/reserve-height. V5 had an assessed passing native lower bound; V6 captured conflicting native edge-derived heights inside each selected state and therefore remains U. Each changed row retains both actuals, state/snapshot indices, reasons and evidence. Source-a has503 unchanged cells and source-b506. There are no assessed P/F conflicts or other disposition changes. No new natural business/style defect detection is demonstrated; those denominators remain zero/N/A.

The three source-a raw failing geometry rows(browse/editing/replaced Reserve height) remain F in both versions. Their serialized47.99994000000004dp values are below the frozen48dp lower bound by0.00006dp. The separate numerical-resolution sensitivity ledger retains all near-threshold F/U rows without altering policy or claiming natural product defects. The P-to-U losses similarly concern threshold-straddling geometry facts, not missing business transitions.

Actual command sums including failures, in seconds:

| Arm | Version | iOS | Android |
|---|---|---:|---:|
| source-a | V5 |209.180|21.747|
| source-a | V6 |192.194|15.705|
| source-b | V5 |208.730|13.436|
| source-b | V6 |192.172|25.256|
| Both arms | V5 |417.910|35.183|
| Both arms | V6 |384.367|40.961|

All four P2 iOS commands(both versions ×both arms) exited1. Their exact native-summary failure text is:

    XCTAssertTrue failed - native control not enabled or no usable visible point

The bound blocked action targets In person with enabled:false and dispatch attempted:false/succeeded:false. This is an acquisition assertion on an expected-disabled native option, not an established product handler defect. Callbacks remain U under the unchanged successful-dispatch gate. These observations report bottom_reached:true, missing_identifiers:[], and zero incomplete post-action target sets. Incomplete target coverage is not the demonstrated failure cause.

commands.json and native-failure-ledger.json retain exact command/native-summary paths and SHA256 values, exit codes, UTC times, wall durations, coverage and blocked-dispatch evidence. P1 iOS and the named Android commands exited0. Source builds exited0; that and usable native observations do not establish successful end-to-end XCUITest/acquisition. The old sealed D0 report's statement that all eight acquisitions succeeded was mistaken: reused V6 P2 iOS commands also exited1. Earlier factual-addendum coverage/search wording was a provisional root attribution; the exact native-summary now identifies the disabled-control assertion. This report corrects that factual scope without editing any prior seal, addendum or grade. Failed acquisition is not converted into product-logic F.

V5 actual acquisition followed V6 by about20 minutes and was not interleaved or randomized. Both versions' iOS P1 build receipts show a cache miss and P2 a cache hit. Gradle/cache state, concurrent source/FINAL work on the shared Mac, shared host contention, order and failed assertion/search duration limit all speed claims. The sums are process wall durations, not elapsed time for a concurrent workflow. Neither total nor per-platform differences establish a treatment-caused speed improvement.

Each alias has per-case files under v5/native-base and v6/native-base, aggregate v5/grade.json and v6/grade.json, and comparison.json containing every gain(empty), loss, assessed conflict(empty), other change(empty) and unchanged status cell. All prior D0/FINAL/selfreview and factual-addendum seals remain byte-exact. No assignment or treatment mapping was inspected. Both paired arms are jointly sealed before reveal.
