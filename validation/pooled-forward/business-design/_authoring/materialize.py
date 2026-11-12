#!/usr/bin/env python3
"""Materialize independent static design artifacts. Contains embargoed data by import."""
from author_designs import *
from datetime import datetime, timezone

def native_type(spec,platform,child=None):
    names={"ios":{"string":"String","integer":"Int","boolean":"Bool"},"android":{"string":"String","integer":"Int","boolean":"Boolean"}}
    if spec["type"] in names[platform]: return names[platform][spec["type"]]
    return "["+(child or "String")+"]" if platform=="ios" else "List<"+(child or "String")+">"

def api(t):
    structs=[(name,t["schema"]["properties"][key]["items"]["properties"]) for key,name in t["child"].items()]+[(t["fixture"],t["schema"]["properties"])]
    a=["# Fixed production API","","These are API declarations, not a production implementation or substitute UI.","","```swift","import SwiftUI","// Export from the AlertToast module. All fields are public; supply public field initializers."]
    for name,props in structs:
        a += ["public struct "+name+": Codable, Equatable {"]+["    public var "+k+": "+native_type(s,"ios",t["child"].get(k)) for k,s in props.items()]+["}"]
    a += ["public struct "+t["api"]+": View {","    public init(fixture: "+t["fixture"]+", onEvent: @escaping (String) -> Void)","    public var body: some View { get }","}","```","","```kotlin","package com.example.reply.ui.components.business"]
    for name,props in structs: a += ["data class "+name+"("]+["    val "+k+": "+native_type(s,"android",t["child"].get(k))+"," for k,s in props.items()]+[")"]
    a += ["@Composable","fun "+t["api"]+"(fixture: "+t["fixture"]+", onEvent: (String) -> Unit)","```","","fixture.schema.json is the transport contract. All fields are nonoptional. IDs/labels are unique within each group and IDs use the delimiter-safe grammar. Allowed empty strings are explicit. Fixtures supply no local selection, approval, summary, eligibility override, or expected callback.","","Production owns real business state, decision gating, and same-versus-changed entity replacement. The component is additive, exported by AlertToast on iOS and located in production app/src/main on Android. No internal ScrollView/LazyColumn, modal, popup, overlay, navigation route, timer, network, randomness, async state, or animation is needed. A single eager vertical flow fills the offered child width; the host owns scrolling."]
    return "\n".join(a)+"\n"

def bridges(t):
    ios=f'''import Foundation
import SwiftUI
import AlertToast

enum ObserverBridge {{
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {{
        let bytes = try! JSONSerialization.data(withJSONObject: fixture)
        let decoded = try! JSONDecoder().decode({t['fixture']}.self, from: bytes)
        return AnyView({t['api']}(fixture: decoded, onEvent: onEvent))
    }}
}}
'''
    kt=["package org.nativeobserver","","import androidx.compose.runtime.Composable","import kotlinx.serialization.json.JsonObject","import kotlinx.serialization.json.jsonObject","import kotlinx.serialization.json.jsonArray","import kotlinx.serialization.json.jsonPrimitive","import kotlinx.serialization.json.boolean","import kotlinx.serialization.json.int","import com.example.reply.ui.theme.ContrastAwareReplyTheme","import com.example.reply.ui.components.business.*","","private fun JsonObject.s(k: String) = getValue(k).jsonPrimitive.content","private fun JsonObject.i(k: String) = getValue(k).jsonPrimitive.int","private fun JsonObject.b(k: String) = getValue(k).jsonPrimitive.boolean","","object ObserverBridge {","    @Composable","    fun Content(input: JsonObject, onEvent: (String) -> Unit) {","        val decoded = "+t["fixture"]+"("]
    for key,spec in t["schema"]["properties"].items():
        if spec["type"]=="array":
            kt += [f'            {key} = input.getValue("{key}").jsonArray.map {{ value ->',"                val item = value.jsonObject","                "+t["child"][key]+"("]
            for k,s in spec["items"]["properties"].items():
                exp=f'item.getValue("{k}").jsonArray.map {{ it.jsonPrimitive.content }}' if s["type"]=="array" else f'item.{dict(string="s",integer="i",boolean="b")[s["type"]]}("{k}")'
                kt.append(f"                    {k} = {exp},")
            kt += ["                )","            },"]
        else: kt.append(f'            {key} = input.{dict(string="s",integer="i",boolean="b")[spec["type"]]}("{key}"),')
    kt += ["        )","        ContrastAwareReplyTheme(darkTheme = false, dynamicColor = false) {","            "+t["api"]+"(fixture = decoded, onEvent = onEvent)","        }","    }","}",""]
    return ios,"\n".join(kt)

