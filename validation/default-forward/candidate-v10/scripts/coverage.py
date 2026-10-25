#!/usr/bin/env python3
"""Audit planned requirement coverage; never infer missing observations as passes."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

METHODS={"native_ax","native_bounds","native_text_layout","native_action","native_pixels","source_review","visual"}
STATUSES={"passed","failed","needs_review","not_executed","unavailable"}


def load(path):
    return json.loads(path.read_text())


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def planned(plan):
    if plan.get("version")!=1 or not isinstance(plan.get("requirements"),list) or not plan["requirements"]:
        raise ValueError("Nonempty version1 requirement plan required")
    ids=set();matrix={}
    for requirement in plan["requirements"]:
        rid=requirement.get("id")
        if not isinstance(rid,str) or not rid or rid in ids:raise ValueError("Unique requirement IDs required")
        ids.add(rid)
        if not requirement.get("source") or not requirement.get("description"):raise ValueError("Requirement source/description required")
        cases=requirement.get("cases",[]);aspects=requirement.get("aspects",[])
        if not cases or len(cases)!=len(set(cases)) or not all(isinstance(c,str) and c for c in cases):raise ValueError("Unique nonempty cases required")
        aids=set()
        for aspect in aspects:
            aid=aspect.get("id");methods=aspect.get("methods",[]);runtime=aspect.get("runtime",False)
            if not isinstance(aid,str) or not aid or aid in aids:raise ValueError("Unique aspect IDs required")
            aids.add(aid)
            if not methods or not set(methods)<=METHODS:raise ValueError("Known evidence methods required")
            if runtime not in {False,"action","state"}:raise ValueError("runtime must be false, action or state")
            for case in cases:matrix[(rid,case,aid)]={"requirement":requirement,"aspect":aspect}
        if not aids:raise ValueError("At least one planned aspect required")
    for r in plan["requirements"]:
        if not set(r.get("related",[]))<=ids:raise ValueError("Unknown related requirement")
    return matrix


def evaluate(plan,observations,root):
    root=root.resolve();matrix=planned(plan);records={}
    for row in observations.get("records",[]):
        key=(row.get("requirement"),row.get("case"),row.get("aspect"))
        if key not in matrix or key in records:raise ValueError("Observation must match a unique planned cell: "+str(key))
        if row.get("status") not in STATUSES:raise ValueError("Unknown observation status")
        if row.get("status") in {"passed","failed"}:
            spec=matrix[key]["aspect"];method=row.get("method");evidence=row.get("evidence",[])
            if method not in spec["methods"] or not evidence or not row.get("observation") or row.get("execution")!="observed":
                raise ValueError("Pass/fail requires compatible observed evidence")
            runtime=spec.get("runtime",False)
            if runtime and method in {"source_review","visual"}:raise ValueError("Static review cannot pass/fail executed behavior")
            if runtime=="action" and method!="native_action":raise ValueError("Runtime action requires native event evidence")
            for item in evidence:
                path=(root/item["path"]).resolve()
                if not path.is_relative_to(root) or not path.is_file():raise ValueError("Evidence missing or outside root")
                if item.get("sha256")!=digest(path):raise ValueError("Evidence hash changed")
        records[key]=row
    cells=[];groups={}
    for key,spec in matrix.items():
        row=records.get(key)
        cell={"requirement":key[0],"case":key[1],"aspect":key[2],
              "status":row["status"] if row else "needs_review",
              "observation":row.get("observation") if row else "No matching observed evidence supplied",
              "record":row}
        cells.append(cell);groups.setdefault(key[:2],[]).append(cell)
    requirements=[];related=[]
    for (rid,case),items in groups.items():
        states={i["status"] for i in items};status="failed" if "failed" in states else "passed" if states=={"passed"} else "needs_review"
        requirements.append({"requirement":rid,"case":case,"status":status,"complete":all(i["status"] in {"passed","failed"} for i in items)})
        if status=="failed":
            relation=next(r for r in plan["requirements"] if r["id"]==rid).get("related",[])
            related.extend({"failed_requirement":rid,"related_requirement":r,"case":case,
                            "instruction":"Inspect related rule against actual evidence; no automatic defect/detection credit"} for r in relation)
    states={r["status"] for r in requirements}
    overall="failed" if "failed" in states else "passed" if states=={"passed"} else "needs_review"
    return {"version":1,"status":overall,"planned_cells":len(cells),"observed_decisions":sum(c["status"] in {"passed","failed"} for c in cells),
            "requirements":requirements,"cells":cells,"related_review_queue":related,
            "limits":"Hashes establish artifact integrity, not semantic truth. Review producers, coordinate meaning, source/state binding and complete viewport/action evidence independently."}


def main():
    p=argparse.ArgumentParser();p.add_argument("--plan",type=Path,required=True);p.add_argument("--observations",type=Path,required=True)
    p.add_argument("--root",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError("Use a fresh report path")
    report=evaluate(load(a.plan),load(a.observations),a.root)
    report["plan_sha256"]=digest(a.plan);report["observations_sha256"]=digest(a.observations)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":report["status"],"planned_cells":report["planned_cells"],"observed_decisions":report["observed_decisions"]}))
    return 0 if report["status"]=="passed" else 1 if report["status"]=="failed" else 3


if __name__=="__main__":
    try:raise SystemExit(main())
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print("Invalid coverage evidence: "+str(exc),file=sys.stderr);raise SystemExit(2)
