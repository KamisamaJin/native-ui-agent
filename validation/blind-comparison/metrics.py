#!/usr/bin/env python3
"""Compute descriptive pilot metrics from sealed ratings, matches and timestamps.

Case/rule incidences are correlated observations, not independent samples.
Missing evidence is retained. A zero defect denominator yields null, never 100%.
"""
from collections import Counter
import argparse
import datetime as dt
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def elapsed(record):
    return round((dt.datetime.fromisoformat(record["submitted_at"].replace("Z","+00:00"))-
                  dt.datetime.fromisoformat(record["started_at"].replace("Z","+00:00"))).total_seconds(),3)


def key(case,incidence):
    return (case["platform"],case["case_id"],incidence["rule_id"])


def failure_keys(rating,stage=None):
    return {key(c,i) for c in rating["cases"] if stage is None or c["case_id"].startswith(stage)
            for i in c["incidences"] if i["status"]=="failed"}


def outcomes(rating,platform,prefix):
    incidences=[i for c in rating["cases"] if c["platform"]==platform and c["case_id"].startswith(prefix) for i in c["incidences"]]
    checks=[ch for i in incidences for ch in i["checks"]]
    return {"rule_outcomes":dict(Counter(i["status"] for i in incidences)),
            "applicable":sum(i.get("applicable",True) for i in incidences),
            "coverage":dict(Counter(i["coverage"] for i in incidences)),
            "check_outcomes":dict(Counter(ch["status"] for ch in checks)),
            "observed_methods":dict(Counter(ch.get("method") for ch in checks if ch.get("execution")=="observed")),
            "visual_ratings":{rule:[i["visual_rating"]["score"] for i in incidences if i["rule_id"]==rule and i.get("visual_rating")]
                              for rule in ["TQ-VIS-01","TQ-VIS-02"]}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--check",action="store_true");args=parser.parse_args()
    inputs=read(ROOT/"analysis-inputs.json");matching=read(ROOT/inputs["detection_matching"])
    assignment=read(ROOT/"unblinding/assignment.json")
    result={"sample":"One requirement, two platforms, one run per arm; no significance or causal speed claim.","arms":{}}
    for arm,files in inputs["arms"].items():
        d0=read(ROOT/files["d0_rating"])["rating"];final=read(ROOT/files["final_rating"])["rating"]
        anon=d0["anonymous_implementation_id"]
        if final["anonymous_implementation_id"]!=anon:raise ValueError("Mismatched anonymous submissions")
        old=failure_keys(d0);new=failure_keys(final,"I")
        matches=[m for m in matching["incidence_matches"] if m["anonymous_id"]==anon]
        detected={(m["platform"],m["case_id"],m["rule_id"]) for m in matches if m["detected"]}
        if not detected<=old:raise ValueError("Detection not present in confirmed D0 failures")
        reassessment={(m["platform"],m["case_id"],m["rule_id"]):m for m in final["repair_reassessment"]}
        if set(reassessment)!=old:raise ValueError("Every D0 failed incidence must be reassessed exactly once")
        platforms={}
        for platform in ["compose_android","swiftui_ios"]:
            failures={k for k in old if k[0]==platform};tp=failures&detected;fn=failures-detected
            evaluated={k for k in failures if reassessment[k]["status"] in {"passed","failed"}}
            fixed={k for k in evaluated if reassessment[k]["status"]=="passed"}
            platforms[platform]={"d0_failures":len(failures),"distinct_failed_rules":sorted({k[2] for k in failures}),
                "true_positive":len(tp),"false_negative":len(fn),
                "miss_rate":len(fn)/len(failures) if failures else None,
                "repaired":len(fixed),"repair_evaluable":len(evaluated),
                "repair_unavailable":len(failures-evaluated),
                "repair_success_rate":len(fixed)/len(evaluated) if evaluated else None,
                "new_failed_incidences":len({k for k in new-old if k[0]==platform}),
                "d0":outcomes(d0,platform,"I"),"final_initial":outcomes(final,platform,"I"),
                "final_holdout":outcomes(final,platform,"H")}
        times={phase:elapsed(read(ROOT/path)) for phase,path in files["timing"].items()}
        claims=[c for c in matching["claims"] if c["anonymous_id"]==anon]
        label=next(k for k,v in assignment.items() if v.replace("_","-")==arm)
        native={}
        for phase in ["d0","final"]:
            records=[r for r in read(ROOT/"execution"/(phase+".json")) if r["label"]==label]
            native[phase]={"captures":len(records),"capture_command_wall_seconds_sum":round(sum(r["elapsed_seconds"] for r in records),3),
                           "failed_commands":sum(r["exit_code"]!=0 for r in records)}
        result["arms"][arm]={"anonymous_id":anon,"platforms":platforms,"elapsed_seconds":times,
            "active_phase_total_seconds":round(sum(times.values()),3),
            "independent_native_scoring_execution":native,
            "self_claim_classifications":dict(Counter(c["classification"] for c in claims))}
    out=ROOT/"result-summary.json";payload=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
    if args.check:
        if out.read_text()!=payload:raise SystemExit("Result summary differs from sealed inputs")
    else:out.write_text(payload)
    print(out)


if __name__=="__main__":main()
