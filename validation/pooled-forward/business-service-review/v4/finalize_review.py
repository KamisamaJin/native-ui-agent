#!/usr/bin/env python3
"""Seal bounded v4 recovery review while retaining v3's original failure."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
HELPER = "1a52cc62be5cee0bad34fefe8b54a7479761ca5ea5e8981937a8a1ad11ae6b05"
FREEZE = "9a24b9eca414f1bb91e92695b7e74d1b7cd384d7596456c08c78758559fba114"
COUNTEREXAMPLE = "ac64bb01acc5598c3f37b903eebb97e3bd376d7f25606bc6943c623c1d19b6e8"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def canonical(v): return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
def put(path, value):
    with Path(path).open("x") as stream:
        stream.write(value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True) + "\n")


assert sha(ROOT / "business-tools-v4/blind_study.py") == HELPER
assert sha(ROOT / "business-tools-v4/FREEZE.json") == FREEZE
assert sha(OUT.parent / "v3/LOST-ANCHOR-COUNTEREXAMPLE.json") == COUNTEREXAMPLE
freezes = {}
for folder in ["business-tools", "business-tools-v2", "business-tools-v3", "business-tools-v4"]:
    frozen = load(ROOT / folder / "FREEZE.json")
    files = {rel: {"expected_sha256": value, "actual_sha256": sha(ROOT / folder / rel)} for rel, value in frozen["files"].items()}
    assert all(v["expected_sha256"] == v["actual_sha256"] for v in files.values())
    freezes[folder] = {"freeze_sha256": sha(ROOT / folder / "FREEZE.json"), "files": files}
predecessors = {}
for folder, expected in [(OUT.parent, "90644daf3935891c9103cdd1eb8ab0fed33df4ef3533568b3018de1ca68bb1f3"),
                         (OUT.parent / "v2", "7e48844368953e34afe999fc1ec8859bb37b4bfa7ebf6340e82b669447236b50"),
                         (OUT.parent / "v3", "7009da12d009fa408b1281f4a37dae475d3eb06d79fc652adfcb4970675ec32e")]:
    assert sha(folder / "SEAL.json") == expected
    inventory = load(folder / "EVIDENCE-INVENTORY.json")["files"]
    assert all(sha(folder / rel) == wanted for rel, wanted in inventory.items())
    predecessors[str(folder)] = {"seal_sha256": expected, "inventory_sha256": sha(folder / "EVIDENCE-INVENTORY.json"), "all_members_unchanged": True, "members": len(inventory)}


def functions(path):
    values = {}
    for node in ast.parse(Path(path).read_text()).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)): values[node.name] = ast.dump(node, include_attributes=False)
        elif isinstance(node, ast.ClassDef):
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)): values[node.name + "." + method.name] = ast.dump(method, include_attributes=False)
    return values


before = functions(ROOT / "business-tools-v3/blind_study.py")
after = functions(ROOT / "business-tools-v4/blind_study.py")
changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
allowed = {"Study.expire", "Study.recover_d0_anchors", "Study.d0_complete", "Study.d0_proof", "Study.serve", "watch", "main"}
assert set(changed) <= allowed
unchanged = ["Study.profile_admission", "Study.domain_authority", "Study.active_configs", "Study.request_domain_review", "Study.admit_domain_review", "Study._admit_domain_review",
             "Study.build_command", "Study.execute", "Study.check_request_integrity", "Study.feedback_ready"]
assert all(before[k] == after[k] for k in unchanged)
assert sha(ROOT / "business-tools-v4/source_domain.py") == sha(ROOT / "business-tools-v3/source_domain.py")
for rel in ["manifest.schema.json", "manifest.example.json", "test_blind_study.py", "test_domain_admission.py", "test_terminal_d0.py"]:
    assert sha(ROOT / "business-tools-v4" / rel) == sha(ROOT / "business-tools-v3" / rel)
put(OUT / "FUNCTION-DELTA.json", {"changed_or_added": changed, "source_domain_file_unchanged": True, "manifest_schema_example_and_old_tests_unchanged": True,
                                  "unchanged_methods": unchanged, "unchanged_method_AST_sha256": {key: hashlib.sha256(after[key].encode()).hexdigest() for key in unchanged}})
readset = {"kind": "independent-bounded-v4-public-readset", "frozen_candidates": freezes, "predecessor_reviews": predecessors,
           "preserved_v3_counterexample": {"path": str(OUT.parent / "v3/LOST-ANCHOR-COUNTEREXAMPLE.json"), "sha256": COUNTEREXAMPLE},
           "protocol": {"path": str(ROOT / "PROTOCOL.json"), "sha256": sha(ROOT / "PROTOCOL.json")},
           "function_delta": {"path": str(OUT / "FUNCTION-DELTA.json"), "sha256": sha(OUT / "FUNCTION-DELTA.json")},
           "optional_business_profile_adapter_or_design_data_read": False,
           "scope": "Frozen common helper/public docs/tests/protocol and prior sealed independent reviews only. No actual business source/design/oracle, SDK/native/timing outcome or Git access."}
put(OUT / "READSET.json", readset)
frozen = load(OUT / "frozen-anchor-13-tests.json")
independent = load(OUT / "independent-recovery-tests.json")
details = load(OUT / "observations.json")
assert frozen["passed"] and frozen["tests_run"] == 13
assert independent["passed"] and independent["tests_run"] == 6
assert len(details["original_v3_counterexample_closed"]) == 2
assert all(v["source_frozen_before_D1_and_unlock"] for v in details["original_v3_counterexample_closed"])

report = """# Independent v4 first-D0 recovery review

