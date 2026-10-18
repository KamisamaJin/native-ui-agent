#!/usr/bin/env python3
"""Prepare/validate/seal anonymous D0 grading records. Does not grade packets.

Reads only this design team's frozen public/private artifacts and explicit files
under grader/. Evidence paths are references; their contents are never opened.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
GRADER = ROOT / "grader"
DESIGN = ["public/brief.md", "public/reference.svg", "private/oracle.json",
          "private/protocol-notes.md"]
OUTCOMES = {"passed", "failed", "not_executed", "not_assessed", "unscorable",
            "blocked", "infrastructure_error"}
METHODS = {"native_semantics", "native_pixels", "blinded_visual", "source_review"}
RUNTIME_SCOPES = {"runtime_callback", "runtime_hit_test", "runtime_accessibility"}
BLIND_FLAGS = ["treatment_mapping_seen", "assignment_seen", "self_review_claims_seen",
               "implementation_directory_read", "skill_files_read",
               "sibling_conversations_read"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def design_hashes():
    return {name: digest((ROOT / name).read_bytes()) for name in DESIGN}


def output_path(name):
    p = Path(name).expanduser().resolve()
    if p == GRADER or GRADER not in p.parents:
        raise ValueError("Grading inputs/outputs must be explicit files under design-team/grader/")
    return p


def read_record(name):
    return json.loads(output_path(name).read_text(encoding="utf-8"))


def write_json(name, value, exclusive=False):
    p = output_path(name)
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    with p.open("x" if exclusive else "w", encoding="utf-8") as f:
        f.write(data)
    return p, digest(data.encode("utf-8"))


def make_template(anonymous_id):
    oracle = json.loads((ROOT / "private/oracle.json").read_text(encoding="utf-8"))
    cases = []
    for fixture in oracle["fixtures"]:
        if fixture["stage"] != "initial":
            continue
        for platform in fixture["platforms"]:
            cases.append({
                "case_id": fixture["fixture_id"], "platform": platform,
                "packet_pseudonym": None, "packet_paths": [],
                "build": {"status": "not_assessed", "evidence": None, "observation": None},
                "render": {"status": "not_assessed", "evidence": None, "observation": None},
                "viewport_evidence": {"top": None, "bottom": None,
                                      "lower_content_assessed": False},
                "incidences": [{
                    "rule_id": rule["rule_id"], "applicable": True,
                    "applicability_reason": "Public rule; assess only its relevant branches.",
                    "coverage_complete": False, "coverage": "none",
                    "status": "not_assessed", "checks": [], "findings": [],
                    "visual_rating": None,
                    "limitation": (
                        "Known host: iOS AX unavailable even for control probe. Do not fail "
                        "component from empty AX. Source review is declaration evidence only; "
                        "callbacks without actual native events are not_executed."
                        if platform == "swiftui_ios" else None)
                } for rule in oracle["rules"]]
            })
    return {
        "schema_version": "1.0", "artifact_role": "ungraded_template",
        "stage": "D0", "anonymous_implementation_id": anonymous_id,
        "reviewer_type": "independent_AI_not_human_expert",
        "design_sha256": design_hashes(),
        "blinding": {name: False for name in BLIND_FLAGS},
        "d0_source_frozen_revision": None, "review_started_at": None,
        "review_completed_at": None, "sealed_before_self_review_matching": False,
        "global_blockers": [],
        "case_count": len(cases),
        "rule_incidence_count": sum(len(c["incidences"]) for c in cases),
        "status_vocabulary": sorted(OUTCOMES),
        "method_vocabulary": sorted(METHODS),
        "visual_anchors": oracle["blinded_visual_rubric"]["anchors"],
        "check_record_example_do_not_score": {
            "aspect": "Describe one public requirement being checked",
            "scope": "rendered|static_contract|runtime_callback|runtime_hit_test|runtime_accessibility",
            "status": "not_assessed", "method": None,
            "execution": "not_executed", "evidence": [],
            "observation": None, "expected_public_rule": None,
            "actual_callback_events": None, "expected_callback_events": None,
            "note": "Example only. Never copy expected values into observed fields."
        },
        "cases": cases,
        "seal_policy": "D0 rating is sealed before seeing self-review claims. Detection matching is a later separate artifact."
    }


def aggregate_incidence(incidence):
    """Coverage and outcome remain separate. Missing branches cannot create a pass."""
    if not incidence.get("applicable", True):
        return "not_assessed", "none"
    checks = incidence.get("checks", [])
    observed = [c for c in checks if c.get("execution") == "observed"]
    coverage = "complete" if incidence.get("coverage_complete") else "partial" if observed else "none"
    statuses = [c.get("status", "not_assessed") for c in checks]
    if "failed" in statuses:
        return "failed", coverage
    if "blocked" in statuses:
        return "blocked", coverage
    if "infrastructure_error" in statuses:
        return "infrastructure_error", coverage
    if checks and incidence.get("coverage_complete") and all(s == "passed" for s in statuses):
        return "passed", coverage
    if statuses and all(s == "not_executed" for s in statuses):
        return "not_executed", coverage
    if "unscorable" in statuses:
        return "unscorable", coverage
    return "not_assessed", coverage


def validate(record, require_sealable=False):
    errors, warnings = [], []
    if record.get("stage") != "D0":
        errors.append("This helper seals only D0. Use a separate artifact for later detection matching.")
    for flag in BLIND_FLAGS:
        if record.get("blinding", {}).get(flag) is not False:
            errors.append("D0 blindness declaration must be explicitly false: " + flag)
    if record.get("design_sha256") != design_hashes():
        errors.append("Frozen design artifact hashes differ from the template. Do not modify the design.")
    oracle = json.loads((ROOT / "private/oracle.json").read_text(encoding="utf-8"))
    rule_methods = {r["rule_id"]: set(r["measurement_methods"]) for r in oracle["rules"]}
    expected_pairs = {(f["fixture_id"], p) for f in oracle["fixtures"] if f["stage"] == "initial" for p in f["platforms"]}
    actual_pairs = [(c.get("case_id"), c.get("platform")) for c in record.get("cases", [])]
    if set(actual_pairs) != expected_pairs or len(actual_pairs) != len(expected_pairs):
        errors.append("Expected exactly six initial cases per platform, without duplicate pairs.")
    for case in record.get("cases", []):
        prefix = str(case.get("case_id")) + "/" + str(case.get("platform"))
        ids = [i.get("rule_id") for i in case.get("incidences", [])]
        if set(ids) != set(rule_methods) or len(ids) != len(rule_methods):
            errors.append(prefix + ": exact public rule incidence set required.")
        for incidence in case.get("incidences", []):
            key = prefix + "/" + str(incidence.get("rule_id"))
            if incidence.get("status") not in OUTCOMES:
                errors.append(key + ": invalid outcome.")
            if not incidence.get("applicable", True) and not incidence.get("applicability_reason"):
                errors.append(key + ": omitted applicability needs a reason.")
            for check in incidence.get("checks", []):
                method, status = check.get("method"), check.get("status")
                scope, execution = check.get("scope"), check.get("execution")
                if status not in OUTCOMES:
                    errors.append(key + ": invalid check outcome.")
                if method is not None and method not in rule_methods.get(incidence.get("rule_id"), set()):
                    errors.append(key + ": method is not admitted by frozen oracle.")
                if status in {"passed", "failed"}:
                    if not check.get("evidence") or not check.get("observation") or execution != "observed":
                        errors.append(key + ": pass/fail requires observed evidence and specific observation.")
                if status == "passed" and scope in RUNTIME_SCOPES:
                    if method == "source_review":
                        errors.append(key + ": source review cannot pass runtime behavior.")
                    if method != "native_semantics":
                        errors.append(key + ": runtime pass needs actual native-event/semantics evidence.")
                if status == "passed" and scope == "runtime_callback":
                    if check.get("actual_callback_events") is None or check.get("expected_callback_events") is None:
                        errors.append(key + ": executed callback pass requires actual and expected event arrays.")
                    elif check["actual_callback_events"] != check["expected_callback_events"]:
                        errors.append(key + ": callback arrays differ; cannot pass.")
                if case.get("platform") == "swiftui_ios" and check.get("aspect") == "empty_AX_export" and status == "failed":
                    errors.append(key + ": known iOS host AX limitation is not a component failure.")
            expected_status, expected_coverage = aggregate_incidence(incidence)
            if incidence.get("status") != expected_status or incidence.get("coverage") != expected_coverage:
                errors.append(key + ": outcome/coverage inconsistent with checks; expected " + expected_status + "/" + expected_coverage)
            rating = incidence.get("visual_rating")
            if rating is not None:
                if incidence.get("rule_id") not in {"TQ-VIS-01", "TQ-VIS-02"}:
                    errors.append(key + ": visual rating belongs only to visual rules.")
                if not isinstance(rating, dict) or type(rating.get("score")) is not int or not 1 <= rating.get("score", 0) <= 5:
                    errors.append(key + ": visual score must be integer 1–5.")
                elif not rating.get("evidence") or not rating.get("specific_observation"):
                    errors.append(key + ": visual rating needs evidence and a concrete observation.")
            elif incidence.get("rule_id") in {"TQ-VIS-01", "TQ-VIS-02"}:
                warnings.append(key + ": no visual rating; keep unassessed if evidence unavailable.")
    if require_sealable:
        if record.get("artifact_role") != "D0_rating":
            errors.append("Change artifact_role to D0_rating only after real anonymous review.")
        for field in ["d0_source_frozen_revision", "review_started_at", "review_completed_at"]:
            if not record.get(field):
                errors.append("Sealing requires " + field)
        if not record.get("sealed_before_self_review_matching"):
            errors.append("Explicitly declare seal-before-self-review-matching.")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def summarize(record):
    result = {}
    for platform in ["compose_android", "swiftui_ios"]:
        incidences = [i for c in record.get("cases", []) if c.get("platform") == platform for i in c.get("incidences", [])]
        result[platform] = {"incidences": len(incidences),
                            "outcomes": dict(Counter(i.get("status") for i in incidences)),
                            "coverage": dict(Counter(i.get("coverage") for i in incidences))}
    return {"anonymous_id": record.get("anonymous_implementation_id"),
            "global_blockers": record.get("global_blockers", []),
            "platform_counts": result,
            "interpretation": "Counts describe evidence coverage/outcomes. No missing-evidence exclusion, inferred group comparison, or combined quality score."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    create = subs.add_parser("init")
    create.add_argument("--anonymous-id", required=True)
    create.add_argument("--out", required=True)
    for name in ["validate", "summarize"]:
        p = subs.add_parser(name); p.add_argument("record")
    seal = subs.add_parser("seal")
    seal.add_argument("record"); seal.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command == "init":
        p, sha = write_json(args.out, make_template(args.anonymous_id), exclusive=True)
        print(json.dumps({"created": str(p), "sha256": sha, "graded": False}))
        return
    record = read_record(args.record)
    if args.command == "summarize":
        print(json.dumps(summarize(record), ensure_ascii=False, indent=2)); return
    verdict = validate(record, require_sealable=args.command == "seal")
    if args.command == "validate" or not verdict["valid"]:
        print(json.dumps(verdict, ensure_ascii=False, indent=2))
        if not verdict["valid"]: sys.exit(1)
        return
    sealed = {"seal_type": "D0_rating_before_self_review_claims", "rating": record}
    p, sha = write_json(args.out, sealed, exclusive=True)
    sidecar = output_path(str(p) + ".sha256")
    with sidecar.open("x", encoding="utf-8") as f:
        f.write(sha + "  " + p.name + "\n")
    print(json.dumps({"sealed": str(p), "sha256": sha,
                      "note": "Self-review matching must be a later separate artifact."}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
