# Neutral folded-paper guide benchmark

This small component measures repeated observation overhead. It is not a business quality experiment and contains no deliberately introduced defects. The source and all requirements below are fixed before any native SDK run.

The host offers a 360pt by 600pt LTR light viewport with standard large Dynamic Type. Its horizontal host padding leaves 328pt for this 314pt-tall guide. Content must fit without scrolling. The guide shows “Fold guide”, a paper diagram, an instruction, a status and a “Mark crease” action. The diagram has an actual native accessibility boundary of 180×100pt. The action has a 44pt native accessibility height. These are AX facts, not claims about physical hit regions or internal padding.

Three required states use one uninterrupted native process:

| State | Stimulus | Instruction | Status | Action enabled | Callback |
|---|---|---|---|---|---|
| overview | Initial checkpoint | Fold the front sheet along the dashed diagonal. | Sheet ready | true | N/A |
| creased | Tap Mark crease once | Same front instruction | Crease marked | false | Exactly `crease.marked` |
| reversed | Caller replaces front with reverse input | Turn the sheet. Fold along the reverse diagonal. | Reverse side | true | N/A |

Two qualitative aspects are required in every state, independently of the native facts:

1. The visible dashed crease connects upper-left to lower-right in overview/creased, and upper-right to lower-left in reversed. The paper outline stays visible. This is a diagram content proposition judged on original images.
2. The instruction text is visibly clear of the heading, diagram, status and action. This is an overlap proposition; it is not an exact font/padding measurement.

Every state requires full-content image coverage and all native fact cells. No state or qualitative cell may be omitted to claim speed. The exact same source, fixture/action sequence, design lock, binding selectors, review policy and requirement route index must be used by both arms. Each arm must complete review of its original bound images; an old review may not establish changed-source or new-image acceptance. A fresh full final collection remains mandatory before delivery acceptance.

Benchmark order, transport warm/cold conditions, and wall-time boundaries belong in the root experiment protocol before SDK execution. This spec does not prescribe a result or performance target.
