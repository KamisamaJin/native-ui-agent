# Service visit rescheduling panel

Create one reusable native component in Compose and SwiftUI. A household customer wants to move a booked service visit. They inspect windows, choose one, accept a fee when required, and confirm. This is a controlled component: the caller owns selection and fee acceptance.

Deliver new production component/model files for the existing projects. Preserve Swift iOS14/macOS11 and the project's current Compose dependencies. Use native text/controls and system fonts, with simple native/vector symbols. Do not add packages, web views, assets, app navigation, or a custom renderer.

## Public API

Use these exact public names and properties. Swift models are Codable, have public stored properties and explicit public initializers. Optional fields may default to nil and arrays to empty. Kotlin uses equivalent data classes. All IDs are unique. Required strings and present optional strings are nonempty. All date/time/amount strings are display-ready: render without parsing or calculation.

```text
VisitRescheduleMode = loading | choosing | unavailable | confirmed
VisitSlotAvailability = available | limited | unavailable
VisitAppointment { dayLabel: String, timeLabel: String }
VisitSlot {
  id: String, timeLabel: String, detail: String,
  availability: VisitSlotAvailability,
  feeLabel: String?, unavailableReason: String?
}
VisitSlotGroup { id: String, dayLabel: String, slots: [VisitSlot] }
VisitConfirmation {
  appointment: VisitAppointment, reference: String, note: String
}
VisitRescheduleModel {
  mode: VisitRescheduleMode,
  serviceTitle: String, location: String,
  currentAppointment: VisitAppointment,
  groups: [VisitSlotGroup], selectedSlotId: String?, feeAccepted: Bool,
  unavailableMessage: String?, confirmation: VisitConfirmation?
}
```

Swift enum cases use the lowercase spellings above as raw JSON values. Kotlin enum cases use `Loading`, `Choosing`, `Unavailable`, `Confirmed`, and `Available`, `Limited`, `Unavailable`. Nil feeLabel means no fee. unavailableReason is required for unavailable slots. unavailableMessage is required in unavailable mode; confirmation is required in confirmed mode. Choosing has at least one group and slot. Other modes may carry stale chooser fields, which must be ignored. Unknown JSON properties may be ignored.

```swift
public struct VisitReschedulePanel: View {
    public init(model: VisitRescheduleModel,
                onAction: @escaping (VisitRescheduleAction) -> Void)
}
public enum VisitRescheduleAction {
    case selectSlot(String)
    case setFeeAccepted(Bool)
    case confirm(String)
    case retry
    case done
}
```

```kotlin
@Composable
fun VisitReschedulePanel(
    model: VisitRescheduleModel,
    onAction: (VisitRescheduleAction) -> Unit,
    modifier: Modifier = Modifier
)
sealed class VisitRescheduleAction {
    data class SelectSlot(val slotId: String) : VisitRescheduleAction()
    data class SetFeeAccepted(val accepted: Boolean) : VisitRescheduleAction()
    data class Confirm(val slotId: String) : VisitRescheduleAction()
    object Retry : VisitRescheduleAction()
    object Done : VisitRescheduleAction()
}
```

The host receives JSON under `model`; `environment` is host configuration, not a product property. The bridge encodes events as `select_slot:<id>`, `fee_accepted:true|false`, `confirm:<id>`, `retry`, `done`. This encoding stays outside production. For test interactions the caller echoes selectSlot by replacing selectedSlotId and clearing feeAccepted only when the ID changes; it echoes setFeeAccepted by replacing that Boolean. Confirm/retry/done are recorded without automatically changing mode. Caller updates replace the entire model. Never retain a competing local copy of selection/consent.

## Acceptance rules

All requirements are public. Evaluation may vary every valid string, group/slot count, state, selection, theme, font, direction, and sequence of caller updates.

