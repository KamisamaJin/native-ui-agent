# Pulse Lab neutral forward specification

This frozen, independently authored specification tests a native UI feedback service. The subject receives approved requirements, native state evidence, and paths to the actual current production source files. It must choose useful actions and continue verification without requiring the caller to supply a state list, transition plan, semantic target, or expected answer.

The app is a small session toy: Start, Step, Pause, Resume, Reset, plus a separate Preview. It has no business workflow. No prior business study or live service implementation was read when creating this specification.

## Inputs and boundaries

- Give the subject `inputs/approved-requirements.json`, one entry from `inputs/cases.json`, the source root it names, and only the referenced native evidence/history.
- Keep `oracle.json` and `harness-world.json` hidden from the subject. The harness owns action effects and capture delivery; its world states are never required caller request fields.
- Source roots contain real SwiftUI production view text, with v1 missing/duplicated identifiers, v2 corrected, and v3 regressing Reset from Paused. Read the named current file from disk; prior observations carry the digest of the source version they witnessed.
- `evidence/observations.json` binds each native tree and screenshot to a capture batch, source digest, and launch. Trees and PNGs are synthetic fixtures, not real simulator captures. They are deliberately sufficient for offline decision testing, and do not establish SDK compilation or real native execution.
- The service may use any equivalent supported operations and reasonable action ordering. No fixture-specific UI automation is expected. An adapter may translate only generic artifact/config formats and native operation transport; it must not make the subject's missing decisions, add passing evidence, or silently manufacture targets.

## Cases

| Case | Condition | Critical decision |
|---|---|---|
| N01 | Complete Idle evidence, no selected states | Derive useful next actions and cover the approved contract. |
| N02 | Step is visible but has no stable native identifier | Diagnose/repair semantics; do not ask the caller to invent a target. |
| N03 | Session and Preview share the same identifier and running label | Recognize ambiguity and preserve the distinction between an executable scoped query and the identifier requirement. |
| N04 | Hierarchy exists; screenshot is missing | Recover visual evidence without inventing a UI defect. |
| N05 | Pause accepted; one pending Running frame precedes settled Paused | Observe bounded settlement and preserve Count through Pause/Resume. |
| N06 | Current production file is v3; complete prior evidence is v2 | Reject stale completion, find the Paused Reset regression, and verify the repaired current build. |
| N07 | v2 repair is built; only a fresh Idle capture exists | Replay relevant coverage across native states. |
| N08 | Complete raw history and current source are both v2 | Deliver a traceable, appropriately limited completion without unnecessary cycles. |
| N09 | Three capture attempts produce no screenshot | Stop at the approved bound and report the exact remaining evidence blocker. |

`oracle.json` defines behavioral assertions. Score exact decisions and evidence rather than wording, a specific JSON schema, or a prescribed call order. A completion claim must satisfy all applicable critical assertions. Record unsupported capability separately from an observed wrong decision; schema rejection alone is not proof of incorrect runtime behavior. The default service interface should nevertheless be assessed for whether a caller can start with the approved requirements, native evidence, and actual sources without designing its verification states.

## Replay and integrity

1. Run each case independently in a disposable workspace and keep raw requests, stdout/stderr, and result artifacts.
2. Preserve source and observation digests. For N06, the actual production root is v3 while supplied captures and prior history remain v2. A repair must affect the production file used for build/relaunch, not a reference copy.
3. Apply `harness-world.json` only as the native transport/world boundary; use the generic view transitions elsewhere. Recheck requirements after meaningful source edits or affected state changes.
4. Use the final-delivery fixture as supplied; its prior history contains raw transitions and captures, not an authoritative pass flag.
5. Verify the freeze with `python3 verify_manifest.py` from this directory. `SHA256SUMS` seals every delivered file except itself. Any later change requires a new explicitly identified specification revision; review outputs belong outside this directory.

Visual inspection performed: the Idle/Running/Paused synthetic contact sheet has legible labels, distinct session/Preview regions, and no overlapping controls. This validates the fixture drawing only.
