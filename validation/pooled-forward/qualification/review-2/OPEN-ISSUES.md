One confirmed blocker remains in frozen candidate-v13.1. Evidence is HOST/SIMULATED; no native or performance claim is made.

**B04 — pending repair context can change after failed default recheck.** Start source `Broken`, expected `Ready`; default emits original F/task. Change actual source to `StillBroken`; default measures the patch and records `patched_needs_native_retest`, then the simulated collector errors. The task field is now cleared while completion remains pending. Change the oracle to `StillBroken` in the same workflow, invoke ordinary default continuation, then ordinary finalization: it returns `accepted`. The original `Ready` obligations never received successful original-context evidence or independent new-scope admission. A pending bridge-context change also accepts.

Concrete commands and retained identities: `raw/pending-context-oracle-repro.json`, `raw/pending-context-bridge-repro.json`, the referenced raw command files, and `work/new-pending-context-oracle/pending-native-handoff-external-pin.json`. New rows N05/N06 retain both first failures.

Direct open-task context changes reject, and valid default-generated measured completion passes. The gap is after source-edit action closure while native behavior remains unresolved.

The original 47 rows are byte-identical checks with exact before/after outcomes retained: 36 P / 11 F became 42 P / 5 F. The five remaining raw failures are documented expectation/probe assumptions and an unchanged host-clock fact, assessed separately. New controls: 9 P / 2 F. None of these counts is a native PFU score or speed sample.
