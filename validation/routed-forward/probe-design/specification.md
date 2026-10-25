# Independent neutral controller forward probe

This specification is fixed before inspection of the execution controller. Only
the skill-creator instructions, native-ui-agent reference contracts, and
`test_state_plan.py`, `test_review_contract.py`, `test_design_contract.py`, and
`test_native_geometry.py` were read. No prior studies, business fixtures,
controller source, controller tests, or implementation results were inspected.

## Realistic request

“Finish verification of the folded-paper sample viewer. Both `front` and
`reverse` states must show the proper label and a fully visible sample. Check the
sample's public accessibility box against the independently pinned dimensions,
and inspect the original state images for separation between the caption and
sample. When a problem is fixed, retest the affected scope, finish queued image
review, and restore the complete selected-state coverage before delivery.”

The fixture has no business domain. `fixture.json` fixes the state matrix, visual
proposition, source revision, action routes, required cells, retry budget, and
numeric controls. The PNGs are synthetic diagrams authored here; they are not
SDK output and do not validate native acquisition or visual judgment quality.

## Observable controller contract

Names below are semantic categories. A thin adapter may map the implemented
public API's names to them, but may not change expectations, add private-field
knowledge, rewrite controller outputs, or substitute an intended answer for a
missing result. Preserve both raw requests/responses and normalized outcomes.

- `image_review`: read existing original image/observation evidence and submit an
  actual bound qualitative observation. It must not launch the native SDK.
- `sdk_acquisition`: source/input/state/coverage or measurement evidence must be
  collected through the native transport; the acquisition receipt is separate
  from image review.
- `repair`: a valid failed assertion is a retained finding. A targeted repair
  plan names its actual state/cell and required related regression scope.
- `blocked`: schema/identity/integrity error or exhausted retry. It cannot earn
  passing coverage or silently remove a selected cell.
- `complete`: every selected, applicable cell has a valid current verdict, no
  required full-content sweep is missing, and no queued image review remains.

All review imports are bound to pinned design/policy/plan, exact current source
fingerprint, original observation bytes, original screenshot bytes, selected
state/input/action/native epoch, and the actual review submission/report. A
report filename or arbitrary `status: passed` is not sufficient provenance.
Importing a completed review must affect the next planning decision; a log entry
alone is not feedback. Reusing stale content must either be rejected explicitly
or routed to fresh evidence; both are acceptable if it never gets current credit.

The retained coverage denominator is six state×rule cells: label, box, caption
separation for each state. Targeted evidence is useful but is not a full-content
sweep. Native pass cannot substitute for an image judgment, and an image judgment
cannot certify exact dimensions or unsupported computed font/layout properties.

## Fixed cases and oracle

The machine-readable `cases.json` contains ten cases. Each case's required output
is evaluated by `oracle.py` against normalized actual public API evidence. Missing
or nonobservable behavior is a gap, never an inferred pass. Subvariants are
mutation controls inside a case and are reported individually.

1. **Review routing:** valid current target/full evidence, five native/past-review
   passes, one missing qualitative judgment. Queue precisely that image-review
   task; no SDK call and no completion claim.
2. **Import actual review:** import a valid `actual:false` separation observation
   on `reverse`; preserve one visual failure at `reverse/caption-clear`, no
   invented native failure, then plan that scope. A subsequent `actual:true`
   bound review clears that queued visual task and affects the next plan.
3. **Queued completion:** two independent queued visual tasks complete in reverse
   order. One completion leaves the other pending; both permit completion only
   with all required full coverage. No SDK reacquisition is caused merely by
   finishing review. Missing/unknown decisions remain pending.
4. **Stale binding:** separately change source bytes, input hash, original PNG
   bytes, or native state/action binding after a good review. Never grant current
   pass credit from it; retain original artifacts and request/reject fresh work.
5. **Report integrity:** duplicate decision, unknown ID, injected expected/unit/
   status, altered catalog/observation digest, changed bound rationale, missing
   report binding, and wrong state screenshot are rejected before coverage credit.
   These are report errors, not product bugs. Preserve every rejected original.
6. **Targeted→full:** after repairing `reverse/caption-clear`, retain the complete
   six-cell denominator and related `reverse/sample-box` regression obligation.
   Passing targeted frames never mark full content complete. Schedule the missing
   full native sweep, then its image work, and finish only after both states and
   the queue are complete. No unrelated state gains detection credit.
7. **Strict metrology:** exact direct iOS CGRect extent 66×44 at a large origin and
   Android integer pixel extent 165×110 at density2.5 pass the unchanged design.
   Preserve misleading rounded endpoint bounds; no snapping or global epsilon.
   Direct width65.75 and Android width164px fail. Relations require both unique
   fully visible boxes in the same coherent frame; malformed packets or an
   explicitly selected native packet with missing samples stay unknown and may
   not fall back to convenient rounded bounds. Legacy observations without native
   packets retain strict legacy evaluation and gain no precision credit.
8. **Calibration classification:** direct provider width65.99999999999999 remains
   a strict failed measurement; conflicting 65.99999999999999/66.00000000000001
   stays unknown. Calibration is a bounded infrastructure/observation task that
   preserves these originals, approved threshold66 and tolerance0. A stable repeat
   with66 may establish new evidence; it does not rewrite history. Stable65.75 is
   still a real measured violation. A failed measurement is not automatically a
   confirmed product defect.
9. **Mixed methods and genuine counterexamples:** a wrong label `Back` in
   `reverse`, undersized native box65.75, and caption overlap in the original PNG
   produce three distinct failed cells with their actual methods and state scope.
   A computed-font/layout-box request without native support remains unknown;
   visual approval must not turn it into numeric pass. Same-cause clustering may
   reduce repair count but cannot erase cells or mint independent detections.
10. **Bounded retry and honest completion:** fail image review or acquisition
    repeatedly using distinguishable saved attempts. Stop after two retry
    transitions beyond the original attempt (at most three attempts total per
    work item); report unresolved cells and preserve evidence. Stable bad geometry
    does not authorize threshold edits, infinite SDK runs, empty queue completion,
    or changed baselines. Completion is barred while any required U/F or full
    coverage debt remains.

## Execution and disclosure

After sealing, exercise only public controller entry points. A synthetic
transport may write exact reproducible observation/image/report envelopes to
exercise scheduling, invalidation, import, and retries. Disclose all synthetic
inputs in the result; it is not native runtime validation. Do not patch live core
or weaken oracle assertions to make an API fit. If a fixture schema adaptation
is needed, keep it in this directory with a recorded reason and do not modify
the sealed spec or original failure.

Actual SDK calibration is a separate stage: execute the neutral known-size box,
large-origin/scroll case, true undersize control, and conflicting repeat on each
available real native provider. Pin source and environment, preserve actual raw
packets/screenshots, verify provider identity and test execution, report observed
cost, and compare unmodified66/44/12 thresholds. Do not claim this stage passed
from synthetic transport. If an SDK/provider is unavailable, mark that stage
unexecuted and state the exact missing prerequisite.

## Seal

`seal.json` records SHA256 for this file, `fixture.json`, `cases.json`, `oracle.py`,
fixture source and original PNGs. The seal is created before controller inspection.
Later runners and raw outcomes are new files outside the seal. Never reseal the
specification after observing implementation behavior.
