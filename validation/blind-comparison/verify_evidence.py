#!/usr/bin/env python3
"""Portable audit of the archived pilot, without Xcode, Gradle or a model.

Checks integrity, execution receipts, assignment commitment, scoring coverage,
stage ordering and metric arithmetic. Does not reproduce subjective AI grading.
"""
import hashlib
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def utc(value):return dt.datetime.fromisoformat(value.replace("Z","+00:00"))
def require(ok,message):
    if not ok:raise AssertionError(message)


def main():
    for name,digest in read(ROOT/"artifact-index.json").items():
        require(sha(ROOT/name)==digest,"Archived artifact changed: "+name)
    frozen=read(ROOT/"freeze.json")
    for name,digest in frozen["design_files"].items():
        require(sha(ROOT/"design-team"/name)==digest,"Frozen design changed: "+name)
    for name,digest in frozen["skill_files"].items():
        require(sha(ROOT.parent.parent/"native-ui-agent"/name)==digest,"Experimental Skill changed: "+name)
    require(sha(ROOT/"preregistration.md")==frozen["preregistration_sha256"],"Preregistration changed")
    require(sha(ROOT/"unblinding/assignment.json")==frozen["assignment_sha256"],"Assignment commitment changed")
    assignments=read(ROOT/"unblinding/assignment.json");mapping=read(ROOT/"unblinding/grading-map.json")
    require(set(mapping)==set(assignments),"Assignment keys differ")
    oracle=read(ROOT/"design-team/private/oracle.json")
    rules={r["rule_id"] for r in oracle["rules"]}
    count=0
    for phase in ["d0","final"]:
        cases=[f for f in oracle["fixtures"] if phase=="final" or f["stage"]=="initial"]
        for label,anon in mapping.items():
            arm=assignments[label].replace("_","-")
            for platform in ["android","ios"]:
                folder=ROOT/"evidence"/phase/anon/platform
                require({p.name for p in folder.iterdir() if p.is_dir()}=={c["fixture_id"] for c in cases},"Case matrix differs")
                source_name="ReplyTransferPanel.kt" if platform=="android" else "TransferToastPanel.swift"
                source=ROOT/"implementations"/arm/phase/source_name
                require(source.read_bytes()==(folder.parent/source_name).read_bytes(),"Reviewed source differs from archived implementation")
                for case in cases:
                    p=folder/case["fixture_id"];manifest=read(p/"capture.json");native=read(p/"native-report.json")
                    require(manifest["status"]=="captured_not_graded","Capture promoted to acceptance")
                    require(sha(p/"actual.png")==manifest["actual_sha256"],"Native image hash mismatch")
                    require(sha(p/"input.json")==manifest["fixture_sha256"],"Fixture bytes differ")
                    require(manifest["harness_sha256"]==sha(ROOT/"harness/capture.py"),"Wrong capture harness version")
                    helper="BlindPanelUiTest.kt" if platform=="android" else "BlindPanelUiTests.swift"
                    require(manifest["test_harness_sha256"]==sha(ROOT/"harness"/helper),"Wrong native test host version")
                    actual={Path(name).name:digest for name,digest in manifest["production_sources"].items()}
                    require(actual.get(source_name)==sha(source),"Captured production source differs")
                    require(all(c["exit_code"]==0 for c in manifest["commands"]),"Failed command in scored evidence")
                    if platform=="android":
                        attrs=ET.parse(p/"junit.xml").getroot().attrib
                        require(int(attrs["tests"])==1 and int(attrs.get("failures",0))==0 and int(attrs.get("errors",0))==0,"Wrong Android test count")
                        require(native["native_night_mode_mask"]==(32 if case["environment"]["appearance"]=="dark" else 16),"Native system appearance mismatch")
                    else:
                        summary=read(p/"xcresult-summary.json")
                        require(summary["totalTestCount"]==1 and summary["passedTests"]==1 and summary["failedTests"]==0,"Wrong iOS native test count")
                        require(native["font_category"]==case["environment"]["ios_content_size_category"],"Native font category mismatch")
                    count+=1
    require(count==56,"Expected 24 D0 + 32 final captures")
    replays=read(ROOT/"replays/execution.json")
    require(len(replays)==4,"Expected four clean native replays")
    for replay in replays:
        p=ROOT/"replays/captures"/replay["arm"]/replay["platform"]
        require(replay["exit_code"]==0 and replay["pixel_identical"],"Clean replay did not reproduce final evidence")
        require(sha(ROOT/"prepare.py")==replay["prepare_script_sha256"],"Replay preparation entry differs")
        require(sha(p/"actual.png")==replay["actual_sha256"]==replay["benchmark_sha256"],"Replay image differs")
        require(sha(p/"input.json")==read(p/"capture.json")["fixture_sha256"],"Replay input differs")
    inputs=read(ROOT/"analysis-inputs.json")
    matching_time=utc(read(ROOT/inputs["detection_matching"])["matched_at"])
    unblinded_at=utc(read(ROOT/"unblinding/receipt.json")["unblinded_at"])
    for arm,files in inputs["arms"].items():
        times={k:read(ROOT/p) for k,p in files["timing"].items()}
        require(utc(frozen["frozen_at"])<=utc(times["implementation"]["started_at"]),"Implementation preceded design freeze")
        require(utc(times["implementation"]["submitted_at"])<=utc(times["self_inspection"]["started_at"]),"Self-inspection preceded D0 freeze")
        for phase,field in [("d0","d0_rating"),("final","final_rating")]:
            path=ROOT/files[field];sidecar=Path(str(path)+".sha256")
            require(sha(path)==sidecar.read_text().split()[0],"Rating seal hash changed")
            rating=read(path)["rating"];anon=rating["anonymous_implementation_id"]
            if phase=="d0":
                require(rating["sealed_before_self_review_matching"] is True,"D0 not sealed before claims")
                require(utc(times["self_inspection"]["submitted_at"])<=utc(rating["review_started_at"])<=utc(rating["review_completed_at"])<=matching_time,"D0/detection stage ordering differs")
                require(utc(rating["review_completed_at"])<=utc(times["repair"]["started_at"]),"Repair preceded blind D0 scoring")
            else:
                require(utc(times["repair"]["submitted_at"])<=utc(rating["review_started_at"])<=utc(rating["review_completed_at"])<=unblinded_at,"Final/unblinding ordering differs")
            require(rating["blinding"]["treatment_mapping_seen"] is False,"Reviewer saw treatment mapping")
            require(rating["blinding"]["assignment_seen"] is False,"Reviewer saw assignment")
            expected={(f["fixture_id"],p) for f in oracle["fixtures"] if phase=="final" or f["stage"]=="initial" for p in f["platforms"]}
            require({(c["case_id"],c["platform"]) for c in rating["cases"]}==expected,"Rating case matrix differs")
            for case in rating["cases"]:
                require({i["rule_id"] for i in case["incidences"]}==rules,"Missing grading rule")
                platform="android" if case["platform"]=="compose_android" else "ios"
                native=read(ROOT/"evidence"/phase/anon/platform/case["case_id"]/"native-report.json")
                for incidence in case["incidences"]:
                    if incidence["status"]=="passed":
                        require(incidence["coverage_complete"] and all(c["status"]=="passed" for c in incidence["checks"]),"Missing coverage promoted to passed")
                    for check in incidence["checks"]:
                        if check["status"] in {"passed","failed"}:
                            require(check["execution"]=="observed" and check.get("evidence") and check.get("observation"),"Unobserved check passed/failed")
                        if check["status"]=="passed" and check.get("scope")=="runtime_callback":
                            require(check["method"]=="native_semantics" and native["activation_executed"],"Unexecuted callback passed")
                            require(check["actual_callback_events"]==check["expected_callback_events"],"Callback trace mismatch")
    matching=ROOT/inputs["detection_matching"]
    require(sha(matching)==Path(str(matching)+".sha256").read_text().split()[0],"Detection matching seal changed")
    self_seals=read(ROOT/"unblinding/self-review-seal.json")
    for label,digest in self_seals["reports"].items():
        arm=assignments[label].replace("_","-")
        require(sha(ROOT/"self-review"/arm/"self_review.json")==digest,"Self-review was changed after sealing")
    subprocess.run([sys.executable,str(ROOT/"metrics.py"),"--check"],check=True,stdout=subprocess.DEVNULL)
    print(json.dumps({"status":"passed_with_stated_scope","native_captures":count,"clean_native_replays":4,"frozen_design_and_skill_unchanged":True,
                      "assignment_commitment_valid":True,"sealed_ratings_and_metric_arithmetic_valid":True,
                      "does_not_reproduce":"AI image/source judgment or native SDK execution"}))


if __name__=="__main__":main()
