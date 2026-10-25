#!/usr/bin/env python3
"""Independent controls for the revised guard; no new native runs or source edits."""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE / "source-snapshot"))
import ax_calibration as calibration
import native_geometry as geometry


def load(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    snapshot = load(HERE / "SNAPSHOT.json")
    assert sha(HERE.parent / "SEAL.json") == snapshot["initial_review_seal_sha256"]
    initial = load(HERE.parent / "SEAL.json")
    for name, digest in initial["files"].items():
        assert sha(HERE.parent / name) == digest
    for name, digest in snapshot["source_files"].items():
        assert sha(HERE / "source-snapshot" / name) == digest
    raw_context = load(HERE.parent / "RAW-CONTEXT.json")
    for name, digest in raw_context["inputs"].items():
        assert sha(REPO / name) == digest
    extraction = load(REPO / "validation/routed-forward/cache/ax-run-2/calibration-rows.json")
    observation = load(REPO / "validation/routed-forward/cache/ax-run-2/observation.json")
    context = raw_context["fit_profile_context"]
    provenance = {"probe_seal_sha256": sha(REPO / "validation/routed-forward/ax-probe/SEAL.json"),
                  "observation_sha256": sha(REPO / "validation/routed-forward/cache/ax-run-2/observation.json"),
                  "extraction_sha256": sha(REPO / "validation/routed-forward/cache/ax-run-2/calibration-rows.json")}
    profile = calibration.fit(extraction, context, provenance)
    assert profile["status"] == "validated" and profile["factor"] == 1
    assert profile["fit_rows"] == 87 and profile["heldout_rows"] == 62
    assert all(v == 0 for r in profile["raw_residuals"] for v in r["residuals"].values())
    row = next(r for r in extraction["rows"] if r["identifier"] == "axprobe.p00"
               and r["fully_within_viewport"])
    frame = copy.deepcopy(row["raw_xcui_frame"])
    source = {"provider": "xcui_cgrect", "unit": "pt", "sample": frame}
    measurement = {"property": "width", "snapshot": row["snapshot_index"],
                   "ratio": [67, 1], "sources": [source]}
    def call(m, p=profile, r=context):
        return calibration.classify(m, 68, "gte", None, p, r)
    controls = {}
    def keep(name, value, expected):
        assert value["classification"] == expected
        controls[name] = value
    keep("ordinary_external_proof_without_reference", call(measurement), "outside_calibrated_scope")
    pinned = copy.deepcopy(measurement)
    pinned["sources"][0]["calibration_reference"] = {
        "extraction_sha256": provenance["extraction_sha256"], "identifier": row["identifier"]}
    keep("matching_record_metadata", call(pinned), "definite_within_profile")
    wrong_digest = copy.deepcopy(pinned)
    wrong_digest["sources"][0]["calibration_reference"]["extraction_sha256"] = "0" * 64
    keep("wrong_extraction_digest", call(wrong_digest), "outside_calibrated_scope")
    wrong_id = copy.deepcopy(pinned)
    wrong_id["sources"][0]["calibration_reference"]["identifier"] = "review.synthetic.external"
    keep("wrong_native_reference_identifier", call(wrong_id), "outside_calibrated_scope")
    one_ulp = copy.deepcopy(pinned)
    one_ulp["sources"][0]["sample"]["x"] += math.ulp(frame["x"])
    keep("one_ulp_frame_mismatch", call(one_ulp), "outside_calibrated_scope")
    for name, patch in (("negative_origin", {"x": -frame["x"], "y": -frame["y"]}),
                        ("cross_axis_x_500", {"x": 500}), ("below_sampled_width_1", {"width": 1})):
        changed = copy.deepcopy(pinned)
        changed["sources"][0]["sample"].update(patch)
        keep(name, call(changed), "outside_calibrated_scope")
    replay = copy.deepcopy(pinned)
    replay["sources"][0].update({"selector": {"identifier": "review.synthetic.external"},
                                 "native_view_class": "SyntheticSwiftUICustomAX",
                                 "local_transform_identity": False,
                                 "snapshot": 999999, "process_instance": "synthetic-different-process"})
    keep("caller_metadata_can_replay_probe_reference_without_runtime_binding", call(replay),
         "definite_within_profile")
    pixels = copy.deepcopy(pinned)
    pixels["sources"][0]["unit"] = "px"
    keep("matching_record_but_source_unit_px", call(pixels), "definite_within_profile")
    keep("wrong_query_os_context", call(pinned, r=dict(context, os_version="synthetic-other-os")),
         "outside_calibrated_scope")
    fit_controls = {}
    for name, key, value in (("false_local_identity_flag", "local_transform_identity", False),
                             ("false_ancestor_identity_flag", "ancestor_transforms_identity", False),
                             ("wrong_runtime_identifier", "reference_identity", "synthetic-other-id"),
                             ("wrong_runtime_os", "os_version", "synthetic-other-os")):
        changed = copy.deepcopy(extraction)
        for candidate in changed["rows"]:
            if candidate["identifier"] == "axprobe.p00":
                candidate["runtime"][key] = value
        p = calibration.fit(changed, context, provenance)
        assert p["status"] == "unsupported_or_incomplete" and p["rejected_rows"]
        fit_controls[name] = {"status": p["status"], "rejected_rows": len(p["rejected_rows"])}
    bad_context = calibration.fit(extraction, dict(context, screen_scale=999), provenance)
    assert bad_context["status"] == "unsupported_or_incomplete"
    fit_controls["unrelated_context"] = {"status": bad_context["status"]}
    bad_provenance = calibration.fit(extraction, context, {"extraction_sha256": "not-a-digest"})
    assert bad_provenance["status"] == "validated"
    fit_controls["provenance_not_verified_by_fit"] = {"status": bad_provenance["status"]}
    changed = copy.deepcopy(extraction)
    for candidate in changed["rows"]:
        candidate["runtime"]["local_transform"]["a"] = 2
    matrix_only = calibration.fit(changed, context, provenance)
    assert matrix_only["status"] == "validated"
    fit_controls["contradictory_transform_matrix_with_true_flags"] = {"status": matrix_only["status"],
        "meaning": "Synthetic dictionary control: boolean flag checks do not independently authenticate the native transform or the extraction."}
    plan = {"design_contract": {"platform": "ios"}, "assertions": [
        {"id": "neutral-after-width", "kind": "geometry", "property": "width", "expected": 68, "op": "gte"}]}
    report = {"rows": [{"id": "neutral-after-width", "status": "failed", "geometry_evidence": [measurement]}]}
    before_report, before_plan = copy.deepcopy(report), copy.deepcopy(plan)
    annotated = calibration.annotate(plan, observation, report, profile)
    assert report == before_report and plan == before_plan
    assert annotated["rows"][0]["status"] == "failed"
    assert annotated["rows"][0]["measurement_calibration"]["classification"] == "outside_calibrated_scope"
    del annotated["rows"][0]["measurement_calibration"]
    assert annotated == report and geometry.compare(measurement, 68, "gte") is False
    result = {"schema": "ax-calibration.after-review.controls.v1",
              "reviewed_source_sha256": snapshot["source_files"]["ax_calibration.py"],
              "profile_summary": {k: profile[k] for k in ("status", "factor", "fit_rows", "heldout_rows", "scope")},
              "classification_controls": controls, "fit_controls": fit_controls,
              "strict_outcomes": {"original_plan_unchanged": True, "original_report_unchanged": True,
                                  "raw_failed_status_preserved": True, "threshold_unchanged": 68,
                                  "normal_external_annotation": "outside_calibrated_scope"},
              "limits": ["No new native observations; all real residuals remain zero.",
                         "Matching caller-supplied reference metadata proves dictionary membership, not target runtime identity or same capture/process.",
                         "Synthetic metadata controls are not newly measured native transform or scope evidence.",
                         "Positive residual behavior remains untested; original raw P/F and tolerances are unchanged."],
              "disposition": "Ordinary external-source guard and fit metadata consistency checks work. Exact record membership is narrower than the former domain box, but must not be claimed as independently authenticated runtime scope."}
    (HERE / "CONTROLS.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    (HERE / "reproduced-profile.json").write_text(json.dumps(profile, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"external_source_guard": "passed", "exact_membership_guards": "passed",
                      "fit_context_and_identity_flag_guards": "passed", "strict_outcomes": "unchanged",
                      "metadata_replay_is_not_runtime_attestation": True, "positive_residual_observations": 0}))


if __name__ == "__main__":
    main()
