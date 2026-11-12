# Pre-run amendment: ordinary finalization and explicit fresh collection

Amendment ID: `pooled-native-qualification-1+a1`.

This amendment preserves the original protocol and its seal byte-for-byte. It was
requested and written before any qualification SDK run or performance sample,
without reading candidate implementation code, prior validation cases, results or
speed measurements. It clarifies the user's NEW requested capture-package reuse.
It does not change required native coverage, expected values, tolerances, raw
P/F/U identity, mandatory U accounting, resource retirement or the 20% speed gate.

## Rationale and supersession

The original protocol inherited the current reference's always-new-full-final
collection rule. That is an existing service behavior, not a necessary limitation
on the newly requested ability to reuse a valid capture package. Keeping that
rule for the ordinary finalization request would exclude the requested capability
from evaluation and force duplicate native work even when all required facts have
already been collected from the exact current code and inputs.

Accordingly, this amendment supersedes every v1 statement that requires an
otherwise eligible original full packet to have been newly collected or marked
`final` solely in order to finalize. It also supersedes benchmark step F2's demand
for another native collection. It does not authorize changing a packet's original
bytes, its collection purpose, scope, identities or historical resource receipt.
An ordinary or targeted *incomplete* packet still cannot gain full coverage by
being relabeled. The unchanged requirements below define eligibility.

## Two distinct external requests

**Ordinary finalization:** Close delivery against the approved current obligation
set. The DEFAULT service may use existing original full native evidence when it
is eligible. It must validate that eligibility and close all required review,
source, environment and resource gates. The final acceptance receipt explicitly
cites the unchanged original packet, its digest and the reuse decision. It is a
new acceptance/closure receipt, not a rewritten native collection manifest.

**Explicit fresh collection:** The caller specifically requests new native
execution and evidence. A valid existing full packet does not satisfy that
request. The service must produce a genuinely new full native test/session/app
instance, input/event receipt, capture/export and fresh evidence directory, or
report the inability honestly. Compiled artifacts and a compatible pooled device
may still be reused. Deterministic image bytes can legitimately hash identically;
actual execution and original exported attachments establish new collection.

The admitted public interface must distinguish these requests unambiguously. Do
not invent an option name in this protocol or invoke an undocumented test-only
method. If the supported default interface cannot distinguish them, record that
capability as U rather than treating the requests as equivalent.

## Full original packet eligibility

For ordinary finalization, all of the following are independently rebuilt from
the original bytes and current approved inputs; a self-entered `valid:true` is
insufficient:

1. Authentic original native provenance, original independently retained digest,
   complete byte integrity and coherent build/source/bridge/template/input/
   action/process/event/snapshot identity. No missing or mixed inner artifacts.
2. The packet's actual production dependency identity is still current for that
   platform. The independently approved platform/shared dependency map is
   unchanged or revalidated. Unknown relevant impact cannot be declared safe.
3. The current approved fixture, environment and execution requirements match
   the actual captured inputs/native environment. Any explicit age constraint
   still holds. A live pool device cannot refresh old evidence.
4. The original packet really contains the complete current mandatory state ×
   requirement × aspect coverage, including every full-content sweep, callback
   precondition/interval, target and native environment check. A targeted packet
   lacking any mandatory scope is ineligible. No denominator or U row is dropped.
5. The current approved oracle/expectations/tolerances/policy remain fixed or
   every required conclusion has been properly rebound/recomputed. Original
   review actuals are tied to the exact original frames/source; missing and
   conflicting duties remain unresolved. No old verdict is blindly copied.
6. Every required source/responsibility observation is bound to current actual
   files. A source change after capture invalidates affected native credit and
   source observations according to the measured dependency scope. A repair
   completion does not waive the required new native recheck.
