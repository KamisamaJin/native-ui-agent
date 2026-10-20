#!/usr/bin/env python3
"""Source-independent exact-row joining only. Does not grade implementation/evidence."""
import json,hashlib
from pathlib import Path
OUTCOMES=("P","F","U")
BUCKETS=("runtime_business","runtime_visual","runtime_integration","runtime_capability","input_member_integration","source_api")
def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":"))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rows(report):
    data=report["rows"]
    if any(r["outcome"] not in OUTCOMES for r in data):raise ValueError("Unknown outcome")
    keyed={r["key"]:r for r in data}
    if len(keyed)!=len(data):raise ValueError("Duplicate exact row")
    for r in data:
        if r["denominator"] not in BUCKETS:raise ValueError("Unknown denominator")
        gate=r["stimulus_gate"]
        if r["denominator"].startswith("runtime_") and gate.get("required") and r["outcome"]!="U" and gate.get("established") is not True:
            raise ValueError("Post-stimulus P/F lacks established gate")
    return keyed
def primary(row):
    return row["denominator"]=="runtime_business" and row["stimulus_gate"].get("required") is True
def confirmed_miss(row):
    return primary(row) and row["outcome"]=="F" and row["stimulus_gate"].get("established") is True
def align(left,right,allow_right_extra=False):
    a,b=rows(left),rows(right)
    if (not allow_right_extra and set(a)!=set(b)) or (allow_right_extra and not set(a)<=set(b)):
        raise ValueError("Missing or unplanned exact row keys")
    for key in a:
        for field in ("platform","case","checkpoint","category","denominator","method","expected_sha256"):
            if a[key][field]!=b[key][field]:raise ValueError("Row identity/expectation differs: "+key)
    return a,b
def paired_d0(anchor,paired,source_commitments):
    if anchor["phase"]!="d0" or paired["phase"]!="d0":raise ValueError("Only D0 source-paired comparison allowed")
    if len(source_commitments)!=2 or not all(isinstance(v,str) and len(v)==64 for v in source_commitments) or source_commitments[0]!=source_commitments[1]:
        raise ValueError("Paired evidence must use the exact same sealed D0 source")
    if anchor["anonymous_id"]!=paired["anonymous_id"]:raise ValueError("Anonymous source identity differs")
    a,b=align(anchor,paired)
    transitions=[]
    for key in sorted(a):
        left,right=a[key],b[key]
        transitions.append({"key":key,"platform":left["platform"],"denominator":left["denominator"],
            "anchor":left["outcome"],"paired":right["outcome"],
            "anchor_stimulus_established":left["stimulus_gate"].get("established") is True,
            "paired_stimulus_established":right["stimulus_gate"].get("established") is True,
            "primary_business_eligible":primary(left),
            "anchor_confirmed_business_miss":confirmed_miss(left),
            "paired_observes_anchor_miss":confirmed_miss(left) and confirmed_miss(right),
            "anchor_miss_unassessed_by_paired":confirmed_miss(left) and right["outcome"]=="U",
            "conflicting_assessed_outcomes":left["outcome"]!="U" and right["outcome"]!="U" and left["outcome"]!=right["outcome"]})
    counts={}
    for bucket in BUCKETS:
        subset=[r for r in transitions if r["denominator"]==bucket]
        counts[bucket]={"required":len(subset),"matrix":{x+"->"+y:sum(r["anchor"]==x and r["paired"]==y for r in subset) for x in OUTCOMES for y in OUTCOMES}}
    return {"version":1,"phase":"d0","anonymous_id":anchor["anonymous_id"],"source_commitment":source_commitments[0],
        "rows":transitions,"counts":counts,"confirmed_business_miss_scope":{
            "anchor_misses":sum(r["anchor_confirmed_business_miss"] for r in transitions),
            "observed_by_paired":sum(r["paired_observes_anchor_miss"] for r in transitions),
            "unassessed_by_paired":sum(r["anchor_miss_unassessed_by_paired"] for r in transitions)},
        "conflicting_assessed_keys":[r["key"] for r in transitions if r["conflicting_assessed_outcomes"]],
        "limitation":"Observation comparison on identical source; U is unavailable evidence, not a business pass/failure. No causal effect or assignment is inferred."}
def review_match(d0,final,claim_matches):
    if d0["phase"]!="d0" or final["phase"]!="final" or d0["anonymous_id"]!=final["anonymous_id"]:
        raise ValueError("Matching anonymous D0 then FINAL reports required")
    a,b=align(d0,final,allow_right_extra=True)
    identities=set();out=[]
    for match in claim_matches:
        key=match["row_key"];identity=(match["claim_id"],key)
        if identity in identities or key not in a:raise ValueError("Duplicate or non-D0 claim-row mapping")
        identities.add(identity)
        if not match.get("quote") or not match.get("reason") or not match.get("review_citation"):raise ValueError("Exact claim quote/citation/rationale required")
        left,right=a[key],b[key]
        state="confirmed_D0_problem" if left["outcome"]=="F" else "contradicted_by_assessed_D0" if left["outcome"]=="P" else "D0_unassessed"
        repair="repaired" if confirmed_miss(left) and right["outcome"]=="P" and right["stimulus_gate"].get("established") is True else "persisted" if confirmed_miss(left) and confirmed_miss(right) else "repair_unassessed" if confirmed_miss(left) else "not_primary_repair_eligible"
        out.append(dict(match,d0_outcome=left["outcome"],final_outcome=right["outcome"],match_state=state,
            denominator=left["denominator"],primary_confirmed_problem=confirmed_miss(left),repair_state=repair))
    detected={r["row_key"] for r in out if r["primary_confirmed_problem"]}
    all_misses={key for key,r in a.items() if confirmed_miss(r)}
    return {"version":1,"anonymous_id":d0["anonymous_id"],"matches":out,
        "primary_confirmed_business_miss_rows":len(all_misses),"review_identified_miss_rows":len(detected),
        "unmatched_primary_miss_keys":sorted(all_misses-detected),
        "rule":"Deduplicate atomic row keys, never merge causes or convert U. FINAL holdouts are excluded from D0 review matching."}
