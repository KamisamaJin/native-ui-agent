# SC18 — complete offscreen singleton native queries remain U

Both arms recognize a valid, complete, bound target-native query with count1, no duplicate and an offscreen entity, yet present:true and local unique:true remain U. The emitted iOS offscreen_not_resolved format and actual Compose semantics format both reproduce it. Two offscreen distinct entities correctly prove presence P.

Expected: For the complete local native matching domain M, count1 establishes present=True and unique=True regardless of viewport intersection. Retain complete:false for full state and visibility=False as a separate raw fact; no activation/hittability/visual claim is earned.

The formal D/M definition and original expectations remain unchanged. Visibility is separate from cardinality; callback, activation, geometry and full-coverage gates earn no additional credit. All10first-failure rows are retained under first-failures and wire-delta. No other confirmed or unresolved issue is declared by this finite review.
