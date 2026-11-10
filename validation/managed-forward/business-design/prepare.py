#!/usr/bin/env python3
"""Mechanically validate and compile fixed Menu Change design inputs; no SDK use.

This script never authors an expectation, changes a fixture/bridge/contract/policy,
reads product source, runs a native renderer, or supplies a review decision. Normal
mode needs fresh generated outputs. --verify recomputes the same generated JSON
without changing files. Independent review is recorded outside these outputs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOL_ROOT = ROOT.parent / "candidate-v12.6"
sys.dont_write_bytecode = True
sys.path.insert(0, str(TOOL_ROOT / "scripts"))
import design_contract as design
import execution_plan
import requirement_routes
import review_contract


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def source_associations(reference, routes):
    """Check independent association completeness, not frozen-tool source routing."""
    claims = reference["responsibilities"]
    required = {c["id"] for c in claims if c["method"] == "source" and c["priority"] == "must"}
    associations = reference["source_obligation_routes"]
    if set(associations) != required:
        raise ValueError("Every mandatory source claim needs its exact declared association")
    known = {o["id"] for o in reference["obligations"]}
    for claim, obligations in associations.items():
        if not obligations or len(obligations) != len(set(obligations)) or not set(obligations) <= known:
            raise ValueError("Source association names an unknown or empty obligation route")
        if any(claim not in routes["routes"][o]["reason"] for o in obligations):
            raise ValueError("Each linked route reason must identify the extra mandatory source claim")
    if len({c["id"] for c in claims}) != len(claims):
        raise ValueError("Duplicate evidence responsibility identity")
    for c in claims:
        if set(c) != {"id", "clause", "priority", "owner", "method", "subject", "rule_ids"}:
            raise ValueError("Exact public evidence responsibility claim schema required")
        if c["method"] == "source" and (c["rule_ids"] or c["owner"] not in {"component", "bridge"}):
            raise ValueError("Source duties cannot borrow native assertion IDs or unsupported owners")
    return {"mandatory_source_claims": len(required),
            "association_check": "complete",
            "execution_limit": "Only textual independent association completeness was checked. The frozen requirement router does not execute source routing. Current source observations are separately required by the default responsibility gate."}


def validate_environment(expected, fixtures, platform):
    fields = {"width", "height", "direction", "theme", "dynamic_type" if platform == "ios" else "font_scale"}
    if platform == "android":
        fields.add("dimension_encoding")
    if set(expected) != fields:
        raise ValueError("Exact approved native environment field schema required")
    aliases = {"height": "viewportHeight", "font_scale": "fontScale"}
    for key in fields - {"dimension_encoding"}:
        if expected[key] != fixtures[aliases.get(key, key)]:
            raise ValueError("Expected environment and locked caller configuration disagree: " + key)
    if platform == "android" and expected["dimension_encoding"] != "paparazzi-float32-screen-config-v1":
        raise ValueError("Pinned provider encoding required")
    # This proves only approved-input consistency. It has no actual native packet.


def prepare(scope, verify=False):
    root = ROOT / scope
    spec = design.load(root / "design-inputs.json")
    contract = design.load(root / "contract.json")
    if set(contract["scenarios"]) != {spec["case"]}:
        raise ValueError("This sealed scope fixes exactly one scenario")
    case = spec["case"]
    fixtures = design.load(root / "cases" / case / "fixtures.json")
    reference = design.load(root / "reference.json")
    bindings = design.load(root / "bindings.json")
    routes = design.load(root / "routes.json")
    policy = design.load(root / "policy.json")
    integration = design.load(root / "integration.json")
    if integration["responsibility_ref"] != {"source": "reference", "pointer": "/responsibilities"}:
        raise ValueError("Fixed responsibility source required")
    if set(integration) != {"component_files", "responsibility_ref"}:
        raise ValueError("Integration declares only production paths and responsibility source")
    if set(integration["component_files"]) != {"ios", "android"} or any(len(v) != 1 for v in integration["component_files"].values()):
        raise ValueError("One new production file per platform is required")
    lock = design.seal(root / "contract.json", root)
    lock_sha = design.digest(lock)
    policy_sha, routes_sha = design.digest(policy), design.digest(routes)
    association = source_associations(reference, routes)
    output = {"design-lock.json": lock}
    summary = {"version": 1, "status": "awaiting_independent_design_review", "scope": scope,
               "design_lock_sha256": lock_sha, "policy_sha256": policy_sha, "routes_sha256": routes_sha,
               "environment_sha256": {case: {}}, "launch_ref": {case: {}}, "plans": {case: {}},
               "source_associations": association,
               "validation_scope": "Typed-source/route/policy/launch consistency only. No product source, source observations, native SDK execution, rendering, visual actuals, test pass, defect denominator or independent approval is claimed."}
    logical_actions = contract["scenarios"][case]["actions"]
    actions = copy.deepcopy(logical_actions)
    for action in actions:
        for key in ["target", "after_target"]:
            if isinstance(action.get(key), str):
                action[key] = copy.deepcopy(bindings[action[key]])
        for condition in action.get("preconditions", []):
            if isinstance(condition.get("target"), str):
                condition["target"] = copy.deepcopy(bindings[condition["target"]])
    for platform in ["ios", "android"]:
        env = design.load(root / "cases" / case / ("environment." + platform + ".json"))
        validate_environment(env, fixtures, platform)
        bridge = root / ("Bridge.swift" if platform == "ios" else "ObserverBridge.kt")
        launch_ref = {"source": "reference", "pointer": "/launch/" + case + "/" + platform}
        plan, enriched = design.compile_contract(lock, lock_sha, case, platform, bindings, actions)
        design.verify_generated(plan, lock, lock_sha, platform)
        catalog = review_contract.catalog(plan, lock, lock_sha, policy, policy_sha, platform)
        coverage = requirement_routes.audit(lock, lock_sha, plan, routes, routes_sha)
        if coverage["must_route_gaps"] or coverage["unowned_assertions"]:
            raise ValueError("Native/visual route coverage gaps: " + repr(coverage))
        # No execution: reconstruct only, to check the sealed fixture/bridge launch.
        execution = execution_plan.compile_execution(plan, lock, lock_sha, fixtures, file_sha(bridge), launch_ref=launch_ref)
        execution_plan.verify_execution(execution, plan, lock, lock_sha, fixtures, file_sha(bridge))
        base = "compiled/" + case + "/" + platform + "/"
        output[base + "plan.json"] = plan
        output[base + "actions.json"] = enriched
        output[base + "catalog.json"] = dict(catalog, catalog_sha256=design.digest(catalog))
        output[base + "coverage.json"] = coverage
        output[base + "launch-summary.json"] = {
            "launch_ref": launch_ref, "launch": design.pointer(reference, launch_ref["pointer"]),
            "execution_manifest_sha256": execution["execution_sha256"],
            "selected_states": execution["selected_states"],
            "business_action_count": len(actions), "native_execution": "not_performed"}
        summary["environment_sha256"][case][platform] = design.digest(env)
        summary["launch_ref"][case][platform] = launch_ref
        summary["plans"][case][platform] = {"plan_sha256": design.digest(plan), "assertions": len(plan["assertions"]),
            "matrix_cells": len(plan["matrix_contract"]["cells"]), "manual_catalog_atoms": len(catalog["rows"]),
            "selected_states": len(plan["states"]), "must_route_gaps": coverage["must_route_gaps"],
            "unowned_assertions": coverage["unowned_assertions"]}
    output["approval.json"] = summary
    inputs = [p for p in root.rglob("*") if p.is_file() and "compiled" not in p.relative_to(root).parts and p.name not in {"design-lock.json", "approval.json", "seal.json"}]
    sealed = {str(p.relative_to(root)): file_sha(p) for p in sorted(inputs)}
    sealed.update({name: hashlib.sha256(encoded(value)).hexdigest() for name, value in output.items()})
    output["seal.json"] = {"version": 1, "scope": scope, "design_lock_sha256": lock_sha,
        "policy_sha256": policy_sha, "routes_sha256": routes_sha,
        "files": dict(sorted(sealed.items())),
        "independent_review": "pending; retain a separate original external approval referencing this seal's canonical digest before implementation",
        "scope_limit": "Design/input seal only; no implementation or native evaluation exists in this scope."}
    for name, value in output.items():
        path = root / name
        data = encoded(value)
        if verify:
            if not path.is_file() or path.read_bytes() != data:
                raise ValueError("Generated bytes differ: " + str(path))
        elif path.exists():
            raise ValueError("Fresh generated output required: " + str(path))
    if not verify:
        for name, value in output.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as f:
                f.write(encoded(value))
    return {"scope": scope, "mode": "verified_existing_design_bytes" if verify else "prepared_design_only",
        "design_lock_sha256": lock_sha, "scope_seal_sha256": design.digest(output["seal.json"]),
        "approval_summary_sha256": design.digest(summary), "states": 8,
        "source_claims": association["mandatory_source_claims"], "independent_approval": "pending", "native_execution": "not_performed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=["public", "private", "all"], default="all")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    scopes = ["public", "private"] if args.scope == "all" else [args.scope]
    for scope in scopes:
        print(json.dumps(prepare(scope, args.verify), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
