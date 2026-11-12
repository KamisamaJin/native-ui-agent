#!/usr/bin/env python3
"""Seal the bounded independent HOST/SIM review without altering its inputs."""
import hashlib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
EXPECTED = "f9495569e2ae23a6511f47918d5ae79617243ed6efbd1bd0860ce6a22d626d8a"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def load(path):
    return json.loads(Path(path).read_text())


def put(path, value):
    with Path(path).open("x") as stream:
        stream.write(value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True) + "\n")


helper = ROOT / "business-tools/blind_study.py"
assert sha(helper) == EXPECTED
freeze = load(ROOT / "business-tools/FREEZE.json")
freeze_checks = {rel: {"expected_sha256": wanted, "actual_sha256": sha(ROOT / "business-tools" / rel)}
                 for rel, wanted in freeze["files"].items()}
assert all(v["actual_sha256"] == v["expected_sha256"] for v in freeze_checks.values())
inputs = ["PROTOCOL.json", "native_envelope.py", "measure.py", "operators/whole-study-meter-spec-v2.json",
          "business-tools/FREEZE.json", *["business-tools/" + rel for rel in freeze["files"]],
          "candidate-v13.9/scripts/coverage_domain.py", "candidate-v13.9/scripts/ui_loop.py", "candidate-v13.9/scripts/design_contract.py",
          "baseline-v12.6-common-6/scripts/coverage_domain.py", "baseline-v12.6-common-6/scripts/ui_loop.py"]
readset = {"kind": "independent-public-readset", "scope": "Only original helper/public protocol, common supervisors/spec and needed public API scripts. No business design, business implementation, real SDK/native execution, timing outcomes, private oracle or Git access.",
           "files": {str(ROOT / rel): sha(ROOT / rel) for rel in sorted(set(inputs))},
           "original_helper_freeze_matches": freeze_checks,
           "coverage_domain_identical_in_both_frozen_apis": sha(ROOT / "candidate-v13.9/scripts/coverage_domain.py") == sha(ROOT / "baseline-v12.6-common-6/scripts/coverage_domain.py")}
put(OUT / "READSET.json", readset)

original = load(OUT / "original-15-tests.json")
independent = load(OUT / "independent-edge-tests.json")
correction = load(OUT / "barrier-observer-correction/RESULT.json")
assert original["passed"] and original["tests_run"] == 15
assert independent["tests_run"] == 10 and independent["failures"] == 1 and independent["errors"] == 0
failed = [row for row in independent["tests"] if row["status"] != "passed"]
assert len(failed) == 1 and "test_full_five_pair_barrier" in failed[0]["test"]
assert correction["passed"] and correction["tests_run"] == 1
observed = load(OUT / "observations.json")
assert observed["source_domain_transport_blocker"]["status"] == "reproduced"
integration = load(OUT / "barrier-observer-correction/observations.json")["all_five_pair_integration"]
assert integration["self_seals"] == 10
assert len(set(integration["envelope_record_basenames"])) == 40
assert len(integration["hidden_configs_opened_after_authorization"]) == 20

