#!/usr/bin/env python3
"""Replace a small, explicitly mutable operator progress view at a milestone."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--next-step", required=True)
    ap.add_argument("--request-id")
    ap.add_argument("--blocker", action="append", default=[])
    ap.add_argument("--sync-status", action="store_true")
    a = ap.parse_args()
    r = a.root.resolve()
    run = r / "cache/business/run-cohort2"
    events = sorted((run / "events").glob("*.json"))
    latest = events[-1]
    event_bytes = latest.read_bytes()
    event = json.loads(event_bytes)
    seals = sorted(run.glob("arms/*/*/SELF-SEAL.json"))
    sealed = [str(p.parent.relative_to(run / "arms")) for p in seals]
    value = {
        "version": 1,
        "kind": "derived-mutable-study-progress-view",
        "updated_at_unix": time.time(),
        "active": {"task": a.task, "arm": a.arm, "stage": a.stage},
        "public_self_sealed_count": len(sealed),
        "public_self_sealed_members": sealed,
        "cohort_seal_receipt_exists": (run / "COHORT-SEAL.json").is_file(),
        "hidden_authorization_receipt_exists": (run / "HIDDEN-AUTHORIZATION.json").is_file(),
        "blocking_conditions": a.blocker,
        "next_step": a.next_step,
        "latest_original_event": {
            "path": str(latest),
            "sha256": hashlib.sha256(event_bytes).hexdigest(),
            "kind": event["kind"],
            "sequence": event["sequence"],
        },
        "scope": "Mutable progress only; original events, sources, claims and evidence remain immutable. This file is not a frozen public input or a quality verdict.",
    }
    if a.request_id:
        request_root = run / "requests" / a.request_id
        value["active"]["request_id"] = a.request_id
        value["active"]["result_exists"] = (request_root / "result.json").is_file()
    dest = Path(__file__).with_name("PROGRESS.json")
    temp = dest.with_suffix(".tmp")
    with temp.open("w") as fp:
        json.dump(value, fp, indent=2, sort_keys=True)
        fp.write("\n")
    os.replace(temp, dest)
    if a.sync_status:
        status_path = r / "STATUS.json"
        status = json.loads(status_path.read_text()) if status_path.is_file() else {}
        status["at_unix"] = value["updated_at_unix"]
        status["current"] = f"{a.task}/{a.arm} {a.stage}"
        status["progress_view"] = "operators/cohort2/coordination/PROGRESS.json"
        status["next"] = a.next_step
        status["sealed_public_arms"] = {}
        for seal_path in seals:
            seal = json.loads(seal_path.read_text())
            initial = json.loads((seal_path.parent / "initial/source.json").read_text())
            status["sealed_public_arms"][f'{seal["task"]}/{seal["arm"]}'] = {
                "own_wall_seconds": seal["own_delivery_wall_seconds"],
                "public_service_accepted": seal["public_service_accepted"],
                "source_unchanged": seal["source_sha256"] == initial["content_sha256"],
                "android": seal["final_outcomes"]["android"].get("service_status"),
                "ios": seal["final_outcomes"]["ios"].get("service_status"),
                "scope": "Frozen public service only; independent hidden quality remains separate.",
            }
        status_temp = status_path.with_suffix(".tmp")
        with status_temp.open("w") as fp:
            json.dump(status, fp, indent=2, sort_keys=True)
            fp.write("\n")
        os.replace(status_temp, status_path)
    print(json.dumps(value, separators=(",", ":")))


if __name__ == "__main__":
    main()
