Six common blockers reproduce in both frozen arms. All evidence is HOST/SIMULATED; no product/native F is inferred.

1. **SC01 terminal geometry:** set the last sentinel frame to y=500 outside y=0..96, keep the true containment header. Full/P still granted.
2. **SC02 epoch error:** set original capture stable_binding=false. Pixel fallback still grants full/P.
3. **SC03 duplicate identity:** add an offscreen duplicate leaf ID under a different container. Container lineage rescues its uniqueness.
4. **SC04 fake leaf:** use container/ScrollView-role witness records with no listed children. They supply the required leaf anchors.
5. **SC05 unobserved scope:** content width 128, observed viewport width 64. Strip-only proof becomes satisfied full_content/absence P despite broken closed-state premise.
6. **SC06 image-root diagnosis:** diagnose the same valid strip with a nonempty production root. The source scan overwrites root and falsely marks full_content incomplete; an empty-source control remains complete.

For SC01–SC05, inspect `work/ARM/CASE/{observation,proof,coverage,evaluated}.json` using case names in `review.json`. SC06 has paired controls in `raw/ARM-diagnostic-root-result.json`. `first-failures` preserves both arms.

Native/performance/business work remains closed. The original shared source was not modified.
