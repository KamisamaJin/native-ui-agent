# Paired blind-study execution helper

This **v2 candidate** preserves the v1 phase/queue/source rules and adds bounded
independent source-domain revision transport plus a mandatory pure profile guard
when configured. See [V2-ADMISSION.md](V2-ADMISSION.md) for the new manifest fields,
review/seal/provenance formats and exact commands. The original `business-tools`
freeze is preserved; v2 starts a fresh run and cannot hot-edit an admitted v1 run.

`blind_study.py` is a case-agnostic controller for the predeclared five-task,
two-arm study. It does not author cases, implement repairs, edit expected values,
grade, reveal mappings, run hidden evaluation, or modify the frozen tools.

The controller calls each frozen `scripts/ui_loop.py` through the existing
`measure.py` and `native_envelope.py`. The envelope's existing default meter spec
must be supplied unchanged. The source windows, queue, transport, source capsules,
readsets, failures, and own delivery endpoints are recorded by this helper.

## Manifest

See `manifest.schema.json` and `manifest.example.json`. The example is entirely
placeholder data and is intentionally not executable. Replace every path/hash;
provide all five independently designed and initially authored paired tasks.
The JSON schema describes structure; the CLI additionally enforces identities,
prerequisites, source equality, resource coverage, ordering and phase barriers.

Required top-level fields:

| Field | Meaning |
|---|---|
| `version`, `study_id`, `run_root` | Version 1; safe ID; fresh absolute append-only output directory. |
| `protocol` | `{path, sha256}` for frozen `PROTOCOL.json`. |
| `speed_gate` | `{path, sha256}` for that root's `qualification/benchmark-gate/RESULT.json`; both `passed` and `business_tasks_may_start` must be `true`. |
| `design_approval` | `{path, sha256}` for the independently approved design seal. This is an opaque prerequisite; the helper does not select or reinterpret design values. |
| `envelope` | Paths and hashes for existing envelope, meter, and envelope's exact default `operators/whole-study-meter-spec-v2.json`. |
| `tools` | Frozen anonymous tool aliases, each containing `skill_root`, `api`, and complete public `files` hash map. The APIs are `baseline-explicit-prior` and `stateful-default`. |
| `tasks` | Exactly five unique tasks in sequential order; exactly two arm aliases in each task. |

Each arm supplies `tool`, `workspace`, complete ordered `source_roots`,
`public_configs` (profile ID → absolute frozen config), optional `profile_order`,
`public_readset` (all immutable public inputs, including bridge/plan/lock/fixtures/
policy/environment/build inputs), `hidden_configs` (same profile IDs → opaque
absolute paths), and `resource_roots` (the existing predeclared private owned
roots). Configs must carry that arm's exact complete `source_roots`.

Use the existing meter spec's declared business paths and journal roots. The
public iOS profiles in an arm must share exactly one owned resource root, with
`max_simulators: 1`; the common envelope enforces the global cap of two. Distinct
tasks finish and retire sequentially. Private roots must be disjoint from source,
evidence, other arms and shared SDK caches. The helper never purges SDK caches or
deletes simulators directly; `retire` delegates to the frozen positive-owned API.
The frozen meter must list each managed-iOS resource journal, because its devices
live outside the private tree. Android JVM roots need allocation-path coverage;
they do not require an external simulator journal entry.

Declare only actual production source directories, such as Swift `Sources` and
Android `app/src/main`. The frozen Android collector generates test sources in
its separate test directory and writes Gradle output outside `app/src/main`;
the iOS collector generates its host and DerivedData in evidence or managed
compiled scratch outside `Sources`. Keep those writable output/build locations
outside `source_roots`; source and final-capsule permissions then do not prevent
the compiler's ordinary output writes. This integration check is based on public
frozen script inspection; the helper's tests do not claim a native compile.

The control config must retain its old documented shape: no new `workflow`,
`platform_source_roots`, or resource `pool` fields. The treatment must supply its
ordinary frozen workflow root. The helper does not invoke measured-completion
or adoption APIs on behalf of the control. Treatment patch measurement, task
handoff, pool selection and adoption remain the default frozen state machine's
responsibility.

Generate a tool identity without running its code:

```sh
python3 -B blind_study.py tool-identity \
  --skill-root /ABS/FROZEN/ARM \
  --api stateful-default
```

