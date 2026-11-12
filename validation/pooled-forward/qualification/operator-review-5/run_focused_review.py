#!/usr/bin/env python3
"""Focused candidate6 per-epoch responsibility HOST/SIM review. No subprocess/device/SDK forwarding."""
from __future__ import annotations
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import sys
import time
import types

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
SUMMARY = []
FORWARDED_SUBPROCESSES = 0


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def read(path):
    return json.loads(Path(path).read_text())


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def outcome(name, evidence_class, expected, actual, details):
    row = {"case": name, "evidence_class": evidence_class, "expected": expected,
           "actual": actual, "expectation_met": expected == actual, "details": details}
    SUMMARY.append(row)
    return row


BASE_DUTIES = {"status": "passed", "blocking_claims": [], "rows": [
    {"id": "component-native-controls", "owner": "component", "method": "control", "priority": "must", "status": "passed", "unit": "bool", "expected": True},
    {"id": "component-native-callbacks", "owner": "component", "method": "callback", "priority": "must", "status": "passed", "unit": "bool", "expected": True},
    {"id": "thin-bridge-decodes-calls", "owner": "bridge", "method": "source", "priority": "must", "status": "passed", "unit": "bool", "expected": True},
]}


def replay_value(case):
    platform = "android" if case == "android" else "ios"
    rows = [{"id": f"atom-{i:03d}", "state": ["start", "after-primary", "after-replacement", "replacement-full", "after-last"][i % 5],
             "status": "passed", "reason": "SIMULATED neutral operator fact; no native truth", "requirement_id": f"rule-{i:03d}",
             "property": "label", "kind": "control", "unit": "string", "expected": f"fixed-{i:03d}", "op": "eq"} for i in range(104)]
    return {"simulation": True, "platform": platform, "design_sha256": "d" * 64,
            "plan_sha256": hashlib.sha256(("plan:" + case).encode()).hexdigest(),
            "fixtures_sha256": hashlib.sha256(("fixture:" + case).encode()).hexdigest(),
            "bridge_sha256": hashlib.sha256(("bridge:" + platform).encode()).hexdigest(),
            "environment_sha256": hashlib.sha256(("environment:" + platform).encode()).hexdigest(),
            "rows": rows, "native_counts": {"passed": 104, "failed": 0, "unassessed": 0},
            "responsibility": copy.deepcopy(BASE_DUTIES), "source_must_claim_ids": ["thin-bridge-decodes-calls"]}


