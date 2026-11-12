# Terminal first-D0 source repair admission

V3 changes one generic readiness rule. A naturally authored, compile-only initial
may crash or encounter a source-domain precondition at its first native request.
Source repair therefore starts from the first **complete terminal D0 bundle**,
including honest failure logs. A successful native collection is not required.

Everything else remains the v2 shared study mechanism: exactly five fresh paired
initials, all-ten initial admission before any D0, sequential task execution, one
serialized native queue, at most two diagnostic bundles per arm including D0,
1200 source-repair seconds per arm, irrevocable early source lock, original
capture/source registries, unchanged frozen defaults, independent same-policy
source-domain approval, configured mandatory pure profile guard, final source
immutability, final F/U retention, own delivery endpoints, and all-ten hidden
barrier. No repair is implemented by the helper. This is common transport and
repair opportunity, never treatment credit or native/quality acceptance.

## Exact readiness rule

The first diagnostic request for an arm is D0 permanently. It becomes ready only
after the controller has durably written:

1. Exactly one outcome for every assigned profile, with no duplicates or missing
   profiles, and each individual `outcome.json` matching the complete result.
2. A complete `result.json` bound to that request/task/arm and a pinned append-only
   `request_finished` event.
3. Passing source/config/tool/readset integrity proofs before each operation and
   again after it, including after a failed operation. The request source must
   equal its exact admitted initial capsule. The common envelope's or original
   capture's explicit source/input/tool drift reports also invalidate integrity.

Zero exit, images, an original capture receipt or `native_collection_success`
are **not** readiness conditions. Runtime/SDK/collector failures, `review_source_domain`,
blocked collections and pure profile-admission rejections remain truthful F/U
outcomes. Their logs and partial original packets stay retained. No successful
status, image, native fact or accepted delivery is fabricated.

An empty/partial profile bundle, missing outcome file, interrupted/in-flight
ticket, source replacement/drift, config/tool/readset drift or invalid first-D0
integrity proof does not start or unlock repair. A later D1 cannot replace that
invalid first D0 to obtain a later deadline. Interrupted tickets keep partial
outcome/log artifacts plus a `request_interrupted` event, no complete result, and
remain pending; the controller neither continues the remaining profiles nor
retries them automatically.

## Automatic clock and acknowledgement

At complete terminal D0 readiness, the controller automatically records
`repair_started` with `deadline_clock = result.finished_at_clock + 1200` and the
corresponding fixed wall-clock deadline. This happens before deadline-guard
startup; a guard setup failure cannot postpone the deadline. Source remains
read-only until a live guard and the acknowledgement command are present:

```sh
python3 -B blind_study.py feedback-ready \
  --assignment /ABS/run/arms/T1/A/assignment.json
```

The command rechecks the first D0 durability proof and current initial integrity,
then restores the production tree's original write permissions within the already
anchored window. It cannot reset the start, extend the deadline, waive a failure,
or edit source. Analysis, initial reviews and admission work consume that same
window. Read-only post-deadline review at the arm's locked exact bytes remains
allowed under v2 rules before final self/cohort seal.

An arm that has not completed its own terminal D0 gets no clock. The other arm's
queue and result times cannot start it. Own end-to-end delivery still starts at
each arm's first D0 enqueue and includes all queue/native/review/check/retirement
time through its own final self-seal; cohort wait remains separate.

## Repair and D1

An agent may inspect D0 failure logs, acknowledge readiness, and perform its own
source repair. If the repaired exact component needs a new closed-domain source
approval, the unchanged v2 independent reviewer/registry/provenance flow appends
only that actual source SHA+bytes under the same immutable policy. Neither an
approval nor a profile guard edits or waives an oracle/responsibility.

```sh
python3 -B blind_study.py request \
  --assignment /ABS/run/arms/T1/A/assignment.json diagnostic
python3 -B blind_study.py serve --run /ABS/run
```

This second diagnostic is D1, including when it retries a failure. It consumes
the second and last bundle and never creates/replaces `repair_started`. A failed
D1 cannot buy another source window. Final collection/review remains read-only
at the irrevocably locked source, and failed/unknown mandatory outcomes remain
not delivered.

## HOST/SIM verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B test_blind_study.py
PYTHONDONTWRITEBYTECODE=1 python3 -B test_domain_admission.py
PYTHONDONTWRITEBYTECODE=1 python3 -B test_terminal_d0.py
```

The first two suites are copied unchanged from v2. Focused v3 checks cover both
profiles failing with read-only logs then source repair and successful synthetic
D1; failed retry clock invariance; blocked source-domain admission then unchanged
v2 approval transport; incomplete/non-durable/interrupted tickets; source/input/
tool drift; intact initial capsules; inactive arms; and guard startup failure.
Every service receipt and log is explicitly synthetic HOST/SIM data. Process/SDK
forwarding is forbidden. No business source, oracle, SDK, simulator or rendering
is used by these tests.