report = """# Independent controller forward review

**Verdict: changes required before study admission.** The original helper is frozen at SHA-256 `f9495569e2ae23a6511f47918d5ae79617243ed6efbd1bd0860ce6a22d626d8a`. Its generic source-domain approval transport is incomplete for a real source repair. This review does not approve business study execution.

The original 15 HOST/SIM tests pass. All 10 independent checks pass after correcting one review-harness observer error. The initial 9-pass/1-failure outcome remains in `independent-edge-tests.json`: the observer initially classified `Path.open(mode='w')` used to create synthetic hidden fixtures as a read. The corrected observer honors keyword mode, and only the affected all-five-pair check was rerun. No candidate code changed. `original-15-tests.json`, both runner versions, correction outputs, and all independent synthetic fixture packets are retained.

## Blocking integration finding — source-domain approval transport

Both frozen APIs have identical `coverage_domain.py`. Its `prepare()` requires the installed component's exact SHA and bytes in `approved_component_revisions` (lines 46–75). A repaired component is correctly rejected with `Current source needs an independent closed-domain approval`. Its `policy()` deliberately excludes source revision approvals from design rules (lines 34–43), so a separate independent revision approval can preserve the exact policy digest.

The synthetic reproduction first admits an initial source, completes D0, and repairs the component. It then appends a separately stored revision approval without changing policy, bridge, fixtures, expectations, or source scope. The exact frozen `prepare()` accepts that repaired source when given the new reference. The original helper, however, always selects the original `public_configs` path in `build_command()` (lines 416–425), while `verify_pins()` rejects changing its reference with `Admitted public input/config changed` (lines 225–231). Leaving the original config intact retains the old approval and correctly fails the source gate. A separate append-only approval has no admitted active-config channel.

This is a case-agnostic transport blocker, not a request to waive source approval or change a business oracle. The helper manifest has no source-domain-admission command or versioned active config facility. Predeclaring unknown future source SHAs or disabling `coverage_domain_ref` would not resolve it legitimately. The original frozen helper and originals must remain intact; a new helper candidate is required.

The generic repair should admit an independently sealed, source-shape-only approval as an append-only config version. Preserve the immutable original config and all prior approvals; allow only `coverage_domain_ref` to change. Bind the actual installed component path, current SHA and byte count to the same task/arm/source roots. Verify identical `coverage_domain.policy()` digest, bridge, fixture, provider, design/plan/expected/environment identities and existing workflow/resources. Reject missing or self-issued authority, wrong arm/path/SHA/bytes, removed or rewritten old revisions, duplicate revision identities, policy drift, queue-time version drift, and tampered config/approval/seal chains. Apply the same transport to both APIs, preserve baseline config shape, charge approval time in the arm's endpoint, retain the 1200-second source deadline, and recheck the chain before service, self-seal and hidden authorization.

The domain reproduction uses synthetic JSON, a synthetic reviewed provider tree and a finite fixture encoding identity. Only the module location and supported fixture encoding identity are supplied for HOST/SIM. The frozen `prepare()`, `pinned()` and `policy()` logic and actual component SHA/byte matching execute unchanged. This demonstrates the transport mismatch; it is not native host conformance, a real independent domain approval, behavior acceptance, or business evidence.

## Procedural checks

- All five initial pairs and all ten capsules exist before D0; mismatched initial bytes and pre-D0 edits fail closed. Admitted initial sources are read-only.
- Exactly two diagnostic bundles are available per arm including D0. Failed and interrupted tickets remain charged/retained; no automatic retry or later FIFO execution bypasses an interrupted started ticket.
- A complete successful D0 bundle automatically starts the 1200-second source window at result readiness. Queue wait is recorded; the other arm has no premature repair anchor. Review and late acknowledgment do not reset it. A synthetic iteration of the actual host-only guard freezes at expiry, records enforcement lateness, and prevents late unlocking. Original tests also reject late source for acceptance.
- Public configs, declared plan/lock/routes/fixtures/bridge/policy/environment inputs, frozen tool scripts, common envelope/meter/spec, protocol and prerequisites detect byte drift. Queued source drift, final source tampering, original evidence tampering and final self-claim tampering block progress. Final source sealing and self-sealing are irrevocable through the CLI.
- The old API receives program-selected original `--previous`, its SHA, and pinned cycle history. The stateful API receives its default transport without previous/history/fresh flags.
- Actual final `status: accepted` and complete retirement proof are both required. An unresolved final remains unresolved after a separate successful retirement; self-claim text and zero exit do not grant delivery acceptance.
- Five pairs complete sequentially. A full synthetic run seals all ten arms before the first of twenty hidden config reads; durable authorization precedes every read. Forty per-profile envelope record basenames are distinct.

No further candidate phase failure was established in this bounded review. The integrity model remains the documented procedural model for cooperating operators; chmod and hash chains are not an OS sandbox against a source owner deliberately bypassing the controller. All results are HOST/SIM only: no helper `execute()` forwarding, subprocess forwarding, SDK, simulator, render, private design/implementation or Git operation occurred. No speed or business quality conclusion follows.

`REVIEW.json` is the effective review outcome; `RESULT.json` and the first independent result remain raw initial artifacts. `READSET.json` identifies the exact public inputs and confirms every original candidate freeze member, including the original HOST/SIM result, is unchanged. `SEAL.json` binds this report and the complete retained artifact inventory.
"""
put(OUT / "REPORT.md", report)
effective = {"kind": "independent-HOST/SIM-controller-forward-review", "version": 1, "verdict": "changes_required_before_study_admission",
             "candidate_helper_sha256": EXPECTED, "original_candidate_freeze_preserved": True,
             "effective_checks": {"original_passed": 15, "independent_passed": 10, "total": 25, "candidate_phase_test_failures": 0,
                                  "initial_review_harness_failures_retained": 1, "corrected_affected_check_passed": True},
             "blocking_findings": [{"id": "SOURCE-DOMAIN-TRANSPORT", "priority": "blocking", "status": "reproduced",
                 "description": "No append-only admitted active-config path for a separately approved post-D0 source revision under unchanged domain policy.",
                 "proof": {"path": str(OUT / "observations.json"), "sha256": sha(OUT / "observations.json")}}],
             "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False,
             "business_quality_or_performance_claim": False,
             "raw_results_preserved": ["original-15-tests.json", "independent-edge-tests.json", "RESULT.json", "barrier-observer-correction/RESULT.json"],
             "report": {"path": str(OUT / "REPORT.md"), "sha256": sha(OUT / "REPORT.md")},
             "readset": {"path": str(OUT / "READSET.json"), "sha256": sha(OUT / "READSET.json")}}