def gate_case(name, mutation=None, expected_pass=False):
    folder = OUT / "gate-cases" / name
    root = folder / "simulated-study"
    gate = module("sim_gate_" + name.replace("-", "_"), OUT / "pinned-verify_benchmark.py")
    gate.R = root
    admission = {"simulation": True, "order": [list(v) for v in gate.ORDER], "threshold": 0.20,
                 "required_native_atoms": 104, "verifier_sha256": sha(OUT / "pinned-verify_benchmark.py"),
                 "driver_sha256": sha(OUT / "pinned-neutral_episode.py"),
                 "envelope_sha256": sha(OUT / "pinned-native_envelope.py"), "python_executable": sys.executable,
                 "production_files": {"neutral/Probe.txt": "c" * 64}, "arms": {}}
    for arm in ["A", "B"]:
        skill = root / ("simulated-" + arm)
        source = skill / "scripts/ui_loop.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("# SIMULATED frozen subject; never executed\n")
        freeze = root / ("freeze-" + arm + ".json")
        dump(freeze, {"files": {"scripts/ui_loop.py": sha(source)}})
        admission["arms"][arm] = {"skill": skill.name, "freeze": freeze.name, "freeze_sha256": sha(freeze)}
    roots = {}
    for index, (block, arm) in enumerate(gate.ORDER):
        ep = root / "cache/benchmark" / block / arm
        roots[(block, arm)] = ep
        skill = (root / admission["arms"][arm]["skill"]).resolve()
        start = 1000 + index * 200
        duration = 100 if arm == "A" else 70
        stage_duration = 20 if arm == "A" else 14
        counts = {"C0": 2, "R0": 4, "W1": 1, "F2": 2}
        stages = []
        for i, stage_name in enumerate(["C0", "R0", "W1", "F2"]):
            st = start + 2 + i * (stage_duration + 2)
            stage = {"stage": stage_name, "clock_start": st, "clock_end": st + stage_duration,
                     "wall_seconds": stage_duration, "started_at_unix": 1_000_000 + st,
                     "finished_at_unix": 1_000_000 + st + stage_duration, "new_commands": counts[stage_name]}
            stages.append(stage)
            dump(ep / ("stage-" + stage_name + ".json"), stage)
        result = {"simulation": True, "block": block, "arm": arm, "failed": None, "source_unchanged": True,
                  "clock_start": start, "clock_end": start + duration, "collection_wall_seconds": duration,
                  "collection_clock_basis": "clock_gettime(CLOCK_MONOTONIC)",
                  "collection_started_at_unix": 1_000_000 + start, "finished_at_unix": 1_000_000 + start + duration,
                  "stages": stages, "collection_stage_seconds": 4 * stage_duration,
                  "operator_and_meter_seconds": duration - 4 * stage_duration}
        dump(ep / "result.json", result)
        dump(ep / "ADMISSION.json", {"skill_seal_sha256": admission["arms"][arm]["freeze_sha256"],
              "source_map": admission["production_files"], "driver_sha256": admission["driver_sha256"],
              "envelope_sha256": admission["envelope_sha256"]})
        dump(ep / "meter.summary.json", {"budget_exceeded": False, "sampling_error": None,
                                         "observed_total_peak_allocated_bytes": 1024})
        for case in ["android", "ios-cold", "ios-warm"]:
            dump(ep / "profiles" / (case + ".json"), {"simulation": True, "case": case})
        for packet_step, packet_case in gate.STEPS:
            dump(ep / "evidence" / packet_step / "capture/result.json", {"simulation": True, "native_executed": False, "native_truth": "none"})
        offsets = {}
        for command_name, case, st_name in gate.COMMANDS:
            st = next(v for v in stages if v["stage"] == st_name)
            j = offsets.get(st_name, 0)
            offsets[st_name] = j + 1
            wall = 2 if arm == "A" else 1
            cs = st["clock_start"] + 1 + j * (wall + 1)
            config = ep / "profiles" / (case + ".json")
            record = ep / "commands" / (block + "-" + arm + "-" + command_name)
            action = "bind-source-review" if command_name.startswith("R0-source-") else "native"
            child = [sys.executable, "-B", str(skill / "scripts/ui_loop.py"), action, "--config", str(config)]
            if action == "bind-source-review":
                submission = ep / "reviews" / (command_name + ".json")
                dump(submission, {"version": 1, "observations": [{"id": "thin-bridge-decodes-calls", "observed": True,
                     "reason": "SIMULATED source observation only", "citations": [{"path": str(ep / "SIMULATED-Bridge.swift"), "line": 1}]}]})
                child += ["--submission", str(submission), "--output", str(ep / "reviews" / (command_name + "-bound.json"))]
            else:
                child += ["--output", str(ep / "evidence" / command_name)]
                if command_name.startswith("F2-"): child.append("--final")
                prior = {"R0-android": "C0-android", "R0-ios-cold": "C0-ios", "F2-ios-warm": "W1-ios", "F2-android": "C0-android"}.get(command_name)
                if arm == "A" and prior:
                    previous_packet = ep / "evidence" / prior / "capture/result.json"
                    child += ["--previous", str(previous_packet), "--previous-sha256", sha(previous_packet)]
            request = {"started_at_unix": 1_000_000 + cs, "argv": child, "config_sha256": sha(config),
                       "skill": str(skill), "source_before": {"0/Probe.txt": "c" * 64},
                       "envelope_sha256": admission["envelope_sha256"], "meter_spec_sha256": "e" * 64,
                       "clock_start": cs, "clock_basis": "clock_gettime(CLOCK_MONOTONIC)",
                       "purpose": "SIMULATED common operator request; no native truth"}
            cmd = dict(request, simulation=True, command_name=command_name, stage=st_name,
                       clock_end=cs + wall, wall_seconds=wall, exit_code=0, wrapper_exit_code=0,
                       error=None, recovery=None, source_unchanged=True, source_after=request["source_before"],
                       finished_at_unix=1_000_000 + cs + wall)
            outer = [sys.executable, "-B", str(root / "native_envelope.py"), "--config", str(config),
                     "--skill", str(skill), "--record", str(record), "--timeout", "1200", "--"] + child
            dump(record / "request.json", request)
            dump(record / "result.json", cmd)
            dump(ep / "commands" / (command_name + ".driver.json"), {"argv": outer, "exit_code": 0, "stdout": "SIMULATED"})
        for step, case in gate.STEPS:
            packet = ep / "evidence" / step / "capture/result.json"
            dump(packet, {"simulation": True, "native_executed": False, "native_truth": "none"})
            prior = {"R0-android": "C0-android", "R0-ios-cold": "C0-ios"}.get(step)
            if arm == "B": prior = prior or {"F2-ios-warm": "W1-ios", "F2-android": "C0-android"}.get(step)
            capture_packet = ep / "evidence" / prior / "capture/result.json" if prior else packet
            cycle = {"simulation": True, "capture_result": str(capture_packet), "status": "accepted" if step.startswith("F2-") else "dispatched",
                     "native_executed": step.startswith("C0-") or step.startswith("W1-") or (arm == "A" and step.startswith("F2-")),
                     "evidence_responsibility": copy.deepcopy(BASE_DUTIES)}
            dump(ep / "evidence" / step / "cycle.json", cycle)
            dump(ep / "evidence" / step / "resources.json", {"remaining_devices": [], "remaining_directories": [], "cleanup_errors": []})
    # Fixed shared original source-U at each initial C0, followed by P after R0.
    for ep in roots.values():
        for step in ["C0-android", "C0-ios"]:
            cycle_path = ep / "evidence" / step / "cycle.json"
            cycle = read(cycle_path)
            cycle["evidence_responsibility"]["status"] = "unassessed_or_failed"
            cycle["evidence_responsibility"]["blocking_claims"] = ["thin-bridge-decodes-calls"]
            cycle["evidence_responsibility"]["rows"][-1]["status"] = "unassessed"
            dump(cycle_path, cycle)
    context = {"root": root, "roots": roots, "admission": admission, "replay_mutation": None}
    if mutation: mutation(context)
    admission_path = folder / "ADMISSION-SIMULATED.json"
    dump(admission_path, admission)
    replay_calls = []
    def fake_run(argv, **kwargs):
        assert isinstance(argv, list) and argv[:4] == [sys.executable, "-B", str(OUT / "pinned-verify_benchmark.py"), "replay"], argv
        assert set(kwargs) == {"text", "stdout", "stderr"}, kwargs
        config = Path(argv[argv.index("--config") + 1]); packet = Path(argv[argv.index("--packet") + 1]); dst = Path(argv[argv.index("--output") + 1])
        assert config.is_relative_to(root) and packet.is_relative_to(root) and dst.is_relative_to(folder), argv
        value = replay_value(config.stem)
        if context["replay_mutation"]: context["replay_mutation"](value, argv)
        dump(dst, value); replay_calls.append({"argv": argv, "simulation": True, "forwarded": False})
        return types.SimpleNamespace(returncode=0, stdout="SIMULATED replay; no frozen replayer or SDK executed")
    gate.subprocess = types.SimpleNamespace(run=fake_run, PIPE=-1, STDOUT=-2)
    stdout = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout): code = gate.evaluate(types.SimpleNamespace(admission=str(admission_path), output=str(folder / "gate-output")))
        value = read(folder / "gate-output/RESULT.json"); actual = bool(value["passed"])
        details = {"return_code": code, "errors": value["errors"], "simulated_reduction": value["reduction"],
                   "comparison_count": len(value["comparisons"]), "actual_command_counts": [e["actual_command_count"] for e in value["episodes"]],
                   "raw_reason_differences": sum(len(c["raw_reason_differences"]) for c in value["comparisons"]),
                   "scope": "SIMULATED verifier decision only; synthetic speed is not measured native speed"}
    except BaseException as exc:
        actual = False; details = {"exception": {"type": type(exc).__name__, "message": str(exc)}, "replay_calls_before_exception": len(replay_calls)}
    dump(folder / "strict-fake-replay-calls.json", replay_calls)
    (folder / "gate.stdout.txt").write_text(stdout.getvalue())
    dump(folder / "case-outcome.json", outcome(name, "HOST/SIMULATED", expected_pass, actual, details))


