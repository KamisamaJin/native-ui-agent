# Additive SDK accounting clarification

Clarification ID: `sdk-accounting-1`.

This interpretation is fixed before any timed episode or business design. No
implementation, result/timing, repair or business material was inspected for it.
No actual performance/episode timing is known. It uses the stated user requirement
and already sealed protocol wording; it performs no SDK operation or regrade.

The user's primary requirement is no redundant native collection, with at least
20% lower inclusive collection wall time under the same code, coverage, native
P/F/U and mandatory-U conditions. That does not require avoiding SDK utilities
needed to validate runtime identity or retire owned resources. Original C01/R0
wording saying "no SDK command" is a narrower literal control and remains intact.

## Three operation classes

Classify actual effects and arguments, including indirect work, rather than
classifying solely by executable name or a controller's label.

| Class | Work and examples | Reuse claim |
| --- | --- | --- |
| A — native acquisition/build/test/export | Build or rebuild native artifacts; launch/run the target observer/App/test; render, act, scroll, query fresh App/UI hierarchy or geometry, capture screenshots, or run native capture/export work. A cache hit or `test-without-building` still does native work. Direct framework/API acquisition counts even without a shell SDK command. | These are not zero-new-collection work. A new acquisition must retain its actual fresh evidence and identity. |
| B — runtime/host identity and validation | Read-only installed-runtime/device/toolchain inventory, SDK/version/path queries, current source/dependency/package identity checks and host metadata verification. `simctl list` can be B. | Permitted during eligible original-package reuse; report actual calls and cost. A query of fresh component/App/UI facts belongs to A, even if read-only. |
| C — owned-resource lifecycle | Native resource admission, create/boot where actually needed, reconciliation, process/device shutdown, deletion and finalization. `simctl shutdown/delete` can be C. | Permitted lifecycle work; report actual calls, ownership, effects, errors and full cost. Target App/test launch or evidence acquisition cannot be hidden in C. |

An invocation may have several effects; retain all relevant events and classify
them honestly. Ordinary checks, package reconstruction, source/image hashing,
routing and durable journaling remain charged under the original timing rules.
Calling a utility a metadata query does not make a build, test, export or new UI
measurement disappear. Conversely, the word `simctl` alone does not prove that
new component evidence was collected.

## Primary interpretation and literal control

For unchanged, otherwise eligible original-package reuse or ordinary finalization,
the primary no-redundant-collection condition may use **zero class-A work**, while
classes B/C and all ordinary verification remain visible and charged. Original
packet bytes, capture purpose/age, source/input/state/event identities and review
bindings stay original; metadata queries do not freshen the native packet.

Maintain a separate literal SDK-utility invocation count and the original
"zero SDK commands" control. An observed metadata/lifecycle SDK invocation is a
counterexample to that literal control, even when zero-new-collection is true.
Incomplete command evidence leaves the literal control U. Do not retrospectively
mark any old literal control P, overwrite an F/U, or pretend there were no SDK
commands. No old command trace or verdict is inspected or assigned a new status
here. An effect-based zero-new-collection claim also needs complete evidence;
zero logged utility commands alone does not establish it.

| Established facts for an eligible reuse transition | Primary zero-new-collection fact | Old literal zero-SDK control |
| --- | --- | --- |
| A=0; at least one observed SDK B/C invocation | Can be true, subject to every required validity/closure gate | False |
| A=0; no SDK invocation, with complete operation evidence | Can be true, subject to every required validity/closure gate | Can be true only from that complete literal evidence |
| Any actual A work | Not zero-new-collection; disclose the actual work | Evaluate the actual SDK invocation evidence separately |
| Missing operation evidence | U; do not assume zero | U |

Explicit force-fresh collection remains a different request and must perform real
fresh native acquisition. Ineligible/stale evidence may require fresh collection
or remain blocked. This clarification does not turn necessary native reacquisition
into a reuse pass, or make zero A sufficient to establish valid source/environment.

## Wall-time accounting and unchanged gates

Every actual machine-collection wall includes A, B and C, including runtime/host
queries, lock/admission waits, validation, failed attempts and owned retirement.
End timing only after required durable resource closure. Do not subtract B/C,
hide cleanup in a later process, or claim an SDK-free path because only A was
zero. Use the original enclosing/union timeline; do not double-count nested
intervals by adding overlapping category durations. Original separately declared
human/model/queue accounting remains unchanged and visible.

The primary interpretation is therefore allowed to qualify zero NEW COLLECTION
with metadata/lifecycle work charged. It does not erase a failed or unknown old
literal control. Report these as distinct claims, with actual operation counts,
categories, original package identity and inclusive wall time. Native requirement
judgments remain the fixed 104-rule, five-state comparison; SDK counts are actual
execution/resource observables and the literal control is separately retained.

All four episodes and the original AB/BA order, cold/warm accounting, same-code/
same-coverage rules, exact native P/F/U comparison, no increased mandatory U,
20% formula/threshold, budgets and retirement costs remain fixed. No expected
native value, fixture, state, action, tolerance, original record or timing data
changes. No timing outcome is available to motivate this clarification.

Failed native execution, source/bridge/plan identity, current runtime/environment,
required review, native safety/coverage, resource ownership or retirement proof
still blocks its required gate. A failed B/C command is retained and charged;
zero new collection does not excuse missing proof. This accounting interpretation
grants no permission to skip or ignore those requirements and authorizes no new
operation beyond the existing task/resource contract.