put(OUT / "REVIEW.json", effective)

excluded = {"EVIDENCE-INVENTORY.json", "SEAL.json"}
inventory = {p.relative_to(OUT).as_posix(): sha(p) for p in sorted(OUT.rglob("*")) if p.is_file() and p.relative_to(OUT).as_posix() not in excluded}
put(OUT / "EVIDENCE-INVENTORY.json", {"kind": "retained-independent-review-file-inventory", "files": inventory})
seal = {"kind": "independent-controller-review-seal", "version": 1, "at_unix": time.time(),
        "candidate_helper_sha256": EXPECTED, "verdict": effective["verdict"],
        "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False,
        "readset_sha256": sha(OUT / "READSET.json"), "report_sha256": sha(OUT / "REPORT.md"), "review_sha256": sha(OUT / "REVIEW.json"),
        "inventory_path": str(OUT / "EVIDENCE-INVENTORY.json"), "inventory_sha256": sha(OUT / "EVIDENCE-INVENTORY.json"),
        "inventory_members": len(inventory), "inventory_canonical_sha256": hashlib.sha256(canonical(inventory)).hexdigest(),
        "original_candidate_freeze_preserved": True}
put(OUT / "SEAL.json", seal)
assert all(sha(OUT / rel) == wanted for rel, wanted in inventory.items())
for path in OUT.rglob("*"):
    if path.is_file():
        path.chmod(0o444)
for path in sorted([p for p in OUT.rglob("*") if p.is_dir()], key=lambda p: len(p.parts), reverse=True):
    path.chmod(0o555)
OUT.chmod(0o555)
print(json.dumps({"review": str(OUT / "REVIEW.json"), "seal": str(OUT / "SEAL.json"), "seal_sha256": sha(OUT / "SEAL.json"), "checks_passed": 25, "inventory_members": len(inventory), "verdict": effective["verdict"]}))
