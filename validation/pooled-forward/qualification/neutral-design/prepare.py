#!/usr/bin/env python3
"""Reproduce sealed neutral plans with documented baseline pure compilers only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode()


def json_digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    design = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-root", type=Path,
                        default=design.parents[1] / "baseline-v12.6")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    baseline = args.baseline_root.resolve()
    output = args.output.resolve()
    if not output.is_relative_to(design) or output == design:
        raise SystemExit("Preparation output must be a fresh subdirectory of neutral-design")
    if output.exists():
        raise SystemExit("Preparation output must not already exist")
    approval = load(design / "approval.json")
    for item in approval["input_files"]:
        if file_digest(design / item["path"]) != item["sha256"]:
            raise SystemExit("Changed independent input: " + item["path"])
    for name, expected in approval["baseline_compiler_sha256"].items():
        if file_digest(baseline / "scripts" / name) != expected:
            raise SystemExit("Baseline compiler differs from approved ABI: " + name)
    output.mkdir(parents=True)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    calls = []

    def run(script, *arguments, allowed=(0,)):
        command = [sys.executable, "-B", str(baseline / "scripts" / script), *map(str, arguments)]
        result = subprocess.run(command, text=True, capture_output=True, env=env,
                                check=False, timeout=120)
        calls.append({"command": command, "exit_code": result.returncode,
                      "stdout": result.stdout, "stderr": result.stderr,
                      "kind": "pure schema/compiler operation; no SDK"})
        dump(output / "compiler-calls.json", calls)
        if result.returncode not in allowed:
            raise SystemExit("Pure compiler failed: " + script + "\n" + result.stderr)

    run("design_contract.py", "seal", "--contract", design / "contract.json",
        "--root", design, "--output", output / "reproduced-lock.json")
    lock_sha = json_digest(load(output / "reproduced-lock.json"))
    if lock_sha != approval["canonical_sha256"]["design_lock"]:
        raise SystemExit("Reproduced independent lock differs from approved digest")
    for key, name in [("policy", "policy.json"), ("routes", "routes.json"),
                      ("environment_ios", "environment.ios.json"),
                      ("environment_android", "environment.android.json"),
                      ("resources", "resources.json")]:
        if json_digest(load(design / name)) != approval["canonical_sha256"][key]:
            raise SystemExit("Changed canonical approval: " + key)

    summary = {"version": 1, "native_runs": 0, "builds": 0,
               "design_lock_sha256": lock_sha, "cases": [],
               "unrepresented_mandatory": load(design / "required-obligations.json")["unrepresented_mandatory"]}
    cases = [("ios-cold", "neutral-A", "ios"),
             ("ios-warm", "neutral-B", "ios"),
             ("android", "neutral-A", "android")]
    for case, scenario, platform in cases:
        target = output / case
        run("design_contract.py", "compile", "--lock", output / "reproduced-lock.json",
            "--lock-sha256", lock_sha, "--scenario", scenario, "--platform", platform,
            "--bindings", design / "bindings.json", "--actions", design / "actions.json",
            "--output", target)
        plan = load(target / "plan.json")
        required = plan["required_assertion_ids"]
        cells = plan["matrix_contract"]["cells"]
        na = [cell for cell in cells if cell["disposition"] == "not_applicable"]
        expected = load(design / "required-obligations.json")
        if (len(required), len(cells), len(na)) != (
                expected["expected_native_assertions_per_case"],
                expected["expected_matrix_cells_per_case"],
                expected["expected_independent_NA_cells_per_case"]):
            raise SystemExit("Independent required coverage changed: " + case)
        if [state["id"] for state in plan["states"]] != [
                "start", "after-primary", "after-replacement", "replacement-full", "after-last"]:
            raise SystemExit("Five-state identity changed: " + case)
        run("review_contract.py", "catalog", "--plan", target / "plan.json",
            "--design-lock", output / "reproduced-lock.json", "--design-sha256", lock_sha,
            "--policy", design / "policy.json", "--policy-sha256",
            approval["canonical_sha256"]["policy"], "--platform", platform,
            "--output", target / "catalog.json")
        if load(target / "catalog.json")["rows"]:
            raise SystemExit("Unexpected image obligation; review is a source duty")
        run("requirement_routes.py", "audit", "--plan", target / "plan.json",
            "--design-lock", output / "reproduced-lock.json", "--design-sha256", lock_sha,
            "--routes", design / "routes.json", "--routes-sha256",
            approval["canonical_sha256"]["routes"], "--output", target / "route-audit.json",
            allowed=(0, 1, 3))
        audit = load(target / "route-audit.json")
        if audit["must_route_gaps"] != ["mounted-component-instance"]:
            raise SystemExit("Unexpected missing mandatory route: " + case)
        if audit["unowned_assertions"]:
            raise SystemExit("Generated native facts lack independent obligation ownership: " + case)
        summary["cases"].append({"case": case, "scenario": scenario, "platform": platform,
                                  "required_native_assertions": len(required),
                                  "matrix_cells": len(cells), "explicit_NA_cells": len(na),
                                  "plan_sha256": file_digest(target / "plan.json"),
                                  "actions_sha256": file_digest(target / "actions.json"),
                                  "source_review_duty": "thin-bridge-decodes-calls (actual observation pending)",
                                  "mounted_component_relation": "mandatory U; no provider"})
    dump(output / "preparation-report.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
