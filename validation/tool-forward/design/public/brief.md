# Return Resolution Card — native component contract

Build a new, reusable `ReturnResolutionCard` in the Reply Android app using Kotlin/Jetpack Compose and in the AlertToast Swift package using SwiftUI. This is a controlled component for choosing how a purchase return will be settled. A caller owns every business state and receives typed actions. Implement the same behavior on both platforms, with native system typography and accessibility conventions.

This document and `public-example.json` are the entire public requirement. `reference.svg` is a structural design reference, not a pixel golden. Private grading fixtures contain different caller content and combinations of these public requirements; they introduce no new behavior.

## P01. Host and platform contract

- Offered host widths are 320 and 390 logical units. The host supplies 16 units of horizontal margin and 24 units before the card, leaving card widths of 288 and 358. The component fills that offered card width without adding another outer margin. Its internal horizontal padding is 16.
- The host is a 600-unit viewport with one parent vertical scroll container. The card grows with content. Its footer belongs to the card's natural flow. It must not introduce a nested vertical scroll region, sticky footer, fixed card height, or maximum text height.
- Support light and dark appearance, LTR and RTL layout, and native enlarged text. Test mapping: Android `fontScale=1.0 / 1.3 / 2.0`; Apple content-size categories `.large / .extraExtraExtraLarge / .accessibilityExtraExtraExtraLarge`, respectively. These are corresponding native test modes, not numerically identical glyph sizes.
- All supplied text must wrap and remain readable without ellipses, clipping, horizontal scrolling, or overlapping other elements. Move amounts, badges, and actions to another line where needed. Card height may exceed the viewport, including at normal text size. Capture the full card by scrolling the parent.
- Swift source must build as a public part of the pinned AlertToast package with deployment targets **iOS 14 and macOS 11**, and Swift 5 language compatibility. An application may demonstrate it on the current installed iOS simulator. A current-runtime build or screenshot does not establish minimum deployment compatibility. Guard newer APIs and platform-specific imports appropriately; provide an available implementation on both declared platforms.
- Keep the existing Reply and AlertToast entry points usable. Add the component and an isolated demonstration if needed. No network, persistence, backend, external assets, or changes to the packages' deployment targets are required.

## P02. Public API and complete model schema

Android symbol: `com.example.reply.ui.components.ReturnResolutionCard(model: ReturnResolutionModel, onAction: (ReturnResolutionAction) -> Unit, modifier: Modifier = Modifier)`, marked `@Composable`. Put its public types in the same package.

Apple symbol in the `AlertToast` module: `public struct ReturnResolutionCard: View`, with `public init(model: ReturnResolutionModel, onAction: @escaping (ReturnResolutionAction) -> Void)`. Its models, enums, stored properties, and model initializers must be public so an external app can construct every fixture. Swift model initializers use the property labels below. Android uses public data classes, enums, and a sealed action class. No extra required initializer parameter is permitted. Additional optional parameters are acceptable.

JSON is a fixture interchange format; the component accepts the typed native models. Field spelling is identical on both platforms. Enum JSON strings are lowercase; Kotlin enum cases are uppercase, Swift cases are lowercase. No custom JSON decoder is required.

| Type | Properties, in initializer order |
| --- | --- |
| `ReturnResolutionModel` | `caseId: String`, `merchant: String`, `heading: String`, `orderReference: String`, `intro: String`, `status: ReturnResolutionStatus`, `statusLabel: String`, `item: ReturnResolutionItem`, `deadline: ReturnResolutionDeadline?`, `contextMessage: String`, `optionsTitle: String`, `options: List<ReturnResolutionOption>`, `selectedOptionId: String?`, `sizesTitle: String`, `sizes: List<ReturnResolutionSize>`, `selectedSizeId: String?`, `acknowledgementAccepted: Bool`, `notes: ReturnResolutionNotes`, `notesExpanded: Bool`, `amountRows: List<ReturnResolutionAmountRow>`, `totalLabel: String`, `totalValue: String`, `totalFootnote: String`, `idlePrimaryLabel: String`, `keepLabel: String`, `progressTitle: String`, `progressBody: String`, `resultTitle: String`, `resultBody: String`, `resultReference: String`, `doneLabel: String`, `strings: ReturnResolutionStrings` |
| `ReturnResolutionItem` | `title: String`, `variant: String`, `quantityLabel: String`, `paidLabel: String`, `accent: ReturnResolutionAccent` |
| `ReturnResolutionDeadline` | `text: String`, `urgent: Bool` |
| `ReturnResolutionOption` | `id: String`, `kind: ReturnResolutionKind`, `title: String`, `description: String`, `amountLabel: String`, `tag: String?`, `disabledReason: String?`, `detailTitle: String`, `detailBody: String`, `acknowledgementLabel: String?`, `primaryLabel: String` |
| `ReturnResolutionSize` | `id: String`, `label: String`, `unavailableReason: String?` |
| `ReturnResolutionNotes` | `title: String`, `body: String`, `bullets: List<String>` |
| `ReturnResolutionAmountRow` | `id: String`, `label: String`, `value: String`, `emphasized: Bool` |
| `ReturnResolutionStrings` | `chooseOption: String`, `chooseSize: String`, `acceptTerms: String`, `ready: String`, `noOptions: String`, `checkedValue: String`, `uncheckedValue: String`, `expandedValue: String`, `collapsedValue: String`, `busyValue: String` |