7. Final resource closure is separately verified and all required owned device/
   scratch retirement is complete before acceptance. Preserve the original
   collection resource receipt. If it intentionally retained a pooled device,
   bind a new authentic owner/generation/lifecycle cleanup receipt to final
   closure. Never edit the original receipt to claim earlier retirement.

An earlier full feedback packet may therefore be eligible even if its original
collection purpose was feedback. A targeted packet may be reused for its actual
measured facts but cannot establish a missing full final obligation. A final
receipt must disclose collection age/purpose and exact reused packet identity.

## Qualification scenario adjustments and added control

* **C01** remains unchanged: unchanged-source routing/review can reuse a valid
  original packet without SDK work.
* **C02** additionally begins from an authentic eligible full feedback packet,
  not only from a previously final-marked packet. Supply its outstanding valid
  observations and request ordinary finalization. Require zero additional SDK
  collection, exact original-byte reuse, current complete gates and newly
  verified resource closure. Its earlier feedback purpose must remain visible.
* **C03** still rejects missing/targeted scope and state-local coverage gaps.
  Feedback purpose alone is no longer a disqualifier when full eligibility is
  independently established. A forged full/final marker never establishes it.
* **C07 force-fresh control** is added outside performance measurement. With the
  same eligible packet and unchanged source/inputs, explicitly request fresh
  full collection. Require a real new native session and complete packet. Repeat
  ordinary finalization with a stale-source, wrong-input, incomplete-coverage,
  wrong-environment, tampered or unresolved-required-review packet; it must
  reacquire applicable missing native evidence or remain unaccepted with exact
  reasons. It cannot reuse stale P or claim that fresh collection occurred.

C07 uses R1–R7/R9 from v1, with actual command/session/test/export proof for the
fresh-collection side. Protocol-only mutations establish rejection decisions,
not native execution. Device retirement/expiry remains separate from evidence
validity. The repair scenarios keep all original gates; an already fresh full
post-repair packet may be reused for ordinary finalization if now eligible.

## Amended AB/BA F2 and comparison

C0, R0 and W1 remain as sealed in v1. In both arms, **F2 is the same ordinary
finalization request using all currently available original full packets**:
the iOS W1 packet and unchanged Android C0 packet, if each is eligible. Complete
their bound review/source duties, verify current native/source/coverage identity,
then retire episode-owned resources and finish. Do not request explicit fresh
collection in this timed step.

Baseline A is allowed to perform whatever its unchanged DEFAULT implementation
requires for that ordinary request, including a redundant full final collection.
Candidate B may reuse eligible originals. Do not force A to recapture if its
ordinary service already supports valid reuse, and do not hand B a special
bypass. Every actual native command and original result is retained. The number
of collections may differ; current approved code, inputs, mandatory coverage and
final P/F/U facts may not. This is precisely the proposed removal of redundant
collection, rather than a reduced acceptance workload.

For the final comparison epoch, map each obligation to the exact original packet
that actually proves it. Preserve its original capture epoch and raw status/
reason. Compare the same current final requirement/state/aspect identity across
arms, retaining all source/input/action/environment identities. Fresh A session
IDs and reused B session IDs differ legitimately across arms; neither can be
mixed within a packet. All mandatory P/F/U rows must remain identical and no
mandatory U may increase. A status discrepancy, even with equal counts, fails
the identity gate.

F2 timing includes eligibility validation, all default route/check/completion
work and actual pool/build-state retirement. A's native final work, if any, is
included. B cannot end its clock while owned resources remain. C0 private-state
cold, W1 warm, R0 reuse, F2 closure and retirement are separately visible, with
the same four-episode AB/BA order and v1 accounting/bounds. C07 explicit force-
fresh is a separate correctness control and contributes no speed sample.

The primary formula remains `1 - sum(B collection walls)/sum(A collection walls)`;
the gate remains at least 0.20 with exact mandatory P/F/U identity, no increased
mandatory U, complete native coverage/current-code proof and completed resource
closure. There is still no runtime result or performance claim at this seal.
