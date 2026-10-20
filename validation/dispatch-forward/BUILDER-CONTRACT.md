# Shared implementation and review contract

Both submissions receive the same public design/API, common thin bridge, clean
upstreams, model settings and stage budgets. Use only the assigned frozen tool.
Do not inspect other submissions, private design/oracle/inputs, prior trial
reports, or the other tool. Do not delegate. No deliberate defects or transplanted
prior experimental components. Preserve upstream licenses and deployment targets.

Production additions belong under `alerttoast/Sources/AlertToast` and
`reply/Reply/app/src/main/java/com/example/reply/ui/waterround`. Only those source
directories may change. Do not modify the common bridge, test dependencies,
operator, selectors, fixtures, acceptance, frozen tool or host. Report an actual
host failure to the operator; do not disguise it as a business source repair.

Implementation has a maximum 25-minute wall budget, including public integration.
Record UTC start/end. Implement both platforms from the public design, then use
one public native integration per platform. Build failures may be corrected and
retried in fresh retained directories within that budget. Before D0 sealing,
inspect compiler/native-test logs and execution counts only: no actual product
image, tree, callback trace, or private validation input review. The provided SVG
is a design intention and may be read at any stage.

The public integration command is `operator.py capture --public --phase d0` with
the assigned workspace/tool/platform/simulator and a fresh output. It uses a
single public example, invokes the actual production component and retains all
native images. Do not open those images/observation before D0. There is one iOS
and one Android native slot per submission; the two platforms may run in parallel.

Finish `implementation.json` with timestamps, changed files, build attempts and
limitations. Notify the operator and stop changing source. Operator seals D0 and
collects the four initial cases with the assigned tool. No images are supplied
until both D0 source capsules seal.

After own D0 corpus delivery: maximum 12-minute **read-only** review, including
reading raw images/native evidence, using assigned tool checks, and writing
`review.json`. No code changes or new captures in this stage. List actual files
and SHA-bound evidence examined, and checked/unassessed scope. Each finding has
`id, platform, case, checkpoint, category, method, target, aspect, certainty,
claim, expected, observed, evidence`. Category is business/visual/integration/
source_api/capability. Certainty is confirmed or uncertain. Evidence entries name
the actual file SHA and snapshot/action when relevant. Findings must name one
atomic aspect and exact case/checkpoint; a related defect does not automatically
establish another rule. Missing dispatch cannot establish handler behavior.
Record duplicates/related clusters separately; do not silently multiply findings.
An empty findings array is valid. Review seal precedes any repair.

After review seal: one repair stage, maximum 15 minutes. Use only own review and
assigned evidence, with no grader findings or other submission. Record each source
repair and its cited finding in `repair.json`. No new business changes after final
seal. Operator will collect all six cases, including unseen holdouts. Final
source may equal D0 when review gives no supported reason to change it.

Budgets are maxima, not waiting requirements. Explicitly finishing a stage early
is allowed. Root records continuous arm wall time including collection, barriers,
operator queue and service interruptions; segment sums are reported separately.
No unsupported PASS for native typography, internal padding or physical hit area.
