# Menu change review

Build one new native `MenuChangeReviewPanel` component on each platform. It lets the organizer of a catered community lunch approve a replacement for an unavailable dish. The organizer chooses a replacement, adjusts the serving count, applies an existing tray-return credit, checks the resulting balance, and sends one typed request to the kitchen. This is an embedded component PR: the caller owns scrolling, network delivery and navigation.

All product rules below are public. The private scope changes only caller data, the continuous action path and the native environment. Implement the general rules, including later revisions and unavailable options, without inspecting private files. There need not be a product defect in a natural first implementation.

## Deliverable and boundaries

Add only `alerttoast/Sources/AlertToast/MenuChangeReviewPanel.swift` and `reply/Reply/app/src/main/java/com/example/reply/ui/components/MenuChangeReviewPanel.kt`. Each file contains its platform's public DTOs, typed submission, component and private helpers. The Swift package is `AlertToast`, minimum iOS 14; the Android package is `com.example.reply.ui.components` using the existing Compose/Material3 dependencies. Do not change package/build files, use assets, add a network client or build an alternative UI in the observer bridge. `API.md` fixes the public interface and JSON keys.

The caller gives the component its finite width in a vertical scroll view. Use a non-scrolling vertical flow; every option, kitchen note and the bottom action remains in that flow. No fixed-height text, line limits, ellipsis or horizontal scrolling. The long notes deliberately represent real kitchen handling and service information. Do not shorten supplied text. The SVG is a structural wireframe, not a screenshot, scale-perfect layout or a pixel oracle.

## Business state

Local state is selected option ID (initially none), desired servings (initially `requestedServings`), whether to use tray credit (initially false), acceptance (initially false) and sent (initially false). The caller's DTO is immutable input. Prices and balances use integer cents; never use floating point for money.

An available option is selectable. After selection, clamp desired servings into that option's inclusive `minimumServings...maximumServings`. Selecting the already selected option does nothing. Selecting a different option clears acceptance. The plus and minus buttons change servings by one within those limits, clear acceptance, and are disabled without a selected option or after sending. The count is still displayed when nothing is selected. Options marked unavailable remain visible and disabled.

The tray-credit switch is enabled whenever `trayReturnCreditCents > 0` and the request is not sent. Toggling it clears acceptance. With a selected option, replacement total is `pricePerServingCents × servings`; applied credit is the DTO credit when the switch is on, otherwise zero. Signed balance is replacement total minus `prepaidTotalCents` minus applied credit. Positive balances display `Additional payment $N.NN`, negative balances display `Refund $N.NN` using the absolute magnitude, and zero displays `No balance due`. Do not clamp negative balances to zero. Money always uses an ASCII dollar sign, decimal point and exactly two digits, without locale grouping. This component's fixed labels are English; supplied Unicode strings are preserved.

The acceptance switch is enabled only with an available selected option and before sending. Its label is `I accept the replacement, serving count, and balance shown.` Turning it on accepts exactly the current selection, count and balance. Send is enabled only when a valid selection and acceptance exist and the component is not sent. On send, synchronously emit one `MenuChangeSubmission` with the exact currently visible values, then set sent. Disable all editable controls and label the button `Request sent`. Do not emit on selection, count, credit, acceptance or caller update. An already sent revision cannot send again. No timer or simulated network is needed.

Status copy, in precedence order:

1. Sent: `Request sent. Waiting for the kitchen.`
2. No selection: `Choose a replacement to continue.`
3. Selected, not accepted: `Review the balance and accept the updated menu.`
4. Selected and accepted: `Ready to send to the kitchen.`

## Updates without replacing component identity

The same component instance receives a newer DTO with the same `requestID` and a different `revision`. Immediately use every new input field and clear acceptance and sent. If the selected option ID still exists and is available, retain it and clamp the current desired servings to its new bounds. If it was removed or became unavailable, clear the selection and retain desired servings until the next selection clamps it. Retain the credit choice only while the new credit is positive; a zero credit forces the switch off. Recompute the visible total and signed balance from the new prices and credit. A different request ID resets all local state as on first presentation. Mere recomposition with the same `(requestID, revision)` must not reset user edits. A DTO revision identifies a complete immutable snapshot; callers do not mutate a snapshot in place.

Use normal SwiftUI/Compose state reconciliation. The host and bridge must not use `.id`, keyed component recreation, a new outer state holder or a cloned product view to implement this requirement. Business derivation and reconciliation belong in the production component file.

## Structure, native units and style intent

The component owns its full warm canvas, including its 16-unit outer gutters; the observer's canvas outside the component belongs to the host. Sections are ordered: header (eyebrow, occasion title, order/location/revision, original dish and response deadline), kitchen update notice, replacement choices, serving controls, tray-credit switch, balance card, kitchen notes, acceptance, status and send. Use leading/trailing alignment and native writing direction; do not reverse the underlying option array in RTL. All monetary and quantity rows are vertical label/value stacks when space is limited. Keep the quantity controls together in one native horizontal row with a wrapping count label if needed.

