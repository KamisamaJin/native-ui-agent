#!/usr/bin/env python3
"""Original packet replay with process/SDK and source-write vetoes."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback
import types

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
R = OUT.parents[1]
SKILL = R / "candidate-v13.9"
EVIDENCE = R / "cache/qualification/evidence-candidate-v13.9"
READS = set()
BLOCKED = []
PYC_VETOES = []


def veto(event, args):
    if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "os.posix_spawnp", "os.fork", "os.exec", "os.kill", "os.killpg"}:
        BLOCKED.append({"event": event, "status": "blocked_before_execution"})
        raise RuntimeError("Read-only audit forbids process/SDK operation: " + event)
    if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).resolve()
        mode = args[1] or ""
        flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
        writing = any(c in str(mode) for c in "wax+") or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if writing and not path.is_relative_to(OUT):
            BLOCKED.append({"event": event, "path": str(path), "status": "blocked_source_write"})
            raise RuntimeError("Audit write outside new review directory")
        if not writing and path.is_relative_to(SKILL) and "__pycache__" in path.parts:
            PYC_VETOES.append(str(path))
            raise FileNotFoundError("Replay audit reads pinned source rather than cached bytecode")
        if not writing and path.is_relative_to(R) and not path.is_relative_to(OUT): READS.add(str(path))
    if event in {"os.mkdir", "os.remove", "os.rmdir", "os.unlink"} and args and isinstance(args[0], (str, bytes, os.PathLike)):
        if not Path(os.fsdecode(args[0])).resolve().is_relative_to(OUT): raise RuntimeError("Audit filesystem mutation outside output")
    if event in {"os.rename", "os.link", "os.symlink"}:
        for p in args[:2]:
            if isinstance(p, (str, bytes, os.PathLike)) and not Path(os.fsdecode(p)).resolve().is_relative_to(OUT):
                raise RuntimeError("Audit filesystem mutation outside output")


sys.addaudithook(veto)
spec = importlib.util.spec_from_file_location("pinned_native_receipt_replayer", OUT / "pinned-verify_benchmark.py")
replayer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replayer)
results = []
for stage, case in [("C0-ios", "ios-cold"), ("C07-ios", "ios-cold"), ("C0-android", "android")]:
    packet = EVIDENCE / stage / "capture/result.json"
    config = R / "cache/qualification/profiles-v3" / (case + ".json")
    output = OUT / ("replay-" + stage + ".json")
    try:
        replayer.replay(types.SimpleNamespace(skill=str(SKILL), config=str(config), packet=str(packet), output=str(output)))
        value = json.loads(output.read_text())
        results.append({"stage": stage, "status": "P", "packet_sha256": hashlib.sha256(packet.read_bytes()).hexdigest(),
                        "counts": value["native_counts"], "native_tests": value["native_tests"],
                        "source_must_claim_ids": value["source_must_claim_ids"], "evidence_class": "HOST replay of original NATIVE artifacts"})
    except BaseException as exc:
        (OUT / ("replay-" + stage + ".error.txt")).write_text(traceback.format_exc())
        results.append({"stage": stage, "status": "U", "error": {"type": type(exc).__name__, "message": str(exc)}})

readset = {}
for name in sorted(READS):
    path = Path(name)
    if path.is_file():
        data = path.read_bytes()
        readset[name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
summary = {"results": results, "blocked_process_or_write_attempts": BLOCKED, "pinned_source_bytecode_vetoes": PYC_VETOES,
           "readset": readset, "reviewer_SDK_calls": 0, "reviewer_native_calls": 0,
           "scope": "Read-only Python reconstruction; no fresh SDK/native execution, process management or present-time resource inventory"}
(OUT / "REPLAY-RESULTS.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({k: v for k, v in summary.items() if k != "readset"}, indent=2))
