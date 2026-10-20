from pathlib import Path
import json, hashlib, datetime, copy

BASE = Path("/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/dispatch-forward/design")
PUBLIC, PRIVATE = BASE / "public", BASE / "private"
PUBLIC.mkdir(parents=True, exist_ok=True)
PRIVATE.mkdir(parents=True, exist_ok=True)

def write(path, value):
    if isinstance(value, (dict, list)):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(value.rstrip() + "\n", encoding="utf-8")

brief = """# Garden Water Round release panel

This is a new controlled native component for a shared garden steward to release one watering round. The steward chooses drip lines or soak hoses, sees the water calculation, and explicitly acknowledges any protected reserve use before release. Implement the real production component in the existing AlertToast Swift public library and Reply Android application package com.example.reply.ui.waterround. The public library must remain source-compatible with iOS 14 and macOS 11.

The component owns its state projection and calculations, but the caller owns the model. Every interaction is a request through a typed callback. No tap mutates the supplied model, checks a consent box locally, changes selection locally, or creates a local submitting state. An explicit new model from the caller recomputes the entire view immediately, including round identity, text, selection, eligibility and amounts. There is no remembered consent or calculation keyed to an old identity.

## Business rules

Let selectedRate be dripLitresPerBed for drip or soakLitresPerBed for soak. Let prime be dripPrimeLitres for drip and zero for soak.

- requiredLitres = bedCount * selectedRate + prime.
- spendableLitres = tankLitres - reserveLitres.
- reserveNeededLitres = max(0, requiredLitres - spendableLitres).
- remainingLitres = max(0, tankLitres - requiredLitres).
- shortfallLitres = max(0, requiredLitres - tankLitres).
- The reserve consent appears exactly when reserveNeededLitres > 0 and shortfallLitres == 0. It displays the supplied reserveAcknowledged value.
- Release is enabled exactly when isEnabled && !isSubmitting && shortfallLitres == 0 && (reserveNeededLitres == 0 || reserveAcknowledged).
- Drip is enabled exactly when isEnabled && !isSubmitting. Soak additionally requires soakAllowed. The selected choice stays enabled when the common enabled condition is true; tapping the already selected method is a no-op.
- Visible consent is enabled exactly when isEnabled && !isSubmitting.
- An enabled different method emits methodRequested. An enabled visible consent emits reserveAcknowledgementRequested with the opposite of the supplied Boolean. A valid release emits releaseRequested with the derived fields specified in api.md.
- Disabled actions and already selected method actions emit no event. A missing consent control has no action route. An attempted unavailable native activation cannot be used as evidence for a zero-event claim.

Status precedence and exact text:

1. !isEnabled: "Round paused".
2. isSubmitting: "Preparing release…".
3. shortfallLitres > 0: "Not enough water".
4. reserveNeededLitres > 0 && !reserveAcknowledged: "Approve reserve use".
5. Otherwise: "Ready to release".

A progress indicator appears exactly when isEnabled && isSubmitting. The action label is always "Release N L", where N is requiredLitres. No device locale, grouping separator, or rounding changes any numeric display: use ASCII base-ten integers and "L". The fixed English interface strings stay English in RTL; caller-supplied Unicode title, description, and notice are displayed verbatim.

## Content and ordering

The card fills the width offered by its parent. Its order is: title; description; input facts (Beds, Tank, Protected reserve, Drip prime); two vertical method choices (drip then soak); calculated summary (Required, Outside reserve, Reserve needed, Remaining, and Shortfall only when positive); conditional reserve consent; conditional notice; status; release action. Progress is inside the action alongside its label. Description is always shown. Notice is absent exactly when it is empty.

Exact fact and summary strings are "Beds: N", "Tank: N L", "Protected reserve: N L", "Drip prime: N L", "Required: N L", "Outside reserve: N L", "Reserve needed: N L", "Remaining: N L", and "Shortfall: N L". Each method shows its name on the first line and "N L per bed" on the second. Names are "Drip lines" and "Soak hoses". The consent label is "Use N L from the protected reserve".

## Native layout and visual requirements

The reference SVG is annotated design intention, not a native pixel golden. Native platform text rasterization may differ; the named dimensions, colors, hierarchy, and content behavior remain requirements.

The shared generic host has a 600 point/dp viewport height and adds 16 horizontal padding on each side. A 320-wide viewport offers 288 to the component; a 390-wide viewport offers 358. The component draws its own card surface. The parent canvas uses the platform host default color and is not responsible for painting the card or its contents. The card has no additional outside horizontal margin and no fixed height.

The card has radius 20, border width 1, and 16 internal padding on all four sides. Major sections have 12 vertical spacing. Method choices have 8 spacing between them, 12 internal padding on all four sides, radius 12 and border width 1. Each method control has minimum visible height 56. Consent has minimum visible height 44. The release control fills the inner width, has minimum visible height 48, 12 corner radius, and 12 internal padding on each side. All interactive controls require a physical hit region at least 44 by 44 points/dp.

Use system native sans-serif fonts, with native accessibility text scaling. At default scale: title 20 semibold; description, input facts, notice, and consent 14 regular; summary labels 13 regular; summary numeric values 17 semibold monospaced digits; method names and release label 16 semibold; method rates 14 regular; status 14 semibold. A summary may be one native text element with mixed typography, but all its text and its identifier must remain observable. No text line limit, ellipsis, clipping, horizontal scrolling, fixed-height card, or fixed-height text row. At narrow widths and larger text, all text wraps, rows grow, and the host vertical scroll can reach the entire card. Summary label/value rows have at least 8 spacing; use a vertical label/value arrangement when two columns would collide. Native layout direction mirrors leading/trailing alignment and control arrangement, while section order and numeric meaning remain unchanged.

Palette (RGB hex, fully opaque):

| Token | Light | Dark |
| --- | --- | --- |
| surface | #FFFFFF | #15251C |
| border | #D7E3D8 | #3B5242 |
| foreground | #183A25 | #E7F3E9 |
| muted | #526B59 | #B2C8B8 |
| accent | #216B3B | #81D89B |
| accentOn | #FFFFFF | #102C19 |
| selectedSurface | #E5F2E8 | #244F33 |
| warning | #865400 | #FFD28A |
| warningSurface | #FFF1D5 | #493715 |
| disabledSurface | #E5EBE6 | #293C2F |
| disabledText | #65756A | #92A396 |

Unselected choices use surface/border, selected choices selectedSurface/accent, and both use foreground text. Enabled release uses accent/accentOn; disabled release uses disabledSurface/disabledText without applying a second overall opacity. Status has warningSurface/warning whenever its text is not "Ready to release", and selectedSurface/foreground otherwise. Description and method rate use muted; all other body text uses foreground. Convey selection, enabled/disabled, checked state, progress, and status in native semantics as well as visually.

Runtime typography, exact internal padding, and physical hit-region evidence are required capabilities. If the observer cannot expose those native facts, retain these assertions as U (unavailable). Source declarations, screenshot guesses, semantic bounds, and a successful tap do not establish those facts.

## Integration boundary

The thin bridges decode every required JSON member, construct the public model, call the actual production entry point and serialize real typed callbacks. They contain no UI, watering business logic, amount calculations, eligibility calculation, callback synthesis, mutation of the model, or default branch. Host scrolling and visual evidence collection are external to the component and must not be counted as component callbacks.

Native activation routes are iOS XCUI tap and Android Compose semantic OnClick. This specification makes no claim about iOS AX performAction or Android OS physical touch. A successful explicit caller replacement can establish replacement quietness; an unavailable activation cannot establish no callbacks, handler failure, or a post-action state. Callback capture windows must preserve their original action interval if a subsequent full-content sweep scrolls to collect images.
"""
write(PUBLIC / "brief.md", brief)

