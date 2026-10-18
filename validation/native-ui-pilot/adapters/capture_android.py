#!/usr/bin/env python3
"""Run the selected native Paparazzi test and preserve its machine-readable report."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("--project", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--scenario", choices=["normal", "long", "dark"], required=True)
args = parser.parse_args()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=True)
environment = os.environ.copy()
environment["NATIVE_UI_OUTPUT"] = str(output)
environment["NATIVE_UI_SCENARIO"] = args.scenario
command = ["./gradlew", ":app:testDebugUnitTest",
           "--tests", "com.example.reply.ReplyNativeUiTest.captureEmailCard", "--console=plain"]
result = subprocess.run(command, cwd=args.project, env=environment)
report = args.project / "app/build/test-results/testDebugUnitTest/TEST-com.example.reply.ReplyNativeUiTest.xml"
if report.is_file():
    shutil.copy2(report, output / "junit.xml")
if result.returncode:
    raise SystemExit(result.returncode)
suite = ET.parse(report).getroot()
if int(suite.attrib["tests"]) != 1 or int(suite.attrib.get("failures", 0)) or int(suite.attrib.get("errors", 0)):
    raise SystemExit("Expected exactly one successful native component test")
run_js = output / "paparazzi-report" / "runs" / (args.scenario + ".js")
payload = run_js.read_text().split(" = ", 1)[1].rstrip().removesuffix(";")
shots = json.loads(payload)
if len(shots) != 1 or shots[0]["testName"] != "com.example.reply.ReplyNativeUiTest#captureEmailCard":
    raise SystemExit("Expected one snapshot from the actual native test")
image_path = (output / "paparazzi-report" / shots[0]["file"]).resolve()
if not image_path.is_relative_to(output):
    raise SystemExit("Report image path escaped the native output")
shutil.copy2(image_path, output / "actual.png")
with Image.open(output / "actual.png") as image:
    measurements = json.loads((output / "measurements.json").read_text())
    measurements.update({
        "image_width": {"value": image.width, "unit": "px", "method": "Decoded native Paparazzi PNG width"},
        "image_height": {"value": image.height, "unit": "px", "method": "Decoded native Paparazzi PNG height"}
    })
(output / "measurements.json").write_text(json.dumps(measurements))
print("NATIVE_UI_CAPTURE_OK", args.scenario, output)
