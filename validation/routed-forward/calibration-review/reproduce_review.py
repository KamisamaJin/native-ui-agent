#!/usr/bin/env python3
"""Read-only numerical review against frozen generic sources and sealed native data."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = HERE / "source-snapshot"
sys.path.insert(0, str(SOURCE))
import ax_calibration as calibration
import native_geometry as geometry


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds(values):
    return {k: [min(row[k] for row in values), max(row[k] for row in values)]
            for k in ("x", "y", "width", "height")}


def main():
    observed = REPO / "validation/routed-forward/cache/ax-run-2"
    probe = REPO / "validation/routed-forward/ax-probe"
    inspection = load(HERE / "INSPECTION-SNAPSHOT.json")
    for record in inspection["source_files"].values():
        assert sha(HERE / record["copy"]) == record["sha256"]
    seal = load(probe / "SEAL.json")
    for name, record in seal["files"].items():
        assert sha(probe / name) == record["sha256"]
    manifest = load(observed / "manifest.json")
    observation = load(observed / "observation.json")
    extraction = load(observed / "calibration-rows.json")
    fixtures, actions = load(probe / "fixtures.json"), load(probe / "actions.json")
    assert extraction["observation_sha256"] == sha(observed / "observation.json")
    assert manifest["source_hashes"][str(probe / "AXProbeBridge.swift")] == seal["files"]["AXProbeBridge.swift"]["sha256"]
    for key, name in (("fixtures", "fixtures.json"), ("actions", "actions.json")):
        assert manifest["input_hashes"][key] == seal["files"][name]["sha256"]
        assert load(observed / name) == load(probe / name)
    expected_input_hash = hashlib.sha256(json.dumps(fixtures["initial"], sort_keys=True,
                                                  separators=(",", ":")).encode()).hexdigest()
    rows = extraction["rows"]
    snapshots = observation["snapshots"]
    assert len(rows) == 612 and len(snapshots) == 34
    expected_ids = {p["id"] for p in fixtures["initial"]["probes"]}
    raw_lengths, raw_seen = [], set()
    for snapshot in snapshots:
        assert snapshot["capture_consistent"] is True
        assert snapshot["binding"] == snapshot["binding_after_capture"]
        assert snapshot["binding"] == snapshots[0]["binding"]
        assert snapshot["binding"]["input_sha256"] == expected_input_hash
        assert snapshot["callbacks"] == [] and snapshot["binding"]["event_revision"] == 0
        selected = [n for n in snapshot["nodes"] if n.get("identifier") in expected_ids]
        assert len(selected) == len({n["identifier"] for n in selected}) == 18
        for node in selected:
            wire = json.loads(node["value"])
            raw_lengths.append(len(node["value"].encode("ascii")))
            raw_seen.add(node["identifier"])
            assert wire["v"] == 2 and wire["m"] is True and "e" not in wire
            assert wire["i"] == node["identifier"]
    assert raw_seen == expected_ids and max(raw_lengths) < 480
    by_snapshot_identifier = {(r["snapshot_index"], r["identifier"]): r for r in rows}
    assert len(by_snapshot_identifier) == len(rows)
    for snapshot in snapshots:
        for node in snapshot["nodes"]:
            if node.get("identifier") not in expected_ids:
                continue
            row = by_snapshot_identifier[snapshot["index"], node["identifier"]]
            wire = json.loads(node["value"])
            assert row["raw_xcui_frame"] == row["xcui_frame"] == node["frame"]
            for compact, semantic in (("b", "bounds"), ("a", "accessibility_frame"),
                                      ("w", "window_converted_bounds")):
                assert dict(zip(("x", "y", "width", "height"), wire[compact])) == row["runtime"][semantic]
            assert row["runtime"]["os_version"] == wire["os"] == snapshot["runtime"]["os_version"]
            assert row["runtime"]["screen_scale"] == wire["s"] == snapshot["runtime"]["screen_scale"]
            assert row["runtime"]["bounds"] == row["reference_bounds"]
            assert all(v == 0 for key in ("runtime_bounds_minus_reference", "xcui_minus_public_uikit_ax",
                                          "observer_image_minus_runtime_projection") for v in row[key].values())
            assert row["runtime"]["bounds"]["width"] == row["raw_xcui_frame"]["width"]
            assert row["runtime"]["bounds"]["height"] == row["raw_xcui_frame"]["height"]
    assert all(s["complete"] and s["stable_binding"] and s["stable_height"]
               and s["top_reached"] and s["bottom_reached"] for s in observation["state_captures"])
    assert [s["action"] for s in observation["steps"]] == actions
    assert all(s["callback_delta"] == [] for s in observation["steps"])
    original_path = observed.parent / "ax-run-1/observation.json"
    original = load(original_path)
    original_values = [n.get("value") for s in original["snapshots"] for n in s["nodes"]
                       if n.get("identifier", "").startswith("axprobe.p")]
    original_failures = 0
    for value in original_values:
        try:
            json.loads(value)
        except (TypeError, ValueError):
            original_failures += 1
    assert len(original_values) == original_failures == 612
    assert all(isinstance(v, str) and len(v) == 512 for v in original_values)
    context = {k: snapshots[0]["runtime"][k] for k in ("os_version", "screen_scale")}
    provenance = {"probe_seal_sha256": sha(probe / "SEAL.json"),
                  "observation_sha256": sha(observed / "observation.json"),
                  "extraction_sha256": sha(observed / "calibration-rows.json")}
    profile = calibration.fit(extraction, context, provenance)
    assert profile["status"] == "validated" and profile["factor"] == 1
    assert profile["fit_rows"] == 87 and profile["heldout_rows"] == 62
    assert profile["heldout_failures"] == profile["rejected_rows"] == []
    assert all(v == 0 for r in profile["raw_residuals"] for v in r["residuals"].values())
    visible = [r for r in rows if r["fully_within_viewport"]]
    fit_visible = [r for r in visible if r["split"] == "fit"]
    held_visible = [r for r in visible if r["split"] == "heldout"]
    raw_context = {
        "schema": "ax-calibration.review.raw-context.v1",
        "source_snapshot": inspection,
        "inputs": {str(p.relative_to(REPO)): sha(p) for p in (
            observed / "manifest.json", observed / "observation.json", observed / "calibration-rows.json",
            probe / "SEAL.json", probe / "AXProbeBridge.swift", probe / "fixtures.json",
            probe / "actions.json", probe / "samples.json", probe / "SPECIFICATION.md")},
        "manifest": {k: manifest[k] for k in ("status", "build_exit_code", "test_exit_code", "native_test_count",
                                                "simulator", "source_hashes", "input_hashes", "actual_environment", "screenshot_pixels")},
        "extraction_rows": len(rows), "snapshots": len(snapshots),
        "independent_view_units": 18, "fit_view_units": 12, "heldout_view_units": 6,
        "fully_visible_rows": len(visible), "fit_fully_visible_rows": len(fit_visible),
        "heldout_fully_visible_rows": len(held_visible),
        "all_raw_frames_range": bounds([r["raw_xcui_frame"] for r in rows]),
        "fit_visible_frames_range": bounds([r["raw_xcui_frame"] for r in fit_visible]),
        "heldout_visible_frames_range": bounds([r["raw_xcui_frame"] for r in held_visible]),
        "all_fitted_size_residuals_zero": True,
        "raw_xcui_equals_public_uikit_ax": True,
        "observer_image_equals_independent_runtime_projection": True,
        "native_payload_bytes_range": [min(raw_lengths), max(raw_lengths)],
        "original_transport_failure": {"path": str(original_path.relative_to(REPO)),
                                       "sha256": sha(original_path), "observer_status": original.get("status"),
                                       "target_values": len(original_values), "all_character_lengths": 512,
                                       "json_parse_failures": original_failures},
        "one_stable_native_instance_per_id": all(v == 1 for v in extraction["summary"]["runtime_instance_count_by_id"].values()),
        "process_binding": snapshots[0]["binding"], "host_runtime_context": snapshots[0]["runtime"],
        "full_state_ids": [s["state_id"] for s in observation["state_captures"]],
        "fit_profile_context": context,
        "limits": "612 repeated rows are 18 native views in one process/context. The image check compares coordinate arithmetic, not independently detected screenshot edges. Zero residual does not validate a nonzero error envelope or universal native layout access.",
    }
    first = next(r for r in visible if r["identifier"] == "axprobe.p00")
    frame = copy.deepcopy(first["raw_xcui_frame"])
    def measurement(sample=frame, unit="pt"):
        number = geometry.number(sample["width"])
        return {"property": "width", "snapshot": first["snapshot_index"],
                "ratio": [number.numerator, number.denominator],
                "sources": [{"provider": "xcui_cgrect", "unit": unit, "sample": sample}]}
    def classify(value, runtime=context, current_profile=profile):
        return calibration.classify(value, float(value["ratio"][0] / value["ratio"][1]) + 1,
                                    "gte", None, current_profile, runtime)
    baseline = measurement()
    missing_scope = classify(baseline)
    explicit_outside = copy.deepcopy(baseline)
    explicit_outside["sources"][0].update({"native_view_class": "SyntheticSwiftUICustomAX",
                                           "local_transform_identity": False})
    explicit_outside_result = classify(explicit_outside)
    negative_frame = dict(frame, x=-frame["x"], y=-frame["y"])
    cross_axis_frame = dict(frame, x=500)
    below_minimum_frame = dict(frame, width=1)
    bad_context = classify(baseline, dict(context, os_version="review-synthetic-mismatch"))
    above_height = copy.deepcopy(baseline)
    above_height["property"] = "height"
    above_height["sources"][0]["sample"] = dict(frame, height=profile["domain"]["max_extent_by_axis"]["height"] + 1)
    above_height_result = classify(above_height)
    wrong_context_profile = calibration.fit(extraction,
        {"os_version": "review-synthetic-unrelated", "screen_scale": 999}, {"observation_sha256": "not-a-digest"})
    assert missing_scope["classification"] == explicit_outside_result["classification"] == "definite_within_profile"
    assert classify(measurement(negative_frame))["classification"] == "definite_within_profile"
    assert classify(measurement(cross_axis_frame))["classification"] == "definite_within_profile"
    assert classify(measurement(below_minimum_frame))["classification"] == "definite_within_profile"
    assert classify(measurement(unit="px"))["classification"] == "definite_within_profile"
    assert bad_context["classification"] == above_height_result["classification"] == "outside_calibrated_scope"
    assert wrong_context_profile["status"] == "validated"
    plan = {"design_contract": {"platform": "ios"}, "assertions": [
        {"id": "neutral-review-width", "kind": "geometry", "property": "width", "expected": 68, "op": "gte"}]}
    report = {"rows": [{"id": "neutral-review-width", "status": "failed",
                         "geometry_evidence": [baseline]}]}
    saved_plan, saved_report = copy.deepcopy(plan), copy.deepcopy(report)
    annotated = calibration.annotate(plan, observation, report, profile)
    assert report == saved_report and plan == saved_plan
    stripped = copy.deepcopy(annotated)
    for row in stripped["rows"]:
        row.pop("measurement_calibration", None)
    assert stripped == report
    assert geometry.compare(baseline, 68, "gte") is False
    results = {
        "schema": "ax-calibration.review.results.v1",
        "reviewed_source_sha256": inspection["source_files"]["native-ui-agent/scripts/ax_calibration.py"]["sha256"],
        "native_record_checks": "passed: exact source/input seals, complete payloads, same epoch, stable native identities, all three full checkpoints, zero bounds/AX/projection residuals",
        "reproduced_profile": {k: profile[k] for k in ("status", "factor", "fit_rows", "heldout_rows", "fit_ids", "heldout_ids", "heldout_failures", "rejected_rows", "domain")},
        "positive_error_envelope_tested_by_native_data": False,
        "findings_reproductions": {
            "missing_target_scope_evidence": missing_scope,
            "explicit_synthetic_nonidentity_custom_ax_metadata_ignored": explicit_outside_result,
            "negative_coordinates_absent_from_fitting_but_accepted": classify(measurement(negative_frame)),
            "x_500_exceeds_observed_x_max_but_accepted": classify(measurement(cross_axis_frame)),
            "width_1_below_observed_min_but_accepted": classify(measurement(below_minimum_frame)),
            "wrong_source_unit_px_accepted_by_classifier_directly": classify(measurement(unit="px")),
            "arbitrary_context_and_unverified_provenance_fit_status": wrong_context_profile["status"],
        },
        "working_guards": {"wrong_os_context": bad_context,
                           "height_above_axis_specific_max": above_height_result},
        "strict_invariants": {"original_report_unchanged": True, "original_plan_unchanged": True,
                              "annotation_only_adds_diagnostic_field": True, "raw_gte_verdict": "failed",
                              "raw_expected": 68, "raw_measured_ratio": baseline["ratio"]},
        "synthetic_case_scope": "Review-only function calls using neutral sample geometry; no changes to probe inputs, native records, P/F thresholds, implementation or production business cases.",
        "disposition": "Accept sealed probe/runtime agreement; do not claim a validated positive residual law or apply within-profile certainty to unproved target semantics. Missing verifiable identity-UIKit target scope must return outside_calibrated_scope.",
    }
    for name, value in (("RAW-CONTEXT.json", raw_context), ("RESULTS.json", results),
                        ("reproduced-profile.json", profile)):
        (HERE / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"native_rows": len(rows), "visible_fit_rows": len(fit_visible),
                      "visible_heldout_rows": len(held_visible), "factor": profile["factor"],
                      "positive_residual_observations": 0,
                      "scope_gap_reproduced": True, "strict_outcomes_preserved": True}))


if __name__ == "__main__":
    main()