api = """# Public native API and local selector contract

The feature name is WaterRound. Swift source belongs to the existing AlertToast public library; Android source belongs to com.example.reply.ui.waterround in Reply. These are public production types, not bridge-only mirror types.

## Shared model

Swift: public struct WaterRoundModel with public immutable stored properties and one public initializer taking every member below without default values. Kotlin: public data class WaterRoundModel with val properties and the same required constructor members. Swift Int and Kotlin Int are sufficient for the constrained domain. All JSON members are required; the bridge must not replace absent or invalid members with defaults.

| Member | Shared type | Valid domain |
| --- | --- | --- |
| roundId | String | nonempty ASCII letters, digits, underscore, or hyphen only |
| title | String | nonempty arbitrary Unicode |
| description | String | nonempty arbitrary Unicode |
| notice | String | arbitrary Unicode; empty means absent |
| bedCount | Int | 1…200 |
| dripLitresPerBed | Int | 1…500 |
| soakLitresPerBed | Int | 1…500 |
| dripPrimeLitres | Int | 0…2000 |
| tankLitres | Int | 0…200000 |
| reserveLitres | Int | 0…tankLitres |
| soakAllowed | Bool / Boolean | required |
| selectedMethod | WateringMethod | drip or soak; must be drip if soakAllowed is false |
| reserveAcknowledged | Bool / Boolean | required; ignored when consent is absent |
| isEnabled | Bool / Boolean | required |
| isSubmitting | Bool / Boolean | required |

WateringMethod is a public String-backed Swift enum and public Kotlin enum with exactly the values drip and soak. JSON enum values use these same lower-case strings. The semantic public model, method values, action alternatives, and payload members are identical across languages.

## Typed actions

Swift public enum WaterRoundAction uses the following associated-value cases. Kotlin public sealed interface WaterRoundAction uses public nested data classes with these same lower-case alternative names and the same members (lower-case class names are intentional here). All payloads are immutable and integer payloads use Int.

~~~swift
case methodRequested(roundId: String, method: WateringMethod)
case reserveAcknowledgementRequested(roundId: String, acknowledged: Bool)
case releaseRequested(
    roundId: String,
    method: WateringMethod,
    bedCount: Int,
    requestedLitres: Int,
    remainingLitres: Int,
    reserveUsedLitres: Int
)
~~~

Kotlin substitutes Boolean for Bool. No other action alternative or hidden UI-originated event is part of this API. reserveUsedLitres is reserveNeededLitres at the instant of an eligible release; requestedLitres is requiredLitres. The other payloads use exactly the current supplied model and current derived summary. On submitting, a request is never emitted merely because the replacement model says submitting.

Swift production entry:
~~~swift
public struct WaterRoundReleaseView: View
public init(model: WaterRoundModel, onAction: @escaping (WaterRoundAction) -> Void)
~~~

Kotlin production entry:
~~~kotlin
@Composable
fun WaterRoundRelease(
    model: WaterRoundModel,
    onAction: (WaterRoundAction) -> Unit,
    modifier: Modifier = Modifier
)
~~~

Swift's modifier remains the normal SwiftUI view modifier chain; Android must honor the optional supplied Modifier. New public Swift API must compile for iOS 14 and macOS 11. Guard later-platform APIs if used internally. Do not place this production view, its model, or its action type in a test host.

## Deterministic callback serialization

The bridge serializes actual typed actions as these exact ordered single-line strings, without whitespace additions or a trailing newline. Preserve event order in an array. Boolean tokens are lower-case true/false. Int tokens are ungrouped base-ten ASCII. roundId's domain makes escaping unnecessary. Never serialize a UI label or synthetic dictionary in place of a typed callback.

~~~text
methodRequested|roundId=ID|method=drip
reserveAcknowledgementRequested|roundId=ID|acknowledged=true
releaseRequested|roundId=ID|method=drip|bedCount=N|requestedLitres=N|remainingLitres=N|reserveUsedLitres=N
~~~

## Exact local selector vocabulary

These identifiers belong only to this component. iOS exposes them as accessibilityIdentifier; Android exposes them as Compose testTag. Do not add whole-application identifiers. A conditional target is absent when its content is absent. The root bounds cover the component's actual owned surface.

| Identifier | Meaning / native text or state |
| --- | --- |
| waterRound.root | owned card surface |
| waterRound.title | supplied title |
| waterRound.description | supplied description |
| waterRound.notice | supplied notice, only when nonempty |
| waterRound.beds | "Beds: N" |
| waterRound.tank | "Tank: N L" |
| waterRound.reserve | "Protected reserve: N L" |
| waterRound.dripPrime | "Drip prime: N L" |
| waterRound.method.drip | native button; accessible label "Drip lines, N L per bed"; selected and enabled state |
| waterRound.method.soak | native button; accessible label "Soak hoses, N L per bed"; selected and enabled state |
| waterRound.required | "Required: N L" |
| waterRound.spendable | "Outside reserve: N L" |
| waterRound.reserveNeeded | "Reserve needed: N L" |
| waterRound.remaining | "Remaining: N L" |
| waterRound.shortfall | "Shortfall: N L", only if positive |
| waterRound.reserveConsent | native checkable control; label "Use N L from the protected reserve"; checked and enabled state; only when consent is required |
| waterRound.status | exact status text defined in brief.md |
| waterRound.submit | native button; label "Release N L"; enabled state |
| waterRound.progress | native progress indicator, only when isEnabled && isSubmitting |

Numeric summary entries may expose the complete combined text via native label/text, even when visually laid out in separate spans. The action buttons must remain native actionable controls. Avoid turning the whole card into one combined accessibility element that hides the local selectors.

Use XCTest/XCUI tap for iOS and the Compose semantic OnClick action for Android. Android semantic activation is not a physical OS touch claim. Native checked/selected/enabled observations may use platform representations normalized to those Boolean concepts, with the original native fields retained. Repeated clicks on the visible consent request the same inverse Boolean until the caller sends a replacement. Repeated release requests use the same supplied model until replacement. A selected method button is enabled in an enabled round, but its successful tap is a no-op.

## Public example

public-example.json is an illustrative caller input, not a private validation case. Its environment is only a host instruction; production APIs receive the model. No expected event trace is published.
"""
write(PUBLIC / "api.md", api)

