#!/usr/bin/env python3
"""Exercise actual replay entry with injected pure models; no native truth."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
MODEL = json.loads((OUT / "gate-cases/coherent-structural-positive/gate-output/block-1-A-C0-ios.json").read_text())
RESULTS = []


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


for case in ["identity-positive", "empty-tool-map", "missing-tool-map", "wrong-tool-sha", "source-U-preserved", "missing-must-source-claim"]:
    folder = OUT / "direct-replay-cases" / case
    arm = folder / "SIMULATED-frozen-arm"
    tool = arm / "scripts/SIM_TOOL.py"
    tool.parent.mkdir(parents=True)
    tool.write_text("# SIMULATED source subject; never executed\n")
    packet = folder / "SIMULATED-packet/result.json"
    original = {"simulation": True, "tool_files": {"scripts/SIM_TOOL.py": hashlib.sha256(tool.read_bytes()).hexdigest()}}
    if case == "empty-tool-map": original["tool_files"] = {}
    if case == "missing-tool-map": original.pop("tool_files")
    if case == "wrong-tool-sha": original["tool_files"]["scripts/SIM_TOOL.py"] = "0" * 64
    dump(packet, original)
    plan = {"assertions": copy.deepcopy(MODEL["rows"]), "design_contract": {"platform": "ios"},
            "matrix_contract": {"simulation": True, "states": ["start", "after-primary", "after-replacement", "replacement-full", "after-last"]}}
    for name, value in [("plan", plan), ("policy", {}), ("lock", {}), ("fixtures", {}), ("environment", {})]:
        dump(folder / (name + ".json"), value)
    bridge = folder / "SIMULATED-Bridge.swift"; bridge.write_text("// SIMULATED bridge bytes; never compiled\n")
    config = {"plan": str(folder / "plan.json"), "policy": str(folder / "policy.json"), "policy_sha256": "p" * 64,
              "design_lock": str(folder / "lock.json"), "design_sha256": "d" * 64, "fixtures": str(folder / "fixtures.json"),
              "bridge": str(bridge), "source_roots": [], "environment": str(folder / "environment.json"), "environment_sha256": "e" * 64}
    config_path = folder / "config.json"; dump(config_path, config)
    coverage = {"satisfied": True, "simulation": True}; environment = {"status": "P", "simulation": True}
    dump(packet.parent / "execution-coverage.json", coverage); dump(packet.parent / "environment-check.json", environment)
    dump(packet.parent / "native/manifest.json", {"native_test_count": 1, "simulation": True, "native_truth": "none"})
    calls = []
    duties = copy.deepcopy(MODEL["responsibility"])
    if case == "source-U-preserved":
        duties["rows"][-1]["status"] = "unassessed"
        duties["status"] = "unassessed_or_failed"; duties["blocking_claims"] = ["thin-bridge-decodes-calls"]
    claims = copy.deepcopy(MODEL["responsibility"]["rows"])
    if case == "missing-must-source-claim": claims = [c for c in claims if c["method"] != "source"]

    def previous(*args, policy, policy_sha, source_config=None):
        assert len(args) == 8 and source_config == config
        calls.append({"hook": "injected_load_previous", "forwarded": False})
        report = {"assertions": copy.deepcopy(MODEL["rows"]), "counts": {"passed": 104, "failed": 0, "unassessed": 0}, "matrix_contract": plan["matrix_contract"]}
        return ({}, report, {}, {}, {"source_unchanged": True, "inputs_unchanged": True, "native_exit_code": 0, "status": "verified_capture"})

    def compile_contract(*args):
        calls.append({"hook": "injected_compile_contract", "forwarded": False})
        return {"claims": claims}

    def evaluate(*args):
        calls.append({"hook": "injected_evaluate", "forwarded": False})
        return duties

    inject = {}
    for name in ["design_contract", "feedback_loop", "execution_plan", "acceptance", "evidence_responsibility"]:
        inject[name] = types.ModuleType(name)
    inject["design_contract"].digest = digest
    inject["feedback_loop"].load_previous = previous
    inject["execution_plan"].coverage_receipt = lambda *args: coverage
    inject["acceptance"].environment = lambda *args: environment
    inject["evidence_responsibility"].compile_contract = compile_contract
    inject["evidence_responsibility"].evaluate = evaluate
    saved = {k: sys.modules.get(k) for k in inject}; old_path = sys.path[:]
    output = folder / "replay-output.json"; error = None
    try:
        sys.modules.update(inject)
        spec = importlib.util.spec_from_file_location("focused_replay_" + case.replace("-", "_"), OUT / "pinned-verify_benchmark.py")
        gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
        gate.replay(types.SimpleNamespace(skill=str(arm), config=str(config_path), packet=str(packet), output=str(output)))
    except BaseException as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        sys.path[:] = old_path
        for k, old in saved.items():
            if old is None: sys.modules.pop(k, None)
            else: sys.modules[k] = old
    expected_reject = case in {"empty-tool-map", "missing-tool-map", "wrong-tool-sha", "missing-must-source-claim"}
    good = (error is not None) == expected_reject
    if case in {"empty-tool-map", "missing-tool-map", "wrong-tool-sha"}: good = good and not calls
    if case == "source-U-preserved": good = good and json.loads(output.read_text())["responsibility"] == duties
    if case == "identity-positive": good = good and [c["hook"] for c in calls] == ["injected_load_previous", "injected_compile_contract", "injected_evaluate"]
    row = {"case": case, "evidence_class": "HOST/SIMULATED", "expectation_met": good, "rejected": error is not None,
           "error": error, "calls": calls, "scope": "Actual replay control flow with injected pure models; no real frozen packet/replayer/SDK/native truth"}
    dump(folder / "case-outcome.json", row); RESULTS.append(row)
dump(OUT / "REPLAY-BOUNDARY-RESULTS.json", {"cases": RESULTS, "unexpected": [v for v in RESULTS if not v["expectation_met"]], "real_subprocesses": 0})
print(json.dumps({"cases": len(RESULTS), "expected": sum(v["expectation_met"] for v in RESULTS), "unexpected": [v for v in RESULTS if not v["expectation_met"]]}, indent=2))
