#!/usr/bin/env python3
"""Seal bounded v3 delta review with its original protocol counterexample."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
HELPER = "d25c9be1bb0e1db2af2370a21553e8ba3a1bb32a8d318d115ea13bed5e027014"
FREEZE = "6c2142e16901cdc2fcb8a24c752829be4a6dddbc50fb6ed4ff8b25ab61ea68ea"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def canonical(v): return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
def put(path, value):
    with Path(path).open("x") as stream:
        stream.write(value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True) + "\n")


assert sha(ROOT / "business-tools-v3/blind_study.py") == HELPER
assert sha(ROOT / "business-tools-v3/FREEZE.json") == FREEZE
freezes = {}
for folder in ["business-tools", "business-tools-v2", "business-tools-v3"]:
    frozen = load(ROOT / folder / "FREEZE.json")
    files = {rel: {"expected_sha256": value, "actual_sha256": sha(ROOT / folder / rel)} for rel, value in frozen["files"].items()}
    assert all(v["expected_sha256"] == v["actual_sha256"] for v in files.values())
    freezes[folder] = {"freeze_sha256": sha(ROOT / folder / "FREEZE.json"), "files": files}
predecessors = {}
for folder, expected in [(OUT.parent, "90644daf3935891c9103cdd1eb8ab0fed33df4ef3533568b3018de1ca68bb1f3"), (OUT.parent / "v2", "7e48844368953e34afe999fc1ec8859bb37b4bfa7ebf6340e82b669447236b50")]:
    assert sha(folder / "SEAL.json") == expected
    inventory = load(folder / "EVIDENCE-INVENTORY.json")["files"]
    assert all(sha(folder / rel) == wanted for rel, wanted in inventory.items())
    predecessors[str(folder)] = {"seal_sha256": expected, "inventory_sha256": sha(folder / "EVIDENCE-INVENTORY.json"), "all_members_unchanged": True, "members": len(inventory)}


def functions(path):
    tree = ast.parse(Path(path).read_text())
    values = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            values[node.name] = ast.dump(node, include_attributes=False)
        elif isinstance(node, ast.ClassDef):
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    values[node.name + "." + method.name] = ast.dump(method, include_attributes=False)
    return values


before = functions(ROOT / "business-tools-v2/blind_study.py")
after = functions(ROOT / "business-tools-v3/blind_study.py")
changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
assert changed == ["Study.check_request_integrity", "Study.d0_complete", "Study.feedback_ready", "Study.serve"]
unchanged_transport = ["Study.domain_authority", "Study.active_configs", "Study.profile_admission", "Study.request_domain_review", "Study.admit_domain_review", "Study._admit_domain_review"]
assert all(before[k] == after[k] for k in unchanged_transport)
assert sha(ROOT / "business-tools-v3/source_domain.py") == sha(ROOT / "business-tools-v2/source_domain.py")
put(OUT / "FUNCTION-DELTA.json", {"changed_or_added": changed, "source_domain_file_unchanged": True, "v2_admission_profile_methods_unchanged": unchanged_transport,
                                  "unchanged_method_AST_sha256": {key: hashlib.sha256(after[key].encode()).hexdigest() for key in unchanged_transport}})
readset = {"kind": "independent-bounded-v3-public-readset", "frozen_candidates": freezes, "predecessor_reviews": predecessors,
           "protocol": {"path": str(ROOT / "PROTOCOL.json"), "sha256": sha(ROOT / "PROTOCOL.json")},
           "function_delta": {"path": str(OUT / "FUNCTION-DELTA.json"), "sha256": sha(OUT / "FUNCTION-DELTA.json")},
           "scope": "Only frozen common controllers, public protocol/docs/tests and prior independent reviews. No business source/design/oracle, SUT mutation, SDK, native/timing outcomes or Git operation."}
put(OUT / "READSET.json", readset)
frozen = load(OUT / "frozen-terminal-12-tests.json")
independent = load(OUT / "independent-focused-tests.json")
counterexample = load(OUT / "LOST-ANCHOR-COUNTEREXAMPLE.json")
assert frozen["passed"] and frozen["tests_run"] == 12
assert independent["passed"] and independent["tests_run"] == 4
assert counterexample["protocol_conforming"] is False and counterexample["deadline_extension_seconds"] == 1301
assert counterexample["source_writable_after_original_deadline"] is True

report = """# Independent v3 terminal-D0 delta review

