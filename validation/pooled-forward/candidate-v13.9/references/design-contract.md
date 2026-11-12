# Independent design and generated assertions

Use this for a new component or a material visual change. A design owner or a
separate context fixes a typed reference before implementation. Give that context
the requirement and approved design inputs; do not supply candidate code,
implementation screenshots or a suspected defect as the answer. Ambiguous prose
still needs design interpretation and review. Hashes cannot certify authorship or
prove that a number captures the designer's intent.

Keep the approval record and canonical lock SHA256 outside the implementation's
editable check plan. In a repository this can be a reviewed design commit or a
sealed experiment record. A changed design is a new revision with a new approval,
not an adjustment to make a test pass. Existing approval remains valid; routine
implementation does not need another permission step.

## Typed reference and contract

See the complete neutral files in [design-example](../assets/design-example/).
`reference.json` contains values such as `{ "value":10, "unit":"dp" }` at
specific JSON Pointers. Each source record in `contract.json` declares its exact
file SHA256. Source paths must stay within the independent design root.

The contract fixes:

- An owner, approval reference, complete rule IDs, logical targets and checks.
- Scenarios, selected states, input/action indices and original stimulus routes.
- Every rule × state cell, with both platforms' source expressions or a reason
  for N/A. No implementation-written per-state expected overrides are accepted.
- Explicit comparison operators. `near` requires a separately sourced tolerance
  in the same native unit. Do not add tolerance to conceal an unexplained error.

Expressions address `source` + `pointer`, or derive `add`, `subtract`, `multiply`
from two source expressions. Addition/subtraction require identical units;
multiplication needs a dimensionless source factor. There are no inline expected
values, implicit pt/dp/sp conversions or executable source expressions. Colors
require `#AARRGGBB`; events are ordered arrays of event strings.

`bindings.json` maps each logical target to one exact native selector. It cannot
contain expected values, operators or exclusions. It also includes logical action
targets. The native action route must match the independently fixed route after
selector substitution. Target resolution still requires unique actual native
nodes; a correct source citation cannot establish a correct runtime binding.

```sh
python3 scripts/design_contract.py seal --contract design/contract.json \
  --root design --output approved-lock.json
# Record the printed canonical digest in the separate approval record.
python3 scripts/design_contract.py compile --lock approved-lock.json \
  --lock-sha256 APPROVED_SHA --scenario public-normal --platform android \
  --bindings bindings.json --actions actions.json --output generated-android
python3 scripts/native_checks.py --plan generated-android/plan.json \
  --observation run/observation.json --platform android \
  --design-lock approved-lock.json --design-sha256 APPROVED_SHA --output checks.json
```

The compiler emits every applicable assertion, exact value/source/unit provenance
and post-action targets. Execution reconstructs the plan from the pinned lock and
rejects altered expectations, precision, state coverage, source claims or routes.
Legacy hand-written plans still run, with `unverified_supplied_expectations` in
their report; do not claim they received the independent source check.

## Style measurement scope

`text_layout` reads actual available native fields, such as Android TextLayout
`font_sp`, `font_weight`, `color_argb`, `lines`, `ellipsized`. Public iOS AX does
not expose generic computed SwiftUI typography/color; those cells remain U.
Visual review is a separate explicitly sourced `manual` assertion. Seeing pixels
does not convert it into an exact native font/color measurement.

`geometry` supports width/height and two-box `gap_x`, `gap_y`, `inset_left`,
`inset_right`, `inset_top`, `inset_bottom`. The target is the measured box; the
reference is the preceding box for gaps or containing box for insets. Choose
`basis:semantic` or `basis:control` explicitly when the distinction matters.
Design rules must declare `measurement:accessibility_box` or `layout_box`, or an
`{ios:..., android:...}` map. Current collectors export public AX/Compose semantic
boxes; `layout_box` remains U on both platforms. A SwiftUI text's AX frame can
be much smaller than its `.frame` allocation. A Compose semantics modifier also
does not independently prove the full layout box intended by a design.
Both unique, fully visible boxes must occur in the same coherent native frame.
These are observed edge distances in iOS pt or Android dp. They are not a proof
of a framework's effective padding attribute, text glyph ink bounds or OS touch
area. No cross-viewport subtraction is allowed.

The collector schedules nearby unseen native boxes first and reuses each original
viewport for all applicable targets. It preserves the original immediate callback
interval, the global scroll budget and unavailable targets. Navigation estimates
never become assertion facts; only subsequently captured native frames count.

## Report the remaining gaps

Separate source rejection before acquisition, incorrect target binding, native
style contradiction, visual judgment and unavailable measurement. Include all
required U/N/A cells and the approved digest. An independently wrong typed design
can still generate consistently wrong code and tests; only the independent design
review and separate acceptance oracle address that remaining semantic risk.
