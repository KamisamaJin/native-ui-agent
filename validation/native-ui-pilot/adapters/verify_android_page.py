#!/usr/bin/env python3
"""Smoke-test the real Reply Activity, locating controls from current UI text."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adb", required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--apk", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    base = [args.adb, "-s", args.serial]
    commands = []

    def run(*argv):
        result = subprocess.run([*base, *argv], check=True, capture_output=True)
        commands.append({"argv": [*base, *argv], "exit_code": result.returncode,
                         "stdout": result.stdout.decode(errors="replace")[:4000]})
        return result.stdout

    def snapshot(name):
        run("shell", "uiautomator", "dump", "/sdcard/native-ui-pilot.xml")
        data = run("shell", "cat", "/sdcard/native-ui-pilot.xml")
        (args.output / (name + ".xml")).write_bytes(data)
        (args.output / (name + ".png")).write_bytes(run("exec-out", "screencap", "-p"))
        return ET.fromstring(data)

    def find(root, field, value):
        matches = [node for node in root.iter("node") if node.get(field) == value]
        if not matches:
            raise RuntimeError("Current UI has no " + field + "=" + value)
        return matches[0]

    def tap(node):
        x1, y1, x2, y2 = map(int, re.fullmatch(
            r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.attrib["bounds"]).groups())
        run("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))

    run("install", "-r", str(args.apk.resolve()))
    run("shell", "am", "force-stop", "com.example.reply")
    run("shell", "am", "start", "-W", "-n", "com.example.reply/.ui.MainActivity")
    inbox = snapshot("inbox")
    tap(find(inbox, "text", "Package shipped!"))
    detail = snapshot("detail")
    find(detail, "text", "Package shipped!")
    find(detail, "text", "Reply All")
    tap(find(detail, "content-desc", "Back"))
    returned = snapshot("returned-inbox")
    find(returned, "text", "Package shipped!")
    report = {"status": "passed", "scope": "Real Activity inbox -> email detail -> Back",
              "locator": "Current UIAutomator text/content-description and observed bounds; no added IDs",
              "apk_sha256": hashlib.sha256(args.apk.read_bytes()).hexdigest(),
              "commands": commands}
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "passed", "report": str(args.output / "report.json")}))


if __name__ == "__main__":
    main()