**Verdict: CHANGES REQUIRED.** A process stop after the durable first-D0 result/event but before the source-window anchor lets D1 create a later deadline. The independent synthetic reproduction extended the deadline by **1301 seconds** and unlocked source after its original D0 deadline. V3 must remain excluded from study execution pending a new frozen candidate.

Reviewed helper: `d25c9be1bb0e1db2af2370a21553e8ba3a1bb32a8d318d115ea13bed5e027014`. Freeze file: `6c2142e16901cdc2fcb8a24c752829be4a6dddbc50fb6ed4ff8b25ab61ea68ea`.

## Blocking durability finding

`serve()` durably saves every profile outcome, the aggregate result, and `request_finished`, then appends `repair_started` separately. The counterexample injects an `OSError` only at that final anchor append, representing a process stop at the exact write boundary. All first-D0 profile outcomes/result/finished event and initial source/input/tool integrity remain valid. The first D0 is complete; source is read-only and no ticket remains pending, but the anchor is absent.

The reproduction restarts the controller at original D0 readiness +1301 seconds, beyond the required original +1200 deadline. D1 can enqueue and finish. The anchor condition checks that the first D0 is complete, but uses the **current D1** request ID, result-readiness clock and wall time to create `repair_started`. `feedback_ready` then unlocks the unchanged initial tree against that later clock. `LOST-ANCHOR-COUNTEREXAMPLE.json` retains the original first result path/hash, both request IDs, required original deadline, observed later anchor, unlock event and exact extension. The full synthetic event/result/outcome/log chain is retained under `lost-anchor-fixture`.

Recovery must derive any missing first-D0 completion/anchor bookkeeping solely from an independently durable exact first-D0 aggregate-result and per-profile proof: original first request ID, immutable hashes, `result.finished_at_clock` and `finished_at_unix`. A current or D1 clock must never supply the source-window start. If its original 1200 seconds have elapsed, freeze the unchanged source immediately before queue or unlock operations. Missing/truncated/unbound results and interrupted/integrity-invalid tickets stay pending/locked. A new candidate should test cuts before and after result preparation, result persistence, finished-event persistence, anchor persistence and guard startup. Original v3 files and failures must remain unchanged.

## Bounded positive checks

The frozen twelve terminal-D0 tests pass. Four additional independent checks pass: 16 positive checks plus the separate reproduced protocol violation. The frozen author's forty-test QA remains a historical artifact; it is not independent coverage of the lost-anchor durability boundary.

The independent flow runs complete synthetic arm A followed by arm B. A starts from an honest runtime crash, B from a blocked source-shape status; all terminal failures remain unaccepted with no invented native facts. Complete durable D0 automatically anchors +1200, and source remains read-only until explicit acknowledgment. Source-only repair then D1 and final collection use the ordinary APIs. D1 remains the second and last diagnostic and cannot reset a normally present anchor. Control final transport retains program-selected previous/SHA/history; treatment uses its default transport. Final source lock and self-seal remain irrevocable, initial cohort/capsules remain unchanged, and inactive B starts no clock while A completes.

Further independent checks establish that late acknowledgment of a normally anchored failed D0 freezes the initial source without unlocking; SystemExit, negative supervisor return and an explicit envelope interruption retain one partial profile/outcome/log and a pending ticket without continuing or retrying; explicit envelope/capture drift reports and tampering in a remote fifth-pair initial capsule prevent the first anchor. A successful D1 cannot upgrade an integrity-invalid first D0. The frozen twelve also cover missing/empty/non-durable profile outcomes, source/config/tool drift, current integrity at unlock, unchanged v2 source-domain approval after blocked D0 and guard-startup failure after a durable normal anchor.