Use `Boolean` and `List<T>` on Android, `Bool` and `[T]` on Apple. Nullable fields map to `?`. Enums: `ReturnResolutionStatus = editing | submitting | complete`; `ReturnResolutionKind = refund | credit | exchange`; `ReturnResolutionAccent = teal | coral | indigo`. IDs are opaque nonempty strings unique within their corresponding list. Arrays preserve caller order. Empty notes bullets and amount rows are valid. Strings are already formatted/localized, including numbers, currency, punctuation and bidirectional marks; do not parse, calculate, uppercase, abbreviate, or rewrite them. Input text is plain text, never Markdown. Unknown selected IDs are valid stale caller state and are handled below.

The public actions are precisely:

| Action | Kotlin representation | Swift representation |
| --- | --- | --- |
| Select an option | `data class SelectOption(val optionId: String)` | `case selectOption(optionId: String)` |
| Select a size | `data class SelectSize(val sizeId: String)` | `case selectSize(sizeId: String)` |
| Change acknowledgement | `data class SetAcknowledgement(val accepted: Boolean)` | `case setAcknowledgement(accepted: Bool)` |
| Change notes expansion | `data class SetNotesExpanded(val expanded: Boolean)` | `case setNotesExpanded(expanded: Bool)` |
| Submit | `data class Submit(val optionId: String, val sizeId: String?, val acknowledgementAccepted: Boolean)` | `case submit(optionId: String, sizeId: String?, acknowledgementAccepted: Bool)` |
| Keep the purchase | `object KeepPurchase` | `case keepPurchase` |
| Dismiss a completed result | `object Done` | `case done` |

Kotlin variants inherit from `ReturnResolutionAction`; Swift cases belong to `public enum ReturnResolutionAction`. JSON action traces use `type: selectOption / selectSize / setAcknowledgement / setNotesExpanded / submit / keepPurchase / done` and the corresponding argument property names.

## P03. Caller control and decisions

Rendering is solely a function of the latest model and host environment. Tapping a control emits exactly one action and does not mutate selection, expansion, acknowledgement, status, totals, or result. The caller may echo a changed model, delay that echo, replace the entire model, revoke availability, retain stale selected IDs, or change `caseId` at any time. Render every replacement immediately, with no state or text retained from an earlier model. There is no mandatory animation or delay.

An **effective option** is the option matching `selectedOptionId` whose `disabledReason` is null. A disabled matching option is not selected. An **effective size** is the size matching `selectedSizeId` whose `unavailableReason` is null. An unavailable matching size is not selected. Stale IDs select nothing. Empty optional text is not used in fixtures; null means absent. Availability changes require no user action before the UI updates.

In `editing`:

1. Every option is displayed, in input order, with title, description, amount, optional tag, and optional disabled reason. An available option emits `SelectOption(id)` when activated, including when already selected. A disabled option emits nothing and cannot become selected.
2. Only the effective option's detail title and detail body are displayed. If it is `exchange`, display `sizesTitle` and all sizes in input order, wrapping to as many rows as needed. Include the unavailable reason visibly beside or beneath each unavailable size. An available size emits `SelectSize(id)`, including if already selected. An unavailable size emits nothing. Size controls do not exist for refund, credit, or no effective option.
3. Display a checkbox row only when the effective option has a non-null `acknowledgementLabel`. It reflects `acknowledgementAccepted`. Activating it emits `SetAcknowledgement(!model.acknowledgementAccepted)`. Do not change the checkmark before caller echo. Do not show an acknowledgement just because the model's boolean is true.
4. Display an expandable notes row. It always shows `notes.title` and a directional chevron. It emits `SetNotesExpanded(!model.notesExpanded)`. Show `notes.body` and each bullet only while `notesExpanded` is true. Expansion must follow caller echo.
5. Display `amountRows` in order, then the total and footnote. If the array is empty, omit the breakdown region. Values are caller-authored; do no arithmetic and do not infer a new total when the user taps a selection. An emphasized amount row uses semibold type. The total is visually stronger than any amount rows present.
6. Display a gate message and full-width primary action, followed by `keepLabel`. The gate message is the first applicable row of this table. The primary label is the effective option's `primaryLabel`, or `idlePrimaryLabel` when none is effective.

