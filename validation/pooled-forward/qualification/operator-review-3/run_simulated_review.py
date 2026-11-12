#!/usr/bin/env python3
"""Focused candidate4 HOST/SIM review. No subprocess/device/SDK forwarding."""
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
    {"id": "component-native-controls", "method": "control", "priority": "must", "status": "passed"},
    {"id": "component-native-callbacks", "method": "callback", "priority": "must", "status": "passed"},
    {"id": "thin-bridge-decodes-calls", "method": "source", "priority": "must", "status": "passed"},
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
            child = [sys.executable, "-B", str(skill / "scripts/ui_loop.py"), action,
                     "--config", str(config), "--output", str(ep / ("reviews" if action == "bind-source-review" else "evidence") / command_name)]
            if command_name.startswith("F2-"): child.append("--final")
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
            packet = ep / "synthetic-packets" / step / "result.json"
            dump(packet, {"simulation": True, "native_executed": False, "native_truth": "none"})
            cycle = {"simulation": True, "capture_result": str(packet), "status": "accepted" if step.startswith("F2-") else "dispatched",
                     "native_executed": step.startswith("C0-") or step.startswith("W1-") or (arm == "A" and step.startswith("F2-")),
                     "evidence_responsibility": copy.deepcopy(BASE_DUTIES)}
            dump(ep / "evidence" / step / "cycle.json", cycle)
            dump(ep / "evidence" / step / "resources.json", {"remaining_devices": [], "remaining_directories": [], "cleanup_errors": []})
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


gate_case("coherent-structural-positive", expected_pass=True)


def empty_cycle(ctx):
    p = ctx["roots"][("block-1", "B")] / "evidence/F2-ios-warm/cycle.json"
    value = read(p)
    value["evidence_responsibility"] = {"status": "passed", "blocking_claims": [], "rows": []}
    dump(p, value)


gate_case("empty-final-source-denominator", empty_cycle)
gate_case("empty-replayed-source-denominator", lambda c: c.update(replay_mutation=lambda value, argv: value.update(responsibility={"status": "passed", "blocking_claims": [], "rows": []}, source_must_claim_ids=[])))
gate_case("negative-B-wall", lambda c: change_result(c, lambda v: v.update(collection_wall_seconds=-1)))
gate_case("wall-one-stage-fifty-six", lambda c: change_result(c, lambda v: v.update(collection_wall_seconds=1, clock_end=v["clock_start"]+1, operator_and_meter_seconds=0)))
gate_case("negative-overhead", lambda c: change_result(c, lambda v: v.update(operator_and_meter_seconds=-1)))
gate_case("nonfinite-wall", lambda c: change_result(c, lambda v: v.update(collection_wall_seconds=float("nan"))))
gate_case("boolean-wall", lambda c: change_result(c, lambda v: v.update(collection_wall_seconds=True)))
gate_case("command-wall-exceeds-stage-sum", lambda c: change_command(c, lambda v: v.update(wall_seconds=1000)))
gate_case("wrapper-error-after-child-zero", lambda c: change_command(c, lambda v: v.update(wrapper_exit_code=1,error={"type":"SIMULATEDReleaseFailure","message":"SIMULATED"})))
gate_case("missing-wrapper-exit", lambda c: change_command(c, lambda v: v.pop("wrapper_exit_code")))
gate_case("negative-command-wall", lambda c: change_command(c, lambda v: v.update(wall_seconds=-1)))


def raw_stage_drift(ctx):
    p = ctx["roots"][("block-1", "B")] / "stage-C0.json"
    value = read(p); value["wall_seconds"] = 99; dump(p, value)


gate_case("raw-stage-disagreement", raw_stage_drift)
gate_case("ABBA-overlap", lambda c: change_result(c, lambda v: v.update(clock_start=1001,clock_end=1071,collection_started_at_unix=1001001)))


def retire_leftover(ctx):
    p = ctx["roots"][("block-1", "B")] / "evidence/F2-android/resources.json"
    value = read(p); value["remaining_devices"] = ["SIMULATED-LEFTOVER"]; dump(p, value)


gate_case("retirement-leftover", retire_leftover)


def unknown_all(value, argv):
    value["rows"][0]["status"] = "unassessed"
    value["native_counts"] = {"passed": 103, "failed": 0, "unassessed": 1}


gate_case("mandatory-U-same-both-arms", lambda c: c.update(replay_mutation=unknown_all))


def pfu_drift(value, argv):
    if "/B/" in argv[argv.index("--config") + 1]: value["rows"][0]["status"] = "unassessed"


gate_case("PFU-drift-counts-unchanged", lambda c: c.update(replay_mutation=pfu_drift))


def reasons(value, argv):
    if "/B/" in argv[argv.index("--config") + 1]: value["rows"][0]["reason"] = "SIMULATED disagreement retained verbatim"