**Verdict: PASS for the bounded shared-controller crash-recovery delta (HOST/SIM only).** The original v3 lost-anchor counterexample is closed for both arms. This qualifies the reviewed controller delta; it does not approve actual business inputs, native results, quality, performance, or any other study gate.

Frozen helper SHA-256: `1a52cc62be5cee0bad34fefe8b54a7479761ca5ea5e8981937a8a1ad11ae6b05`. Freeze file: `9a24b9eca414f1bb91e92695b7e74d1b7cd384d7596456c08c78758559fba114`.

All thirteen frozen recovery-cut tests and six independent targeted checks pass: **19 checks, no failures or errors**. The original forty inherited tests and the author's fifty-three-test QA are retained frozen artifacts; this bounded independent run executes the focused recovery suite and independent cases, without re-auditing the SUT.

The exact original v3 boundary was replayed independently for A and B: complete terminal failed-D0 outcomes and immutable result exist; execution stops immediately before `repair_started`; the controller restarts at original readiness +1301 seconds. V4 recovers only the original first request ID and aggregate hash, original monotonic/wall finish times, and their fixed +1200 deadline. Before a D1 enqueue or source unlock can proceed, it freezes the unchanged initial source. D1 is rejected, no unlock event appears, and no other arm starts a clock. The preserved v3 failure remains untouched; `observations.json` records the new v4 passing replay and its exact artifacts.

Further independent checks establish:

- A cut immediately after complete aggregate persistence but before `request_finished` recovers the finish event and original anchor. Acknowledgment at +275 leaves exactly 925 source seconds. Both APIs can then perform an actual synthetic source-only repair, D1 and final collection without resetting the anchor. Baseline retains original previous/SHA/history transport; treatment uses its default transport. A final source lock remains irrevocable.
- Cuts before write-ahead preparation, after preparation with no aggregate, and during truncated aggregate persistence stay pending/locked. Recovery does not create a clock, overwrite retained bytes, continue, or silently retry. The aggregate must match its original prepared SHA and every originally pinned profile outcome.
- An outcome explicitly missing when the aggregate was prepared cannot be added later to upgrade the first D0. Even a successful D1 cannot create a source window from that incomplete first proof.
- Corrupting an existing anchor's original-result hash rejects both foreground acknowledgment and a restarted watchdog. A stable watchdog cache, after validating the original proof, freezes at the same original deadline on its next cached iteration; it does not derive time from guard startup or cache refresh.

The frozen thirteen additionally cover before/after result, completion and anchor publication, guard startup failure, finite original timestamp/hash binding, the exact late-D1 extension, correct remaining time, tampered aggregate/outcome proofs, and a legitimate D1 queued within the original window but served after expiry. Honest terminal failed D0 remains a repair opportunity, with failure logs and F/U retained; no native success, image, accepted status or delivery is invented.

