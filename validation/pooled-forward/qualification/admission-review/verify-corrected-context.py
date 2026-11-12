#!/usr/bin/env python3
"""Verify declared context/config/build-input bytes; never invoke SDK/native tools."""
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = OUT.parents[1]
PROFILES = BASE / "cache/qualification/profiles-v2"
CONTEXT = BASE / "operators/native-input-contexts-v2.json"
READS = {}
CHECKS = []


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def read(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    READS[str(path.relative_to(BASE))] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    return data


def load(path):
    return json.loads(read(path))


def check(name, value, details=None):
    CHECKS.append({"check": name, "passed": bool(value), "details": details})


def digest(path):
    return hashlib.sha256(read(path)).hexdigest()


contexts_raw = read(CONTEXT)
contexts = json.loads(contexts_raw)
admission = load(PROFILES / "ADMISSION.json")
previous = Path(admission["previous_admission"]["path"])
check("unchanged prior profile admission", digest(previous) == admission["previous_admission"]["sha256"])
previous_admission = load(previous)
check("v2 admission bound in context", digest(PROFILES / "ADMISSION.json") == contexts["profiles_admission_sha256"])
check("operator-supplied candidate freeze anchor", contexts["candidate_freeze_sha256"] == "acaa4e8595ea640450952429d3ed851108e0f13fda7aadc1a1ec3e71244f15ca",
      "Scalar supplied by parent operator; no candidate implementation or freeze artifact was opened")
check("COMPOSE_SNAPSHOT_ID owner selection", admission["COMPOSE_SNAPSHOT_ID"] == {"present": False, "sha256": None})
initial = load(OUT / "INITIAL-READSET.json")
for name, identity in initial["readset"].items():
    check("initial admitted input preserved " + name, digest(BASE / name) == identity["sha256"])

for name, expected in admission["configs"].items():
    check("v2 config seal " + name, digest(PROFILES / name) == expected)
for name, expected in previous_admission["production_files"].items():
    check("v2 production source-map hash " + name, digest(BASE / "cache/qualification/workspace" / name) == expected)

for case, entry in contexts["cases"].items():
    path = Path(entry["config"])
    config = load(path)
    previous_config = load(BASE / "cache/qualification/profiles" / (case + ".json"))
    changed = {key for key in set(config) | set(previous_config) if config.get(key) != previous_config.get(key)}
    check(case + " integration-only correction", changed == {"dependency_files", "dependency_environment"})
    check(case + " exact v2 config path", path.resolve() == (PROFILES / (case + ".json")).resolve())
    check(case + " actual v2 config bytes", digest(path) == entry["config_sha256"])
    context = entry["context"]
    platform = context["platform"]
    check(case + " canonical context digest", hashlib.sha256(canonical(context)).hexdigest() == entry["context_sha256"])
    for key, expected in context["files"].items():
        check(case + " bound file " + key, digest(Path(config[key])) == expected)
    for key in ["design_sha256", "routes_sha256", "environment_sha256", "policy_sha256", "launch_ref", "native_options", "capture_validity_ref"]:
        check(case + " approved/configured identity " + key, context[key] == config[key])
    model = context["source_model"]
    groups = {key: config["platform_source_roots"].get(key, []) for key in ["ios", "android", "shared"]}
    check(case + " distinct actual source namespaces", model["source_roots"] == config["source_roots"] and
          model["groups"] == groups and model["indices"] == [0 if platform == "ios" else 1])
    root = Path(config["native_options"]["package" if platform == "ios" else "project"])
    pinned_paths = set()
    for name, expected in context["build_dependencies"].items():
        build_path = Path(name) if Path(name).is_absolute() else root / name
        pinned_paths.add(build_path.resolve())
        check(case + " actual conventional/explicit build input " + name, digest(build_path) == expected)
    if platform == "android":
        launcher = (root / "gradlew").resolve()
        check(case + " S1 actual launcher now explicitly pinned", launcher in pinned_paths and
              str(launcher) in config["dependency_files"]["android"] and len(pinned_paths) == 11)
        check(case + " S2 selector explicitly declared", "COMPOSE_SNAPSHOT_ID" in config["dependency_environment"]["android"])
    else:
        check(case + " actual configured iOS runtime matches supplied inventory", context["host_identity"]["runtime"]["identifier"] == config["resources"]["ios"]["runtime"])
    effective = dict(os.environ)
    if platform == "ios":
        effective["DEVELOPER_DIR"] = config["native_options"]["developer-dir"]
        # An omitted sdk option does not rewrite the inherited SDKROOT
        # environment variable. The collector's CLI/build default is separate.
        if "sdk" in config["native_options"]:
            effective["SDKROOT"] = config["native_options"]["sdk"]
    else:
        effective["JAVA_HOME"] = str(Path(config["native_options"]["java-home"]).resolve())
        effective["ANDROID_HOME"] = str(Path(config["native_options"]["android-sdk"]).resolve())
    for name, expected in context["dependency_environment"].items():
        value = effective.get(name)
        actual = {"present": value is not None, "sha256": hashlib.sha256(value.encode()).hexdigest() if value is not None else None}
        check(case + " actual effective selector presence/hash " + name, actual == expected,
              {"actual": actual, "expected": expected})
    if platform == "android":
        check(case + " S2 actual selector absent", context["dependency_environment"]["COMPOSE_SNAPSHOT_ID"] == {"present": False, "sha256": None} and "COMPOSE_SNAPSHOT_ID" not in os.environ)

for name in ["candidate-v13.2/references/pooled-workflow.md", "candidate-v13.3/references/pooled-workflow.md"]:
    read(BASE / name)
result = {"review_id": "concrete-pre-native-admission-1-corrected-context", "at_utc": datetime.now(timezone.utc).isoformat(),
          "context_file_sha256": hashlib.sha256(contexts_raw).hexdigest(), "checks": CHECKS,
          "passed": sum(row["passed"] for row in CHECKS), "failed": [row for row in CHECKS if not row["passed"]],
          "readset": READS, "scope": "Actual allowed source/config/build bytes and current effective declared selector identity only. No raw environment values logged; no SDK/device/native/build command; no candidate implementation read or compiler-closure/native-truth claim."}
(OUT / "corrected-context-checks.json").write_text(json.dumps(result, indent=2) + "\n")
(OUT / "input-context-v2.json").write_bytes(contexts_raw)
print(json.dumps({"checks": len(CHECKS), "passed": result["passed"], "failed": result["failed"], "context_file_sha256": result["context_file_sha256"]}, indent=2))
