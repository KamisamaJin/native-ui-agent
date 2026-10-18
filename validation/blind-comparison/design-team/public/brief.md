# Attachment transfer queue panel

Build a reusable native attachment transfer panel for Reply (Compose) and AlertToast (SwiftUI). This is a new queue surface, independent of the old email attachment presentation. A person should immediately see whether a queue needs attention, inspect file progress, expand the queue, and retry a failed file. Both implementations must express the same product behavior.

The first version should be achievable in about 20 minutes. Use native text, shapes, controls, and a simple document glyph. Do not fetch assets, add networking, simulate transfers, or build a surrounding screen. `reference.svg` illustrates the intended hierarchy; the numbered rules below resolve any ambiguity in the illustration. All evaluated requirements are public here. Evaluation may combine inputs in ways not pictured in the reference.

The common host uses the project's original theme and native light/dark environment. Its viewport is 390 logical units wide normally or 320 in the narrow configuration, with 16-unit left/right margins and 24-unit top placement. Thus the component is offered 358 or 288 units. Canvas height is 620 or 800; the host owns vertical scrolling for taller content. The component supplies its specified internal colors rather than relying on unpublished theme tokens. Android evaluation can use real Compose semantics, TextLayoutResult, and native click actions. iOS evaluation has real native PNGs and Apple Vision OCR. The common iOS unit-test host's AX export is unavailable even for a known identifier-bearing probe, so iOS accessibility declarations are checked by source review, and actions without a real UI event are `not_executed`. An empty iOS AX export alone is not a component defect. A source-reviewed action is not reported as an executed tap.

One public example, pictured in the reference, is the following queue in the listed order. It is suitable for implementation self-checks. With `expanded = true`, summary is `1 needs retry`, count is `1 of 4 complete`, aggregate is `45%`, all four rows show, and only `archive` has Retry. With `expanded = false`, only `labels` and `audio` show, `+2 more attachments` appears, and the same error summary and aggregate remain.

| ID | Name | Status | Progress |
| --- | --- | --- | --- |
| labels | Shipment labels.pdf | done | 1.0 |
| audio | studio-audio.wav | running | 0.46 |
| archive | Portfolio archive.zip | failed | 0.33 |
| notes | Team notes.txt | queued | 0.0 |

## API and ownership

**TQ-API-01 — Integration contract.** Add `ReplyTransferPanel.kt` in package `com.example.reply.ui.components`, exposing:

```kotlin
data class TransferItem(
    val id: String,
    val name: String,
    val status: String,
    val progress: Double,
)

@Composable
fun ReplyTransferPanel(
    items: List<TransferItem>,
    expanded: Boolean,
    onToggle: () -> Unit,
    onRetry: (String) -> Unit,
    modifier: Modifier = Modifier,
)
```

Add `TransferToastPanel.swift` to the AlertToast library target. Expose the following public types, public stored values, and public initializers. Additional conformances such as `Identifiable` are fine.

```swift
public struct TransferToastItem {
    public let id: String
    public let name: String
    public let status: String
    public let progress: Double
    public init(id: String, name: String, status: String, progress: Double)
}

public struct TransferToastPanel: View {
    public init(
        items: [TransferToastItem],
        expanded: Bool,
        onToggle: @escaping () -> Void,
        onRetry: @escaping (String) -> Void
    )
    public var body: some View { get }
}
```

Swift must remain compatible with the package's iOS 14 / macOS 11 minimums. Do not require a new dependency, a hosting application change, or a newer OS API without a compatible fallback. Compose callers must be able to supply their usual `Modifier`.

Inputs have unique, nonempty IDs; nonempty names may contain spaces, non-Latin text, punctuation, emoji, or long unbroken strings. `status` is exactly one of `queued`, `running`, `failed`, `done`. Unsupported status tokens are outside this task. Progress can be any `Double`, including nonfinite values.

**TQ-API-02 — Controlled component.** Render the supplied values. Keep queue state and expansion state with the caller. Do not mutate or reorder items, generate timer-based changes, persist retry state, or optimistically remove failures. The caller may change `items`, `expanded`, theme, font settings, or layout direction at any time; the next composition/render must reflect those values. There is no required animation.

## Derived state and exact copy