AST comparison proves the only changed/added helper functions from v2 are `feedback_ready`, `d0_complete`, `check_request_integrity`, and `serve`. Source-domain transport and all source-domain/profile admission method ASTs remain unchanged; `source_domain.py` is byte-identical. There was no responsibility filtering, SUT/SDK/oracle rewrite or study policy adjustment.

All v1/v2/v3 frozen candidate files and both prior sealed independent reviews remain unchanged; exact hashes and AST checks are in `READSET.json` and `FUNCTION-DELTA.json`. Every new artifact is under this `v3` directory. The reproduction and test drivers are included in the sealed inventory.

This is HOST/SIM only. All service receipts/logs are synthetic. Helper `execute()`, subprocess/SDK forwarding, actual business source/design/oracles, native/render execution, real timing outcomes and Git operations were excluded. No native, business-quality or performance result follows. `REVIEW.json` records the effective changes-required verdict; `SEAL.json` binds the complete retained counterexample and positive-test artifacts.
"""
put(OUT / "REPORT.md", report)
effective = {"kind": "independent-v3-terminal-D0-forward-review", "version": 1, "verdict": "changes_required", "candidate_helper_sha256": HELPER, "candidate_freeze_file_sha256": FREEZE,
             "positive_checks": {"frozen_terminal_passed": 12, "independent_focused_passed": 4, "total_passed": 16},
             "blocking_findings": [{"id": "FIRST-D0-ANCHOR-DURABILITY", "status": "reproduced", "deadline_extension_seconds": 1301,
                                    "source_unlocked_after_original_deadline": True, "proof": {"path": str(OUT / "LOST-ANCHOR-COUNTEREXAMPLE.json"), "sha256": sha(OUT / "LOST-ANCHOR-COUNTEREXAMPLE.json")}}],
             "original_candidates_and_v1_v2_reviews_preserved": True, "v2_source_domain_and_profile_APIs_unchanged": True,
             "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False, "business_data_access": False, "business_study_authorized": False,
             "report_sha256": sha(OUT / "REPORT.md"), "readset_sha256": sha(OUT / "READSET.json")}
put(OUT / "REVIEW.json", effective)
excluded = {"SEAL.json", "EVIDENCE-INVENTORY.json"}
inventory = {p.relative_to(OUT).as_posix(): sha(p) for p in sorted(OUT.rglob("*")) if p.is_file() and p.relative_to(OUT).as_posix() not in excluded}
put(OUT / "EVIDENCE-INVENTORY.json", {"kind": "retained-independent-v3-review-file-inventory", "files": inventory})
seal = {"kind": "independent-v3-controller-review-seal", "version": 1, "at_unix": time.time(), "verdict": "changes_required", "candidate_helper_sha256": HELPER, "candidate_freeze_file_sha256": FREEZE,
        "report_sha256": sha(OUT / "REPORT.md"), "review_sha256": sha(OUT / "REVIEW.json"), "readset_sha256": sha(OUT / "READSET.json"),
        "counterexample_sha256": sha(OUT / "LOST-ANCHOR-COUNTEREXAMPLE.json"), "inventory_path": str(OUT / "EVIDENCE-INVENTORY.json"), "inventory_sha256": sha(OUT / "EVIDENCE-INVENTORY.json"),
        "inventory_members": len(inventory), "inventory_canonical_sha256": hashlib.sha256(canonical(inventory)).hexdigest(), "native_execution": False, "sdk_forwarding": False, "helper_execute_forwarding": False}
put(OUT / "SEAL.json", seal)
assert all(sha(OUT / rel) == wanted for rel, wanted in inventory.items())
for p in OUT.rglob("*"):
    if p.is_file(): p.chmod(0o444)
for p in sorted([p for p in OUT.rglob("*") if p.is_dir()], key=lambda p: len(p.parts), reverse=True): p.chmod(0o555)
OUT.chmod(0o555)
print(json.dumps({"review": str(OUT / "REVIEW.json"), "seal": str(OUT / "SEAL.json"), "seal_sha256": sha(OUT / "SEAL.json"), "positive_checks_passed": 16, "protocol_counterexamples": 1, "verdict": "changes_required", "inventory_members": len(inventory)}))