example_model = dict(
    roundId="demo_south", title="South teaching beds",
    description="Review the watering round before the steward opens the garden supply.",
    notice="Please return the hose to its rack after the round.",
    bedCount=8, dripLitresPerBed=6, soakLitresPerBed=9, dripPrimeLitres=3,
    tankLitres=120, reserveLitres=25, soakAllowed=True, selectedMethod="drip",
    reserveAcknowledged=False, isEnabled=True, isSubmitting=False
)
write(PUBLIC / "public-example.json", {
    "environment": {"width":390, "height":600, "component_offered_width":358, "theme":"light",
                    "direction":"ltr", "font_scale":1, "dynamic_type":"large"},
    "model": example_model
})

svg = """<svg xmlns="http://www.w3.org/2000/svg" width="970" height="1200" viewBox="0 0 970 1200" role="img" aria-labelledby="t d">
<title id="t">WaterRound annotated design intention</title>
<desc id="d">DESIGN INTENT ONLY — not a native screenshot or pixel golden. A 390 wide host offers a 358 wide card after its own 16 horizontal padding. The complete vertically growing card is illustrated with annotations.</desc>
<rect width="970" height="1200" fill="#F0F3F0"/>
<text x="24" y="32" font-family="sans-serif" font-size="19" font-weight="700" fill="#183A25">DESIGN INTENT ONLY · NOT A NATIVE PIXEL GOLDEN</text>
<text x="24" y="58" font-family="sans-serif" font-size="14" fill="#526B59">390-wide host example · platform default canvas is not prescribed · long content grows vertically</text>
<rect x="16" y="86" width="358" height="1072" rx="20" fill="#FFFFFF" stroke="#D7E3D8"/>
<g font-family="sans-serif" fill="#183A25">
<text x="32" y="124" font-size="20" font-weight="600">South teaching beds</text>
<text x="32" y="154" font-size="14">Review the watering round before</text>
<text x="32" y="175" font-size="14">the steward opens the garden supply.</text>
<text x="32" y="211" font-size="14">Beds: 8</text>
<text x="32" y="236" font-size="14">Tank: 120 L</text>
<text x="32" y="261" font-size="14">Protected reserve: 25 L</text>
<text x="32" y="286" font-size="14">Drip prime: 3 L</text>
<rect x="32" y="306" width="326" height="76" rx="12" fill="#E5F2E8" stroke="#216B3B"/>
<circle cx="51" cy="333" r="7" fill="#216B3B"/>
<text x="69" y="336" font-size="16" font-weight="600">Drip lines</text>
<text x="69" y="360" font-size="14" fill="#526B59">6 L per bed</text>
<rect x="32" y="390" width="326" height="76" rx="12" fill="#FFFFFF" stroke="#D7E3D8"/>
<circle cx="51" cy="417" r="7" fill="none" stroke="#526B59"/>
<text x="69" y="420" font-size="16" font-weight="600">Soak hoses</text>
<text x="69" y="444" font-size="14" fill="#526B59">9 L per bed</text>
<text x="32" y="504" font-size="13">Required</text><text x="358" y="504" font-size="17" font-weight="600" text-anchor="end">51 L</text>
<text x="32" y="541" font-size="13">Outside reserve</text><text x="358" y="541" font-size="17" font-weight="600" text-anchor="end">95 L</text>
<text x="32" y="578" font-size="13">Reserve needed</text><text x="358" y="578" font-size="17" font-weight="600" text-anchor="end">0 L</text>
<text x="32" y="615" font-size="13">Remaining</text><text x="358" y="615" font-size="17" font-weight="600" text-anchor="end">69 L</text>
<text x="32" y="661" font-size="14">Please return the hose to its rack</text><text x="32" y="682" font-size="14">after the round.</text>
<rect x="32" y="706" width="326" height="52" rx="12" fill="#E5F2E8"/>
<text x="48" y="738" font-size="14" font-weight="600">Ready to release</text>
<rect x="32" y="770" width="326" height="56" rx="12" fill="#216B3B"/>
<text x="195" y="805" font-size="16" font-weight="600" text-anchor="middle" fill="#FFFFFF">Release 51 L</text>
<path d="M32 861H358" stroke="#D7E3D8" stroke-dasharray="4 4"/>
<text x="32" y="891" font-size="14" fill="#526B59">Conditional reserve-control inset:</text>
<rect x="32" y="912" width="326" height="88" rx="12" fill="#FFF1D5"/>
<rect x="45" y="928" width="22" height="22" rx="3" fill="#FFFFFF" stroke="#865400"/>
<text x="79" y="944" font-size="14">Use N L from the</text><text x="79" y="966" font-size="14">protected reserve</text>
<text x="32" y="1032" font-size="13" fill="#526B59">Inset is explanatory, not simultaneous</text><text x="32" y="1053" font-size="13" fill="#526B59">content in this example model.</text>
<text x="32" y="1103" font-size="13" fill="#526B59">Final native card height follows content;</text><text x="32" y="1124" font-size="13" fill="#526B59">this drawing is not a height requirement.</text>
</g>
<g font-family="sans-serif" font-size="15" fill="#183A25" stroke="#216B3B" stroke-width="1">
<path d="M374 107H424"/><text x="440" y="112" stroke="none">Own opaque surface; radius 20; 1 border.</text>
<path d="M32 192H424"/><text x="440" y="197" stroke="none">16 inside padding; 12 between major sections.</text>
<path d="M358 346H424"/><text x="440" y="351" stroke="none">Native choices; semantic selected + enabled states.</text>
<path d="M358 580H424"/><text x="440" y="575" stroke="none">Summary derives from the supplied selected method.</text>
<text x="440" y="599" stroke="none">At narrow widths, stack label/value if needed.</text>
<path d="M358 801H424"/><text x="440" y="806" stroke="none">Typed release payload; no local model mutation.</text>
<path d="M358 951H424"/><text x="440" y="944" stroke="none">Consent only when reserve is needed and water fits.</text>
<text x="440" y="968" stroke="none">Caller replacement is the only consent echo.</text>
<text x="440" y="1020" stroke="none">Scale native type; wrap all long content.</text>
<text x="440" y="1044" stroke="none">Mirror leading/trailing for RTL, preserve order.</text>
<text x="440" y="1082" stroke="none">600-high native viewports require overlapping</text>
<text x="440" y="1106" stroke="none">scroll coverage to inspect the entire real component.</text>
</g>
</svg>"""
write(PUBLIC / "reference.svg", svg)

