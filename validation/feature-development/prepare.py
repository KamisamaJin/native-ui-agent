#!/usr/bin/env python3
"""Prepare fresh pinned upstream checkouts with the completed features and test hosts."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PROJECTS = {
    "android": ("https://github.com/android/compose-samples.git", "53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79", "compose-samples"),
    "ios": ("https://github.com/elai950/AlertToast.git", "76a1c1793cd3443001c20c6033beb84453b25d9f", "alerttoast"),
}


def run(*argv, cwd=None):
    subprocess.run(list(map(str, argv)), cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path, help="New empty output directory; existing directories are rejected")
    parser.add_argument("--android-sdk", required=True)
    parser.add_argument("--java-home", required=True)
    parser.add_argument("--ios-device", required=True)
    parser.add_argument("--developer-dir", default="/Applications/Xcode.app/Contents/Developer")
    parser.add_argument("--local-reply-repository", type=Path, help="Optional local object source; working-tree changes are not copied")
    parser.add_argument("--local-alerttoast-repository", type=Path)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=False)
    receipts = {}
    for platform, (url, revision, name) in PROJECTS.items():
        checkout = workspace / "checkouts" / name
        checkout.parent.mkdir(exist_ok=True)
        local = args.local_reply_repository if platform == "android" else args.local_alerttoast_repository
        if local:
            run("git", "clone", "--no-checkout", "--shared", local.resolve(), checkout)
            run("git", "remote", "set-url", "origin", url, cwd=checkout)
            run("git", "checkout", "--detach", revision, cwd=checkout)
        else:
            run("git", "init", checkout)
            run("git", "remote", "add", "origin", url, cwd=checkout)
            run("git", "fetch", "--depth", "1", "origin", revision, cwd=checkout)
            run("git", "checkout", "--detach", "FETCH_HEAD", cwd=checkout)
        actual = subprocess.run(["git", "rev-parse", "HEAD"], cwd=checkout,
                                check=True, text=True, capture_output=True).stdout.strip()
        if actual != revision:
            raise SystemExit("Wrong upstream revision")
        patches = [ROOT.parent / "native-ui-pilot/patches" / (platform + "-host.patch"),
                   ROOT / "patches" / (platform + "-feature.patch")]
        receipts[platform] = {"upstream": url, "revision": actual, "patches": []}
        for patch in patches:
            run("git", "apply", "--check", patch, cwd=checkout)
            run("git", "apply", patch, cwd=checkout)
            receipts[platform]["patches"].append({"file": patch.name,
                "sha256": hashlib.sha256(patch.read_bytes()).hexdigest()})
        if platform == "ios":
            shutil.copy2(ROOT.parent / "native-ui-pilot/adapters/AlertToast.Package.resolved",
                         checkout / "Package.resolved")
    run(sys.executable, ROOT / "configure.py", "--reply", workspace / "checkouts/compose-samples/Reply",
        "--alerttoast", workspace / "checkouts/alerttoast", "--android-sdk", args.android_sdk,
        "--java-home", args.java_home, "--ios-device", args.ios_device,
        "--developer-dir", args.developer_dir, "--profiles", workspace / "profiles")
    (workspace / "prepare-receipt.json").write_text(json.dumps(receipts, indent=2) + "\n")
    print("Ready:", workspace)


if __name__ == "__main__":
    main()
