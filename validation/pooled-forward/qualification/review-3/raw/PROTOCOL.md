# Sealed forward qualification protocol

Protocol ID: `pooled-native-qualification-1`.

This is a pre-implementation requirements protocol, not a result. Its author has
read only the skill entry point, the current interface references listed in
`sources.json`, and the skill-creator instructions. The author has not read
validation cases, historical product results, implementation scripts, tests, or
the implementing agent's conclusions. No SDK command, build, device acquisition,
or product task has been run for this protocol.

The qualification question is whether the DEFAULT execution service can retain a
bounded owned iOS device pool, invalidate evidence at the correct platform and
dependency boundary, reuse a still-valid native capture package, and give a
repair worker a tool-verifiable handoff, while preserving native evidence and
delivery gates. The performance gate remains at least **20% less collection
wall time**, with the same code, mandatory coverage and P/F/U judgments and no
increase in mandatory U. No new business blind task belongs to this protocol.

## Evidence classes and limits

Use these labels on every qualification result:

* **NATIVE**: original commands actually executed against the selected SDK, with
  raw SDK output, native test result, images, hierarchy and runtime identities.
  This can establish only the native facts those artifacts demonstrate.
* **HOST**: actual filesystem, process, lock, timing and controller execution on
  the qualification host. A real lock race or preserved directory can be HOST
  evidence without being a native UI fact.
* **SIMULATED**: a controlled clock, inventory, command failure, broken receipt,
  dependency change or repair-worker response supplied to test the protocol.
  This can establish a decision under supplied inputs; it cannot establish
  device creation, native app freshness, taps, rendering, real deletion or SDK
  compatibility. Simulated command logs must never be presented as native logs.
* **DOCUMENTED**: an interface promise from the sources. It is a requirement to
  qualify, not an independently demonstrated capability.

The current references document fresh app/input/image evidence for each native
capture even when compiled artifacts are reused; per-state input/process/event
binding; separate target and full-content coverage; original callback intervals;
actual environment checks; source-bound full final capture; append-only review
binding; owned-resource retirement; and tool queues that do not themselves edit
source. They do not independently prove that any of those promises hold on this
host. In particular, no real device-pool reuse/expiry, cross-platform dependency
closure, repair completion, native run or speed improvement is evidenced here.

Do not describe SwiftUI AX geometry as generic computed font/padding/color, a
Paparazzi semantic action as physical Android touch, a host shell as the real
application's navigation/lifecycle, or a changed-root digest as a complete compiler
dependency proof. A hash proves byte identity, not correct interpretation or
independent authorship. Unsupported aspects remain U.

## Freeze and admission

Before any run, an independent operator binds this seal to an immutable run
manifest containing:

1. Baseline A and candidate B source/archive digests, public invocation and
   toolchain versions. A is the last default service before these changes; B
   uses the default service with the changes. Application, generic fixture,
   bridge, approved rules, tolerances, mandatory-ID set, environment, actions,
   review policy, resource policy and selected native coverage are byte-identical
   between corresponding A/B steps. No special bypass entry point is allowed.
2. An owner-approved platform dependency ledger: each production file/resource,
   bridge, fixture, template, package/lock/build option and environment input is
   assigned to iOS, Android, shared, or irrelevant, with the reason and resolved
   path namespace. Unknown relevant dependencies are explicitly unknown.
3. Exact installed iOS device type/runtime and toolchain selection; Android
   project/JVM/SDK facts if Android native qualification is available. Record
   hardware, OS, free space, private/shared cache state and background contention.
4. A complete native capability harness and its independent oracle. It contains
   only ordinary native text, an actionable button, tall content and a bottom
   target, plus caller replacement. It has no business behavior. It calls the
   real native controls/semantics of the selected platform and does not replace
   any product component used outside this qualification.
5. Every expected obligation/state/aspect, including deliberate protocol
   negative cases and any independently unsupported aspect. No row, font,
   content length, viewport, callback requirement or sampling limit can change
   after the first result to improve the score or time.

The protocol is frozen now. Concrete workload bytes may be bound later only if
they satisfy these admission rules and are sealed before either arm runs. The
operator must reject a late binding chosen from candidate performance or prior
product judgments. If existing immutable code/coverage is the user's comparison
workload, the operator may bind its digests without revealing its historical
results to this author. Creating a new business task is not an alternative.

