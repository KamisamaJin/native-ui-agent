# Neutral capability comparison before the new design

Same original components, inputs, actions and typed plan. No deliberate product
faults or business-specific expected values. Both native tests executed once per
run. Callback verdict function is unchanged from frozen v4.

| Platform | v4 P/F/U | v5 P/F/U | v4 warm command | v5 warm command |
|---|---:|---:|---:|---:|
| iOS | 7 / 0 / 9 | 15 / 0 / 1 | 34.226 s | 61.526 s |
| Android | 6 / 0 / 10 | 15 / 0 / 1 | 4.594 s | 5.441 s |

On this input, target evidence gains 8 iOS and 9 Android assessed cells, with no
P/F disagreements. The disabled callback remains U. Multi-target navigation costs
79.8% more iOS and 18.4% more Android warm command time; this is a coverage/cost
tradeoff, not a speedup. Single observations are not statistically stable timing
estimates. Cold runs include different boot/compiler-cache histories and are
retained without a causal speed claim (iOS v5 boot alone took20.686 s).

v4/v5 retained22/27 iOS and17/22 Android raw frames. No full sweep, content, state
or failed command was omitted. The same plan gives legacy single-frame data every
fact it actually supports. Target-set states stay incomplete for full-content
coverage even when every selected target was observed.

Original PNGs, sources, inputs, native logs and SHA inventories are in
`../generic-evidence`. `../generic-summary.json` is replayed by
`python3 -B validation/state-forward/verify_generic.py`. Four-state negative-plan
replays produce4 exact typed-native findings on each platform; process, input,
event and image mismatch controls withhold target-set verdicts. These synthetic
controls are separate from the genuine native captures and business defect rates.
