# Public production API — WorkshopSlotPlanner

Swift module `AlertToast`: public `struct WorkshopSlot: Codable, Identifiable` with `id: String`, `label: String`, `detail: String`, `available: Bool`. Public `struct WorkshopSlotPlannerModel: Codable` contains `revision: String`, `title: String`, `subtitle: String`, `notice: String`, `footer: String`, `initialSelectedID: String?`, `initialDetailsExpanded: Bool`, `slots: [WorkshopSlot]`. Synthesized Codable keys exactly match fixtures (camelCase); nullable selection is JSON null. Provide public memberwise initializers and public Codable decoding. Public `struct WorkshopSlotPlanner: View` has `init(model: WorkshopSlotPlannerModel, onSelect: (String) -> Void, onDetailsChange: (Bool) -> Void, onReserve: (String) -> Void)`; closure parameters escaping. Initializer parameter order used by Bridge.swift is authoritative: selection callback, onDetailsChange, submission callback.

Kotlin package `com.example.reply.ui.components`: public `data class WorkshopSlot(id: String, label: String, detail: String, available: Boolean)`. Public `data class WorkshopSlotPlannerModel(revision: String, title: String, subtitle: String, notice: String, footer: String, initialSelectedID: String?, initialDetailsExpanded: Boolean, slots: List<WorkshopSlot>)`. Public `@Composable fun WorkshopSlotPlanner(model: WorkshopSlotPlannerModel, onSelect: (String) -> Unit, onReserve: (String) -> Unit, onDetailsChange: (Boolean) -> Unit)`. All parameters are named by ObserverBridge.kt. Types in Kotlin use Boolean, not Swift Bool. The component reads Material/native theme or system light/dark environment and native direction/font scale; the bridge adds no alternate visual theme.

The real component owns transient state keyed by model.revision, callback dispatch, disabled semantics, and all semantic IDs. Bridges only decode approved inputs, invoke this API and map callbacks into event strings. No bridge state/reducer or reconstructed tested view is allowed. IDs below belong on actual production controls/text/container. Use a containing semantics group for canvas without merging away descendants. Use selected semantics on each single native choice control, and native disabled semantics on unavailable controls. A visual-only checkmark cannot substitute for selected semantics. No independently actionable nested indicator inside a choice.

| Logical target | Exact semantic ID | Role / meaning |
|---|---|---|
| canvas | workshop.canvas | Component-owned container spanning all content; children retained |
| title | workshop.title | Actual heading text, native weight600 |
| notice | workshop.notice | Actual padded notice panel; label is notice text |
| choiceA/choiceB/locked | workshop.choice.a / .b / .c | Actual selection buttons; c disabled |
| all entries | workshop.choice.<id> | Same rule for d,e,f and any incoming ID |
| summary | workshop.summary | Actual summary text; exact native label below |
| disclosure | workshop.disclosure | Actual detail toggle button |
| submit | workshop.submit | Actual primary button incl native activation box |
| footer | workshop.footer | Actual final body copy |

Summary is `No station selected` with no valid selection. With selection it is `Draft station: <selected label>`. Prefixes/punctuation/spacing are exact. Action visible label is `Request station`. Never change the summary after submission alone. A new revision resets disclosure and selection even when the view instance survives.

Callback event map (exact lowercase IDs): workshop:details:open|closed; workshop:select:<id>; workshop:reserve:<id>. Submission forwards the current selected IDs; bridge sorts set IDs only to normalize event order. Exactly one callback for each successful action. No callback on mere recomposition or model replacement. Do not emit fixture-update acknowledgements as business callbacks.

Host/component boundary: canvas and internal surfaces/semantic bounds are component responsibility. Outer600-unit viewport, padding, screen conversion, host controls and surrounding background are observer responsibility. There is no fixed internal component height. SwiftUI import is `import AlertToast`; Kotlin bridge package is `org.nativeobserver` and imports only the newly specified production types from `com.example.reply.ui.components`.
