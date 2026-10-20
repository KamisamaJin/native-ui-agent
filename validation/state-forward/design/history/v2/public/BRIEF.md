# Print Batch Approval — fixed public brief

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
