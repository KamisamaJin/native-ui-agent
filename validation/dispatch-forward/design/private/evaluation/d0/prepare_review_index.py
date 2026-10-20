import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util,json,hashlib
R=Path("/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/dispatch-forward")
spec=importlib.util.spec_from_file_location("v3_review",R/"design/private/evaluator-prep/v3/evaluator.py")
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
plan=e.read(R/"design/private/evaluator-prep/normalized-d0.json")
oracle=e.read(R/"design/private/oracle.json")
for anonymous_id in ["sample-716d41","sample-e318ec"]:
    cap=R/"private/grade-capsules/d0"/anonymous_id
    manifest=e.read(cap/"manifest.json")
    entries={(x["platform"],x["case"]):x for x in manifest["observations"]}
    states={}
    for row in plan["rows"]:
        if row["sourceOnly"] or not row["full_content"]:continue
        key=(row["platform"],row["caseId"],row["stateId"])
        if key in states:continue
        entry=entries[key[:2]];ctx=e.load_context(entry,cap,row,oracle)
        gate=e.atomic_gate(row,ctx.get("mapping",{}),ctx.get("observation",{}))
        snapshots=[]
        for i,s in ctx.get("found",[]):
            snapshots.append({"index":i,"path":str((cap/Path(entry["observation"]["path"]).parent/s["screenshot"]).resolve()),
                "raw_screenshot":s["screenshot"],"viewport":s.get("viewport",s.get("logical_viewport_dp")),
                "app_frame":s.get("app_frame"),"scroll_offset_dp":s.get("scroll_offset_dp")})
        states[key]={"platform":key[0],"case":key[1],"checkpoint":key[2],"valid":ctx.get("valid"),
              "complete":ctx.get("complete"),"gate":gate,"reason":ctx.get("reason"),"snapshots":snapshots}
    output=R/"design/private/evaluation/d0"/anonymous_id/"review-index.json"
    output.write_text(json.dumps(list(states.values()),ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"anonymous_id":anonymous_id,"states":[{"key":"/".join(k),"valid":v["valid"],"complete":v["complete"],"stimulus":v["gate"].get("established"),"snapshots":[s["index"] for s in v["snapshots"]]} for k,v in states.items()]}))
