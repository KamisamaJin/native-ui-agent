# Independent neutral paired review, pass 2

All eight supplied runs preserve the same **54 supported native assertion IDs and pass statuses**, with no newly missing or conflicting required native evidence. All four required states, all nine targets in each state, both full-content scans, the real tap callback and same-instance quiet caller replacement are preserved. This conclusion comes from exact state/input/event bindings, original node facts, image hashes and raw interval calculations, not snapshot counts.

The remaining six runs each evaluate to **64 passed, 2 failed, 0 unassessed** after actual visual review. Like the sealed pass1 pair, they fail `replaced/action-appearance` and `disabled/action-appearance`. The one confirmed visual root cause remains the unintended disabled rendered palette. Original PNGs again show `#EDF0F3` fill / `#A1A8AF` solid glyph ink instead of the sealed `#DCE2E7` / `#55616C`. Native control height, disabled state and blocked dispatch pass their separate requirements. No source or expected value was changed to make the test pass, and no fix or successful retest is claimed.

The original narrow images add no observed clipping, overlap, missing cards or wrapping failures. The actual environment is light / xxxLarge / LTR at 3× scale, with a 280 × 600 pt viewport and 248 pt available child width. Every required target has a fully visible frame in its own current binding. The two complete states each use ten overlapping images. Their independently recalculated content heights are 2870.333 pt before replacement and 2933.333 pt afterward, or 4.78 and 4.89 viewports. The later title and summary wrap to more lines, and the scan correctly follows the changed height. Each scan covers zero through the real bottom with zero gap. Ordinary content stays at 2346.333 pt in eight overlapping frames.

The two original supported callback checks pass in every run: action 1 demonstrably dispatches a unique enabled native control through `xcui_tap` and emits exactly `notes.reviewed.A`; action 2 demonstrably replaces caller input in the same native process and component identity with no business callback. Action 4 remains `blocked_disabled`, with `attempted:false`, no new event and unchanged state. The callback evaluator returns unassessed for that unexecuted activation rather than scoring its empty interval as success. This unassessed diagnostic is distinct from the complete 66-row contract, which deliberately does not claim disabled callback behavior.

Every original snapshot was checked for correct canonical source input hash, matching before/after binding, coherent image association, event-receipt revision and actual environment. The native collectors report no issues or serialization failures. Compiled bridge bytes and exact strategy-specific config/action values match the original neutral seal. The supplied legacy collector provenance differs from the candidate collector, as already disclosed in pass1; no files outside the supplied captures and authorized snapshot were inspected.

The observed native-command timings are repeatable in both start orders:

| Fixture | Repeat / start order | Legacy seconds | Coalesced seconds |
| --- | --- | ---: | ---: |
| ordinary400 | 1: legacy first | 265.778 | 102.567 |
| ordinary400 | 2: coalesced first | 256.970 | 102.250 |
| narrow280-large | 1: legacy first | 321.691 | 127.077 |
| narrow280-large | 2: coalesced first | 324.748 | 127.121 |

Within these fixed requests, the coalesced native-command wall is descriptively 60.2–61.4% lower while retaining all required native verdicts and the same detected visual failure. This is limited to two fixtures, two repeats, one simulator/runtime, the supplied collector versions and these action paths. The first pair includes a cold boot; these observations are not a general runtime guarantee, and nested operation walls are not additive costs.

Thirty labelled contact sheets cover all remaining required full sequences and the two scoped visual target locations. The associated manual reports bind the original PNGs and SHA256 values. Representative original PNGs were also opened directly. `native-audit.json` contains the per-frame facts, per-state coverage and comparisons; `completion.json` contains the six evaluated results and actual timing/order data. Pass1 stays sealed and separate. No SDK or device operation was executed in this review. Generic computed SwiftUI styles, internal padding and physical touch bounds remain outside measured claims; a second independent visual oracle has not reviewed these judgments.
