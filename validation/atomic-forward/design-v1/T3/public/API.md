# Public production API — BicycleServiceIntake

Swift module `AlertToast`: public `struct BicycleServiceOption: Codable, Identifiable` with `id: String`, `label: String`, `detail: String`, `available: Bool`; minutes: Int. Public `struct BicycleServiceIntakeModel: Codable` contains `revision: String`, `title: String`, `subtitle: String`, `notice: String`, `footer: String`, `initialSelectedIDs: [String]`, `initialDetailsExpanded: Bool`, `services: [BicycleServiceOption]`. Synthesized Codable keys exactly match fixtures (camelCase); nullable selection is JSON null. Provide public memberwise initializers and public Codable decoding. Public `struct BicycleServiceIntake: View` has `init(model: BicycleServiceIntakeModel, onToggle: (String, Bool) -> Void, onDetailsChange: (Bool) -> Void, onSubmit: ([String]) -> Void)`; closure parameters escaping. Initializer parameter order used by Bridge.swift is authoritative: selection callback, onDetailsChange, submission callback.

Kotlin package `com.example.reply.ui.components`: public `data class BicycleServiceOption(id: String, label: String, detail: String, available: Boolean, minutes: Int)`. Public `data class BicycleServiceIntakeModel(revision: String, title: String, subtitle: String, notice: String, footer: String, initialSelectedIDs: List<String>, initialDetailsExpanded: Boolean, services: List<BicycleServiceOption>)`. Public `@Composable fun BicycleServiceIntake(model: BicycleServiceIntakeModel, onToggle: (String, Boolean) -> Unit, onSubmit: (List<String>) -> Unit, onDetailsChange: (Boolean) -> Unit)`. All parameters are named by ObserverBridge.kt. Types in Kotlin use Boolean, not Swift Bool. The component reads Material/native theme or system light/dark environment and native direction/font scale; the bridge adds no alternate visual theme.

The real component owns transient state keyed by model.revision, callback dispatch, disabled semantics, and all semantic IDs. Bridges only decode approved inputs, invoke this API and map callbacks into event strings. No bridge state/reducer or reconstructed tested view is allowed. IDs below belong on actual production controls/text/container. Use a containing semantics group for canvas without merging away descendants. Use selected semantics on each single native choice control, and native disabled semantics on unavailable controls. A visual-only checkmark cannot substitute for selected semantics. No independently actionable nested indicator inside a choice.

| Logical target | Exact semantic ID | Role / meaning |
|---|---|---|
| canvas | bicycle.canvas | Component-owned container spanning all content; children retained |
| title | bicycle.title | Actual heading text, native weight600 |
| notice | bicycle.notice | Actual padded notice panel; label is notice text |
| choiceA/choiceB/locked | bicycle.choice.a / .b / .c | Actual selection buttons; c disabled |
| all entries | bicycle.choice.<id> | Same rule for d,e,f and any incoming ID |
| summary | bicycle.summary | Actual summary text; exact native label below |
| disclosure | bicycle.disclosure | Actual detail toggle button |
| submit | bicycle.submit | Actual primary button incl native activation box |
| footer | bicycle.footer | Actual final body copy |

Summary is `No work selected · 0 min` with no valid selection. With selection it is `Work: <labels joined by + in model order> · <sum minutes> min`; the join has one space around +. Prefixes/punctuation/spacing are exact. Action visible label is `Send service draft`. Never change the summary after submission alone. A new revision resets disclosure and selection even when the view instance survives.

Callback event map (exact lowercase IDs): bicycle:details:open|closed; bicycle:toggle:<id>:true|false; bicycle:submit:sorted comma-joined IDs. Submission forwards the current selected IDs; bridge sorts set IDs only to normalize event order. Exactly one callback for each successful action. No callback on mere recomposition or model replacement. Do not emit fixture-update acknowledgements as business callbacks.

Host/component boundary: canvas and internal surfaces/semantic bounds are component responsibility. Outer600-unit viewport, padding, screen conversion, host controls and surrounding background are observer responsibility. There is no fixed internal component height. SwiftUI import is `import AlertToast`; Kotlin bridge package is `org.nativeobserver` and imports only the newly specified production types from `com.example.reply.ui.components`.
