#!/usr/bin/env python3
"""Read-only PRE-NATIVE ABI/integrity checks. No SDK/native/build invocation."""
from __future__ import annotations

import hashlib
import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
BASE = OUT.parents[1]
DESIGN = BASE / "qualification/neutral-design/executable-profile"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--profiles", type=Path, default=BASE / "cache/qualification/profiles")
ARGS = parser.parse_args()
PROFILES = ARGS.profiles.resolve()
WORKSPACE = BASE / "cache/qualification/workspace"
BASELINE = BASE / "baseline-v12.6"
READS = {}
CHECKS = []


def raw(path, mode="semantic"):
    path = Path(path).resolve()
    data = path.read_bytes()
    READS[str(path.relative_to(BASE))] = {
        "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "mode": mode
    }
    return data


def load(path):
    return json.loads(raw(path))


def canon(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canon(value)).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def check(name, passed, details=None):
    CHECKS.append({"check": name, "passed": bool(passed), "details": details})


approval = load(DESIGN / "approval.json")
for name, expected in approval["baseline_compiler_sha256"].items():
    actual = hashlib.sha256(raw(BASELINE / "scripts" / name)).hexdigest()
    check("baseline approved pure compiler " + name, actual == expected, {"expected": expected, "actual": actual})
if not all(row["passed"] for row in CHECKS):
    raise SystemExit("Baseline compiler bytes differ from approval; nothing executed")

# These imported functions only perform schema/canonical compilation. The run,
# SDK, device, native capture, resource and source-review binding functions are
# deliberately never called. Bytecode generation is disabled.
sys.path.insert(0, str(BASELINE / "scripts"))
import design_contract as design
import review_contract as review
import requirement_routes as routes
import execution_plan as execution
import evidence_responsibility as responsibility
import acceptance

lock = load(DESIGN / "approved-lock.json")
reproduced = design.seal(DESIGN / "contract.json", DESIGN)
dump(OUT / "independent-compile/reproduced-lock.json", reproduced)
check("independently reproduced lock", reproduced == lock, {
    "canonical_sha256": digest(reproduced), "approved": approval["canonical_sha256"]["design_lock"]
})
for key, name in [("design_lock", "approved-lock.json"), ("policy", "policy.json"),
                  ("routes", "routes.json"), ("environment_ios", "environment.ios.json"),
                  ("environment_android", "environment.android.json"), ("resources", "resources.json")]:
    actual = digest(load(DESIGN / name))
    check("canonical approval " + key, actual == approval["canonical_sha256"][key], actual)

bindings = load(DESIGN / "bindings.json")
actions = load(DESIGN / "actions.json")
oracle = load(BASE / "qualification/spec/modular-fixture/ORACLE.json")
reference = load(DESIGN / "reference.json")
required = load(DESIGN / "required-obligations.json")
gates = load(DESIGN / "native-safety-gates.json")
overall = load(DESIGN / "overall-capabilities.json")
policy = load(DESIGN / "policy.json")
route_map = load(DESIGN / "routes.json")
check("original action bytes retained", raw(DESIGN / "actions.json") == raw(BASE / "qualification/spec/fixture/actions.json"))
check("mandatory native safety gates", len(gates["gates"]) == 7 and
      {g["id"] for g in gates["gates"]} == set(required["mandatory_raw_native_gate_ids"]) and
      all(g["priority"] == "must" for g in gates["gates"]))
check("advisory U retained", overall["retained"] == reference["overall_capability_ledger"] and
      len(overall["retained"]) == 1 and overall["retained"][0]["id"] == "mounted-component-instance" and
      overall["retained"][0]["priority"] == "advisory" and overall["retained"][0]["status"] == "U")
check("validity scope and policy unchanged", reference["capture_validity"] == approval["capture_validity"] == {
    "scope": "deterministic_component_fixture", "max_age_seconds": 3600,
    "reset": "fresh_native_fixture", "external_state": "all_dependencies_pinned"
})

