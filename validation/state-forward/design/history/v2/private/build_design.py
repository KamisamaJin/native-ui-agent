from pathlib import Path
import json, copy, html
ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'public'; PRIV=ROOT/'private'
def write(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n' if not isinstance(data,str) else data)
def job(id,title,pages,copies=1,color=False,selected=False,locked=False):
    return dict(id=id,title=title,pages=pages,copies=copies,isColor=color,selected=selected,locked=locked)
def model(id,budget,jobs,mode='single',priority=False,expanded=False,allow=True):
    return dict(modelID=id,budgetCredits=budget,allowPriority=allow,initialPaperMode=mode,initialPriority=priority,initialExpanded=expanded,jobs=jobs)
def act(target): return dict(type='activate',targetID='printbatch.'+target)
def repl(idx): return dict(type='replaceModel',modelIndex=idx)
def case(id,width,dark,scale,rtl,models,actions,full):
    return dict(caseID=id,host=dict(width=width,height=600,theme='dark' if dark else 'light',textScale=scale,direction='rtl' if rtl else 'ltr'),models=models,initial=dict(stateID=id+'.s0',full_content=0 in full),actions=[dict(a,actionIndex=i,stateID=f'{id}.s{i}',full_content=i in full) for i,a in enumerate(actions,1)])
public=[
case('P1',390,False,1,False,[model('P1-A',60,[job('agenda','Meeting agenda',8,2,selected=True),job('cover','Color cover',5,color=True,selected=True),job('notes','Desk notes',3)])],[act('breakdown.toggle'),act('mode.duplex'),act('priority'),act('approve')],{0,4}),
case('P2',320,True,1,False,[model('P2-A',30,[job('report','Operations report',12,selected=True),job('poster','Color posters',4,2,True,True),job('note','One-page note',1)])],[act('approve'),act('job.poster.toggle'),act('priority'),act('breakdown.toggle'),act('approve')],{0,5}),
case('P3',320,False,1.2,False,[model('P3-A',12,[job('field','Field notes',2,2),job('legal','Legal master',3,locked=True),job('proof','Color proof',1,color=True)],'duplex',expanded=True)],[act('priority'),act('job.legal.toggle'),act('job.field.toggle'),act('priority'),act('approve')],{0,5}),
case('P4',390,True,1,True,[model('P4-A',50,[job('board','Board packet',6,selected=True),job('study','Cover study',2,2,True),job('appendix','Appendix',5,selected=True)],priority=True,expanded=True),model('P4-B',18,[job('board','Board packet v2',4),job('study','Cover study v2',3,color=True,selected=True),job('appendix','Appendix v2',8,locked=True)],'duplex',allow=False)],[act('job.study.toggle'),act('mode.duplex'),act('breakdown.toggle'),repl(1),act('approve')],{0,4})]
held=[
case('H1',320,True,1.2,False,[model('H1-A',8,[job('safety','Safety checklist',2,selected=True,locked=True),job('reference','Reference color',1,color=True,selected=True),job('spare','Spare copy',3)],allow=False),model('H1-B',9,[job('safety','Safety checklist v2',3,selected=True,locked=True),job('reference','Reference color v2',2,color=True),job('spare','Spare copy v2',4)],'duplex',True,True)],[act('priority'),act('job.safety.toggle'),act('job.reference.toggle'),repl(1),act('priority'),act('approve')],{0,4}),
case('H2',390,False,1,True,[model('H2-A',13,[job('handbook','Quarterly workshop participant handbook',5,selected=True),job('sample','Front-cover color sample',2,color=True),job('archive','Do not print: retained archive',2,locked=True)],'duplex',True,True)],[act('job.handbook.toggle'),act('mode.duplex'),act('job.handbook.toggle'),act('priority'),act('breakdown.toggle'),act('approve')],{0,6})]
write(PUB/'cases.json',dict(schemaVersion=1,cases=public))
write(PRIV/'heldout-cases.json',dict(schemaVersion=1,cases=held))
brief='''# Print Batch Approval — fixed public brief

Build one reusable native card in each pinned production module. A small office reviews a print batch against a credit budget before approving it. The card must remain coherent as jobs, printing mode and handling change, and when its caller supplies a replacement model. Both platforms implement this same behavior and API. No network, persistence, timers or random behavior is needed.

The host is 320 or 390 logical units wide and 600 high. It gives the card a child width of host width minus 32, with 16 units outside each side. The common native host owns the vertical ScrollView/ScrollState and reaches all content in its 600-high viewport. The card is intrinsic-height content inside that existing scroller; do not add a nested vertical scroller. Content order is title/status, large charge and summary, jobs, paper mode, priority, expandable breakdown, balance, approval. The screenshot reference is a design specification created before implementation; it is not an implementation golden. Files in this public folder are the complete builder inputs; private holdouts combine these rules without adding rules.

## Models and local state

Every batch has exactly three jobs in model order. IDs are unique lowercase slugs. Every job has a title, pages per copy, copy count, color flag, initial selected flag and locked flag. Local selection starts from those flags. A locked job cannot be toggled; its selected value can be either true or false. Locked does not exclude a selected job from calculations. The two paper modes are `single` and `duplex`. Priority and breakdown expansion start from model defaults. Mode controls stay enabled even with no jobs selected. Tapping the already selected paper mode dispatches normally but changes nothing and emits no event.

A caller replacement with a different modelID atomically resets selection, mode, priority and expansion from the new model, updates every label and enablement fact, and emits no component event. Jobs can retain IDs while their other fields change. Treat a new modelID as a complete replacement. The supplied fixtures always use distinct modelIDs and allowPriority=false always has initialPriority=false.

## Exact calculations

For each selected job, printedPages = pages * copies. Ink costs 1 credit per printed mono page and 3 credits per printed color page. In single mode, sheets = pages * copies; in duplex mode, sheets = ceil(pages / 2) * copies (round within each copy). Paper costs 1 credit per sheet. An individual row's displayed cost is ink plus paper for that job in the current mode, whether selected or not. Priority adds 6 credits once per batch only when at least one job is selected and priority is on. Total = selected ink + selected paper + priority. No selected jobs means all calculated sums, including priority charge, are zero. The priority on/off value itself persists when the final selected job is deselected. Selecting a job again restores the surcharge if that value is still on.

Approval is enabled exactly when selected count > 0 and total <= budgetCredits. Priority is enabled exactly when allowPriority and selected count > 0. A disabled activation emits no event; observing its current disabled state does not establish an exercised handler. Job toggles are enabled exactly when not locked. Breakdowns and mode controls are always enabled. Every successful state-changing activation emits exactly one corresponding event; approval emits its event without clearing or changing local state. Replacement emits none. See API.md for payloads and native identifiers.

## Exact visible copy

Use English strings below verbatim; interpolate decimal integers without grouping and always use the words `jobs`, `pages`, `sheets`, `copies` even at 1.

- Title: `Print budget check`; charge caption: `Estimated charge`; large charge: `{total} cr`.
- Summary: `{count} jobs • {printedPages} pages • {sheets} sheets`.
- Badge: `No jobs` if count=0, else `Over budget` if total>budget, else `Ready`.
- Each job title is its model title. Subtitle: `{pages} pages × {copies} copies • {Color|Mono}` followed by ` • Locked` for locked jobs. Row price: `{ink+paper} cr`.
- Selection control accessibility name: `Select {title}` when unselected and `Deselect {title}` when selected. Its checked/selected state must be available natively.
- Mode section title: `Paper mode`; buttons: `Single-sided` and `Duplex`. Expose the selected mode natively.
- Priority control label: `Priority handling`. Helper: `Priority unavailable for this batch.` if allowPriority=false; else `Adds 6 cr to this batch.` if priority=true; else `Add 6 cr for priority handling.` This helper describes the persisted choice even when count=0. Expose the on/off and enabled state natively.
- Breakdown toggle: `Show cost breakdown` when collapsed; `Hide cost breakdown` when expanded. Expanded contents are four ordered rows labelled `Ink`, `Paper`, `Priority`, `Total` with values `{ink} cr`, `{sheets} cr`, `{surcharge} cr`, `{total} cr`. Collapsed contents are absent from the native tree, not merely transparent.
- Balance: `No charge selected` if count=0; else `Short by {total-budget} cr` if over budget; else `Balance after approval: {budget-total} cr`.
- Approval: `Select a job to approve` if count=0; else `Over budget by {total-budget} cr` if over budget; else `Approve {count} jobs · {total} cr`.

## Visual and accessibility requirements

Use the exact palette and typography tokens in reference.svg. Light: background #F5F7FA, surface #FFFFFF, primary text #14243A, muted #53657A, accent #265FE4, ready #167650, error #B63835. Dark: background #10161F, surface #1B2532, primary text #F2F5FA, muted #B7C4D5, accent #8BB0FF, ready #75D6AA, error #FF9A96. A ready badge uses ready; an over-budget badge and shortfall use error; no-jobs badge uses muted. Selected mode and enabled approval use accent fill, with #FFFFFF foreground in light and #14243A foreground in dark. Unselected mode uses surface fill and primary text. Selected job indicators and on priority indicators use accent. Disabled controls use muted text and a visibly subdued surface; their labels remain legible. Separators use muted at 25% alpha. No decorative imagery is required.

Use system sans-serif. Token sizes before textScale: title 20 semibold, charge 28 bold, body/control/row title 14 (controls and row titles semibold), caption/helper/subtitle/breakdown 12 regular, badge 12 semibold. Multiply point/sp size by host textScale (1 or 1.2); do not also multiply by another automatic scale. The title and large charge have distinct hierarchy. Long labels and summaries wrap; no required text is truncated or horizontally clipped. Rows expand vertically as needed. Values and relevant labels remain clearly associated, and content does not overlap at either width or scale.

Card surface corner radius 16. Card content padding 16. Section spacing 12. Job rows have 12 vertical units of padding and a separator between rows. The header title is leading and badge trailing; charge and summary align leading. Job selection is leading, text in the middle and price trailing. The approval spans available inner width with radius 10 and minimum height 48; other interactive controls have semantic bounds at least 48 by 48 logical units, enlarging unobtrusive bounds if needed. Provide separate stable identifiers for text and interactive elements. No overlay intercepts another control. A reachable native semantic action and a physical hit region are different aspects.

Respect the supplied RTL direction: leading/trailing alignment and row/section order mirror, including title/badge, selection/text/price and mode order. English words and numbers remain readable. The vertical content order stays unchanged. The card must show the chosen light/dark palette, all selected states, disabled states and expansion state in actual native rendering. Every public and held-out state, including offscreen targets, belongs to acceptance; unsupported inspection remains unknown rather than being omitted.

## Cases and checkpoints

cases.json contains inputs and actions only. Initial checkpoint is action index 0. Each actionIndex N leads to the exactly named stateID `{caseID}.s{N}`. `full_content=true` requests bounded scroll coverage of all native content for that checkpoint; it does not mean one screenshot must contain all content. Other checkpoints still include every relevant state aspect in acceptance, and available target evidence may be reused only within that same state revision. Every case uses at most two models, eight non-sweep actions and two full-content checkpoints. Non-sweep actions are activated once, with no retries to inflate callback evidence. The harness may scroll to reach an exact target. Preserve uncertain/missing/ambiguous target outcomes.
'''
write(PUB/'BRIEF.md',brief)
api='''# Fixed native API and observer contract

Exact production files, relative to the pinned repositories:

- Reply: `app/src/main/java/com/example/reply/ui/printbatch/PrintBatchApprovalCard.kt`; Kotlin package `com.example.reply.ui.printbatch`.
- AlertToast: `Sources/AlertToast/PrintBatchApprovalCard.swift`; Swift module `AlertToast`.

These files are the production implementations. Bridges call these components directly. Do not duplicate a product implementation inside a bridge.

## Kotlin public declarations

```kotlin
data class PrintBatchJob(val id: String, val title: String, val pages: Int, val copies: Int, val isColor: Boolean, val selected: Boolean, val locked: Boolean)
data class PrintBatchModel(val modelID: String, val budgetCredits: Int, val allowPriority: Boolean, val initialPaperMode: String, val initialPriority: Boolean, val initialExpanded: Boolean, val jobs: List<PrintBatchJob>)
data class PrintBatchPresentation(val isDark: Boolean, val textScale: Double, val isRTL: Boolean)
@Composable
fun PrintBatchApprovalCard(
    model: PrintBatchModel,
    presentation: PrintBatchPresentation,
    onEvent: (String, Map<String, Any>) -> Unit,
    modifier: Modifier = Modifier
)
```

## Swift public declarations

All fields and initializers are public. Models may conform to Equatable/Hashable as helpful.

```swift
public struct PrintBatchJob {
    public let id: String; public let title: String
    public let pages: Int; public let copies: Int
    public let isColor: Bool; public let selected: Bool; public let locked: Bool
    public init(id: String, title: String, pages: Int, copies: Int, isColor: Bool, selected: Bool, locked: Bool)
}
public struct PrintBatchModel {
    public let modelID: String; public let budgetCredits: Int
    public let allowPriority: Bool; public let initialPaperMode: String
    public let initialPriority: Bool; public let initialExpanded: Bool
    public let jobs: [PrintBatchJob]
    public init(modelID: String, budgetCredits: Int, allowPriority: Bool, initialPaperMode: String, initialPriority: Bool, initialExpanded: Bool, jobs: [PrintBatchJob])
}
public struct PrintBatchPresentation {
    public let isDark: Bool; public let textScale: Double; public let isRTL: Bool
    public init(isDark: Bool, textScale: Double, isRTL: Bool)
}
public struct PrintBatchApprovalCard: View {
    public init(model: PrintBatchModel, presentation: PrintBatchPresentation, onEvent: @escaping (String, [String: Any]) -> Void)
    public var body: some View { get }
}
```

`initialPaperMode` accepts only `single` or `duplex`. The callback name and payload are separate parameters. Payload is a JSON-compatible dictionary. The observer adapter serializes it as one JSON object `{"name":name,"payload":payload}`. Integer values remain integers. Job IDs in callbacks are in current model order, with no duplicates.

## Callbacks

- `selectionChanged`: `{"jobIDs":[all currently selected job IDs]}`.
- `paperModeChanged`: `{"paperMode":"single"|"duplex"}`.
- `priorityChanged`: `{"priority":true|false}`.
- `breakdownChanged`: `{"expanded":true|false}`.
- `approve`: `{"modelID":current modelID,"jobIDs":[selected IDs],"paperMode":"single"|"duplex","priority":current persisted boolean,"totalCredits":total,"printedPages":printedPages,"sheets":sheets}`.

Each changing enabled activation produces exactly one event of its corresponding name and payload; approval produces exactly one approve event without changing state. Already-selected mode produces zero events. Disabled activation and caller replacement produce zero component events. Programmatic reset does not emit selection/mode/priority/breakdown events.

## Exact native identifiers

SwiftUI uses accessibilityIdentifier; Compose uses testTag, with those tags exposed as native resource identifiers for the observer. Keep identifiers unique and do not place the same identifier on a parent and child. Every named text value has a separate observable native text node. Identifiers are stable across model replacement. The semantic root may contain children; do not merge all contents into one inaccessible label.

| Identifier | Native meaning / accessibility name |
| --- | --- |
| printbatch.card | Intrinsic-height component content root inside the host scroller |
| printbatch.title | `Print budget check` |
| printbatch.status | Current badge text |
| printbatch.charge.caption | `Estimated charge` |
| printbatch.charge.value | `{total} cr` |
| printbatch.summary | Exact current summary |
| printbatch.job.ID.toggle | Checkbox/selection action; `Select TITLE` / `Deselect TITLE`, native checked/selected and enabled state |
| printbatch.job.ID.title | Model title |
| printbatch.job.ID.subtitle | Exact subtitle |
| printbatch.job.ID.price | Current per-job price |
| printbatch.mode.title | `Paper mode` |
| printbatch.mode.single | Button `Single-sided`, selected state |
| printbatch.mode.duplex | Button `Duplex`, selected state |
| printbatch.priority | Switch/toggle `Priority handling`, native checked/on and enabled state |
| printbatch.priority.helper | Exact helper text |
| printbatch.breakdown.toggle | Button with exact Show/Hide label and native expanded state or accessibility value `Expanded` / `Collapsed` |
| printbatch.breakdown.ink.label | `Ink` (expanded only) |
| printbatch.breakdown.ink.value | `{ink} cr` (expanded only) |
| printbatch.breakdown.paper.label | `Paper` (expanded only) |
| printbatch.breakdown.paper.value | `{sheets} cr` (expanded only) |
| printbatch.breakdown.priority.label | `Priority` (expanded only) |
| printbatch.breakdown.priority.value | `{surcharge} cr` (expanded only) |
| printbatch.breakdown.total.label | `Total` (expanded only) |
| printbatch.breakdown.total.value | `{total} cr` (expanded only) |
| printbatch.balance | Exact current balance/shortfall text |
| printbatch.approve | Button with exact current approval label and native enabled state |

`ID` is replaced literally by the current job ID. Controls expose one unambiguous exact native activation target. Use native checkbox/switch/button roles and value/selected attributes, or an exact native accessibilityValue `Selected` / `Not selected`, `On` / `Off`, `Expanded` / `Collapsed` where a framework lacks the matching standard attribute. Absence checks require completed bounded content coverage and cannot be inferred from a single viewport.

## Fixture and action wire format

The JSON Schema is input.schema.json. cases.json contains only host configuration, model inputs, initial checkpoint and action inputs. Bridge.swift and ObserverBridge.kt are adapter examples, not implementations. A bridge accepts `{"host":host,"model":activeModel}`; for convenience it also accepts a whole case with `models` and optional `activeModelIndex` (default 0). Caller replacement must preserve the production component's position/identity while supplying the new model, so replacement handling is exercised in production code. The host applies 16 external horizontal units, height 600, and supplies native screenshot/semantic collection; the host owns the only vertical scroll container; the component supplies intrinsic-height content without a nested vertical scroller.

The observation normalization contract and the evaluator's capability policy are frozen privately before implementation. No runtime result is inferred from a product source declaration. Public AX does not provide arbitrary SwiftUI font, padding, color or physical hit-region inspection.
'''
write(PUB/'API.md',api)
model_schema={'type':'object','additionalProperties':False,'required':['modelID','budgetCredits','allowPriority','initialPaperMode','initialPriority','initialExpanded','jobs'],'properties':{'modelID':{'type':'string','minLength':1},'budgetCredits':{'type':'integer','minimum':0,'maximum':9999},'allowPriority':{'type':'boolean'},'initialPaperMode':{'enum':['single','duplex']},'initialPriority':{'type':'boolean'},'initialExpanded':{'type':'boolean'},'jobs':{'type':'array','minItems':3,'maxItems':3,'items':{'type':'object','additionalProperties':False,'required':['id','title','pages','copies','isColor','selected','locked'],'properties':{'id':{'type':'string','pattern':'^[a-z][a-z0-9_-]*$'},'title':{'type':'string','minLength':1},'pages':{'type':'integer','minimum':1,'maximum':100},'copies':{'type':'integer','minimum':1,'maximum':5},'isColor':{'type':'boolean'},'selected':{'type':'boolean'},'locked':{'type':'boolean'}}}}}}
host_schema={'type':'object','additionalProperties':False,'required':['width','height','theme','textScale','direction'],'properties':{'width':{'enum':[320,390]},'height':{'const':600},'theme':{'enum':['light','dark']},'textScale':{'enum':[1,1.2]},'direction':{'enum':['ltr','rtl']}}}
cp_schema={'type':'object','additionalProperties':False,'required':['stateID','full_content'],'properties':{'stateID':{'type':'string'},'full_content':{'type':'boolean'}}}
action_schema={'oneOf':[{'type':'object','additionalProperties':False,'required':['type','targetID','actionIndex','stateID','full_content'],'properties':{'type':{'const':'activate'},'targetID':{'type':'string','pattern':'^printbatch\\.'},'actionIndex':{'type':'integer','minimum':1,'maximum':8},'stateID':{'type':'string'},'full_content':{'type':'boolean'}}},{'type':'object','additionalProperties':False,'required':['type','modelIndex','actionIndex','stateID','full_content'],'properties':{'type':{'const':'replaceModel'},'modelIndex':{'type':'integer','minimum':0,'maximum':1},'actionIndex':{'type':'integer','minimum':1,'maximum':8},'stateID':{'type':'string'},'full_content':{'type':'boolean'}}}]}
case_schema={'type':'object','additionalProperties':False,'required':['caseID','host','models','initial','actions'],'properties':{'caseID':{'type':'string'},'host':host_schema,'models':{'type':'array','minItems':1,'maxItems':2,'items':model_schema},'initial':cp_schema,'actions':{'type':'array','maxItems':8,'items':action_schema}}}
write(PUB/'input.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','title':'Print Batch Approval case inputs','type':'object','additionalProperties':False,'required':['schemaVersion','cases'],'properties':{'schemaVersion':{'const':1},'cases':{'type':'array','minItems':1,'items':case_schema}}})
# Keep adapter free of product state and product calculations.
write(PUB/'Bridge.swift','''import SwiftUI
import AlertToast

public enum ObserverBridge {
    public static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let host = fixture["host"] as! [String: Any]
        let index = fixture["activeModelIndex"] as? Int ?? 0
        let raw = (fixture["model"] as? [String: Any]) ?? (fixture["models"] as! [[String: Any]])[index]
        let jobs = (raw["jobs"] as! [[String: Any]]).map { j in
            PrintBatchJob(id: j["id"] as! String, title: j["title"] as! String, pages: j["pages"] as! Int, copies: j["copies"] as! Int, isColor: j["isColor"] as! Bool, selected: j["selected"] as! Bool, locked: j["locked"] as! Bool)
        }
        let model = PrintBatchModel(modelID: raw["modelID"] as! String, budgetCredits: raw["budgetCredits"] as! Int, allowPriority: raw["allowPriority"] as! Bool, initialPaperMode: raw["initialPaperMode"] as! String, initialPriority: raw["initialPriority"] as! Bool, initialExpanded: raw["initialExpanded"] as! Bool, jobs: jobs)
        let presentation = PrintBatchPresentation(isDark: host["theme"] as! String == "dark", textScale: (host["textScale"] as! NSNumber).doubleValue, isRTL: host["direction"] as! String == "rtl")
        return AnyView(PrintBatchApprovalCard(model: model, presentation: presentation) { name, payload in
            let envelope: [String: Any] = ["name": name, "payload": payload]
            if let data = try? JSONSerialization.data(withJSONObject: envelope, options: [.sortedKeys]), let line = String(data: data, encoding: .utf8) { onEvent(line) }
        })
    }
}
''')
write(PUB/'ObserverBridge.kt','''package org.nativeobserver

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.example.reply.ui.printbatch.PrintBatchApprovalCard
import com.example.reply.ui.printbatch.PrintBatchJob
import com.example.reply.ui.printbatch.PrintBatchModel
import com.example.reply.ui.printbatch.PrintBatchPresentation
import org.json.JSONObject

@Composable
fun ObserverBridge(fixture: JSONObject, onEvent: (String) -> Unit, modifier: Modifier = Modifier) {
    val host = fixture.getJSONObject("host")
    val raw = fixture.optJSONObject("model") ?: fixture.getJSONArray("models").getJSONObject(fixture.optInt("activeModelIndex", 0))
    val rawJobs = raw.getJSONArray("jobs")
    val jobs = (0 until rawJobs.length()).map { index ->
        val j = rawJobs.getJSONObject(index)
        PrintBatchJob(j.getString("id"), j.getString("title"), j.getInt("pages"), j.getInt("copies"), j.getBoolean("isColor"), j.getBoolean("selected"), j.getBoolean("locked"))
    }
    val model = PrintBatchModel(raw.getString("modelID"), raw.getInt("budgetCredits"), raw.getBoolean("allowPriority"), raw.getString("initialPaperMode"), raw.getBoolean("initialPriority"), raw.getBoolean("initialExpanded"), jobs)
    val presentation = PrintBatchPresentation(host.getString("theme") == "dark", host.getDouble("textScale"), host.getString("direction") == "rtl")
    PrintBatchApprovalCard(model, presentation, { name, payload ->
        onEvent(JSONObject(mapOf("name" to name, "payload" to JSONObject(payload))).toString())
    }, modifier)
}
''')
# Annotated reference: explicit visual design created before code exists.
svg='''<svg xmlns="http://www.w3.org/2000/svg" width="840" height="1060" viewBox="0 0 840 1060"><rect width="840" height="1060" fill="#E7EBF1"/><style>text{font-family:system-ui,sans-serif;fill:#14243A}.note{font-size:12px;fill:#3F5169}.body{font-size:14px}.small{font-size:12px;fill:#53657A}.bold{font-weight:600}</style><text x="24" y="28" font-size="18" font-weight="700">Print Batch Approval — preimplementation design reference</text><text x="24" y="49" class="note">Example: P1 after duplex + priority + expanded breakdown. Scroll content shown beyond 600-high viewport.</text><rect x="24" y="72" width="390" height="930" fill="#F5F7FA" stroke="#94A3B8"/><path d="M24 672H414" stroke="#B63835" stroke-dasharray="5 4"/><text x="430" y="674" class="note">600-high viewport ends here; vertical scroll reaches footer.</text><rect x="40" y="88" width="358" height="894" rx="16" fill="#FFFFFF"/><text x="56" y="124" font-size="20" font-weight="600">Print budget check</text><rect x="326" y="103" width="56" height="24" rx="12" fill="#167650" opacity=".13"/><text x="338" y="119" font-size="12" font-weight="600" fill="#167650">Ready</text><text x="56" y="155" class="small">Estimated charge</text><text x="56" y="189" font-size="28" font-weight="700">48 cr</text><text x="56" y="216" class="small">2 jobs • 21 pages • 11 sheets</text><rect x="56" y="240" width="20" height="20" rx="4" fill="#265FE4"/><path d="M60 250l4 4 8-9" fill="none" stroke="white" stroke-width="2"/><text x="88" y="253" class="body bold">Meeting agenda</text><text x="88" y="274" class="small">8 pages × 2 copies • Mono</text><text x="344" y="253" class="body">24 cr</text><path d="M56 290H382" stroke="#53657A" opacity=".25"/><rect x="56" y="314" width="20" height="20" rx="4" fill="#265FE4"/><path d="M60 324l4 4 8-9" fill="none" stroke="white" stroke-width="2"/><text x="88" y="327" class="body bold">Color cover</text><text x="88" y="348" class="small">5 pages × 1 copies • Color</text><text x="344" y="327" class="body">18 cr</text><path d="M56 364H382" stroke="#53657A" opacity=".25"/><rect x="56" y="388" width="20" height="20" rx="4" fill="none" stroke="#53657A"/><text x="88" y="401" class="body bold">Desk notes</text><text x="88" y="422" class="small">3 pages × 1 copies • Mono</text><text x="352" y="401" class="body">5 cr</text><text x="56" y="458" class="body bold">Paper mode</text><rect x="56" y="470" width="326" height="48" rx="10" fill="#F5F7FA"/><text x="74" y="499" class="body">Single-sided</text><rect x="219" y="470" width="163" height="48" rx="10" fill="#265FE4"/><text x="273" y="499" class="body" style="fill:white">Duplex</text><text x="56" y="557" class="body bold">Priority handling</text><rect x="334" y="538" width="48" height="28" rx="14" fill="#265FE4"/><circle cx="368" cy="552" r="11" fill="white"/><text x="56" y="584" class="small">Adds 6 cr to this batch.</text><text x="56" y="630" class="body bold" style="fill:#265FE4">Hide cost breakdown</text><text x="56" y="673" class="small">Ink</text><text x="349" y="673" class="small">31 cr</text><text x="56" y="704" class="small">Paper</text><text x="349" y="704" class="small">11 cr</text><text x="56" y="735" class="small">Priority</text><text x="356" y="735" class="small">6 cr</text><text x="56" y="766" class="small">Total</text><text x="349" y="766" class="small">48 cr</text><text x="56" y="814" class="body bold">Balance after approval: 12 cr</text><rect x="56" y="838" width="326" height="48" rx="10" fill="#265FE4"/><text x="127" y="867" class="body bold" style="fill:white">Approve 2 jobs · 48 cr</text><text x="440" y="116" class="note">390 host / 358 card; host outside inset 16.</text><text x="440" y="138" class="note">320 host / 288 card. Internal inset 16.</text><text x="440" y="160" class="note">Card radius 16; section spacing 12.</text><text x="440" y="182" class="note">Row vertical padding 12; row separators muted at 25%.</text><text x="440" y="204" class="note">Native action bounds ≥48×48; approval radius 10.</text><text x="440" y="248" class="note">System sans-serif tokens, multiplied by textScale:</text><text x="440" y="270" class="note">title 20 semibold; charge 28 bold;</text><text x="440" y="292" class="note">body/controls/titles 14; helper/caption/detail 12.</text><text x="440" y="314" class="note">Control/title weight semibold; other body regular.</text><text x="440" y="336" class="note">textScale ∈ {1,1.2}; wrap and grow, never truncate.</text><text x="440" y="380" class="note">Light palette:</text><text x="440" y="402" class="note">background #F5F7FA / surface #FFFFFF</text><text x="440" y="424" class="note">text #14243A / muted #53657A / accent #265FE4</text><text x="440" y="446" class="note">ready #167650 / error #B63835</text><text x="440" y="490" class="note">Dark palette:</text><text x="440" y="512" class="note">background #10161F / surface #1B2532</text><text x="440" y="534" class="note">text #F2F5FA / muted #B7C4D5 / accent #8BB0FF</text><text x="440" y="556" class="note">ready #75D6AA / error #FF9A96</text><text x="440" y="600" class="note">RTL mirrors leading/trailing relationships and mode order.</text><text x="440" y="622" class="note">Vertical order remains; words/numbers stay readable.</text><text x="440" y="730" class="note">This fixes hierarchy, colors, dimensions and semantics.</text><text x="440" y="752" class="note">It does not fix incidental y positions or exact line wrapping.</text><text x="440" y="774" class="note">Actual long text/large text must expand without overlap.</text><text x="440" y="818" class="note">Cost example: ink31 + paper11 + priority6 = total48.</text><text x="440" y="840" class="note">Reference drawn before either implementation exists.</text></svg>'''
write(PUB/'reference.svg',svg)

