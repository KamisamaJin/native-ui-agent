# Independent source-domain admission and pure profile guard

V2 changes transport only. It preserves all v1 cohort, source, deadline, request,
queue, final review, failure-retention and cleanup rules. It does not change the
frozen tools, their default state machines, SDK environment, oracle, expected
values, responsibility index or acceptance rules. Both frozen arms use exactly
the same admission mechanism and bound; this is shared study infrastructure.

## Predeclared independent authority

When a public config has `coverage_domain_ref`, the manifest must include:

```json
{
  "source_domain_reviews": {
    "registry": {"path": "/ABS/independent/REGISTRY.json", "sha256": "FILE_SHA256"},
    "max_requests_per_arm": 4
  }
}
```

The immutable registry has this structure:

```json
{
  "version": 1,
  "kind": "independent-source-domain-review-registry",
  "reviewers": {
    "shape-reviewer": {
      "root": "/ABS/independent/shape-reviewer",
      "scope": "source_shape_only"
    }
  },
  "operators": ["study-controller"]
}
```

Each reviewer root must already be a real directory without symlink traversal,
separate from repair workspaces, source, evidence, resource roots and hidden
configs. Its device/inode and registry bytes are bound at init and rechecked.
Place review artifacts within the study's predeclared measured owned scope.
The review-request bound is fixed identically for both APIs: default four per
arm, explicit range one through eight. Successful admission is one-shot per
request. Rejections are append-only `domain_review_rejected` events, with no
automatic retry.

This is **procedural authority**, consistent with the controller's existing trust
boundary. A trusted operator supplies the exact independent seal SHA and a
separate pinned delivery-provenance record. An ID and hash alone do not establish
independence. The operator must obtain the response from the registered independent
reviewer, verify its origin, and record that delivery. There are no cryptographic
signatures or OS access controls against a deliberately bypassing same-user owner.
The repair worker can request review; it cannot add/select a new authority or
approve its own response through an assignment command.

## Request, independent response, and admission

After D0 automatically starts the repair window, the assigned worker requests a
source-shape review at actual current source:

```sh
python3 -B blind_study.py request-domain-review \
  --assignment /ABS/run/arms/T1/A/assignment.json --profile ios
```

This creates an immutable `domain-requests/ID/request.json` and exact raw
`component.source` capsule. The request binds task/arm/profile, full source
fingerprint, actual installed component path/SHA/bytes, current active config,
parent approval, unchanged policy digest and public readset. The helper never
creates an approved future source revision. A native ticket may not be pending.

The independent reviewer reads the source-shape material and emits a new response
directory under its predeclared root. It contains exactly these sealed members:

* `component.source`: exactly the actual reviewed request component bytes.
* `approval.json`: parent approval with exactly one new revision entry for the
  requested platform; every prior revision is retained byte-for-byte as JSON.
* `review.json`: an explicit independent source-shape observation, as below.

The new revision value must be exactly
`{"sha256": ACTUAL_COMPONENT_SHA256, "bytes": ACTUAL_COMPONENT_BYTES}`.
There are no wildcards, future SHA declarations, duplicate aliases, rewritten
old entries, extra unreviewed revisions, or additions to another platform.

`review.json` fields:

| Field | Required value |
|---|---|
| `version`, `kind` | `1`, `independent-source-domain-review` |
| `reviewer_id`, `scope`, `decision` | Registered ID, `source_shape_only`, `approved` |
| `request_id`, `request_sha256` | Exact generated request ID and request file-byte SHA |
| `study_id`, `task`, `arm`, `profile`, `platform` | Exact request values |
| `source_sha256` | Request `source.content_sha256` |
| `component` | Exact request `{path, sha256, bytes}` |
| `parent_approval_sha256`, `policy_sha256` | Exact request values |
| `config_sha256` | Request `active_config.sha256` |
| `proposed_approval_sha256` | Canonical JSON digest of sealed `approval.json` |
| `reason` | Nonempty original independent source-shape observation |

The response's `SEAL.json` is:

```json
{
  "version": 1,
  "kind": "source-domain-review-seal",
  "reviewer_id": "shape-reviewer",
  "files": {
    "review.json": "FILE_SHA256",
    "approval.json": "FILE_SHA256",
    "component.source": "FILE_SHA256"
  }
}
```

The trusted operator separately records delivery provenance:

