# Independent generic forward-test result

Passed within the declared scope. No Skill or implementation correction was needed. No native build/test failed. Expectations and sources stayed unchanged after their pre-native freezes.

| Native run | Tests | P / F / U | Actual images | Wall seconds |
|---|---:|---:|---:|---:|
| ios probe | 1 | 6 / 0 / 0 | 23 | 92.57 |
| ios component | 1 | 16 / 0 / 0 | 40 | 144.64 |
| android probe | 1 | 6 / 0 / 0 | 19 | 18.05 |
| android component | 1 | 16 / 0 / 0 | 42 | 8.48 |

The component denominator is 16 cells/platform: 2 states × 8 requirements (title, top status, middle action label/enabled/selected, distant footer, demonstrated callback interval, and scoped target visual review). Fourteen cells/platform are typed native checks; two are manual visual judgments bound to actual screenshot hashes. The initial previsual reports retain 14P/0F/2U. Probe denominator is six/platform. Duplicate evaluator replays do not add coverage credit.

Selection emitted exactly `toggle-mark`; replacement advanced input 0→1 with an empty callback delta. Component process/session identity stayed unchanged, and event revision remained 1 through replacement and all target frames. The four target selectors were title, status, middle action, and footer. iOS used 8 then 7 shared target scrolls; Android used 7 then 4; all were within the fixed 24-scroll budget. Actual target and independent full-sweep top/action/footer images were inspected in both states. Text wraps, panels and hierarchy match the frozen textual design reference. Native disabled iOS styling visibly dims the replacement action; no contrast threshold was specified or measured.

Original inputs retained the documented `state_capture:true` default. Each native component capture therefore includes complete initial, marked, before-update, replaced and final sweeps; geometric overlap was complete. Original `native_checks` selects these available state captures. To isolate the new target-bundle path, `observation.targets-only.json` removes only `state_captures` from the exact original JSON. Its source hash and transformation are retained. These are evaluator replays, not additional native captures. Both replay component reports pass 16/16 and retain `complete:false` for every selected state.

A single Android evaluator replay removed the marked-footer target frame while leaving producer `all_targets_observed:true`. The expected result was declared before replay: 13P/0F/3U, including unassessed marked footer and two absent manual reviews. Actual results matched. This establishes no missing-footer credit from the producer flag in this example; it is not a product failure.

Limits: reviewed target frames do not establish a whole-content visual pass. No SwiftUI numeric style, pixel-golden, contrast-compliance, full hit-region, app navigation/keyboard/lifecycle, physical Android touch, RTL/dark/large-font, or business-component claim is made. The iOS run was iPhone 17 Pro/iOS 26.5 with light/LTR/large ordinary Dynamic Type at requested width390; Android used light/LTR/fontScale1.0/width390 in one attached ComposeView. The independent design reference is preimplementation prose, not an approved pixel golden.

Evidence locations: `acceptance.md`, `expectations-frozen.json`, `implementation-frozen.json`, `matrix.json`, `component-plan/`, `*-invocation.json` (exact commands/times/entire copied-Skill hashes), and each run folder (native source/inputs/logs/reports/images/original observation). `checks.reviewed.json` grades original evidence; `checks.targets-only.reviewed.json` grades labelled replays. `manual.*.json` binds visual decisions to screenshot SHA256. `summary.json` is the compact machine summary.

Exactly two native runs/platform were used. The dedicated simulator was shut down and verified in `cleanup.json`. No main Skill, other validation artifacts, external apps, or Git commits were modified.
