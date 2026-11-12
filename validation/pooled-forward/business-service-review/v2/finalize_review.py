#!/usr/bin/env python3
"""Seal v2 independent HOST/SIM findings; preserve all earlier raw records."""
import hashlib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
HELPER = "cd2ab17f43426096c2ac4c322c5a09310d2d7d2fa9d51c453f3b52cd7083aaf8"
DOMAIN = "fd82356e7b76a8b3099351d6de4d19259eeb241dd99e06b1c4efad3668ba7c8c"
FREEZE = "258edc5d22c538587d1b3ff4b950b8c34239ff666325bedbe520d520743929be"
OLD_SEAL = "90644daf3935891c9103cdd1eb8ab0fed33df4ef3533568b3018de1ca68bb1f3"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def put(path, value):
    with Path(path).open("x") as stream:
        stream.write(value if isinstance(value, str) else json.dumps(value, sort_keys=True, indent=2) + "\n")


assert sha(ROOT / "business-tools-v2/blind_study.py") == HELPER
assert sha(ROOT / "business-tools-v2/source_domain.py") == DOMAIN
assert sha(ROOT / "business-tools-v2/FREEZE.json") == FREEZE
freeze_checks = {}
for folder in ["business-tools", "business-tools-v2"]:
    frozen = load(ROOT / folder / "FREEZE.json")
    checks = {rel: {"expected_sha256": wanted, "actual_sha256": sha(ROOT / folder / rel)} for rel, wanted in frozen["files"].items()}
    assert all(v["actual_sha256"] == v["expected_sha256"] for v in checks.values())
    freeze_checks[folder] = checks
assert sha(OUT.parent / "SEAL.json") == OLD_SEAL
old_inventory_path = OUT.parent / "EVIDENCE-INVENTORY.json"
old_inventory = load(old_inventory_path)["files"]
assert all(sha(OUT.parent / path) == wanted for path, wanted in old_inventory.items())
inputs = ["PROTOCOL.json", "native_envelope.py", "measure.py", "operators/whole-study-meter-spec-v2.json",
          "candidate-v13.9/scripts/coverage_domain.py", "candidate-v13.9/scripts/capture_validity.py", "candidate-v13.9/scripts/workflow_state.py",
          "baseline-v12.6-common-6/scripts/coverage_domain.py", "baseline-v12.6-common-6/scripts/feedback_loop.py"]
for folder in freeze_checks:
    inputs += [folder + "/FREEZE.json", *[folder + "/" + rel for rel in freeze_checks[folder]]]
readset = {"kind": "independent-public-v2-delta-readset", "files": {str(ROOT / rel): sha(ROOT / rel) for rel in sorted(set(inputs))},
           "frozen_candidate_checks": freeze_checks,
           "predecessor_review": {"seal_path": str(OUT.parent / "SEAL.json"), "seal_sha256": OLD_SEAL,
                                  "inventory_sha256": sha(old_inventory_path), "all_original_members_unchanged": True, "original_inventory_members": len(old_inventory)},
           "scope": "Only approved public controller/protocol/supervisor/API inputs and prior independent review. No business data, design/implementation, oracle, SDK, native outcome, timing result or Git access."}
put(OUT / "READSET.json", readset)

phase = load(OUT / "original-15-tests.json")
domain = load(OUT / "frozen-v2-13-tests.json")
independent = load(OUT / "independent-delta-tests.json")
correction = load(OUT / "context-stub-correction/RESULT.json")
assert phase["passed"] and phase["tests_run"] == 15
assert domain["passed"] and domain["tests_run"] == 13
assert independent["tests_run"] == 10 and independent["failures"] == 0 and independent["errors"] == 1
failed = [v for v in independent["tests"] if v["status"] != "passed"]
assert len(failed) == 1 and "test_frozen_default_context" in failed[0]["test"] and "environment_dependencies" in failed[0]["detail"]
assert correction["passed"] and correction["tests_run"] == 1
details = load(OUT / "observations.json")
context = load(OUT / "context-stub-correction/observations.json")["frozen_default_context_and_pending_repair"]
assert len(details["both_api_active_config_transport"]) == 4
assert context["frozen_context_and_Session_methods_unchanged"]

