#!/usr/bin/env python3
"""Create anonymous grading material without treatment, build logs or Skill files."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import shutil

ROOT=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser();p.add_argument("--phase",choices=["d0","final"],required=True);a=p.parse_args()
    mapping_file=ROOT/"cache/grading-map.json"
    if mapping_file.exists():
        mapping=json.loads(mapping_file.read_text())
    else:
        mapping={label:"submission-"+secrets.token_hex(3) for label in ["unit-52dc59","unit-07b638"]}
        mapping_file.write_text(json.dumps(mapping,indent=2)+"\n")
    packet=ROOT/"cache/anonymous"/a.phase;packet.mkdir(parents=True,exist_ok=True)
    cases=json.loads((ROOT/"design-team/private/oracle.json").read_text())["fixtures"]
    manifest={"phase":a.phase,"submissions":{},"scope":"Component-native artifacts, not full app E2E"}
    for label,anon in mapping.items():
        dest=packet/anon;dest.mkdir(exist_ok=True)
        source=ROOT/"cache"/("sealed-d0" if a.phase=="d0" else "sealed-final")/label
        for filename in ["ReplyTransferPanel.kt","TransferToastPanel.swift"]:
            shutil.copy2(source/filename,dest/filename)
        manifest["submissions"][anon]={"source_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir() if p.is_file()},"cases":[]}
        for platform in ["android","ios"]:
            for case in cases:
                if a.phase=="d0" and case["stage"]!="initial":continue
                caseid=case["fixture_id"];src=ROOT/"cache/runs"/a.phase/label/platform/caseid
                out=dest/platform/caseid;out.mkdir(parents=True,exist_ok=True)
                for filename in ["actual.png","semantics.json","native-report.json","ocr.json","observation.json","automatic-checks.json","infrastructure-error.json"]:
                    if (src/filename).exists():shutil.copy2(src/filename,out/filename)
                shutil.copy2(src.parent/(caseid+"-input.json"),out/"input.json")
                manifest["submissions"][anon]["cases"].append({"platform":platform,"fixture_id":caseid,"path":str(out.relative_to(packet)),"image_sha256":hashlib.sha256((out/"actual.png").read_bytes()).hexdigest() if (out/"actual.png").exists() else None})
    (packet/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(packet)


if __name__=="__main__":main()