MEMBERS = list(example_model)
PLATFORMS = ["ios", "android"]
METHODS = {"ios":"ios.xcui.tap", "android":"android.compose.OnClick"}
COLORS = {
"light":{"surface":"#FFFFFF","border":"#D7E3D8","foreground":"#183A25","muted":"#526B59","accent":"#216B3B","accentOn":"#FFFFFF","selectedSurface":"#E5F2E8","warning":"#865400","warningSurface":"#FFF1D5","disabledSurface":"#E5EBE6","disabledText":"#65756A"},
"dark":{"surface":"#15251C","border":"#3B5242","foreground":"#E7F3E9","muted":"#B2C8B8","accent":"#81D89B","accentOn":"#102C19","selectedSurface":"#244F33","warning":"#FFD28A","warningSurface":"#493715","disabledSurface":"#293C2F","disabledText":"#92A396"}}
CATEGORY = {"business","visual","integration","source_api","capability"}
OBSERVATION_METHODS = {"callback","native_control","native_text","native_bounds","native_typography","pixels","visual","source_api"}

def model(**updates):
    m = copy.deepcopy(example_model)
    m.update(updates)
    return m

def env(width,theme,direction,font_scale,dynamic_type):
    return dict(width=width,height=600,component_offered_width=width-32,theme=theme,direction=direction,font_scale=font_scale,dynamic_type=dynamic_type,host_horizontal_padding=16,parent_canvas="platform_host_default")

def derive(m):
    required = m["bedCount"] * m["dripLitresPerBed" if m["selectedMethod"]=="drip" else "soakLitresPerBed"] + (m["dripPrimeLitres"] if m["selectedMethod"]=="drip" else 0)
    spendable = m["tankLitres"]-m["reserveLitres"]
    reserve_needed=max(0,required-spendable)
    shortfall=max(0,required-m["tankLitres"])
    common=m["isEnabled"] and not m["isSubmitting"]
    consent=reserve_needed>0 and shortfall==0
    release=common and shortfall==0 and (reserve_needed==0 or m["reserveAcknowledged"])
    if not m["isEnabled"]: status="Round paused"
    elif m["isSubmitting"]: status="Preparing release…"
    elif shortfall>0: status="Not enough water"
    elif reserve_needed>0 and not m["reserveAcknowledged"]: status="Approve reserve use"
    else: status="Ready to release"
    return dict(required=required,spendable=spendable,reserveNeeded=reserve_needed,remaining=max(0,m["tankLitres"]-required),shortfall=shortfall,common=common,consent=consent,release=release,status=status,progress=m["isEnabled"] and m["isSubmitting"])

def event_for(m, target):
    d=derive(m)
    if target.startswith("waterRound.method."):
        method=target.rsplit(".",1)[1]
        if not d["common"] or (method=="soak" and not m["soakAllowed"]) or method==m["selectedMethod"]: return []
        return [f'methodRequested|roundId={m["roundId"]}|method={method}']
    if target=="waterRound.reserveConsent":
        if not d["common"] or not d["consent"]: return []
        return [f'reserveAcknowledgementRequested|roundId={m["roundId"]}|acknowledged={str(not m["reserveAcknowledged"]).lower()}']
    if target=="waterRound.submit":
        if not d["release"]: return []
        return [f'releaseRequested|roundId={m["roundId"]}|method={m["selectedMethod"]}|bedCount={m["bedCount"]}|requestedLitres={d["required"]}|remainingLitres={d["remaining"]}|reserveUsedLitres={d["reserveNeeded"]}']
    raise ValueError(target)

def assertion(id, category, method, target, expected, stimulated=False, **more):
    return dict(id=id,category=category,method=method,target={"identifier":target},expected=expected,requires_stimulus=stimulated,source_only=False,**more)

