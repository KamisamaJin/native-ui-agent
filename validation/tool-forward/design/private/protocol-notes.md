# Private independent design and grading protocol

## Frozen scope and procedural blindness

This design was created independently in `validation/tool-forward/design/`. Before freeze, the only project input read was the expressly permitted pinned upstream `validation/fresh-blind/cache/unit-cf99de/alerttoast/Package.swift`. It declares Swift tools 5.3, iOS 14, and macOS 11. No root README, Skills, prior experiments, old agent material, mappings, implementation workspace, tool implementation, candidate source, self-review, or prior bug condition was read. Work used local artifact construction and validation only. No production sources, network services, external accounts, or external messages were changed. The designer did not delegate.

This is procedural blindness on a shared filesystem, not OS isolation. No claim of sandbox enforcement is made. The root engineering agent receives only artifact paths, SHA256 hashes, timestamp, and counts before its tool version is frozen. Public task contents are released only after root explicitly states that the tool version is frozen and requests the public brief. Concrete private fixtures and holdouts remain private. Existence of a public requirement in the brief must not be mistaken for release of concrete hidden input values.

The four main artifacts are `public/brief.md`, `public/public-example.json`, `public/reference.svg`, and `private/oracle.json`. This protocol is a fifth, supporting sealed artifact. `freeze-manifest.json` records the main four hashes, this support hash, and one UTC freeze timestamp. Do not silently edit any sealed artifact. A necessary correction must be a separately dated, hashed erratum, with an explicit statement of whether it changes requirements, inputs, or evidence interpretation. A new design revision is not retroactively substituted for this freeze.

## Units and counts

A logical case has one environment, full concrete models, and an ordered sequence of labeled checkpoints. There are **6 initial cases and 2 previously unseen repair holdouts**. Every distinct fixture model appears at a full rendered checkpoint. Every action checkpoint retains the preceding model until the next explicit `replaceModel` trigger. No caller update is implicit.

| Case | Split | Concrete models | Checkpoints | Mandatory runtime assertion templates |
| --- | --- | ---: | ---: | ---: |
| C01 | initial | 4 | 7 | 771 |
| C02 | initial | 3 | 7 | 1009 |
| C03 | initial | 3 | 6 | 835 |
| C04 | initial | 3 | 6 | 630 |
| C05 | initial | 2 | 4 | 352 |
| C06 | initial | 3 | 5 | 707 |
| H01 | repair-holdout | 3 | 6 | 958 |
| H02 | repair-holdout | 5 | 9 | 1319 |

There are **26 concrete models, 50 logical checkpoints, 26 full rendered checkpoints and 24 controlled-response delta checkpoints**. Initial cases contain 18 models and 35 checkpoints; repair holdouts contain 8 models and 15 checkpoints. There are **6,581 runtime assertion templates plus 196 common source assertion templates = 6,777 mandatory assertion templates**.

Each case runs once on Android and once on Apple: **16 native case executions and 100 native checkpoints**. Apply each assertion only to its explicit `platforms`. Common source checks run once per candidate source, not once per case. There are **6,766 Android assessments and 6,775 Apple assessments = 13,541 platform-expanded mandatory assessments**. The difference is source applicability, not a different business contract. Initial runtime templates total 4,304; holdout runtime templates total 2,277. Common source assertions remain applicable during holdouts but are not counted twice merely because a source tree was already assessed.

| Aspect | Mandatory templates |
| --- | ---: |
| sourceOnlyAPI | 186 |
| sourceOnlyCompatibility | 10 |
| nativeSemantics | 2259 |
| observedPixels | 2556 |
| actualCallbacks | 117 |
| nativeBounds | 1315 |
| actualNativeAction | 230 |
| nativeTypography | 104 |

Count an assertion by its full `key`, with the platform prefixed in a grade record. Keys are unique. A criterion has one outcome. An expected object such as `propertyEquals: {name, value}` is one relational equality; platform maps are alternatives for the relevant native platform, not hidden conjunctions. Tolerances describe a measurement acceptance interval and are not separate scored claims. No free-form “whole card passed” statement substitutes for the keyed outcomes.

## Execution and checkpoints

Use the concrete environment in each case. Host width is offered width, not card width. Measure logical units, with physical pixel scale and coordinate origin recorded. On Apple use the named Dynamic Type category, without assuming its glyph ratio equals the Android `fontScale` number. Font scale/category, appearance, direction, parent viewport, and source-build identity must be recorded by the actual host. Set direction on the host even when caller prose is in a language with a different natural script direction.