# Oracle compiler. Each state includes all fixed aspects; collapse is explicit absence.
PALETTES={'light':dict(background='#F5F7FA',surface='#FFFFFF',text='#14243A',muted='#53657A',accent='#265FE4',ready='#167650',error='#B63835'),'dark':dict(background='#10161F',surface='#1B2532',text='#F2F5FA',muted='#B7C4D5',accent='#8BB0FF',ready='#75D6AA',error='#FF9A96')}
def reset(m): return dict(selected=[j['id'] for j in m['jobs'] if j['selected']],paperMode=m['initialPaperMode'],priority=m['initialPriority'],expanded=m['initialExpanded'])
def calc(m,s):
    rows={}; ink=sheets=pages=0
    for j in m['jobs']:
        p=j['pages']*j['copies']; sh=(j['pages'] if s['paperMode']=='single' else (j['pages']+1)//2)*j['copies']; i=p*(3 if j['isColor'] else 1)
        rows[j['id']]=dict(ink=i,sheets=sh,printedPages=p,cost=i+sh)
        if j['id'] in s['selected']: ink+=i; sheets+=sh; pages+=p
    n=len(s['selected']); extra=6 if n and s['priority'] else 0; total=ink+sheets+extra
    return dict(rows=rows,ink=ink,sheets=sheets,printedPages=pages,count=n,surcharge=extra,total=total,canApprove=n>0 and total<=m['budgetCredits'],canPriority=m['allowPriority'] and n>0)
def event(name,**payload): return dict(name=name,payload=payload)
def apply(m,s,a,newm):
    s=copy.deepcopy(s); c=calc(m,s)
    if a['type']=='replaceModel': return newm,reset(newm),[],True
    t=a['targetID']; events=[]; enabled=True
    if t=='printbatch.approve':
        enabled=c['canApprove']
        if enabled: events=[event('approve',modelID=m['modelID'],jobIDs=s['selected'],paperMode=s['paperMode'],priority=s['priority'],totalCredits=c['total'],printedPages=c['printedPages'],sheets=c['sheets'])]
    elif t=='printbatch.priority':
        enabled=c['canPriority']
        if enabled: s['priority']=not s['priority']; events=[event('priorityChanged',priority=s['priority'])]
    elif t=='printbatch.breakdown.toggle':
        s['expanded']=not s['expanded']; events=[event('breakdownChanged',expanded=s['expanded'])]
    elif t.startswith('printbatch.mode.'):
        mode=t.split('.')[-1]
        if mode!=s['paperMode']: s['paperMode']=mode; events=[event('paperModeChanged',paperMode=mode)]
    elif t.startswith('printbatch.job.'):
        jid=t.split('.')[2]; j=next(x for x in m['jobs'] if x['id']==jid); enabled=not j['locked']
        if enabled:
            selected=set(s['selected']); selected.symmetric_difference_update({jid}); s['selected']=[x['id'] for x in m['jobs'] if x['id'] in selected]; events=[event('selectionChanged',jobIDs=s['selected'])]
    else: raise ValueError(t)
    return m,s,events,enabled
cells=[]; ledger=[]
def cell(platform,caseid,stateid,aspect,cls,target,op,expected,**extra):
    x=dict(cellID=f'{platform}.{stateid}.{aspect}',platform=platform,caseID=caseid,stateID=stateid,aspect=aspect,classification=cls,targetID=target,operator=op,expected=expected,**extra);cells.append(x)
def state_cells(platform,case,cp,m,s,events,enabled,action):
    id=case['caseID']; sid=cp['stateID']; c=calc(m,s); host=case['host']; pal=PALETTES[host['theme']]
    def add(aspect,target,expected,op='equal',cls='runtime.business.current',**kw): cell(platform,id,sid,aspect,cls,target,op,expected,**kw)
    def txt(aspect,target,value,size=14,weight='regular',color='text'):
        add(aspect+'.text',target,value)
        add(aspect+'.fontSize',target,size*host['textScale'],op='scalar',cls='runtime.style.native',unit='sp' if platform=='android' else 'pt')
        add(aspect+'.fontWeight',target,weight,op='equal',cls='runtime.style.native')
        add(aspect+'.color',target,pal.get(color,color),op='color',cls='runtime.style.native')
    status='No jobs' if not c['count'] else ('Over budget' if c['total']>m['budgetCredits'] else 'Ready')
    status_color='muted' if not c['count'] else ('error' if c['total']>m['budgetCredits'] else 'ready')
    txt('title','printbatch.title','Print budget check',20,'semibold')
    txt('status','printbatch.status',status,12,'semibold',status_color)
    txt('charge.caption','printbatch.charge.caption','Estimated charge',12,color='muted')
    txt('charge.value','printbatch.charge.value',f"{c['total']} cr",28,'bold')
    txt('summary','printbatch.summary',f"{c['count']} jobs • {c['printedPages']} pages • {c['sheets']} sheets",12,color='muted')
    for j in m['jobs']:
        p='job.'+j['id']; t='printbatch.'+p
        txt(p+'.title',t+'.title',j['title'],14,'semibold')
        txt(p+'.subtitle',t+'.subtitle',f"{j['pages']} pages × {j['copies']} copies • {'Color' if j['isColor'] else 'Mono'}"+(' • Locked' if j['locked'] else ''),12,color='muted')
        txt(p+'.price',t+'.price',str(c['rows'][j['id']]['cost'])+' cr')
        add(p+'.selection',t+'.toggle',j['id'] in s['selected'],op='selected')
        add(p+'.enabled',t+'.toggle',not j['locked'],op='enabled')
        add(p+'.name',t+'.toggle',('Deselect ' if j['id'] in s['selected'] else 'Select ')+j['title'],op='name')
    txt('mode.title','printbatch.mode.title','Paper mode',14,'semibold')
    for mode,label in [('single','Single-sided'),('duplex','Duplex')]:
        txt('mode.'+mode,'printbatch.mode.'+mode,label,14,'semibold',('#FFFFFF' if host['theme']=='light' else '#14243A') if mode==s['paperMode'] else 'text')
        add('mode.'+mode+'.selected','printbatch.mode.'+mode,mode==s['paperMode'],op='selected')
        add('mode.'+mode+'.enabled','printbatch.mode.'+mode,True,op='enabled')
    txt('priority','printbatch.priority','Priority handling',14,'semibold','text' if c['canPriority'] else 'muted')
    add('priority.on','printbatch.priority',s['priority'],op='selected');add('priority.enabled','printbatch.priority',c['canPriority'],op='enabled')
    helper='Priority unavailable for this batch.' if not m['allowPriority'] else ('Adds 6 cr to this batch.' if s['priority'] else 'Add 6 cr for priority handling.')
    txt('priority.helper','printbatch.priority.helper',helper,12,color='muted')
    txt('breakdown.toggle','printbatch.breakdown.toggle','Hide cost breakdown' if s['expanded'] else 'Show cost breakdown',14,'semibold','accent')
    add('breakdown.expanded','printbatch.breakdown.toggle',s['expanded'],op='expanded');add('breakdown.enabled','printbatch.breakdown.toggle',True,op='enabled')
    for key,label,value in [('ink','Ink',c['ink']),('paper','Paper',c['sheets']),('priority','Priority',c['surcharge']),('total','Total',c['total'])]:
        for sub,text in [('label',label),('value',str(value)+' cr')]:
            target='printbatch.breakdown.'+key+'.'+sub; aspect='breakdown.'+key+'.'+sub
            add(aspect+'.presence',target,s['expanded'],op='presence')
            if s['expanded']: txt(aspect,target,text,12,color='muted')
            else:
                # Fixed denominator: not-applicable font/text/color for absent elements are separately recorded, not runtime passes.
                for suffix in ['text','fontSize','fontWeight','color']: add(aspect+'.'+suffix,target,None,op='notApplicable',cls='notApplicable.absent',reason='Breakdown collapsed: element required absent.')
    balance='No charge selected' if not c['count'] else (f"Short by {c['total']-m['budgetCredits']} cr" if c['total']>m['budgetCredits'] else f"Balance after approval: {m['budgetCredits']-c['total']} cr")
    txt('balance','printbatch.balance',balance,14,'semibold','error' if c['count'] and c['total']>m['budgetCredits'] else 'text')
    approve='Select a job to approve' if not c['count'] else (f"Over budget by {c['total']-m['budgetCredits']} cr" if c['total']>m['budgetCredits'] else f"Approve {c['count']} jobs · {c['total']} cr")
    # Approval foreground can be contrast text on an accent surface; exact foreground is not fixed by public design.
    add('approve.text','printbatch.approve',approve);add('approve.enabled','printbatch.approve',c['canApprove'],op='enabled')
    add('approve.fontSize','printbatch.approve',14*host['textScale'],op='scalar',cls='runtime.style.native',unit='sp' if platform=='android' else 'pt')
    add('approve.fontWeight','printbatch.approve','semibold',cls='runtime.style.native')
    add('approve.foreground','printbatch.approve',('#FFFFFF' if host['theme']=='light' else '#14243A') if c['canApprove'] else pal['muted'],op='color',cls='runtime.style.native')
    add('approve.fill','printbatch.approve',pal['accent'] if c['canApprove'] else 'visibly subdued surface',op='color' if c['canApprove'] else 'screenshotReview',cls='runtime.style.native' if c['canApprove'] else 'runtime.style.visual')
    controls=['printbatch.job.'+j['id']+'.toggle' for j in m['jobs']]+['printbatch.mode.single','printbatch.mode.duplex','printbatch.priority','printbatch.breakdown.toggle','printbatch.approve']
    for target in controls:
        for dim in ['width','height']:
            add('control.'+target.removeprefix('printbatch.')+'.semanticBounds.'+dim,target,48,op='minimum',cls='runtime.layout.native',unit='dp' if platform=='android' else 'pt',dimension=dim)
        for dim in ['width','height']:
            add('control.'+target.removeprefix('printbatch.')+'.physicalHitRegion.'+dim,target,48,op='physicalHitRegion',cls='runtime.capability.physicalHit',unit='dp' if platform=='android' else 'pt',dimension=dim)
    for asp,value in [('surfaceColor',pal['surface']),('backgroundColor',pal['background']),('cornerRadius',16),('contentPadding',16),('sectionSpacing',12),('approvalRadius',10)]:
        add('tokens.'+asp,'printbatch.card',value,op='color' if asp.endswith('Color') else 'scalar',cls='runtime.style.native',unit='dp' if platform=='android' else 'pt')
    for aspect,meaning in [
      ('visual.verticalOrder','Title/status, charge/summary, jobs, mode, priority, breakdown, balance, approval have specified vertical order.'),
      ('visual.typeHierarchy','Title and large charge have distinct specified hierarchy in actual rendering.'),
      ('visual.paletteBackground','Actual background and surface match chosen '+host['theme']+' palette.'),
      ('visual.paletteText','Actual primary/muted text use specified palette and remain legible.'),
      ('visual.paletteAccent','Selected mode and enabled approval use accent fill and specified contrasting text; selected/on indicators use accent.'),
      ('visual.paletteStatus','Badge and shortfall use semantic ready/error/muted colors matching current state.'),
      ('visual.disabled','Disabled controls have muted text and a visibly subdued legible surface.'),
      ('visual.wrap','All long required text and summaries wrap and rows expand as needed.'),
      ('visual.noClip','No required content is truncated or horizontally clipped.'),
      ('visual.noOverlap','No required labels, values or controls overlap.'),
      ('visual.association','Job title/subtitle and trailing price, and breakdown label/value pairs, remain clearly associated.'),
      ('visual.headerDirection','Header title is leading and badge trailing under '+host['direction']+'.'),
      ('visual.jobDirection','Job selection/text/price obey leading/middle/trailing under '+host['direction']+'.'),
      ('visual.modeDirection','Mode Single-sided then Duplex follows leading-to-trailing order under '+host['direction']+'.'),
      ('visual.readability','English words and numeric values remain readable under supplied direction.'),
      ('visual.expansion','Expanded cost rows render Ink, Paper, Priority, Total in order.' if s['expanded'] else 'Collapsed cost rows occupy no rendered area.'),
      ('visual.controls','Controls are visibly distinguishable with correct selected states.'),
      ('visual.noObstruction','No visible overlay obscures another control.')]:
        add(aspect,'printbatch.card',meaning,op='screenshotReview',cls='runtime.style.visual')
    add('coverage.nativeAllTargets','printbatch.card',True,op='completeCoverage',cls='runtime.coverage',full_content=cp['full_content'])
    if action is not None:
        gate='replacementApplied' if action['type']=='replaceModel' else 'successfulExactActivation'
        add('stimulus.dispatch',action.get('targetID','caller.model'),dict(kind=action['type'],targetID=action.get('targetID'),modelID=m['modelID'] if action['type']=='replaceModel' else None,enabledBefore=enabled),op='stimulus',cls='stimulus.execution',requiresSuccessfulStimulus=False)
        add('behavior.callbackInterval',action.get('targetID','caller.model'),events,op='eventSequence',cls='runtime.business.stimulus',gate=gate,expectedEnabledBefore=enabled)
        # Exact state facts do not by themselves prove a dynamic transition.
        add('behavior.resultingState',action.get('targetID','caller.model'),dict(modelID=m['modelID'],selected=s['selected'],paperMode=s['paperMode'],priority=s['priority'],expanded=s['expanded'],total=c['total']),op='transition',cls='runtime.business.stimulus',gate=gate,expectedEnabledBefore=enabled)
    return c
for case_ in public+held:
    m=case_['models'][0];s=reset(m)
    for index,cp in enumerate([case_['initial']]+case_['actions']):
        a=None if index==0 else cp; events=[]; enabled=True
        if a: m,s,events,enabled=apply(m,s,a,case_['models'][a['modelIndex']] if a['type']=='replaceModel' else None)
        c=calc(m,s)
        ledger.append(dict(caseID=case_['caseID'],stateID=cp['stateID'],actionIndex=index,trigger='initial' if index==0 else a['type'],full_content=cp['full_content'],modelID=m['modelID'],model=copy.deepcopy(m),localState=copy.deepcopy(s),calculated=c,requestedAction=a,expectedEnabledBefore=enabled if a else None,expectedIntervalEvents=events))
        for platform in ['android','ios']:state_cells(platform,case_,cp,m,s,events,enabled,a)
# Source/API/input obligations remain outside all runtime counts.
for platform in ['android','ios']:
    for aspect,expected in [('entrypoint','Exact production file and component from API.md'),('modelAPI','All public model and presentation fields and initializers from API.md'),('callbackAPI','One onEvent callback with name and JSON-compatible payload'),('bridgeCallsProduction','Observer adapter imports and calls real production component'),('replacementIdentity','Caller replaces model without replacing component identity')]:
        cells.append(dict(cellID=f'{platform}.global.source.{aspect}',platform=platform,caseID=None,stateID=None,aspect=aspect,classification='source.api',targetID=None,operator='sourceReview',expected=expected))
for case_ in public+held:
    for aspect,expected in [('schema','Case input validates input.schema.json plus unique job IDs and distinct modelIDs'),('host',case_['host']),('actionSequence',case_['actions']),('modelMembers',case_['models'])]:
        cells.append(dict(cellID=f'input.{case_["caseID"]}.{aspect}',platform='host',caseID=case_['caseID'],stateID=None,aspect=aspect,classification='input.integrity',targetID=None,operator='inputReview',expected=expected))
write(PRIV/'states-ledger.json',dict(schemaVersion=1,states=ledger))
write(PRIV/'oracle.json',dict(schemaVersion=1,task='Print Batch Approval',cases=[c['caseID'] for c in public+held],cells=cells))
counts={}
for x in cells:counts[x['classification']]=counts.get(x['classification'],0)+1
write(PRIV/'denominator.json',dict(schemaVersion=1,caseCount=len(public+held),stateCount=len(ledger),platformStateCount=2*len(ledger),cellCount=len(cells),byClass=counts,notes=['notApplicable.absent is explicit ledger material, excluded from P/F/U denominator and reported separately.','All other cells remain in their fixed class denominators even unsupported or unobserved.','Public/held-out, platform, case, checkpoint and source/input/runtime strata must all be retained.']))
print(json.dumps(dict(cells=len(cells),states=len(ledger),counts=counts),indent=2))
