# Procedural isolation and scope

Research participants receive fresh scoped contexts and are instructed to read only
their assigned artifacts. They share a local filesystem with the orchestrator;
this is procedural assessor isolation, not a security sandbox. Parent orchestration
can see all assignments and reports. Root implements common infrastructure;
independent design/build/review/repair contexts are used only where isolation is
necessary for the explicitly requested blind test and Skill forward validation.

New cases use real production component files in pinned Reply and AlertToast
checkouts. Thin immutable test bridges call the approved public APIs. Test hosts
provide fixed caller inputs and collect actual native semantics, activation,
callback receipts and PNGs. Paparazzi is an Android JVM renderer, not a physical
Android device. iOS runs XCTest on an owned Simulator. No claim of physical device
or universal computed SwiftUI-style access is made.

Only neutral engineering cases can change tools before release freeze. A discovered
business-run collector/contract failure remains in the primary experiment. Any
necessary later infrastructure recheck must be separately labelled, use frozen
source and equal coverage, and cannot overwrite original metrics or failures.

No intentional component bug injection, hidden-result-driven repair, task replacement
based on observed defects, post-hoc expected/unit changes, missing-evidence pass,
third-judge override or source-label reveal before required seals is authorized.
