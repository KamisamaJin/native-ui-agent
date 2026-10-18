#!/usr/bin/env python3
"""Run sealed inputs through the same native harness for both frozen submissions.

This is an experiment coordinator, not a product acceptance test. Captures and
observations are distinct from the independent grader's conclusions.
"""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def native_input(case):
    e = case["environment"]
    result = dict(case_id=case["fixture_id"], width=e["viewport_width"],
                  height=e["viewport_height"], dark=e["appearance"] == "dark",
                  rtl=e["layout_direction"] == "rtl", font_scale=e["android_font_scale"],
                  ios_category=e["ios_content_size_category"],
                  expanded=case["expanded"], items=[dict(item,progress=(item["progress"]["double_special"]
                      if isinstance(item["progress"],dict) else item["progress"])) for item in case["items"]])
    # One actual native accessibility activation is supported by this host.
    # Only choose controls expected to be visible before caller state updates.
    visible = {"transfer.retry." + r["id"] for r in case["expected"]["rows"]
               if r["retry_visible"]}
    if case["expected"]["toggle_visible"]:
        visible.add("transfer.toggle")
    for action in case["actions"]:
        if action["event"] == "native_activate_once" and action["target_identifier"] in visible:
            result["activate_id"] = action["target_identifier"]
            break
    return result


def observe_android(folder, case):
    nodes = read(folder / "semantics.json")
    tags = {n["tag"]: n for n in nodes if n.get("tag")}
    children = {}
    for n in nodes:
        children.setdefault(n["parent_id"], []).append(n)
    def descendants(n):
        return [n] + [x for child in children.get(n["node_id"], []) for x in descendants(child)]
    def texts(tag):
        return " ".join(n["text"] for n in descendants(tags[tag]) if n.get("text")) if tag in tags else None
    measurements = {}
    def put(path, value):
        measurements[path] = dict(value=value, method="native_semantics",
                                  evidence="semantics.json", execution="observed")
    for path, tag in {"title_text":"title", "summary_text":"summary", "count_text":"count",
                      "aggregate_percent_text":"percent", "toggle_text":"toggle",
                      "more_text":"more", "empty_text":"empty"}.items():
        put(path, texts("transfer." + tag))
    for path, tag in {"aggregate_visible":"progress", "list_visible":"list", "toggle_visible":"toggle"}.items():
        put(path, "transfer." + tag in tags)
    put("visible_row_ids", [n["tag"][13:] for n in nodes if n.get("tag", "").startswith("transfer.row.")])
    hidden = [] if case["expanded"] else [i["id"] for i in case["items"][2:]]
    put("hidden_row_ids_absent", not any("transfer.row."+i in tags for i in hidden))
    put("required_identifiers", list(tags))
    for path, tag, key in [("toggle_label","transfer.toggle","content_description"),
                           ("toggle_state","transfer.toggle","state_description"),
                           ("aggregate_fraction","transfer.progress","progress"),
                           ("aggregate_label","transfer.progress","content_description")]:
        if tag in tags:
            put(path, tags[tag].get(key))
    for item in case["items"]:
        i=item["id"]; prefix="rows/"+i+"/"; row="transfer.row."+i
        if row not in tags:
            continue
        put(prefix+"status_text", texts("transfer.status."+i))
        put(prefix+"progress_visible", "transfer.progress."+i in tags)
        put(prefix+"retry_visible", "transfer.retry."+i in tags)
        for suffix, tag, key in [("full_name_semantics","transfer.name."+i,"content_description"),
                                 ("progress_fraction","transfer.progress."+i,"progress"),
                                 ("progress_label","transfer.progress."+i,"content_description"),
                                 ("progress_accessible_percent","transfer.progress."+i,"state_description"),
                                 ("retry_label","transfer.retry."+i,"content_description")]:
            if tag in tags:
                val=tags[tag].get(key)
                if suffix=="full_name_semantics" and not val:
                    val=texts(tag)
                put(prefix+suffix,val)
        retry=tags.get("transfer.retry."+i); status=tags.get("transfer.status."+i)
        if retry and status:
            # Actual layout coordinates, not environmental compactness guesses.
            position="below_status" if retry["bounds_dp"][1] >= status["bounds_dp"][3]-2 else "trailing"
            put(prefix+"retry_position",position)
    if "transfer.toggle" in tags and "transfer.title" in tags:
        put("compact", tags["transfer.toggle"]["bounds_dp"][1] >= tags["transfer.title"]["bounds_dp"][3]-2)
    # Actual native hit bounds for all available controls.
    environment=case.get("environment",{})
    viewport_width=environment.get("viewport_width",390)
    viewport_height=environment.get("viewport_height",620)
    buttons=[n for n in nodes if n.get("clickable") and n.get("tag", "").startswith("transfer.")
             and 0 < n["bounds_dp"][0] < n["bounds_dp"][2] < viewport_width
             and 0 < n["bounds_dp"][1] < n["bounds_dp"][3] < viewport_height]
    if buttons:
        put("geometry/button_hit_width", min(n["touch_bounds_dp"][2]-n["touch_bounds_dp"][0] for n in buttons))
        put("geometry/button_hit_height", min(n["touch_bounds_dp"][3]-n["touch_bounds_dp"][1] for n in buttons))
    return dict(build_status="passed", render_status="passed", measurements=measurements,
                limitations=["line count is not configured maxLines", "RTL environment is not fill-direction evidence",
                             "native semantic bounds are not pixel measurements"])


