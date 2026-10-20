import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util,copy,json,datetime
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("frozen_exact_rows",ROOT/"exact_rows.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def run(name,fn):
    fn();checks.append({"id":name,"status":"PASS"})
def reject(fn):
    try:fn()
    except ValueError:return
    raise AssertionError("Invalid join accepted")
def report(phase="d0",outcome="F",established=True):
    return {"phase":phase,"anonymous_id":"opaque","rows":[{"key":"ios/SYN/a01/generic","platform":"ios","case":"SYN","checkpoint":"a01","category":"business","denominator":"runtime_business","method":"callback","expected_sha256":"e"*64,"outcome":outcome,"stimulus_gate":{"required":True,"established":established}}]}
def pair(a,b,source=None):return m.paired_d0(a,b,source or ["a"*64,"a"*64])
run("exact-row-pair-preserved",lambda:pair(report(),report()))
def unknown():
    p=pair(report(),report(outcome="U",established=False))
    assert p["confirmed_business_miss_scope"]=={"anchor_misses":1,"observed_by_paired":0,"unassessed_by_paired":1}
run("paired-U-never-becomes-business-pass-or-failure",unknown)
run("reject-source-mismatch",lambda:reject(lambda:pair(report(),report(),["a"*64,"b"*64])))
run("reject-duplicate-key",lambda:reject(lambda:pair(report(),dict(report(),rows=report()["rows"]*2))))
run("reject-omitted-key",lambda:reject(lambda:pair(report(),dict(report(),rows=[]))))
def changed_expected():
    b=report();b["rows"][0]["expected_sha256"]="f"*64
    reject(lambda:pair(report(),b))
run("reject-expected-substitution",changed_expected)
run("reject-poststimulus-F-without-gate",lambda:reject(lambda:pair(report(established=False),report())))
run("reject-FINAL-in-D0-pair",lambda:reject(lambda:pair(report(),report(phase="final"))))
def matched():
    claims=[{"claim_id":"claim1","row_key":"ios/SYN/a01/generic","quote":"generic problem","reason":"same atomic requirement","review_citation":{"artifact":"synthetic","range_type":"lines","start":1,"end":1}}]
    p=m.review_match(report(),report("final","P"),claims)
    assert p["review_identified_miss_rows"]==1 and p["matches"][0]["repair_state"]=="repaired"
run("review-identification-and-repair-exact-row",matched)
def unknown_review():
    claims=[{"claim_id":"claim1","row_key":"ios/SYN/a01/generic","quote":"generic problem","reason":"same atomic requirement","review_citation":{"artifact":"synthetic"}}]
    p=m.review_match(report(outcome="U",established=False),report("final","P"),claims)
    assert p["review_identified_miss_rows"]==0 and p["matches"][0]["match_state"]=="D0_unassessed"
run("review-cannot-convert-U-to-confirmed-miss",unknown_review)
def unknown_key():
    claims=[{"claim_id":"claim1","row_key":"ios/HOLDOUT/a01/generic","quote":"generic","reason":"generic","review_citation":{"artifact":"synthetic"}}]
    reject(lambda:m.review_match(report(),report("final"),claims))
run("reject-review-non-D0-key",unknown_key)
(ROOT/"synthetic-controls-report.json").write_text(json.dumps({"version":1,"status":"PASS","tested_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"candidate_or_business_grades_used":False,"control_count":len(checks),"controls":checks},indent=2)+"\n")
print(json.dumps({"status":"PASS","control_count":len(checks)}))