Start each case in its initial model. Execute triggers in order on the same mounted presentation slot. “Same live instance” means the same mounted host/component position and current process, with no app restart; SwiftUI value-view recreation during an update is normal and allowed. `replaceModel` replaces the entire model, never merges only changed fields. Cases may restart between cases. The root model is held after every activation and no automatic echo is allowed. Capture callbacks after native idle, before applying the next trigger. Wait for ordinary native rendering idle; there is no artificial business timeout or delayed automatic completion to await.

For a `full-rendered-checkpoint`, capture enough parent-scroll screenshots for the complete card, bounds, accessibility state, and the explicit other evidence types. Scroll to the top for the `yAtParentScrollZero` measurement. Retained scroll offset immediately after replacement is not itself an error. For a `controlled-response-delta`, assess the explicit keyed assertions and trace the actual action. Passing a delta does not claim a fresh full visual audit of the whole card. Every fixture model already has a full checkpoint, so each concrete visual state has a full mandatory visual/bounds/semantics set.

`target` names such as `.title`, `.description`, `.tag`, and logical panel unions identify the corresponding visible/model field; they are not extra required test identifiers beyond P06. Geometry assertions on the documented `rr.*` identifiers require actual runtime frames. Reading-order comparisons concern meaningful descendants, ignoring decorative/non-accessible containers. An unselected native selected trait may be absent rather than literally false; this is equivalent to false. The declared Android/Apple role and state alternatives are allowed exactly as described by P06.

Every callback interval includes an explicit expected count. For nonempty intervals, each payload property and its exact shape are mandatory separately. Thus a screenshot of a changed state cannot substitute for action capture, and a correct payload cannot compensate for a duplicate extra event. For disabled controls, native activation is intentionally attempted and a zero-event trace is required. Do not fabricate a tap success from a script that was never executed. If a native automation API refuses disabled activation, a recorded hit test/tap attempt plus a real empty callback interval is acceptable for the tap stimulus; it does not prove accessibility activation if that requested activation was not possible.

## Visual rubric

The reference SVG conveys structure, rhythm, selection emphasis, decorative tile, and status alternatives. It is neither a runtime screenshot nor an exact golden. Never grade exact font glyphs, exact line breaks, native spinner geometry, parcel/check/chevron glyph shapes, or platform rendering antialiasing against that drawing. Use the public brief and the case model for exact strings and required regions.

For observed-pixel assertions, inspect all the captures needed to see the entire required string or region. A `fullyReadableTextEquals` criterion means the supplied text is present in full and readable, with no text lost to truncation, clipping, horizontal scrolling, or occlusion. Script shaping and native bidirectional visual order are allowed. Logical character preservation is checked independently where actual native semantic labels are specified. Do not infer a long unobserved ending from a short visible prefix or a source string. A parent-scroll seam is acceptable if adjacent captures overlap enough to establish complete coverage and unchanged state.

The main visual dimensions are: hierarchy of heading/section/body/total; correct status-specific structure and conditional panels; legibility of all caller content; non-overlap and reflow; visible selected versus disabled distinctions; directional leading/trailing placement; themed surfaces/text; and clear action affordances. Each listed keyed predicate is mandatory. There are no subjective bonus points that offset a failed mandatory predicate.

Sample flat fills away from text, shadows, boundaries and antialiasing. Accept an RGB channel delta of at most 12. Radius measurements accept their per-assertion tolerance. Respect the specified type-size ranges and native mode mapping. A base 52-unit item tile may remain 52 or grow naturally at enlarged native text sizes; the oracle uses a minimum in enlarged modes. A notes-panel radius applies to the complete disclosure/body panel, not an artificial separately rounded row while open. A visual selected-indicator assertion requires visible selection, independently of the native selected-state assertion.

Use native bounds for exact card placement, width containment, order, and minimum touch targets. Pixels alone do not establish invisible touch padding. A measured text container inside the content frame does not establish that its ink is unclipped; that is a separate screenshot predicate. A role/label dump alone does not prove draw order, text color, or visible absence.

## Supported and unsupported evidence

The oracle defines the allowed evidence method for every assertion. Evidence must be bound to the anonymous candidate source snapshot, native build/install/run, case, model checkpoint, platform, and environment. Use source hashes/build IDs, execution logs, and state labels to establish that screenshots and runtime traces came from that source. Provenance cannot be supplied solely by a candidate's self-review. Unbound or contradictory evidence is unsupported.

