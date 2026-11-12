#!/usr/bin/env python3
"""Operator forwarding for fresh post-cohort facts; no repair, retry, or grading."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import traceback

HELPER_SHA = "1a52cc62be5cee0bad34fefe8b54a7479761ca5ea5e8981937a8a1ad11ae6b05"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


def ref(path):
    return {"path": str(Path(path).resolve()), "sha256": sha(path)}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def barrier(root, helper):
    run = root / "cache/business/run-cohort2"
    manifest = load(run / "manifest.json")
    init = load(run / "INIT.json")
    if init["manifest_sha256"] != sha(run / "manifest.json"):
        raise ValueError("Frozen manifest changed")
    cohort = load(run / "COHORT-SEAL.json")
    authorization = load(run / "HIDDEN-AUTHORIZATION.json")
    if len(cohort["members"]) != 10:
        raise ValueError("Ten public seals are required")
    for member in cohort["members"].values():
        if sha(member["path"]) != member["sha256"]:
            raise ValueError("Public self-seal changed")
    if authorization["authorization"]["cohort_sha256"] != sha(run / "COHORT-SEAL.json"):
        raise ValueError("Hidden authorization changed")
    events = []
    previous = None
    for index, path in enumerate(sorted((run / "events").glob("*.json"))):
        event = load(path)
        if path.name != f"{index:06d}.json" or event["sequence"] != index or event["previous_sha256"] != previous:
            raise ValueError("Original event chain changed")
        previous = sha(path)
        events.append(event)
    registered = {e["request_id"] for e in events if e["kind"] == "request_enqueued"}
    terminal = {e["request_id"] for e in events if e["kind"] == "request_finished"}
    if registered != terminal:
        raise ValueError("Public FIFO still has unfinished work")
    auth = [e for e in events if e["kind"] == "hidden_authorized"]
    if len(auth) != 1 or auth[0] != authorization["authorization"]:
        raise ValueError("Original one-shot authorization is absent")
    for tool in manifest["tools"].values():
        helper.frozen_files(tool)
    return run, manifest, authorization


def profile_admission(root, manifest_arm, config_path, helper, output):
    config = load(config_path)
    hook = manifest_arm["profile_admissions"][helper.domain.platform(config)]
    approval = load(hook["approval"])
    if helper.digest(approval) != hook["approval_sha256"]:
        raise ValueError("Profile approval canonical pin changed")
    guard = module(hook["script"], "independent_actual_profile")
    platform = helper.domain.platform(config)
    verdict = guard.verify(Path(hook["root"]), approval, hook["approval_sha256"], platform, config)
    if verdict.get("status") != "admitted_profile" or verdict.get("platform") != platform:
        raise ValueError("Actual runtime profile was not admitted")
    inputs = {}
    for key in ["design_lock", "plan", "policy", "routes", "environment", "fixtures"]:
        inputs[key] = {**ref(config[key]), "canonical_sha256": helper.digest(load(config[key]))}
    inputs["bridge"] = ref(config["bridge"])
    for key in ["coverage_domain_ref", "coverage_provider_ref"]:
        if key in config:
            item = config[key]
            if helper.digest(load(item["path"])) != item["sha256"]:
                raise ValueError(f"Changed {key}")
            inputs[key] = {**ref(item["path"]), "canonical_sha256": item["sha256"]}
    receipt = {
        "version": 1, "config": {**ref(config_path), "canonical_sha256": helper.digest(config)},
        "script": ref(hook["script"]), "approval": {**ref(hook["approval"]), "canonical_sha256": hook["approval_sha256"]},
        "platform": platform, "platform_source": "actual config.plan.design_contract.platform",
        "inputs": inputs, "verdict": verdict,
    }
    save(output, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--task", choices=[f"T{i}" for i in range(1, 6)], required=True)
    parser.add_argument("--arm", choices=["A", "B", "I"], required=True)
    parser.add_argument("--profile", choices=["ios", "android"], required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--action", choices=["native", "bind-source-review", "bind-native-review", "finish-native-review", "cleanup-native-resources"], required=True)
    parser.add_argument("--submission", type=Path)
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--cycle", type=Path)
    parser.add_argument("--initial-monitor", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    helper_path = root / "business-tools-v4/blind_study.py"
    if sha(helper_path) != HELPER_SHA:
        raise ValueError("Frozen controller identity changed")
    helper = module(helper_path, "independent_frozen_helpers")
    run, manifest, authorization = barrier(root, helper)
    task = next(t for t in manifest["tasks"] if t["id"] == args.task)
    # The common initial reference uses the old/common observer path, without
    # previous/history. It is research/oracle work, never a treatment endpoint.
    manifest_arm = task["arms"]["A" if args.arm == "I" else args.arm]
    tool = manifest["tools"][manifest_arm["tool"]]
    config_path = args.config.resolve()
    record = args.record.resolve()
    evidence_root = root / "cache/business/independent-evaluation"
    if not record.is_relative_to(evidence_root) or record == evidence_root:
        raise ValueError("An explicit fresh independent-evaluation record is required")
    if args.arm == "I":
        expected_config = root / f"cache/business/initial-reference/{args.task}/profiles/{args.profile}.json"
        if not args.initial_monitor:
            raise ValueError("A live supplemental monitor is required for initial references")
    else:
        pin = authorization["hidden_configs"][args.task][args.arm][args.profile]
        expected_config = Path(pin["path"])
        if sha(expected_config) != pin["sha256"]:
            raise ValueError("Authorized hidden config changed")
    if config_path != expected_config.resolve() or config_path.is_symlink():
        raise ValueError("Config must be the exact declared independent profile")
    config = load(config_path)
    if helper.domain.platform(config) != args.profile or config["resources"].get("max_simulators", 1) != 1:
        raise ValueError("Actual platform and one-device bound are required")
    capsule = run / f"arms/{args.task}/{'A' if args.arm == 'I' else args.arm}/{'initial' if args.arm == 'I' else 'final-source'}/source.json"
    wanted = load(capsule)
    source_before = helper.source(config["source_roots"])
    if source_before["files"] != wanted["files"] or source_before["content_sha256"] != wanted["content_sha256"]:
        raise ValueError("Independent source does not exactly match the sealed capsule")
    if args.arm != "I" and source_before != wanted:
        raise ValueError("Final source root identity changed")
    evidence_root.mkdir(parents=True, exist_ok=True)
    with (evidence_root / "serialized-forwarding.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        record.mkdir(parents=True, exist_ok=False)
        start = time.monotonic()
        outcome = {"version": 1, "kind": "independent-original-fact-operation", "task": args.task, "arm": args.arm,
                   "profile": args.profile, "action": args.action, "started_at_unix": time.time(),
                   "started_at_monotonic": start, "config": ref(config_path), "source_capsule": ref(capsule),
                   "source_before": source_before, "tool_root": tool["skill_root"],
                   "scope": "Fresh independent facts at locked source; process exit is not delivery acceptance. No public prior/history or retry."}
        code = None
        service = None
        try:
            if args.arm == "I":
                preflight = [sys.executable, "-B", str(root / "initial-reference-monitor/monitor.py"), "--record", str(args.initial_monitor.resolve()), "--preflight"]
                with (record / "initial-monitor-preflight.log").open("x") as stream:
                    check = subprocess.run(preflight, stdout=stream, stderr=subprocess.STDOUT)
                save(record / "initial-monitor-preflight.json", {"argv": preflight, "exit_code": check.returncode})
                if check.returncode:
                    raise ValueError("Supplemental monitor preflight rejected")
            admission = profile_admission(root, manifest_arm, config_path, helper, record / "profile-admission.json")
            service = record / "service"
            argv = [sys.executable, "-B", str(Path(tool["skill_root"]) / "scripts/ui_loop.py"), args.action, "--config", str(config_path)]
            if args.action == "native":
                argv += ["--output", str(service), "--final"]
            elif args.action == "bind-source-review":
                if not args.submission:
                    raise ValueError("An independently sealed source submission is required")
                service.mkdir()
                argv += ["--submission", str(args.submission.resolve()), "--output", str(service / "source-review-ref.json")]
            elif args.action == "bind-native-review":
                if not args.submission or not args.capture:
                    raise ValueError("Independent actuals and the exact original capture are required")
                service = Path(config["review_store"]) / record.name
                argv += ["--capture-result", str(args.capture.resolve()), "--capture-sha256", sha(args.capture),
                         "--submission", str(args.submission.resolve()), "--submission-sha256", sha(args.submission), "--output", str(service)]
            elif args.action == "finish-native-review":
                if not args.cycle:
                    raise ValueError("The exact original final cycle is required")
                argv += ["--cycle", str(args.cycle.resolve()), "--cycle-sha256", sha(args.cycle), "--output", str(service)]
            else:
                argv += ["--output", str(service)]
            envelope = manifest["envelope"]
            for path_key, sha_key in [("path", "sha256"), ("meter_path", "meter_sha256"), ("meter_spec_path", "meter_spec_sha256")]:
                if sha(envelope[path_key]) != envelope[sha_key]:
                    raise ValueError("Original common supervision changed")
            command = [sys.executable, "-B", envelope["meter_path"], "--spec", envelope["meter_spec_path"], "--output", str(record / "meter.jsonl"), "--",
                       sys.executable, "-B", envelope["path"], "--config", str(config_path), "--skill", tool["skill_root"],
                       "--record", str(record / "envelope"), "--timeout", "1200", "--", *argv]
            save(record / "command.json", {"argv": argv, "service_output": str(service), "config": ref(config_path),
                                           "submission": ref(args.submission) if args.submission else None,
                                           "capture": ref(args.capture) if args.capture else None, "cycle": ref(args.cycle) if args.cycle else None})
            save(record / "supervised-command.json", {"argv": command})
            journals = [Path(config["resources"]["root"]) / "events.jsonl"]
            offsets = {str(p): p.stat().st_size if p.exists() else 0 for p in journals}
            with (record / "supervisor.log").open("x") as stream:
                code = subprocess.run(command, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), stdout=stream, stderr=subprocess.STDOUT).returncode
            rows, prefixes = [], []
            for path in journals:
                raw = path.read_bytes() if path.exists() else b""
                prefixes.append({"path": str(path), "start_byte": offsets[str(path)], "end_byte": len(raw), "prefix_sha256": hashlib.sha256(raw).hexdigest()})
                rows.extend(item for line in raw[offsets[str(path)]:].splitlines() if (item := json.loads(line)).get("kind") in {"simctl_command", "process_started"})
            save(record / "sdk-observation.json", {"journal_prefixes": prefixes, "observed_command_records": rows,
                 "scope": "Explicit partial owned-resource journal observations; internal descendants and metadata identity queries may be unobserved."})
            outcome.update(exit_code=code, service_output=str(service))
            for key, name in [("cycle", "cycle.json"), ("completion", "completion.json"), ("review", "review-result.json"), ("resources", "resources.json")]:
                path = service / name
                if path.is_file():
                    outcome[key] = ref(path)
            if "cycle" in outcome:
                cycle = load(outcome["cycle"]["path"])
                outcome.update(service_status=cycle.get("status"), new_ui_acquisition=cycle.get("native_executed"), capture_reused=cycle.get("capture_reused"))
                if cycle.get("capture_result"):
                    capture = Path(cycle["capture_result"])
                    if (args.action == "native" and not capture.is_relative_to(record)) or sha(capture) != cycle["capture_sha256"]:
                        raise ValueError("Independent native run did not retain its own fresh original capture")
                    outcome["capture"] = ref(capture)
            if "completion" in outcome:
                outcome["service_status"] = load(outcome["completion"]["path"]).get("status")
            if service.exists():
                inventory = {}
                for path in sorted(service.rglob("*")):
                    if path.is_symlink():
                        raise ValueError("Original service packet unexpectedly contains a symlink")
                    if path.is_file():
                        inventory[str(path)] = {"sha256": sha(path), "bytes": path.stat().st_size}
                save(record / "original-inventory.json", inventory)
                helper.protect([str(service)])
                outcome["inventory"] = ref(record / "original-inventory.json")
            if sha(config_path) != admission["config"]["sha256"] or any(sha(v["path"]) != v["sha256"] for v in admission["inputs"].values()):
                raise ValueError("Independent config/admitted input changed during operation")
            helper.frozen_files(tool)
        except BaseException as error:
            outcome["error"] = {"type": type(error).__name__, "message": str(error)}
            save(record / "failure.json", {"error": outcome["error"], "traceback": traceback.format_exc()})
        finally:
            if service is not None and service.exists() and not (record / "original-inventory.json").exists():
                partial = {}
                for path in sorted(service.rglob("*")):
                    if path.is_symlink():
                        partial[str(path)] = {"kind": "symlink", "target": os.readlink(path)}
                    elif path.is_file():
                        partial[str(path)] = {"sha256": sha(path), "bytes": path.stat().st_size}
                save(record / "original-inventory.json", partial)
                helper.protect([str(service)])
                outcome["inventory"] = ref(record / "original-inventory.json")
                outcome["partial_originals_retained"] = True
            try:
                after = helper.source(config["source_roots"])
            except BaseException as error:
                after = None
                outcome["source_after_error"] = {"type": type(error).__name__, "message": str(error)}
            outcome.update(finished_at_unix=time.time(), finished_at_monotonic=time.monotonic(),
                           wall_seconds=time.monotonic() - start, source_after=after, source_unchanged=after == source_before)
            outcome["accepted"] = code == 0 and not outcome.get("error") and outcome.get("service_status") == "accepted" and outcome["source_unchanged"]
            save(record / "outcome.json", outcome)
        print(json.dumps({"outcome": str(record / "outcome.json"), "sha256": sha(record / "outcome.json"),
                          "exit_code": code, "accepted": outcome["accepted"], "error": outcome.get("error")}))
        return 0 if code == 0 and not outcome.get("error") and outcome["source_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
