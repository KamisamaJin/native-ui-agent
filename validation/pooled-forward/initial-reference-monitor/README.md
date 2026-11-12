# Common initial-reference supplemental monitor

This is an operational registration/measurement supplement for already-required
initial private reference collection. It changes no frozen spec, envelope, SUT,
contract, threshold, final source or old ownership journal. It forwards no SDK
and deletes no files/devices. Keep the original v2 continuous meter running.

Before any initial reference SDK, all ten public sources/self-claims must seal,
the hidden authorization must exist, and original resource slots must be zero.
Use a new canonical initial source tree verified against the original capsule
(complete file set, byte counts, controller content SHA), with read-only source.
Use distinct new resource roots, e.g. `cache/business/initial-reference/Tn/resources/ios`.
Do not copy a final journal or put an initial source into a final arm's old path.
The SUT derives the new owner key from the new resolved source roots.

Create and pin a declaration before collection:

```json
{
  "version": 1,
  "kind": "common-initial-reference-meter-extension",
  "owned_root": "/ABS/study/cache/business/initial-reference",
  "resource_journals": [
    "/ABS/study/cache/business/initial-reference/T1/resources/ios/journal.json"
  ]
}
```

List all five actual task journals, not just the modified task. Paths are scope
declarations, not ownership proof. The frozen envelope's existing token, root
inode and unique create-name checks validate every present journal. Create
intents without UUID still count. Its global two-slot cap is retained; every
individual reference config retains one slot. Only one reference episode runs
at a time and is positively closed before the next one.

Run the monitor as a fresh, process-visible Python process with an explicit
32-hex acquisition token and fresh record directory:

```sh
python3 -B monitor.py --declaration /ABS/declaration.json \
  --record /ABS/fresh-monitor-record --token TOKEN32 --max-seconds 14400
```

`READY.json` appears only after the full extended-union first sample. The monitor
has its own session and records the frozen process birth/group/token identity.
Before **each** reference SDK, require a successful process-visible preflight:

```sh
python3 -B monitor.py --record /ABS/fresh-monitor-record --preflight
```

Preflight verifies unchanged inputs/modules, live process identity, no halt/close,
the exact original-plus-declared spec and zero original/supplemental slots. It
never creates a replacement time window or launches a device. The original
`native_envelope.py` still wraps collection unchanged. Monitor error, expired
lifetime or the same original byte/free-space budget sets the existing study
halt marker; the original envelope safety gate handles cancellation/recovery.
The supplement does not guess or kill a PID and does not erase a halt.

After all supplemental reference resources and current original slots close,
create the record's `STOP` file, await `CLOSED.json` and require `status: closed`
and explicit zero slots. `union.jsonl`/its original Meter summary and every
failure remain records. A source tree is cleaned only after archive byte checks
and closed pure replay, using positive ownership.

For the whole-study observed peak, use complete original-v2 samples before the
READY cutover, extended union samples during supplemental coverage, and original
samples after positive supplemental closure. Take the maximum across these
coverage windows; never sum group/device/phase peaks. Record cutover/closure and
actual sampling durations. These remain allocated-byte sampled lower bounds,
not exact transient/APFS physical usage. New common-reference collection and
its monitoring are research/oracle cost, separate from either arm's own public
delivery or treatment credit. The original meter alone omits new simulator
paths during this window and must not be claimed as complete coverage there.

HOST tests exercise metadata/ownership boundaries without SDKs or an actual
monitor. A real READY/preflight/close and byte-preserving reference collection
remain required before claiming operational success.