QUAL={
 "heading-visual-size":("heading","typography","Does the iOS heading follow the annotated reference's fixed22pt system-font size intent and title-to-body scale? This is qualitative, not a computed font reading.","ios"),
 "heading-visual-weight":("heading","typography","Does the iOS heading show the annotated reference's semibold/600 weight intent?","ios"),
 "body-visual-size":("description","typography","Does iOS body copy follow the annotated reference's fixed16pt regular system-font size intent? This is qualitative typography, not a computed point-size observation.","ios"),
 "body-visual-ink":("description","typography","Does iOS body copy follow the reference's dark ink (#FF201B13) visual intent against the white panel? This is a qualitative ink judgment, not computed color.","ios"),
 "content-wrap":("surface","layout","Across the complete swept state, is every supplied description, choice detail, summary, status, and current preview readable through natural wrapping, without ellipsis or a clipped final line?","both"),
 "content-overlap":("surface","layout","Across the complete swept state, do successive vertical blocks remain separate without overlapping or occluding one another?","both"),
 "horizontal-fit":("surface","layout","Across the complete swept state, does all component content stay within the offered child width without horizontal clipping or horizontal scrolling?","both"),
 "section-rhythm":("surface","layout","Do major vertical sections follow the annotated reference's16pt iOS /16dp Android separation intent? Judge the visual rhythm; do not infer framework padding from AX boxes.","both"),
 "row-padding":("surface","layout","Do option rows follow the annotated reference's12pt iOS /12dp Android content inset intent and leave their trailing24pt/dp paint gutter free of text and marks?","both"),
 "panel-corners":("surface","shape","Does the white panel follow the annotated reference's16pt iOS /16dp Android rounded-corner intent?","both"),
 "row-corners":("surface","shape","Do option rows follow the annotated reference's8pt iOS /8dp Android rounded-corner intent?","both"),
 "primary-ink":("primary","paint","Is the primary label visibly light against its enabled amber fill and dark against its disabled pale fill, as the reference shows?","both")}

SCOPE={"closed_shape":"One eager finite vertical production component. No internal scroll, overlays, asynchronous state, external data, or full app navigation.","fixture_domain":"Assessment covers the exact independently sealed family and action prefixes. The reusable public schema supports up to4 data rows per group; unbounded future caller inputs are not certified.","host":"390x600 logical viewport; host inset16 horizontal and24 top; Android density2.75 and explicit paparazzi-float32-screen-config-v1.","unsupported":[
 {"aspect":"generic computed SwiftUI typography/color/padding/layout_box","disposition":"not_applicable","reason":"Public iOS AX cannot expose these computed values. Sourced qualitative propositions and rendered opaque fill pixels cover the intended aspects; no mandatory unknown is added."},
 {"aspect":"generic effective padding and glyph ink geometry","disposition":"not_applicable","reason":"Public AX/Compose semantic boxes do not prove generic layout padding or glyph ink; visual intent is assessed separately."},
 {"aspect":"physical OS touch area","disposition":"not_applicable","reason":"Only primary control accessibility-box height and actual native dispatch are claimed."},
 {"aspect":"whole-app navigation/network/lifecycle/keyboard, RTL, other themes/font settings/widths","disposition":"not_applicable","reason":"Scope is an additive reusable component in the approved finite light/LTR/Large-or1.0 observer fixture."}]}

PIXEL='''# Frozen rendered-fill policy

All source colors are opaque #AARRGGBB, painted by the component itself. No alpha model, added epsilon, expected override, or color-dependent region selection is permitted. Host canvas color is not scored as component paint.

Panel: normalized [0.018,0.06,0.035,0.94] of full panel semantic box; visible_fragment; minimum12pixels; support0.95; RGB channel tolerance0. At358pt/dp width this x-strip is approximately6–12pt/dp: inside the white16pt/dp inset and outside every child. Its vertical range excludes rounded ends. Tall panels use eligible visible fragments of this same approved gutter.

Primary: [0.04,0.25,0.10,0.75]; fully_visible; minimum20pixels; support0.95; tolerance0. This left interior band is clear of the fixed short centered label and8pt/dp corner curves. Primary labels are fixed by each task and never supplied as long caller text.

Every option row: [0.94,0.25,0.98,0.75]; fully_visible; minimum20pixels; support0.95; tolerance0. A trailing24pt/dp gutter is intentionally free of text, marks, and icons. At326pt/dp row width the sample spans306.44–319.48, wholly inside the302–326 gutter. Labels/detail copy stop to its left; selection marks are at the leading edge. The sample excludes rounded top/bottom corners. A partial long row does not earn a fill pass where full visibility is required.

These independently suitable regions were fixed before candidate pixels exist. They establish dominant rendered sRGB fill only, not computed SwiftUI attributes, whole-canvas coverage, text ink, typography, effective padding, or physical hit area. Insufficient eligible support remains unknown. Semantic control facts, callbacks, rendered fill atoms and qualitative visual atoms stay separate.
'''

def all_controls(t,case):
    out=copy.deepcopy(case["ledger"][0]["expected"]["controls"]);out["primary"]=control(t["primary"],False,kind="action");return out
def bindings(t,case):
    b={k:{"identifier":t["id"]+"."+k} for k in ("surface","entity","description","summary","status")};b["heading"]={"label":t["name"]}
    for k,c in all_controls(t,case).items():
        b[k]={"label":c["label"]}
        if "detail" in c:b[k+"Detail"]={"identifier":t["id"]+"."+k+".detail"}
    if t["id"]=="T4":b["preview"]={"identifier":"T4.preview"}
    return b
def substitute(x,b):
    if isinstance(x,list):return [substitute(v,b) for v in x]
    if not isinstance(x,dict):return x
    return {k:b[v] if k=="target" and isinstance(v,str) else substitute(v,b) for k,v in x.items()}
def source(pointer):return dict(source="reference",pointer=pointer)

