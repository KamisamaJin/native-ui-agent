#!/usr/bin/env python3
"""Synthetic controls only; no candidate source or observation is used."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import copy, importlib.util, json, tempfile, hashlib, datetime
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("independent_evaluator",ROOT/"evaluator.py")
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
results=[]
def test(name,fn):
    fn();results.append({"id":name,"status":"PASS"})
def reject(fn):
    try:fn()
    except (AssertionError,ValueError,KeyError,TypeError):return
    raise AssertionError("Invalid evaluation was accepted")
def row(method="callback",expected=None,platform="ios",trigger="activate"):
    return dict(key="generic/"+platform+"/checkpoint/cell",platform=platform,category="business",
        method=method,sourceOnly=False,source_only=False,requires_stimulus=True,
        expected=["generic_event"] if expected is None else expected,
        original_expected_sha256=e.value_digest(["generic_event"] if expected is None else expected),
        trigger={"type":trigger,"target":{"identifier":"generic.control"},"method":"caller_fixture_update" if trigger=="replaceModel" else "xcui_tap" if platform=="ios" else "compose_onclick"},
        required_method="caller_fixture_update" if trigger=="replaceModel" else "xcui_tap" if platform=="ios" else "compose_onclick",
        denominator="runtime_business",id="callback.events")
def step(platform="ios",events=None,replacement=False):
    before=dict(pid=314,instance="synthetic_instance",fixture_index=0,input_sha256="synthetic_fixture_sha",event_revision=0)
    after=dict(before,fixture_index=1 if replacement else 0,event_revision=len(["generic_event"] if events is None else events))
    return {"outcome":"updated" if replacement else "tapped","selector":{"identifier":"generic.control"},
       "callback_delta":["generic_event"] if events is None else events,"binding_after":after,
       "dispatch":{"attempted":True,"succeeded":True,"method":"caller_fixture_update" if replacement else "xcui_tap" if platform=="ios" else "compose_onclick",
        "stimulus":"caller_update" if replacement else "activation","binding_before":before,
        "matches":1,"native_controls":1,"enabled":True,"event_start":0,"event_end":after["event_revision"]}}
def verdict(r,s):
    return e.atomic_gate(r,{"trigger_action_index":0},{"steps":[s]})
def positive(platform):
    g=verdict(row(platform=platform),step(platform))
    assert g["established"] and g["verdict"]["status"]=="passed"
for platform in ("ios","android"):test("requested-route-"+platform,lambda p=platform:positive(p))
test("successful-missing-callback-is-F",lambda:(
    (lambda g: (_ for _ in ()).throw(AssertionError()) if not(g["established"] and g["verdict"]["status"]=="failed") else None)(verdict(row(),step(events=[])))))
test("successful-noop-empty-is-P",lambda:(
    (lambda g: (_ for _ in ()).throw(AssertionError()) if not(g["established"] and g["verdict"]["status"]=="passed") else None)(verdict(row(expected=[]),step(events=[])))))
test("successful-replacement-quiet-is-P",lambda:(
    (lambda g: (_ for _ in ()).throw(AssertionError()) if not(g["established"] and g["verdict"]["status"]=="passed") else None)(verdict(row(expected=[],trigger="replaceModel"),step(events=[],replacement=True)))))

def unavailable_mutation(name,mutate):
    s=step();mutate(s)
    for expected in (["generic_event"],[]):
        r=row(expected=expected);g=verdict(r,s)
        assert not g["established"],name
        # Both false PASS and false FAIL must be rejected by the common gate.
        for outcome in ("PASS","FAIL"):
            reject(lambda:e.import_common().validate_precondition_outcome(r,{"outcome":outcome},{"trigger_action_index":0},{"steps":[s]}))
    return
mutations={
 "dispatch-not-attempted":lambda s:s["dispatch"].update(attempted=False),
 "dispatch-not-succeeded":lambda s:s["dispatch"].update(succeeded=False),
 "requested-method-mismatch":lambda s:s["dispatch"].update(method="ax_performAction"),
 "requested-stimulus-mismatch":lambda s:s["dispatch"].update(stimulus="navigation"),
 "missing-ios-pid":lambda s:s["dispatch"]["binding_before"].pop("pid"),
 "changed-pid":lambda s:s["binding_after"].update(pid=999),
 "changed-instance":lambda s:s["binding_after"].update(instance="other"),
 "missing-instance":lambda s:s["dispatch"]["binding_before"].pop("instance"),
 "changed-input-index":lambda s:s["binding_after"].update(fixture_index=1),
 "missing-input-sha":lambda s:s["binding_after"].pop("input_sha256"),
 "changed-input-sha":lambda s:s["binding_after"].update(input_sha256="different"),
 "ambiguous-native-matches":lambda s:s["dispatch"].update(matches=2),
 "boolean-native-match-count":lambda s:s["dispatch"].update(matches=True),
 "ambiguous-native-controls":lambda s:s["dispatch"].update(native_controls=2),
 "disabled-control":lambda s:s["dispatch"].update(enabled=False),
 "unavailable-outcome":lambda s:s.update(outcome="unavailable"),
 "missing-callback-interval":lambda s:s.pop("callback_delta"),
 "event-revision-count-mismatch":lambda s:s["binding_after"].update(event_revision=4),
 "wrong-event-start":lambda s:s["dispatch"].update(event_start=3),
 "wrong-event-end":lambda s:s["dispatch"].update(event_end=3),
 "receipt-from-other-input":lambda s:s.update(callback_delta=[{"event":"generic_event","fixture_index":99}])
}
for name,mutate in mutations.items():test(name,lambda n=name,m=mutate:unavailable_mutation(n,m))

def wrong_target():
    s=step();s["selector"]["identifier"]="another.control"
    assert not verdict(row(),s)["established"]
test("requested-selector-mismatch-stays-U",wrong_target)
def absent_target():
    s=step();s.pop("selector")
    assert not verdict(row(),s)["established"]
test("missing-actual-selector-stays-U",absent_target)
def absent_step():
    g=e.atomic_gate(row(),{"trigger_action_index":0},{"steps":[]})
    assert not g["established"]
test("missing-native-step-stays-U",absent_step)
def business_gate():
    r=row(method="native_text",expected={"equals":"generic state"})
    s=step();s["dispatch"]["succeeded"]=False
    assert not verdict(r,s)["established"]
test("post-business-cannot-use-literal-or-source-without-dispatch",business_gate)
def replacement_not_advanced():
    s=step(events=[],replacement=True);s["binding_after"]["fixture_index"]=0
    assert not verdict(row(expected=[],trigger="replaceModel"),s)["established"]
test("unadvanced-replacement-stays-U",replacement_not_advanced)

def minimal_grade(r,outcome="P"):
    return dict(key=r["key"],outcome=outcome,denominator=r["denominator"],
        expected_sha256=r["original_expected_sha256"],evidence=[{"path":"literal-receipt","pointer":"/not-native"}])
def audit_reject(change,blocked=False):
    r=row();s=step()
    if blocked:s["dispatch"]["succeeded"]=False
    report={"rows":[minimal_grade(r)]};plan={"required_keys":[r["key"]],"rows":[r]}
    contexts={(r["platform"],r.get("caseId"),r.get("stateId")):{"valid":True,"mapping":{"trigger_action_index":0},"observation":{"steps":[s]}}}
    change(report,r)
    reject(lambda:e.audit_report(report,plan,contexts))
test("reject-omitted-grade-row",lambda:audit_reject(lambda report,r:report.update(rows=[])))
test("reject-duplicate-grade-row",lambda:audit_reject(lambda report,r:report["rows"].append(copy.deepcopy(report["rows"][0]))))
test("reject-unplanned-grade-key",lambda:audit_reject(lambda report,r:report["rows"][0].update(key="unplanned")))
test("reject-changed-expected-hash",lambda:audit_reject(lambda report,r:report["rows"][0].update(expected_sha256="changed")))
test("reject-empty-evidence-on-P",lambda:audit_reject(lambda report,r:report["rows"][0].update(evidence=[])))
test("reject-cross-denominator-grade",lambda:audit_reject(lambda report,r:report["rows"][0].update(denominator="source_api")))
test("reject-literal-P-for-blocked-action",lambda:audit_reject(lambda report,r:None,blocked=True))
def forged_callback():
    r=row();s=step(events=[]);report={"rows":[minimal_grade(r)]};plan={"required_keys":[r["key"]],"rows":[r]}
    contexts={(r["platform"],r.get("caseId"),r.get("stateId")):{"valid":True,"mapping":{"trigger_action_index":0},"observation":{"steps":[s]}}}
    reject(lambda:e.audit_report(report,plan,contexts))
test("reject-P-contradicting-common-callback-F",forged_callback)
def unsupported_capability():
    r=row(method="native_bounds",expected={"field":"physical_hit_region_width","minimum":44})
    r.update(category="capability",capability="native_physical_hit_region",denominator="runtime_capability",requires_stimulus=False,trigger={"type":"initial"})
    report={"rows":[minimal_grade(r)]};plan={"required_keys":[r["key"]],"rows":[r]}
    contexts={(r["platform"],r.get("caseId"),r.get("stateId")):{"valid":True,"mapping":{},"observation":{},"found":[]}}
    reject(lambda:e.audit_report(report,plan,contexts))
test("reject-capability-P-from-semantic-or-source-fact",unsupported_capability)
test("null-placeholder-does-not-replace-minimum",lambda:(_ for _ in ()).throw(AssertionError()) if e.match_value(8,{"minimum":8,"equals":None}) is not True else None)

def full_missing_corpus():
    with tempfile.TemporaryDirectory(prefix="synthetic-controls-",dir=ROOT) as d:
        d=Path(d);manifest=d/"manifest.json";manifest.write_text(json.dumps({"version":1,"phase":"d0","anonymous_id":"synthetic_empty","observations":[]}))
        report=e.grade(manifest,d/"report.json")
        plan=e.read(ROOT/"normalized-d0.json")
        assert len(report["rows"])==len(plan["required_keys"])
        assert all(r["outcome"]=="U" for r in report["rows"])
        assert report["business_scopes"]["primary_post_stimulus"]["required"]>0
        assert report["business_scopes"]["primary_post_stimulus"]["stimulus_established"]==0
test("omitted-corpus-retains-all-required-U-rows",full_missing_corpus)

def no_expected_changes():
    for phase in ("d0","final"):
        p=e.read(ROOT/("normalized-"+phase+".json"))
        assert e.value_digest(p)==e.value_digest(e.normalize(phase))
        assert all(r["original_expected_sha256"]==e.value_digest(r["expected"]) for r in p["rows"])
test("adapter-preserves-all-sealed-expectations",no_expected_changes)

report={"version":1,"status":"PASS","tested_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "candidate_source_or_evidence_used":False,"control_count":len(results),"controls":results}
(ROOT/"negative-controls-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":"PASS","control_count":len(results)}))