The output hashes `SKILL.md`, public scripts, public references and assets. Add
any further frozen service dependencies to `files`. Pin actual frozen copies;
do not use the synthetic fixtures in `test_blind_study.py`.

## Controller workflow

Commands below are run from this directory. All CLI paths are absolute.

```sh
python3 -B blind_study.py init --manifest /ABS/study-manifest.json
python3 -B blind_study.py admit --run /ABS/run --task T1
```

`init` verifies the passed measured gate and independent design seal, all five
initial A/B byte identities, fixed public inputs, frozen tools, and predeclared
resource coverage. It seals all ten raw initial source capsules and one
`INITIAL-COHORT.json` before any request can be served. Hidden paths need not
exist at this point and are not opened or hashed. No renders occur during init.

`admit` assigns the next task and makes both initial production trees read-only.
T2 cannot be admitted until both T1 arms have final source/self-claim seals and
positive retirement proofs. Each generated `arms/T1/A/assignment.json` contains
only that arm's public configuration, sources and frozen tool location. Repair
agents need neither the controller manifest nor the other assignment.

Enqueue both initial diagnostic bundles (D0), then serve each FIFO ticket:

```sh
python3 -B blind_study.py request --assignment /ABS/run/arms/T1/A/assignment.json diagnostic
python3 -B blind_study.py request --assignment /ABS/run/arms/T1/B/assignment.json diagnostic
python3 -B blind_study.py serve --run /ABS/run
python3 -B blind_study.py serve --run /ABS/run
```

One diagnostic request traverses every assigned public profile in declared
`profile_order` (otherwise sorted profile ID order). There are at most **two
diagnostic bundles total per arm, including D0**. Failed requests remain charged.
There are no automatic retries. A visibly requested second diagnostic can retry
a failed initial collection, still at exact initial source; it consumes the
remaining request. Each native capture is serialized by one study-wide exclusive
FIFO queue. A queued-source change fails the ticket rather than silently
reissuing it at new source. A started ticket without a completed result is
retained and blocks later execution for operator reconciliation.

The first complete successful D0 evidence bundle automatically starts that arm's
1200-second source-repair window at result readiness. Its images/native facts
are available then. The other arm's queue wait cannot consume this source
window. Initial image/source review and analysis **do** consume it. A live,
separate host-only deadline guard freezes the actual source at expiry. The
guard's observed enforcement lateness and any file modification time after the
deadline remain visible; late source cannot receive a public accepted endpoint.

The repair agent acknowledges D0 and unlocks its source within that already
anchored window:

```sh
python3 -B blind_study.py feedback-ready --assignment /ABS/run/arms/T1/A/assignment.json
```

This acknowledgement cannot reset or postpone the deadline. It is optional for
an arm that chooses to lock its unchanged initial source and report failure.
Initial bytes are checked again before every profile's D0 execution. The agent
may now perform its own source repairs; the helper never writes source bytes.

Actual reviews use only the assigned public profile. Capture receipts, hashes,
final cycle references and control history are selected by the program:

```sh
python3 -B blind_study.py request --assignment /ABS/run/arms/T1/A/assignment.json \
  review-native --profile ios --submission /ABS/actual-image-observations.json
python3 -B blind_study.py serve --run /ABS/run
python3 -B blind_study.py request --assignment /ABS/run/arms/T1/A/assignment.json \
  review-source --profile ios --submission /ABS/actual-source-observations.json
python3 -B blind_study.py serve --run /ABS/run
```

Use the frozen service's generated review templates. Image review corrections
require explicit `--supersedes-sha256 HASH` and `--revision-reason TEXT`; original
judgments stay archived. Reviews are explicit operations, never hidden retries.
They do not consume another diagnostic bundle or edit expected values. The old
control receives its documented previous original capture plus SHA and pinned
cycle history. The treatment receives no previous/history flags and resolves
registered source/image/repair state itself.

When ready, seal source irrevocably and collect final public outcomes:

```sh
python3 -B blind_study.py lock-source --assignment /ABS/run/arms/T1/A/assignment.json
python3 -B blind_study.py request --assignment /ABS/run/arms/T1/A/assignment.json final
python3 -B blind_study.py serve --run /ABS/run
```

