# Independent neutral forward pass

Fixed before implementation: an expandable reading/status panel, neutral title, a 48 native-unit disclosure growing to 72 when expanded, selectable reading preference, disabled export action, twelve long text sections, and caller replacement resetting expansion and selection.

Public normal: 360 logical width, light, default text. Public dark-large: 390 logical width, dark, iOS xLarge / Android 1.2. Both use the same action sequence: expand, select, observe disabled action, caller replacement.

Acceptance uses exact labels/selected/enabled flags, native accessibility-bound disclosure height with independently allowed 0.75-unit quantization tolerance, Android title 22sp and theme ink; iOS computed style and framework layout allocation remain unassessed. Manual review inspects legibility, ordering, clipped text, and the changed disclosure. Callbacks require native delivery; observing a blocked disabled control cannot pass a callback assertion.

No pixel regression reference is asserted; the typed design and this authored layout description are the new design reference. Source/capture identity does not prove design interpretation correct. No actual application navigation/keyboard/lifecycle/OS physical Android touch claim.
