#!/usr/bin/env python3
"""Portable audit of archived evidence; does not execute native SDKs or an AI model."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def audit_capture(name, report_name):
    folder = ROOT / "evidence" / name
    capture = load(folder / "capture.json")
    report = load(ROOT / "evidence" / report_name / "report.json")
    assert capture["status"] == "captured"
    assert report["capture_sha256"] == sha(folder / "capture.json")
    assert report["status"] == "passed"
    assert all(check["status"] == "passed" for check in report["checks"])
    for artifact in capture["artifacts"]:
        assert sha(folder / artifact["path"]) == artifact["sha256"]
    if name.startswith("android"):
        native = ET.parse(folder / "native/junit.xml").getroot().attrib
        assert int(native["tests"]) == 1 and int(native.get("failures", 0)) == 0
        assert int(native.get("errors", 0)) == 0
    else:
        native = load(folder / "native/xcresult-summary.json")
        assert native["totalTestCount"] == 1 and native["passedTests"] == 1
        assert native["failedTests"] == 0
    return {"status": "passed", "capture": "evidence/" + name + "/capture.json",
            "report": "evidence/" + report_name + "/report.json",
            "actual": "evidence/" + name + "/artifacts/000-actual.png",
            "capture_seconds": capture["commands"][0]["duration_seconds"], "native_tests": 1}


def track_sample(name):
    """Sample the normal light track at 90% using frozen geometry and actual blue-bar y."""
    with Image.open(ROOT / "evidence" / name / "artifacts/000-actual.png") as image:
        rgb = image.convert("RGB")
        blue_rows = []
        for y in range(rgb.height):
            xs = [x for x in range(rgb.width) if rgb.getpixel((x,y))[2] > 200
                  and rgb.getpixel((x,y))[0] < 100 and rgb.getpixel((x,y))[1] < 200]
            if len(xs) > 15 and max(xs)-min(xs)+1 == len(xs):
                blue_rows.append(y)
        assert blue_rows
        y = blue_rows[-1] - 2
        scale = rgb.width / 390
        x = round((36 + 318 * 0.9) * scale)
        return {"pixel": [x,y], "rgb": list(rgb.getpixel((x,y)))}


def main():
    freeze = load(ROOT / "design/freeze.json")
    for name, expected in freeze["files"].items():
        assert sha(ROOT / "design" / name) == expected, name + " changed after freeze"
    results = {"status": "passed_with_stated_scope", "design_commit": "26f101c36c1b98f40a230b9e9c92f3cd952fbb2a",
        "design_unchanged": True, "android": {}, "ios": {}, "correction_rounds": {"android":0,"ios":1}}
    for scenario in ("normal","long","dark","narrow","empty"):
        results["android"][scenario] = audit_capture("android-initial-"+scenario+"-1", "android-initial-"+scenario+"-review")
    for scenario in ("normal","long","dark","narrow","complete","legacy"):
        results["ios"][scenario] = audit_capture("ios-final-"+scenario+"-1", "ios-final-"+scenario+"-review")
    for scenario in ("normal","long","narrow"):
        report = load(ROOT / "evidence" / ("ios-initial-"+scenario+"-design-review/report.json"))
        capture = ROOT / "evidence" / ("ios-initial-"+scenario+"-1/capture.json")
        assert report["status"] == "failed" and report["capture_sha256"] == sha(capture)
        captured = load(capture)
        for artifact in captured["artifacts"]:
            assert sha(capture.parent / artifact["path"]) == artifact["sha256"]
    # The design itself was frozen before implementation; this audit adds a deterministic
    # check of the discovered color mismatch, without changing that design or runner gates.
    svg = ET.parse(ROOT / "design/ios-reference.svg").getroot()
    track = next(node for node in svg if node.tag.endswith("rect") and node.get("width")=="318")
    color = track.attrib["fill"].lstrip("#")
    expected_rgb = [int(color[i:i+2],16) for i in (0,2,4)]
    before = track_sample("ios-initial-normal-1")
    after = track_sample("ios-final-normal-1")
    assert before["rgb"] != expected_rgb and after["rgb"] == expected_rgb
    results["track_audit"] = {"source":"frozen SVG track fill", "expected_rgb":expected_rgb,
                               "initial":before,"final":after,"kind":"rendered pixel sample, not UIColor introspection"}
    legacy = load(ROOT / "evidence/ios-final-legacy-review/report.json")
    assert next(c for c in legacy["checks"] if c["kind"]=="pixel")["changed_pixels"] == 0
    page = load(ROOT / "evidence/android-page-final/report.json")
    assert page["status"] == "passed"
    results["android_page"] = "passed: attachment row visible, email detail, Back"
    results["ios_page_scope"] = "Real simulator XCTest component host; no full business App navigation"
    results["clean_replay"] = {}
    for platform in ("android","ios"):
        results["clean_replay"][platform] = audit_capture(platform+"-clean-replay-normal-1", platform+"-clean-replay-normal-review")
    results["limitations"] = ["Self-authored requirements/design; no independent designer approval",
        "No blind evaluation or without-Skill control group; cannot estimate causal PR-quality gain",
        "Initial quick iOS visual review missed track shade; detailed design review found it",
        "Only Compose 1.9.4 and SwiftUI tested; plain-text metrics do not form a generic style tree",
        "No injected production regressions in this feature-development experiment"]
    (ROOT / "result-summary.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":results["status"],"new_feature_scenarios":11,"clean_replays":2,
                      "design_unchanged":True}))


if __name__ == "__main__":
    main()