def change_result(ctx, edit, arm="B", block="block-1"):
    p = ctx["roots"][(block, arm)] / "result.json"
    value = read(p)
    edit(value)
    dump(p, value)


def change_command(ctx, edit, arm="B", block="block-1", name="C0-android"):
    ep = ctx["roots"][(block, arm)]
    p = ep / "commands" / (block + "-" + arm + "-" + name) / "result.json"
    value = read(p)
    edit(value)
    dump(p, value)




def edit_duties(ctx, edit, step="R0-android", arm="B", block="block-1"):
    path = ctx["roots"][(block, arm)] / "evidence" / step / "cycle.json"
    cycle = read(path); edit(cycle["evidence_responsibility"]); dump(path, cycle)

def source_field(ctx, field, value, step="R0-android"):
    edit_duties(ctx, lambda d: next(v for v in d["rows"] if v["id"] == "thin-bridge-decodes-calls").update({field: value}), step=step)

gate_case("coherent-shared-C0-source-U-then-P", expected_pass=True)
gate_case("missing-duty-C0", lambda c: edit_duties(c, lambda d: d["rows"].pop(), step="C0-ios"))
gate_case("extra-duty-W1", lambda c: edit_duties(c, lambda d: d["rows"].append(dict(d["rows"][-1], id="foreign-duty")), step="W1-ios"))
gate_case("duplicate-three-duty-identities-R0", lambda c: edit_duties(c, lambda d: d["rows"][0].update(id=d["rows"][1]["id"])))
gate_case("advisory-priority-R0", lambda c: source_field(c,"priority","advisory"))
gate_case("B-only-source-U-R0", lambda c: source_field(c,"status","unassessed"))
gate_case("B-only-source-U-W1", lambda c: source_field(c,"status","unassessed",step="W1-ios"))
gate_case("B-only-method-drift-R0", lambda c: source_field(c,"method","visual"))
gate_case("B-only-method-drift-W1", lambda c: source_field(c,"method","visual",step="W1-ios"))
gate_case("B-only-expected-drift-R0", lambda c: source_field(c,"expected",False))
gate_case("B-only-expected-drift-W1", lambda c: source_field(c,"expected",False,step="W1-ios"))
gate_case("B-only-owner-drift-R0", lambda c: source_field(c,"owner","integration"))
gate_case("B-only-unit-drift-W1", lambda c: source_field(c,"unit","string",step="W1-ios"))
gate_case("B-initial-source-P-vs-original-U", lambda c: source_field(c,"status","passed",step="C0-ios"))
gate_case("invalid-duty-status", lambda c: source_field(c,"status","unknown"))
gate_case("duty-order-is-nonsemantic", lambda c: edit_duties(c, lambda d: d["rows"].reverse()), expected_pass=True)
# A minimal unchanged-guard regression alongside the narrow AST audit.
gate_case("unchanged-native-PFU-drift-rejects", lambda c: c.update(replay_mutation=lambda v,a: v["rows"][0].update(status="unassessed") if "/B/" in a[a.index("--config")+1] else None))

