#!/usr/bin/env python3
"""Synthetic current-model encoding, provenance, replacement and relocation controls."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,base64,copy,tempfile,shutil,importlib.util,datetime
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("frozen_v2_evaluator_controls",ROOT/"evaluator.py")
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
native=e.encoding_module()
vectors=e.read(ROOT/"encoding-vectors.json")["vectors"]
byid={v["id"]:v["model"] for v in vectors}
results=[]
def test(name,fn):
    fn();results.append({"id":name,"status":"PASS"})
def reject_encoding(model,platform):
    try:native.native_model_hash(model,platform)
    except native.NativeEncodingUnavailable:return
    raise AssertionError("Unestablished encoding was accepted")
def equal_probe(platform,filename,vector):
    outputs={r["id"]:base64.b64decode(r["utf8_base64"]) for r in e.read(ROOT/filename)["results"]}
    digest,proof=native.native_model_hash(vector["model"],platform)
    assert digest==hashlib.sha256(outputs[vector["id"]]).hexdigest()
    assert proof["encoded_byte_count"]==len(outputs[vector["id"]])
for platform,filename in (("ios","foundation-probe-output.json"),("android","kotlin-probe-output.json")):
    for vector in vectors:test("native-probe-exact-"+platform+"-"+vector["id"],lambda p=platform,f=filename,v=vector:equal_probe(p,f,v))

def ordering(platform,equal):
    a,_=native.native_model_hash(byid["replacement_before"],platform)
    b,_=native.native_model_hash(byid["same_values_reordered"],platform)
    assert (a==b)==equal
test("Foundation-sorts-reordered-model",lambda:ordering("ios",True))
test("Kotlin-preserves-reordered-model",lambda:ordering("android",False))
for p in ("ios","android"):
    def changed(platform=p):
        a,_=native.native_model_hash(byid["replacement_before"],platform)
        b,_=native.native_model_hash(byid["replacement_after"],platform)
        assert a!=b
    test("replacement-changes-native-model-hash-"+p,changed)

for id,value in [
 ("nested",{"title":{"nested":True}}),("array",{"title":["value"]}),
 ("float",{"bedCount":2.0}),("null",{"title":None}),
 ("non-ASCII-key",{"名前":"value"}),("out-of-range-int",{"bedCount":2**40}),
 ("lone-surrogate",{"title":"\ud800"})]:
    test("unknown-domain-stays-U-"+id,lambda v=value:reject_encoding(v,"ios"))
test("unknown-platform-stays-U",lambda:reject_encoding({"title":"value"},"unknown"))
test("typed-equality-rejects-Bool-as-Int",lambda:(_ for _ in ()).throw(AssertionError()) if e.model_equal({"bedCount":True},{"bedCount":1}) else None)
test("typed-equality-rejects-Float-as-Int",lambda:(_ for _ in ()).throw(AssertionError()) if e.model_equal({"bedCount":2.0},{"bedCount":2}) else None)

def synthetic_context(platform,replacement=False,corrupt=None):
    with tempfile.TemporaryDirectory(prefix="encoding-provenance-",dir=ROOT) as tmp:
        root=Path(tmp)
        before=copy.deepcopy(byid["replacement_before"]);after=copy.deepcopy(byid["replacement_after"])
        fixture={"width":390,"height":600,"initial":before,"updates":[after],"actions":[]}
        def save(name,value):
            p=root/name;p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
            return {"path":name,"sha256":e.digest(p)}
        fixture_ref=save("fixtures.json",fixture)
        hash_before,_=native.native_model_hash(before,platform);hash_after,_=native.native_model_hash(after,platform)
        current=hash_after if replacement else hash_before
        bind_before={"pid":321,"instance":"synthetic-encoding","fixture_index":0,"input_sha256":hash_before,"event_revision":0}
        bind_after=dict(bind_before,fixture_index=1 if replacement else 0,input_sha256=current)
        if corrupt=="whole-file":bind_after["input_sha256"]=fixture_ref["sha256"]
        elif corrupt=="previous":bind_before["input_sha256"]="not-previous-model"
        elif corrupt=="wrong-order":
            bind_after["input_sha256"]=hashlib.sha256(json.dumps(after if replacement else before,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
        elif corrupt=="unescaped-ios":
            bind_after["input_sha256"]=hashlib.sha256(json.dumps(after if replacement else before,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
        state="replaced" if replacement else "initial"
        snapshot={"state_id":state,"binding":bind_after,"capture_consistent":True,
                  "viewport":{"x":0,"y":0,"width":390,"height":600},
                  "runtime":{"content_frame":{"x":0,"y":0,"width":390,"height":600}},
                  "nodes":[]}
        capture={"state_id":state,"binding":bind_after,"snapshot_indices":[0],
                 "top_reached":True,"bottom_reached":True,"stable_binding":True}
        mapping={"state_id":state,"input_index":1 if replacement else 0}
        steps=[]
        if replacement:
            capture["after_action"]=0
            mapping.update(trigger_action_index=0,state_action_index=0,after_action=0)
            steps=[{"outcome":"updated","callback_delta":[],"binding_after":bind_after,"state_id":state,"snapshot":0,
              "dispatch":{"attempted":True,"succeeded":True,"method":"caller_fixture_update","stimulus":"caller_update",
                "binding_before":bind_before,"event_start":0,"event_end":0}}]
        observation={"steps":steps,"snapshots":[snapshot],"state_captures":[capture]}
        obs_ref=save("observation.json",observation);map_ref=save("mapping.json",{state:mapping})
        entry={"platform":platform,"case":"SYN","observation":obs_ref,"mapping":map_ref,"fixture":fixture_ref,
               "model_pointers":{"initial":"/initial","replacement":"/updates/0"}}
        row={"platform":platform,"caseId":"SYN","stateId":state,"modelId":"replacement" if replacement else "initial",
             "full_content":True,"sourceOnly":False,"source_only":False,"requires_stimulus":replacement,
             "method":"callback" if replacement else "native_text","expected":[] if replacement else {"equals":"generic"},
             "trigger":{"type":"replaceModel","method":"caller_fixture_update"} if replacement else {"type":"initial"}}
        if replacement:row["required_method"]="caller_fixture_update"
        oracle={"cases":[{"id":"SYN","models":{"initial":before,"replacement":after}}]}
        context=e.load_context(entry,root,row,oracle)
        if corrupt:
            assert context["valid"] is False
            assert "fixture_model" in context and context["provenance"]
            # Input facts remain separately visible; they never override the runtime U.
        else:
            assert context["valid"] is True,context.get("reason")
            proof=context["native_input_provenance"]
            assert proof["current_model_sha256"]==current
            assert proof["fixture_file_sha256"]==fixture_ref["sha256"]
            assert current!=fixture_ref["sha256"]
            if replacement:
                assert proof["previous_model_sha256"]==hash_before
                gate=e.atomic_gate(row,mapping,observation)
                assert gate["established"] and gate["verdict"]["status"]=="passed"
for platform in ("ios","android"):
    test("current-model-not-whole-file-"+platform,lambda p=platform:synthetic_context(p))
    test("replacement-binds-before-and-after-model-"+platform,lambda p=platform:synthetic_context(p,True))
    test("whole-file-hash-cannot-prove-native-input-"+platform,lambda p=platform:synthetic_context(p,True,"whole-file"))
    test("wrong-previous-model-hash-stays-U-"+platform,lambda p=platform:synthetic_context(p,True,"previous"))
test("Android-sorted-hash-cannot-replace-input-order",lambda:synthetic_context("android",False,"wrong-order"))
test("Foundation-unescaped-slash-hash-stays-U",lambda:synthetic_context("ios",False,"unescaped-ios"))

def profile_unavailable():
    original=native.ROOT
    with tempfile.TemporaryDirectory(prefix="missing-profile-",dir=ROOT) as tmp:
        try:
            native.ROOT=Path(tmp);native.verify_profile.cache_clear()
            reject_encoding(byid["replacement_before"],"ios")
        finally:native.ROOT=original;native.verify_profile.cache_clear()
test("missing-native-profile-stays-U",profile_unavailable)

def relocation():
    with tempfile.TemporaryDirectory(prefix="cache-free-relocated-",dir=ROOT) as tmp:
        repo=Path(tmp)/"repository"
        relative=e.DESIGN.relative_to(e.REPO)
        target_design=repo/relative
        design_seal=e.read(e.DESIGN/"private/SEAL.json")
        for f in design_seal["payload"]["files"]:
            src=e.DESIGN/f["path"];dst=target_design/f["path"];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        sealpath=target_design/"private/SEAL.json";sealpath.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(e.DESIGN/"private/SEAL.json",sealpath)
        for dep in e.read(ROOT/"dependencies.json")["files"]:
            src=e.REPO/dep["path"];dst=repo/dep["path"];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        target_v1=target_design/"private/evaluator-prep";target_v1.mkdir(parents=True,exist_ok=True)
        for name in ("normalized-d0.json","normalized-final.json"):shutil.copy2(ROOT.parent/name,target_v1/name)
        target=target_v1/"v2";target.mkdir()
        for name in ("evaluator.py","native_encoding.py","dependencies.json","encoding-profiles.json","encoding-vectors.json","foundation-probe-output.json","kotlin-probe-output.json","probe-provenance.json","FoundationEncodingProbe.swift","KotlinJsonEncodingProbe.java","geometry_calibration.py"):
            shutil.copy2(ROOT/name,target/name)
        spec=importlib.util.spec_from_file_location("relocated_frozen_evaluator",target/"evaluator.py")
        relocated=importlib.util.module_from_spec(spec);spec.loader.exec_module(relocated)
        assert relocated.REPO==repo
        common=relocated.import_common()
        assert Path(common.__file__).is_relative_to(repo)
        assert Path(common.checks.__file__).is_relative_to(repo)
        assert all(not Path(f["path"]).is_absolute() for f in relocated.read(target/"dependencies.json")["files"])
        assert relocated.verify_design()["commitment_sha256"]==e.EXPECTED_DESIGN_COMMITMENT
        assert relocated.encoding_module().native_model_hash(byid["replacement_before"],"ios")[0]==native.native_model_hash(byid["replacement_before"],"ios")[0]
        assert relocated.encoding_module().native_model_hash(byid["replacement_before"],"android")[0]==native.native_model_hash(byid["replacement_before"],"android")[0]
test("relocated-cache-free-archive-import-and-profiles",relocation)

report={"version":2,"status":"PASS","tested_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "candidate_source_or_evidence_used":False,"control_count":len(results),"controls":results}
(ROOT/"encoding-controls-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":"PASS","control_count":len(results)}))
