# 新增 UI 开发实跑：Reply + AlertToast

本次新增业务 UI，没有向生产组件注入已知错误。先独立绘制设计、固定验收，再由当前 coding agent 实现、运行原生宿主、看图、修正，并保留完整过程。日期：2026-10-18。

## 结果

| 工程 | 新需求 | 场景 | 结果 |
| --- | --- | --- | --- |
| Reply | 已有邮件附件在卡片内显示摘要 | normal / long / dark / narrow / empty | **5/5**；首版达标，0 轮生产修正 |
| AlertToast | 可选上传进度 HUD，兼容旧调用 | normal / long / dark / narrow / complete / legacy | **6/6**；对照设计发现轨道颜色偏差，1 轮生产样式修正 |

两端各有一次额外的干净检出复跑。Reply 的真实 Activity 还验证了附件摘要可见、打开对应邮件、返回列表。AlertToast 是组件库，验证到实际模拟器 XCTest 宿主，没有完整业务 App 导航验证。

![参考、首版、最终结果](comparison.png)

图片拼接仅供展示；原生实际图保持原尺寸。独立 SVG 是结构与样式参考，不是可与平台字体逐像素比较的 native golden。新增设计没有使用最终实现截图来证明自身正确。

## 实现前固定了什么

设计与验收在提交 [`26f101c`](https://github.com/KamisamaJin/native-ui-agent/commit/26f101c36c1b98f40a230b9e9c92f3cd952fbb2a) 中先于功能实现保存。`design/freeze.json` 记录四个原始文件的 SHA-256，后续验证没有更改它们：

- [Reply 独立参考](design/android-reference.svg) / [验收 JSON](design/android-acceptance.json)
- [AlertToast 独立参考](design/ios-reference.svg) / [验收 JSON](design/ios-acceptance.json)

Reply 复用 `Email.attachments`，不创建新业务数据模型。有附件才显示图标、数量和首个描述；描述单行省略，整卡点击继续打开邮件。固定 12dp 摘要外间隔、12dp 内留白、24dp 图标、8dp 图文间隔、4dp 两行文字间隔，文字使用工程主题，数量 14sp、描述 12sp。

AlertToast 增加默认 nil 的 `progress` 参数，展示标题、副标题、百分比与 4pt 高进度条。有限值归一到 0…1，非有限值按 0；没有 progress 时保持原 HUD。固定宿主外距 20pt、卡片内距 16pt、图标 24pt、行间 12pt、圆角 20pt、卡片最大宽 360pt。浅蓝轨道来自实现前 SVG 中的 `#ddeaff`。

设计与需求由本次 agent 选择，没有独立设计师审批，也不是未知需求盲测。它比“已知错误恢复原样”更接近开发，但不是因果质量对照实验。

## 生产代码交付

| 平台 | 完整功能补丁 | 首版与修正 |
| --- | --- | --- |
| Android | [android-feature.patch](patches/android-feature.patch) | [首版](patches/android-initial-feature.patch)，与最终一致；没有人为制造一轮失败 |
| iOS | [ios-feature.patch](patches/ios-feature.patch) | [首版](patches/ios-initial-feature.patch) / [看图后的修正](patches/ios-visual-correction.patch) |

Android 新增生产 `ReplyAttachmentSummary.kt`、本地化数量 plurals，并在既有 `ReplyEmailListItem` 的正文下条件调用。没有新增测试 ID，没有改写旧主题，没有换一套 UI 框架。

iOS 新增生产 `progressHUD`、可选公开参数与归一化逻辑。首版复用系统 `LinearProgressViewStyle`；后续修正为生产 `UploadProgressStyle`，固定设计轨道色，继续由 SwiftUI 的 ProgressView 提供进度语义。上传模式显示上传图标；其他 HUD 保留旧分支。此功能补丁不是回滚到上游源码。

集成原库 `.toast(...)` 修饰器时，持续显示时间仍由原 API 的 duration/tapToDismiss 等参数控制。本次没有验证上传业务状态流转、定时消失、动画或网络上传，也没有把静态 HUD 截图算作这些行为通过。

## 实际发现及自动修正

最初普通状态的快速视觉检查判断布局与进度可读并通过，见 [原始报告](evidence/ios-initial-normal-review/report.json)。逐项核对冻结 SVG 后，发现首版未填充轨道是系统灰色，与浅蓝设计不符：

- [初版实际图](evidence/ios-initial-normal-1/artifacts/000-actual.png)，可见轨道采样 RGB **228,228,229**。
- [追加的失败判定](evidence/ios-initial-normal-design-review/report.json)，绑定原始 capture；没有删除最初较宽松的通过记录。
- [生产样式修正](patches/ios-visual-correction.patch)，没有修改参考或验收。
- [最终实际图](evidence/ios-final-normal-1/artifacts/000-actual.png)，对应轨道 RGB **221,234,255**，与冻结 SVG 相同。

浅色 long/narrow 同样能看到该偏差。深色参考没有定义精确 RGB，100% 场景没有暴露未填充轨道，因此没有把这两个场景按该色差判失败。最终仍对全部六个状态重新原生渲染与检查。

这也暴露了限制：模型的快速看图可能漏掉小的颜色细节。归档审计后来增加了对冻结 SVG 色值和实际轨道像素的确定性核对；这是把已存在的设计事实自动化，没有放宽原先标准。不能据本次过程声称 AI 视觉判断没有漏检。

## 数值与证据

Android 的 [宿主](adapters/ReplyFeatureUiTest.kt) 读取真实 `ViewRootForTest.semanticsOwner` 的 unmerged 节点；按实际文字定位 `4 attachments`、描述和正文，不增加业务 ID。通过 `GetTextLayoutResult` 与 `boundsInRoot` 实际获得：

| 实测内容 | 结果 |
| --- | --- |
| 数量 / 描述字号 | 14sp / 12sp |
| 数量颜色 | 浅色 `FF4F4539`，深色 `FFD3C4B4`，来自当前普通 Text 的 layoutInput.style |
| 两行文字框的垂直间隔 | 4dp |
| 数量与正文的左边界偏移 | 44dp = 摘要内边距 12 + 图标 24 + 图文间隔 8 |
| 正文框底部到数量框顶部 | 24dp = 摘要外间隔 12 + 摘要内边距 12 |
| 长描述、省略状态 | long/narrow 原生 isLineEllipsized=true；数量为 false |
| 空附件 | 实际语义树中无摘要数量节点，图片也无占位 |

这是特定 Compose 1.9.4 普通 Text 的采样，不覆盖富文本 run、brush、所有绘制覆盖或通用样式树；框间隔也不等于字形墨迹间隔。

iOS 的 [宿主](adapters/AlertToastFeatureUiTests.swift) 在原生测试内验证负值、超过 1、NaN、infinity 与缺省参数。渲染图片的蓝色条几何与独立设计比较：普通实际填充 **0.4198**，窄屏 **0.4194**，期望 0.42±0.025；左距 **36pt**、可见条高 **4pt**。颜色采样与条长属于渲染像素观测，不是 UIKit/SwiftUI 属性反射。旧调用与上游冻结 native 图的像素差异为 **0**。

每个已验收状态，原生 JUnit 或 xcresult 均确认 **1 个测试、0 失败**。每次 capture 保存了实际命令、日志、输入与保护目录指纹、原生产物和复制图 SHA；视觉 findings 绑定本轮 capture。没有用旧图冒充重新运行。

各场景与逐项结论见 [result-summary.json](result-summary.json)，包含指向每份实际图、capture 与 review 的相对路径。Android 首版就是最终版本，因此索引保留 `android-initial-*` 名称，没有复制一组伪造的 final capture。

## 页面与干净检出复跑

[Android 页面报告](evidence/android-page-final/report.json) / [实际页面](evidence/android-page-final/inbox.png) / [详情](evidence/android-page-final/detail.png) / [脚本](adapters/verify_android_page.py)。在 API 36.1 模拟器中读取当前 UIAutomator 树，先确认数量及描述，再按邮件标题本轮 bounds 点击、查看详情、按 Back 返回。没有新增业务 ID；不会由组件通过推断整个应用业务正确。

[prepare 收据](evidence/clean-replay-prepare-receipt.json) 记录固定提交与实际应用的 host/feature 补丁哈希。干净检出从本机上游 Git 对象创建，不复制其 working tree 或原构建目录；两端分别重新构建并运行正常状态：[Android](evidence/android-clean-replay-normal-review/report.json) / [iOS](evidence/ios-clean-replay-normal-review/report.json)。新渲染图与最终状态像素相同。使用远端下载的路径提供在脚本中；本次没有另做网络下载分支的完整构建验证。

## 复跑

上游固定版本：Reply `53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79`，AlertToast `76a1c1793cd3443001c20c6033beb84453b25d9f`。原工程构建版本不升级：AGP 8.13.0、Kotlin 2.2.21、Compose 1.9.4、SDK 36；新增 Paparazzi 2.0.0-alpha02。iOS 使用 SnapshotTesting 1.19.2、Xcode 27.1、iOS 26.5 (23F77)。字体缩放为 1；未覆盖无障碍大字和其他语言。

先安装 Python 依赖、完成 Xcode 首次设置、安装所需 SDK/运行时。用 `xcrun simctl list devices available` 取得实际 UUID，启动并等待模拟器完成引导。下列路径是示例，须替换成当前机器真实值：

```sh
python3 -m pip install -r native-ui-agent/scripts/requirements.txt
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
xcrun simctl boot YOUR_SIMULATOR_UUID
xcrun simctl bootstatus YOUR_SIMULATOR_UUID -b

python3 validation/feature-development/prepare.py \
  --workspace /absolute/path/to/new-workspace \
  --android-sdk /absolute/path/to/Android/sdk \
  --java-home /absolute/path/to/jdk-21/Contents/Home \
  --ios-device YOUR_SIMULATOR_UUID

python3 native-ui-agent/scripts/ui_loop.py capture \
  --project /absolute/path/to/new-workspace/checkouts/compose-samples/Reply \
  --profile /absolute/path/to/new-workspace/profiles/android-normal.json \
  --output /absolute/path/to/new-evidence/android-normal-1

python3 native-ui-agent/scripts/ui_loop.py capture \
  --project /absolute/path/to/new-workspace/checkouts/alerttoast \
  --profile /absolute/path/to/new-workspace/profiles/ios-normal.json \
  --output /absolute/path/to/new-evidence/ios-normal-1
```

`prepare.py` 仅接受新目录；其他状态选择对应 profile。使用已有 Git 对象加速时，另传 `--local-reply-repository`、`--local-alerttoast-repository`，这条路径已实跑验证。测试宿主直接调用生产组件，依赖原主题和资源；渲染及参数传递的细节封装在 [Android 导出适配器](adapters/capture_android.py) 与 [iOS 导出适配器](adapters/capture_ios.py)。

之后让 agent 读取新 actual，按 Skill 协议生成新 findings，执行 `review`。不能复制归档 findings 并换哈希冒充本轮看图；没有模型调用能力时，只能执行原生与确定性检查，视觉项保留待审。

```sh
python3 validation/feature-development/verify_evidence.py
```

这条已实际执行的跨机器审计检查归档，不重新跑原生 SDK/模型。归档保留本机绝对路径以追溯当时环境；审计依靠文件内绑定及相对产物路径，复跑则由 configure 生成本机路径。SDK、克隆源码、缓存、签名文件与 xcresult 大包不进 Git；关键图片、原生日志摘要、JUnit XML 和配置进入 Git。

## 可以得出和不能得出的结论

可以证明：两个既有工程能增加业务 UI，薄宿主调用生产代码；独立设计可以约束实现，原生测量能覆盖部分精确样式，看图发现的问题可转化为源码修改并重新验证；接入可以用完整补丁在干净检出中复跑。

尚不能证明：对任意旧项目零配置、自动理解所有模糊 testcase、完整获取两端样式树、覆盖全部设备/大字/语言/页面状态，或量化总体 PR 质量增益。没有独立 reviewer 和无 Skill 对照组；iOS 自动修正是设计轨道颜色，未演示复杂业务缺陷修复。后续应使用独立需求、未知历史 PR 和预先固定失败集来比较漏检、误报、修复率和耗时。