case_summaries = []
for case, scenario, platform in [("ios-cold", "neutral-A", "ios"), ("ios-warm", "neutral-B", "ios"), ("android", "neutral-A", "android")]:
    config = load(PROFILES / (case + ".json"))
    expected_plan = load(DESIGN / "prepared" / case / "plan.json")
    plan, generated_actions = design.compile_contract(lock, config["design_sha256"], scenario, platform, bindings, actions)
    target = OUT / "independent-compile" / case
    dump(target / "plan.json", plan)
    dump(target / "actions.json", generated_actions)
    check(case + " exact generated plan", plan == expected_plan)
    check(case + " exact generated actions", generated_actions == load(DESIGN / "prepared" / case / "actions.json"))
    check(case + " concrete plan pointer", Path(config["plan"]).resolve() == (DESIGN / "prepared" / case / "plan.json").resolve())
    for field, pinned_key in [("design_sha256", "design_lock"), ("policy_sha256", "policy"), ("routes_sha256", "routes"), ("environment_sha256", "environment_" + platform)]:
        check(case + " config approved " + field, config[field] == approval["canonical_sha256"][pinned_key])
    for field, name in [("design_lock", "approved-lock.json"), ("routes", "routes.json"), ("policy", "policy.json"), ("environment", "environment." + platform + ".json"), ("fixtures", "fixtures/" + case + ".json")]:
        check(case + " exact bound path " + field, Path(config[field]).resolve() == (DESIGN / name).resolve())
    fixture = load(Path(config["fixtures"]))
    check(case + " original scalar fixture bytes", raw(Path(config["fixtures"])) == raw(BASE / "qualification/spec/fixture" / (case + ".json")))
    compiled = execution.compile_execution(plan, lock, config["design_sha256"], fixture,
        hashlib.sha256(raw(Path(config["bridge"]))).hexdigest(), launch_ref=config["launch_ref"])
    dump(target / "execution.json", compiled)
    check(case + " full ordinary execution", compiled["scope"] == "full" and compiled["executed_action_count"] == 5 and
          compiled["selected_states"] == ["start", "after-primary", "after-replacement", "replacement-full", "after-last"])
    cells = plan["matrix_contract"]["cells"]
    nas = [c for c in cells if c["disposition"] == "not_applicable"]
    check(case + " complete 104/170/66 frozen matrix", len(plan["required_assertion_ids"]) == len(set(plan["required_assertion_ids"])) == 104 and
          len(plan["assertions"]) == 104 and len(cells) == 170 and len(nas) == 66 and all(c["reason"].strip() for c in nas))
    by_id = {r["id"]: r for r in plan["assertions"]}
    for state in plan["states"]:
        sid = state["id"]
        values = fixture["initial"] if state["input_index"] == 0 else fixture["updates"][0]
        original = next(row for row in oracle["state_expectations"] if row["state"] == sid)
        check(case + " original scalar/count oracle " + sid,
              state["input_index"] == original["input_index"] and state["after_action"] == original["after_action"] and
              by_id[sid + "/marker-label"]["expected"] == values["marker"] and
              by_id[sid + "/detail-label"]["expected"] == values["detail"] and
              by_id[sid + "/count-label"]["expected"] == original["count_label"])
    for sid, rid in [("after-primary", "primary-callback"), ("after-replacement", "caller-update-quiet"), ("after-last", "last-callback")]:
        original = next(row for row in oracle["state_expectations"] if row["state"] == sid)
        row = by_id[sid + "/" + rid]
        check(case + " original stimulus/callback oracle " + sid, row["expected"] == original["exact_callback_delta"] and
              row["action_index"] == original["after_action"] and row["stimulus"] == ("caller_update" if sid == "after-replacement" else "activation"))
    for state in ["start", "replacement-full"]:
        rows = [r for r in plan["assertions"] if r["state"] == state and r["requirement_id"].startswith("row-")]
        state_coverage = next(c for c in compiled["required_coverage"] if c["state_id"] == state)
        check(case + " all eighteen row labels/full coverage " + state, len(rows) == 18 and
              {r["expected"] for r in rows} == {"Native content row " + str(i) for i in range(1, 19)} and
              state_coverage["coverage"] == "full_content")
    audit = routes.audit(lock, config["design_sha256"], plan, route_map, config["routes_sha256"])
    dump(target / "route-audit.json", audit)
    check(case + " zero mandatory gaps/unowned assertions", not audit["must_route_gaps"] and not audit["unowned_assertions"])
    native_rows = [r for r in audit["obligations"] if r["priority"] == "must"]
    extra = [r for r in audit["obligations"] if r["id"] == "mounted-component-instance"]
    check(case + " nine supported mandatory and advisory route U", len(native_rows) == 9 and all(r["route_available"] for r in native_rows) and
          len(extra) == 1 and extra[0]["priority"] == "advisory" and not extra[0]["route_available"])
    catalog = review.catalog(plan, lock, config["design_sha256"], policy, config["policy_sha256"], platform)
    dump(target / "catalog.json", catalog)
    check(case + " no unsupported image atom", catalog["rows"] == [])
    claims = responsibility.compile_contract(config, plan, lock)
    dump(target / "responsibility.json", claims)
    check(case + " native/source responsibility ABI supported", claims["issues"] == [] and len(claims["claims"]) == 3)
    source_claim = next(c for c in claims["claims"] if c["id"] == "thin-bridge-decodes-calls")
    check(case + " bridge source duty current exact subject", source_claim["supported"] and source_claim["priority"] == "must" and
          set(source_claim["files"]) == {str(Path(config["bridge"]).resolve())})
    env = acceptance.environment({}, load(Path(config["environment"])), platform)
    check(case + " approved environment schema with no runtime fabrication", env["status"] == "U" and env["frames"] == [])
    allowed = {"package", "simulator", "developer-dir", "build-cache", "product", "sdk"} if platform == "ios" else {"project", "java-home", "android-sdk"}
    check(case + " default native option ABI", set(config["native_options"]) <= allowed and
          ({"package", "simulator", "developer-dir"} if platform == "ios" else {"project", "java-home", "android-sdk"}) <= set(config["native_options"]))
    normalized_resources = dict(config["resources"])
    normalized_resources.pop("root")
    check(case + " approved resources plus isolated root", normalized_resources == load(DESIGN / "resources.json"))
    case_summaries.append({"case": case, "platform": platform, "scenario": scenario,
                           "assertions": len(plan["assertions"]), "matrix_cells": len(cells), "explicit_NA": len(nas),
                           "states": compiled["selected_states"], "plan_canonical_sha256": digest(plan),
                           "execution_sha256": compiled["execution_sha256"], "source_duty": source_claim["files"],
                           "runtime_status": "pending; no native command or build executed"})

