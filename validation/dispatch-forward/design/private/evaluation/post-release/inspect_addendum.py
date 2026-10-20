#!/usr/bin/env python3
"""Post-release interpretation diagnostics only; never edits or grades trial inputs."""
import collections
import datetime
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, __version__ as pillow_version

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
TRIAL = REPO / "validation/dispatch-forward"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": str(path.relative_to(REPO)), "sha256": sha(path)}


def read(path):
    return json.loads(path.read_text())


def collect_dispatch(aid):
    grade_path = TRIAL / "design/private/evaluation/final" / aid / "grade.json"
    grade = read(grade_path)
    groups = collections.defaultdict(list)
    reasons = collections.Counter()
    for row in grade["rows"]:
        if row["denominator"] != "runtime_business" or row["outcome"] != "U":
            continue
        reasons[row["reason"]] += 1
        if row["reason"].startswith(("native dispatch before-binding", "no demonstrated")):
            groups[("/".join(row["key"].split("/")[:3]), row["reason"])].append(row["key"])
    records = []
    for (checkpoint, reason), keys in groups.items():
        platform, case, cp = checkpoint.split("/")
        base = TRIAL / "private/grade-capsules/final" / aid / "native" / platform / case
        ob_path, mapping_path = base / "observation.json", base / "mapping.json"
        ob, mapping = read(ob_path), read(mapping_path)
        index = mapping[cp]["trigger_action_index"]
        step = ob["steps"][index]
        before_index = step.get("before")
        before_snapshot_binding = ob["snapshots"][before_index].get("binding") if isinstance(before_index, int) else None
        records.append({
            "checkpoint": checkpoint, "row_count": len(keys), "exact_keys": keys, "sealed_reason": reason,
            "observation": ref(ob_path), "mapping": ref(mapping_path), "trigger_action_index": index,
            "raw_outcome": step.get("outcome"), "raw_dispatch": step.get("dispatch"),
            "raw_activation_enabled": step.get("activation_target", {}).get("enabled"),
            "raw_before_snapshot_index": before_index, "raw_before_snapshot_binding": before_snapshot_binding,
            "raw_binding_after": step.get("binding_after"),
        })
    return {"grade": ref(grade_path), "sealed_business_U_reasons": dict(reasons), "checkpoint_records": records}


def collect_c04():
    ob_path = TRIAL / "private/grade-capsules/final/sample-716d41/native/ios/C04/observation.json"
    ob = read(ob_path)
    records = []
    hash_groups = collections.defaultdict(list)
    selectors = ["waterRound.title", "waterRound.beds", "waterRound.required", "waterRound.spendable", "waterRound.reserveNeeded", "waterRound.remaining", "waterRound.status"]
    for index, snap in enumerate(ob["snapshots"]):
        path = ob_path.parent / snap["screenshot"]
        with Image.open(path) as original:
            rgb = original.convert("RGB")
            original_info = {"mode": original.mode, "frames": getattr(original, "n_frames", 1), "size": list(original.size)}
            image_sha = sha(path)
            hash_groups[image_sha].append(index)
            app = snap["app_frame"]
            sx, sy = rgb.width / app["width"], rgb.height / app["height"]
            regions = []
            for selector in selectors:
                node = next(n for n in snap["nodes"] if n.get("identifier") == selector)
                frame = node["frame"]
                box = [max(0, math.floor((frame["x"] - app["x"]) * sx)), max(0, math.floor((frame["y"] - app["y"]) * sy)), min(rgb.width, math.ceil((frame["x"] + frame["width"] - app["x"]) * sx)), min(rgb.height, math.ceil((frame["y"] + frame["height"] - app["y"]) * sy))]
                counts = collections.Counter(rgb.crop(box).getdata())
                regions.append({"selector": selector, "pixel_box": box, "raw_label": node.get("label"), "nonblack_pixels": sum(v for color, v in counts.items() if color != (0, 0, 0)), "bright_pixels_min_channel_gt_150": sum(v for color, v in counts.items() if min(color) > 150), "most_common_rgb": [[list(color), count] for color, count in counts.most_common(3)]})
            records.append({"snapshot_index": index, "name": snap["name"], "state_id": snap.get("state_id"), "image": ref(path), "decoded": original_info, "binding": snap.get("binding"), "binding_after_capture": snap.get("binding_after_capture"), "capture_consistent": snap.get("capture_consistent"), "regions": regions})
    d0 = TRIAL / "private/grade-capsules/d0/sample-716d41/native/ios/C04/attachments/CE4945B2-20B8-42D7-BB19-4C5AC5A7D9AB.png"
    return {"observation": ref(ob_path), "comparison_d0_original": ref(d0), "identical_file_hash_snapshot_groups": dict(hash_groups), "scope": "Original PNG bytes and decoded region presence only; no new grade, OCR, font, hitbox, or product rendering-cause verdict.", "snapshots": records}


def verify_prior_seals():
    records = []
    for phase in ["d0", "final", "selfreview", "paired-d0"]:
        for aid in ["sample-716d41", "sample-e318ec"]:
            path = TRIAL / "design/private/evaluation" / phase / aid / "SEAL.json"
            seal = read(path)
            payload = json.dumps(seal["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            assert hashlib.sha256(payload).hexdigest() == seal["commitment_sha256"]
            for item in seal["payload"]["files"]:
                assert sha(path.parent / item["path"]) == item["sha256"]
            for item in seal["payload"]["inputs"]:
                assert sha(REPO / item["path"]) == item["sha256"]
            records.append({"phase": phase, "anonymous_id": aid, "seal": ref(path), "commitment_sha256": seal["commitment_sha256"], "all_files_and_inputs_unchanged": True})
    return records


if __name__ == "__main__":
    result = {
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stage": "post-release-interpretation-only", "grade_or_seal_changes": False,
        "diagnostic_script": ref(Path(__file__).resolve()), "pillow_version": pillow_version,
        "final_dispatch_reasons": {aid: collect_dispatch(aid) for aid in ["sample-716d41", "sample-e318ec"]},
        "c04_original_image_diagnostics": collect_c04(), "unchanged_stage_seals": verify_prior_seals(),
    }
    output = HERE / "interpretation-addendum-evidence.json"
    if output.exists():
        raise SystemExit("Fresh output required")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"path": str(output), "sha256": sha(output), "prior_seals_unchanged": len(result["unchanged_stage_seals"])}))