gate_case("raw-reason-disagreement-visible", lambda c: c.update(replay_mutation=reasons), expected_pass=True)


def missing_commands(ctx):
    for p in (ctx["roots"][("block-1", "B")] / "commands").glob("*/result.json"): p.unlink()


gate_case("MISSING-command-receipts", missing_commands)
gate_case("COMMAND-outside-episode", lambda c: change_command(c, lambda v: v.update(clock_start=10,clock_end=11)))
gate_case("COMMAND-negative-clock", lambda c: change_command(c, lambda v: v.update(clock_start=-50,clock_end=-49)))
gate_case("COMMAND-wall-clock-disagreement", lambda c: change_command(c, lambda v: v.update(clock_end=v["clock_start"]+200)))


def overlapping_commands(ctx):
    first = ctx["roots"][("block-1", "B")] / "commands/block-1-B-C0-android/result.json"
    data = read(first)
    change_command(ctx, lambda v: v.update(clock_start=data["clock_start"], clock_end=data["clock_end"]), name="C0-ios")


gate_case("COMMAND-overlap", overlapping_commands)
def wrong_stage(ctx):
    stage = next(s for s in read(ctx["roots"][("block-1", "B")] / "result.json")["stages"] if s["stage"] == "F2")
    change_command(ctx, lambda v: v.update(stage="F2", clock_start=stage["clock_start"]+1, clock_end=stage["clock_start"]+2))
gate_case("COMMAND-wrong-stage-placement", wrong_stage)



def request_edit(ctx, edit):
    p = ctx["roots"][("block-1", "B")] / "commands/block-1-B-C0-android/request.json"
    data = read(p); edit(data); dump(p, data)

gate_case("EMPTY-raw-request", lambda c: request_edit(c, lambda v: v.clear()))
gate_case("MISSING-request-clock-start", lambda c: request_edit(c, lambda v: v.pop("clock_start")))
gate_case("request-result-parity-disagreement", lambda c: request_edit(c, lambda v: v.update(config_sha256="0"*64)))

def changed_child(ctx, mode):
    ep = ctx["roots"][("block-1", "B")]; record = ep / "commands/block-1-B-C0-android"
    cmd = read(record / "result.json"); req = read(record / "request.json"); driver_path = ep / "commands/C0-android.driver.json"; driver = read(driver_path)
    if mode == "output":
        cmd["argv"][cmd["argv"].index("--output")+1] = str(ep / "UNRELATED-OUTPUT")
        req["argv"] = cmd["argv"][:]
        driver["argv"] = driver["argv"][:driver["argv"].index("--")+1] + cmd["argv"]
    elif mode == "python":
        cmd["argv"][0] = "/SIMULATED-FOREIGN-PYTHON"; req["argv"] = cmd["argv"][:]
        driver["argv"] = driver["argv"][:driver["argv"].index("--")+1] + cmd["argv"]
    elif mode == "outer": driver["argv"][2] = str(ep / "UNRELATED-ENVELOPE.py")
    dump(record / "result.json", cmd); dump(record / "request.json", req); dump(driver_path, driver)

gate_case("FOREIGN-output-path", lambda c: changed_child(c,"output"))
gate_case("FOREIGN-outer-envelope", lambda c: changed_child(c,"outer"))
gate_case("foreign-child-python", lambda c: changed_child(c,"python"))
gate_case("frozen-arm-source-drift-before-replay", lambda c: (c["root"] / c["admission"]["arms"]["B"]["skill"] / "scripts/ui_loop.py").write_text("# SIMULATED source drift\n"))
gate_case("frozen-arm-manifest-drift-before-replay", lambda c: (c["root"] / c["admission"]["arms"]["B"]["freeze"]).write_text("{}"))

