# Pre-source grading implementation

This implementation follows EVALUATOR.md and consumes observations after both anonymous corpora for the named stage are supplied. It does not inspect product source automatically, infer runtime styles from code, dispatch actions, or implement a new gate. No actual business source or observation was available while this code and its synthetic controls were written.

Files: grade.py grades normalized records; normalize.py is a conservative optional thin adapter around the immutable native helper's public delivered API; compare.py computes fixed-row repairs and format-neutral adjudicated review matching. Source/screenshot review and transition synthesis are explicit evaluator work, not invented automatic passes. Missing or unsupported records default U. Keep all raw inputs, mappings, receipt fields, frames and screenshots beside normalized records.

## Raw adapter

The immutable helper is imported by path without reading its source. Its API is resolve(snapshot, {'identifier': exactID}, platform), state_evidence(observation,stateSpec), callback_verdict(copiedStep,canonicalExpectedEvents,platform,stimulus=...). No product expectation is sent to the native host. JSON object callback keys are canonicalized in copies only; raw receipts are retained unchanged. Integers, booleans, arrays, counts, payload membership and native interval bounds retain their semantics.

A per-case mapping.json is keyed by logical stateID and includes input_index, state_action_index, state_id, trigger_action_index. For automatic callback normalization it additionally supplies trigger_step_pointer, an explicit absolute JSON pointer such as /steps/3. The adapter never guesses the index base or raw step container. Missing pointer leaves behavior U. Root may add this pointer as a mapping field; it changes no action or expectation. Initial states need no trigger pointer.

Run normalize.py with --helper /absolute/frozen/scripts/native_checks.py --observation raw.json --mapping mapping.json --platform ios|android --case P1 --anonymous-id A --stage D0 --out records.json. Repeat over supplied platform/case evidence and combine records under one stage/anonymousID while retaining all rawEvidence references. Native snapshot references retain the state_evidence snapshot index, exact identifier and binding context. The helper establishes frame epoch/scope; native facts do not require prior activation. The adapter does not synthesize missing snapshot bindings.

Current text, name, booleans, native font_sp/font_weight/color_argb, semantic bounds and bounded absence are normalized only when exact native semantics are unique and intersect the viewport. Text resolution no_native_control is valid for current text; actual control requirements remain with native attributes and callback helper. The adapter conservatively records absence only after completed full-content coverage, and only declares completeCoverage after checking independent required exact target membership and collapsed target absence. Additional genuine bounded non-full absence evidence can be entered explicitly by the evaluator under the frozen policy.

For native measured text on control containers, only a real unique descendant with matching native_text and node_id/parent_id ancestry can supply TextLayout fields. The candidate nodes and ancestry path remain in normalized/output provenance; multiple candidates stay U. Nearby rectangles are never used to guess a descendant.

The adapter cannot establish arbitrary padding/radii/fills or physical hit regions from TextLayout/semantics. It leaves them U. It leaves resulting transition vectors U for explicit evaluator synthesis from actual native facts plus successful stimulus/input binding; callback payloads are never used to fabricate resulting state. It leaves screenshot and source review U until actual review records exist.

## Normalized records

NORMALIZATION.schema.json fixes the base envelope. Additive measurement fields used by the implementation are unit, uncertainty, nativeProperty (textColor or fill), and capability (genuineOSPhysicalHitRegion only for a real separate physical inspector). A numeric actual may instead be {"value":14,"unit":"sp","uncertainty":0}. The original declared uncertainty/units remain visible in output. Bounds dimensions formed from native edge coordinates default to uncertainty2 logical units; direct native scalar exports default0. These are the pre-source policy values.

Every runtime record carries context platform/caseID/stateID/processID/inputRevision/eventRevision/mappingRef. These bind facts to current state; successful action is required only for the separate stimulus behavior records. Manual screenshot records use evidenceKind manual.screenshot plus reviewVerdict pass/fail/unknown and reviewReason referencing inspected actual native frames. Source records use manual.source; input checks use input.integrity. Source/input context has matching platform/caseID/stateID but needs no fabricated native process. They never affect runtime coverage.

For callbacks use the immutable helper's verdict mapped passed/failed/unassessed -> pass/fail/unknown. A gate passes only when stimulus_established is true. Preserve immediate interval/provenance. Native events are decoded JSON envelopes, retaining typed integers. Gate targetID is the actual exact requested identifier, attempts1 is established by the one-step successful native receipt, and intervalComplete requires the immutable helper's assessed immediate interval. Do not set those fields from expected values. Gate failure or unknown leaves callbacks/transitions U.

## Grading and simultaneous stages

The preferred grade invocation is --batch batch.json --out grade-batch.json, where batch.json has stage and exactly two corpora with distinct anonymousID and normalizedEvidence paths. Both must explicitly be supplied for the same stage. Source/screenshot/manual records are added under the same evidence schema before grading, retaining all conflicting entries. The --evidence option supports internal single-corpus recomputation after the batch is available; it does not authorize receiving stages out of order.

All oracle cells remain output, including 896 explicit N/A cells. No record means U. Conflicting same-cell records remain U rather than last-write-wins. Rows include raw references, original actuals, gate, interval/epsilon and comparison reasons. Summary panels separate each class, platform, public/holdout case and checkpoint. The fixed design denominator is not recompiled from observations.