def state_assertions(m, full, stimulated, environment):
    d=derive(m); a=[]
    def add(id,cat,method,target,expected,**extra):
        a.append(assertion(id,cat,method,target,expected,stimulated,**extra))
    for name in ("drip","soak"):
        target="waterRound.method."+name
        add("method."+name+".enabled","business","native_control",target,{"field":"enabled","equals":d["common"] and (name=="drip" or m["soakAllowed"])})
        add("method."+name+".selected","business","native_control",target,{"field":"selected","equals":m["selectedMethod"]==name})
    add("submit.enabled","business","native_control","waterRound.submit",{"field":"enabled","equals":d["release"]})
    add("status.text","business","native_text","waterRound.status",{"equals":d["status"]})
    for field,label in [("required","Required"),("spendable","Outside reserve"),("reserveNeeded","Reserve needed"),("remaining","Remaining")]:
        add("summary."+field+".text","business","native_text","waterRound."+field,{"equals":f'{label}: {d[field]} L'})
    add("shortfall.exists","business","native_control","waterRound.shortfall",{"field":"exists","equals":d["shortfall"]>0})
    if d["shortfall"]>0: add("summary.shortfall.text","business","native_text","waterRound.shortfall",{"equals":f'Shortfall: {d["shortfall"]} L'})
    add("consent.exists","business","native_control","waterRound.reserveConsent",{"field":"exists","equals":d["consent"]})
    if d["consent"]:
        add("consent.checked","business","native_control","waterRound.reserveConsent",{"field":"checked","equals":m["reserveAcknowledged"]})
        add("consent.enabled","business","native_control","waterRound.reserveConsent",{"field":"enabled","equals":d["common"]})
        add("consent.text","business","native_text","waterRound.reserveConsent",{"equals":f'Use {d["reserveNeeded"]} L from the protected reserve'})
    add("progress.exists","business","native_control","waterRound.progress",{"field":"exists","equals":d["progress"]})
    add("submit.text","business","native_text","waterRound.submit",{"equals":f'Release {d["required"]} L'})
    if not full: return a
    texts = {
      "title":m["title"],"description":m["description"],"beds":f'Beds: {m["bedCount"]}',
      "tank":f'Tank: {m["tankLitres"]} L',"reserve":f'Protected reserve: {m["reserveLitres"]} L',
      "dripPrime":f'Drip prime: {m["dripPrimeLitres"]} L'}
    if m["notice"]: texts["notice"]=m["notice"]
    for key,value in texts.items():
        add("content."+key+".text","integration","native_text","waterRound."+key,{"equals":value})
    add("notice.exists","integration","native_control","waterRound.notice",{"field":"exists","equals":bool(m["notice"])})
    for name,label in [("drip","Drip lines"),("soak","Soak hoses")]:
        add("method."+name+".label","integration","native_text","waterRound.method."+name,{"equals":f'{label}, {m[name+"LitresPerBed"]} L per bed',"field":"accessible_label"})
    add("layout.offeredWidth","visual","native_bounds","waterRound.root",{"field":"width","equals":environment["component_offered_width"],"unit":"logical","tolerance":1})
    add("layout.hostInsetLeading","integration","native_bounds","waterRound.root",{"field":"viewport_x_min","equals":16,"unit":"logical","tolerance":1})
    add("layout.fullContentCoverage","visual","visual","waterRound.root",{"coverage":"entire_component_top_to_bottom","native_overlapping_intervals":True,"minimum_overlap":24,"unit":"logical"})
    add("layout.noHorizontalOverflow","visual","native_bounds","waterRound.root",{"rule":"all_descendant_rendered_content_within_component_inner_horizontal_bounds","allow_native_focus_ring":True})
    add("layout.noTextTruncation","visual","visual","waterRound.root",{"rule":"every_displayed_string_complete_after_wrapping","ellipsis_allowed":False,"clipping_allowed":False})
    add("layout.sectionOrder","visual","visual","waterRound.root",{"ordered_sections":["title","description","facts","methods","summary","consent_if_visible","notice_if_nonempty","status","submit"]})
    add("layout.direction","visual","visual","waterRound.root",{"leading_trailing_direction":environment["direction"],"vertical_section_order_preserved":True})
    for name in ("drip","soak"):
        add("layout.method."+name+".minVisibleHeight","visual","native_bounds","waterRound.method."+name,{"field":"height","minimum":56,"unit":"logical"})
    add("layout.submit.minVisibleHeight","visual","native_bounds","waterRound.submit",{"field":"height","minimum":48,"unit":"logical"})
    if d["consent"]:
        add("layout.consent.minVisibleHeight","visual","native_bounds","waterRound.reserveConsent",{"field":"height","minimum":44,"unit":"logical"})
    c=COLORS[environment["theme"]]
    status_warn=d["status"]!="Ready to release"
    color_checks = [
      ("surface.fill","waterRound.root","fill",c["surface"]),
      ("surface.border","waterRound.root","border",c["border"]),
      ("title.foreground","waterRound.title","foreground",c["foreground"]),
      ("description.foreground","waterRound.description","foreground",c["muted"]),
      ("selected.fill","waterRound.method."+m["selectedMethod"],"fill",c["selectedSurface"]),
      ("selected.border","waterRound.method."+m["selectedMethod"],"border",c["accent"]),
      ("unselected.fill","waterRound.method."+("soak" if m["selectedMethod"]=="drip" else "drip"),"fill",c["surface"]),
      ("unselected.border","waterRound.method."+("soak" if m["selectedMethod"]=="drip" else "drip"),"border",c["border"]),
      ("submit.fill","waterRound.submit","fill",c["accent"] if d["release"] else c["disabledSurface"]),
      ("submit.foreground","waterRound.submit","foreground",c["accentOn"] if d["release"] else c["disabledText"]),
      ("status.fill","waterRound.status","container_fill",c["warningSurface"] if status_warn else c["selectedSurface"]),
      ("status.foreground","waterRound.status","foreground",c["warning"] if status_warn else c["foreground"])]
    for key,target,part,color in color_checks:
        add("style.color."+key,"visual","pixels",target,{"part":part,"rgb":color,"maximum_per_channel_error":4,"opaque":True})
    for key,target,part,value in [
      ("surface.radius","waterRound.root","corner_radius",20),
      ("surface.borderWidth","waterRound.root","border_width",1),
      ("method.drip.radius","waterRound.method.drip","corner_radius",12),
      ("method.soak.radius","waterRound.method.soak","corner_radius",12),
      ("method.drip.borderWidth","waterRound.method.drip","border_width",1),
      ("method.soak.borderWidth","waterRound.method.soak","border_width",1),
      ("submit.radius","waterRound.submit","corner_radius",12)]:
        add("style.geometry."+key,"visual","pixels",target,{"part":part,"equals":value,"unit":"logical","tolerance":1})
    # Exact padding, type, and physical hit areas remain explicit capability cells.
    pad_targets=[("card","waterRound.root",16),("drip","waterRound.method.drip",12),("soak","waterRound.method.soak",12),("submit","waterRound.submit",12)]
    for name,target,padding in pad_targets:
        for side in ("top","bottom","leading","trailing"):
            add("capability.padding."+name+"."+side,"capability","native_bounds",target,{"field":"internal_padding_"+side,"equals":padding,"unit":"logical","tolerance":0.5},capability="runtime_native_internal_padding",missing_native_evidence="U",forbidden_substitutes=["source_declaration","semantic_outer_bounds","screenshot_estimate"])
    for key,target,field,value in [
      ("title.size","waterRound.title","unscaled_font_size",20),
      ("title.weight","waterRound.title","font_weight","semibold"),
      ("description.size","waterRound.description","unscaled_font_size",14),
      ("description.weight","waterRound.description","font_weight","regular"),
      ("facts.size","waterRound.beds","unscaled_font_size",14),
      ("facts.weight","waterRound.beds","font_weight","regular"),
      ("summary.label.size","waterRound.required","label_unscaled_font_size",13),
      ("summary.label.weight","waterRound.required","label_font_weight","regular"),
      ("summary.value.size","waterRound.required","value_unscaled_font_size",17),
      ("summary.value.weight","waterRound.required","value_font_weight","semibold"),
      ("summary.value.digits","waterRound.required","value_digit_design","monospaced"),
      ("method.name.size","waterRound.method.drip","name_unscaled_font_size",16),
      ("method.name.weight","waterRound.method.drip","name_font_weight","semibold"),
      ("method.rate.size","waterRound.method.drip","rate_unscaled_font_size",14),
      ("method.rate.weight","waterRound.method.drip","rate_font_weight","regular"),
      ("submit.size","waterRound.submit","unscaled_font_size",16),
      ("submit.weight","waterRound.submit","font_weight","semibold"),
      ("status.size","waterRound.status","unscaled_font_size",14),
      ("status.weight","waterRound.status","font_weight","semibold")]:
        add("capability.typography."+key,"capability","native_typography",target,{"field":field,"equals":value},capability="runtime_native_typography",missing_native_evidence="U",forbidden_substitutes=["source_declaration","screenshot_estimate"])
    if m["notice"]:
        for field,value in [("unscaled_font_size",14),("font_weight","regular")]:
            add("capability.typography.notice."+field,"capability","native_typography","waterRound.notice",{"field":field,"equals":value},capability="runtime_native_typography",missing_native_evidence="U")
    if d["consent"]:
        for field,value in [("unscaled_font_size",14),("font_weight","regular")]:
            add("capability.typography.consent."+field,"capability","native_typography","waterRound.reserveConsent",{"field":field,"equals":value},capability="runtime_native_typography",missing_native_evidence="U")
    for target in ["waterRound.method.drip","waterRound.method.soak","waterRound.submit"]+(["waterRound.reserveConsent"] if d["consent"] else []):
        for dimension in ("width","height"):
            add("capability.hit."+target.rsplit(".",1)[1]+"."+dimension,"capability","native_bounds",target,{"field":"physical_hit_region_"+dimension,"minimum":44,"unit":"logical"},capability="native_physical_hit_region",missing_native_evidence="U",forbidden_substitutes=["semantic_bounds","successful_semantic_action","successful_single_coordinate_tap","source_declaration"])
    for name,target,value in [("sections","waterRound.root",12),("methodGap","waterRound.root",8),("summaryLabelValue","waterRound.required",8)]:
        add("capability.spacing."+name,"capability","native_bounds",target,{"field":name+"_spacing","minimum":value if name=="summaryLabelValue" else None,"equals":value if name!="summaryLabelValue" else None,"unit":"logical","tolerance":0.5},capability="runtime_native_internal_spacing",missing_native_evidence="U")
    add("capability.typography.appliedScaling","capability","native_typography","waterRound.root",{"android_font_scale":environment["font_scale"],"ios_dynamic_type":environment["dynamic_type"],"rule":"native_scaling_applied_to_all_text"},capability="runtime_native_accessibility_typography",missing_native_evidence="U")
    return a

