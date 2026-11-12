# Additive pre-run repair-handoff interpretation

This is an interpretation before native/performance samples, independent of
candidate implementation and results. It preserves the original protocol and
amendment files. It addresses H02/H03 wording that described an explicit worker
completion call, while the user's intended capability is tool-driven handoff in
the DEFAULT state machine without relying on remembered optional calls.

An explicit worker CLI request is not an intrinsic requirement. The default
service may itself produce the tool-verifiable source-change handoff receipt from
a pinned open task/capture/context and actual tool-measured production-source
diff. It must then require applicable fresh native retest. The receipt proves
that a source-change handoff was recorded; it does not prove the patch addresses
the cause, the worker's intent, correct behavior, or acceptance.

Minimum raw proof for this equivalent default path is:

1. The real public default-service invocation, ordered trace and original open
   task/request bytes/digest. Pin task ID, work kind/owner, failed rule/state IDs,
   original finding/capture/plan/policy/input identities and source-before maps.
   The service must not reconstruct a convenient foreign task after seeing a diff.
2. Actual filesystem-derived before/after source maps and changed paths, bound
   to the same namespace and real production subject. The before identity comes
   from the retained original capture/task; the after identity is measured from
   current files. Caller-declared hashes/paths or a claimed patch are insufficient.
   An unchanged component or bridge-only edit cannot complete a component-source
   handoff. Unknown impact retains conservative full-retest scope.
3. An append-only tool-produced receipt tied to that measured transition and
   exact task/context. It discloses `default-generated measured source change`
   versus an explicit worker-origin request; it never fabricates a worker call.
   Retain original request, source maps, diff evidence, task transition and actual
   tool response. Repeated inspection is idempotent, not a new repair round.
4. A pending-native-retest disposition preserving the original F/U and affected
   obligation ledger. Diff existence cannot mark all findings repaired or assign
   one ambiguous edit to unrelated open tasks. A task's source-edit action may
   be closed while behavior remains unresolved; the receipt must distinguish them.
5. The next default transition must obtain genuinely fresh applicable native
   evidence for changed code, with actual current source/build/input/app/event
   identities, required callbacks and coverage. An old package cannot pass new
   source. Complete current-code final gates remain mandatory; an eligible new
   full post-repair package can later be finalized under amendment 1.

Under this interpretation, H03 **omitted completion** means that the default path
has no valid tool-verifiable handoff record for the transition, not merely that a
separate worker command was absent. Missing/unpinned/stale/foreign task context,
unchanged source, spoofed diffs, altered expected values, a bridge-only patch for
a component task or an absent/invalid receipt must retain unresolved F/U and
cannot yield a claimed successful handoff or acceptance. A real diff may justify
new diagnostic acquisition without establishing repair correctness. Native
retest failure remains failure; it cannot be overwritten by this receipt.

This clarification changes no expected value, mandatory coverage, P/F/U/U count,
fresh-retest requirement, resource gate or 20% threshold. An automatic tool-driven
receipt meeting the same evidence requirements and an explicit worker-origin
receipt are equivalent for the handoff requirement. Neither is a native pass.