def fake_envelope(name, failure=None, child=0, mutate_source=False):
    folder = OUT / "envelope-cases" / name
    study = folder / "simulated-study"
    source = study / "source/Probe.txt"
    source.parent.mkdir(parents=True)
    source.write_text("SIMULATED neutral source")
    config = study / "config.json"
    dump(config, {"source_roots": [str(source.parent)]})
    dump(study / "operators/whole-study-meter-spec-v2.json", {"groups": {}, "max_total_allocated_bytes": 1024,
         "min_free_bytes": 0, "sample_seconds": 2})
    calls = []

    class StrictFakeResources:
        def __init__(self, policy, output, final=False):
            assert final is True and Path(output).is_relative_to(study), (policy, output)
            self.policy = policy
            self.borrowed_paths = []
            calls.append({"method": "construct", "simulation": True, "forwarded": False})
        def __enter__(self):
            calls.append({"method": "enter", "simulation": True, "forwarded": False})
            self.sample(); self.check_budget()
            return self
        def sample(self):
            calls.append({"method": "sample", "simulation": True, "forwarded": False})
            return None
        def check_budget(self):
            calls.append({"method": "check_budget", "simulation": True, "forwarded": False})
            return None
        def run(self, argv, env, stdout):
            assert argv == ["SIMULATED_CHILD_ONLY"]
            calls.append({"method": "run", "argv": argv, "simulation": True, "forwarded": False})
            stdout.write("SIMULATED child; no process was launched\n")
            if mutate_source: source.write_text("SIMULATED mutation")
            return child
        def __exit__(self, *args):
            calls.append({"method": "release", "simulation": True, "forwarded": False})
            if failure: raise RuntimeError("SIMULATED supervisor release failure")
            return False
        def __getattr__(self, key):
            raise AssertionError("Unsupported fake resource operation: " + key)

    rm = types.ModuleType("resource_manager"); rm.Resources = StrictFakeResources; rm.FORMAT = "SIMULATED_ONLY"
    measure = types.ModuleType("measure")
    sub = types.ModuleType("subprocess"); sub.STDOUT = -2
    def fake_recovery(argv, **kwargs):
        assert argv[-1] == "cleanup" and Path(argv[2]).is_relative_to(study), argv
        assert set(kwargs) == {"stdout", "stderr", "timeout"} and kwargs["timeout"] == 180
        calls.append({"method": "recovery", "argv": argv, "simulation": True, "forwarded": False})
        kwargs["stdout"].write("SIMULATED recovery; no process launched\n")
        return types.SimpleNamespace(returncode=0)
    sub.run = fake_recovery
    originals = {key: sys.modules.get(key) for key in ["resource_manager", "measure", "subprocess"]}
    old_argv = sys.argv[:]
    stdout = io.StringIO()
    try:
        sys.modules.update(resource_manager=rm, measure=measure, subprocess=sub)
        envelope = module("sim_envelope_" + name.replace("-", "_"), OUT / "pinned-native_envelope.py")
        envelope.R = study
        sys.argv = [str(OUT / "pinned-native_envelope.py"), "--config", str(config), "--skill", str(study / "skill"),
                    "--record", str(study / "record"), "--", "SIMULATED_CHILD_ONLY"]
        with contextlib.redirect_stdout(stdout): code = envelope.main()
        value = read(study / "record/result.json")
        expected = 1 if failure or mutate_source else child
        details = {"returned": code, "record": value, "strict_fake_calls": calls,
                   "scope": "HOST execution of supervisor logic with SIMULATED lifecycle and child result; no native/process/resource truth"}
        outcome(name, "HOST/SIMULATED", expected, code, details)
    finally:
        sys.argv = old_argv
        for key, original in originals.items():
            if original is None: sys.modules.pop(key, None)
            else: sys.modules[key] = original
    dump(folder / "strict-fake-resource-calls.json", calls)
    (folder / "stdout.txt").write_text(stdout.getvalue())


fake_envelope("envelope-structural-positive")
fake_envelope("envelope-release-failure-after-child-zero", failure=True)
fake_envelope("envelope-child-seven", child=7)
fake_envelope("envelope-source-change-after-child-zero", mutate_source=True)

# Directly exercise the frozen-source tree guard using a disjoint synthetic tree.
measure_stub = types.ModuleType("measure"); measure_stub.Meter = object
old_measure = sys.modules.get("measure")
sys.modules["measure"] = measure_stub
try:
    episode = module("sim_episode_tree_guard", OUT / "pinned-neutral_episode.py")
finally:
    if old_measure is None: sys.modules.pop("measure", None)
    else: sys.modules["measure"] = old_measure
tree = OUT / "tree-guard/source"
tree.mkdir(parents=True)
(tree / "neutral.py").write_text("SIMULATED immutable operator subject\n")
seal = {"files": {"neutral.py": sha(tree / "neutral.py")}}
episode.verify_tree(tree, seal)
outcome("frozen-tree-unchanged", "HOST/SIMULATED", True, True, {"scope": "Actual byte guard on synthetic source"})
(tree / "neutral.py").write_text("SIMULATED changed source\n")
try:
    episode.verify_tree(tree, seal)
except AssertionError:
    rejected = True
else:
    rejected = False
outcome("frozen-tree-drift", "HOST/SIMULATED", True, rejected, {"scope": "Actual byte guard on synthetic source"})

dump(OUT / "TEST-RESULTS.json", {"scope": "DISJOINT HOST/SIM only; no native/SDK/performance subprocess executed",
     "strict_fake_no_forwarding": True, "real_subprocesses_launched": FORWARDED_SUBPROCESSES,
     "cases": SUMMARY, "unexpected": [v for v in SUMMARY if not v["expectation_met"]]})
print(json.dumps({"cases": len(SUMMARY), "expected_outcomes": sum(v["expectation_met"] for v in SUMMARY),
                  "unexpected": [{"case": v["case"], "expected": v["expected"], "actual": v["actual"], "details": v["details"]} for v in SUMMARY if not v["expectation_met"]]}, indent=2))
