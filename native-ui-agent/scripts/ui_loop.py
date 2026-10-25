#!/usr/bin/env python3
"""Capture native UI evidence and review numeric, pixel, and visual checks."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone


BACKENDS = {
    "ios": {"snapshot-testing", "simulator"},
    "android": {"paparazzi", "compose-preview", "simulator"},
}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    def invalid(value):
        raise ValueError("Non-finite JSON number: " + value)
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=invalid)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def inside(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("Expected a nonempty project-relative path")
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Path escapes its root: " + relative)
    return path


def fingerprint(root, paths):
    result = {}
    for relative in paths:
        path = inside(root, relative)
        if not path.exists():
            result[relative] = None
            continue
        files = sorted(path.rglob("*")) if path.is_dir() else [path]
        entries = {}
        for item in files:
            resolved = item.resolve()
            if not resolved.is_relative_to(root):
                raise ValueError("Source or protected path contains an external symlink")
            if item.is_file():
                entries[str(item.relative_to(root))] = sha(item)
        result[relative] = entries
    return result


def validate(profile, project):
    if not isinstance(profile, dict) or type(profile.get("version")) is not int or profile["version"] != 1:
        raise ValueError("Profile must have integer version 1")
    platform = profile.get("platform")
    if platform not in BACKENDS or profile.get("backend") not in BACKENDS[platform]:
        raise ValueError("Invalid platform/backend combination")
    target = profile.get("target", {})
    if not isinstance(target, dict) or not target.get("description"):
        raise ValueError("target.description is required")
    sources = target.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("target.sources must list actual production inputs")
    for value in sources:
        if not inside(project, value).exists():
            raise ValueError("Production input does not exist: " + value)
    if not isinstance(profile.get("environment"), dict) or not profile["environment"]:
        raise ValueError("environment must describe the actual render configuration")
    commands = profile.get("commands")
    if not isinstance(commands, list) or not commands:
        raise ValueError("commands must be nonempty")
    for command in commands:
        if not isinstance(command, dict):
            raise ValueError("Each command must be an object")
        argv = command.get("argv")
        if not isinstance(argv, list) or not argv or any(
            not isinstance(x, str) or not x or "\0" in x for x in argv
        ):
            raise ValueError("argv must be a nonempty string array")
        if not inside(project, command.get("cwd", ".")).is_dir():
            raise ValueError("Command cwd must be an existing project directory")
        timeout = command.get("timeout_seconds", 900)
        if not number(timeout) or timeout <= 0:
            raise ValueError("timeout_seconds must be finite and positive")
        env = command.get("env", {})
        if not isinstance(env, dict) or any(
            not isinstance(k, str) or not k or "=" in k or "\0" in k
            or not isinstance(v, str) or "\0" in v for k, v in env.items()
        ):
            raise ValueError("Command env must contain valid string keys and values")
    selectors = profile.get("artifacts")
    if not isinstance(selectors, list) or not selectors:
        raise ValueError("artifacts must be nonempty")
    for item in selectors:
        if not isinstance(item, dict) or item.get("base") not in {"project", "output"}:
            raise ValueError("Artifact base must be project or output")
        if item.get("role") not in {"actual", "measurement", "native-report"}:
            raise ValueError("Invalid artifact role")
        pattern = item.get("glob")
        if not isinstance(pattern, str) or not pattern or Path(pattern).is_absolute() or ".." in Path(pattern).parts:
            raise ValueError("Artifact glob must stay within its base")
    checks = profile.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("checks must be nonempty")
    seen = set()
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("Each check must be an object")
        key = check.get("id")
        if not isinstance(key, str) or not key or key in seen:
            raise ValueError("Check ids must be unique nonempty strings")
        seen.add(key)
        if check.get("kind") not in {"visual", "numeric", "pixel"}:
            raise ValueError("Check kind must be visual, numeric, or pixel")
        if not check.get("description") or not check.get("source"):
            raise ValueError("Each check needs a description and independent expectation source")
        if type(check.get("required", True)) is not bool:
            raise ValueError("required must be boolean")
        if check["kind"] == "numeric":
            if not check.get("measurement") or not check.get("unit"):
                raise ValueError("Numeric checks need measurement and unit")
            if not number(check.get("expected")) or not number(check.get("tolerance", 0)) or check.get("tolerance", 0) < 0:
                raise ValueError("Numeric expected/tolerance must be finite; tolerance nonnegative")
        if check["kind"] == "pixel":
            inside(project, check.get("reference"))
            channel = check.get("channel_tolerance", 0)
            fraction = check.get("max_changed_fraction", 0)
            if type(channel) is not int or not 0 <= channel <= 255:
                raise ValueError("channel_tolerance must be an integer from 0 to 255")
            if not number(fraction) or not 0 <= fraction <= 1:
                raise ValueError("max_changed_fraction must be from 0 to 1")
            region = check.get("region")
            if region is not None and (
                not isinstance(region, list) or len(region) != 4
                or any(type(v) is not int for v in region)
                or min(region[:2]) < 0 or min(region[2:]) <= 0
            ):
                raise ValueError("region must be [x,y,width,height] in image pixels")
    if not any(c.get("required", True) for c in checks):
        raise ValueError("At least one required check is needed")
    protected = profile.get("protected_paths", [])
    if not isinstance(protected, list):
        raise ValueError("protected_paths must be an array")
    for value in protected:
        inside(project, value)
    return sorted(set(protected + [c["reference"] for c in checks if c["kind"] == "pixel"]))


def matches(profile, project, output):
    found = {}
    for selector in profile["artifacts"]:
        root = project if selector["base"] == "project" else output
        for path in sorted(root.glob(selector["glob"])):
            resolved = path.resolve()
            if not resolved.is_relative_to(root):
                raise ValueError("Artifact symlink escapes its base")
            if path.is_file():
                existing = found.get(resolved)
                if existing and existing != selector["role"]:
                    raise ValueError("The same file cannot have two artifact roles")
                found[resolved] = selector["role"]
    return found


def stop(process):
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        process.kill()
    process.wait()


def capture(args):
    project = args.project.resolve()
    if not project.is_dir():
        raise ValueError("Project directory does not exist")
    profile = read_json(args.profile)
    protected = validate(profile, project)
    output = args.output.resolve()
    for value in profile["target"]["sources"] + protected:
        if output.is_relative_to(inside(project, value)):
            raise ValueError("Output must be outside source/protected inputs")
    output.mkdir(parents=True, exist_ok=False)
    (output / "native").mkdir()
    before = {path: (path.stat().st_mtime_ns, sha(path))
              for path in matches(profile, project, output)}
    source_before = fingerprint(project, profile["target"]["sources"])
    protected_before = fingerprint(project, protected)
    report = {"version": 1, "status": "running", "project": str(project),
              "profile": profile, "started_at": now(), "commands": [], "artifacts": [],
              "source_fingerprint": source_before, "protected_fingerprint": protected_before,
              "interpretation": "Captured evidence is not a UI acceptance verdict."}
    write_json(output / "capture.json", report)
    interrupted = False
    for index, command in enumerate(profile["commands"]):
        log_path = output / f"command-{index + 1}.log"
        environment = os.environ.copy()
        environment.update(command.get("env", {}))
        environment["NATIVE_UI_OUTPUT"] = str(output / "native")
        # Only this explicit token is expanded; argv is never interpreted by a shell.
        argv = [arg.replace("{output}", str(output / "native")) for arg in command["argv"]]
        result = {"argv": argv, "cwd": str(inside(project, command.get("cwd", "."))),
                  "status": "error", "log": log_path.name}
        process = None
        started = time.monotonic()
        with log_path.open("wb") as log:
            try:
                process = subprocess.Popen(argv, cwd=result["cwd"], env=environment,
                                           stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=(os.name == "posix"))
                process.wait(timeout=command.get("timeout_seconds", 900))
                result["status"] = "passed" if process.returncode == 0 else "failed"
            except subprocess.TimeoutExpired:
                stop(process)
                result["status"] = "timeout"
            except KeyboardInterrupt:
                if process:
                    stop(process)
                result["status"], interrupted = "interrupted", True
            except OSError as exc:
                result["error"] = str(exc)
        result.update(exit_code=process.returncode if process else None,
                      duration_seconds=round(time.monotonic() - started, 3))
        report["commands"].append(result)
        write_json(output / "capture.json", report)
        if result["status"] != "passed":
            break
    errors = []
    if len(report["commands"]) != len(profile["commands"]) or any(
        item["status"] != "passed" for item in report["commands"]
    ):
        errors.append("A native command failed, timed out, or was interrupted")
    if fingerprint(project, profile["target"]["sources"]) != source_before:
        errors.append("Production inputs changed during capture")
    if fingerprint(project, protected) != protected_before:
        errors.append("Protected references changed during capture")
    artifact_dir = output / "artifacts"
    artifact_dir.mkdir()
    for path, role in matches(profile, project, output).items():
        state = (path.stat().st_mtime_ns, sha(path))
        if before.get(path) == state:
            continue  # Old images do not prove that this invocation rendered the component.
        destination = artifact_dir / f"{len(report['artifacts']):03d}-{path.name}"
        shutil.copy2(path, destination)
        report["artifacts"].append({"role": role, "original": str(path),
                                    "path": str(destination.relative_to(output)),
                                    "sha256": sha(destination)})
    actual = [a for a in report["artifacts"] if a["role"] == "actual"]
    if len(actual) != 1:
        errors.append(f"Expected exactly one fresh actual image; found {len(actual)}")
    else:
        try:
            from PIL import Image
            with Image.open(inside(output, actual[0]["path"])) as image:
                image.verify()
        except ImportError:
            errors.append("Pillow is required to validate the actual image")
        except (OSError, ValueError) as exc:
            errors.append("Actual artifact is not a decodable image: " + str(exc))
    report.update(status="error" if errors else "captured", errors=errors, finished_at=now())
    write_json(output / "capture.json", report)
    print(json.dumps({"status": report["status"], "capture": str(output / "capture.json"),
                      "capture_sha256": sha(output / "capture.json"),
                      "errors": errors}, ensure_ascii=False))
    return 130 if interrupted else (1 if errors else 0)


def pixel_check(actual, reference, check, directory):
    if not reference.is_file():
        return {"status": "needs_reference", "reason": "Reference image is missing"}
    try:
        from PIL import Image, ImageChops
    except ImportError:
        return {"status": "needs_review", "reason": "Pillow is required for pixel comparison"}
    with Image.open(actual) as a, Image.open(reference) as b:
        a, b = a.convert("RGBA"), b.convert("RGBA")
        if a.size != b.size:
            return {"status": "needs_review", "reason": "Image dimensions differ; no automatic resizing",
                    "actual_size": list(a.size), "reference_size": list(b.size)}
        region = check.get("region", [0, 0, a.width, a.height])
        x, y, width, height = region
        if x + width > a.width or y + height > a.height:
            raise ValueError("Pixel check region falls outside the image")
        a, b = a.crop((x, y, x + width, y + height)), b.crop((x, y, x + width, y + height))
        delta = ImageChops.difference(a, b)
        tolerance = check.get("channel_tolerance", 0)
        red, green, blue, alpha = delta.split()
        maximum = ImageChops.lighter(ImageChops.lighter(red, green),
                                    ImageChops.lighter(blue, alpha))
        changed = sum(maximum.histogram()[tolerance + 1:])
        total = a.width * a.height
        fraction = changed / total
        empty = Image.new("L", a.size)
        heat = Image.merge("RGB", (maximum, empty, empty))
        directory.mkdir(parents=True, exist_ok=False)
        a.save(directory / "actual.png")
        b.save(directory / "reference.png")
        heat.save(directory / "diff.png")
    return {"status": "passed" if fraction <= check.get("max_changed_fraction", 0) else "failed",
            "changed_pixels": changed, "total_pixels": total,
            "changed_fraction": fraction, "region": region,
            "reference_sha256": sha(reference), "evidence_directory": str(directory),
            "method": "RGBA pixel comparison; not a semantic or style-property measurement"}


def review(args):
    capture_path = args.capture.resolve()
    captured = read_json(capture_path)
    if captured.get("status") != "captured":
        raise ValueError("Only a successful capture can be reviewed")
    root = capture_path.parent
    profile, project = captured["profile"], Path(captured["project"])
    protected = validate(profile, project)
    if fingerprint(project, profile["target"]["sources"]) != captured["source_fingerprint"]:
        raise ValueError("Capture is stale: production inputs changed; render again")
    if fingerprint(project, protected) != captured["protected_fingerprint"]:
        raise ValueError("Capture is stale: protected references changed")
    artifacts = captured["artifacts"]
    for artifact in artifacts:
        path = inside(root, artifact["path"])
        if not path.is_file() or sha(path) != artifact["sha256"]:
            raise ValueError("Captured artifact is missing or was modified")
    actual = inside(root, next(a["path"] for a in artifacts if a["role"] == "actual"))
    findings = read_json(args.findings) if args.findings else {"checks": []}
    if not isinstance(findings, dict) or not isinstance(findings.get("checks"), list):
        raise ValueError("Findings must contain a checks array")
    if args.findings and findings.get("capture_sha256") != sha(capture_path):
        raise ValueError("Visual findings must be bound to this capture_sha256")
    visual = {}
    visual_ids = {c["id"] for c in profile["checks"] if c["kind"] == "visual"}
    for finding in findings["checks"]:
        if not isinstance(finding, dict):
            raise ValueError("Each visual finding must be an object")
        key = finding.get("id")
        if key not in visual_ids or key in visual:
            raise ValueError("Findings may contain only unique planned visual check ids")
        if finding.get("status") not in {"passed", "failed", "needs_review"} or not finding.get("observed"):
            raise ValueError("Visual findings need status and observed evidence description")
        visual[key] = finding
    measurements = {}
    for artifact in artifacts:
        if artifact["role"] == "measurement":
            data = read_json(inside(root, artifact["path"]))
            if not isinstance(data, dict):
                raise ValueError("Measurement artifact must be an object")
            for key, value in data.items():
                if key in measurements:
                    raise ValueError("Duplicate native measurement key")
                measurements[key] = value
    output = args.output.resolve()
    for value in profile["target"]["sources"] + protected:
        if output.is_relative_to(inside(project, value)):
            raise ValueError("Review output must be outside source/protected inputs")
    output.mkdir(parents=True, exist_ok=False)
    results = []
    for index, check in enumerate(profile["checks"]):
        result = {"id": check["id"], "kind": check["kind"], "description": check["description"],
                  "source": check["source"], "required": check.get("required", True)}
        if check["kind"] == "visual":
            finding = visual.get(check["id"])
            result.update(status=finding["status"] if finding else "needs_review",
                          observed=finding["observed"] if finding else "No visual finding supplied",
                          method="Model/human visual judgment; not an exact native measurement",
                          evidence=str(actual))
        elif check["kind"] == "pixel":
            result.update(pixel_check(actual, inside(project, check["reference"]), check,
                                      output / f"pixel-{index}"))
        else:
            value = measurements.get(check["measurement"])
            if (not isinstance(value, dict) or not number(value.get("value"))
                or value.get("unit") != check["unit"] or not value.get("method")):
                result.update(status="needs_review", reason="Native measurement missing, invalid, or in different units")
            else:
                passed = abs(value["value"] - check["expected"]) <= check.get("tolerance", 0)
                result.update(status="passed" if passed else "failed", actual=value["value"],
                              expected=check["expected"], unit=check["unit"],
                              tolerance=check.get("tolerance", 0), method=value["method"],
                              measurement=check["measurement"])
        results.append(result)
    statuses = {r["status"] for r in results if r["required"]}
    status = next((s for s in ("failed", "needs_reference", "needs_review") if s in statuses), "passed")
    report = {"version": 1, "status": status, "capture": str(capture_path),
              "capture_sha256": sha(capture_path), "platform": profile["platform"],
              "target": profile["target"], "environment": profile["environment"],
              "checks": results, "created_at": now(),
              "scope": "Configured component checks only; page integration is a separate verification."}
    write_json(output / "report.json", report)
    print(json.dumps({"status": status, "report": str(output / "report.json")}, ensure_ascii=False))
    return 0 if status == "passed" else (1 if status == "failed" else 3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    run = commands.add_parser("capture", help="Execute confirmed native render commands")
    run.add_argument("--project", required=True, type=Path)
    run.add_argument("--profile", required=True, type=Path)
    run.add_argument("--output", required=True, type=Path, help="New directory")
    check = commands.add_parser("review", help="Evaluate planned checks and merge visual findings")
    check.add_argument("--capture", required=True, type=Path)
    check.add_argument("--findings", type=Path)
    check.add_argument("--output", required=True, type=Path, help="New directory")
    native = commands.add_parser("native", help="Default approved native feedback chain: routing, diagnosis, planning, capture")
    native.add_argument("--config", required=True, type=Path)
    native.add_argument("--output", required=True, type=Path)
    native.add_argument("--previous", type=Path)
    native.add_argument("--previous-sha256")
    native.add_argument("--final", action="store_true")
    native.add_argument("--history", type=Path)
    native.add_argument("--intake", action="store_true")
    native.add_argument("--review-result", type=Path)
    native.add_argument("--review-result-sha256")
    bind = commands.add_parser("bind-native-review", help="Bind actual review to exact original source/state/images")
    bind.add_argument("--config", type=Path, required=True)
    bind.add_argument("--capture-result", type=Path, required=True)
    bind.add_argument("--capture-sha256", required=True)
    bind.add_argument("--submission", type=Path, required=True)
    bind.add_argument("--submission-sha256", required=True)
    bind.add_argument("--output", type=Path, required=True)
    bind.add_argument("--supersedes-sha256", action="append", default=[])
    bind.add_argument("--revision-reason")
    finish = commands.add_parser("finish-native-review", help="Close original final review without recapturing")
    finish.add_argument("--config", type=Path, required=True)
    finish.add_argument("--cycle", type=Path, required=True)
    finish.add_argument("--cycle-sha256", required=True)
    finish.add_argument("--review-result", type=Path)
    finish.add_argument("--review-result-sha256")
    finish.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == "bind-native-review":
            import evidence_review
            result = evidence_review.bind(json.loads(args.config.read_text()), args.capture_result, args.capture_sha256,
                args.submission, args.submission_sha256, args.output, supersedes=args.supersedes_sha256, revision_reason=args.revision_reason)
            print(json.dumps(result, indent=2)); return 0
        if args.action == "finish-native-review":
            import feedback_loop
            result = feedback_loop.complete_review(json.loads(args.config.read_text()), args.cycle, args.cycle_sha256,
                {"path": str(args.review_result), "sha256": args.review_result_sha256} if args.review_result else None, args.output)
            print(json.dumps(result, indent=2)); return 0 if result["status"] == "accepted" else 1
        if args.action == "native":
            import feedback_loop
            result = feedback_loop.run_cycle(json.loads(args.config.read_text()), args.output, previous=args.previous,
                previous_sha=args.previous_sha256, final=args.final,
                history=json.loads(args.history.read_text()) if args.history else [], intake=args.intake,
                review_result={"path": str(args.review_result), "sha256": args.review_result_sha256} if args.review_result else None)
            print(json.dumps(result, indent=2))
            # A queued review/repair is a successful dispatch, not delivery acceptance.
            return 1 if result["status"].startswith("blocked") else 0
        return capture(args) if args.action == "capture" else review(args)
    except (ValueError, OSError, KeyError, TypeError, StopIteration) as exc:
        print("Configuration/evidence error: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
