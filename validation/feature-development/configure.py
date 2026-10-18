#!/usr/bin/env python3
"""Install thin test hosts and generate local profiles. Never edits acceptance/design."""
import argparse
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parent


def numeric(key, expected, unit, tolerance=0):
    return {"id": key.replace("_", "-"), "kind": "numeric", "measurement": key,
            "expected": expected, "unit": unit, "tolerance": tolerance,
            "description": key, "source": "Frozen design/acceptance in initial design commit; derived geometry documented in README"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reply", required=True, type=Path)
    parser.add_argument("--alerttoast", required=True, type=Path)
    parser.add_argument("--android-sdk", required=True)
    parser.add_argument("--java-home", required=True)
    parser.add_argument("--ios-device", required=True)
    parser.add_argument("--developer-dir", default="/Applications/Xcode.app/Contents/Developer")
    parser.add_argument("--profiles", type=Path, default=ROOT / "profiles")
    args = parser.parse_args()
    args.profiles.mkdir(parents=True, exist_ok=True)
    for platform, project, test_file, test_target in [
        ("android", args.reply.resolve(), "ReplyFeatureUiTest.kt", "app/src/test/java/com/example/reply/ReplyFeatureUiTest.kt"),
        ("ios", args.alerttoast.resolve(), "AlertToastFeatureUiTests.swift", "Tests/AlertToastTests/AlertToastFeatureUiTests.swift")]:
        native = project / ".native-ui"
        native.mkdir(exist_ok=True)
        shutil.copytree(ROOT / "design", native / "design", dirs_exist_ok=True)
        (project / test_target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "adapters" / test_file, project / test_target)
        shutil.copy2(ROOT / "adapters" / ("capture_" + platform + ".py"), native / "capture.py")
        spec = json.loads((ROOT / "design" / (platform + "-acceptance.json")).read_text())
        if platform == "ios":
            (native / "references").mkdir(exist_ok=True)
            shutil.copy2(ROOT.parent / "native-ui-pilot/references/ios/normal.png", native / "references/legacy.png")
        for scenario in spec["scenarios"]:
            checks = [{"id": "design-hierarchy", "kind": "visual",
                       "description": "Read actual native image against frozen independent SVG and acceptance, including readability and clipping",
                       "source": "Initial design commit / design/" + platform + "-reference.svg and acceptance.json"}]
            command = ["python3", ".native-ui/capture.py", "--project", ".", "--output", "{output}", "--scenario", scenario]
            if platform == "android":
                command_env = {"ANDROID_HOME": args.android_sdk, "JAVA_HOME": args.java_home}
                sources = ["app/src/main/java/com/example/reply/ui/components", "app/src/main/java/com/example/reply/data",
                           "app/src/main/java/com/example/reply/ui/theme", "app/src/main/res", test_target,
                           "app/build.gradle.kts", "gradle/libs.versions.toml", ".native-ui/capture.py"]
                checks.append(numeric("summary_visible", 0 if scenario == "empty" else 1, "boolean"))
                if scenario != "empty":
                    checks.extend([numeric("count_font",14,"sp"), numeric("description_font",12,"sp"),
                        numeric("text_gap",4,"dp",1), numeric("count_body_offset",44,"dp",1),
                        numeric("body_count_gap",24,"dp",1),
                        numeric("count_color",int("FFD3C4B4" if scenario=="dark" else "FF4F4539",16),"ARGB"),
                        numeric("count_ellipsized",0,"boolean"),
                        numeric("description_ellipsized",1 if scenario in ("long","narrow") else 0,"boolean")])
                artifacts = ["measurements.json", "native-test.json", "junit.xml", "semantics.json"]
            else:
                command += ["--cache", str(ROOT / "cache/ios"), "--device-id", args.ios_device]
                command_env = {"DEVELOPER_DIR": args.developer_dir}
                sources = ["Package.swift", "Sources/AlertToast", test_target, ".native-ui/capture.py"]
                if scenario == "legacy":
                    checks.append({"id":"legacy-appearance","kind":"pixel","reference":".native-ui/references/legacy.png",
                        "description":"No-progress initializer preserves original HUD","source":"Frozen upstream legacy reference from original pilot",
                        "channel_tolerance":0,"max_changed_fraction":0})
                else:
                    checks.extend([numeric("bar_fill_ratio",1 if scenario=="complete" else (0.73 if scenario=="dark" else 0.42),"ratio",0.025),
                                   numeric("bar_left",36,"pt",2),numeric("bar_height",4,"pt",1)])
                artifacts = ["measurements.json", "native-test.json", "xcresult-summary.json"]
            profile = {"version":1,"platform":platform,"backend":"paparazzi" if platform=="android" else "snapshot-testing",
                "target":{"description":spec["feature"]+" / "+scenario,"sources":sources},
                "environment":{"scenario":scenario,"theme":"dark" if scenario=="dark" else "light",
                    "renderer":"Paparazzi 2.0.0-alpha02" if platform=="android" else "SnapshotTesting 1.19.2 / iOS 26.5 / Xcode 27.1",
                    "width":"320dp" if scenario=="narrow" and platform=="android" else ("320pt" if scenario=="narrow" else "default"),
                    "font_scale":1,"preview_mode":platform=="android"},
                "commands":[{"argv":command,"env":command_env,"timeout_seconds":1200}],
                "artifacts":[{"base":"output","glob":"native/actual.png","role":"actual"}]+[
                    {"base":"output","glob":"native/"+name,"role":"measurement" if name=="measurements.json" else "native-report"}
                    for name in artifacts],
                "protected_paths":[".native-ui/design"]+([".native-ui/references"] if platform=="ios" else []),"checks":checks}
            (args.profiles / (platform+"-"+scenario+".json")).write_text(json.dumps(profile,ensure_ascii=False,indent=2)+"\n")
    print("Installed native test hosts and generated local profiles:", args.profiles)


if __name__ == "__main__":
    main()