def materialize(t,kind):
    case=t[kind];out=ROOT/t["id"]/kind;out.mkdir(parents=True,exist_ok=True);scenario="public-main" if kind=="public" else "hidden-edge"
    ids=[x["state"]["id"] for x in case["ledger"]];cs=all_controls(t,case);b=bindings(t,case)
    ref=dict(design_owner=OWNER,business_rules=t["rules"],tokens=copy.deepcopy(TOKENS),scope=copy.deepcopy(SCOPE),states={},questions={k:typed(v[2]) for k,v in QUAL.items()},visual={k:typed(True) for k in QUAL},obligations=[],responsibilities=[],capture_validity=dict(scope="deterministic_component_fixture",max_age_seconds=1800,reset="fresh_native_fixture",external_state="all_dependencies_pinned"))
    rules=[];groups={};qual=copy.deepcopy(QUAL)
    for key,c in cs.items():
        if "selected" in c:qual[key+"-mark"]=(key,"selection","Is a selected/checked mark visibly present on this control?","both")
        if "detail" in c:qual[key+"-wrap"]=(key,"layout","Is all of this option's visible label and detail text readable through natural wrapping, without ellipsis or a clipped final line?","both")
    for key in ("summary","status"):qual[key+"-wrap"]=(key,"layout","Is all of this current text readable through natural wrapping, without ellipsis or a clipped final line?","both")
    ref["questions"]={k:typed(v[2]) for k,v in qual.items()};ref["visual"]={k:typed(True) for k in qual}
    def add(id,kind,target=None,property=None,group="content",**kw):
        r=dict(id=id,kind=kind)
        if target:r["target"]=target
        if property:r["property"]=property
        r.update(kw);rules.append(r);groups.setdefault(group,[]).append(id)
    for k in ("heading","entity","description","summary","status"):add(k+"-label","control",k,"label")
    add("surface-present","control","surface","present")
    for k,c in cs.items():
        add(k+"-label","control",k,"label");add(k+"-enabled","control",k,"enabled",group="eligibility")
        if "selected" in c:add(k+"-selected","control",k,"selected",group="eligibility")
        if "detail" in c:add(k+"-detail","control",k+"Detail","label")
    add("primary-height","geometry","primary","height",group="geometry",op="eq",measurement="accessibility_box",basis="control")
    for id,target,prop in (("heading-native-size","heading","font_sp"),("heading-native-weight","heading","font_weight"),("body-native-size","description","font_sp"),("body-native-ink","description","color_argb")):add(id,"text_layout",target,prop,group="typography")
    if t["id"]=="T4":add("preview-present","control","preview","present");add("preview-label","control","preview","label")
    add("tap-receipt","event",group="receipts");add("replacement-quiet","event",group="replacement",stimulus="caller_update")
    for k in ["surface","primary"]+[k for k,c in cs.items() if c["kind"]=="option"]:add(k+"-fill","manual",k,"rendered_fill_argb",group="paint",coverage="target",allowed_methods=["native_pixels"])
    for k,(target,group,q,platform) in qual.items():add(k,"manual",target,k,group=group,coverage="full_content" if target=="surface" else "target",allowed_methods=["visual"])
    for x in case["ledger"]:
        sid=x["state"]["id"];e=x["expected"];controls=copy.deepcopy(e["controls"]);controls["primary"]=control(t["primary"],e["primary_enabled"],kind="action")
        s={k:typed(e[k]) for k in ("entity","description","summary","status")};s.update(heading=typed(t["name"]),surface=typed(True),controls={},tap_events=typed(x["events"],"events"),replacement_events=typed([],"events"),preview_present=typed(e["preview"] is not None),fills=dict(surface=copy.deepcopy(TOKENS["colors"]["surface"])))
        if e["preview"] is not None:s["preview"]=typed(e["preview"])
        for k,c in controls.items():
            s["controls"][k]={p:typed(v) for p,v in c.items() if p!="kind"}
            if c["kind"]=="option":s["fills"][k]=copy.deepcopy(TOKENS["colors"]["selected" if c["selected"] else "surface" if c["enabled"] else "disabled"])
        s["fills"]["primary"]=copy.deepcopy(TOKENS["colors"]["primary" if e["primary_enabled"] else "disabledPrimary"]);ref["states"][sid]=s
    values={r["id"]:{} for r in rules};cells=[]
    for r in rules:
      rid=r["id"]
      for x in case["ledger"]:
        sid=x["state"]["id"];base="/states/"+sid;cell={};details={}
        for platform in ("ios","android"):
            p=None;na=None
            if rid.endswith("-label") and rid!="preview-label":
                k=rid[:-6];p=base+"/"+k if k in ("heading","entity","description","summary","status") else base+"/controls/"+k+"/label"
            elif rid=="surface-present":p=base+"/surface"
            elif rid.endswith("-enabled"):p=base+"/controls/"+rid[:-8]+"/enabled"
            elif rid.endswith("-selected"):p=base+"/controls/"+rid[:-9]+"/selected"
            elif rid.endswith("-detail"):p=base+"/controls/"+rid[:-7]+"/detail"
            elif rid=="primary-height":p="/tokens/"+platform+"/buttonHeight"
            elif rid in ("heading-native-size","heading-native-weight","body-native-size","body-native-ink"):
                if platform=="ios":na="Public iOS AX has no generic computed SwiftUI typography/color; the sourced iOS visual atom covers this intent."
                else:p={"heading-native-size":"/tokens/android/titleSize","heading-native-weight":"/tokens/android/titleWeight","body-native-size":"/tokens/android/bodySize","body-native-ink":"/tokens/colors/ink"}[rid]
            elif rid=="preview-present":p=base+"/preview_present"
            elif rid=="preview-label":
                if x["expected"]["preview"] is None:na="No preview exists in this draft; preview-present requires its absence after a complete sweep."
                else:p=base+"/preview"
            elif rid=="tap-receipt":
                if x["stimulus"]!="tap":na="No original requested tap stimulus belongs to this state; a sweep or caller update cannot establish a tap callback interval."
                else:p=base+"/tap_events"
            elif rid=="replacement-quiet":
                if x["stimulus"]!="caller_update":na="No original caller-replacement stimulus belongs to this state."
                else:p=base+"/replacement_events"
            elif rid.endswith("-fill"):p=base+"/fills/"+rid[:-5]
            elif rid in qual:
                if r.get("coverage")=="full_content" and x["state"]["coverage"]!="full_content":na="This intermediate state is independently target-scoped. Whole-component flow is not claimed here; local wrapping, selection marks, semantic decisions, paint and callbacks are actively assessed. Full-flow atoms are assessed at initial, ready/recorded, preview and replacement sweeps; no earlier pass is carried forward."
                elif qual[rid][3]=="ios" and platform=="android":na="Intentionally iOS-only qualitative font/ink atom; Android uses the exact available native TextLayout assertion."
                elif rid.endswith("-mark"):p=base+"/controls/"+rid[:-5]+"/selected"
                else:p="/visual/"+rid
            else:raise AssertionError(rid)
            if na:cell[platform]=dict(not_applicable=na);details[platform]=dict(disposition="not_applicable",reason=na)
            else:
                cell[platform]=source(p);v=ref
                for k in p.strip("/").split("/"):v=v[k]
                details[platform]=dict(disposition="assess",source="reference",pointer=p,expected=v["value"],unit=v["unit"],operator=r.get("op","eq"),method=r.get("allowed_methods",[r["kind"]])[0])
        if all("not_applicable" in c for c in cell.values()):cell=dict(not_applicable="; ".join(sorted(set(c["not_applicable"] for c in cell.values()))))
        values[rid][sid]=cell;cells.append(dict(requirement=rid,state=sid,aspect=r.get("property","callback"),platforms=details))
    obligations=[
      ("business-content","All supplied and computed business text is current and exact.","content",groups["content"],ids),
      ("decision-eligibility","Native disabled/selected facts obey published business decisions.","behavior",groups["eligibility"],ids),
      ("successful-tap-receipts","Exact tap event intervals require demonstrated successful original native dispatch; blocked taps never prove quiet behavior.","behavior",groups["receipts"],[x["state"]["id"] for x in case["ledger"] if x["stimulus"]=="tap"]),
      ("caller-replacement","Same-entity revalidation and changed-entity reset are distinct and callback-silent.","behavior",groups["replacement"]+groups["eligibility"]+groups["content"],[x["state"]["id"] for x in case["ledger"] if x["stimulus"]=="caller_update"]),
      ("typography","Typography follows sourced native or qualitative platform intent.","style",groups["typography"],ids),
      ("content-layout","Full variable-length vertical content wraps, fits and preserves separation/insets.","layout",groups["layout"],ids),
      ("opaque-paint","Component opaque fills match approved suitable pixel regions; primary ink is readable.","style",groups["paint"],ids),
      ("primary-accessibility-box","Primary control accessibility-box height is48pt/dp; no physical OS hit-area claim.","layout",groups["geometry"],ids),
      ("selection-affordance","Visible selection marks agree with native selected facts.","style",groups["selection"],ids),
      ("corner-shape","Panel and option corner shape follow independent annotated references.","style",groups["shape"],ids)]
    routes={}
    for id,clause,risk,rids,states in obligations:
        ref["obligations"].append(dict(id=id,clause=clause,priority="must",states=states,risk=risk))
        deps={"caller-replacement":["decision-eligibility","business-content","successful-tap-receipts","opaque-paint","selection-affordance"],"decision-eligibility":["caller-replacement","successful-tap-receipts","opaque-paint","selection-affordance"],"business-content":["content-layout"],"typography":["content-layout"],"content-layout":["primary-accessibility-box"]}.get(id,[])
        routes[id]=dict(rule_ids=rids,reason=clause,regression_obligations=deps)
    for method,kinds in (("control",["control"]),("geometry",["geometry"]),("text_layout",["text_layout"]),("callback",["event"]),("visual",["manual"])):
        ref["responsibilities"].append(dict(id="component-"+method,clause="Production owns applicable "+method+" facts in this fixture scope.",priority="must",owner="component",method=method,subject="production-component",rule_ids=[r["id"] for r in rules if r["kind"] in kinds]))
    for id,owner,subject,clause in (("real-production-api","component","production-component","The real exported additive production component owns all decisions, local UI state and replacement behavior; no external state or internal scroll."),("thin-pass-through","bridge","thin-bridge","Pinned bridge only decodes typed data, applies the real Android theme, and calls production with the same callback; no state, replacement UI, business computation, forced identity, or event echo."),("production-placement","integration","host-integration","AlertToast exports the actual SwiftUI component and Reply compiles the actual component from app/src/main. Existing finite vertical host owns scrolling/insets; no full-app navigation claim.")):
        ref["responsibilities"].append(dict(id=id,clause=clause,priority="must",owner=owner,method="source",subject=subject,rule_ids=[]))
    write(out/"reference.json",ref)
    schema=copy.deepcopy(t["schema"]);schema.update({"$schema":"https://json-schema.org/draft/2020-12/schema","title":t["fixture"],"$comment":"Unique group IDs and action labels; all UI/business decisions component-owned. No hidden-only requirement."});write(out/"fixture.schema.json",schema)
    ios,android=bridges(t);write(out/"ObserverBridge.swift",ios);write(out/"ObserverBridge.kt",android);launch={}
    for p,bridge in (("ios",ios),("android",android)):
        env=dict(width=390,height=600,direction="ltr",theme="light")
        if p=="ios":env["dynamic_type"]="large"
        else:env.update(font_scale=1.0,dimension_encoding="paparazzi-float32-screen-config-v1")
        write(out/("environment."+p+".json"),env)
        fixture=dict(initial=case["fixtures"][0],updates=case["fixtures"][1:],width=390,theme="light",direction="ltr",canvas_color="#FFF8F4",max_scrolls=18,required_identifiers=[v["identifier"] for k,v in b.items() if "identifier" in v and k!="preview"])
        fixture["dynamic_type" if p=="ios" else "font_scale"]="large" if p=="ios" else 1.0
        write(out/("fixtures."+p+".json"),fixture);launch[p]=dict(scenario=scenario,platform=p,fixtures_sha256=digest(fixture),bridge_sha256=rawsha(bridge.encode()))
        write(out/("bindings."+p+".json"),b);write(out/("actions."+p+".json"),substitute(case["actions"],b))
    write(out/"launch.json",launch);sources=[];source_data={}
    for id,name in (("reference","reference.json"),("launch","launch.json")):
        raw=(out/name).read_bytes();s=dict(id=id,path=name,sha256=rawsha(raw));sources.append(s);source_data[id]=dict(**s,document=json.loads(raw),raw_utf8=raw.decode())
    contract=dict(version=1,design_owner=OWNER,approval_reference="Root INDEPENDENCE.md and SEAL.sha256; author seal pending independent preimplementation review",sources=sources,required_rule_ids=[r["id"] for r in rules],rules=rules,scenarios={scenario:dict(states=[x["state"] for x in case["ledger"]],actions=case["actions"],values=values)})
    write(out/"contract.json",contract);lock=dict(version=1,contract=contract,sources=source_data,contract_sha256=digest(contract),trust_limit="Identity and exact typed derivation only. Authorship, design correctness and approval require a separate preimplementation review record.");write(out/"lock.json",lock)
    atoms=[];ownership={}
    for r in rules:
        if r["kind"]!="manual":continue
        id=r["id"];k=r["target"];ownership[k]="component"
        if r["allowed_methods"]==["native_pixels"]:
            sampling=dict(region=[0.018,0.06,0.035,0.94] if k=="surface" else [0.04,0.25,0.10,0.75] if k=="primary" else [0.94,0.25,0.98,0.75],minimum_pixels=12 if k=="surface" else 20,minimum_support=0.95,channel_tolerance=0,basis="semantic",visibility="visible_fragment" if k=="surface" else "fully_visible")
            atoms.append(dict(rule_id=id,aspect="rendered_fill",method="native_pixels",sampling=sampling))
        else:atoms.append(dict(rule_id=id,aspect=r["property"],method="visual",question=source("/questions/"+id)))
    policy=dict(version=1,design_lock_sha256=digest(lock),approval_reference="Preimplementation independent sampling and propositions; PIXEL-SCOPE.md",ownership=ownership,atoms=atoms);write(out/"policy.json",policy)
    routefile=dict(version=1,index=source("/obligations"),routes=routes);write(out/"routes.json",routefile)
    targetstates=[]
    for x in case["ledger"]:
        sid=x["state"]["id"];targets=sorted({r["target"] for r in rules if "target" in r for c in cells if c["requirement"]==r["id"] and c["state"]==sid and any(v["disposition"]=="assess" for v in c["platforms"].values())})
        targetstates.append(dict(**x["state"],after_targets=targets,observation_action=x["state"]["after_action"],callback_gate="Original stimulus_action must have actual successful native dispatch by the requested method. Missing, disabled or blocked stimulus is U, not a quiet pass."))
    write(out/"target-observations.json",dict(version=1,scenario=scenario,states=targetstates))
    assess=sum(v["disposition"]=="assess" for c in cells for v in c["platforms"].values())
    write(out/"denominator.json",dict(version=1,authorship="Independent author; no implementation-written expected overrides",complete_rule_ids=[r["id"] for r in rules],complete_state_ids=ids,platforms=["ios","android"],total_cells=len(cells)*2,assess_cells=assess,not_applicable_cells=len(cells)*2-assess,cells=cells))
    write(out/"outcomes.json",dict(version=1,scenario=scenario,business_rules_source="reference.json#/business_rules",states=[dict(**x["state"],stimulus=x["stimulus"],exact_business_state=x["expected"],exact_callback_interval=x["events"],callback_gate="Only original successfully dispatched tap/caller-update; sweeps have no business callback assertion") for x in case["ledger"]]))
    write(out/"API.md",api(t));write(out/"PIXEL-SCOPE.md",PIXEL);write(out/"BRIEF.md",brief(t,kind,scenario))
    svg(t,case["ledger"][0]["expected"],out/"reference-initial.svg","Initial draft");svg(t,next(x["expected"] for x in case["ledger"] if x["expected"]["primary_enabled"]),out/"reference-ready.svg","Ready to submit")
    write(out/"seal.json",dict(version=1,design_owner=OWNER,phase="all-five independent preimplementation author seal; review pending",scenario=scenario,design_lock_sha256=digest(lock),policy_sha256=digest(policy),routes_sha256=digest(routefile),environment_sha256={p:digest(json.loads((out/("environment."+p+".json")).read_text())) for p in ("ios","android")},launch_ref={p:dict(source="launch",pointer="/"+p) for p in ("ios","android")},responsibility_ref=source("/responsibilities"),capture_validity_ref=source("/capture_validity")))