AST verification confirms source-domain admission, configured profile admission, both API command builders/forwarding, current request-integrity checks and `feedback_ready` remain unchanged from v3. `source_domain.py`, manifest schema/example and the old three test sources are byte-identical. The changed functions are limited to first-D0 proof/recovery, deadline enforcement, aggregate preparation, watchdog validation and status recovery; exact names/digests are in `FUNCTION-DELTA.json`. No responsibility filtering, frozen service, oracle, ownership, resource or study-policy rewrite occurred.

All four candidate freezes and all three earlier sealed independent reviews remain byte-identical, including the v3 failure/counterexample. `READSET.json` records exact checks. The v4 drivers, all independent synthetic fixtures, test outputs and report are retained under this directory and bound by `SEAL.json`.

All evidence is HOST/SIM. Helper `execute()` and subprocess forwarding were blocked; no SDK, simulator, native/render execution, actual business source/design/oracle, real timing outcome or Git access occurred. The optional business profile adapter metadata was not needed and was not read. Service packets are synthetic transport fixtures. Actual business D0 continues to require all its other independently approved preconditions and all-ten initial-source admission.
"""
put(OUT / "REPORT.md", report)
effective = {"kind": "independent-v4-first-D0-recovery-review", "version": 1, "verdict": "pass_bounded_shared_controller_recovery_HOST_SIM_only",
             "candidate_helper_sha256": HELPER, "candidate_freeze_file_sha256": FREEZE, "original_v3_counterexample_closed_for_both_arms": True,
             "checks": {"frozen_recovery_passed": 13, "independent_targeted_passed": 6, "total_passed": 19, "failures": 0, "errors": 0}, "blocking_findings": [],
             "all_predecessor_candidates_reviews_and_v3_counterexample_preserved": True, "domain_profile_and_API_transport_ASTs_unchanged": True,
             "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False, "actual_business_data_access": False,
             "business_study_authorized": False, "business_quality_or_performance_claim": False,
             "report_sha256": sha(OUT / "REPORT.md"), "readset_sha256": sha(OUT / "READSET.json"), "observations_sha256": sha(OUT / "observations.json")}
put(OUT / "REVIEW.json", effective)
excluded = {"SEAL.json", "EVIDENCE-INVENTORY.json"}
inventory = {p.relative_to(OUT).as_posix(): sha(p) for p in sorted(OUT.rglob("*")) if p.is_file() and p.relative_to(OUT).as_posix() not in excluded}
put(OUT / "EVIDENCE-INVENTORY.json", {"kind": "retained-independent-v4-review-file-inventory", "files": inventory})
seal = {"kind": "independent-v4-controller-recovery-review-seal", "version": 1, "at_unix": time.time(), "verdict": effective["verdict"],
        "candidate_helper_sha256": HELPER, "candidate_freeze_file_sha256": FREEZE, "preserved_v3_counterexample_sha256": COUNTEREXAMPLE,
        "report_sha256": sha(OUT / "REPORT.md"), "review_sha256": sha(OUT / "REVIEW.json"), "readset_sha256": sha(OUT / "READSET.json"),
        "inventory_path": str(OUT / "EVIDENCE-INVENTORY.json"), "inventory_sha256": sha(OUT / "EVIDENCE-INVENTORY.json"),
        "inventory_members": len(inventory), "inventory_canonical_sha256": hashlib.sha256(canonical(inventory)).hexdigest(), "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False}
put(OUT / "SEAL.json", seal)
assert all(sha(OUT / rel) == wanted for rel, wanted in inventory.items())
for p in OUT.rglob("*"):
    if p.is_file(): p.chmod(0o444)
for p in sorted([p for p in OUT.rglob("*") if p.is_dir()], key=lambda p: len(p.parts), reverse=True): p.chmod(0o555)
OUT.chmod(0o555)
print(json.dumps({"review": str(OUT / "REVIEW.json"), "seal": str(OUT / "SEAL.json"), "seal_sha256": sha(OUT / "SEAL.json"), "checks_passed": 19, "verdict": effective["verdict"], "inventory_members": len(inventory)}))
