#!/usr/bin/env python3
"""Prepare claim-only anonymous material, disclosed after D0 ratings are sealed."""
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parent


def main():
    mapping=json.loads((ROOT/"cache/grading-map.json").read_text())
    packet=ROOT/"cache/anonymous/self-review";packet.mkdir(parents=True,exist_ok=True)
    for label,anon in mapping.items():
        worker=ROOT/"cache"/label;dest=packet/anon;dest.mkdir(exist_ok=True)
        raw=(ROOT/"cache/sealed-self-review"/label/"self_review.json").read_bytes()
        review=json.loads(raw);issues=review["observed_issues"]
        def neutralize(v):
            if isinstance(v,dict):return {k:neutralize(x) for k,x in v.items()}
            if isinstance(v,list):return [neutralize(x) for x in v]
            if isinstance(v,str):
                v=v.replace(str(worker),anon)
                v=re.sub(r'native-ui-agent|ui_loop|\b[Ss][Kk][Ii][Ll][Ll]\b','review-tool',v)
                return v
            return v
        claims=[]
        for index,issue in enumerate(issues):
            output=dest/issue["issue_id"];output.mkdir(exist_ok=True)
            rewritten=neutralize(issue);evidence=[]
            for number,path in enumerate(issue.get("evidence_paths",[])):
                src=Path(path)
                if not src.is_relative_to(worker) or not src.is_file():
                    raise ValueError("Invalid sealed evidence path: "+path)
                target=output/(str(number).zfill(2)+"-"+src.name)
                if src.suffix==".png":shutil.copy2(src,target)
                else:
                    target.write_text(neutralize(src.read_text()))
                evidence.append(str(target.relative_to(packet)))
            rewritten["evidence_paths"]=evidence;claims.append(rewritten)
        result={"anonymous_id":anon,"observed_issues":claims,
                "source_review_sha256":hashlib.sha256(raw).hexdigest(),
                "redactions":"Worker absolute path replaced by anonymous ID; tool names neutralized. Product observations/rules/numeric values unchanged. Only observed issues disclosed; workflow and passing-check counts withheld to reduce treatment clues."}
        (dest/"claims.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(packet)


if __name__=="__main__":main()