cases=[]
def make_case(id,split,environment,initial,replacement,actions):
    assert set(initial)==set(MEMBERS)==set(replacement)
    checkpoints=[dict(id="initial",model="initial",full_content=True,trigger={"type":"initial"},assertions=state_assertions(initial,True,False,environment))]
    current_name="initial"; current=initial
    for number, action in enumerate(actions,1):
        cp_id=f"a{number:02d}"
        if action["type"]=="replaceModel":
            current_name="replacement"; current=replacement
            trigger={"type":"replaceModel","model":"replacement","requested_method":"caller.replaceModel"}
            callback=assertion("callback.events","integration","callback","waterRound.root",[],True,callback_gate="common_callback_gate",requires_successful_native_activation=False,requires_successful_caller_replacement=True,callback_interval="this_explicit_replacement_only",empty_interval_is_handler_proof=False)
            full=True
        else:
            trigger={"type":"activate","target":{"identifier":action["target"]},"requested_methods":METHODS.copy()}
            callback=assertion("callback.events","business","callback",action["target"],event_for(current,action["target"]),True,callback_gate="common_callback_gate",requires_successful_native_activation=True,requires_successful_caller_replacement=False,callback_interval="original_activation_only",empty_interval_is_handler_proof=False)
            full=False
        assertions=[callback]+state_assertions(current,full,True,environment)
        checkpoints.append(dict(id=cp_id,model=current_name,full_content=full,trigger=trigger,assertions=assertions))
    cases.append(dict(id=id,split=split,environment=environment,models={"initial":initial,"replacement":replacement},checkpoints=checkpoints))

def act(target): return {"type":"activate","target":target}
def replace(): return {"type":"replaceModel"}

c01=model(roundId="round_alder",title="Alder corner watering round",
 description="Six raised beds need a measured round before the afternoon volunteers arrive.",
 notice="Keep the shared path dry while the beds are watered.",bedCount=6,dripLitresPerBed=8,soakLitresPerBed=12,dripPrimeLitres=4,tankLitres=100,reserveLitres=20)
make_case("C01","initial",env(390,"light","ltr",1,"large"),c01,dict(c01,selectedMethod="soak"),[
 act("waterRound.submit"),act("waterRound.method.soak"),act("waterRound.submit"),replace(),act("waterRound.submit"),act("waterRound.method.drip")])

c02=model(roundId="round_cedar",title="جولة ري أحواض الأرز التعليمية قرب المدخل الشرقي",
 description="راجع كمية الماء لكل حوض قبل فتح الصمام. يبقى احتياطي الحديقة محمياً إلى أن يؤكد المشرف استخدامه، ويجب أن تظل جميع الملاحظات ظاهرة عند تكبير النص.",
 notice="اترك الممر متاحاً للزوار، وأعد الأدوات إلى مكانها بعد انتهاء هذه الجولة.",bedCount=5,dripLitresPerBed=10,soakLitresPerBed=14,dripPrimeLitres=0,tankLitres=70,reserveLitres=20,selectedMethod="soak")
make_case("C02","initial",env(320,"dark","rtl",1.3,"accessibility1"),c02,dict(c02,reserveAcknowledged=True),[
 act("waterRound.reserveConsent"),act("waterRound.reserveConsent"),replace(),act("waterRound.submit"),act("waterRound.reserveConsent"),act("waterRound.submit")])

c03=model(roundId="round_willow",title="Willow demonstration garden: the very long northern border beside the community workshop",
 description="This round covers the four teaching beds along the long workshop wall. Read the entire description and the reserve summary before releasing water; the card must grow as text scales so the final action remains reachable without losing any of these instructions.",
 notice="A volunteer may request a different method, but wait for the caller to confirm the new plan before treating the selection as changed.",bedCount=4,dripLitresPerBed=10,soakLitresPerBed=12,dripPrimeLitres=0,tankLitres=60,reserveLitres=20)
make_case("C03","initial",env(320,"light","ltr",1.6,"accessibility2"),c03,dict(c03,selectedMethod="soak",reserveAcknowledged=True),[
 act("waterRound.submit"),act("waterRound.method.soak"),replace(),act("waterRound.submit"),act("waterRound.reserveConsent"),act("waterRound.submit")])

c04=model(roundId="round_reed",title="Reed beds — steward pause",
 description="The steward has paused this round while the garden gate is being cleared.",
 notice="",bedCount=4,dripLitresPerBed=9,soakLitresPerBed=11,dripPrimeLitres=2,tankLitres=70,reserveLitres=10,isEnabled=False)
make_case("C04","initial",env(390,"dark","ltr",1,"large"),c04,dict(c04,roundId="round_reed_confirmed",title="Reed beds — release preparation",description="The caller is preparing the confirmed round. Wait for a new model before another request.",selectedMethod="soak",isEnabled=True,isSubmitting=True),[
 act("waterRound.method.soak"),act("waterRound.submit"),replace(),act("waterRound.method.drip"),act("waterRound.submit")])

h01=model(roundId="round_juniper",title="Juniper court — حديقة الساحة المشتركة",
 description="The seven small beds have different watering rates. The requested amount must fit inside the tank even when protected reserve use has already been acknowledged.",
 notice="Retain the note at the bottom of the card when the direction is right to left.",bedCount=7,dripLitresPerBed=11,soakLitresPerBed=10,dripPrimeLitres=4,tankLitres=80,reserveLitres=15,reserveAcknowledged=True)
make_case("H01","holdout",env(390,"light","rtl",1,"large"),h01,dict(h01,selectedMethod="soak"),[
 act("waterRound.submit"),act("waterRound.method.soak"),replace(),act("waterRound.submit"),act("waterRound.method.drip"),act("waterRound.submit")])

h02=model(roundId="round_ivy_before",title="Ivy terrace and the extremely long teaching strip beside the west fence and accessible garden entrance",
 description="The soak hoses are unavailable for this terrace. A requested reserve acknowledgement is only a request, and the steward may replace the entire round with different beds, identity, and tank numbers before releasing anything.",
 notice="Shared equipment remains in the garden. Read this complete note after changing the round and preserve the new caller identity in every delivered action.",bedCount=6,dripLitresPerBed=10,soakLitresPerBed=17,dripPrimeLitres=1,tankLitres=90,reserveLitres=30,soakAllowed=False)