| Rule | Requirement |
|---|---|
| R01 — Production API | Provide the public native production API above, constructible by callers. Preserve deployment compatibility and existing dependencies. |
| R02 — Shared context | Every mode shows full serviceTitle, location and current appointment day/time. Title: `Reschedule visit`, except confirmed: `Visit rescheduled`. Current label: `Current appointment`, except confirmed: `Previous appointment`. Preserve all supplied strings. |
| R03 — Choices | Only choosing renders groups/slots, in caller order. Each group shows dayLabel; each row shows time, detail and availability. Available: `Available`; limited: `Few left`. Eligible rows show `No fee` or `<feeLabel> fee`. Unavailable rows show `Unavailable` and their full reason instead of fee metadata. |
| R04 — Effective selection | Selection exists only in choosing when selectedSlotId matches an available/limited slot. Exactly that row is visually and natively selected. Missing/unavailable IDs yield no selection even with feeAccepted=true. Never auto-select a row. |
| R05 — Row actions | Activating an eligible unselected complete row emits exactly one selectSlot(id). Activating the selected row emits nothing. Unavailable rows are natively disabled and emit nothing. Use a radio-style affordance. |
| R06 — Summary/guidance | A valid selection shows `New appointment`, selected group day/time, and `No rescheduling fee` or `Rescheduling fee` plus amount. Nil selection: no summary and `Choose one appointment to continue.` Supplied invalid/unavailable ID: no summary, an amber `That appointment is no longer available. Choose another time.` warning, and no ordinary guidance. Valid fee selection awaiting consent: `Agree to the fee to continue.` Valid no-fee or accepted fee: `Your current time stays reserved until you confirm.` |
| R07 — Fee consent | Only a valid fee selection shows a native checkbox/toggle labeled `I agree to the rescheduling fee of <feeLabel>.` Value is supplied feeAccepted; activation emits exactly one setFeeAccepted(!feeAccepted). Hide for no-fee, invalid selection, and non-choosing. Do not cache approval. |
| R08 — Confirmation | Choosing has full-width `Confirm new time`, natively enabled exactly when selection is valid and either no fee or feeAccepted=true. Enabled activation emits exactly one confirm(effectiveSlotId); disabled emits nothing. Rendering/data updates emit no confirm/retry/done. |
| R09 — Caller updates | The replacement model immediately controls mode, row content/order/availability, selection and fee value. A selection that becomes unavailable or disappears immediately follows R04/R06/R08. Interactions/rendering never mutate caller data. |
| R10 — Loading | Below shared context, show a small native progress indicator and `Checking available appointments…`. Hide groups, summary/warning, consent, guidance and every action, including stale input. |
| R11 — Unavailable | Show `No appointments available`, full unavailableMessage, and enabled full-width `Check again` emitting exactly one retry. Hide chooser, summary/warning, consent, ordinary guidance, confirm and done. |
| R12 — Confirmed | Use green success treatment with `New appointment confirmed`, confirmation day/time, `Reference: <reference>`, full note and enabled full-width `Done` emitting exactly one done. Hide chooser, summary/warning, consent, ordinary guidance, confirm and retry. Never substitute the old appointment for the new one. |
| R13 — Native accessibility | Actual native controls expose row selected/disabled state, fee accepted state and button enabled state. Each coherent row label includes group day, time, detail, availability and fee/reason. No duplicate activatable row controls. Use IDs below and meaningful context→groups→summary/warning→consent→guidance→action order. Targets at least44×44pt Apple/48×48dp Android. |
| R14 — Visual treatment | Follow the independent SVG's hierarchy, surfaces, radio/selection treatment, generous vertical rhythm and full-width action with the tokens below. Use system fonts and simple radio icons, amber warning, green success. Disabled content stays readable. Native font/icon details may vary. |
| R15 — Adaptive content | At panel widths288/358 all fixed/supplied text wraps fully: no ellipsis, line limits, horizontal scroll, clipping, overlap or fixed-height text boxes. Long amounts, labels, locations, notes/reasons expand rows. Respect font sizes up to2.0× or Apple accessibility equivalent without shrinking text to fit. Keep controls operable. |
| R16 — Parent scroll | Host parent vertical scroll viewport600 must expose all content and the final action through ordinary scrolling. Panel grows to content; no nested vertical scroll, fixed panel height or lazy stack requiring bounded viewport. |
| R17 — Theme/direction | Support light/dark and native RTL. Use leading/trailing layout. Radio affordances mirror in RTL, while date/time/amount strings remain intact and readable. Maintain contrast, including disabled rows/buttons. |

## Visual specification

Host canvas light#EDF1F6/dark#0D1420, horizontal16/top24 margins supplied by host. Add no outside margin. Panel fills available width; radius20, padding16. Inset cards/rows radius12/padding12; section gap20, row gap10, group-heading-to-row10, ordinary text gaps4–8. Normal row border1, selected outline2. Radio diameter20 and text gap12. Metadata flows below time/detail, wrapping freely rather than a fixed trailing column. Unavailable rows use readable secondary foreground and full opacity. Primary min-height48, radius12, horizontal padding16 and control separation12; height grows with fonts.

| Token | Light | Dark |
|---|---|---|
| Panel | #FFFFFF | #161C27 |
| Primary text | #182230 | #F2F4F7 |
| Secondary text | #526174 | #B8C4D4 |
| Neutral inset | #F4F6F9 | #202938 |
| Border | #D5DDE7 | #485568 |
| Accent/selection outline | #175CD3 | #84ADFF |
| Selected fill | #EFF6FF | #162F51 |
| Warning text/fill | #854A0E / #FFF7E0 | #FFD691 / #3B2D17 |
| Success text/fill | #087443 / #EAFBF2 | #75E0AD / #163629 |
| Enabled primary fill/text | #175CD3 / #FFFFFF | #84ADFF / #10213D |
| Disabled primary fill/text | #E4E7EC / #667085 | #344054 / #B8C4D4 |