The deadline guard performs the same source lock if the arm does not lock early.
There is no unlock operation after source seal. Public final acquisition,
read-only inspection and actual review may extend beyond the source deadline,
always at exactly that arm's own sealed bytes. A final image/source review can be
bound with the commands above, followed by the frozen final review completion:

```sh
python3 -B blind_study.py request --assignment /ABS/run/arms/T1/A/assignment.json \
  finish-review --profile ios
python3 -B blind_study.py serve --run /ABS/run
```

Repeat for all mandatory profiles. A final cycle's positive-owned retirement
receipt is checked; if finalization failed without complete retirement proof,
request an explicit `retire` bundle and serve it. This invokes only frozen
`cleanup-native-resources` and preserves the failure. Successful finalization
does not incur an extra cleanup request merely for the helper.

After all final public service outcomes and retirement proofs exist, submit a
final self-claim JSON with a nonempty `statement`:

```sh
python3 -B blind_study.py seal-self --assignment /ABS/run/arms/T1/A/assignment.json \
  --claim /ABS/final-self-claim.json
```

This binds the final source, claim, immutable original evidence, final service
outcomes and retirement. A self-claim cannot override a service failure/unknown.
Exit code zero, `native_executed`, a dispatched task or an original capture alone
is never delivery acceptance. `public_service_accepted` requires actual final
`status: accepted`; full study delivery still requires independent hidden quality.
F/U outcomes remain archived and publicly unresolved.

The arm's own endpoint starts at its first D0 enqueue and ends at this final
self-seal. It includes all queue wait, native work, reviews/checks, retirement and
the self-claim; it does not wait for the other nine arms. The later research
barrier wait is recorded separately.

After both arms finish, repeat `admit`/repair/final/self-seal for T2 through T5.
Only then may the controller seal and authorize the hidden cohort:

```sh
python3 -B blind_study.py seal-cohort --run /ABS/run
python3 -B blind_study.py authorize-hidden --run /ABS/run
```

`authorize-hidden` rechecks all ten current sources, original packages and final
self-claims. It records authorization durably **before its first hidden file
open**, then checks that hidden configs retain final source identity and owned
resource bounds and use fresh, independently admitted workflow/review stores
disjoint from public contexts and other arms. Hidden profiles may share one
fresh workflow within their own arm. Public task/F state is never cleared or
replaced. A hidden evaluation must not receive public previous/history transport,
including on the old control, because its oracle/inputs differ. This helper does
not launch hidden evaluation, assemble grader packets, grade or reveal mappings.

## Records and limits

* `events/*.json` is an exclusive, append-only hash chain; requests, results,
  timestamps, source maps and readsets are individually immutable files.
* Initial/final source capsules contain original bytes. Each service packet,
  including partial failures, has an immutable full file hash inventory.
* Per-profile `command.json` records generated transport; `supervised-command.json`
  records meter/envelope invocation. Frozen services keep their own full original
  native packets, source registries, state/handoff journals and measured repair
  completion. Nothing is recopied into an invented accepted capture.
* `meter.jsonl` and its existing summary record sampled allocation peaks and
  enclosing command work. All identity/lifecycle/cleanup utility time remains
  inside enclosing request and own delivery wall.
* `sdk-observation.json` contains **explicit partial** resource journal command
  records and pinned byte prefixes. SDK identity queries and internal descendants
  are unobserved. Empty journal observations never mean zero SDK work. The helper
  does not inject modules, change `PYTHONPATH`, or patch frozen processes.
* `new_ui_acquisition` comes from the frozen cycle and is corroborated with its
  original execution/capture identities; missing/error outcomes stay `null`.
* This is a procedural controller for cooperating study operators. Read-only
  permissions, process heartbeats and append-only hashes do not create an OS
  sandbox against an owner deliberately bypassing or killing the controller.
  Source replacement, queued drift, after-seal edits, missing proof and interrupted
  tickets fail closed through this CLI.

## HOST/SIM verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B test_blind_study.py
PYTHONDONTWRITEBYTECODE=1 python3 -B test_domain_admission.py
```

These tests use synthetic JSON service outcomes and forbid subprocess/SDK
forwarding. They exercise five-pair identity admission, timing/request caps,
source immutability, FIFO exclusion, failure retention, control/default transport,
final F/U handling and the all-ten hidden barrier. `HOST-SIM/RESULT.json` is a
controller verification artifact, never native or business evidence.
