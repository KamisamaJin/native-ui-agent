import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ios_observe.py"
spec = importlib.util.spec_from_file_location("ios_observe", SCRIPT)
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)


class ObserverInvariants(unittest.TestCase):
    def test_ambiguous_and_missing_identifiers_are_rejected(self):
        with self.assertRaises(ValueError): observer.unique_node([], "save")
        with self.assertRaises(ValueError): observer.unique_node([{"identifier": "save"}] * 2, "save")
        self.assertEqual(observer.unique_node([{"identifier": "save", "enabled": False}], "save")["enabled"], False)

    def test_native_points_map_to_screenshot_pixels_with_offset(self):
        result = observer.point_to_pixels({"x": 20, "y": 80, "width": 48, "height": 48},
                                          {"x": 10, "y": 20, "width": 390, "height": 844},
                                          {"width": 1170, "height": 2532})
        self.assertEqual(result, {"x": 30, "y": 180, "width": 144, "height": 144})

    def test_missing_lower_coverage_cannot_pass(self):
        self.assertEqual(observer.coverage_status({"bottom_reached": False, "missing_identifiers": []}), "failed")
        self.assertEqual(observer.coverage_status({"bottom_reached": True, "missing_identifiers": ["last"]}), "failed")
        self.assertEqual(observer.coverage_status({}), "failed")
        self.assertEqual(observer.coverage_status({"bottom_reached": True, "missing_identifiers": []}), "passed")

    def test_invalid_native_geometry_is_unavailable_not_zero_pixels(self):
        app = {"x": 0, "y": 0, "width": 390, "height": 844}
        pixels = {"width": 1170, "height": 2532}
        for invalid in [None, float("inf"), float("nan")]:
            self.assertIsNone(observer.point_to_pixels({"x": invalid, "y": 0, "width": 0, "height": 0}, app, pixels))
        with self.assertRaises(ValueError):
            observer.point_to_pixels(app, dict(app, width=float("inf")), pixels)

    def test_exported_attachment_names_must_match_unique_native_prefix(self):
        self.assertEqual(observer.resolve_attachment("000-top.png", {"000-top_0_UUID.png": "actual.png"}), "actual.png")
        with self.assertRaises(ValueError): observer.resolve_attachment("000-top.png", {"001-top_0_UUID.png": "other.png"})
        with self.assertRaises(ValueError): observer.resolve_attachment("000-top.png", {"000-top_0_A.png": "a.png", "000-top_1_B.png": "b.png"})

    def test_project_generation_uses_caller_bridge_and_unique_fresh_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bridge = root / "Custom.swift"; bridge.write_text("// caller factory")
            project = observer.generate_project(root / "generated", bridge, None)
            self.assertEqual((project.parent / "Bridge.swift").read_text(), "// caller factory")
            self.assertTrue((project / "xcshareddata/xcschemes/Observer.xcscheme").exists())
            with self.assertRaises(FileExistsError): observer.generate_project(root / "generated", bridge, None)


if __name__ == "__main__": unittest.main()