def brief(t,kind,scenario):
    visibility="PUBLIC — initial PR implementers may read this directory." if kind=="public" else "PRIVATE — embargoed until ALL10 final production-source/selfclaim seals. No implementation/repair worker may read this directory earlier."
    return f'''# {t['id']} — {t['name']}

{visibility}

Deliver `{t['api']}`, a reusable additive AlertToast public SwiftUI View and Reply production Compose component. Use the exact typed API in API.md. Caller data is immutable; production owns actual UI decisions, state, and replacement transitions. `onEvent(String)` forwards local request payloads only.

## Business rules

{t['rules']}

## Layout and style

The annotated initial/ready SVGs are independent structural and qualitative references, not candidate renders or cross-renderer glyph pixel oracles. Native tokens in reference.json are normative. Order: heading, entity, description, prerequisite choices, dependent option rows, summary, status, final review/approval, primary. T4 puts its current preview between Preview notice and wording approval. Credit/modes/intake checks precede their dependent choices. Every section participates in one eager vertical flow. Keep all supplied text, selected decisions, disabled options and their reasons visible through natural wrapping; no ellipsis, internal scrolling, overlay, or horizontal overflow.

The panel is opaque white,16pt/dp inset,16pt/dp radius. Option rows use12pt/dp inset,8pt/dp gaps/radius, and an empty trailing24pt/dp paint gutter. Major sections use16pt/dp gaps. Selection marks are leading. Primary fills available content width, has48pt/dp control-box height and8pt/dp radius, with its fixed centered short label. Selected rows retain selected fill when recorded state locks controls; unselected disabled rows use disabled fill. Enabled unselected rows are white. Primary uses its separately sourced enabled/disabled opaque fills; do not blend native disabled alpha over them.

iOS uses explicit system22pt semibold heading and16pt regular body intent at Large Dynamic Type. Android reuses Reply titleLarge22sp/600 and bodyLarge16sp/400. iOS typography/layout/ink questions are qualitative source-backed atoms; no generic computed font, color, layout-box or padding extraction is claimed. Android available TextLayout font/color facts are separate native atoms. The48pt/dp primary assertion measures its actual control accessibility box, not physical OS touch area.

## Host, data and bridges

Approved viewport:390logical width,600height, light, LTR; iOS Large or Android font_scale1.0. iOS host inset16horizontal/24top offers358pt child width. Android uses matching host insets at requested390x600dp,density2.75 with `paparazzi-float32-screen-config-v1`; requested390dp may serialize389.81818dp. This encoding is not product tolerance. The existing host owns scrolling. No whole-app navigation claim is made.

Each family includes initial, same-entity and changed-entity typed payloads. The schema contains no decisions or expected state. The pinned thin bridge only decodes and calls production with the same callback; Android applies the real stock non-dynamic light theme. It has no replacement UI, business state, identity reset or synthetic callback. API placement and thin-bridge source responsibilities are separately audited.

## Scenarios and denominator

Scenario `{scenario}` in contract.json fixes the original tap/apply_next_fixture/sweep/checkpoint route. Initial, ready/recorded, preview and replacement states have explicit full sweeps. Intermediate decision states have checkpoint/targets coverage and active local wrapping/mark/semantic/paint/callback checks. Every state has an independent after-target list. Earlier business stimuli are linked through `stimulus_action`; the compiler derives native target observation work. Whole-flow questions are scoped only to full-sweep states, without carrying an earlier pass into a target-scoped state. Every tap requires native enabled=true; toggles additionally require their exact previous selection. No direct state injection or invented action kind is allowed.

Callbacks require actual successful original native dispatch by the requested method. Missing, disabled, blocked, wrong-method or unexecuted actions cannot establish a callback pass/fail. Disabled choices are assessed as native facts without pretending to activate them. Every successful non-submit tap has an exact empty event interval; each successful submit has the exact one-element interval; successful caller replacement is silent. Full sweep evidence is distinct from those immediate intervals.

outcomes.json fixes exact business text, summaries, previews, disabled/selected decisions and payloads. denominator.json contains every rule×selected-state×platform/aspect cell with its exact source/operator/unit or explicit N/A reason. Native semantic facts, callbacks, rendered opaque pixels and atomic visual propositions are distinct. Unsupported iOS computed style, effective padding/glyph ink, physical hit area and whole-app concerns are N/A with reasons in reference.json#/scope, without padded mandatory U rows.

The routes close meaningful regression dependencies: eligibility/selection changes require replacement, current content, callbacks, paint and visible cue checks; typography/business text changes require complete long-content layout checks. A repair in one state never proves another state's evidence.

## Local accessibility metadata

Actions/options use exact unique natural labels. Only the panel and dynamic text fields use a small static component-local accessibilityIdentifier/testTag map in bindings.*.json. Keys contain no business record IDs and require no global registry. Dynamic text exposes its actual label; no unverified cross-platform native-value mapping is assumed. Preserve separate action/description children. The surface exposes its panel box without merging children away. Actual Button/Compose action nodes expose enabled/selected facts.

## Frozen identity

Public/private contracts, references, fixtures, bridges, API/schema, policy, routes, environments, outcomes, denominator and SVGs are physically separate. Public source documents contain no private data. seal.json records canonical digests; root SEAL.sha256 fixes all five public/private families together before implementation. Hash identity is not semantic approval. An independent format/design reviewer validates compilation and scope before initial code. No expectation or tolerance may be changed after seeing candidate results.
'''