## Review and repair matching

compare.py --d0 D0.json --final FINAL.json [--review claims.json] --out comparison.json requires the same anonymous source and complete fixed row sets. It retains every original natural runtime F row and its FINAL P/F/U, plus every status change elsewhere. Zero natural F means repair/detection shares null (N/A).

Review normalization is manual and format-neutral. claims.json contains claims with unique claimID, original text/rawRefs, origin manual|typed, scope runtime|source|input, and matches [{cellID,adjudication:exact|partial|uncertain|false,reason}]. Empty matches retain an unmapped claim. A typed claim additionally needs typedCheckEstablished:true and typedNativeReportRefs to the actual delivered failed native check. A v4 failed check row is eligible under this same rule without any machine_findings field; planned checks are not eligible. Source-only claims remain in a separate scope and cannot inflate natural runtime detection.

Output retains all claims, uncertain/unmapped and duplicate content, manual detection, actual typed detection, exclusive/overlap and combined detection. False-alarm reporting is conditional false-discovery share among adjudicable claims, accompanied by counts, by-scope panels and an interval assigning all uncertain/unmapped claims each way. No complete TN universe is asserted, so classicalFPR stays null. An evaluator's exact native F-row match establishes detection; a shared cause repair does not establish a missing finding retroactively.

## Synthetic controls before source delivery

37 synthetic controls cover current labels after unavailable activation, gated zero-event/no-op evidence, interval incompleteness, bounded absence, uncertainty, conflict retention, source/style separation, typed JSON integers, color-property separation, screenshot review, copied callback canonicalization, explicit index mapping, zero natural-F denominators, v4 failed-row eligibility without machine_findings, planned-check exclusion and unmapped/false claim retention. They use no business implementation, old trial or native result.

The source identity requirement concerns the common caller/bridge/host. Component-owned remember(modelID), onChange handling, and internally keyed reset subtrees are legitimate complete-replacement implementations; an external host must not recreate the production component to supply replacement behavior. This is an explicit interpretation of the unchanged public API, fixed before source delivery.

Semantic bounds are measured only when the native control/semantic node is fully visible (Android fully_visible; iOS fully_within_viewport), so viewport clipping during a scroll is not misreported as a too-small underlying control. Partially intersecting nodes may still establish exact current text or attributes. All original native bounds remain in raw evidence.

Unavailable measurements in one frame remain retained as unresolved provenance and do not erase a valid same-input/process/event native value in another frame. Equal values may union different actual native node paths, retaining each occurrence. Conflicting actual values or different binding contexts remain U.

Pre-source schema audit corrected immediate_after/after as integer snapshot indices: callback context uses the receipt binding_after directly. The selected-state normalizer recognizes native checked/on values and documented Selected/Not selected alternatives instead of treating a default selected=false as authoritative off. Contradictory explicit native values remain U with candidate provenance. These are common evaluator corrections, not observer benefits.


## Grader-v2 actual receipt provenance correction

The exact grader-v1 files and seal are preserved at history/grader-v1. PRE-DELIVERY-GATE-AUDIT.json records the pre-delivery static audit; no source/raw business result was supplied. No fixed design/acceptance or native helper changed.

Each mapping row must now additionally provide trigger_state_id from the actual native actions JSON. A requested tap may be stateID.trigger while its subsequent sweep is stateID. The actual raw step.state_id must equal that mapped trigger identity, and binding_after.fixture_index must equal mapping.input_index. The actual identifier is read only from iOS step.action.target.identifier or step.action.identifier, or Android step.selector.identifier. It remains gate.targetID even when wrong; the oracle is only a comparison operand. Missing or conflicting actual selector proof stays U. Actual selector candidates, raw action state, method and native bindings remain in gate provenance with original references.

Caller updates ignore target identity and require actual dispatch.method caller_fixture_update plus an actual native fixture-index advance to the mapped input. They keep replacementApplied gate kind. All callback intervals still use the immutable helper's immediate interval. Later missing/drifted full-content or target viewport collection never invalidates an otherwise established immediate callback. Invalid pointers and helper/acquisition exceptions are explicit adapter diagnostics.

ATTRIBUTION.md fixes a separate narrative overlay for execution gaps, observer/session failures, confirmed exercised business defects, direct current-fact contradictions and possible downstream prerequisite scope. It never changes literal grades, denominators or retroactive detection/repair credit.


## Grader-v3 Android semantic-bound field correction

Exact grader-v2 bytes/seal are retained at history/grader-v2. Android semanticBounds width/height now come from the unique actual native control.unclipped_bounds_dp rectangle, not expanded touch_bounds_dp or helper touch_width/height. Normalized and graded provenance retains nativeProperty, measurementSourcePath, control node path and both raw native rectangles. Frozen dimension uncertainty2 dp and all minimum thresholds are unchanged. iOS actual AX geometry and physicalHit U obligations are unchanged. PRE-DELIVERY-MEASUREMENT-AUDIT.json records this common interpretation correction. MEASUREMENT-SENSITIVITY-PLAN.md freezes a v2/v3 replay on both anonymous corpora with the same raw evidence, oracle and immutable helper, preserving original v2 scores and every changed cell separately from treatment comparisons.