- `renderedPixels`: actual native app screenshots. A browser mockup, SVG, illustration, source preview, image of code, accessibility label, or implementation constant is not pixel evidence of the component.
- `nativeBounds`: actual native/accessibility/instrumentation frames, with unit scale and scroll coordinate information. Bounds calculated from source constants or estimated only from pixels do not count.
- `nativeSemantics`: actual native tree output, traits, names, enabled/selected/checked/expanded values, actions, and identifiers. A source `testTag` or accessibility modifier proves only a source declaration and cannot substitute for an observed runtime tree.
- `callbackTrace`: actual captured typed callback invocations in the specified interval. A static handler, app-authored assertion of success, screenshot, or planned script is not a callback trace.
- `nativeInteraction`: execution evidence for actual native tap/accessibility activation, scroll behavior, environment, or same-host model replacement. Source commands without successful execution/provenance do not count.
- `nativeTypography`: resolved-font/layout instrumentation at the actual rendered native text. It must identify the native system font/base size/effective native scaling under the recorded environment. Source font declarations, screenshot resemblance, and a current-runtime build do not prove resolved typography. If the platform cannot expose it, retain **UNASSESSED** for those predicates; do not invent a measurement.
- `sourceAudit`: anonymous source may establish the public construction API and the explicitly source-only compatibility claims. Check unguarded APIs, imports, language features, fallback paths, and declared target preservation separately. A build on a current installed iOS runtime does not prove iOS 14 or macOS 11 availability. Current iOS runtime evidence is not macOS runtime evidence. The design requires source compatibility on macOS 11; it does not require a macOS 11 screenshot or a run on that historic OS.

No source inspection is used as a substitute for required runtime semantics, action capture, pixels or native geometry. Missing access, unsupported inspection, absent output, a hidden/unreadable region, or a script without executed evidence is **UNASSESSED**, not PASS and not automatically FAIL. A directly observed contradiction is FAIL even if another field is correct. If evidence is contradictory or cannot be attributed to a case/state, do not choose a favorable interpretation; mark the affected predicates UNASSESSED and describe why. An inaccessible aspect is reported as inaccessible explicitly, not silently omitted.

## Outcomes and strict rollups

For every platform/key, report `PASS`, `FAIL`, or `UNASSESSED`, with evidence locator(s) and a concise reason for FAIL/UNASSESSED. The key's criterion is the assessment unit. Additional observations can be reported separately but cannot become a hidden acceptance requirement. If a public detail has not been established by an enumerated predicate or other accepted evidence, do not claim that unexamined detail passed merely because nearby predicates passed.

A case/state/aspect or public-rule rollup is PASS only if **every applicable mandatory predicate in that rollup is PASS**. Any FAIL makes that rollup FAIL. Otherwise, any UNASSESSED makes the rollup INCOMPLETE. A whole-candidate PASS requires all applicable mandatory predicates, including source-only compatibility, to pass. Never report a full-rule pass while a required sub-aspect is unassessed. Report pass/fail/unassessed counts, evidence coverage and concrete defects separately; do not turn unsupported claims into a weighted positive score or hide unknown coverage behind an average. Native-platform results remain separate until their strict combined rollup.

A source-only compatibility PASS must be labeled as such. It is not a claim that an old operating system was run. Conversely, the absence of an old OS runtime is not a failure of this task, which calls for current installed iOS runtime and minimum-target source compatibility. A passing screenshot-only subset is not a passing native component.

## Independent later grading and seals

After the tool version is frozen and the public brief is requested, release only the public artifacts. Keep the six initial concrete inputs and two repair holdouts private unless the experiment coordinator expressly authorizes a controlled fixture release for execution. A holdout is not shown during initial repair. All held-out behaviors are already public; only their concrete combinations and strings are withheld.

For later grading, accept anonymous candidate source/evidence bundles in newly staged locations under this design directory. Do not read version labels, assignment/tool mappings, build strategy descriptions, implementer self-reviews, earlier reviews, or claimed success. If a bundle reveals these, record the contamination and request an anonymized replacement before forming the comparative outcome. Grade each specimen against the same frozen oracle and evidence policy. Similar source must not cause evidence to be borrowed across specimens.

First create and seal each independent assessment and the anonymous comparative outcome using SHA256 and UTC timestamp. Only after the independent outcome is sealed may sealed reviews be opened/matched, then assignment/version mappings revealed. Keep the independent pre-unblinding outcome intact. Later reconciliation is a separate dated artifact, never a rewrite of the sealed grade. The independent designer/grader must not infer candidate identity from tooling style or ask the root engineering agent for a favorable mapping.