def lane(label, platform, phase, cases):
    workspace=ROOT/"cache"/label
    records=[]
    for case in cases:
        caseid=case["fixture_id"]; folder=ROOT/"cache/runs"/phase/label/platform/caseid
        folder.parent.mkdir(parents=True,exist_ok=True)
        fixture=folder.parent/(caseid+"-input.json")
        write(fixture,native_input(case))
        argv=[sys.executable,str(workspace/"capture.py"),"--platform",platform,
              "--project",str(workspace/("reply/Reply" if platform=="android" else "alerttoast")),
              "--fixture",str(fixture),"--output",str(folder)]
        t=time.monotonic();started=dt.datetime.now(dt.timezone.utc).isoformat()
        with (folder.parent/(caseid+"-command.log")).open("w") as log:
            result=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
        record=dict(label=label,platform=platform,phase=phase,case_id=caseid,
                    started_at=started,elapsed_seconds=round(time.monotonic()-t,3),
                    exit_code=result.returncode)
        if result.returncode==0:
            subprocess.run([str(ROOT/"cache/ocr"),str(folder/"actual.png"),str(folder/"ocr.json")],check=True,stdout=subprocess.DEVNULL)
            obs=observe_android(folder,case) if platform=="android" else dict(build_status="passed",render_status="passed",measurements={},limitations=["Common iOS unit host has no runtime AX; pixels/OCR require independent review"])
            write(folder/"observation.json",obs)
            oracle=read(ROOT/"design-team/private/oracle.json")
            namespace={};exec(oracle["checker_python"],namespace)
            checks=case["assertions"] + oracle["pixel_measurement_checks"]
            write(folder/"automatic-checks.json",namespace["evaluate_checks"](checks,obs))
        else:
            write(folder/"infrastructure-error.json",record)
        records.append(record)
        print(json.dumps(record),flush=True)
    return records


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--phase",choices=["d0","final"],required=True)
    a=parser.parse_args();oracle=read(ROOT/"design-team/private/oracle.json")
    cases=[c for c in oracle["fixtures"] if a.phase=="final" or c["stage"]=="initial"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(lane,label,platform,a.phase,cases)
                 for label in ["unit-52dc59","unit-07b638"] for platform in ["android","ios"]]
        records=[r for future in concurrent.futures.as_completed(futures) for r in future.result()]
    write(ROOT/"cache/runs"/a.phase/"execution.json",records)


if __name__=="__main__":main()
