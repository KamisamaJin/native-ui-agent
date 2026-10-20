#!/usr/bin/env python3
"""Source-independent frozen evaluator. No candidate source is imported or run."""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json, math, re, struct, sys, zlib
from pathlib import Path

sys.dont_write_bytecode=True
PREP=Path(__file__).resolve().parent
BASE_PREP=PREP.parent
DESIGN=BASE_PREP.parent.parent
REPO=DESIGN.parents[2]
ENCODING=None
GEOMETRY_CALIBRATION=None
COMMON=DESIGN.parent / "contract.py"
EXPECTED_DESIGN_COMMITMENT="b4f8fe5d30edab8d5261f099e3ffc62f99591fbbf081c8c738c8d2c375ce72f7"
METHOD_MAP={"ios.xcui.tap":"xcui_tap","android.compose.OnClick":"compose_onclick","caller.replaceModel":"caller_fixture_update"}
OUTCOMES={"passed":"P","failed":"F","unassessed":"U"}
COMMON_OUTCOMES={"P":"PASS","F":"FAIL","U":"UNASSESSED"}
BUCKETS=("runtime_business","runtime_visual","runtime_integration","runtime_capability","input_member_integration","source_api")
COMMON_MODULE=None

def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def canonical(v): return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(",",":"))
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def value_digest(v): return hashlib.sha256(canonical(v).encode()).hexdigest()
def write(path,value):
    p=Path(path)
    if p.exists(): raise ValueError("Fresh output required: "+str(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def import_common():
    global COMMON_MODULE
    if COMMON_MODULE is None:
        pins=read(PREP/"dependencies.json")
        for f in pins["files"]:
            p=(REPO/f["path"]).resolve()
            if not p.is_relative_to(REPO.resolve()):raise ValueError("Pinned dependency outside relocated repository")
            if digest(p)!=f["sha256"]: raise ValueError("Frozen shared dependency changed: "+str(p))
        spec=importlib.util.spec_from_file_location("dispatch_common_contract",COMMON)
        COMMON_MODULE=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(COMMON_MODULE)
    return COMMON_MODULE

def verify_design():
    seal=read(DESIGN/"private/SEAL.json")
    if value_digest(seal["payload"])!=EXPECTED_DESIGN_COMMITMENT or seal["commitment_sha256"]!=EXPECTED_DESIGN_COMMITMENT:
        raise ValueError("Independent design commitment changed")
    for entry in seal["payload"]["files"]:
        p=DESIGN/entry["path"]
        if digest(p)!=entry["sha256"]: raise ValueError("Sealed design file changed: "+entry["path"])
    return seal

def normalize(phase):
    verify_design()
    if phase not in ("d0","final"): raise ValueError("Known phase required")
    expanded=read(DESIGN/"private/expanded-plan.json")
    oracle=read(DESIGN/"private/oracle.json")
    allowed={c["id"] for c in oracle["cases"] if phase=="final" or c["split"]=="initial"}
    rows=[]
    for family in ("runtime_rows","input_member_rows","source_api_rows"):
        for original in expanded[family]:
            if original.get("case") is not None and original["case"] not in allowed: continue
            r=copy.deepcopy(original)
            r["caseId"]=r.get("case") or "source"
            r["stateId"]=r.get("checkpoint") or "source"
            r["modelId"]=r.get("model")
            r["sourceOnly"]=bool(r["source_only"])
            r["original_expected_sha256"]=value_digest(original["expected"])
            r["original_row_sha256"]=value_digest(original)
            r["original_requested_method"]=r.get("requested_method")
            if family=="input_member_rows": r["denominator"]="input_member_integration"
            elif family=="source_api_rows": r["denominator"]="source_api"
            else:r["denominator"]="runtime_"+{"business":"business","visual":"visual","integration":"integration","capability":"capability"}[r["category"]]
            if r.get("trigger",{}).get("type") in ("activate","replaceModel"):
                requested=r.get("requested_method",r["trigger"].get("requested_method"))
                if requested is None and r["trigger"]["type"]=="activate":
                    requested=oracle["native_activation_routes"][r["platform"]]
                if requested not in METHOD_MAP:raise ValueError("Unrecognized frozen requested method")
                r["original_requested_method"]=requested
                r["required_method"]=METHOD_MAP[requested]
                r["trigger"]["method"]=r["required_method"]
            if value_digest(r["expected"])!=r["original_expected_sha256"]:raise ValueError("Representation adapter changed expected value")
            rows.append(r)
    if len({r["key"] for r in rows})!=len(rows):raise ValueError("Duplicate normalized key")
    counts={b:sum(r["denominator"]==b for r in rows) for b in BUCKETS}
    return {"version":1,"phase":phase,"design_commitment":EXPECTED_DESIGN_COMMITMENT,
            "cases":sorted(allowed),"method_map":METHOD_MAP,"rows":rows,"counts":counts,
            "required_keys":[r["key"] for r in rows],"expectation_changes":0}

def pointer(value,path):
    if path=="":return value
    if not isinstance(path,str) or not path.startswith("/"):raise ValueError("JSON pointer required")
    for token in path[1:].split("/"):
        token=token.replace("~1","/").replace("~0","~")
        value=value[int(token)] if isinstance(value,list) else value[token]
    return value

def artifact(root,ref):
    if not isinstance(ref,dict) or set(ref)-{"path","sha256","pointer"}:raise ValueError("Exact artifact reference required")
    if not isinstance(ref.get("path"),str) or not isinstance(ref.get("sha256"),str):raise ValueError("Artifact path/hash required")
    p=(root/ref["path"]).resolve()
    if not p.is_relative_to(root.resolve()) or not p.is_file() or digest(p)!=ref["sha256"]:
        raise ValueError("Artifact missing, out of capsule, or hash changed: "+str(p))
    return p

def json_artifact(root,ref):
    p=artifact(root,ref)
    v=read(p)
    return pointer(v,ref.get("pointer","")),{"path":ref["path"],"sha256":ref["sha256"]}

def ref_at(ref,path):
    return {"path":ref["path"],"sha256":ref["sha256"],"pointer":path}

def selector_value(value):
    if isinstance(value,str):return value
    if isinstance(value,dict) and isinstance(value.get("identifier"),str):return value["identifier"]
    return None

def dispatch_target_bound(row,mapping,observation):
    if row["trigger"]["type"]!="activate":return True,"explicit replacement"
    i=mapping.get("trigger_action_index")
    if type(i) is not int or not 0<=i<len(observation.get("steps",[])):return False,"no actual trigger step"
    expected=row["trigger"]["target"]["identifier"]
    permitted={f"/steps/{i}/{name}" for name in ("selector","target","query")}
    permitted|={f"/steps/{i}/dispatch/{name}" for name in ("selector","target","query")}
    explicit=mapping.get("dispatch_target_pointer")
    if explicit is not None and explicit not in permitted:return False,"selector locator is not a native dispatch field"
    pointers=[explicit] if explicit else sorted(permitted)
    values=[]
    for p in pointers:
        try:v=selector_value(pointer(observation,p))
        except (KeyError,IndexError,ValueError,TypeError):continue
        if v is not None:values.append(v)
    if not values:return False,"actual dispatch selector not retained"
    return all(v==expected for v in values),"exact actual requested selector" if all(v==expected for v in values) else "actual dispatch selector differs"

def atomic_gate(row,mapping,observation):
    common=import_common()
    gate=common.stimulus_gate(row,mapping,observation)
    if gate["required"] and gate["established"]:
        ok,reason=dispatch_target_bound(row,mapping,observation)
        gate["requested_target_established"]=ok
        if not ok:gate["established"]=False;gate["reason"]=reason
    return gate

def strict_equal(a,b):
    if isinstance(a,bool)!=isinstance(b,bool):return False
    return a==b

def model_equal(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,dict):return set(a)==set(b) and all(model_equal(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(model_equal(x,y) for x,y in zip(a,b))
    return a==b

def encoding_module():
    global ENCODING
    if ENCODING is None:
        spec=importlib.util.spec_from_file_location("frozen_native_encoding_v2",PREP/"native_encoding.py")
        ENCODING=importlib.util.module_from_spec(spec);spec.loader.exec_module(ENCODING)
    return ENCODING

def geometry_calibration_module():
    global GEOMETRY_CALIBRATION
    if GEOMETRY_CALIBRATION is None:
        spec=importlib.util.spec_from_file_location("frozen_native_geometry_v3",PREP/"geometry_calibration.py")
        GEOMETRY_CALIBRATION=importlib.util.module_from_spec(spec);spec.loader.exec_module(GEOMETRY_CALIBRATION)
    return GEOMETRY_CALIBRATION


def checkpoint_state(row,mapping,observation):
    state={"id":mapping.get("state_id",row["stateId"]),"input_index":mapping.get("input_index"),
           "coverage":"full_content" if row.get("full_content") else "target"}
    if type(state["input_index"]) is not int or state["input_index"]<0:return [],False,"mapping lacks integer input_index",None
    if row["trigger"]["type"]!="initial":
        index=mapping.get("state_action_index",mapping.get("after_action",mapping.get("trigger_action_index")))
        if "state_action_index" in mapping and "after_action" in mapping and mapping["state_action_index"]!=mapping["after_action"]:
            return [],False,"conflicting state action indices",None
        if type(index) is not int:return [],False,"mapping lacks state action index",None
        state["after_action"]=index
    found,complete,why,capture=import_common().checks.state_evidence(observation,state)
    # Bind every target/full frame to the original stimulus epoch, including event revision.
    if found and row["trigger"]["type"]!="initial":
        i=mapping.get("trigger_action_index")
        if type(i) is not int or not 0<=i<len(observation.get("steps",[])):
            return [],False,"missing original trigger",capture
        if any(s.get("binding")!=observation["steps"][i].get("binding_after") for _,s in found):
            return [],False,"state frame differs from original dispatch binding",capture
    return found,complete,why,capture

def geometry(snapshot,node,platform):
    if platform=="ios" and isinstance(node.get("frame"),dict):
        f=node["frame"]
        if all(type(f.get(k)) in (int,float) for k in ("x","y","width","height")):return f
    b=node.get("bounds_dp")
    if platform=="android" and isinstance(b,list) and len(b)==4 and all(type(v) in (int,float) for v in b):
        return dict(x=b[0],y=b[1],width=b[2]-b[0],height=b[3]-b[1])
    f=node.get("frame_dp") if platform=="android" else None
    if isinstance(f,dict) and all(type(f.get(k)) in (int,float) for k in ("x","y","width","height")):return f
    return None

def present_native_values(row,found,complete):
    values=[];locators=[];field=row["expected"].get("field")
    for si,snap in found:
        resolved=import_common().checks.resolve(snap,row["target"],row["platform"])
        facts=resolved["facts"];semantic=resolved.get("semantic",{});control=resolved.get("control",{})
        visible=semantic.get("intersects_viewport") is True
        if row["method"]=="native_control":
            if field=="exists":
                if facts.get("unique") and visible:v=True
                elif not facts.get("present") and complete:v=False
                elif facts.get("present") and not facts.get("unique"):continue
                else:continue
            elif not visible or resolved.get("resolution")!="unique_native_control":continue
            elif field=="checked":
                v=facts.get("value")
                if not isinstance(v,bool):continue
            elif field=="selected":
                native_selected=[n.get("selected") for n in (semantic,control) if isinstance(n.get("selected"),bool)]
                if not native_selected:continue
                v=any(native_selected)
            elif field=="enabled":
                v=facts.get("enabled")
                if not isinstance(v,bool):continue
            else:continue
        elif row["method"]=="native_text":
            if not visible or not facts.get("unique"):continue
            candidates=[semantic.get(k) for k in ("label","text") if isinstance(semantic.get(k),str)]
            if not candidates:continue
            # Label is authoritative, or raw text only when label is absent. No joins or fuzzy match.
            v=candidates[0]
        elif row["method"]=="native_bounds":
            if not visible or not facts.get("unique"):continue
            f=geometry(snap,semantic,row["platform"]) or geometry(snap,control,row["platform"])
            if not f:continue
            if field in ("width","height"):v=f[field]
            elif field=="viewport_x_min":
                vp=snap.get("viewport",{})
                if row["platform"]=="ios" and type(vp.get("x")) in (int,float):v=f["x"]-vp["x"]
                elif row["platform"]=="android":v=f["x"]
                else:continue
            else:continue
        else:continue
        values.append(v);locators.append({"snapshot":si,"pointer":f"/snapshots/{si}/nodes","target":row["target"]})
    return values,locators

def match_value(value,expected):
    if expected.get("equals") is not None:
        goal=expected["equals"];tol=expected.get("tolerance",0)
        if type(goal) in (int,float) and type(value) in (int,float):return abs(value-goal)<=tol
        return strict_equal(value,goal)
    if expected.get("minimum") is not None:
        return type(value) in (int,float) and value>=expected["minimum"]
    if "rgb" in expected:
        return isinstance(value,list) and len(value)==3 and max(abs(a-b) for a,b in zip(value,bytes.fromhex(expected["rgb"][1:])))<=expected["maximum_per_channel_error"]
    return None

def collapse_values(row,values):
    if not values:return "U",None,"native field unavailable or target not observed"
    results=[match_value(v,row["expected"]) for v in values]
    if any(v is None for v in results):return "U",values,"no frozen matcher for this field"
    if all(results):return "P",values,"exact typed native comparison"
    if not any(results):return "F",values,"typed native contradiction"
    return "U",values,"contradictory facts within immutable epoch"

def interval_overlap(found):
    intervals=[];heights=[]
    for _,s in found:
        runtime=s.get("runtime",{});f=runtime.get("content_frame");vp=s.get("viewport")
        if f and vp:
            h=f["height"];start=max(0,vp["y"]-f["y"]);end=min(h,vp["y"]-f["y"]+vp["height"])
        elif all(k in s for k in ("scroll_offset_dp","scroll_max_dp","viewport_height_dp")):
            start=s["scroll_offset_dp"];h=s["scroll_max_dp"]+s["viewport_height_dp"];end=min(h,start+s["viewport_height_dp"])
        else:continue
        intervals.append((start,end));heights.append(h)
    if not intervals:return False
    if max(heights)-min(heights)>1:return False
    frontier=0;first=True
    for start,end in sorted(set(intervals)):
        if end<=frontier:continue
        if first:
            if start>1:return False
            first=False
        elif frontier-start<24:return False
        frontier=max(frontier,end)
    return frontier>=max(heights)-1

def native_capability(row,found):
    field=row["expected"].get("field");values=[];refs=[]
    for si,s in found:
        binding=s.get("binding",{})
        for fi,f in enumerate(s.get("native_facts",[])):
            if f.get("kind")!="native_runtime_fact" or f.get("target")!=row["target"] or f.get("field")!=field:continue
            origin=f.get("origin",{})
            if origin.get("method")!=row["capability"] or origin.get("platform")!=row["platform"] or origin.get("binding")!=binding:continue
            if origin.get("source_kind")!="runtime_inspection" or "value" not in f:continue
            if not origin.get("native_probe"):continue
            values.append(f["value"]);refs.append({"snapshot":si,"pointer":f"/snapshots/{si}/native_facts/{fi}"})
    if field is None:
        # Applied accessibility scaling is one structured native fact, not inferred from input.
        for si,s in found:
            for fi,f in enumerate(s.get("native_facts",[])):
                if f.get("kind")=="native_runtime_fact" and f.get("field")=="applied_accessibility_scaling" and f.get("target")==row["target"] and f.get("origin",{}).get("binding")==s.get("binding") and f.get("origin",{}).get("method")==row["capability"] and f.get("origin",{}).get("source_kind")=="runtime_inspection" and f.get("origin",{}).get("platform")==row["platform"] and f.get("origin",{}).get("native_probe"):
                    val=f.get("value",{})
                    expected=row["expected"]["ios_dynamic_type" if row["platform"]=="ios" else "android_font_scale"]
                    actual=val.get("dynamic_type" if row["platform"]=="ios" else "font_scale")
                    if actual is not None:values.append(actual);refs.append({"snapshot":si,"pointer":f"/snapshots/{si}/native_facts/{fi}"})
        if values:
            results=[strict_equal(v,expected) for v in values]
            if all(results):return "P",values,"direct native scaling fact",refs
            if not any(results):return "F",values,"direct native scaling contradiction",refs
        return "U",None,"native scaling field unavailable",[]
    outcome,actual,reason=collapse_values(row,values)
    return outcome,actual,reason,refs

def read_png(path):
    data=Path(path).read_bytes()
    if data[:8]!=b"\x89PNG\r\n\x1a\n":raise ValueError("Original PNG required for measured pixels")
    pos=8;idat=b"";palette=None;trans=None;header=None
    while pos<len(data):
        length=struct.unpack(">I",data[pos:pos+4])[0];kind=data[pos+4:pos+8];body=data[pos+8:pos+8+length];pos+=12+length
        if kind==b"IHDR":header=struct.unpack(">IIBBBBB",body)
        elif kind==b"IDAT":idat+=body
        elif kind==b"PLTE":palette=[tuple(body[i:i+3]) for i in range(0,len(body),3)]
        elif kind==b"tRNS":trans=body
        elif kind==b"IEND":break
    w,h,depth,color,compression,filtration,interlace=header
    channels={0:1,2:3,3:1,4:2,6:4}.get(color)
    if depth!=8 or not channels or interlace!=0:raise ValueError("PNG mode unsupported; leave measured row U")
    raw=zlib.decompress(idat);stride=w*channels;previous=[0]*stride;rows=[];cursor=0
    def paeth(a,b,c):
        p=a+b-c;pa,pb,pc=abs(p-a),abs(p-b),abs(p-c)
        return a if pa<=pb and pa<=pc else b if pb<=pc else c
    for y in range(h):
        filter_type=raw[cursor];cursor+=1;line=list(raw[cursor:cursor+stride]);cursor+=stride
        for x in range(stride):
            left=line[x-channels] if x>=channels else 0;up=previous[x];upper_left=previous[x-channels] if x>=channels else 0
            if filter_type==1:line[x]=(line[x]+left)&255
            elif filter_type==2:line[x]=(line[x]+up)&255
            elif filter_type==3:line[x]=(line[x]+((left+up)//2))&255
            elif filter_type==4:line[x]=(line[x]+paeth(left,up,upper_left))&255
            elif filter_type!=0:raise ValueError("Unknown PNG filter")
        rgb=[]
        for x in range(w):
            v=line[x*channels:(x+1)*channels]
            if color==0:pixel=(v[0],)*3+(255,)
            elif color==2:pixel=tuple(v)+(255,)
            elif color==3:pixel=palette[v[0]]+((trans[v[0]] if trans and v[0]<len(trans) else 255),)
            elif color==4:pixel=(v[0],)*3+(v[1],)
            else:pixel=tuple(v)
            rgb.append(pixel)
        rows.append(rgb);previous=line
    return w,h,rows

def visual_decision(row,decision,context,root):
    if decision is None:return "U",None,"manual visual measurement not supplied",[]
    required={"key","outcome","method","reason","snapshot_indices","evidence","observation_sha256"}
    if not required<=set(decision) or decision["key"]!=row["key"]:raise ValueError("Malformed visual decision")
    if decision["outcome"] not in ("P","F","U"):raise ValueError("Unknown visual outcome")
    if decision["observation_sha256"]!=context["observation_ref"]["sha256"]:raise ValueError("Manual visual decision binds wrong observation")
    if row["method"] not in ("pixels","visual"):raise ValueError("Manual visuals cannot establish native facts")
    if decision["method"]!=row["method"]:raise ValueError("Manual method differs from frozen method")
    if not decision["reason"]:raise ValueError("Manual rationale required")
    allowed={i for i,_ in context["found"]};indices=decision["snapshot_indices"]
    if not indices or any(type(i) is not int or i not in allowed for i in indices):raise ValueError("Manual screenshots outside named state")
    refs=[]
    for ref in decision["evidence"]:artifact(root,ref);refs.append(ref)
    expected_images={context["observation"]["snapshots"][i]["screenshot"] for i in indices}
    declared_paths={ref["path"] for ref in refs}
    obs_parent=Path(context["observation_ref"]["path"]).parent
    expected_paths={str(obs_parent/p) for p in expected_images}
    if not expected_paths<=declared_paths:raise ValueError("Manual decision lacks actual original state image")
    if decision["outcome"]=="U":return "U",None,decision["reason"],refs
    if not decision.get("target_region") or not decision.get("witness"):raise ValueError("Target region and visual witness required")
    if row.get("full_content") and decision["outcome"]=="P" and not context["complete"]:
        return "U",None,"full-content visual pass lacks native overlapping coverage",refs
    if row["method"]=="pixels":
        measurement=decision.get("measurement",{})
        if "rgb" in row["expected"]:
            patches=measurement.get("patches",[])
            if len(patches)<3:raise ValueError("Three independent native pixel patches required")
            measured=[]
            for patch in patches:
                if patch.get("snapshot") not in indices:raise ValueError("Patch outside declared state images")
                snap=context["observation"]["snapshots"][patch["snapshot"]]
                image_ref=next((r for r in refs if r["path"]==str(obs_parent/snap["screenshot"])),None)
                if image_ref is None:raise ValueError("Patch image not hash-bound")
                w,h,pixels=read_png(artifact(root,image_ref))
                x,y,size=patch["x"],patch["y"],patch["size"]
                if any(type(v) is not int for v in (x,y,size)) or size<1 or x<0 or y<0 or x+size>w or y+size>h:raise ValueError("Invalid native pixel patch")
                if row["expected"]["part"] in ("fill","container_fill") and size<3:raise ValueError("Fill patches need 3x3 native pixels")
                target_box=decision["target_region"].get(str(patch["snapshot"]))
                if not target_box or len(target_box)!=4 or not(target_box[0]<=x and target_box[1]<=y and x+size<=target_box[2] and y+size<=target_box[3]):raise ValueError("Patch lies outside annotated target region")
                samples=[pixels[j][i] for j in range(y,y+size) for i in range(x,x+size)]
                if any(p[3]!=255 for p in samples):return "U",None,"nonopaque raw pixels cannot establish opaque palette",refs
                med=[sorted(p[c] for p in samples)[len(samples)//2] for c in range(3)]
                measured.append(med)
            checks=[match_value(v,row["expected"]) for v in measured]
            result="P" if all(checks) else "F" if not any(checks) else "U"
            if result!=decision["outcome"]:raise ValueError("Manual color outcome disagrees with actual frozen pixel matcher")
            return result,measured,decision["reason"],refs
        if row["expected"].get("part") in ("corner_radius","border_width"):
            segments=measurement.get("segments",[])
            if not segments:raise ValueError("Original pixel measurement segments required")
            values=[]
            for s in segments:
                if s.get("snapshot") not in indices:raise ValueError("Measurement outside state")
                scale=s.get("native_pixels_per_logical_unit")
                if type(scale) not in (int,float) or scale<=0:raise ValueError("Native screenshot scale required")
                si=s["snapshot"];snap=context["observation"]["snapshots"][si]
                image_ref=next(r for r in refs if r["path"]==str(obs_parent/snap["screenshot"]))
                image_path=artifact(root,image_ref)
                geometry_format=geometry_calibration_module()
                try:
                    calibration=geometry_format.calibrate_png(snap,row["platform"],image_path)
                except geometry_format.NativeCalibrationUnavailable as exc:
                    return "U",None,"original native PNG calibration unavailable: "+str(exc),refs
                geometry_format.validate_measurement_scale(calibration,scale)
                a,b=s["a"],s["b"];length=math.hypot(a[0]-b[0],a[1]-b[1])
                if length<=0:raise ValueError("Nonzero measured segment required")
                values.append(length/scale)
            outcome,actual,why=collapse_values(row,values)
            if outcome!=decision["outcome"]:raise ValueError("Manual geometry outcome contradicts measured segments")
            return outcome,actual,decision["reason"],refs
        return "U",None,"no frozen pixel measurement rule",refs
    if decision["outcome"]=="F" and not decision.get("local_counterexample",False) and not context["complete"]:
        return "U",None,"global visual failure lacks complete evidence",refs
    return decision["outcome"],{"witness":decision["witness"],"target_region":decision["target_region"]},decision["reason"],refs

def load_context(entry,root,row,oracle):
    if entry is None:return {"valid":False,"reason":"platform/case observation omitted"}
    observation,obsref=json_artifact(root,entry["observation"])
    mappings,mapref=json_artifact(root,entry["mapping"])
    mapping=mappings.get(row["stateId"],{})
    if not isinstance(mapping,dict):raise ValueError("Checkpoint mapping must be an object")
    fixture,fixref=json_artifact(root,entry["fixture"])
    model_pointer=entry.get("model_pointers",{}).get(row["modelId"])
    if model_pointer is None:return {"valid":False,"reason":"model input pointer omitted","observation":observation,"mapping":mapping}
    try:actual_model=pointer(fixture,model_pointer)
    except (KeyError,ValueError,TypeError,IndexError):return {"valid":False,"reason":"model input pointer unavailable","observation":observation,"mapping":mapping}
    base=dict(observation=observation,mapping=mapping,observation_ref=obsref,fixture_model=actual_model,
              fixture_artifact_sha256=fixref["sha256"],
              provenance=[ref_at(fixref,model_pointer),ref_at(mapref,"/"+row["stateId"])])
    expected=next(c for c in oracle["cases"] if c["id"]==row["caseId"])["models"][row["modelId"]]
    if not model_equal(actual_model,expected):return dict(base,valid=False,reason="fixture model differs from sealed model")
    native=encoding_module()
    try:
        current_hash,encoding_proof=native.native_model_hash(actual_model,row["platform"])
    except native.NativeEncodingUnavailable as exc:
        return dict(base,valid=False,reason="native model encoding unavailable: "+str(exc))
    base["native_input_provenance"]=dict(encoding_proof,current_model_sha256=current_hash,
        fixture_artifact=fixref,model_pointer=model_pointer,fixture_file_sha256=fixref["sha256"])
    expected_index=0 if row["modelId"]=="initial" else 1
    if mapping.get("input_index")!=expected_index or type(mapping.get("input_index")) is not int:
        return dict(base,valid=False,reason="checkpoint mapping differs from frozen producer model index")
    found,complete,why,capture=checkpoint_state(row,mapping,observation)
    # Frozen producers bind the CURRENT MODEL encoding, never the complete fixture file bytes.
    if any(s.get("binding",{}).get("input_sha256")!=current_hash for _,s in found):
        return dict(base,valid=False,reason="native snapshot not bound to exact current-model serialization")
    if row["trigger"]["type"]!="initial":
        i=mapping.get("trigger_action_index")
        if type(i) is int and 0<=i<len(observation.get("steps",[])):
            step=observation["steps"][i]
            after=step.get("binding_after",{})
            if after.get("input_sha256")!=current_hash:
                return dict(base,valid=False,reason="native dispatch not bound to exact current-model serialization")
            if after.get("fixture_index",after.get("input_index"))!=expected_index:
                return dict(base,valid=False,reason="native dispatch bound to another model index")
            before=step.get("dispatch",{}).get("binding_before",{})
            before_hash=current_hash
            if row["trigger"]["type"]=="replaceModel":
                before_pointer=entry.get("model_pointers",{}).get("initial")
                try:
                    before_model=pointer(fixture,before_pointer)
                    before_hash,_=native.native_model_hash(before_model,row["platform"])
                except (native.NativeEncodingUnavailable,KeyError,ValueError,TypeError,IndexError):
                    return dict(base,valid=False,reason="previous native model encoding unavailable")
                expected_before=next(c for c in oracle["cases"] if c["id"]==row["caseId"])["models"]["initial"]
                if not model_equal(before_model,expected_before):
                    return dict(base,valid=False,reason="previous fixture differs from sealed initial model")
                base["native_input_provenance"]["previous_model_sha256"]=before_hash
            if before.get("input_sha256")!=before_hash:
                return dict(base,valid=False,reason="native dispatch before-binding differs from correct previous/current model serialization")
    return dict(base,valid=True,reason=why,found=found,complete=complete and interval_overlap(found),capture=capture)

def source_decision(row,review,root,source_files):
    decision=review.get(row["key"])
    if decision is None:return "U",None,"source/API review omitted",[]
    if decision.get("outcome") not in ("P","F","U") or decision.get("method")!="source_api":raise ValueError("Invalid source review")
    if decision.get("expected_sha256")!=row["original_expected_sha256"]:raise ValueError("Source review changes frozen expected requirement")
    if decision["outcome"]=="U":return "U",None,decision.get("reason","unavailable source evidence"),[]
    if not decision.get("reason") or not decision.get("citations"):raise ValueError("Source/API P/F requires scoped citations")
    refs=[]
    for cite in decision["citations"]:
        ref=cite["artifact"]
        if (ref["path"],ref["sha256"]) not in source_files:raise ValueError("Source citation outside anonymous source capsule")
        p=artifact(root,ref);lines=p.read_text(encoding="utf-8").splitlines()
        start,end=cite["line_start"],cite["line_end"]
        if type(start) is not int or type(end) is not int or start<1 or end<start or end>len(lines):raise ValueError("Invalid source lines")
        quote="\n".join(lines[start-1:end])
        if quote!=cite.get("quote"):raise ValueError("Source quote differs from sealed source bytes")
        refs.append({"path":ref["path"],"sha256":ref["sha256"],"line_start":start,"line_end":end})
    return decision["outcome"],decision.get("fact"),decision["reason"],refs

def audit_report(report,plan,contexts):
    expected=set(plan["required_keys"])
    actual=[r["key"] for r in report["rows"]]
    if set(actual)!=expected or len(actual)!=len(set(actual)):raise ValueError("Grade omission, duplicate, or unplanned row")
    originals={r["key"]:r for r in plan["rows"]}
    for grade in report["rows"]:
        row=originals[grade["key"]]
        if grade["outcome"] not in ("P","F","U") or grade["denominator"]!=row["denominator"]:raise ValueError("Invalid grade outcome/bucket")
        if grade["expected_sha256"]!=row["original_expected_sha256"]:raise ValueError("Grade expectation substitution")
        if grade["outcome"]!="U" and not grade.get("evidence"):raise ValueError("P/F lacks explicit raw evidence")
        if not row["sourceOnly"]:
            context=contexts.get((row["platform"],row["caseId"],row["stateId"]),{})
            observation=context.get("observation",{});mapping=context.get("mapping",{})
            gate=atomic_gate(row,mapping,observation)
            if grade["outcome"]!="U" and gate["required"] and not gate["established"]:raise ValueError("P/F without requested native dispatch binding")
            import_common().validate_precondition_outcome(row,{"outcome":COMMON_OUTCOMES[grade["outcome"]]},mapping,observation)
            if grade["outcome"]!="U" and not context.get("valid"):raise ValueError("Runtime P/F lacks sealed fixture provenance")
            if grade["outcome"]!="U" and row["category"]=="capability":
                actual_outcome,_,_,_=native_capability(row,context.get("found",[]))
                if grade["outcome"]!=actual_outcome:raise ValueError("Capability grade lacks actual native fact")
            if grade["outcome"]!="U" and row["method"] in ("native_control","native_text","native_bounds") and row["category"]!="capability":
                values,_=present_native_values(row,context.get("found",[]),context.get("complete",False))
                actual_outcome,_,_=collapse_values(row,values)
                if grade["outcome"]!=actual_outcome:raise ValueError("Native grade differs from raw native facts")
    return True

def summarize(rows):
    return {b:{"required":sum(r["denominator"]==b for r in rows),
               **{o:sum(r["denominator"]==b and r["outcome"]==o for r in rows) for o in ("P","F","U")}}
            for b in BUCKETS}

def grade(manifest_path,output):
    root=Path(manifest_path).resolve().parent;manifest=read(manifest_path)
    if manifest.get("version")!=1 or manifest.get("phase") not in ("d0","final"):raise ValueError("Known frozen grade manifest required")
    phase=manifest["phase"];plan=read(BASE_PREP/("normalized-"+phase+".json"))
    if value_digest(plan)!=value_digest(normalize(phase)):raise ValueError("Frozen normalized plan changed")
    entries={}
    for e in manifest.get("observations",[]):
        key=(e["platform"],e["case"])
        if key in entries or e["platform"] not in ("ios","android") or e["case"] not in plan["cases"]:raise ValueError("Duplicate or phase-forbidden observation")
        entries[key]=e
    def decisions(name):
        if name not in manifest:return {}
        value,_=json_artifact(root,manifest[name])
        rows=value["decisions"]
        if len({r["key"] for r in rows})!=len(rows):raise ValueError("Duplicate manual decision")
        if set(r["key"] for r in rows)-set(plan["required_keys"]):raise ValueError("Unplanned manual decision")
        return {r["key"]:r for r in rows}
    visual=decisions("visual_review");source=decisions("source_review")
    source_files=set()
    for ref in manifest.get("source_files",[]):artifact(root,ref);source_files.add((ref["path"],ref["sha256"]))
    oracle=read(DESIGN/"private/oracle.json");contexts={};rows=[]
    for row in plan["rows"]:
        outcome="U";actual=None;reason="required evidence not supplied";evidence=[];gate={"required":not row["sourceOnly"] and (row["method"]=="callback" or row.get("requires_stimulus") is True),"established":False if not row["sourceOnly"] and (row["method"]=="callback" or row.get("requires_stimulus") is True) else True}
        if row["denominator"]=="source_api":
            outcome,actual,reason,evidence=source_decision(row,source,root,source_files)
        else:
            ck=(row["platform"],row["caseId"],row["stateId"])
            if ck not in contexts:contexts[ck]=load_context(entries.get(ck[:2]),root,row,oracle)
            context=contexts[ck]
            if row["denominator"]=="input_member_integration":
                if "fixture_model" in context:
                    member=row["expected"]["member"];actual=context["fixture_model"].get(member)
                    outcome="P" if strict_equal(actual,row["expected"]["value"]) else "F"
                    reason="exact captured fixture member only; no native behavior claim";evidence=context.get("provenance",[])
                    if not evidence:outcome="U";reason="fixture member has no immutable locator"
                else:reason=context.get("reason",reason)
            elif not context.get("valid"):reason=context.get("reason",reason)
            else:
                gate=atomic_gate(row,context["mapping"],context["observation"])
                if gate["required"] and not gate["established"]:reason=gate.get("reason",gate.get("verdict",{}).get("reason","native dispatch not established"))
                elif row["method"]=="callback":
                    outcome=OUTCOMES[gate["verdict"]["status"]];actual=gate["verdict"].get("interval_facts");reason=gate["verdict"]["reason"]
                    i=context["mapping"]["trigger_action_index"]
                    evidence=[ref_at(context["observation_ref"],f"/steps/{i}")]
                elif row["category"]=="capability":
                    outcome,actual,reason,refs=native_capability(row,context["found"])
                    evidence=[ref_at(context["observation_ref"],r["pointer"]) for r in refs]
                elif row["id"]=="layout.fullContentCoverage":
                    if context["complete"]:
                        outcome="P";actual="native interval union complete with >=24 overlap";reason="recomputed native coverage, not producer complete flag"
                        evidence=[ref_at(context["observation_ref"],"/state_captures"),ref_at(context["observation_ref"],"/snapshots")]
                    else:reason="required native full-content overlapping coverage unavailable"
                elif row["method"] in ("native_control","native_text","native_bounds"):
                    values,refs=present_native_values(row,context["found"],context["complete"])
                    outcome,actual,reason=collapse_values(row,values)
                    evidence=[ref_at(context["observation_ref"],r["pointer"]) for r in refs]
                elif row["method"] in ("pixels","visual"):
                    outcome,actual,reason,evidence=visual_decision(row,visual.get(row["key"]),context,root)
                else:reason="no frozen matcher; requirement retained U"
        rows.append({"key":row["key"],"platform":row["platform"],"case":row["caseId"],"checkpoint":row["stateId"],
                     "category":row["category"],"denominator":row["denominator"],"method":row["method"],
                     "outcome":outcome,"expected_sha256":row["original_expected_sha256"],"actual":actual,
                     "reason":reason,"evidence":evidence,"stimulus_gate":gate})
    report={"version":1,"anonymous_id":manifest.get("anonymous_id"),"phase":phase,
            "design_commitment":EXPECTED_DESIGN_COMMITMENT,"normalized_plan_sha256":digest(BASE_PREP/("normalized-"+phase+".json")),
            "manifest_sha256":digest(manifest_path),"rows":rows,"counts":summarize(rows),
            "evaluator_adapter":"v3",
            "input_encoding_provenance":[{"platform":p,"case":c,"checkpoint":cp,**ctx["native_input_provenance"]} for (p,c,cp),ctx in contexts.items() if "native_input_provenance" in ctx],
            "platform_counts":{p:summarize([r for r in rows if r["platform"]==p]) for p in ("ios","android")},
            "business_scopes":{
                "primary_post_stimulus":{"required":sum(r["denominator"]=="runtime_business" and r["stimulus_gate"].get("required") for r in rows),
                    "stimulus_established":sum(r["denominator"]=="runtime_business" and r["stimulus_gate"].get("required") and r["stimulus_gate"].get("established") for r in rows),
                    **{o:sum(r["denominator"]=="runtime_business" and r["stimulus_gate"].get("required") and r["outcome"]==o for r in rows) for o in ("P","F","U")}},
                "initial_native_descriptive":{o:sum(r["denominator"]=="runtime_business" and r["checkpoint"]=="initial" and r["outcome"]==o for r in rows) for o in ("P","F","U")}},
            "claim":"All frozen rows retained. Primary business misses are confirmed FAIL only after successful requested stimulus. Initial business rows are wider descriptive evidence. Runtime, input provenance, source API, and native capability denominators remain separate."}
    audit_report(report,plan,contexts)
    write(output,report)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="command",required=True)
    n=sub.add_parser("normalize");n.add_argument("--phase",choices=["d0","final"],required=True);n.add_argument("--output",type=Path,required=True)
    g=sub.add_parser("grade");g.add_argument("--manifest",type=Path,required=True);g.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.command=="normalize":write(a.output,normalize(a.phase))
    else:
        result=grade(a.manifest,a.output)
        print(json.dumps({"phase":result["phase"],"counts":result["counts"]}))
if __name__=="__main__":main()