h02r=dict(h02,roundId="round_ivy_after",title="Ivy terrace — caller replacement for three deeper beds",description="The caller has supplied a new round identity, three beds, a new drip rate, and one additional litre in the tank.",notice="Check the new identity and remaining amount before opening the supply.",bedCount=3,dripLitresPerBed=20,tankLitres=91,reserveAcknowledged=False)
make_case("H02","holdout",env(320,"dark","ltr",1.3,"xxxLarge"),h02,h02r,[
 act("waterRound.method.soak"),act("waterRound.reserveConsent"),act("waterRound.reserveConsent"),replace(),act("waterRound.submit"),act("waterRound.method.drip"),act("waterRound.submit")])

source_assertions=[]
def source(platform,id,target,expected):
    source_assertions.append(dict(id=id,platform=platform,category="source_api",method="source_api",target={"identifier":target},expected=expected,requires_stimulus=False,source_only=True))
for p in PLATFORMS:
    source(p,"production.location","WaterRoundReleaseView" if p=="ios" else "WaterRoundRelease",{"module":"AlertToast" if p=="ios" else "Reply","package":None if p=="ios" else "com.example.reply.ui.waterround","production_not_host":True})
    source(p,"entry.model","WaterRoundReleaseView" if p=="ios" else "WaterRoundRelease",{"parameter":"model","public_type":"WaterRoundModel","required":True})
    source(p,"entry.callback","WaterRoundReleaseView" if p=="ios" else "WaterRoundRelease",{"parameter":"onAction","type":"(WaterRoundAction) -> Void" if p=="ios" else "(WaterRoundAction) -> Unit","public":True})
    source(p,"model.public","WaterRoundModel",{"public":True,"immutable":True,"required_initializer_members":MEMBERS})
    source(p,"method.values","WateringMethod",{"public":True,"values":["drip","soak"]})
    source(p,"actions.typed","WaterRoundAction",{"public":True,"kind":"enum_with_associated_values" if p=="ios" else "sealed_interface_with_data_classes","alternatives":["methodRequested","reserveAcknowledgementRequested","releaseRequested"]})
    source(p,"bridge.actual_entry","bridge",{"rule":"decode construct call production serialize actual typed callback only"})
    for forbidden in ["business_validation","amount_calculation","eligibility_calculation","UI_rendering","callback_synthesis","model_mutation","fallback_default"]:
        source(p,"bridge.forbid."+forbidden,"bridge",{"forbidden":forbidden})
    if p=="ios":
        source(p,"compatibility.ios","AlertToast",{"minimum_source_deployment":"iOS 14","unguarded_later_API":False})
        source(p,"compatibility.macos","AlertToast",{"minimum_source_deployment":"macOS 11","unguarded_later_API":False})
    else:
        source(p,"entry.modifier","WaterRoundRelease",{"parameter":"modifier","type":"Modifier","default":"Modifier","honored":True})
    for member in MEMBERS:
        typ = "String" if isinstance(example_model[member],str) else ("Bool" if p=="ios" else "Boolean") if isinstance(example_model[member],bool) else "Int"
        if member=="selectedMethod":typ="WateringMethod"
        source(p,"model.member."+member,"WaterRoundModel."+member,{"name":member,"type":typ,"public":True,"immutable":True,"required":True})
        source(p,"bridge.member."+member,"bridge.model."+member,{"rule":"exact required JSON member decoded and passed to the same public constructor member","member":member,"fallback":False})
    payloads={
      "methodRequested":{"roundId":"String","method":"WateringMethod"},
      "reserveAcknowledgementRequested":{"roundId":"String","acknowledged":"Bool" if p=="ios" else "Boolean"},
      "releaseRequested":{"roundId":"String","method":"WateringMethod","bedCount":"Int","requestedLitres":"Int","remainingLitres":"Int","reserveUsedLitres":"Int"}}
    for alternative, members in payloads.items():
        for member,typ in members.items():
            source(p,"action."+alternative+"."+member,"WaterRoundAction."+alternative+"."+member,{"name":member,"type":typ,"public_typed_payload":True})
    source(p,"callback.serialization","bridge.serialize",{"format":"ordered tokens exactly as public api.md","typed_input":"WaterRoundAction","preserve_event_order":True,"synthesize_missing_callbacks":False})

oracle={
 "version":1,"feature":"WaterRound","design_independence":"Only PLAN-CONTRACT.md was read before this design was authored. No tool schema, implementation, previous validation, source, scores, failures, root README, or generic probes were read.",
 "units":"integer litres; logical points on iOS and dp on Android",
 "platforms":PLATFORMS,"native_activation_routes":METHODS,
 "callback_gate_contract":{"import_required":"common_callback_gate","no_local_override":True,"callback_P_or_F_requires_gate_allow":True,"blocked_or_unavailable_activation":"U","successful_explicit_caller_replacement_can_establish_quietness":True,"empty_events_do_not_prove_handler_execution":True},
 "stimulus_contract":{"post_action_requires_stimulus":True,"activation_requires_native_success":True,"replacement_requires_explicit_success":True,"navigation_is_not_activation":True,"callback_interval_preserved_before_visual_sweep":True},
 "capability_contract":{"runtime_native_typography":"U without direct runtime native facts","runtime_native_internal_padding":"U without direct runtime native facts","native_physical_hit_region":"U without direct runtime physical hit-region facts","separate_from_business_miss_metrics":True},
 "cases":cases,"source_assertions":source_assertions
}
write(PRIVATE / "oracle.json",oracle)

runtime_rows=[]; input_rows=[]; source_rows=[]
for case in cases:
    for cp in case["checkpoints"]:
        for p in PLATFORMS:
            stim=cp["trigger"]["type"]!="initial"
            trigger=copy.deepcopy(cp["trigger"])
            if trigger["type"]=="activate":
                trigger["requested_method"]=METHODS[p];trigger.pop("requested_methods",None)
            requirement=dict(platform=p,case=case["id"],checkpoint=cp["id"],split=case["split"],model=cp["model"],full_content=cp["full_content"],trigger=trigger)
            for member in MEMBERS:
                input_rows.append({
                    "key":f'{p}/{case["id"]}/{cp["id"]}/input/{member}',
                    **requirement,"id":"input."+member,"category":"integration","method":"source_api",
                    "target":{"identifier":"WaterRoundModel."+member},
                    "expected":{"member":member,"value":case["models"][cp["model"]][member],"provenance":"exact immutable test input at this epoch; native behavior is evaluated only in separate runtime rows"},
                    "requires_stimulus":stim,"source_only":True,
                    "evidence_scope":"input_decode_and_constructor_provenance_only",
                    "cannot_establish":["business_behavior","visual_style","native_typography","native_hit_region","native_internal_padding"]
                })
            for a in cp["assertions"]:
                row={"key":f'{p}/{case["id"]}/{cp["id"]}/{a["id"]}',**requirement,**copy.deepcopy(a)}
                if row["method"]=="callback":
                    row["requested_method"]=METHODS[p] if trigger["type"]=="activate" else "caller.replaceModel"
                if row["category"]=="capability":
                    row["metric_bucket"]="capability_U_separate_from_business"
                elif row["category"]=="business":row["metric_bucket"]="business_behavior"
                elif row["category"]=="visual":row["metric_bucket"]="visual_style"
                else:row["metric_bucket"]="integration"
                runtime_rows.append(row)
