#!/usr/bin/env python3
"""Build the real Swift package test, bridge xctestrun environment, and capture it."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import subprocess


def expand_testroot(value, root):
    if isinstance(value, str):
        return value.replace("__TESTROOT__", str(root))
    if isinstance(value, list):
        return [expand_testroot(item, root) for item in value]
    if isinstance(value, dict):
        return {key: expand_testroot(item, root) for key, item in value.items()}
    return value


def bind_environment(node, values):
    count = 0
    if isinstance(node, dict):
        if "TestBundlePath" in node:
            node.setdefault("EnvironmentVariables", {}).update(values)
            count += 1
        for value in list(node.values()):
            count += bind_environment(value, values)
    elif isinstance(node, list):
        for value in node:
            count += bind_environment(value, values)
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--device-id", required=True)
    parser.add_argument("--scenario", choices=["normal", "long", "dark"], required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    cache = args.cache.resolve()
    derived = cache / "derived-data"
    destination = "platform=iOS Simulator,id=" + args.device_id
    environment = os.environ.copy()
    environment.setdefault("DEVELOPER_DIR", "/Applications/Xcode.app/Contents/Developer")
    common = ["-scheme", "AlertToast", "-destination", destination,
              "-derivedDataPath", str(derived),
              "-clonedSourcePackagesDirPath", str(cache / "packages"),
              "CODE_SIGNING_ALLOWED=NO"]
    subprocess.run(["xcodebuild", "build-for-testing", *common], cwd=args.project,
                   env=environment, check=True)
    files = sorted((derived / "Build/Products").glob("*.xctestrun"),
                   key=lambda path: path.stat().st_mtime_ns, reverse=True)
    if not files:
        raise SystemExit("build-for-testing did not produce an xctestrun test host")
    original = files[0]
    with original.open("rb") as stream:
        configuration = expand_testroot(plistlib.load(stream), original.parent)
    count = bind_environment(configuration, {
        "NATIVE_UI_OUTPUT": str(output), "NATIVE_UI_SCENARIO": args.scenario
    })
    if not count:
        raise SystemExit("No native test target found in xctestrun")
    configured = output / "native-ui.xctestrun"
    with configured.open("wb") as stream:
        plistlib.dump(configuration, stream)
    subprocess.run([
        "xcodebuild", "test-without-building", "-xctestrun", str(configured),
        "-destination", destination, "-parallel-testing-enabled", "NO",
        "-only-testing:AlertToastTests/AlertToastNativeUiTests/testCaptureHUD",
        "-resultBundlePath", str(output / "result.xcresult")
    ], cwd=args.project, env=environment, check=True)
    summary_process = subprocess.run([
        "xcrun", "xcresulttool", "get", "test-results", "summary",
        "--path", str(output / "result.xcresult"), "--compact"
    ], env=environment, check=True, text=True, capture_output=True)
    summary = json.loads(summary_process.stdout)
    (output / "xcresult-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    if (summary.get("totalTestCount") != 1 or summary.get("passedTests") != 1
            or summary.get("failedTests") != 0):
        raise SystemExit("The native test result must contain exactly one passing test")
    report = json.loads((output / "native-test.json").read_text())
    if report.get("executed_test") != "AlertToastNativeUiTests.testCaptureHUD":
        raise SystemExit("The intended native test did not execute")
    if not (output / "actual.png").is_file():
        raise SystemExit("Native test did not export an actual image")
    print("NATIVE_UI_CAPTURE_OK", args.scenario, output)


if __name__ == "__main__":
    main()
