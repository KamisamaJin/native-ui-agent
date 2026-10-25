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


def decode_runtime(raw, identifier, sample_split):
    """Expand wire abbreviations without altering any observed number."""
    wire = json.loads(raw)
    assert wire["v"] == 2 and wire["m"] is True and "e" not in wire
    assert wire["i"] == identifier
    def rect(key):
        values = wire[key]
        assert isinstance(values, list) and len(values) == 4
        result = dict(zip(AXES, values))
        assert finite_rect(result)
        return result
    transform = wire["t"]
    assert isinstance(transform, list) and len(transform) == 6
    assert all(type(x) in (int, float) and math.isfinite(x) for x in transform)
    assert type(wire["p"]) is bool
    assert type(wire["s"]) in (int, float) and math.isfinite(wire["s"]) and wire["s"] > 0
    assert isinstance(wire["u"], str) and len(wire["u"]) == 32
    assert isinstance(wire["o"], str) and wire["o"] and all(c in "0123456789abcdef" for c in wire["o"])
    assert isinstance(wire["os"], str) and wire["os"]
    assert type(wire["r"]) is int and wire["r"] > 0
    return {
        "schema": "ax-probe.runtime.v2", "status": "measured",
        "reference_identity": wire["i"],
        "sample_split": sample_split, "sample_split_source": "sealed_samples",
        "native_instance_identity": wire["u"],
        "native_object_identity": "0x" + wire["o"],
        "bounds": rect("b"), "accessibility_frame": rect("a"),
        "window_converted_bounds": rect("w"),
        "local_transform": dict(zip(("a", "b", "c", "d", "tx", "ty"), transform)),
        "local_transform_identity": transform == [1, 0, 0, 1, 0, 0],
        "ancestor_transforms_identity": wire["p"],
        "screen_scale": wire["s"], "os_version": wire["os"],
        "geometry_revision": wire["r"],
    }


def preflight_transport():
    """Synthetic wire budget; no native data or numeric rounding is involved."""
    cases = []
    # Long 64-bit object identity, full UUID bits, long OS version and revision.
    base = {"v": 2, "m": True, "i": "axprobe.p17", "u": "f" * 32,
            "o": "f" * 16, "p": True, "s": 3.0, "os": "999.999.999.999",
            "r": 9223372036854775807, "t": [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]}
    # These synthetic coordinates exceed the fixture's finite canvas range and
    # include long double representations, mixed signs, and positive dimensions.
    long_rect = [-99999.66666666667, -88888.33333333333,
                 77777.66666666667, 66666.33333333333]
    for name, bounds in (("long_fractional_metrics", long_rect),
                         ("mixed_sign_coordinates", [99999.33333333333, -77777.66666666667,
                                                     0.3333333333333333, 0.6666666666666666])):
        wire = dict(base, b=bounds, a=long_rect, w=long_rect)
        text = json.dumps(wire, separators=(",", ":"), sort_keys=True, allow_nan=False)
        # Python emits .0 for integral doubles; Foundation often omits it, so
        # this is a conservative representative payload rather than a Swift run.
        assert len(text.encode("ascii")) < 480
        normalized = decode_runtime(text, "axprobe.p17", "heldout")
        assert list(normalized["bounds"].values()) == bounds
        assert list(normalized["accessibility_frame"].values()) == long_rect
        cases.append({"case": name, "utf8_bytes": len(text.encode("ascii")),
                      "below_native_guard": True, "normalized_without_rounding": True})
    return {"schema": "ax-probe.transport-preflight.v2", "native_sdk_execution": False,
            "observed_xcui_truncation_characters": 512, "native_fail_closed_guard_bytes": 480,
            "cases": cases, "maximum_representative_bytes": max(c["utf8_bytes"] for c in cases)}


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
    identities, wire_lengths = {}, []
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
            raw_value = node.get("value")
            wire_bytes = len(raw_value.encode("utf8")) if isinstance(raw_value, str) else None
            if wire_bytes is not None:
                wire_lengths.append(wire_bytes)
            try:
                runtime = decode_runtime(raw_value, identifier, expected[identifier]["split"])
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
                "wire_bytes": wire_bytes,
                "runtime_bounds_minus_reference": bound_delta,
                "raw_xcui_frame": node.get("frame"),
                "xcui_frame": node.get("frame"),
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
        "schema": "ax-probe.extraction.v2",
        "scope": split["scope"], "sample_split": {k: split[k] for k in ("fit", "heldout")},
        "summary": {
            "runtime_rows": len(rows), "eligible_rows": sum(r["eligible_identity_transform_sample"] for r in rows),
            "distinct_measured_ids": sorted(identities),
            "unmeasured_ids": sorted(set(expected) - set(identities)),
            "runtime_instance_count_by_id": {k: len(v) for k, v in sorted(identities.items())},
            "runtime_ax_y_range": [min(numeric_y), max(numeric_y)] if numeric_y else None,
            "wire_bytes_range": [min(wire_lengths), max(wire_lengths)] if wire_lengths else None,
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
    parser.add_argument("--preflight-transport", action="store_true")
    parser.add_argument("--observation", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    _, split, expected = specification()
    if args.validate_spec:
        print(json.dumps({"specification": "valid", "views": len(expected),
                          "fit": len(split["fit"]), "heldout": len(split["heldout"])}))
    if args.preflight_transport:
        print(json.dumps(preflight_transport()))
    if args.observation:
        if args.output is None or args.output.exists():
            parser.error("--observation requires a fresh --output file")
        raw = args.observation.read_bytes()
        result = extract(json.loads(raw), split, expected)
        result["observation_sha256"] = hashlib.sha256(raw).hexdigest()
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"output": str(args.output), "runtime_rows": result["summary"]["runtime_rows"],
                          "diagnostics": len(result["diagnostics"])}))
    elif not args.validate_spec and not args.preflight_transport:
        parser.error("Choose --validate-spec, --preflight-transport or --observation")


if __name__ == "__main__":
    main()
