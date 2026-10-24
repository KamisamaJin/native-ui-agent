# Independent neutral forward test

Prepared from `../development/candidate-attempt-1/SKILL.md` and its relevant reference/compiler files, plus the pinned `native-ui-agent/assets/ios-observer` host interfaces. No prior validation study, live root tool edit, SDK execution, device operation, web source, or product screenshot was consulted.

`source/Bridge.swift` is a self-contained SwiftUI component and the required `ObserverBridge.make` entry point. It has ten neutral reading-note cards, a real review action, and a retained local review count. The ordinary layout is intended to occupy approximately four to five 600 pt viewports. Actual native height and readability remain to be measured.

`design/PREIMPLEMENTATION.json` records the complete design, rules, routes, actions, bindings, and fixtures before the Swift file existed. `design/reference.json` supplies every expectation. The final `design/contract.json` only adds exact source records for that reference and the launch approvals. `APPROVAL.json` separately pins the canonical design-lock/routes digests and exact bridge/fixture identity. The tester context is independent of the Skill optimizer and earlier studies; it authored the design and component sequentially, so it is not a separate second visual oracle.

Both `ordinary400` (offered width 400 pt, Dynamic Type large) and `narrow280-large` (280 pt, xxxLarge) use the same component and business inputs. The pinned host subtracts 32 pt horizontal padding, giving intended child widths 368 and 248 pt. Actual viewport geometry must confirm this.

Four explicit checkpoints are fixed:

| State | Input | Checkpoint action | Coverage |
| --- | --- | --- | --- |
| ready | A, review count 0 | sweep 0 | full content |
| reviewed | A, review count 1 | real tap 1 | named targets |
| replaced | B, review count remains 1 | sweep 3 after caller replacement 2 | full content |
| disabled | B, review count remains 1 | disabled action observation 4 | named targets |

Every state requires the top input labels, review count, action control facts, first/middle/last anchors, and footer. The two full states additionally require full-layout and wrapping judgments. Both callback checks preserve exact original stimulus indices: tap 1 must emit `notes.reviewed.A`; caller replacement 2 must be quiet after successful same-instance input advancement. Disabled action 4 is expected to be blocked with no dispatch. A zero interval there is recorded as a literal fact and is never callback-behavior success.

The snapshot tools generated the design plans, obligation audits, and both strategies' manifests under `generated/<case>/`. Each plan has 66 required assertions, 76 matrix cells, and 12 manual visual assertions. Both strategies retain identical required states, targets, actions, callbacks, source identity and launch inputs. Only their observation strategy and resulting manifest digest differ. `logs/prelaunch-verification.json` records exact reconstruction, equality, source-before-design checks, host-interface equality, and six rejected tamper controls. These are Python checks only.

`launch-requests.json` contains ready argument arrays for the parent-owned simulator and fresh capture directories. The parent may execute only after checking `SEAL.json`. Use a changed source or input as a new revision with a new approval and seal; retain this attempt. Native capture output belongs under `captures/`, outside `source/`. Native compilation, runtime environment, real dispatch, current-state geometry, actual scroll overlap, control height, rendered appearance, and all 12 manual rows remain unassessed until captures arrive.

`oracle.json` is the independently fixed completion-pass checklist. `USABILITY.json` distinguishes an operator path mistake from actual Skill behavior. `SEAL.json` binds every prepared file and the consumed snapshot tools/interfaces. No pass/fail benchmark outcome is anticipated.
