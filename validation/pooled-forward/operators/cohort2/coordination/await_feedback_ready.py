#!/usr/bin/env python3
"""Wait for one original D0 aggregate, then call the frozen acknowledgement.

Run this operator wrapper with process visibility.  It does not serve/retry a
request, derive a replacement clock, inspect source, or perform repairs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def save(path, value):
    with path.open("x") as fp:
        json.dump(value, fp, indent=2, sort_keys=True)
        fp.write("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--arm", choices=("A", "B"), required=True)
    ap.add_argument("--d0", required=True)
    a = ap.parse_args()
    r = a.root.resolve()
    run = r / "cache/business/run-cohort2"
    operator = Path(__file__).resolve().parent
    stem = f"{a.task}-{a.arm}"
    helper = r / "business-tools-v4/blind_study.py"
    expected_helper = "1a52cc62be5cee0bad34fefe8b54a7479761ca5ea5e8981937a8a1ad11ae6b05"
    assert hashlib.sha256(helper.read_bytes()).hexdigest() == expected_helper
    assignment = run / "arms" / a.task / a.arm / "assignment.json"
    result_path = run / "requests" / a.d0 / "result.json"
    ack = operator / f"{stem}-feedback-ready.json"
    stderr = operator / f"{stem}-feedback-ready.stderr.log"
    argv = [sys.executable, "-B", str(helper), "feedback-ready", "--assignment", str(assignment)]
    save(operator / f"{stem}-feedback-wait-admission.json", {
        "version": 1,
        "kind": "operator-original-D0-readiness-waiter",
        "started_at_unix": time.time(),
        "task": a.task, "arm": a.arm, "request_id": a.d0,
        "original_result": str(result_path), "argv": argv,
        "helper_sha256": expected_helper,
        "scope": "One frozen feedback-ready acknowledgement only, with no source inspection, SDK call, request retry or clock reset.",
    })
    while True:
        try:
            raw = result_path.read_bytes()
            result = json.loads(raw)
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.25)
            continue
        assert (result["task"], result["arm"], result["request_id"]) == (a.task, a.arm, a.d0)
        break
    observed = time.time()
    started = time.time()
    with ack.open("xb") as out, stderr.open("xb") as err:
        completed = subprocess.run(argv, stdout=out, stderr=err, check=False)
    finished = time.time()
    save(operator / f"{stem}-feedback-wait-result.json", {
        "version": 1,
        "kind": "operator-original-D0-readiness-waiter-result",
        "task": a.task, "arm": a.arm, "request_id": a.d0,
        "original_result": {"path": str(result_path), "sha256": hashlib.sha256(raw).hexdigest()},
        "original_D0_finished_at_unix": result["finished_at_unix"],
        "aggregate_observed_at_unix": observed,
        "ack_started_at_unix": started,
        "ack_finished_at_unix": finished,
        "ack_exit_code": completed.returncode,
        "ack_stdout": str(ack), "ack_stderr": str(stderr),
        "scope": "Acknowledgement latency metadata only; the frozen controller's authenticated first-D0 anchor remains the sole clock authority.",
    })
    print(json.dumps({"task": a.task, "arm": a.arm, "ack_exit_code": completed.returncode, "ack_stdout": str(ack)}, separators=(",", ":")), flush=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