Baseline system typography pt/sp (size/line-height): title22/28 semibold; service and slot time17/23 semibold; group15/20 semibold; body/location/detail14/20 regular; metadata/context labels13/18 regular/semibold; button16/22 semibold. Scale with platform font settings. Ordinary visual tolerance: spacing±2 logical units, baseline size±1.5, flat fills±8 per RGB channel; allow native antialiasing. At large fonts readability/wrapping outranks identical line breaks or accumulated height.

## Native IDs and observations

Expose these as Compose test tags/native semantics and Apple accessibility identifiers on actual meaningful nodes. IDs exist only with their corresponding element. Do not add hidden proxy controls or accessibility-only duplicates.

- `visit.panel`, `visit.title`, `visit.service`, `visit.location`, `visit.current`
- `visit.group.<groupId>` on group headings; `visit.slot.<slotId>` on whole native row targets
- `visit.selection_summary`, `visit.selection_warning`, `visit.guidance`
- `visit.fee_consent`, `visit.confirm`, `visit.retry`, `visit.done`
- `visit.loading`, `visit.unavailable`, `visit.confirmation`, `visit.reference`

Protocol observation IDs: `initial`, `after_select`, `after_fee_on`, `after_fee_off`, `after_confirm`, `after_retry`, `after_done`, `after_update_1`, `after_update_2`, `scroll_<n>` as applicable. These label evidence checkpoints, not product nodes. Test-only traces and host IDs stay outside production.

## Complete public sample

This complete example illustrates the API and SVG, and is not an evaluation fixture. There are exactly6 initial evaluation fixtures and2 repair holdouts. Their concrete inputs/expected values are private; every requirement they exercise is public above.

```json
{
  "caseId": "public_example",
  "environment": {"width":390,"viewportHeight":600,"theme":"light","fontScale":1.0,"direction":"ltr"},
  "model": {
    "mode":"choosing",
    "serviceTitle":"Boiler safety inspection",
    "location":"18 Maple Street, Apartment 4B",
    "currentAppointment":{"dayLabel":"Friday, 23 October","timeLabel":"15:00–17:00"},
    "groups":[
      {"id":"mon","dayLabel":"Monday, 26 October","slots":[
        {"id":"mon_am","timeLabel":"09:00–11:00","detail":"Your engineer will call before arrival.","availability":"available","feeLabel":null,"unavailableReason":null},
        {"id":"mon_pm","timeLabel":"13:00–15:00","detail":"Priority afternoon window.","availability":"limited","feeLabel":"$20.00","unavailableReason":null}
      ]},
      {"id":"tue","dayLabel":"Tuesday, 27 October","slots":[
        {"id":"tue_am","timeLabel":"10:00–12:00","detail":"Standard morning window.","availability":"unavailable","feeLabel":null,"unavailableReason":"This window is fully booked."}
      ]}
    ],
    "selectedSlotId":"mon_pm","feeAccepted":false,
    "unavailableMessage":null,"confirmation":null
  }
}
```

Expected sample: mon_pm selected, checkbox off, summary Monday26 October/13:00–15:00/$20.00, confirm disabled. Fee tap emits setFeeAccepted(true); caller echo enables confirm, which emits confirm("mon_pm"). Tapping mon_am emits selectSlot("mon_am"); caller echo hides consent and enables free confirmation. Unavailable tue_am emits nothing.

## Evidence and reporting

Separate declarative source review from runtime evidence. Source can establish API, compatibility, layout choices and accessibility intent; it cannot alone prove native reachability, callbacks, updates, accessibility exposure or scrolling. Every runtime claim needs case/checkpoint/channel evidence. Label unavailable channels `missing evidence`; preserve unobserved separately from pass/fail.

Report distinct defect/root-cause cluster counts separately from failing case×rule counts, separately for each platform and initial/holdout phase. One cause can affect many case×rule pairs. Root-cause detection and exact-rule attribution are separate outcomes: a detailed shared-cause observation may detect its cluster without being credited as explicitly reporting every related rule. Attribute a rule only when its violation is actually identified with sufficient evidence.

Visual rubric per case/platform, with screenshot and rationale: **5** reference hierarchy/spacing/colors, readable content, only normal native differences; **4** minor cosmetic deviation without material hierarchy/readability harm; **3** material hierarchy/spacing/color deviations but usable content/actions; **2** severe clipping/overlap/contrast/layout disruption obscures important information/action; **1** intended panel/state largely absent or unusable. Missing screenshot is unscored. Callback-only failures do not automatically lower visual score.