**TQ-STATE-01 — Stable order and status authority.** Rows preserve input order. The status token controls presentation even when progress appears inconsistent: a `running` item at 100% remains running, a `done` item at 0% is complete, and a `failed` item at 100% still offers retry. Do not infer a new status from progress.

**TQ-STATE-02 — Safe progress and rounding.** First compute `p = 0` for NaN, positive infinity, or negative infinity; otherwise clamp progress to `[0, 1]`. The effective contribution `e` is `0` for queued, `1` for done, and `p` for running or failed. Display percentages as `floor(value * 100 + 0.5)` followed immediately by `%` (nearest whole percent, halves upward). Never display `NaN`, infinity, negative percentages, percentages over 100, or an indeterminate spinner. A running item's bar uses `p`, including a completely empty bar at zero and a full bar at one.

**TQ-STATE-03 — Queue summary priority.** Count the whole queue, including hidden rows. Let `N` be total, `F` failed, `R` running, `Q` queued, and `D` done. Choose exactly one summary by this priority:

| Condition, first match wins | Exact summary | Tone |
| --- | --- | --- |
| `N == 0` | `No transfers` | neutral |
| `F == 1` | `1 needs retry` | error |
| `F > 1` | `{F} need retry` | error |
| `R > 0` | `{R} transferring` | accent |
| `Q > 0` | `{Q} waiting` | neutral |
| otherwise | `All transfers complete` | success |

The header title is always `Attachment transfers`. Show an 8-unit tone-colored dot beside the summary; text must convey its meaning without the dot.

**TQ-STATE-04 — Whole-queue aggregate.** For nonempty queues, show `{D} of {N} complete` and the aggregate percentage on one flexible row, then a determinate aggregate bar. The aggregate fraction is `sum(e) / N`; it includes failed partial progress and every hidden row. Its fill uses the summary tone. This is a transfer-work indicator, so it can read 100% while a status still needs retry. The displayed completion count remains based only on `done` tokens.

**TQ-STATE-05 — Empty state.** For zero items, show the title, `No transfers`, and `Add an attachment to get started.` Hide the count, aggregate percentage/bar, list, overflow hint, and toggle. Empty state is identical for either `expanded` value. It has no enabled action.

**TQ-STATE-06 — Per-file copy.** Every visible row shows its file name and exactly one status label:

| Token | Exact row label | Progress bar | Retry control |
| --- | --- | --- | --- |
| queued | `Waiting` | absent | absent |
| running | `{rounded p}% sent` | determinate | absent |
| failed | `Failed · retry available` | absent | visible, label `Retry` |
| done | `Complete` | absent | absent |

The status text and document glyph use neutral/accent/error/success respectively. All four states use the same row structure. No thumbnail, file size, cancel control, or extra per-file action is required.

## Expansion and actions

**TQ-LIST-01 — Preview and expansion.** For `N <= 2`, show every row and hide the toggle and overflow hint, regardless of `expanded`. For `N > 2`, show all rows when expanded and only the first two when collapsed. A collapsed queue ends with `+1 more attachment` or `+{N-2} more attachments`, in secondary caption text. Expanded queues have no overflow hint. The hidden rows must also be absent from the accessibility tree. The panel grows to fit its content; scrolling belongs to its parent. Do not create an inner scroll area or a fixed panel height.

**TQ-ACT-01 — Toggle.** For `N > 2`, show a real button in the header with `Show all` + downward chevron when collapsed, or `Show less` + upward chevron when expanded. Its accessibility label is respectively `Show all attachments` or `Show fewer attachments`, and its accessibility state/value is `Collapsed` or `Expanded`. One activation invokes `onToggle` exactly once. Invoking it does not itself change the visible rows until the caller changes `expanded`.

**TQ-ACT-02 — Retry.** Each visible failed row has its own real `Retry` button. Its accessibility label is `Retry {full original file name}`. One activation invokes `onRetry` exactly once with that item's original, unchanged ID. It remains a failed row until the caller supplies a changed item. No retry control exists for other statuses or hidden rows.

**TQ-ACT-03 — Action boundaries.** Title, summary, file text, glyph, progress bar, overflow hint, and row background are informational. Tapping them does not invoke either callback. Do not make the entire panel/header/row a duplicate action. Buttons must remain independently reachable, with minimum 48 × 48 logical-unit hit targets, and have button accessibility roles/traits.

## Layout and typography

