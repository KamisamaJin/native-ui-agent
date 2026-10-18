#!/usr/bin/env python3
"""Archive native receipts and source snapshots after the blind ratings are locked.

No SDK, Git checkout, xctestrun host or xcresult bundle is published. Original
metadata is preserved byte-for-byte; relocation prefixes support portable audit.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent


def copy_file(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)


def curated_tree(src,dst):
    for p in src.rglob("*"):
        if not p.is_file():continue
        parts=p.relative_to(src).parts
        if any(s.endswith(".xcresult") for s in parts):continue
        if "paparazzi-report" in parts or "__pycache__" in parts:continue
        if p.suffix in {".xctestrun",".pyc"}:continue
        copy_file(p,dst/p.relative_to(src))


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--final-ratings-sealed",action="store_true",required=True)
    parser.parse_args()
    assignments=json.loads((ROOT/"cache/assignment.json").read_text())
    mapping=json.loads((ROOT/"cache/grading-map.json").read_text())
    analysis=json.loads((ROOT/"analysis-inputs.json").read_text())
    sealed_ids=set()
    for files in analysis["arms"].values():
        path=ROOT/files["final_rating"]
        expected=Path(str(path)+".sha256").read_text().split()[0]
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError("Final rating seal mismatch")
        rating=json.loads(path.read_text())["rating"]
        if not rating.get("review_completed_at") or rating["blinding"]["treatment_mapping_seen"] is not False:
            raise ValueError("Final blind rating is incomplete")
        sealed_ids.add(rating["anonymous_implementation_id"])
    if sealed_ids!=set(mapping.values()):raise ValueError("Both final ratings must be sealed first")
    out=ROOT/"unblinding";out.mkdir(exist_ok=True)
    for name in ["assignment.json","grading-map.json","self-review-seal.json","preregistration-push.json","device-cleanup.json"]:
        copy_file(ROOT/"cache"/name,out/name)
    relocation={str(ROOT/"cache/anonymous"):"evidence"}
    for label,arm0 in assignments.items():
        arm=arm0.replace("_","-");anon=mapping[label];worker=ROOT/"cache"/label
        relocation[str(worker)]="self-review/"+arm
        for phase in ["d0","final"]:
            for name in ["ReplyTransferPanel.kt","TransferToastPanel.swift"]:
                copy_file(ROOT/"cache"/("sealed-d0" if phase=="d0" else "sealed-final")/label/name,
                          ROOT/"implementations"/arm/phase/name)
            native=ROOT/"cache/runs"/phase/label
            for platform in ["android","ios"]:
                for case in (native/platform).iterdir():
                    if not case.is_dir():continue
                    target=ROOT/"evidence"/phase/anon/platform/case.name
                    for name in ["capture.json","junit.xml","xcresult-summary.json"]:
                        if (case/name).exists():copy_file(case/name,target/name)
                    copy_file(case.parent/(case.name+"-command.log"),target/"command.log")
            for name in ["submission-d0.json","submission-self-review.json","submission-final.json","self_review.json"]:
                p=worker/name
                if p.exists():copy_file(p,ROOT/"self-review"/arm/name)
        for folder in ["draft","self-review","repair","feedback"]:
            curated_tree(worker/folder,ROOT/"self-review"/arm/folder)
        receipt=ROOT/"cache/sealed-final"/label/"skill-verification.json"
        if receipt.exists():copy_file(receipt,out/"skill-snapshot-verification.json")
    # Anonymous packets retain the exact native images reviewed by the grader.
    curated_tree(ROOT/"cache/anonymous",ROOT/"evidence")
    for phase in ["d0","final"]:
        copy_file(ROOT/"cache/runs"/phase/"execution.json",ROOT/"execution"/(phase+".json"))
    curated_tree(ROOT/"cache/runs/d0-transport-invalid",ROOT/"infrastructure/excluded-transport-batch")
    curated_tree(ROOT/"cache/infrastructure",ROOT/"infrastructure/probes")
    curated_tree(ROOT/"cache/lifecycle-probe",ROOT/"infrastructure/lifecycle-probe")
    curated_tree(ROOT/"cache/replay/captures",ROOT/"replays/captures")
    copy_file(ROOT/"cache/replay/execution.json",ROOT/"replays/execution.json")
    for label,arm0 in assignments.items():
        arm=arm0.replace("_","-")
        copy_file(ROOT/"cache/replay"/arm/"prepare-receipt.json",ROOT/"replays"/(arm+"-prepare-receipt.json"))
        copy_file(ROOT/"cache/replay"/(arm+"-prepare.log"),ROOT/"replays"/(arm+"-prepare.log"))
        for platform in ["android","ios"]:
            copy_file(ROOT/"cache/runs/final"/label/platform/"I04-input.json",ROOT/"replays/captures"/arm/platform/"input.json")
    (out/"relocations.json").write_text(json.dumps(relocation,indent=2)+"\n")
    (out/"receipt.json").write_text(json.dumps({"unblinded_at":dt.datetime.now(dt.timezone.utc).isoformat(),
        "assignment_sha256":hashlib.sha256((out/"assignment.json").read_bytes()).hexdigest(),
        "declaration":"Both D0 and final anonymous ratings were sealed before publication of treatment mapping."},indent=2)+"\n")
    files={}
    for folder in ["evidence","implementations","self-review","infrastructure","unblinding","replays"]:
        for path in (ROOT/folder).rglob("*"):
            if path.is_file():files[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT/"artifact-index.json").write_text(json.dumps(files,indent=2)+"\n")
    print("Archived native artifacts; inspect before committing.")


if __name__=="__main__":main()