## Mandatory raw record

Keep every original file in a fresh evidence directory. Never overwrite a prior
package. Every scenario cites the relevant records below, not just a summary flag.

| Record | Required raw observables |
| --- | --- |
| R1 Invocation | exact public command/arguments, environment selection without secrets, start/end monotonic times, wall-clock times, exit status, stdout/stderr, default-service task/cycle transitions and error chain |
| R2 Resource | raw inventory before/after, owner/root and generation, acquisition/lease identity, device UUID/type/runtime, create/boot/reuse/release/retire requests and actual replies, active/idle/expiry times and clock basis, cap/byte/free-space policy, lock contention, sampled resource sizes, cleanup errors/leftovers |
| R3 Build | actual source/dependency namespace and file-byte digests, bridge/template/input/SDK/toolchain/build-option identity, compile-cache lookup and validation, retained artifact digests, actual build commands/results and build/test/export timing |
| R4 Native session | actual test name/count/failures from native reports, device identity, test/session and fresh app-instance identity, process lifetime, fixture index/hash, action/checkpoint/state identity, event start/end/delta, successful dispatch/method/activation target, actual environment and geometry |
| R5 Capture | original manifest, observation, full native result/logs, hierarchy and screenshot bytes/hashes/dimensions, immediate and located frames, state-to-snapshot map, overlapping scroll intervals, native top/bottom/sentinel evidence, per-target availability and torn-frame diagnostics |
| R6 Evaluation | original approved plan/required IDs/source policy, rebuilt execution and coverage identities, automatic raw report, bound original visual/source actuals, all rule/state/aspect dispositions including N/A rationale, independent image observations and disagreements |
| R7 Reuse/dependency | previous package digest retained outside the package, validation inputs and decision/reason, the exact original bytes referenced, dependency before/after maps and measured changed paths, explicit invalidation scope, actual SDK-call count including zero, current source/env/coverage gate result |
| R8 Handoff | emitted task/request bytes and digest, supported failing IDs and cited raw frames/source, task/source/plan/capture identity, worker's actual tool request/response, actual measured source diff, completion/rejection receipt, next default transitions and fresh recheck/final package |
| R9 Timing | enclosing machine timeline, stage intervals with inclusivity, reviewer/model/queue intervals separately, all failed attempts and retries, admission/validation/boot/build/test/export/check/reuse/journal/final retirement intervals; no sum of nested times |

If a public interface cannot expose a required fact, record the fact as unavailable.
Do not reconstruct an alleged native action, deletion or process freshness from a
controller's desired state. A PID alone can be recycled; establish fresh app
identity using a native session/launch-instance receipt as well as process times.

## Identity and verdict oracle

Keep the original output status and reason verbatim beside the comparison status:
P = demonstrated pass; F = demonstrated violation; U = needs review/reference,
not executed, unavailable, blocked, environment/receipt error or otherwise missing
proof. A broken protocol is never a product F. N/A stays a separate approved row.
Never drop U or N/A from the denominator or rewrite an upstream blocked callback
as a successful zero-callback assertion.

Compare by the immutable identity `(platform, workload epoch, obligation,
requirement/rule, state, aspect, method)` and the approved source/input/action/
environment/coverage identities for that epoch. Corresponding A/B device UUIDs,
timestamps and fresh app-instance IDs may differ and must remain in raw evidence;
they are not interchangeable identities inside an individual capture. Report
every missing, added, duplicated or changed raw status/reason as a discrepancy,
even if aggregate P/F/U counts match. All mandatory P/F/U rows must be identical
between A and B. This is stronger than merely comparing the number of U rows.
Review disagreement remains visible and cannot be settled by last-wins or majority
votes introduced for this benchmark.

## Device lifecycle scenarios

The observation requirements apply to the externally visible default path. These
are independent outcomes, not prescriptions for internal data structures.