dump(OUT / "TEST-RESULTS.json", {"scope": "Focused candidate6 per-epoch original duty identity HOST/SIM only", "cases": SUMMARY,
    "unexpected": [v for v in SUMMARY if not v["expectation_met"]], "real_subprocesses": 0})
positive = read(OUT / "gate-cases/coherent-shared-C0-source-U-then-P/gate-output/RESULT.json")
proof = {"native_denominator": positive["denominators"]["native_atoms_per_packet"],
         "source_duty_denominator": positive["denominators"]["source_must_claims_separate"],
         "comparisons": [{"block": c["block"], "step": c["step"], "same_original_responsibility_pfu": c["same_original_responsibility_pfu"],
              "source_status_A": next(v["status"] for v in c["original_responsibility_A"] if v["id"] == "thin-bridge-decodes-calls"),
              "source_status_B": next(v["status"] for v in c["original_responsibility_B"] if v["id"] == "thin-bridge-decodes-calls")} for c in positive["comparisons"]]}
assert proof["native_denominator"] == 104 and proof["source_duty_denominator"] == 1
assert all(v["source_status_A"] == v["source_status_B"] == ("unassessed" if v["step"].startswith("C0-") else "passed") for v in proof["comparisons"])
dump(OUT / "ORIGINAL-U-IDENTITY-PROOF.json", proof)
print(json.dumps({"cases": len(SUMMARY), "expected": sum(v["expectation_met"] for v in SUMMARY), "unexpected": [v for v in SUMMARY if not v["expectation_met"]]},indent=2))
