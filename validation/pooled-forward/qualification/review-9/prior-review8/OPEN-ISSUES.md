# Open shared findings

SC13 — Unsupported native-query formats earn completeness

A non-enumerated arbitrary iOS group resolution with count1 earns local unique P. An Android singleton containing only provider string/node IDs (without emitted native geometry schema) also earns local unique P.

Expected: A reported singleton or provider label cannot establish an actually complete native matching query.

SC14 — Cyclic native parent graphs count as complete trees

Disconnected parent cycles pass native_query_complete in both platforms and grant local uniqueness P.

Expected: An impossible disconnected/cyclic structure is not a complete actual native tree.

SC15 — Repeated records of one identity become a duplicate counterexample

The same native index/node_id repeated twice is treated as two actual matching entities: unique:true F and unique:false P.

Expected: Distinct actual entity evidence is required; one-vs-two unresolved/malformed identity retains U.

SC16 — Query header hides contradictory original native matches

A valid full original native tree has a visible target, but group header missing/count0 overrides it and grants present:false P.

Expected: Contradictory bound original native evidence cannot be erased by a count header; no absence P. Original test expects U; a genuine-presence interpretation could instead refute the negative. Either way the observed P is wrong.

SC17 — Complete local empty query cannot decide local negatives

Actual complete local zero-result native queries stay U for present:false/unique:false because state.complete=false, even though no full-state claim is made.

Expected: The sealed D/cardinality table decides zero matches in a complete local native domain as False; retain full-state complete:false and bounded scope.

Original malformed/incorrect test expectations are preserved separately in raw/harness-and-expectation-adjudications.json. No old F was overwritten. Operator issues are separate under operator-review.