host_setup = load(BASE / "cache/hosts/setup.json")
jar = WORKSPACE / "reply/Reply/.native-ui/java-desktop.jar"
check("private desktop jar agrees with pinned host setup", hashlib.sha256(raw(jar, "hash-only declared native build dependency")).hexdigest() == host_setup["private_desktop_jar_sha256"])

# Identify concrete build declarations that are outside the explicit source and
# dependency lists; this is a declared-coverage gap, never a compiler-closure proof.
build_candidates = {
    "ios": [WORKSPACE / "alerttoast/Package.swift"],
    "android": [WORKSPACE / ("reply/Reply/" + n) for n in ["settings.gradle.kts", "build.gradle.kts", "app/build.gradle.kts",
        "gradle/libs.versions.toml", "gradle.properties", "gradle/wrapper/gradle-wrapper.properties", "gradle/wrapper/gradle-wrapper.jar",
        "buildscripts/toml-updater-config.gradle", "local.properties", "gradlew", ".native-ui/java-desktop.jar"]]
}
declarations = {}
for case in ["ios-cold", "ios-warm", "android"]:
    config = load(PROFILES / (case + ".json"))
    declaration = {}
    for platform, paths in build_candidates.items():
        roots = [Path(p).resolve() for p in config["platform_source_roots"].get(platform, [])]
        deps = {Path(p).resolve() for p in config.get("dependency_files", {}).get(platform, [])}
        rows = []
        for p in paths:
            data = raw(p, "hash-only actual build/lock configuration")
            explicit = p.resolve() in deps or any(p.resolve() == r or p.resolve().is_relative_to(r) for r in roots)
            rows.append({"path": str(p.resolve()), "sha256": hashlib.sha256(data).hexdigest(), "explicitly_declared": explicit})
        declaration[platform] = rows
    declarations[case] = declaration

# Include exact bytes of the baseline public documents/ABI examined, and every
# baseline module loaded by these pure compiler calls.
for name in ["references/default-feedback.md", "references/native-tools.md", "references/native-precision.md", "references/design-contract.md", "assets/ios-observer/CONTRACT.md",
             "scripts/ui_loop.py", "scripts/feedback_loop.py", "scripts/ios_observe.py", "scripts/android_observe.py"]:
    raw(BASELINE / name, "public baseline reference/ABI inspection only")
for module in list(sys.modules.values()):
    name = getattr(module, "__file__", None)
    if name:
        p = Path(name).resolve()
        if p.is_file() and p.is_relative_to(BASELINE):
            raw(p, "baseline pure compiler/ABI module loaded; no native run")

dump(OUT / "supplemental-readset.json", {"captured_at_utc": datetime.now(timezone.utc).isoformat(), "readset": READS,
     "native_commands": 0, "builds": 0, "sdk_commands": 0, "devices_created": 0})
dump(OUT / "static-checks.json", {"checks": CHECKS, "passed": sum(c["passed"] for c in CHECKS),
     "failed": [c for c in CHECKS if not c["passed"]], "cases": case_summaries})
dump(OUT / "declared-build-dependencies.json", {"scope": "Static explicit-declaration audit only; no compiler-dependency completeness or runtime claim",
     "profiles": declarations})
print(json.dumps({"checks": len(CHECKS), "passed": sum(c["passed"] for c in CHECKS),
                  "failed": [c for c in CHECKS if not c["passed"]], "cases": case_summaries}, indent=2))
