#!/usr/bin/env python3
"""Read-only public source-scope and context checkpoint after all ten seals."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import time


NAMES = {
    "T1": "CateringPackagePlanner",
    "T2": "TrainingPathwayEnrollment",
    "T3": "SubscriptionCapacityChange",
    "T4": "VisitorAccessPreclearance",
    "T5": "CandidateDispositionReview",
}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for block in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tree(root):
    if root.is_symlink():
        raise ValueError(f"Context root is a symlink: {root}")
    if not root.exists():
        return {"exists": False, "entries": {}}
    entries = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in sorted([*dirs, *files]):
            path = Path(parent) / name
            s = path.lstat()
            key = path.relative_to(root).as_posix()
            value = {"mode": stat.S_IMODE(s.st_mode)}
            if stat.S_ISLNK(s.st_mode):
                value.update(kind="symlink", target=os.readlink(path))
            elif stat.S_ISREG(s.st_mode):
                value.update(kind="file", bytes=s.st_size, sha256=sha(path))
            elif stat.S_ISDIR(s.st_mode):
                value.update(kind="directory")
            else:
                raise ValueError(f"Unsupported public context entry: {path}")
            entries[key] = value
    return {"exists": True, "entries": entries}


def checkpoint(run):
    manifest = read(run / "manifest.json")
    cohort_path = run / "COHORT-SEAL.json"
    cohort = read(cohort_path)
    if len(cohort["members"]) != 10:
        raise ValueError("Complete ten-member cohort seal required")
    source_diffs = {}
    contexts = {}
    for task in manifest["tasks"]:
        name = NAMES[task["id"]]
        permitted = {
            f"0/AlertToast/{name}.swift",
            f"1/java/com/example/reply/ui/components/business/{name}.kt",
        }
        for arm, cfg in task["arms"].items():
            key = f'{task["id"]}/{arm}'
            base = run / "arms" / task["id"] / arm
            seal = read(base / "SELF-SEAL.json")
            assert cohort["members"][key]["sha256"] == sha(base / "SELF-SEAL.json")
            initial = read(base / "initial/source.json")
            final = read(base / "final-source/source.json")
            assert seal["source_sha256"] == final["content_sha256"]
            changes = {
                p: {"initial": initial["files"].get(p), "final": final["files"].get(p)}
                for p in sorted(set(initial["files"]) | set(final["files"]))
                if initial["files"].get(p) != final["files"].get(p)
            }
            source_diffs[key] = {
                "initial_controller_content_sha256": initial["content_sha256"],
                "final_controller_content_sha256": final["content_sha256"],
                "initial_file_count": len(initial["files"]),
                "final_file_count": len(final["files"]),
                "changed_entries": changes,
                "within_predeclared_editable_files": set(changes) <= permitted,
                "scope": "Byte-map differences only; not a claim of successful repair or an OS write audit.",
            }
            arm_root = Path(cfg["workspace"]).parent.resolve()
            for ref in seal["active_configs"].values():
                config_path = Path(ref["path"])
                assert sha(config_path) == ref["sha256"]
                config = read(config_path)
                roots = [config.get("review_store"), config.get("source_review_store"), config.get("workflow", {}).get("root")]
                for value in roots:
                    if not value:
                        continue
                    root = Path(value)
                    if not root.resolve().is_relative_to(arm_root):
                        raise ValueError(f"Public context escaped its assigned arm: {root}")
                    if str(root) not in contexts:
                        contexts[str(root)] = {"owner": key, **tree(root)}
    return {
        "version": 1,
        "kind": "public-source-scope-and-context-byte-checkpoint",
        "at_unix": time.time(),
        "cohort": {"path": str(cohort_path), "sha256": sha(cohort_path)},
        "source_diffs": source_diffs,
        "public_contexts": contexts,
        "scope": "Public source-scope and context preservation only; no hidden input is opened and no quality judgment is made.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--compare", type=Path)
    args = ap.parse_args()
    value = checkpoint(args.run.resolve())
    if args.compare:
        old = read(args.compare)
        value["compared_checkpoint"] = {"path": str(args.compare.resolve()), "sha256": sha(args.compare)}
        value["public_contexts_unchanged"] = value["public_contexts"] == old["public_contexts"]
        value["source_diffs_unchanged"] = value["source_diffs"] == old["source_diffs"]
    with args.out.open("x") as fp:
        json.dump(value, fp, indent=2, sort_keys=True)
        fp.write("\n")
    print(json.dumps({
        "out": str(args.out), "sha256": sha(args.out),
        "all_source_changes_in_scope": all(v["within_predeclared_editable_files"] for v in value["source_diffs"].values()),
        "context_count": len(value["public_contexts"]),
        "public_contexts_unchanged": value.get("public_contexts_unchanged"),
    }))


if __name__ == "__main__":
    main()