All geometry below uses logical units: dp in Compose, points in SwiftUI. Font sizes are sp or scalable system-point equivalents. Use platform system sans-serif fonts. Base measurements apply at the normal/default text category. Exact glyph shapes need not match across platforms.

**TQ-LAYOUT-01 — Container.** Fill the available width up to 560; center the panel if more width is offered. Supported supplied widths are 280 through 560. Use 16 padding on all four sides, a 20 corner radius, a 1-unit border, and no shadow or gradient. The panel height follows its content. Honor available width and the Compose caller's modifier.

**TQ-LAYOUT-02 — Hierarchy and spacing.** The order is header, summary, aggregate block (or empty helper), then file list, then optional overflow hint. At normal size and width above 340, place title at logical leading and toggle at trailing in a header at least 48 high. Summary is 4 below that header. Place aggregate count/percentage 12 below the summary, with the 6-high, fully rounded aggregate track 6 below the count row. Place the list 16 below the track. Rows have 12 vertical padding and 1-unit separators between rows, with no separator after the last. Each row has a 32 × 32 neutral-surface document-glyph cell, a 12 gap, then a flexible text column. Use a simple 20–24 glyph inside the cell and 8 cell corner radius. File name and status have a 4 gap. A running row has its 4-high rounded track 8 below the status, spanning its text column. In the wide/default layout, retry is trailing with a 12 gap from the text column. The overflow hint is 8 below the list. Empty helper is 12 below its summary.

**TQ-LAYOUT-03 — Type and control styling.** Use the following base sizes and weights; text must scale with the user's font preference. Do not counter-scale or cap accessibility sizes.

| Element | Size | Weight | Color |
| --- | --- | --- | --- |
| Title | 20 | semibold / 600 | primary text |
| Summary | 14 | semibold / 600 | summary tone |
| Count | 13 | regular / 400 | secondary text |
| Aggregate percentage | 13 | semibold / 600 | primary text |
| File name | 16 | medium / 500 | primary text |
| File status | 13 | regular / 400 | state tone |
| Toggle / retry labels | 14 | semibold / 600 | accent / error |
| Overflow hint | 12 | regular / 400 | secondary text |
| Empty helper | 13 | regular / 400 | secondary text |

Retry uses a 1-unit error-colored outline, 10 corner radius, at least 12 horizontal content padding, and a 48 minimum height / 72 minimum width. Its background is the panel color. Toggle is a plain text-and-chevron button without a surrounding filled box. A chevron is 12 units at base size. All labels may grow vertically at large sizes.

**TQ-LAYOUT-04 — Long text and reflow.** File names use at most two visible lines with end ellipsis at default text sizes; use at most three lines at accessibility sizes. Their full original text remains available to assistive technology. Title, summary, counts, status labels, buttons, empty helper, and overflow hint must wrap as necessary without truncation. Use the compact arrangement when the supplied panel width is **340 or less**, or when Android font scale is **1.6 or more**, or SwiftUI `sizeCategory.isAccessibilityCategory` is true. In that arrangement, put the toggle on its own line below the title, aligned leading, and put a failed row's retry button below its status with an 8 gap, aligned to the text column's leading edge. Keep the document cell beside the text column. Keep the aggregate percent at trailing when it fits, otherwise move it to the next line. Space increases caused by wrapping are expected. No horizontal overflow, overlap, clipped action label, or compressed hit target is acceptable.

**TQ-LAYOUT-05 — Directionality.** Respect the native layout direction. In RTL, the document cell is at logical leading, controls align to logical trailing in the wide arrangement, compact controls align to logical leading, and progress fills grow from logical leading (right to left). Keep text in native bidirectional order; do not reverse file names or digits. Vertical chevrons do not change direction.

## Color and visual finish

**TQ-COLOR-01 — Adaptive palette.** Use these colors in their respective system light/dark appearances. RGB flat-color sampling tolerates minor rendering variation; do not substitute a different theme palette.

| Token | Light | Dark |
| --- | --- | --- |
| Panel | `#FFFFFF` | `#182235` |
| Border | `#D7DFEB` | `#34445F` |
| Primary text | `#17243B` | `#F2F5FB` |
| Secondary / neutral | `#526279` | `#B9C5D9` |
| Neutral surface | `#F1F4F9` | `#24324A` |
| Track / separators | `#E2E8F2` | `#34445F` |
| Accent | `#275DD8` | `#9DBDFF` |
| Error | `#B3313B` | `#FFADB3` |
| Success | `#13795B` | `#7CDDBB` |