| ID | Challenge and required outcome | Minimum raw proof and limit |
| --- | --- | --- |
| L01 positive reuse/freshness | Two sequential compatible feedback captures under one owner may use the same live managed device, while each capture launches a fresh app/test session with exact new inputs, empty starting callback interval and new images. A caller replacement within one capture must retain that capture's app instance. | R1–R5; actual create count, UUID inventory and native session identities. NATIVE is required to claim pool reuse and fresh native execution; a fake device UUID is insufficient. |
| L02 incompatible/foreign | Change the requested runtime/type or ownership namespace; offer an unrelated borrowed device or incompatible idle device. It must not be silently leased as the requested compatible owned device. A compatible replacement must respect the same cap; otherwise acquisition blocks with reason. | R1–R4; independent inventory, requested/actual tuple and acquire/retire replies. Toolchain changes require measured compatibility or invalidation, never an assumption. |
| L03 cap/exclusivity | With cap one, overlap two acquisitions and attempt a third; an active device can have at most one lease and total owned active + idle + retirement-pending devices cannot exceed the admitted cap. Wait or fail boundedly; no second unjournaled create and no deletion of an active lease. | R1/R2/R9; HOST real concurrent process/lock trace and, separately, NATIVE inventory/create replies. Repeat with separate owner namespaces to detect cross-owner leasing/deletion. Simulated lock success does not establish exclusivity. |
| L04 expiry | Freeze a finite expiry policy before the run. Exercise before-expiry reuse, at/after-expiry refusal, and an active lease crossing expiry. Expired idle devices cannot be reused. Active operations cannot be deleted out from under their lease; retirement follows release or documented bounded cancellation. A backwards wall clock cannot prolong ownership indefinitely. | R1/R2/R9; controlled-clock SIMULATED boundary cases plus one real idle-expiry/reacquisition NATIVE case with a short configured TTL and recorded actual delay. If TTL/clock semantics are not exposed, mark expiry qualification U. |
| L05 retirement | Separately close through successful final capture, explicit cleanup, and a nonrecoverable command/error path. All owned devices and disposable private build state required by that lifecycle must be retired; raw source/evidence and borrowed/shared caches remain. Retirement wall cost is charged. | R1–R3/R9; actual delete replies and independent post-inventory, preserved file hashes, final receipt. A requested delete without observed completion is a leftover. |
| L06 borrowed | Run using a caller-supplied device/build path. It is accounted for but never adopted into the owned deletion set, retired or globally purged by this owner. | R1–R3; pre/post identity and byte/directory snapshots. Need real borrowed-resource evidence for this claim; protocol simulation alone is partial. |
| L07 interruption/ownership | Interrupt an owner after a journaled create and after a dispatched command, then reenter the same root. Reconciliation must not create a duplicate or delete another owner's resource. A stale PID, edited marker, swapped root, copied journal or claimed device prefix is not sufficient ownership proof. | R1–R3; real HOST process termination/lock evidence plus NATIVE inventory for actual native recovery. Fault-injected checkpoints are SIMULATED. Retain both interrupted and recovery logs. |
| L08 admission/cleanup failures | Insufficient space, at-cap resources, unhealthy pooled device, unavailable SDK/runtime, command timeout and failed retirement must fail boundedly and preserve the primary error plus cleanup errors. Read-only routing of an existing valid package can continue where safe; no accepted delivery with unresolved required cleanup. | R1–R3/R7/R9; each supplied failure source labeled. At most one declared recovery attempt per request in this qualification; all attempts and costs remain. No global cache purge or retry-until-pass. |

The exact expiry semantics and resource cap are operator-declared policy, not
assumed new configuration field names. Use the documented default cap for normal
runs, and a short finite TTL only for the expiry challenge. Keep benchmark policy
identical between A/B; expiry fault probes are outside performance measurement.

## Capture package and coverage scenarios

