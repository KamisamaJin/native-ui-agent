#!/usr/bin/env python3
"""Audit preserved pilot evidence and create a result index; does not judge images."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    results = {"experiment": "Controlled regression and repair on real upstream components",
               "date": "2026-10-18", "platforms": {},
               "limitations": ["Not blind; agent knew the planned faults", "No without-Skill control group",
                               "No generic SwiftUI/Compose style property tree was implemented",
                               "Single runtime/device configuration per platform"]}
    for platform in ("android", "ios"):
        references = read("references/" + platform + "/manifest.json")
        reference_hashes = ({item["scenario"]: item["image_sha256"] for item in references}
                            if isinstance(references, list) else
                            {name: item["sha256"] for name, item in references["references"].items()})
        project = ROOT / ("checkouts/compose-samples/Reply" if platform == "android" else "checkouts/alerttoast")
        bad = read("evidence/" + platform + "-regression-normal-review/report.json")
        assert bad["status"] == "failed", platform
        assert bad["capture_sha256"] == sha(Path(bad["capture"]))
        assert next(c for c in bad["checks"] if c["kind"] == "pixel")["status"] == "failed"
        bad_capture = json.loads(Path(bad["capture"]).read_text())
        assert bad_capture["status"] == "captured"
        for artifact in bad_capture["artifacts"]:
            assert sha(Path(bad["capture"]).parent / artifact["path"]) == artifact["sha256"]
        result = {"regression_report": "evidence/" + platform + "-regression-normal-review/report.json",
                  "regression_changed_fraction": next(c for c in bad["checks"] if c["kind"] == "pixel")["changed_fraction"],
                  "repair_rounds": 1, "scenarios": {}}
        for scenario in ("normal", "long", "dark"):
            folder = "evidence/" + platform + "-repaired-" + scenario + "-1"
            capture = read(folder + "/capture.json")
            report_path = "evidence/" + platform + "-repaired-" + scenario + "-review/report.json"
            report = read(report_path)
            assert capture["status"] == "captured" and report["status"] == "passed"
            assert report["capture_sha256"] == sha(ROOT / folder / "capture.json")
            assert all(check["status"] == "passed" for check in report["checks"])
            pixel = next(check for check in report["checks"] if check["kind"] == "pixel")
            assert pixel["changed_pixels"] == 0
            reference_hash = reference_hashes[scenario]
            assert sha(ROOT / "references" / platform / (scenario + ".png")) == reference_hash
            assert sha(project / "native-ui-baselines" / (scenario + ".png")) == reference_hash
            for artifact in capture["artifacts"]:
                assert sha(ROOT / folder / artifact["path"]) == artifact["sha256"]
            if platform == "android":
                native = ET.parse(ROOT / folder / "native/junit.xml").getroot().attrib
                assert int(native["tests"]) == 1 and int(native.get("failures", 0)) == 0
                assert int(native.get("errors", 0)) == 0
            else:
                native = read(folder + "/native/xcresult-summary.json")
                assert native["totalTestCount"] == 1 and native["passedTests"] == 1
                assert native["failedTests"] == 0
            result["scenarios"][scenario] = {"status": "passed", "native_tests_passed": 1,
                "changed_pixels": 0, "capture_seconds": capture["commands"][0]["duration_seconds"],
                "actual": folder + "/artifacts/000-actual.png", "report": report_path,
                "reference_sha256": reference_hash}
        results["platforms"][platform] = result
    page = read("evidence/android-page-repaired/report.json")
    assert page["status"] == "passed"
    results["android_page_smoke"] = {"status": page["status"], "scope": page["scope"],
                                      "report": "evidence/android-page-repaired/report.json"}
    results["ios_page_integration"] = "Component library hosted in real simulator XCTest; no full business app/navigation tested"
    results["status"] = "passed_with_stated_scope"
    (ROOT / "result-summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": results["status"], "repaired_scenarios": 6,
                      "report": str(ROOT / "result-summary.json")}))


if __name__ == "__main__":
    main()