| Precedence | Condition | Gate message | Primary enabled |
| --- | --- | --- | --- |
| 1 | No available options exist | `strings.noOptions` | false |
| 2 | No effective option exists | `strings.chooseOption` | false |
| 3 | Effective option is exchange, with no effective size | `strings.chooseSize` | false |
| 4 | Effective option requires acknowledgement, and it is false | `strings.acceptTerms` | false |
| 5 | Otherwise | `strings.ready` | true |

7. An enabled primary emits `Submit` with the effective option ID. Its `sizeId` is the effective size ID only for exchange, otherwise null. Its `acknowledgementAccepted` is the model boolean only when that effective option requires acknowledgement, otherwise false. Irrelevant stale size/acknowledgement fields must not leak into the submission. A disabled primary emits nothing. `keepLabel` emits `KeepPurchase` without modifying the UI.

## P04. State-dependent structure

Every status has the header and item summary. The header contains merchant, heading, order reference, intro, and a status badge with `statusLabel`.

- **editing:** header → item → optional deadline strip → context message → options title → all options → effective option details → conditional sizes → conditional acknowledgement → notes → amount rows → total/footnote → gate → primary → keep-purchase action. Omit only the optional regions described above.
- **submitting:** header → item → progress panel → total/footnote. The progress panel has an indeterminate native progress indicator, `progressTitle`, and `progressBody`. No editing controls, deadline, context, amount rows, notes, result, primary action, or keep-purchase action remain visible or accessible. Expose the progress panel as busy using `strings.busyValue`.
- **complete:** header → item → successful result panel → total/footnote → full-width `doneLabel` action. The result panel has a decorative checkmark plus `resultTitle`, `resultBody`, and `resultReference`. No editing controls, deadline, context, amount rows, notes, progress indicator, primary action, or keep-purchase action remain visible or accessible. `doneLabel` emits `Done` exactly once per activation and leaves the model unchanged.

No status transition happens automatically after submitting, keeping a purchase, or dismissing a result. An external model replacement can move between any statuses.

## P05. Structural design and tokens

Use a calm retail support aesthetic with strong information hierarchy and enough separation to compare real financial choices. The reference shows the intended order and emphasis, not a required content height.

| Token | Value |
| --- | --- |
| Card | radius 20, 1-unit border, flat or very restrained shadow |
| Interior | 16 horizontal/vertical padding, 20 between major sections, 12 between related rows, 8 within text groups, 4 within tight label groups |
| Option card | card-color surface when unselected (including disabled), radius 12, 1-unit border, padding 12, minimum height 72, natural content height, 12 between cards |
| Selected option | accent border of 2 units and selected tint background; visible selected indicator |
| Detail/notes panel | radius 10, neutral surface, padding 12 |
| Item tile | 52 square at base size, radius 12; simple parcel/purchase pictogram drawn locally or using a native symbol; decorative |
| Status/tag/deadline | small capsule or rounded strip; labels wrap; do not use a fixed height |
| Size choices | minimum 48×48 touch target; capsule/rounded rectangle, selected accent border/tint, card surface when available and unselected; wrap in input order |
| Checkbox | clear square outline with checkmark when accepted; entire label row has a minimum 48-unit touch target |
| Primary/done | minimum height 48; radius 12; full available content width; label may wrap |
| Keep/notes | minimum 44-unit touch target; text-led button; notes chevron reflects expansion |
| Base typography | merchant/caption 12, label/gate 13, body 15, section/option title 17 semibold, money/total 18 semibold, main heading 24 semibold |

Use native system font families and actual Dynamic Type/fontScale. Platform-specific line metrics, weight rendering, parcel glyph, progress spinner, checkmark and chevron shapes are allowed. Base typography may differ by up to two logical units to match a native semantic style. Do not use fixed line counts. No exact line-break matching between platforms is required.

| Color role | Light | Dark |
| --- | --- | --- |
| Host background (demonstration only) | `#FAF8F5` | `#101718` |
| Card | `#FFFFFF` | `#192224` |
| Neutral panel | `#F5F3EE` | `#253033` |
| Main text | `#20282D` | `#F2F6F3` |
| Secondary text | `#5D676C` | `#B4C0BB` |
| Border | `#D7DDD9` | `#4A5A56` |
| Accent/primary | `#21645A` | `#8ED6BD` |
| Primary foreground | `#FFFFFF` | `#12382C` |
| Selected tint | `#EAF5EF` | `#223F36` |
| Disabled action fill / text | `#DFE6E1` / `#59655E` | `#34443C` / `#BAC8C0` |
| Urgent deadline fill / text | `#FFF0D2` / `#775004` | `#4A3B1D` / `#F7D58A` |
| Success panel fill / text | `#EAF5EF` / `#21645A` | `#223F36` / `#8ED6BD` |
| Item teal / coral / indigo tile | `#DDEFE9` / `#F8E2D9` / `#E4E5F5` | `#28483E` / `#52382F` / `#353951` |

