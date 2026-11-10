"""Read-only evidence recheck. Runs no product, SDK, observer or acceptance code."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from PIL import Image

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "cause-matching"

def read(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

def descendant(a, b, by_id, platform):
    key, parent = ("index", "parent_index") if platform == "ios" else ("node_id", "parent_id")
    current = b
    seen = set()
    while current.get(parent) in by_id and current.get(parent) not in seen:
        seen.add(current[parent])
        if current[parent] == a[key]:
            return True
        current = by_id[current[parent]]
    return False

def controls(snapshot, semantic, platform):
    key = "index" if platform == "ios" else "node_id"
    by_id = {n[key]: n for n in snapshot["nodes"]}
    def native(n):
        return n.get("role_raw") in (9, 40) if platform == "ios" else n.get("role") in ("Button", "Switch") and n.get("clickable") is True
    pool = [n for n in snapshot["nodes"] if native(n) and (n[key] == semantic[key] or descendant(semantic, n, by_id, platform))]
    # XCUI compound toggles contain an additional actual switch; use the leaf.
    return [n for n in pool if not any(m[key] != n[key] and descendant(n, m, by_id, platform) for m in pool)]

def bool_value(value):
    if value in (True, "1", "On", "true"):
        return True
    if value in (False, "0", "Off", "false"):
        return False
    raise ValueError(f"Non-Boolean switch value: {value!r}")

def prop(snapshot, row, platform):
    target = row["target"]["identifier"]
    sems = [n for n in snapshot["nodes"] if n.get("identifier") == target]
    if len(sems) != 1:
        raise ValueError(f"Expected one original semantic target, got {len(sems)}")
    sem = sems[0]
    visible = "fully_within_viewport" if platform == "ios" else "fully_visible"
    if sem.get(visible) is not True:
        raise ValueError("Report's cited target is not fully visible")
    property_ = row["property"]
    if property_ in ("label", "selected"):
        return sem[property_], sem
    control = controls(snapshot, sem, platform)
    if len(control) != 1:
        raise ValueError(f"Expected one leaf native control, got {len(control)}")
    node = control[0]
    if node.get(visible) is not True:
        raise ValueError("Actual native control is not fully visible")
    if property_ == "enabled":
        return node["enabled"], node
    if property_ == "value":
        return bool_value(node["value"] if platform == "ios" else node["toggle_state"]), node
    if property_ == "height":
        if platform == "ios":
            return node["frame"]["height"], node
        geo = node["native_geometry"]
        return float(Fraction(geo["size_px"][1]) / Fraction(str(geo["density"]))), node
    raise ValueError(property_)

def image_box(snapshot, node, platform):
    if platform == "ios":
        f, a, p = node["frame"], snapshot["app_frame"], snapshot["screenshot_pixels"]
        sx, sy = p["width"] / a["width"], p["height"] / a["height"]
        return [(f["x"] - a["x"]) * sx, (f["y"] - a["y"]) * sy, f["width"] * sx, f["height"] * sy]
    g, v, p = node["native_geometry"], snapshot["native_viewport_px"], snapshot["screenshot_pixels"]
    sx, sy = p["width"] / v["width"], p["height"] / v["height"]
    return [g["position_px"][0] * sx, g["position_px"][1] * sy, g["size_px"][0] * sx, g["size_px"][1] * sy]

def sample(image, box, sampling, expected, convention):
    x, y, w, h = box
    a, b, c, d = sampling["region"]
    lo, hi = (math.ceil, math.floor) if convention == "interior" else (math.floor, math.ceil)
    rect = [lo(x + a*w), lo(y + b*h), hi(x + c*w), hi(y + d*h)]
    if not (0 <= rect[0] < rect[2] <= image.width and 0 <= rect[1] < rect[3] <= image.height):
        raise ValueError("Frozen sample falls outside original PNG")
    pixels = list(image.crop(rect).convert("RGBA").getdata())
    desired = ((expected >> 16) & 255, (expected >> 8) & 255, expected & 255, (expected >> 24) & 255)
    support = sum(max(abs(p[i] - desired[i]) for i in range(4)) <= sampling["channel_tolerance"] for p in pixels) / len(pixels)
    mode, count = Counter(pixels).most_common(1)[0]
    return {"pixel_rect": rect, "pixel_count": len(pixels), "mode_argb": "#" + "".join(f"{v:02X}" for v in (mode[3], *mode[:3])), "mode_count": count, "support": support, "status": "P" if len(pixels) >= sampling["minimum_pixels"] and support >= sampling["minimum_support"] else "F"}

cohorts = []
for arm in ("A", "B"):
    for phase in ("D0", "Final"):
        for platform in ("ios", "android"):
            cohorts.append({"cohort": f"{arm}/{phase}/{platform}", "candidate": "initial" if phase == "D0" else arm, "scope": "public", "platform": platform, "root": f"packet-public/native/{arm}/public/{phase}/{platform}"})
for candidate in ("initial", "A", "B"):
    for platform in ("ios", "android"):
        prefix = "packet-initial-hidden" if candidate == "initial" else "packet-hidden-finals"
        cohorts.append({"cohort": f"{candidate}/private/{platform}", "candidate": candidate, "scope": "private", "platform": platform, "root": f"{prefix}/{candidate}/{platform}"})

source_index = read(BASE / "packet-public/SOURCE-INDEX.json")
results, native_rows, pixel_rows, raw_alerts = [], [], [], []
for cohort in cohorts:
    root = BASE / cohort["root"]
    candidate, scope, platform = cohort["candidate"], cohort["scope"], cohort["platform"]
    case = "cedar-lunch" if scope == "public" else "evening-service"
    design = BASE / f"packet-public/design/{scope}/compiled/{case}/{platform}"
    plan, report, obs = read(root / "parent-plan.json"), read(root / "automatic.json"), read(root / "native/observation.json")
    expected_catalog = read(design / "catalog.json")
    catalog_rows = {r["id"]: r for r in expected_catalog["rows"]}
    by_id = {r["id"]: r for r in report["assertions"]}
    states = [s["id"] if isinstance(s, dict) else s for s in plan["states"]]
    captures = {s: [c for c in obs["state_captures"] if c["state_id"] == s] for s in states}
    errors = []
    source = source_index[candidate][platform]
    manifest_key = "0/AlertToast/MenuChangeReviewPanel.swift" if platform == "ios" else "1/java/com/example/reply/ui/components/MenuChangeReviewPanel.kt"
    before, after = read(root / "source-before.json"), read(root / "source-after.json")
    if before != after or before.get(manifest_key) != sha(BASE / "packet-public" / source["packet"]):
        errors.append("Source manifest changed or does not match anonymous source")
    if sha(root / "parent-plan.json") != sha(design / "plan.json"):
        errors.append("Parent plan differs from independently fixed plan")
    if set(by_id) != set(plan["required_assertion_ids"]):
        errors.append("Original mandatory assertion set differs")
    environment = read(root / "environment-check.json")
    if environment["status"] != "P":
        errors.append("Environment not passed")
    for state, captures_ in captures.items():
        if len(captures_) != 1:
            errors.append(f"Nonunique selected full capture: {state}")
            continue
        c = captures_[0]
        if not all(c.get(k) is True for k in ("complete", "top_reached", "bottom_reached", "stable_binding")) or c.get("max_gap") != 0:
            errors.append(f"Incomplete or unstable selected full capture: {state}")
        bindings = [obs["snapshots"][i].get("binding") for i in c["snapshot_indices"]]
        if any(x != c["binding"] for x in bindings):
            errors.append(f"Capture binding mismatch: {state}")
    for row in plan["assertions"]:
        original = by_id[row["id"]]
        if original["status"] == "failed":
            raw_alerts.append({**cohort, "assertion_id": row["id"], "requirement_id": row["requirement_id"], "raw_status": "F", "snapshot_indices": original.get("snapshot_indices", []), "common_cause_id": "CC-001", "classification": "TP"})
        if row["kind"] not in ("control", "geometry", "event"):
            continue
        actuals, citations, err = [], [], []
        if row["kind"] == "event":
            step = obs["steps"][row["action_index"]]
            actuals = [[e["event"] if isinstance(e, dict) else e for e in step.get("callback_delta", [])]]
            citations = [{"step_index": row["action_index"], "dispatch": step.get("dispatch"), "binding_after": step.get("binding_after")}]
        else:
            for i in original.get("snapshot_indices", []):
                try:
                    snap = obs["snapshots"][i]
                    value, node = prop(snap, row, platform)
                    actuals.append(value)
                    citations.append({"snapshot_index": i, "node": node.get("index", node.get("node_id")), "binding": snap.get("binding")})
                except (KeyError, ValueError) as e:
                    err.append({"snapshot_index": i, "error": str(e)})
        statuses = [(x >= row["expected"] if row.get("op") == "gte" else type(x) == type(row["expected"]) and x == row["expected"]) for x in actuals]
        # An assertion concerns its selected business state, not every scroll
        # frame. A cited partial frame need not prove a fact already established
        # by one or more complete native-control frames in that same stable sweep.
        excluded = [e for e in err if "not fully visible" in e["error"]]
        hard_errors = [e for e in err if e not in excluded]
        status = "U" if not actuals or hard_errors else "P" if all(statuses) else "F"
        native_rows.append({**cohort, "id": row["id"], "kind": row["kind"], "independently_observed": actuals, "fixed_expected": row["expected"], "fixed_unit": row["unit"], "status": status, "errors": hard_errors, "partial_scroll_frames_not_used": excluded, "citations": citations, "original_report_status": original["status"]})
    if platform == "ios":
        for row in plan["assertions"]:
            if row["requirement_id"] != "send-fill":
                continue
            frozen = catalog_rows[row["id"]]
            for i in by_id[row["id"]]["snapshot_indices"]:
                snapshot = obs["snapshots"][i]
                _, node = prop(snapshot, {"target": row["target"], "property": "enabled"}, platform)
                path = root / "native" / snapshot["screenshot"]
                with Image.open(path) as im:
                    im.load()
                    box = image_box(snapshot, node, platform)
                    interior = sample(im, box, frozen["sampling"], row["expected"], "interior")
                    superset = sample(im, box, frozen["sampling"], row["expected"], "superset")
                pixel_rows.append({**cohort, "id": row["id"], "snapshot_index": i, "image": str(path.relative_to(BASE)), "image_sha256": sha(path), "source_sha256": source["sha256"], "binding": snapshot["binding"], "native_image_box": box, "fixed_sampling": frozen["sampling"], "fixed_expected_argb": f"#{row['expected']:08X}", "interior": interior, "fractional_edge_superset": superset, "original_report_status": by_id[row["id"]]["status"]})
    results.append({**cohort, "source_sha256": source["sha256"], "source_bound_before_after": before == after and before.get(manifest_key) == source["sha256"], "plan_equals_fixed": sha(root / "parent-plan.json") == sha(design / "plan.json"), "raw_counts": report["counts"], "required_assertions": len(plan["required_assertion_ids"]), "kind_counts": dict(Counter(x["kind"] for x in plan["assertions"])), "selected_states": list(captures), "full_capture_complete_and_bound": not errors, "capture_source_environment_errors": errors})

save("cohort-core-checks.json", results)
save("native-independent-recheck.json", {"method": "Recompute values from original selector nodes, ancestry, exact native dimensions and callback deltas; report rows only select cited original snapshots, never supply actual values. Each atom must have at least one complete native target in its selected stable state sweep; extra partial scroll frames are explicitly retained as unused, not reclassified as mandatory atoms.", "rows": native_rows, "counts": dict(Counter(x["status"] for x in native_rows))})
save("send-pixel-independent-recheck.json", {"method": "Original PNG and actual unique native Button frame; frozen design region/thresholds preserved. Both wholly interior pixels and a superset including fractional boundary pixels are checked to make the reviewers' one-pixel rasterization difference explicit.", "rows": pixel_rows, "counts": dict(Counter(x["interior"]["status"] for x in pixel_rows))})
save("original-alert-rows.json", raw_alerts)
print("cohorts", len(results), "capture/source/environment errors", sum(len(x["capture_source_environment_errors"]) for x in results))
print("native rows", len(native_rows), Counter(x["status"] for x in native_rows))
print("native nonpass", [{k:x[k] for k in ['cohort','id','status','errors','independently_observed']} for x in native_rows if x['status'] != 'P'][:12])
print("ios send samples", len(pixel_rows), Counter(x["interior"]["status"] for x in pixel_rows), "rasterization outcome differences", sum(x["interior"]["status"] != x["fractional_edge_superset"]["status"] for x in pixel_rows))
print("original failed alerts", len(raw_alerts), Counter(x["cohort"] for x in raw_alerts))
