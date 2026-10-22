"""Evidence/decision tests with a synthetic renderer; no native SDK is exercised."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ui_loop.py"
SPEC = importlib.util.spec_from_file_location("ui_loop", SCRIPT)
LOOP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LOOP)


class UILoopTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / "Component.swift").write_text("original production input\n")
        (self.project / "goldens").mkdir()
        Image.new("RGBA", (8, 8), "white").save(self.project / "goldens" / "reference.png")
        self.renderer = self.project / "render.py"
        self.renderer.write_text(
            "import os,json\n"
            "from pathlib import Path\n"
            "from PIL import Image\n"
            "out=Path(os.environ['NATIVE_UI_OUTPUT'])\n"
            "Image.new('RGBA',(8,8),'white').save(out/'actual.png')\n"
            "(out/'measurements.json').write_text(json.dumps("
            "{'gap':{'value':8,'unit':'pt','method':'synthetic test fixture'}}))\n"
        )
        self.profile = {
            "version": 1, "platform": "ios", "backend": "snapshot-testing",
            "target": {"description": "Synthetic test case", "sources": ["Component.swift"]},
            "environment": {"device": "synthetic 8x8", "theme": "light"},
            "commands": [{"argv": [sys.executable, "render.py"]}],
            "artifacts": [
                {"base": "output", "glob": "native/actual.png", "role": "actual"},
                {"base": "output", "glob": "native/measurements.json", "role": "measurement"},
            ],
            "protected_paths": ["goldens"],
            "checks": [{"id": "gap", "kind": "numeric", "description": "Gap equals eight",
                        "source": "Test specification", "measurement": "gap",
                        "expected": 8, "unit": "pt"}],
        }
        self.profile_path = self.root / "profile.json"
        self.capture_count = 0
        self.review_count = 0

    def command(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True, timeout=15)

    def capture(self, expected=0):
        self.capture_count += 1
        output = self.root / f"capture-{self.capture_count}"
        self.profile_path.write_text(json.dumps(self.profile))
        result = self.command("capture", "--project", self.project, "--profile",
                              self.profile_path, "--output", output)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        report_path = output / "capture.json"
        return report_path, json.loads(report_path.read_text()) if report_path.exists() else None

    def review(self, capture, findings=None, expected=0):
        self.review_count += 1
        output = self.root / f"review-{self.review_count}"
        args = ["review", "--capture", capture, "--output", output]
        if findings is not None:
            findings.setdefault("capture_sha256", LOOP.sha(capture))
            path = self.root / f"findings-{self.review_count}.json"
            path.write_text(json.dumps(findings))
            args.extend(["--findings", path])
        result = self.command(*args)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        path = output / "report.json"
        return json.loads(path.read_text()) if path.exists() else None

    def pixel(self):
        return {"id": "image", "kind": "pixel", "description": "Approved image",
                "source": "Reviewed reference", "reference": "goldens/reference.png"}

    def test_capture_is_not_a_style_pass(self):
        path, captured = self.capture()
        self.assertEqual(captured["status"], "captured")
        self.assertEqual(len(captured["artifacts"]), 2)
        self.assertEqual(self.review(path)["status"], "passed")

    def test_android_backends_use_the_same_evidence_protocol(self):
        for backend in ("paparazzi", "compose-preview", "simulator"):
            with self.subTest(backend=backend):
                self.profile.update(platform="android", backend=backend)
                path, _ = self.capture()
                self.assertEqual(self.review(path)["status"], "passed")

    def test_zero_tests_zero_artifacts_cannot_pass(self):
        self.profile["commands"] = [{"argv": [sys.executable, "-c", "pass"]}]
        _, captured = self.capture(expected=1)
        self.assertEqual(captured["status"], "error")

    def test_non_image_artifact_cannot_pass_capture(self):
        self.renderer.write_text(
            "import os\nfrom pathlib import Path\n"
            "Path(os.environ['NATIVE_UI_OUTPUT'],'actual.png').write_text('not an image')\n"
        )
        _, captured = self.capture(expected=1)
        self.assertTrue(any("not a decodable image" in item for item in captured["errors"]))

    def test_stale_project_image_is_not_counted(self):
        Image.new("RGB", (8, 8), "white").save(self.project / "old.png")
        self.profile["commands"] = [{"argv": [sys.executable, "-c", "pass"]}]
        self.profile["artifacts"] = [{"base": "project", "glob": "old.png", "role": "actual"}]
        _, captured = self.capture(expected=1)
        self.assertEqual(captured["artifacts"], [])

    def test_command_failure_preserves_logs_and_does_not_pass(self):
        self.profile["commands"].append({"argv": [sys.executable, "-c",
                                                 "print('native error');raise SystemExit(7)"]})
        path, captured = self.capture(expected=1)
        self.assertEqual(captured["commands"][-1]["exit_code"], 7)
        self.assertIn("native error", (path.parent / "command-2.log").read_text())
        self.review(path, expected=2)

    def test_timeout_does_not_pass(self):
        self.profile["commands"] = [{"argv": [sys.executable, "-c", "import time;time.sleep(5)"],
                                    "timeout_seconds": 0.1}]
        _, captured = self.capture(expected=1)
        self.assertEqual(captured["commands"][0]["status"], "timeout")

    def test_source_change_during_capture_is_invalid(self):
        self.profile["commands"].append({"argv": [sys.executable, "-c",
            "from pathlib import Path;Path('Component.swift').write_text('changed')"]})
        _, captured = self.capture(expected=1)
        self.assertIn("Production inputs changed during capture", captured["errors"])

    def test_baseline_write_is_detected(self):
        self.profile["commands"].append({"argv": [sys.executable, "-c",
            "from pathlib import Path;Path('goldens/new.txt').write_text('new reference')"]})
        _, captured = self.capture(expected=1)
        self.assertIn("Protected references changed during capture", captured["errors"])

    def test_code_change_after_capture_requires_new_render(self):
        path, _ = self.capture()
        (self.project / "Component.swift").write_text("patched after screenshot")
        self.review(path, expected=2)

    def test_artifact_tampering_is_detected(self):
        path, captured = self.capture()
        artifact = path.parent / captured["artifacts"][0]["path"]
        artifact.write_bytes(b"tampered")
        self.review(path, expected=2)

    def test_review_cannot_write_inside_protected_baselines(self):
        path, _ = self.capture()
        output = self.project / "goldens" / "review-output"
        result = self.command("review", "--capture", path, "--output", output)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse(output.exists())

    def test_numeric_mismatch_fails(self):
        self.profile["checks"][0]["expected"] = 10
        path, _ = self.capture()
        result = self.review(path, expected=1)
        self.assertEqual(result["checks"][0]["actual"], 8)

    def test_missing_numeric_evidence_is_needs_review(self):
        self.profile["artifacts"] = [self.profile["artifacts"][0]]
        path, _ = self.capture()
        self.assertEqual(self.review(path, expected=3)["status"], "needs_review")

    def test_unit_mismatch_is_not_an_implicit_conversion(self):
        self.profile["checks"][0]["unit"] = "px"
        path, _ = self.capture()
        self.assertEqual(self.review(path, expected=3)["status"], "needs_review")

    def test_nan_and_bool_cannot_be_numeric_expectations(self):
        for value in (True, float("nan"), float("inf")):
            with self.subTest(value=value):
                self.profile["checks"][0]["expected"] = value
                self.capture(expected=2)

    def test_missing_visual_finding_cannot_pass(self):
        self.profile["checks"] = [{"id": "badge", "kind": "visual",
                                  "description": "Badge is visible", "source": "User requirement"}]
        path, _ = self.capture()
        self.assertEqual(self.review(path, expected=3)["status"], "needs_review")
        findings = {"checks": [{"id": "badge", "status": "passed",
                                "observed": "Synthetic image inspected for this test"}]}
        self.assertEqual(self.review(path, findings)["status"], "passed")

    def test_visual_findings_cannot_override_numeric_results(self):
        path, _ = self.capture()
        findings = {"checks": [{"id": "gap", "status": "passed", "observed": "Looks fine"}]}
        self.review(path, findings, expected=2)

    def test_visual_findings_are_bound_to_this_capture(self):
        self.profile["checks"] = [{"id": "badge", "kind": "visual",
                                  "description": "Badge is visible", "source": "User requirement"}]
        path, _ = self.capture()
        findings = {"capture_sha256": "wrong-round",
                    "checks": [{"id": "badge", "status": "passed", "observed": "Old screenshot"}]}
        self.review(path, findings, expected=2)

    def test_identical_pixels_pass(self):
        self.profile["checks"] = [self.pixel()]
        path, _ = self.capture()
        result = self.review(path)
        self.assertEqual(result["checks"][0]["changed_pixels"], 0)
        directory = Path(result["checks"][0]["evidence_directory"])
        self.assertTrue((directory / "diff.png").is_file())

    def test_missing_reference_is_not_auto_recorded(self):
        self.profile["checks"] = [self.pixel()]
        reference = self.project / "goldens/reference.png"
        reference.unlink()
        path, _ = self.capture()
        self.assertEqual(self.review(path, expected=3)["status"], "needs_reference")
        self.assertFalse(reference.exists())

    def test_dimensions_are_not_silently_resized(self):
        self.profile["checks"] = [self.pixel()]
        Image.new("RGBA", (9, 8), "white").save(self.project / "goldens/reference.png")
        path, _ = self.capture()
        self.assertEqual(self.review(path, expected=3)["status"], "needs_review")

    def test_small_critical_region_catches_local_defect(self):
        self.profile["checks"] = [self.pixel()]
        self.profile["checks"][0].update(region=[0, 0, 1, 1], max_changed_fraction=0.02)
        image = Image.new("RGBA", (8, 8), "white")
        image.putpixel((0, 0), (0, 0, 0, 255))
        image.save(self.project / "goldens/reference.png")
        path, _ = self.capture()
        result = self.review(path, expected=1)
        self.assertEqual(result["checks"][0]["changed_fraction"], 1)

    def test_alpha_only_changes_are_visible_in_diff(self):
        actual, reference = self.root / "actual.png", self.root / "reference.png"
        Image.new("RGBA", (1, 1), (0, 0, 0, 255)).save(actual)
        Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(reference)
        result = LOOP.pixel_check(actual, reference, {}, self.root / "diff")
        self.assertEqual(result["status"], "failed")
        with Image.open(self.root / "diff/diff.png") as image:
            self.assertEqual(image.getpixel((0, 0)), (255, 0, 0))

    def test_argv_does_not_use_shell_expansion(self):
        literal = "$(touch should-not-exist)"
        self.profile["commands"].append({"argv": [sys.executable, "-c",
            "import sys;assert sys.argv[1]=='$(touch should-not-exist)'", literal]})
        self.capture()
        self.assertFalse((self.project / "should-not-exist").exists())


if __name__ == "__main__":
    unittest.main()
