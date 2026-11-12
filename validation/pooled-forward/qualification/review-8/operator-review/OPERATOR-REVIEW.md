# Original pinned pre-run operator review

Corrections required before the timed gate. Nine HOST/SIMULATED structural checks record5P/4F against the original saved operator files. This is separate from the frozen skill review.

* OB01: The gate accepts final source-duty rows=[] when blocking_claims=[], yet advertises source denominator1.
* OB02: It accepts negative B durations and a wall inconsistent with positive stage sums/operator cost, reporting impossible reductions.
* OB03: native_envelope records supervisor release failure after child0, performs recovery, then returns0; the original driver treats that as success and original gate ignores command errors.

All replay outputs, resource contexts and recovery calls were deliberately synthetic and non-forwarding. No SDK, native replay, benchmark episode or speed sample ran. The fake RESULT files under probes are validation fixtures, **not permission to start business work**. Later live operator fixes are unassessed.

Explicit A/B paths, initial full-tree identity, declared ABBA order,104-native-row replay, resource finalization flags, aggregate reduction formula and retained raw reason differences were inspected. Controls reject overlap, changed application source, native count discrepancy and final leftovers. See OPERATOR-REVIEW.json, source-pins.json and each probe-result for exact source/command/raw evidence.
