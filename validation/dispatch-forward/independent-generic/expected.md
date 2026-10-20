# Frozen independent expectations, written before native execution

Neutral authored FoldBoard component; no business implementation or existing probe read. Two distinct text fixtures A and B. Platform-specific implementations share this contract. White card, dark readable text, a title, a disabled action, expandable region, and long independent paragraphs followed by a finish action. No pixel baseline; visual review concerns readability, ordering and clipping only. No universal font/padding/hit claim.

1. Initial: title Alpha field and six long paragraphs, real disabled control `fold.locked`, enabled `fold.open`, final `fold.finish`. Top-to-bottom evidence must belong to input A.
2. Action 0: disabled activation observed with allow_disabled. Native enabled=false and blocked_disabled; empty callback interval is retained, callback behavior verdict must be U (not a business pass).
3. Action 1: native open route succeeds uniquely and emits exactly `open:A`. The component inserts a 420-point/dp region before the same button, moving its native position. Keep immediate and post-reveal frames; evaluate post-target binding separately. State `opened` must have complete long-content evidence for A.
4. Action 2: caller replaces A with B in same mounted host/process; title Beta field and eight paragraphs appear, expanded state remains. Caller update callback delta empty, with input index advancing by one. Replacement coverage cannot borrow prior snapshots.
5. Action 3: native finish route succeeds uniquely and emits exactly `finish:B`; final long-content state B has independent full coverage. No activation assertion may pass from blocked/unavailable delivery or wrong input/process/method.

Required methods: iOS xcui_tap; Android compose_onclick. Caller update uses caller_fixture_update. All unavailable evidence stays U. Native test count must be exactly one per run; at most two runs per platform, and original failures retained. Android is continuous attached Paparazzi/Compose native semantics, not Activity/OS physical touch. iOS is App/XCUITest.