| ID | Challenge and required outcome | Minimum raw proof and limit |
| --- | --- | --- |
| C01 valid unchanged reuse | Invoke the default path again with unchanged relevant source, plan, inputs, environment and a complete byte-intact package while a review/measurement/source-repair task is pending. The service validates and routes that same package without another SDK launch, image collection or app activation. | R1/R3/R5–R7; exact reused bytes and zero SDK invocations from the command/process trace, not a cache-hit label. This is HOST/protocol reuse; its native credibility comes from the original NATIVE package. |
| C02 final review closure | Produce a fresh full final package, complete its outstanding bound image/source observations, then finish through the public default completion path. It must revalidate current source, full coverage, actual environment and resource retirement against that original final package without another native capture. | R1/R5–R8; final capture marker cannot be added later by a worker. Current source drift, missing source duty, disagreement or incomplete cleanup blocks acceptance. |
| C03 wrong scope | Supply an ordinary feedback or targeted package as final, omit a mandatory state/target/scroll interval, or use one state's bottom image for another state. The service must retain the exact missing cells/U and request the required full native work; it cannot relabel scope or reduce the mandatory denominator. | R4–R7; complete frozen required-ID set and state-local snapshot/interval maps. A union of observed IDs does not prove full content. |
| C04 action/coverage negatives | Include a disabled or ambiguous target, missing reveal target, unexecuted/failed dispatch, wrong callback interval, caller replacement without demonstrated input advancement, target-only coverage and a torn hierarchy/image epoch. Pass only independently evidenced aspects; dependent callback/visual claims remain U. | R4–R6; real native negative cases for claimed action/coverage capability. SIMULATED malformed packets qualify rejection only. Existing native facts must not disappear because a separate aspect is unavailable. |
| C05 integrity/identity negatives | Swap one frame or report, edit manifest/observation bytes, use a foreign review, mix source/bridge/input/process/action bindings, alter a compiled cache artifact, or substitute an old package under a new path. Reject the altered proof; retain the original unmodified package and diagnostic. | R3–R7; independently retained original digests and exact altered payload. Rehashing the outer wrapper cannot legitimize a false inner identity. |
| C06 separate lifetimes | Retire/expire the device while retaining an otherwise valid historical package: routing/review may still use that original evidence. Conversely a live pooled device does not freshen old evidence. Any independently declared evidence-age limit or final fresh-capture requirement still applies. | R2/R5–R7; distinct device and evidence times, expiry policy and decision. Device TTL is not screenshot freshness. No new blanket evidence TTL is introduced by this protocol. |

## Platform dependency scenarios

Start these from authentic iOS and Android packages with separately sealed
platform source maps and any shared dependencies. If authentic packets are not
available for a platform, do the protocol challenge but label its native claim U.
Each challenge starts from a clean copy of the same frozen starting state; it does
not inherit another challenge's invalidation.

| ID | Single controlled change | Required invalidation and raw proof |
| --- | --- | --- |
| D01 | iOS-only production dependency | iOS current-code credit is invalid; unchanged Android native evidence remains eligible after validation. R3/R5–R7 show measured iOS change, Android unchanged digest namespace, actual routing/SDK calls and retained Android raw rows. |
| D02 | Android-only production dependency | Symmetric to D01. Same relative filename under two platform roots must not merge namespaces. |
| D03 | shared source/resource/semantic dependency | Both affected platforms lose current-code credit and require applicable fresh native rechecks; no stale P survives by platform prefix. Raw before/after resolved paths and both dependency maps are required. |
| D04 | unrelated unbound file or new evidence output | Neither platform's valid capture is invalidated merely because an unrelated directory changed. R3/R7 must show the file was independently outside both dependency/claim sets, not declared irrelevant after observing the result. |
| D05 | one platform's bridge, fixture, font/resource, toolchain/SDK, compile option or requested runtime environment | That platform cannot reuse old current-runtime/native credit without a verified compatible identity. The other platform is invalidated only if its sealed dependency/claim set is actually affected. R3/R4/R7 show the changed input and actual environment; an unchanged component file alone is insufficient. |
| D06 | approved expectation/policy/routes/required coverage changes | Old evaluated conclusions and review bindings cannot pass under a new oracle. Raw observations may be reused only through explicit revalidation that proves compatible measured inputs/environment and sufficient current mandatory coverage. Otherwise reacquire. Never reuse an old verdict or reduce current required IDs. R5–R7 retain both oracle versions and rebuilt verdicts. This does not require an unimplemented cross-oracle reuse feature; rejecting reuse safely is sufficient. |
| D07 | deleted/renamed source, alias/symlink/root swap or unclassified relevant edit | Resolved dependency identity must detect the edit or mark impact unknown; unknown impact triggers conservative full applicable recheck. No claim that all unknown files are platform local. R3/R7 include namespace and resolution evidence and the unresolved capability. |

