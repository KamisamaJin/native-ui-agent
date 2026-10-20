# Garden Water Round release panel

This is a new controlled native component for a shared garden steward to release one watering round. The steward chooses drip lines or soak hoses, sees the water calculation, and explicitly acknowledges any protected reserve use before release. Implement the real production component in the existing AlertToast Swift public library and Reply Android application package com.example.reply.ui.waterround. The public library must remain source-compatible with iOS 14 and macOS 11.

The component owns its state projection and calculations, but the caller owns the model. Every interaction is a request through a typed callback. No tap mutates the supplied model, checks a consent box locally, changes selection locally, or creates a local submitting state. An explicit new model from the caller recomputes the entire view immediately, including round identity, text, selection, eligibility and amounts. There is no remembered consent or calculation keyed to an old identity.

## Business rules

Let selectedRate be dripLitresPerBed for drip or soakLitresPerBed for soak. Let prime be dripPrimeLitres for drip and zero for soak.

- requiredLitres = bedCount * selectedRate + prime.
- spendableLitres = tankLitres - reserveLitres.
- reserveNeededLitres = max(0, requiredLitres - spendableLitres).
- remainingLitres = max(0, tankLitres - requiredLitres).
- shortfallLitres = max(0, requiredLitres - tankLitres).
- The reserve consent appears exactly when reserveNeededLitres > 0 and shortfallLitres == 0. It displays the supplied reserveAcknowledged value.
- Release is enabled exactly when isEnabled && !isSubmitting && shortfallLitres == 0 && (reserveNeededLitres == 0 || reserveAcknowledged).
- Drip is enabled exactly when isEnabled && !isSubmitting. Soak additionally requires soakAllowed. The selected choice stays enabled when the common enabled condition is true; tapping the already selected method is a no-op.
- Visible consent is enabled exactly when isEnabled && !isSubmitting.
- An enabled different method emits methodRequested. An enabled visible consent emits reserveAcknowledgementRequested with the opposite of the supplied Boolean. A valid release emits releaseRequested with the derived fields specified in api.md.
- Disabled actions and already selected method actions emit no event. A missing consent control has no action route. An attempted unavailable native activation cannot be used as evidence for a zero-event claim.

Status precedence and exact text:

1. !isEnabled: "Round paused".
2. isSubmitting: "Preparing release…".
3. shortfallLitres > 0: "Not enough water".
4. reserveNeededLitres > 0 && !reserveAcknowledged: "Approve reserve use".
5. Otherwise: "Ready to release".

A progress indicator appears exactly when isEnabled && isSubmitting. The action label is always "Release N L", where N is requiredLitres. No device locale, grouping separator, or rounding changes any numeric display: use ASCII base-ten integers and "L". The fixed English interface strings stay English in RTL; caller-supplied Unicode title, description, and notice are displayed verbatim.

## Content and ordering

The card fills the width offered by its parent. Its order is: title; description; input facts (Beds, Tank, Protected reserve, Drip prime); two vertical method choices (drip then soak); calculated summary (Required, Outside reserve, Reserve needed, Remaining, and Shortfall only when positive); conditional reserve consent; conditional notice; status; release action. Progress is inside the action alongside its label. Description is always shown. Notice is absent exactly when it is empty.

Exact fact and summary strings are "Beds: N", "Tank: N L", "Protected reserve: N L", "Drip prime: N L", "Required: N L", "Outside reserve: N L", "Reserve needed: N L", "Remaining: N L", and "Shortfall: N L". Each method shows its name on the first line and "N L per bed" on the second. Names are "Drip lines" and "Soak hoses". The consent label is "Use N L from the protected reserve".

## Native layout and visual requirements

The reference SVG is annotated design intention, not a native pixel golden. Native platform text rasterization may differ; the named dimensions, colors, hierarchy, and content behavior remain requirements.

The shared generic host has a 600 point/dp viewport height and adds 16 horizontal padding on each side. A 320-wide viewport offers 288 to the component; a 390-wide viewport offers 358. The component draws its own card surface. The parent canvas uses the platform host default color and is not responsible for painting the card or its contents. The card has no additional outside horizontal margin and no fixed height.

The card has radius 20, border width 1, and 16 internal padding on all four sides. Major sections have 12 vertical spacing. Method choices have 8 spacing between them, 12 internal padding on all four sides, radius 12 and border width 1. Each method control has minimum visible height 56. Consent has minimum visible height 44. The release control fills the inner width, has minimum visible height 48, 12 corner radius, and 12 internal padding on each side. All interactive controls require a physical hit region at least 44 by 44 points/dp.

Use system native sans-serif fonts, with native accessibility text scaling. At default scale: title 20 semibold; description, input facts, notice, and consent 14 regular; summary labels 13 regular; summary numeric values 17 semibold monospaced digits; method names and release label 16 semibold; method rates 14 regular; status 14 semibold. A summary may be one native text element with mixed typography, but all its text and its identifier must remain observable. No text line limit, ellipsis, clipping, horizontal scrolling, fixed-height card, or fixed-height text row. At narrow widths and larger text, all text wraps, rows grow, and the host vertical scroll can reach the entire card. Summary label/value rows have at least 8 spacing; use a vertical label/value arrangement when two columns would collide. Native layout direction mirrors leading/trailing alignment and control arrangement, while section order and numeric meaning remain unchanged.

Palette (RGB hex, fully opaque):

| Token | Light | Dark |
| --- | --- | --- |
| surface | #FFFFFF | #15251C |
| border | #D7E3D8 | #3B5242 |
| foreground | #183A25 | #E7F3E9 |
| muted | #526B59 | #B2C8B8 |
| accent | #216B3B | #81D89B |
| accentOn | #FFFFFF | #102C19 |
| selectedSurface | #E5F2E8 | #244F33 |
| warning | #865400 | #FFD28A |
| warningSurface | #FFF1D5 | #493715 |
| disabledSurface | #E5EBE6 | #293C2F |
| disabledText | #65756A | #92A396 |

Unselected choices use surface/border, selected choices selectedSurface/accent, and both use foreground text. Enabled release uses accent/accentOn; disabled release uses disabledSurface/disabledText without applying a second overall opacity. Status has warningSurface/warning whenever its text is not "Ready to release", and selectedSurface/foreground otherwise. Description and method rate use muted; all other body text uses foreground. Convey selection, enabled/disabled, checked state, progress, and status in native semantics as well as visually.

Runtime typography, exact internal padding, and physical hit-region evidence are required capabilities. If the observer cannot expose those native facts, retain these assertions as U (unavailable). Source declarations, screenshot guesses, semantic bounds, and a successful tap do not establish those facts.

## Integration boundary

The thin bridges decode every required JSON member, construct the public model, call the actual production entry point and serialize real typed callbacks. They contain no UI, watering business logic, amount calculations, eligibility calculation, callback synthesis, mutation of the model, or default branch. Host scrolling and visual evidence collection are external to the component and must not be counted as component callbacks.

Native activation routes are iOS XCUI tap and Android Compose semantic OnClick. This specification makes no claim about iOS AX performAction or Android OS physical touch. A successful explicit caller replacement can establish replacement quietness; an unavailable activation cannot establish no callbacks, handler failure, or a post-action state. Callback capture windows must preserve their original action interval if a subsequent full-content sweep scrolls to collect images.
