#!/usr/bin/env python3
"""Read-only operator checks of a public self-seal and its original pointers.

This does not inspect private inputs, judge source/image quality, or mutate a
controller record.  It writes one exclusive operator receipt when asked.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def checked(ref):
    p = Path(ref["path"])
    assert p.is_file(), f"missing original: {p}"
    assert sha(p) == ref["sha256"], f"changed original: {p}"
    return p


def verify(run, task, arm):
    base = run / "arms" / task / arm
    seal_path = base / "SELF-SEAL.json"
    seal = load(seal_path)
    assert seal["kind"] == "self_sealed"
    assert (seal["task"], seal["arm"]) == (task, arm)
    event = run / "events" / f'{seal["sequence"]:06d}.json'
    assert event.read_bytes() == seal_path.read_bytes(), "self-seal/event mismatch"
    checked({"path": seal["claim_path"], "sha256": seal["claim_sha256"]})
    source = load(base / "final-source" / "source.json")
    assert source["content_sha256"] == seal["source_sha256"]
    assert set(seal["final_outcomes"]) == {"ios", "android"}
    assert set(seal["retirement"]) == {"ios", "android"}
    outcomes = {}
    for profile, outcome in seal["final_outcomes"].items():
        supplied_originals = {}
        for key in ("completion", "inventory"):
            ref = outcome.get(key)
            if ref:
                checked(ref)
            supplied_originals[key] = ref
        outcomes[profile] = {
            k: outcome.get(k)
            for k in ("accepted", "service_status", "exit_code", "action", "integrity", "error")
        }
        outcomes[profile]["original_pointers"] = supplied_originals
    resources = {}
    for profile, ref in seal["retirement"].items():
        resource = load(checked(ref))
        assert resource["final"] is True, f"unclosed resources: {profile}"
        for key in ("cleanup_errors", "remaining_directories", "remaining_devices"):
            assert resource.get(key) == [], f"unclosed {profile}: {key}"
        resources[profile] = {
            "original": ref,
            "final": resource["final"],
            "cleanup_errors": resource["cleanup_errors"],
            "remaining_directories": resource["remaining_directories"],
            "remaining_devices": resource["remaining_devices"],
        }
    return {
        "version": 1,
        "kind": "operator-public-self-seal-pointer-and-closure-verification",
        "at_unix": time.time(),
        "task": task,
        "arm": arm,
        "self_seal": {"path": str(seal_path), "sha256": sha(seal_path)},
        "source_sha256": seal["source_sha256"],
        "claim_sha256": seal["claim_sha256"],
        "public_service_accepted": seal["public_service_accepted"],
        "own_delivery_wall_seconds": seal["own_delivery_wall_seconds"],
        "outcomes": outcomes,
        "positive_resource_closure": resources,
        "scope": "Original pointer integrity and public closure only; no independent quality judgment.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--arm", choices=("A", "B"), required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    receipt = verify(args.run.resolve(), args.task, args.arm)
    data = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x") as fp:
            fp.write(data)
    print(data, end="")


if __name__ == "__main__":
    main()