Native evidence, visual/source review bindings and delivery acceptance are
separate validity layers. A source-only claim edit invalidates that claim's
observation; it need not invent an additional SDK capture if it is not a native
dependency. Conversely valid source review cannot certify changed native code.
The operator must approve the ledger's actual dependency completeness; a correctly
executed declared map does not prove that undeclared real dependencies are absent.

## Tool-driven repair handoff scenarios

No production business source is changed in qualification. A native capability
harness with an independently sealed, deterministic mismatch may supply a real F
for these checks. Correctness repair is a separate phase; its changed source must
never enter the same-code speed comparison.

| ID | Challenge and required outcome | Minimum raw proof and limit |
| --- | --- | --- |
| H01 supported task | A demonstrated native/visual F must emit a repair task through the DEFAULT queue, carrying exact current-source/capture/rule/state identity and raw evidence needed by an independent worker. Source locations must be actual citations; cause hypotheses must remain hypotheses. Unsupported U, environment repair, image review and measurement disagreement must remain the appropriate distinct work. | R1/R5/R6/R8; worker receives only emitted task plus minimum cited raw artifacts and public skill contract, not the intended patch, suspected implementation bug or prior conclusions. |
| H02 valid tool completion | The worker performs a minimal authorized harness patch, then uses the documented completion tool. The service measures actual source changes, binds the completion to the task and original finding, invalidates affected evidence, and requests a fresh appropriate native recheck. Only new native evidence plus fresh full final gates can establish pass. | R3/R7/R8; actual tool call/response, before/after bytes, measured changed paths and subsequent native receipts. A completion receipt is not a test pass or proof of root cause. |
| H03 invalid/no completion | Try an unchanged source with a claimed patch, a foreign/stale/duplicated task, a replaced capture, modified expected value, omitted tool completion and a worker explicitly unable to fix. Retain unresolved F/U and reject false success; no accepted result and no unbounded unchanged-source SDK loop. | R1/R5–R8; actual negative tool requests/responses and subsequent default trace. A simulated worker only proves handshake behavior, not that the system repaired real code. |
| H04 review/source-only cycle | Give valid image/source observations without a native source change; continue through default routing/completion using the valid original package. Missing or conflicting observations stay pending with the raw reasons. | R1/R5–R8; task identities, bound actuals, zero extra native commands, and final/source acceptance gates as applicable. Runner dispatch does not claim to understand the design or autonomously edit code. |

## Same-code/same-coverage AB/BA benchmark

Run this only after correctness qualification has a sealed report and the
workload/arms are frozen. Any missing required native capability or unresolved
identity problem is reported before a speed claim. Never start a new business
blind task to obtain a speed result.

Use exactly two order blocks: block 1 = A then B; block 2 = B then A. This is four
arm episodes. The operator records all four; it does not select the fastest pair.
Use the same hardware, process scheduling, public default entry points, timeouts,
resource policy and mandatory plan. Run arms sequentially, with no overlapping
benchmark native commands. Private caches/pool start empty for every episode;
borrowed/shared SDK caches are not purged. Record their observed state and order.
This is **private-state cold**, not a claim of a physically cold OS/compiler cache.

Each episode contains the following identical externally requested work:

1. **C0 cold:** full native capability collection for both available platforms,
   with the fixed text/button/callback/caller-update/tall-content/bottom-target
   plan and actual environment. Preserve a pending image or source review where
   the frozen plan requires it.
2. **R0 unchanged:** invoke the default routing/review path for those exact
   packages, bind independently observed actuals, and invoke the next default
   transition. No relevant input/source change exists. A correctly reused
   package needs no SDK command. A baseline is allowed to use any reuse its
   unmodified normal service already supports; do not force redundant work.
3. **W1 warm:** an independently approved second deterministic iOS fixture
   payload requires a fresh iOS capture (for example, a visible generic marker
   changes while the same callback/update/scroll coverage remains mandatory).
   Source is unchanged. Android inputs/dependencies are unchanged; its existing
   valid package remains available. Use only documented default transitions,
   and retain any unnecessary baseline recapture in its measured work. The
   exact two payloads and expected rows were frozen before C0.