```json
{
  "version": 1,
  "kind": "independent-source-domain-review-provenance",
  "request_id": "REQUEST_ID",
  "review_seal_sha256": "SEAL_FILE_SHA256",
  "reviewer_id": "shape-reviewer",
  "operator_id": "study-controller",
  "independent_of_repair": true,
  "delivery_reference": "Original independent reviewer delivery reference"
}
```

Only the controller admission command publishes the next config version:

```sh
python3 -B blind_study.py admit-domain-review --run /ABS/run \
  --request-id REQUEST_ID \
  --seal /ABS/independent/shape-reviewer/RESPONSE/SEAL.json \
  --seal-sha256 SEAL_FILE_SHA256 \
  --provenance /ABS/controller/DELIVERY.json \
  --provenance-sha256 DELIVERY_FILE_SHA256
```

Admission checks exact actual source against the immutable request and independent
capsule. It requires the same frozen `coverage_domain.policy()` digest. That
documented digest removes only approval metadata (`approved_at_utc`, `approved_by`)
and per-platform approved revisions; all host, geometry, fixture, oracle, design
and environment policy remains unchanged.

The original config is never edited. The helper copies the independently sealed
approval verbatim and emits `config-versions/ID/config.json` with **only**
`coverage_domain_ref` changed. Every other config field, including plan, policy,
fixtures, bridge, expected values, provider, environment, source roots, workflow
and resources, remains equal. Immutable public inputs retain their original pins.
Original requests, reviewer members, seal and provenance stay retained and are
rechecked, along with every config-version inventory, at queue/serve/self/cohort
boundaries. A queued ticket snapshots its exact active configs; admission cannot
switch a version while any ticket for that arm is pending.

The source deadline never resets. Review/admission elapsed time is recorded and
remains inside that arm's D0-enqueue → final-self-seal wall. A read-only review at
already locked exact bytes is allowed after the source deadline; it cannot unlock
or edit source. Admission and new review requests reject after final self-seal or
cohort seal. The treatment still resolves its own default measured repair/state;
the old control receives only its old documented previous/history transport.
The frozen treatment context deliberately excludes revision observations while
binding policy, so appending a same-policy approval cannot clear an old repair.

## Mandatory pure public profile admission

Each arm may configure `profile_admissions`; when present it must cover every
public profile, and both arms of the pair must use this mechanism:

```json
{
  "profile_admissions": {
    "ios": {
      "script": "/ABS/public/admit_profile.py",
      "root": "/ABS/public",
      "approval": "/ABS/public/PROFILE-APPROVAL.json",
      "approval_sha256": "CANONICAL_APPROVAL_SHA256",
      "dependencies": []
    },
    "android": {
      "script": "/ABS/public/admit_profile.py",
      "root": "/ABS/public",
      "approval": "/ABS/public/PROFILE-APPROVAL.json",
      "approval_sha256": "CANONICAL_APPROVAL_SHA256",
      "dependencies": []
    }
  }
}
```

The preapproved script must be a pure config verifier, with all local dependencies
declared and pinned. It exports:

```python
verify(root: pathlib.Path, approval: dict, approval_sha: str,
       platform: str, config: dict) -> dict
```

It raises on rejection and returns at least
`{"status":"admitted_profile", "platform": ACTUAL_PLATFORM, ...}` on admission.
`approval_sha256` is a canonical-object digest; script, approval and declared
dependency file bytes are also pinned in the immutable public readset.

The default `serve` path invokes this hook on the **exact active config before
every forwarding operation**, and again when admitting a source-domain config
version. Platform comes exclusively from the actual config's
`plan.design_contract.platform`; there is no caller-selected platform argument.
An inconsistent separate `config.platform` rejects. Configured profiles must
include both actual iOS and Android namespaces. A `profile-admission.json` receipt
pins config file/canonical SHA, verifier code, approval file/canonical SHA,
guarded plan/lock/policy/routes/environment/fixtures/bridge, derived platform and
returned verdict. Public pins/source are rechecked after the hook and before
forwarding. A hook rejection remains a recorded failure and never launches SDK.

This guard only admits or rejects the public representation. It cannot remove,
filter, waive or mark passed any responsibility, task, F/U or unsupported native
claim. It cannot change the oracle through source-domain admission.

Canonical digest everywhere above is SHA256 of UTF-8
`json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
allow_nan=False)`. File-byte SHA and canonical JSON SHA are deliberately distinct.
