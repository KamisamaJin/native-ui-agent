# Third-party material

The root MIT license covers original Skill, runner, documentation and harness code. It does not replace upstream licenses.

The blind-comparison transfer queue, fresh-blind visit-rescheduling components, tool-forward return-resolution components and dispatch-forward WaterRound components, independent designs/oracles, generic observer probes and adapters are original additions covered by the root MIT license. Their Reply/AlertToast test hosts still use the upstream projects and native dependencies below. Screenshots and archived native reports document those integrations; they do not relicense upstream assets or dependencies.

| Material | Source | License / notice |
| --- | --- | --- |
| Reply component patches and screenshots containing its UI/assets | [android/compose-samples](https://github.com/android/compose-samples), revision `53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79` | Copyright The Android Open Source Project; Apache-2.0. See [full license](validation/native-ui-pilot/licenses/android-LICENSE). Preserve source headers when applying or distributing patches. |
| AlertToast component patches and UI screenshots | [elai950/AlertToast](https://github.com/elai950/AlertToast), revision `76a1c1793cd3443001c20c6033beb84453b25d9f` | Copyright (c) 2021 Elai Zuberman; MIT. See [full license](validation/native-ui-pilot/licenses/ios-LICENSE); original source notice is retained. |

Generated Paparazzi report support files under `evidence/**/paparazzi-report/` originate from [cashapp/paparazzi](https://github.com/cashapp/paparazzi) and retain its Apache-2.0 terms; the full Apache-2.0 text is included with the Android license above. They are archived evidence, not original MIT-licensed runner code.

Native dependencies are fetched by the example projects: [Paparazzi](https://github.com/cashapp/paparazzi) (Apache-2.0), [SnapshotTesting](https://github.com/pointfreeco/swift-snapshot-testing) (MIT), AndroidX/Compose and other upstream dependencies under their respective terms. The Python runner depends on Pillow; see its [license](https://github.com/python-pillow/Pillow/blob/main/LICENSE).

Simulator runtimes, SDKs, Xcode, Gradle caches, signing material and upstream checkouts are excluded from this repository. Screenshots document local test runs; they do not imply endorsement by upstream maintainers. This repository is an independent experiment, not an official Android, Apple or Point-Free product.