report = """# Independent v2 controller forward review

**Verdict: PASS for the reviewed shared controller transport and configured profile-admission delta (HOST/SIM only).** The original source-domain transport blocker is resolved in the synthetic forward checks. This is not authorization of actual business cases, native execution, performance, or business quality.

Frozen helper SHA-256: `cd2ab17f43426096c2ac4c322c5a09310d2d7d2fa9d51c453f3b52cd7083aaf8`. Frozen `source_domain.py`: `fd82356e7b76a8b3099351d6de4d19259eeb241dd99e06b1c4efad3668ba7c8c`. Freeze file: `258edc5d22c538587d1b3ff4b950b8c34239ff666325bedbe520d520743929be`.

All 15 original phase tests, all 13 frozen v2 domain/profile tests, and all 10 independent delta checks pass: 38 effective checks. The initial independent run had 9 passes and one review-harness NameError: its SDK-free environment observer stub was named `dependency_environment`, while the frozen context function calls `environment_dependencies`. Only that affected test was rerun after correcting the stub name. Both runner versions, the original raw error, corrected result, and all independent synthetic fixture artifacts are retained. No candidate file changed.

The targeted checks establish:

- Both baseline and stateful APIs, on both iOS and Android profile namespaces, request exact actual-source review capsules and admit one independently sealed SHA/byte revision under an unchanged `coverage_domain.policy()` digest. Original configs remain unchanged; active versions differ only in `coverage_domain_ref`. Final transport selects those exact active files. Baseline retains original previous/SHA/history arguments; treatment retains its ordinary default transport.
- The admission chain rechecks registry bytes and reviewer directory inode, request and component capsule, independent response/seal/provenance, original/config-version members, parent approval, actual component path/SHA/bytes, prior revisions and policy. Tests reject stale source, wrong task/arm/component, foreign capsules even after resealing, future/wildcard SHAs, byte mismatches, duplicate aliases, removed/rewritten revisions, additional unreviewed/platform revisions, forged pins, unregistered authority, false independence provenance, and symlinked original seal paths. Ownership, platform, oracle, bridge, fixture and provider/config mutations fail closed.
- Pending service tickets prevent source-domain review/config switches. Requests/admissions reject after final self/cohort seal. A review at already locked source after the source deadline is admitted read-only at exactly those bytes. The original source lock and 1200-second deadline remain unchanged, no new unlock event appears, and the tested 100-second review interval is recorded without resetting the budget. Existing phase tests retain all-five initial identity, sequential tasks, two diagnostics including failures, FIFO/interrupted-ticket handling, final accepted-status/retirement requirements and all-ten hidden barrier.
- The exact frozen treatment `capture_validity.context()` function yields equal context before/after same-policy revision approval. The exact frozen workflow `Session` loads the same existing repair task, records the real synthetic changed-file handoff as `patched_needs_native_retest`, and preserves both task and pending completion across reopen. Source approval does not clear a repair or grant a retest pass. Only host/SDK observer dependencies, source-model plumbing and native clock identity were supplied as synthetic fixtures; no SDK observer or native cycle was executed.
- For configured profiles, the default `serve()` path invokes the pinned pure verifier on the exact active config before its forwarding callback. During active config admission it uses the new config as well. Platform is derived from the actual plan, demonstrated with opaque profile IDs; an inconsistent explicit config platform rejects. Receipts bind actual config, plan-derived platform, verifier and approved inputs. Wrong frozen fixtures, declared dependency drift, and a deliberately side-effecting verifier are retained failures before any forwarding. No responsibility, native claim, F/U, task, or oracle is filtered, removed, waived or marked passed by this hook.

Authority remains the documented procedural model: the predeclared independent reviewer registry plus a separately pinned trusted-operator delivery attestation. A hash alone does not prove independent authorship, and this is not an OS-owner or cryptographic-identity defense. Actual review origin and purity of the preapproved verifier remain study-operator responsibilities. The controller still checks exact pins and source after the verifier and before forwarding. The hook is mandatory when configured and applied to both arms; this review does not validate any real business-profile approval.

No further blocker was established in the bounded delta review. Every original v1 and new v2 freeze member, including both original HOST/SIM results, is byte-identical to its freeze. All 2439 members of the original sealed v1 review and its seal are unchanged; its 25-check outcome and original blocker report remain historical records. `READSET.json` records these checks. New artifacts are exclusively under this `v2` directory.

All evidence is HOST/SIM. Helper `execute()`, subprocess forwarding, SDK, simulator, render, actual business data/design/source/oracles, timing outcomes and Git operations were excluded. The service receiver is synthetic JSON transport. No native, speed or business-quality result follows. `REVIEW.json` is the effective v2 outcome; `RESULT.json` and initial test outputs are preserved raw artifacts. `SEAL.json` binds the exact report, readset, effective outcome and complete retained v2 file inventory.
"""
put(OUT / "REPORT.md", report)
effective = {"kind": "independent-v2-HOST/SIM-controller-forward-review", "version": 1,
             "verdict": "pass_reviewed_shared_controller_delta_HOST_SIM_only", "original_source_domain_transport_blocker_resolved": True,
             "candidate_helper_sha256": HELPER, "source_domain_sha256": DOMAIN, "candidate_freeze_file_sha256": FREEZE,
             "effective_checks": {"original_phase_passed": 15, "frozen_v2_domain_profile_passed": 13, "independent_delta_passed": 10,
                                  "total_passed": 38, "candidate_test_failures": 0, "initial_review_harness_error_retained": 1, "corrected_affected_check_passed": True},
             "blocking_findings": [], "original_v1_candidate_and_review_preserved": True, "v2_freeze_preserved": True,
             "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False,
             "actual_business_data_access": False, "business_study_authorized": False, "business_quality_or_performance_claim": False,
             "report": {"path": str(OUT / "REPORT.md"), "sha256": sha(OUT / "REPORT.md")},
             "readset": {"path": str(OUT / "READSET.json"), "sha256": sha(OUT / "READSET.json")},
             "retained_raw_results": ["original-15-tests.json", "frozen-v2-13-tests.json", "independent-delta-tests.json", "context-stub-correction/RESULT.json", "RESULT.json"]}