The ordinary deadline uses neutral panel/text colors. Status and option tags use selected tint/accent colors. Disabled options retain legible secondary text and show their reason; do not fade the whole subtree into illegibility. Pixel grading accepts small antialiasing/color-management differences (RGB channel delta ≤12 for sampled flat fills) and native progress/icon/checkbox shapes, but it requires each color role and visible selected/disabled distinction.

Layout is directional: leading item tile, option indicator, panel padding and trailing amounts mirror in RTL. Text uses the host's natural layout direction. Keep caller strings intact, including their punctuation and bidirectional marks. At narrow widths or enlarged text, stack an amount under its label rather than shrinking text or obscuring another control. Long unbroken IDs may wrap at character boundaries. A selected option's detail panel belongs after the entire option list, not embedded in an unrelated option.

## P06. Native semantics and identifiers

The following stable identifiers are observable in the native accessibility/test tree: Android `Modifier.testTag`, Apple `accessibilityIdentifier`. Identify actionable parents without hiding their meaningful text or nested independent controls. Do not merge the entire card into a single accessibility element.

| Identifier | Meaning |
| --- | --- |
| `rr.card` | component root |
| `rr.header.title`, `rr.header.badge`, `rr.item`, `rr.deadline` | heading, status, item summary, optional deadline |
| `rr.option.<id>`, `rr.option.<id>.reason` | each option control and its optional disabled reason |
| `rr.detail`, `rr.sizes`, `rr.size.<id>`, `rr.size.<id>.reason` | selected detail panel, conditional size group, each size, optional unavailable reason |
| `rr.ack` | conditional acknowledgement control |
| `rr.notes.toggle`, `rr.notes.body` | notes disclosure control and expanded content |
| `rr.breakdown`, `rr.summary`, `rr.gate` | editing amount rows, always-visible total group, editing helper message |
| `rr.primary`, `rr.keep`, `rr.progress`, `rr.result`, `rr.done` | status-specific controls/panels |

Identifiers whose regions are absent must not appear as hidden accessible controls. Set the heading's native heading trait. Hide decorative icons from accessibility. The item exposes its complete supplied text. Each option exposes title, description, amount, tag if present, and disabled reason if present. Each size exposes its label and unavailable reason if present. Names must not be replaced solely by internal IDs.

- Android options use radio-button role, native selected state, and enabled state. Apple options use button and selected traits plus enabled/disabled state. Size choices use a button or radio-button role and native selected state. A disabled/stale match is not selected.
- The acknowledgement exposes checkbox/toggle semantics and its on/off state on Android. On Apple an accessible checkbox-style button is allowed, with `checkedValue`/`uncheckedValue` as its accessibility value. Its name includes the complete caller label.
- The notes control is a button named by `notes.title`, with expanded/collapsed state exposed through a native expanded property or `expandedValue`/`collapsedValue` accessibility value. The visual chevron must agree.
- Primary, keep and done are individually discoverable native buttons with their exact supplied label and current enabled state. Controls support native accessibility activation in addition to taps. Disabled option, size, and primary activations emit no action.
- Progress has `busyValue`; complete result exposes all three caller result strings. Accessibility read order follows visual reading order. Native button/radio/checkbox selected roles may differ only as specified above.

## P07. Evidence and acceptance

Provide source plus an externally constructible native demonstration/harness. Use the models as real inputs; a screenshot-only facsimile is insufficient. Record each callback from actual control activation, including an interval without caller echo. Caller replacement must use the same live component instance, not restart the app for every state.

Evidence is assessed atomically. Rendered screenshots establish visible pixels, text, colors and clipping. Runtime native bounds establish measured placement and hit-target geometry. Runtime resolved-font/layout instrumentation establishes native font family, base text size and actual native scaling. Runtime accessibility trees establish actual names, roles, values, identifiers and enabled/selected state. Actual interaction/callback traces establish emitted actions and absence of actions. Source inspection establishes API and minimum deployment compatibility. One kind does not automatically prove another. Missing or inaccessible evidence is **unassessed**, never a pass. Do not claim an entire rule passed while any mandatory sub-aspect is unassessed. The reference SVG is not runtime evidence.

All initial and repair-holdout cases follow this contract. Expect caller replacement, long strings, caller-formatted amounts, stale IDs, unavailable choices, both notes states, all statuses, optional acknowledgement, and changes in effective selection. No particular fixture text, hidden input, exact font glyph, animation timing, or exact text line break is required by this public brief.