4. **F2 final:** request fresh FULL final native collection for both platforms
   with the final epoch's fixed inputs and every mandatory row. Bind the final
   package's required review/source actuals and finish it without changing code.
   Neither arm can relabel C0/W1/targeted evidence as a fresh final packet.
5. Retire all episode-owned pool devices and disposable build state through the
   normal final/cleanup lifecycle, preserve evidence, verify raw post-inventory,
   and close the resource receipt. Stop timing only after durable completion.

The iOS app/test process, inputs, events and images must be fresh for C0, W1 and
F2 even if B reuses its simulator or compiled host. R0 and final-review closure
refer to original package bytes and do not pretend to be new captures. Shared
SDK caches remain a documented common exposure. A build-cache advantage caused
by unequal starting private state invalidates a pair.

For every epoch and arm retain the complete raw mandatory-ID denominator,
per-state full/target coverage, all original P/F/U/N/A rows and raw reason/status,
dispatch/method/interval checks, environment and identities. The oracle includes
actual P checks and a predeclared independent F/U control when needed to prove
those statuses are preserved; controlled protocol mismatches are not reported as
business defects. Do not invent unsupported expected P values just to make the
benchmark all green. Repairs, expectation edits, changing source or shrinking
coverage invalidate the performance episode.

Use one monotonic machine collection timeline per episode. It includes resource
admission, lock wait, pool validation/create/boot, source/package verification,
compile/cache validation, native test, export, checks/routing, journaling and all
owned retirement. Count failed work, rejected attempts and cleanup. Exclude only
separately timestamped human/model observation/repair/queue intervals; report
those intervals and total elapsed time alongside collection time. Do not subtract
nested native substage intervals twice or hide cleanup in another process after
the measured end. Timings for source-changing repair scenarios are outside this
same-code comparison.

Report C0, W1, reuse/closure and retirement components as explanatory breakdowns,
without adding overlapping stage walls. Compute the primary measured improvement:

`speedup = 1 - (sum of B machine-collection walls / sum of A machine-collection walls)`.

The local performance gate passes only when speedup is at least 0.20, every
corresponding mandatory P/F/U row is identical, no mandatory U increases, all
mandatory coverage and evidence identity gates hold, and no required retirement
remains. Keep both order-block ratios and all four raw episode walls visible.
Two blocks support this bounded local measurement; they do not establish a broad
statistical claim across hardware/projects. No rounding can turn 19.99% into 20%.

Bound the benchmark to these four episodes, one normal native attempt per
requested acquisition, the frozen existing command timeout (900 seconds unless
the admitted project already requires another value), and 120 minutes total
machine collection time. Stop on that bound and report incomplete; do not reduce
work to fit. An unrelated host interruption can invalidate at most one complete
block, which may be rerun once in the same order with both arms; retain the failed
block and its time and explain the objective interruption. Candidate failures,
slower timing, changed judgments or cleanup failures are results, not grounds to
discard a block. No adaptive runs or post-result threshold changes are allowed.

If one platform cannot supply authentic native packets, report the available
platform's bounded timings and the protocol-simulated cross-platform results
separately. That is partial qualification; it cannot claim native qualification of
the unavailable platform or completion of an all-platform performance gate.

## Report and handback

The executor returns a sealed raw-artifact index, source/workload/arm hashes,
scenario-by-scenario evidence class and P/F/U, all discrepancies, actual open
tasks/capabilities, per-episode timings and the exact formula inputs. It states
whether the 20%/identity/U gate passed, failed, or could not be evaluated.

No runtime result exists at this protocol's seal. SDK availability, native pool
health/reuse/expiry/deletion, concurrent ownership recovery, actual iOS/Android
packets, full dependency completeness, original review correctness, repair-worker
behavior, tool completion, resource footprint and performance remain unevidenced.
The implementing agent may read this protocol after sealing to meet the
requirements; subsequent qualification must preserve the frozen requirements and
report unsupported capabilities honestly. A changed protocol requires a new seal
and an explicit reason before rerunning, never retroactive acceptance.