| Intent | iOS | Android |
|---|---:|---:|
| Root outer padding | 16 pt | 16 dp |
| Section gap | 20 pt | 20 dp |
| Card padding / corner radius | 12 / 16 pt | 12 / 16 dp |
| Inside-card gap / option gap | 8 / 8 pt | 8 / 8 dp |
| Notes paragraph gap | 10 pt | 10 dp |
| Footer gap | 16 pt | 16 dp |
| Border | 1 pt | 1 dp |
| Choice minimum height | 64 pt | 64 dp |
| Quantity buttons minimum width and height | 44 pt | 44 dp |
| Send minimum height / horizontal padding / vertical padding | 52 / 16 / 14 pt | 52 / 16 / 14 dp |
| Root corner radius | 20 pt | 20 dp |

| Text role | Base iOS pt / Android sp | Weight |
|---|---:|---:|
| Eyebrow | 12 | 500 |
| Occasion title | 28 | 700 |
| Context and detail | 13 | 400 |
| Section heading | 18 | 600 |
| Body and option title | 15 | 400 / option title 600 |
| Amount | 26 | 700 |
| Button | 16 | 600 |
| Serving count | 20 | 600 |

Use native system fonts. Base values above are source-style obligations, not generic SwiftUI runtime measurements. Scale all text with the caller's Dynamic Type / Compose font scale (iOS-14-compatible scaled metrics are suitable). Do not cap the approved large-text environment. Buttons and cards can grow vertically. Exact base font sizes, spacing and palette selection must be independently reviewed in the actual component source; actual hierarchy, wrapping and clipping are separate image observations.

| Color role | Light ARGB | Dark ARGB |
|---|---|---|
| Component canvas | `#FFF5F2EA` | `#FF101A15` |
| Card surface | `#FFFFFFFF` | `#FF19291F` |
| Main ink | `#FF1F2A25` | `#FFF2F7F3` |
| Secondary ink | `#FF59665E` | `#FFB8C8BC` |
| Accent / enabled send fill | `#FF216B4A` | `#FF8DDBAF` |
| Selected option fill | `#FFE9F3ED` | `#FF254735` |
| Border | `#FFCBD5CC` | `#FF3D5848` |
| Notice ink / notice fill | `#FF975A16` / `#FFFFF0D9` | `#FFFFCA80` / `#FF382A17` |
| Enabled send ink | `#FFFFFFFF` | `#FF102017` |
| Disabled send fill / ink | `#FFD9E2DC` / `#FF68756D` | `#FF344A3C` / `#FF93A99A` |

Cards use surface, unselected choices use surface, selected choices use selected fill and accent border. Show unavailable choices with secondary ink, retaining readable text rather than whole-row opacity. Use accent for a refund, main ink for an additional payment or zero balance. The top notice uses the notice colors. Sent controls use disabled treatment; keep all business text legible. The summary card remains a solid surface. Insets and palette are source intentions. The separate native-pixel atoms sample the component canvas gutter and the summary card gutter; they establish only their approved rendered regions. If a native semantic box cannot support a sample, the result stays unavailable and is investigated rather than guessed.

## Public continuous example

`cases/cedar-lunch/fixtures.json` has one initial DTO and one update. No reload occurs between these actions. The exact independent values are in `reference.json`; the table explains the business arithmetic.

| Selected state | Trigger / intended visible result |
|---|---|
| `draft` | Checkpoint; 12 servings, no choice, send disabled. |
| `replacement` | Choose `roast`; 12 × $11.00 − $120.00 = $12.00 additional payment. |
| `quantityChanged` | Increase to 13; $23.00 additional payment. |
| `ready` | Apply $9.00 credit, then accept; $14.00 additional payment, send enabled. |
| `sent` | Send revision 1 once with `roast`, 13, credit on, signed balance 1400 cents. |
| `revised` | Apply revision 2 in place; retain `roast`, clamp 13 to 12, retain positive credit, clear acceptance/sent; 12 × $10.50 − $120.00 − $5.00 = $1.00. |
| `readyRevised` | Choose `lentil`, decrease to 11, accept; 11 × $9.00 − $120.00 − $5.00 = −$26.00, displayed as a refund. |
| `sentRevised` | Send revision 2 once with `lentil`, 11, credit on, signed balance −2600 cents. |

The path observes eight business states, not a Cartesian product. Automatic state sweeps collect the long content at each selected state. Omitted intermediate observations do not acquire extra detection credit. Callback assertions concern their exact native action interval; additional no-callback requirements are also source obligations.

## Evidence and approval

`contract.json`, typed `reference.json`, `policy.json`, `routes.json`, fixtures and bridges are fixed before any product source exists. `prepare.py` only validates these inputs and mechanically seals/compiles them. `approval.json` is a preparation summary with status `awaiting_independent_design_review`; it is not an independent approval, a render result or a test pass. A separate reviewer must approve the sealed public and private scope hashes before implementation.

Every native/visual obligation has a complete route. Mandatory source duties are separately listed at `/responsibilities` and linked by `/source_obligation_routes` and the corresponding `routes.reason`. Those textual links establish independent association completeness only: the frozen route tool does not execute source routing. The default responsibility gate independently requires current source-review observations for those duties. Native geometry rules explicitly measure accessibility/control boxes, not layout padding or physical touch regions. No ordinary AX assertion claims an exact SwiftUI computed font or color. This experiment makes no whole-app navigation, keyboard, physical Android touch or real network claim.
