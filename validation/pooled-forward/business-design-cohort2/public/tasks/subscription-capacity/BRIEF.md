# Subscription capacity change

Build the API in API.md, following this complete public rule set and the sealed
public expected-state table. Private testing adds inputs and paths under these same
rules. It introduces no new requirements or hidden flags.

## Business inputs and decisions

`fixture.schema.json` fixes every input type and valid range. Inputs contain raw
request facts and display content only, with no selected/ready/expected/decision fields.
`entityID` is a nonempty delimiter-free identifier; `revision` is a caller-published
nonnegative revision. Empty notes are valid; render their joined text as an empty
label without a placeholder. All title/context/notes strings wrap completely.

Package-level choice labels and IDs are constant, in this order:

- `scale` — **Scale plan**.
- `team` — **Team plan**.

Dependent choice labels and IDs are constant, in this order:

- `annual` — **Annual billing**.
- `monthly` — **Monthly billing**.

Eligibility is deterministic and uses inclusive boundaries exactly as written:

1. Scale plan is eligible when seatCount is at least 10 and at most scaleQuota.
2. Team plan is eligible when seatCount is between 2 and 25 inclusive and at most teamQuota.
3. Annual billing is eligible only for Scale plan and when prepaidMonths is at least 12.
4. Monthly billing is eligible for either selected eligible plan when accountBalanceCents is nonnegative. A negative balance blocks Monthly, independently of plan capacity.

All options remain in the document, including unavailable ones. A detail is enabled
only when a root is currently selected and its own eligibility predicate is true.
Disabled rows preserve their natural labels and provide native disabled semantics.
Each choice and confirmation is a native Button with an exact visible label. A
selected button has native selected semantics plus a visible check indicator.
There are no popups, dialogs, menus, overlays, lazy containers, or internal scrolling.

## Transient state and dependency ordering

A fresh instance has no root or detail selected, confirmation false, and no receipt.
Choosing a different eligible root clears detail and confirmation. Choosing a
different eligible detail clears confirmation. Tapping the already selected root
or detail is idempotent and preserves dependent state. Confirmation is a toggle
button labelled **I confirm the capacity commitment**, enabled only while valid root and detail exist.

**Record capacity change** is enabled only when root and detail remain eligible, confirmation
is true, and no request is recorded. A successful actual activation emits exactly
one callback, synchronously, before setting the receipt and locking choices,
confirmation, and primary action. Disabled controls never invoke a business handler.
Selection changes, confirmation toggles, and caller updates emit no callbacks.

Callback grammar, using the selected stable IDs, has no spaces:

`capacity|<entityID>|<revision>|<rootID>|<detailID>|<seatCount>`

The recorded display is **Capacity change recorded.**; before recording it is **No request recorded.**
No raw callback transport string is displayed to the operator.

For every caller replacement, first compare `(entityID, revision)` to the previous
input. A changed entity OR changed published revision resets all local state,
including a recorded receipt, even when other values match. No indistinguishable
same-value callback epoch or host-index reset is required. For the same pair,
preserve valid state and any receipt; update all display content immediately.
Re-evaluate root eligibility before detail eligibility. An invalid selected root
clears root, detail, confirmation, and receipt. Otherwise an invalid selected detail
clears detail, confirmation, and receipt. Remaining valid selections/confirmation
and a receipt are preserved, even if other raw facts change. Reconciliation emits
no callback and uses no forced view identity in the bridge.

## Exact text generation

Display notes as `notes.joined(separator: "\n\n")` / `joinToString("\n\n")`.
Render a stable summary in this exact order, substituting full visible choice labels
or **Not chosen**:

`Plan: <root label>. Term: <detail label>. <seatCount> seats.`

Status uses the first matching branch:

1. Recorded: `Recorded. Selections are locked for this request.`
2. No eligible root: `No plan is eligible for these request details.`
3. Root unselected: `Choose a plan.`
4. Detail unselected: `Choose a billing term for <root label>.`
5. Confirmation false: `Confirm the capacity commitment to continue.`
6. Ready: `Ready to record capacity change.`

The reference table fixes all public state strings, selected/disabled controls,
and callback deltas from this grammar. It is normative and independently authored.

## Layout, visual semantics, and evidence scope

Use DESIGN.md, tokens.json and the authored SVGs. Dynamic text must grow vertically,
remain at its specified native type size, and never truncate, shrink, or overlay.
The host owns the only vertical scroll; the component fills its finite offered
width. Long title, context, notes, summary, and receipt must all remain reachable.
Do not move UI into the bridge or special-case a fixture value or state label.

Minimal local observation tags are listed in bindings.*.json. They apply only to
the real component's surface and dynamic Text nodes. Natural action labels identify
buttons; there is no global ID registry or test-only replacement UI.

Native semantics, native AX/Compose control-box geometry, and automatic opaque RGB
gutters have separate claims. iOS public AX cannot measure generic SwiftUI computed
fonts, padding, or colors. iOS typography/wrapping use source-backed visual Boolean
questions; exact native font/color slots are explicitly N/A in MASTER-DENOMINATOR.
Android adds precise available TextLayout facts. These are planned observations,
not results, source approvals, or claims of native execution.