The reference host background is `#EDF2F8` / `#0C1424`, supplied by the host and outside the component. **TQ-COLOR-02 — State mapping.** Apply tone consistently to summary dot/text, aggregate fill, file status/glyph, and retry outline/text as specified above. Neutral surfaces and tracks remain visible in both appearances. Progress fill may disappear at exactly zero; its track must remain visible.

**TQ-VIS-01 — Visual hierarchy.** Match the reference's quiet, compact queue-card composition: clear title, readable summary and total progress, consistent file rows, and locally prominent retry buttons. Use native text and crisp, simple vector shapes. Content must look intentionally aligned and spaced rather than like an unstyled debug stack. The reference's surrounding annotations are not part of the component.

**TQ-VIS-02 — Readability and finish.** At supported widths, themes, text sizes, and directions, text and controls remain legible and separated. No accidental clipping, overlap, broken glyph, clipped progress fill, or content outside the border. A very tall panel may extend below a viewport if its parent can scroll; this is not clipping by the component. Platform font differences, anti-aliasing, and the exact document glyph are acceptable.

## Accessibility and test observability

**TQ-A11Y-01 — Stable identifiers.** Attach the following test tags in Compose and accessibility identifiers in SwiftUI to the corresponding visible elements. These are observation hooks, not visible strings. Keep child controls and texts independently observable. Do not add hidden duplicates solely for testing.

| Identifier | Element |
| --- | --- |
| `transfer.panel` | outer container |
| `transfer.title` | title text |
| `transfer.summary` | exact summary text |
| `transfer.count` | completion-count text, only nonempty |
| `transfer.percent` | aggregate percentage text, only nonempty |
| `transfer.progress` | aggregate progress bar, only nonempty |
| `transfer.toggle` | toggle button, only when N > 2 |
| `transfer.list` | visible-row container, only nonempty |
| `transfer.more` | collapsed overflow hint, only when applicable |
| `transfer.empty` | empty helper, only when empty |
| `transfer.row.{id}` | a visible row, using the original ID |
| `transfer.name.{id}` | its file-name text |
| `transfer.status.{id}` | its exact status text |
| `transfer.progress.{id}` | its progress bar, only running |
| `transfer.retry.{id}` | its retry button, only failed |

**TQ-A11Y-02 — Accessible meaning.** Expose full names, the status text, and button labels/roles above. The aggregate bar's accessible label is `Overall transfer progress`; a running bar's is `{full original file name} transfer progress`. Both expose a determinate normalized fraction in `[0,1]` through native progress semantics where supported, plus an accessible percentage equal to the displayed rounding (e.g. SwiftUI accessibility value `42%`). Compose must expose `ProgressBarRangeInfo` with range `0f..1f`; a readable percentage content/state description may supplement it. Decorative document glyphs, dots, and chevrons must not create extra focus stops or duplicate announcements. Focus/read order follows visible input order and keeps each retry with its file. Hidden rows have no accessibility elements.

## Acceptance and self-review

Build/render failure is a separate blocking defect. Unexecuted interactions, unavailable semantics, or missing evidence are **not scored as passing**. Native semantics can check text, visibility, values, roles, order, and real callback events; native PNGs can check geometry and colors. API/platform compatibility requires build/source evidence. Native font rendering and overall visual quality require an anonymous visual review by an independent AI reviewer, not a human expert. Layout tolerances at default text size are ±2 logical units, color tolerances ±12 per RGB channel on flat interior samples, and normalized native progress tolerance is 0.002. No literal pixel comparison across operating systems is expected.

After the first implementation is frozen, perform a read-only self-review against this brief and your own public/input examples; do not edit that frozen source during the self-review phase. If asked to produce `self_review.json`, report observed defects by the exact public rule IDs. A useful record is `{ "rule_id": "TQ-LAYOUT-04", "case": "my narrow example", "observation": "Retry label is clipped at the trailing edge", "evidence": "path or measured value", "execution": "observed" }`. Record checks without execution as `not_executed`, not as defects found or tests passed. Generic statements such as “RTL may be risky” are not an observed issue. Hidden evaluation and any later repair use only the requirements in this brief.