def svg(t,e,path,state):
    parts=[];y=44
    def tx(s,x,y,size=16,weight=400,color="#201B13"):parts.append(f'<text x="{x}" y="{y}" font-family="system-ui,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(s)}</text>')
    def wrap(s,x,start,width=35,size=16,weight=400,color="#201B13"):
        z=start
        for para in s.split("\n"):
            for line in textwrap.wrap(para,width) or [""]:tx(line,x,z,size,weight,color);z+=24
        return z
    y=wrap(t["name"],32,y,25,22,600)+12;y=wrap(e["entity"],32,y,33,16,600)+8;y=wrap(e["description"],32,y)+16
    order=list(e["controls"])
    if t["id"]=="T3":order=["credit","methodA","methodB","authorize"]
    if t["id"]=="T5":order=["accessories","data","power","restock","repair","recycle","custody"]
    deferred=[]
    for k in order:
        c=e["controls"][k]
        if k in ("packing","notify","authorize","approve","custody"):deferred.append(c);continue
        s=c["label"]+("\n"+c["detail"] if "detail" in c else "");n=sum(max(1,len(textwrap.wrap(p,28))) for p in s.split("\n"));h=max(56,n*24+24)
        fill="#FFDDB3" if c.get("selected") else "#FFFFFF" if c["enabled"] else "#F3E6DA"
        parts.append(f'<rect x="32" y="{y}" width="326" height="{h}" rx="8" fill="{fill}" stroke="#817567"/><path d="M334 {y+12} V{y+h-12}" stroke="#D3C4B4" stroke-dasharray="2 4"/>')
        tx("✓" if c.get("selected") else "○",44,y+28,16,600);wrap(s,68,y+28,28,color="#201B13" if c["enabled"] else "#4F4539");y+=h+8
        if k=="previewAction" and e["preview"]:y=wrap(e["preview"],44,y+28,33)+16
    y+=8;n=max(1,len(textwrap.wrap(e["summary"],32)));h=n*24+24;parts.append(f'<rect x="32" y="{y}" width="326" height="{h}" rx="8" fill="#FFF1E5"/>');wrap(e["summary"],44,y+28,32,16,600);y+=h+16;y=wrap(e["status"],32,y+16)+16
    for c in deferred:y=wrap(("☑ " if c.get("selected") else "☐ ")+c["label"],32,y+16)+16
    fill="#805610" if e["primary_enabled"] else "#EDE0D4";ink="#FFFFFF" if e["primary_enabled"] else "#201B13";parts.append(f'<rect x="32" y="{y}" width="326" height="48" rx="8" fill="{fill}"/><text x="195" y="{y+30}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="16" font-weight="600" fill="{ink}">{escape(t["primary"])}</text>');y+=64
    notes=["INDEPENDENT AUTHOR REFERENCE",t["id"]+" · "+state,"390 logical parent /358 child","Host viewport600; full content shown","No component-owned scrolling","","Title22pt iOS /22sp Android,600","Body16pt iOS /16sp Android","Panel inset16, radius16pt/dp","Major section gap16pt/dp","Rows inset12, gap8, radius8pt/dp","Empty trailing paint gutter24pt/dp","Dashed guide is annotation only","Primary height48pt/dp, radius8","","Opaque source-backed palette:","#FFFFFFFF panel/unselected row","#FFFFDDB3 selected row","#FFF3E6DA disabled option","#FF805610 enabled primary","#FFEDE0D4 disabled primary","#FF201B13 text /#FFFFFFFF primary","","Wrap all copy; no ellipsis","No overlap or horizontal clipping","Visible selected/checked marks","","Schematic wrapping and glyphs","are not cross-renderer pixel targets.","Pixel regions are frozen separately","in policy.json /PIXEL-SCOPE.md."]
    for i,s in enumerate(notes):tx(s,416,36+i*24,13,600 if i<2 else 400)
    height=max(860,y+32);write(path,f'<svg xmlns="http://www.w3.org/2000/svg" width="780" height="{height}" viewBox="0 0 780 {height}"><title>{escape(t["id"]+" "+state+" independent reference")}</title><rect width="780" height="{height}" fill="#FFF8F4"/><rect x="16" y="16" width="358" height="{y}" rx="16" fill="#FFFFFF"/>\n'+"\n".join(parts)+"\n</svg>\n")