for a in source_assertions:
    source_rows.append({"key":f'{a["platform"]}/source_api/{a["id"]}',"case":None,"checkpoint":None,**copy.deepcopy(a),"metric_bucket":"source_api_separate"})

plan={
 "version":1,"feature":"WaterRound","platforms":PLATFORMS,
 "row_contract":{"all_keys_unique":True,"atomic_member_rows":True,"source_api_separate":True,"post_stimulus_gate_required":True,"callback_gate_import_required":"common_callback_gate","callback_gate_must_not_be_reimplemented_or_overridden":True,"unavailable_native_facts_grade":"U","required_grade_values":["P","F","U"],"mandatory_evidence_fields":["native_stimulus_locator_for_post_stimulus_rows","original_native_fields_or_pixels_locator","callback_interval_locator_for_callback_rows"],"independent_evaluator_preparation":"Source-independent executable evaluator and concrete evidence adapters must be frozen in a subsequent explicitly authorized preparation phase, before builders start. This design does not inspect tools or candidate source."},
 "input_member_rows":input_rows,"runtime_rows":runtime_rows,"source_api_rows":source_rows
}
write(PRIVATE / "expanded-plan.json",plan)

validation_errors=[]
for case in cases:
    if len(case["models"])>2:validation_errors.append(case["id"]+": model limit")
    actions=[cp for cp in case["checkpoints"] if cp["trigger"]["type"]!="initial"]
    if len(actions)>8:validation_errors.append(case["id"]+": action limit")
    if sum(cp["full_content"] for cp in case["checkpoints"])>2:validation_errors.append(case["id"]+": full checkpoint limit")
    for name,m in case["models"].items():
        if set(m)!=set(MEMBERS):validation_errors.append(case["id"]+"/"+name+": member set")
        if m["selectedMethod"]=="soak" and not m["soakAllowed"]:validation_errors.append(case["id"]+": invalid selected method")
        if not 0<=m["reserveLitres"]<=m["tankLitres"]<=200000:validation_errors.append(case["id"]+": tank domain")
        for cp in case["checkpoints"]:
            for p in PLATFORMS:
                prefix=f'{p}/{case["id"]}/{cp["id"]}/input/'
                found={r["id"].split(".",1)[1] for r in input_rows if r["key"].startswith(prefix)}
                if found!=set(MEMBERS):validation_errors.append(prefix+": missing atomic member")
all_rows=input_rows+runtime_rows+source_rows
keys=[r["key"] for r in all_rows]
if len(keys)!=len(set(keys)):validation_errors.append("duplicate expanded key")
for row in all_rows:
    for required in ["platform","category","method","expected","target","source_only","requires_stimulus"]:
        if required not in row:validation_errors.append(row["key"]+": missing "+required)
    if row["platform"] not in PLATFORMS:validation_errors.append(row["key"]+": platform")
    if row["category"] not in CATEGORY:validation_errors.append(row["key"]+": category")
    if row["method"] not in OBSERVATION_METHODS:validation_errors.append(row["key"]+": method")
    if not row["target"].get("identifier"):validation_errors.append(row["key"]+": target")
    if row in runtime_rows:
        if row["trigger"]["type"]!="initial" and not row["requires_stimulus"]:validation_errors.append(row["key"]+": post-stimulus not gated")
        if row["method"]=="callback" and row.get("callback_gate")!="common_callback_gate":validation_errors.append(row["key"]+": callback gate")
        if row["method"]=="callback" and not row.get("requested_method"):validation_errors.append(row["key"]+": native method")
        if row["category"]=="capability" and row.get("missing_native_evidence")!="U":validation_errors.append(row["key"]+": capability fallback")
for p in PLATFORMS:
    for case in cases:
        caps={r.get("capability") for r in runtime_rows if r["platform"]==p and r["case"]==case["id"]}
        for c in ["runtime_native_typography","runtime_native_internal_padding","native_physical_hit_region"]:
            if c not in caps:validation_errors.append(p+"/"+case["id"]+": missing "+c)
if validation_errors:raise RuntimeError(json.dumps(validation_errors))
report={
 "validated_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "status":"PASS","candidate_source_or_evidence_read":False,
 "checks":["public/private separation","C01-C04 and H01-H02 frozen","at most two models per case","at most eight actions per case","at most two full checkpoints per case","every parameter member expanded at every platform/case/checkpoint","unique expanded keys","required row members present","only ios/android platforms","callback native stimulus and common gate required","all post-stimulus runtime rows require demonstrated transition","source/API rows separate","typography/padding/physical hit capability U retained"],
 "counts":{"cases":len(cases),"initial_cases":4,"holdout_cases":2,"models":sum(len(c["models"]) for c in cases),"actions":sum(len(c["checkpoints"])-1 for c in cases),"full_content_checkpoints":sum(cp["full_content"] for c in cases for cp in c["checkpoints"]),"expanded_input_member_rows":len(input_rows),"expanded_runtime_rows":len(runtime_rows),"expanded_source_api_rows":len(source_rows),"expanded_total_rows":len(all_rows),"capability_rows":sum(r["category"]=="capability" for r in runtime_rows)},
 "per_case":[{"id":c["id"],"model_count":len(c["models"]),"action_count":len(c["checkpoints"])-1,"full_content_checkpoint_count":sum(cp["full_content"] for cp in c["checkpoints"])} for c in cases],
 "errors":[]
}
write(PRIVATE / "validation-report.json",report)

files=[]
for directory in (PUBLIC, PRIVATE):
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.name!="SEAL.json":
            data=path.read_bytes()
            files.append({"path":str(path.relative_to(BASE)),"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),"mtime_utc":datetime.datetime.fromtimestamp(path.stat().st_mtime,datetime.timezone.utc).isoformat()})
payload={
 "version":1,"feature":"WaterRound","sealed_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "design_independent_of_tools_and_candidates":True,
 "hash_algorithm":"SHA-256",
 "commitment_encoding":"UTF-8 canonical JSON of the payload object (sort_keys=True,separators=(',',':'),ensure_ascii=False)",
 "files":sorted(files,key=lambda x:x["path"]),
 "counts":report["counts"],
 "scope":"All design/public and design/private files except this self-describing SEAL.json envelope. No tool schema or candidate implementation was read before sealing."
}
canonical=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
commitment=hashlib.sha256(canonical).hexdigest()
write(PRIVATE / "SEAL.json",{"commitment_sha256":commitment,"payload":payload})
print(json.dumps({"public_directory":str(PUBLIC),"private_directory":str(PRIVATE),"file_count":len(files)+1,"counts":report["counts"],"commitment_sha256":commitment,"sealed_at_utc":payload["sealed_at_utc"]},indent=2))