put(OUT / "REVIEW.json", effective)
excluded = {"SEAL.json", "EVIDENCE-INVENTORY.json"}
inventory = {p.relative_to(OUT).as_posix(): sha(p) for p in sorted(OUT.rglob("*")) if p.is_file() and p.relative_to(OUT).as_posix() not in excluded}
put(OUT / "EVIDENCE-INVENTORY.json", {"kind": "retained-independent-v2-review-file-inventory", "files": inventory})
seal = {"kind": "independent-v2-controller-review-seal", "version": 1, "at_unix": time.time(), "verdict": effective["verdict"],
        "candidate_helper_sha256": HELPER, "source_domain_sha256": DOMAIN, "candidate_freeze_file_sha256": FREEZE,
        "original_v1_review_seal_sha256": OLD_SEAL, "original_v1_review_preserved": True,
        "report_sha256": sha(OUT / "REPORT.md"), "review_sha256": sha(OUT / "REVIEW.json"), "readset_sha256": sha(OUT / "READSET.json"),
        "inventory_path": str(OUT / "EVIDENCE-INVENTORY.json"), "inventory_sha256": sha(OUT / "EVIDENCE-INVENTORY.json"),
        "inventory_members": len(inventory), "inventory_canonical_sha256": hashlib.sha256(canonical(inventory)).hexdigest(),
        "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False}
put(OUT / "SEAL.json", seal)
assert all(sha(OUT / rel) == wanted for rel, wanted in inventory.items())
for path in OUT.rglob("*"):
    if path.is_file(): path.chmod(0o444)
for path in sorted([p for p in OUT.rglob("*") if p.is_dir()], key=lambda p: len(p.parts), reverse=True): path.chmod(0o555)
OUT.chmod(0o555)
print(json.dumps({"review": str(OUT / "REVIEW.json"), "seal": str(OUT / "SEAL.json"), "seal_sha256": sha(OUT / "SEAL.json"), "checks_passed": 38, "inventory_members": len(inventory), "verdict": effective["verdict"]}))
