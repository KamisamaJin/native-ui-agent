# ListeningBreakPanel — independent product requirements

[R01] Add the standalone ListeningBreakPanel component in exactly the approved single production file on each platform; retain the upstream library/application and its existing behavior.

[R02] Expose the exact public, value-equatable data models and callable signatures in api-contract.json; the iOS component is a SwiftUI View available on iOS 14 and Android is a Compose @Composable in com.example.reply.ui.components.

[R03] Accept valid caller inputs with a nonempty sessionID, at least one available option, unique ASCII option IDs matching [A-Za-z0-9_-]+, nonempty copy, and caller-preserved option order; the component owns no audio engine or network operation.

[R04] Display this exact vertical order: input title, introduction, all option title/detail pairs in caller order, quietNote, fixed acknowledgement switch, status, conditional error, conditional success summary, primary action, Cancel action, and footer; display all caller copy verbatim.

[R05] Expose stable identifiers listening.canvas, listening.title, listening.introduction, listening.note, listening.acknowledge, listening.status, listening.primary, listening.cancel, listening.footer, listening.error and listening.summary; each option control uses listening.option.<id>.

[R06] Give each option one native button with accessible label title + " — " + detail and a selected trait that matches its local selection; the acknowledgement is one labeled native switch with its real Boolean value.

[R07] Begin editing with no selection, acknowledgement off, no error or success summary, status "Choose a soundscape for your break.", and enabled Start listening and Cancel controls.

[R08] Selecting an available option exclusively selects its ID; selecting it again preserves that selection, changing to another available option replaces it, and unavailable options remain disabled and never selectable.

[R09] While editing, a successful Start listening activation validates both an available selected option and acknowledgement on; unmet conditions leave editing active and show the applicable exact error text defined in api-contract.json without emitting onStart or onCancel.

[R10] On valid Start listening activation, enter the started state synchronously, show status "Your listening break is ready.", show summary "Ready to begin: " + selected option title, and invoke onStart(sessionID, optionID) exactly once for that activation.

[R11] In the started state, retain all caller content, preserve the selected option and on acknowledgement, disable every option and the acknowledgement, and change the enabled primary label to "Choose again".

[R12] A Choose again activation returns to the initial editing state for the current input, clears selection, acknowledgement, errors and summary, and emits no callbacks.

[R13] Cancel remains enabled in every state; each activation invokes onCancel(current sessionID) once and returns to initial editing for that same input, including repeated Cancel activations with no choices.

[R14] Changing either editing choice clears the visible validation error; turning acknowledgement off is allowed while editing and does not clear the selected option.

[R15] Any unequal full input replacement resets selection, acknowledgement, validation and started state before the replacement is rendered, even when sessionID and option IDs are unchanged; rendering an equal input preserves local state and neither case emits callbacks.

[R16] Keep the component identity and business logic in production: the supplied bridges adapt fixture values and real callback arguments only, and neither bridge may force identity changes, supply local product state, or synthesize callback outcomes.

[R17] Use exact opaque sRGB colors from reference.json: canvas behind the column and Cancel; option/selectedOption/unavailableOption on option surfaces; primary and primaryInk on the primary button; title on the heading; body on introduction, note, available option titles, acknowledgement, status, summary and Cancel text; muted on option details, unavailable option titles and footer; error on error text; border on every option outline; use no shadows, gradients or translucency.

[R18] Render the component canvas in its canvas role color throughout all states and the primary button in its primary role color in both Start listening and Choose again states.

[R19] Use a single column filling its parent content width (the observer offers total width minus its own 32-unit horizontal inset), with 20 native units of internal canvas padding, 12 units between major blocks and options, 12-unit option and action corner radii, 16-unit option/action horizontal padding and 12-unit vertical padding, and a 1-unit option border; each title/detail option pair has a 4-unit internal gap and actions fill the available column width.

[R20] Use platform-scaled system text at the base sizes and weights in reference.json: title 24 semibold, introduction/note/option title 16 regular except option title semibold, option detail/footer 14 regular, status/error/summary 16 regular, and action text 16 semibold.

[R21] Give the primary and Cancel native accessible/control rectangles minimum height 48 native units and minimum width 120 native units; option rectangles have minimum height 64 native units and may grow for content or text size.

[R22] Allow all supplied copy and action labels to wrap without truncation, ellipsis, text scaling down, horizontal scrolling, clipping, or overlap; use leading alignment and let the parent vertical scroller reach every item at offered widths 320 through 430 and system text sizes through iOS accessibility2 / Android fontScale 1.6.

[R23] Keep source font and padding review separate from native rectangle and text facts: AX bounds do not establish computed font, padding, color or physical hit regions.

[R24] The six route checkpoints and all assertions are fixed before implementation; callback verdicts require demonstrated successful dispatch to exactly one enabled native control in one input epoch, or demonstrated same-process caller replacement for caller_update, before comparing the exact callback interval.

[R25] At every route checkpoint the visible content must be complete and mutually non-overlapping, including validation and success text when present; the canvas and primary color, content presence, wrapping and overlap are independent review atoms.

[R26] For the route, an invalid Start emits no events, a valid Start emits only the selected start event, Choose again emits no events, Cancel emits only its cancel event, and dirty-state caller replacement emits no events and displays only the new copy with reset local choices.

[R27] Only valid Start listening and Cancel activations invoke the supplied callbacks; selection changes, acknowledgement changes, validation failures, Choose again, recomposition and caller replacements invoke neither callback, and each actual action uses the callbacks supplied by the current caller.

| Checkpoint | Stimulus and expected product state |
|---|---|
| ready | Initial empty editing state. |
| validation | Activate Start listening with neither requirement satisfied; show both-condition error. |
| started | Choose the first available option, turn acknowledgement on, then Start listening; one start callback. |
| renewed | Activate Choose again; empty editing state and no callback. |
| canceled | Choose the second available option, acknowledge, then Cancel; one cancel callback and empty editing state. |
| replaced | Make editing dirty with the first option and acknowledgement, then replace the entire input without remounting; new copy, empty local state, no callback. |

Public API signatures and exact fixed strings: [api-contract.json](api-contract.json). Independent typed design values: [reference.json](reference.json).