def main():
    for t in TASKS:
        for kind in ("public","private"):materialize(t,kind)
    paths=["validation/pooled-forward/candidate-v13.9/SKILL.md",*["validation/pooled-forward/candidate-v13.9/references/"+n+".md" for n in ("design-contract","atomic-review","state-evidence","default-feedback","decision-feedback","managed-execution","pooled-workflow")],"validation/pooled-forward/candidate-v13.9/assets/ios-observer/CONTRACT.md",*["validation/pooled-forward/candidate-v13.9/assets/design-example/"+n+".json" for n in ("contract","reference","actions","bindings")],*["validation/pooled-forward/candidate-v13.9/assets/atomic-example/"+n+".json" for n in ("contract","reference","actions","bindings","policy","lock","approval","environment.ios","environment.android")],"validation/pooled-forward/cache/hosts/alerttoast/Sources/AlertToast/AlertToast.swift",*["validation/pooled-forward/cache/hosts/reply/Reply/app/src/main/java/com/example/reply/ui/"+n for n in ("theme/Color.kt","theme/Type.kt","theme/Shapes.kt","theme/Theme.kt","components/ReplyEmailListItem.kt")]]
    write(ROOT/"READSET.json",dict(version=1,owner=OWNER,files=[dict(path=p,sha256=rawsha((REPO/p).read_bytes())) for p in paths],directory_inventory=["candidate-v13.9/assets/design-example","candidate-v13.9/assets/atomic-example","cache/hosts/alerttoast/Sources","cache/hosts/reply/Reply/app/src/main"],additional_interface_from_parent=dict(path="candidate-v13.9/references/native-tools.md",scope="Only public Android ABI excerpt lines14–24 supplied by parent; author did not read the file",signature="org.nativeobserver.ObserverBridge.Content(input: JsonObject,onEvent:(String)->Unit) @Composable"),prohibited_reads="No prior study/result, qualification/counter source, candidate implementation/test, performance data or future implementation read; no SDK/native renderer executed."))
    write(ROOT/"INDEPENDENCE.md",'''# Independent authorship and freeze

Owner: Independent design/oracle author /root/v13_business_design. This separate context received only the requirement, frozen public interface references/examples, and stock host source permission. It chose five new business briefs without reading previous tasks/studies/results, qualification/counter source, implementation/tests, performance data, or future implementation. No implementer was contacted and no SDK/native renderer was run. The parent supplied only a public Android bridge ABI excerpt. READSET.json pins exact file identities and inventories.

All five PUBLIC and PRIVATE fixture/scenario/reference/contract/lock/policy/routes/environment/API/schema/bridge/outcome/denominator/SVG families are fixed together before first initial production implementation. Public/private source documents and locks are physically separate. Public sources contain no private input, expectation, or edge sequence. The design-only authoring scripts contain held-out data and are not given to implementers.

This is an author seal, not external human approval or a claim of semantic infallibility. Existing design_contract/review_contract tooling is not invoked by this author; the independent reviewer validates compilation and scope before code. If a reviewer rejects a draft, preserve its exact bytes and rejection, revise only from public requirement evidence, and reseal all five families before initial code. Never alter a rule, tolerance, sampling region, or expected outcome after seeing candidate results. One author-QA draft is preserved in _drafts/author-qc-001.tar.gz with exact seal/reasons in AUTHOR-QC-001.json: its long SVG heading needed wrapping, its option pixel region needed to lie wholly within the independently empty gutter, and its approximate start time was replaced by the first observed timestamp. No candidate evidence existed. One failed apply_patch made no file change while authoring.

Every selected state has an independent target list. Full-flow claims at initial, ready/recorded, preview and replacement states have explicit full sweeps. Intermediate decisions use checkpoint/targets with local wrapping, mark, paint, semantic and callback atoms, without carrying forward prior passes. Callback assertions bind original successful stimuli and method; blocked/disabled actions cannot earn quiet callback credit. Every family distinguishes same-entity revalidation from changed-entity reset. Complete denominators include explicit platform/state N/A reasons, with no padded mandatory unsupported iOS style/physical-hit U rows.

Local metadata scope is explicit: natural action labels and a small static component-local AX identifier/testTag map for panel/dynamic text. No global business-record registry is required; zero markup instrumentation is not claimed. Source responsibilities separately require actual production API/placement, component-owned decisions and thin pass-through bridges.

PRIVATE EMBARGO: only T*/public/ goes to initial implementation or repair workers. All private files and _authoring remain unexposed until the coordinator verifies ALL10 final production-source/selfclaim seals. Hidden inputs contain longer varied data and rule-derived edge sequences, with identical public business rules, tokens, sampling policy and qualitative propositions. They add no secret design requirement or tolerance.
''')
    lines=["# Five independently designed paired native component tasks","","All designs are fixed together before implementation. Hand implementation workers ONLY T*/public/.","","| Task | Business component | Public states | Private states |","|---|---|---:|---:|"]
    for t in TASKS:lines.append(f"| {t['id']} | {t['name']} | {len(t['public']['ledger'])} | {len(t['private']['ledger'])} |")
    lines += ["","Each family contains a public-rule brief, typed API/schema, platform fixtures and pure decoding bridges, guarded original actions/bindings, exact outcomes, complete denominator, per-state target observation plan, typed reference/contract/lock, atomic visual/pixel policy, obligation routes, environments and annotated initial/ready SVGs.","","Public/private locks embed only their own sources. seal.json records canonical digests. SEAL.sha256 pins file-byte identities for every family and author record, including TIME.json, except the seal itself. The exact seal-file digest is reported to the coordinator for external retention. Reviewer compilation before approval remains required.","","Eligibility repair dependencies cover replacement, receipts, paint and selection cues. Content/typography dependencies cover long-content layout. Scope is finite reusable-component integration, without whole-app navigation claims. No production implementation or native rendering was performed. See INDEPENDENCE.md/READSET.json."]
    write(ROOT/"INDEX.md","\n".join(lines)+"\n")
    write(ROOT/"TIME.json",dict(version=1,first_observed_utc=START,start_precision="First exact wall-clock observation; drafting began before this reading",completed_utc=datetime.now(timezone.utc).isoformat(),phase="all-five independent public/private author freeze before implementation",seal_identity="SEAL.sha256 includes this time record; exact seal-file digest retained externally by coordinator",sdk_or_render_commands=0,implementation_files_read=0,previous_study_files_read=0))
    files=sorted(p for p in ROOT.rglob("*") if p.is_file() and p.name!="SEAL.sha256" and "__pycache__" not in p.parts)
    seal="".join(rawsha(p.read_bytes())+"  "+str(p.relative_to(ROOT))+"\n" for p in files);write(ROOT/"SEAL.sha256",seal)
    print(json.dumps(dict(root=str(ROOT),file_seal_sha256=rawsha(seal.encode()),families=10,states={t["id"]:{k:len(t[k]["ledger"]) for k in ("public","private")} for t in TASKS})))

if __name__=="__main__":main()
