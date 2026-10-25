#!/usr/bin/env python3
"""Extract pre-split numerical evidence without importing candidate geometry code."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AXES = ("x", "y", "width", "height")


def finite_rect(value):
    return (isinstance(value, dict) and all(
        type(value.get(k)) in (int, float) and math.isfinite(value[k])
        for k in AXES))


def delta(actual, expected):
    if not finite_rect(actual) or not finite_rect(expected):
        return None
    return {k: actual[k] - expected[k] for k in AXES}


def project(rect, app, pixels):
    """Independent arithmetic on runtime UIKit screen geometry and image metadata."""
    if not finite_rect(rect) or not finite_rect(app):
        return None
    if app["width"] <= 0 or app["height"] <= 0 or not isinstance(pixels, dict):
        return None
    pw, ph = pixels.get("width"), pixels.get("height")
    if not all(type(x) in (int, float) and math.isfinite(x) and x > 0 for x in (pw, ph)):
        return None
    x_density, y_density = pw / app["width"], ph / app["height"]
    return {"x": (rect["x"] - app["x"]) * x_density,
            "y": (rect["y"] - app["y"]) * y_density,
            "width": rect["width"] * x_density,
            "height": rect["height"] * y_density}


def specification():
    fixtures = json.loads((ROOT / "fixtures.json").read_text())
    split = json.loads((ROOT / "samples.json").read_text())
    probes = fixtures["initial"]["probes"]
    ids = [p["id"] for p in probes]
    assert len(ids) == len(set(ids)) == 18
    assert len(split["fit"]) == 12 and len(split["heldout"]) == 6
    assert set(split["fit"]).isdisjoint(split["heldout"])
    assert set(ids) == set(split["fit"] + split["heldout"])
    canvas = fixtures["initial"]["canvas"]
    for p in probes:
        assert finite_rect(p["bounds"])
        assert p["bounds"]["width"] > 0 and p["bounds"]["height"] > 0
        assert p["bounds"] == split["oracle_reference_bounds"][p["id"]]
        assert p["id"] in split[p["split"]]
        assert 0 <= p["placement"]["x"] < canvas["width"] - p["bounds"]["width"]
        assert 0 <= p["placement"]["y"] < canvas["height"] - p["bounds"]["height"]
    fit = [p for p in probes if p["split"] == "fit"]
    held = [p for p in probes if p["split"] == "heldout"]
    for key in ("width", "height"):
        assert {p["bounds"][key] for p in fit}.isdisjoint(
            p["bounds"][key] for p in held)
    for key in ("x", "y"):
        assert {p["placement"][key] for p in fit}.isdisjoint(
            p["placement"][key] for p in held)
    assert set(fixtures["required_identifiers"]) == set(ids)
    return fixtures, split, {p["id"]: p for p in probes}


def extract(observation, split, expected):
    rows, diagnostics = [], []
    identities = {}
    for snap in observation.get("snapshots", []):
        seen = set()
        for node in snap.get("nodes", []):
            identifier = node.get("identifier")
            if identifier not in expected:
                continue
            if identifier in seen:
                diagnostics.append({"snapshot_index": snap.get("index"),
                                    "identifier": identifier, "issue": "duplicate_ax_identifier"})
            seen.add(identifier)
            try:
                runtime = json.loads(node["value"])
                assert runtime["schema"] == "ax-probe.runtime.v1"
                assert runtime["reference_identity"] == identifier
                assert runtime["status"] == "measured"
                assert finite_rect(runtime["bounds"]) and finite_rect(runtime["accessibility_frame"])
            except (KeyError, TypeError, ValueError, AssertionError):
                diagnostics.append({"snapshot_index": snap.get("index"),
                                    "identifier": identifier, "issue": "runtime_truth_unavailable",
                                    "raw_value": node.get("value")})
                continue
            native_ax = runtime["accessibility_frame"]
            runtime_bounds = runtime["bounds"]
            ref = split["oracle_reference_bounds"][identifier]
            bound_delta = delta(runtime_bounds, ref)
            projected = project(native_ax, snap.get("app_frame"), snap.get("screenshot_pixels"))
            eligible = (snap.get("capture_consistent") is True
                        and runtime.get("local_transform_identity") is True
                        and runtime.get("ancestor_transforms_identity") is True
                        and all(abs(v) <= 1e-6 for v in bound_delta.values()))
            row = {
                "snapshot_index": snap.get("index"), "snapshot_name": snap.get("name"),
                "state_id": snap.get("state_id"), "binding": snap.get("binding"),
                "capture_consistent": snap.get("capture_consistent"),
                "identifier": identifier, "split": expected[identifier]["split"],
                "eligible_identity_transform_sample": eligible,
                "intersects_viewport": node.get("intersects_viewport"),
                "fully_within_viewport": node.get("fully_within_viewport"),
                "reference_bounds": ref, "runtime": runtime,
                "runtime_bounds_minus_reference": bound_delta,
                "raw_xcui_frame": node.get("frame"),
                "xcui_minus_public_uikit_ax": delta(node.get("frame"), native_ax),
                "public_uikit_ax_minus_bounds_size": {
                    k: native_ax[k] - runtime_bounds[k] for k in ("width", "height")},
                "window_bounds_minus_local_bounds_size": {
                    k: runtime["window_converted_bounds"][k] - runtime_bounds[k]
                    for k in ("width", "height")},
                "app_frame": snap.get("app_frame"),
                "screenshot_pixels": snap.get("screenshot_pixels"),
                "independent_projection_from_public_uikit_ax": projected,
                "observer_image_frame": node.get("image_frame"),
                "observer_image_minus_runtime_projection": delta(node.get("image_frame"), projected),
            }
            rows.append(row)
            identities.setdefault(identifier, set()).add(runtime["native_instance_identity"])
    numeric_y = [r["runtime"]["accessibility_frame"]["y"] for r in rows]
    return {
        "schema": "ax-probe.extraction.v1",
        "scope": split["scope"], "sample_split": {k: split[k] for k in ("fit", "heldout")},
        "summary": {
            "runtime_rows": len(rows), "eligible_rows": sum(r["eligible_identity_transform_sample"] for r in rows),
            "distinct_measured_ids": sorted(identities),
            "unmeasured_ids": sorted(set(expected) - set(identities)),
            "runtime_instance_count_by_id": {k: len(v) for k, v in sorted(identities.items())},
            "runtime_ax_y_range": [min(numeric_y), max(numeric_y)] if numeric_y else None,
            "has_negative_runtime_ax_y": any(y < 0 for y in numeric_y),
            "has_runtime_ax_y_above_1500": any(y > 1500 for y in numeric_y),
            "observation_coverage": observation.get("coverage"),
            "native_state_captures": observation.get("state_captures"),
        },
        "diagnostics": diagnostics, "rows": rows,
        "interpretation": "Raw numerical evidence only. Fit by distinct fit identifiers; evaluate heldout identifiers without retuning. Repeated scroll observations are correlated. In-process UIKit AX geometry is independent of XCUI transport, but is not an independent screenshot-edge oracle or universal layout accessor.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-spec", action="store_true")
    parser.add_argument("--observation", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    _, split, expected = specification()
    if args.validate_spec:
        print(json.dumps({"specification": "valid", "views": len(expected),
                          "fit": len(split["fit"]), "heldout": len(split["heldout"])}))
    if args.observation:
        if args.output is None or args.output.exists():
            parser.error("--observation requires a fresh --output file")
        raw = args.observation.read_bytes()
        result = extract(json.loads(raw), split, expected)
        result["observation_sha256"] = hashlib.sha256(raw).hexdigest()
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"output": str(args.output), "runtime_rows": result["summary"]["runtime_rows"],
                          "diagnostics": len(result["diagnostics"])}))
    elif not args.validate_spec:
        parser.error("Choose --validate-spec or --observation")


if __name__ == "__main__":
    main()
