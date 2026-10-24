# Native UI Agent

让 coding agent 在已有 iOS / Android 工程中实现 UI，通过真实原生渲染、看图、可测量断言和源码修正交付结果。

这个仓库包含可加载的 **Skill**、确定性的 **证据 runner**，以及两个真实开源工程的接入代码和实跑记录。模型由宿主 coding agent 提供；runner 不内置 LLM，也不假装提供通用完整的原生样式树。

## 本轮 v9：采集提速确认，整体质量与成功交付成本优势未证实

实现需求覆盖与发现路由、统一执行计划、源码绑定的定向复验，并减少 iOS 同状态重复扫描。工具先用无关组件验证并冻结，再独立设计两项全新复杂 UI；每项只有一份自然产生的初始双端 PR，原字节复制给 v8/v9 两组。全部自验、隐藏场景、双轮质量/源码评审及原始告警评审封存后正式揭盲；未注入缺陷。

**同代码、同覆盖的 iOS 采集：**4 组配对均无已知支持项丢失或判定冲突，1211.675 → 468.853 秒，下降 **61.31%**；反向顺序暖运行仍下降约 60%。这是共享后端收益，两组修复都使用该后端与最终 MUST 门控。

| 同首版 PR 的双任务结果 | v8 | v9 |
| --- | ---: | ---: |
| 确认产品缺陷 / 真实漏检率 / 产品修复率 | 0；N/A；N/A | 0；N/A；N/A |
| 原始 TP / FP / 未裁定告警 | 0 / 0 / 10 | 0 / 0 / 10 |
| 最终公开 P / F / U | 2940 / 0 / 24 | 2930 / 0 / 34 |
| 最终公开未评估 | 0.81% | 1.15% |
| 新增确认产品回归 | 0 | 0 |
| 完整自身验收 accepted | 0/2 | 0/2 |
| 内循环原生请求 | 2 | 1 |
| 初始编写＋初始采集＋完整自验，均值 | 33.60 分 | 31.88 分 |

十条原始严格标签 F 后来两组均变 P，但其真实产品责任未获确认，不能算成十个 bug 修复；零分母不是零漏检，未裁定告警也不能写成零实际误报。新版少一次复验，却保留了旧版已恢复的 iOS 观测，含隐藏场景共多 **15 U**。四份最终结果都因必需未知项而未通过完整验收，较短的自验结果耗时不代表成功 PR 更便宜。

新版实际调用了需求路由，但这次未记录复验规划器的实际调用，不能把少一次请求直接归因于它。瓶颈仍是把必需 U 转成执行中的定位诊断与闭合任务，以及保证测量判据代表真实平台语义。保留 **44 次业务采集、11 次不完整回执**、共享路径恢复、排队和全部评审分歧；设计/协议准备 118.15 分钟、自预注册至揭盲研究墙钟 351.46 分钟另列。CI 只验证原始档案与复算，不表示组件验收通过。

[完整结果与瓶颈](validation/feedback-forward/RESULTS.md)、[指标及完整成本](validation/feedback-forward/TABLES.md)、[工程实现](validation/feedback-forward/ENGINEERING.md)、[决策协议](native-ui-agent/references/decision-feedback.md)、[原始界面](validation/feedback-forward/GALLERY.md)、[失败与未知](validation/feedback-forward/failure-index.json)、[复算](validation/feedback-forward/REPRODUCE.md)。本轮为 SwiftUI / Compose 组件级验证，不覆盖完整旧 App 与后端；双 AI 一致不是人类金标准。

## 上一轮 v8：自动样式证据增加，未证明缺陷簇、修复或成本优势

把人工式发现与独立契约的绑定、预期/单位生成、原子配色测量做成可执行工具；修复共享评估器的环境适配、数值事实与责任归属处理。工具先用无关原生组件和负例验证并冻结，再独立设计 Workshop Slot Planner、River Sensor Triage Board、Bicycle Service Intake 三个新增复杂 UI。六份双端实现、108 条计划原生采集；未注入产品缺陷，完整评分与告警双评封存后正式揭盲。两组都已使用 Skill。

| 原始主结果，三任务汇总 | v7 | v8 |
| --- | ---: | ---: |
| 检出产品原子表现† | 17/20 | 16/16 |
| 检出 / 修复确认缺陷簇 | 3/3；3/3 | 4/4；4/4 |
| 原始真实 / 确认误报 / 未裁定告警 | 17 / 0 / 1 | 16 / 0 / 10 |
| 确认产品行修复 | 20/20 | 16/16 |
| 最终公开 P / F / U / N/A | 922 / 0 / 50 / 204 | 922 / 0 / 50 / 204 |
| 实现→自身最终原始证据及自动检查端点，均值 | 175.13 分钟 | 175.18 分钟 |

†旧组漏记的三行是已发现裁切共因的另外三个重叠表现，不能解释成新版额外找到三个独立 bug。两组初始缺陷分母不同；旧组仅一个任务有计分缺陷，新组有三个。最终公开未评估均为 **5.14%**；含保留场景为 **5.14% / 5.01%**。这不支持整体质量或提速的因果结论。

**同源码、同原始证据的自动检查：**24 组配置中 U **732→234**，新增 **498** 行可判定证据（484 P、14 F），无已知结果丢失或冲突；额外 SDK 采集为 **0**。这是自动渲染配色证据的明确收益，不能替代真实开发效果。消除重复配对采集属于共享实验基础设施。

不能把零确认误报写成零实际误报。未知告警的保守误报范围是 **0–5.56% / 0–38.46%**：其中旧组1条、新组7条是原始证据支持、但刻意未纳入计分契约的同类网格发现；另3条新组换行发现仍有判定冲突。经典 FPR 不可得。新绑定能阻止预期/单位漂移，但没有补齐契约外需求，也没有保证 AI 看图判断正确。

保留9次原生非零退出、全部失败与未知。发现共享公共采集路线缺少自身路线的动作后补充观测，未在本轮改路线或补采；同图换行判断的跨阶段不稳定也单列。115项工具测试、9项指标控制和完整证据复算纳入 CI；**CI 通过不代表组件验收全部通过**。

[完整报告](validation/atomic-forward/RESULTS.md)、[指标与完整成本](validation/atomic-forward/TABLES.md)、[通用工具实现](validation/atomic-forward/ENGINEERING.md)、[绑定协议](native-ui-agent/references/atomic-review.md)、[评审分歧](validation/atomic-forward/DISAGREEMENTS.md)、[失败记录](validation/atomic-forward/FAILURES.md)、[原图](validation/atomic-forward/GALLERY.md)、[复算](validation/atomic-forward/REPRODUCE.md)。iOS 为 Simulator/XCUITest，Android 为 Paparazzi/Compose JVM 语义动作；本轮不证明任意无埋点旧 App、完整业务或 SwiftUI 计算样式能力。

首次远端 CI 暴露了发布遗漏：封存链引用的274个原始 `.xcresult` 文件未上传，以及一处文件名大小写差异。本地文件系统掩盖了问题。[发布补充记录](validation/publications/atomic-v8-completion/README.md)保留失败 CI 和原始发布清单，补齐原字节并增加通用 Git 引用闭包校验；不改冻结工具、源码、契约、评分和指标。当前发布完整性请使用补充记录中的验证入口。

## 上一轮 v7：三任务盲测完成，仍未证明质量优势

先修复原生几何精度链并加入可执行全员封存屏障，再独立固定三个全新复杂 UI：装备组合、广播混音、馆藏状况审核。六份不同双端实现、132 次计划原生采集；未注入产品缺陷，全部阶段评分封存后才揭盲。两组均已有 v6 契约与观测能力。

| 原始主结果，三任务汇总 | v6 | v7 |
| --- | ---: | ---: |
| 严格原始描述符检出产品行 | 45/45 | 32/45 |
| 已确认产品簇检出 / 修复 | 5/5；5/5 | 4/5；5/5 |
| 最终 P / F / U / N/A | 857 / 0 / 1297 / 222 | 857 / 0 / 1297 / 222 |
| 实现→自身最终证据封存，均值 | 78.01 分钟 | 77.87 分钟 |

**未证明 v7 提升检出、修复、覆盖或成本。** 严格描述符拒绝含预期/单位格式不一致，不能全算真实误报；独立评审的两条误报标签也与原像素证据冲突，真实产品误报率不可确定。

原始 oracle 把 Compose `Ltr` 与 `ltr` 直接比较，导致 Android 适用项全部 U；原分数保留。揭盲前另封存共享适配及匿名事后复核，两组最终均为 **1894 P / 36 F / 224 U / 222 N/A**，未评估 **10.40%**。此改善属于共享基础设施，不能算 v7 收益；新增画布 F 的宿主/产品责任标签存在分歧，全部保留。

同源码 3024 项配对无判定变化，296 项同帧几何断言全部 P→P。新计量方法未放宽容差，也未填补 iOS 计算样式缺口。98 项工具检查和独立中性原生验证先于新任务冻结。

[完整报告](validation/multitask-forward/RESULTS.md)、[指标与成本](validation/multitask-forward/TABLES.md)、[共享修正](validation/multitask-forward/SHARED-INFRASTRUCTURE.md)、[评审分歧](validation/multitask-forward/GRADER-DISAGREEMENTS.md)、[工程实现](validation/multitask-forward/ENGINEERING.md)、[失败记录](validation/multitask-forward/FAILURES.md)、[原图](validation/multitask-forward/GALLERY.md)、[复算](validation/multitask-forward/REPRODUCE.md)。

## 上一轮 v6：独立契约可执行，质量与覆盖优势仍未证实

新增独立设计契约、具体来源/单位/推导校验、样式与业务断言生成；执行时从外部批准摘要重建计划，拒绝静默修改预期、容差、状态和动作路线。先用无关组件与独立上下文验证并冻结，再开发全新 Workshop enrollment card，对比 v5 手写自测与 v6 契约生成。

| 双端结果 | v5 | v6 |
| --- | ---: | ---: |
| 最终 P / F / U / N/A | 674 / 0 / 50 / 44 | 674 / 0 / 50 / 44 |
| 最终未评估 | 50/724，6.91% | 50/724，6.91% |
| 自然产品/业务漏检及修复率 | N/A：无确认缺陷分母 | N/A：无确认缺陷分母 |
| 冻结行原始 TP / FP / 未裁定 | 0 / 0 / 3 | 3 / 0 / 1 |
| 实现→自身最终证据封存，含等待 | 33:11.0 | 32:52.6 |

新版原始三个高度F是47.99994dp与48dp的精度边界，原始检测和F→P保留，但不能宣称修复三个真实bug。两组502个公开适用预期事后均语义一致；新版四份计划通过独立来源重建，16次通用篡改负例及额外降级尝试被拒绝。机制生效不等于自然漏检、误报或修复优势已被证明。iOS计算文字样式继续U。

**同源码原生配对：**未评估70/960→73/960，新增0、丢失3、已裁定冲突0；命令资源453.093→425.328秒，约−6.13%。iOS下降约8.03%，Android增加约16.42%；单次共享机器/缓存样本不支持稳定提速结论。共同width适配不计新版收益。

保留46条采集命令、1599个快照及12次非零退出。首轮新版采集比另一组源码封存早26.5秒，违反预定屏障；原始自测均在全部有效语料封存后才开始，排程偏差仍明确限制结论。四阶段双组评分封存后才揭盲，旧失败/评分未重写。经典FPR及产品误报率不可得，未知主张和数值分辨率限制单列。

[完整报告](validation/contract-forward/RESULTS.md)、[全部指标与成本](validation/contract-forward/TABLES.md)、[通用实现](validation/contract-forward/ENGINEERING.md)、[设计契约用法](native-ui-agent/references/design-contract.md)、[失败](validation/contract-forward/FAILURES.md)、[原图](validation/contract-forward/GALLERY.md)、[复现](validation/contract-forward/REPRODUCE.md)。本轮为生产组件薄宿主验收，不覆盖完整旧App及后端。

## 上一轮 v5：覆盖改善，采集成本增加，质量优势未证实

冻结可执行的多目标观测和逐状态断言编译后，独立设计全新 Print Batch Approval，比较冻结 Skill v4 / v5。两组都用 Skill；88 次计划原生采集、1891 个快照记录及 3 次失败尝试全部保留。四阶段双组评分先封存，再揭盲。

**同源码配对：**运行时未评估 **54.39% → 40.85%**，新增 **2424** 行证据（1470 原生类、954 视觉），没有丢失或已裁定冲突；命令资源时间 **365.634 → 734.914 秒，+101.00%**。这些是同源码工具证据，不能替代代码质量结论。

| 不同实现的开发结果 | Skill v4 | Skill v5 |
| --- | ---: | ---: |
| 成功刺激业务漏检 | N/A：无自然 F | N/A：无自然 F |
| 首版运行时合并漏检† | 0/23 | 53/122，43.44% |
| 首次主张条件误报占比 FP/(TP+FP) | 137/(46+137)，74.86% | 114/(46+114)，71.25% |
| 未裁定 / 未映射主张 | 376 | 415 |
| 首版 F→最终 P / F / U† | 0 / 0 / 23 | 53 / 46 / 23 |
| 最终运行时未评估 | 5878/14324，41.04% | 5880/14324，41.05% |
| 实现开始→自身最终语料封存，含等待 | 34:50.7 | 35:35.2 |

†原子失败行不是独立 bug。新版漏了46条字体规则：代码和自测把同一设计预期写错，逐状态矩阵无法自动纠正。两组各23个原始 AX 尺寸 F 修复后变为48±2pt，仍为 U，不算通过。新版最终仍有74条字体 F。误报条件比例之外，未知主张两端范围分别24.51%–91.77% / 19.83%–92.00%；不能宣称误报已显著下降，缺完整 TN 分母时经典 FPR 不可得。

[完整报告](validation/state-forward/RESULTS.md)、[全部表格与成本](validation/state-forward/TABLES.md)、[原因分析](validation/state-forward/ANALYSIS.md)、[通用实现](validation/state-forward/ENGINEERING.md)、[共同修正](validation/state-forward/INFRASTRUCTURE.md)、[失败记录](validation/state-forward/FAILURES.md)、[原图](validation/state-forward/GALLERY.md)、[复现](validation/state-forward/REPRODUCE.md)。iOS 数值样式和物理点击区域缺口继续记 U；CI 验证证据完整性，不表示组件验收全部通过。

## 上一轮 v4：采集显著变快，未证实覆盖和漏检改善

先修复回调断言的成功原生派发前置条件，再冻结通用优化；独立设计全新 WaterRound 放水审批组件，在 AlertToast / Reply 生产模块中盲测。两组均用 Skill，对比共同修复后的 v3 与 v4；全部独立评分、自查匹配和同源码配对封存后才揭盲。

| 双端指标 | common-v3＋共同修复 | candidate-v4 |
| --- | ---: | ---: |
| 成功请求刺激后的业务漏检 | N/A：没有自然 F | 6/8，75.0% |
| 可裁定映射发现误报占比 FP/(TP+FP) | 0/5 | 0/8 |
| 首版运行时 F→最终 P† | 12/12 | 20/22 |
| 最终运行时未评估 | 1625/3470，46.8% | 1545/3470，44.5% |
| 实现开始→自身最终语料封存，含等待 | 90:14.6 | 52:26.0 |

†冻结 F 行包含重复症状和数值边界，不能当作独立 bug 数。新版八个业务 F 来自一个装饰勾号并入 AX 名称的问题，自查只明确报告两个状态；一次共因修复使八项通过，但不倒填六项检出信用。两组最终 Android 各两行 `47.99994 dp < 48 dp` 的严格阈值 F 保留，不解读为有意义的尺寸缺陷。未映射旧/新 7/2 条发现及旧组一条不确定发现另列，0 个确认误报不代表其余发现都正确。

**同源码配对更能说明工具收益：**iOS 命令耗时降低 89.3%–89.4%，Android 降低 47.3%–57.1%；合计 53:34.6→6:26.7。运行时新增 2 项证据、失去 3 项，净 −1，无判定冲突。因此没有证实覆盖提升。两份不同实现的最终 U 比例差不能归因为工具。回调门控、宿主、输入翻译和评估格式修正是共同基础设施。

完成 68 次计划采集，保留 1474 个快照记录、额外失败尝试和编译日志。禁用/未派发后的空回调仍为未评估；字号、内部 padding、物理 hit 等能力缺口也继续保留。不能声称整屏或业务全部通过。

[完整新报告](validation/dispatch-forward/RESULTS.md)、[完整表格与成本](validation/dispatch-forward/TABLES.md)、[通用实现](validation/dispatch-forward/ENGINEERING.md)、[失败记录](validation/dispatch-forward/FAILURES.md)、[原图与修正](validation/dispatch-forward/GALLERY.md)、[复现说明](validation/dispatch-forward/REPRODUCE.md)。旧轮次原始得分与负面结论保持不变。

## 上一轮 v2 / v3：观测覆盖改善，采集成本上升

完成全新退款/换货组件的两组盲测、同源码采集器配对与 68 次计划原生采集，保留 3,212 张快照。全部主评分、发现匹配、配对评分封存后才揭盲；两组均使用 Skill。

| 指标，双端合计 | 旧 v2 | 新 v3 |
| --- | ---: | ---: |
| 确认误报发现占比 FP/(TP+FP) | 0/21，0% | 0/10，0% |
| 漏检，冻结原子口径† | 34/55，61.8% | 0/10，0% |
| 最终运行时未评估 | 208/2518，8.3% | 198/2518，7.9% |
| 首版评分失败转为通过† | 55/55，100% | 10/10，100% |
| 自查 / 修复秒数 | 547.296 / 774.762 | 600.000 / 746.000 |

†旧组 28 个首版失败、2 个最终失败是未成功派发动作后的回调区间事实，不能证明业务 handler 错误；不能把这些分数当作独立业务 bug 数。业务漏检优势也受此评分前提限制。未裁定和缺证据项继续保留，经典误报率因无完整 TN 分母不可得。

更能隔离工具能力的同源码配对：运行时未评估 **26.0% → 10.1%**，新获得 296 项证据、失去 5 项，净改善 291 项；采集命令 **56:48 → 96:27**，增加约 69.8%。公共 JSON、宿主与排程修复均不算新版独有收益。两组确认误报占比和首版失败转通过率相同，不能声称这两项提升。

两组实际自查语料采集耗时为 56:48 / 2:49:07，不能只报自查分钟数。旧组首版跨服务中断，精确活跃耗时不可得；一个任务、相关平台、没有人类金标准，结果只支持描述性比较。

[完整报告与归因限制](validation/tool-forward/RESULTS.md)、[完整指标与耗时](validation/tool-forward/TABLES.md)、[失败记录](validation/tool-forward/FAILURES.md)、[原始图片](validation/tool-forward/GALLERY.md)。本轮原始得分与未成功尝试全部保留，未针对结果修改业务代码或工具后重算。

## 前一轮三臂盲测：未证实新版额外收益

先冻结通用改进，再由独立上下文设计全新的服务预约改期组件；比较无 Skill、冻结 v1、改进 v2。完成84组原生采集、1,086张快照及双端各1次干净检出复跑，先封存评分和自查匹配再揭盲。

| 指标，双端合计 | 无 Skill | v1 | v2 |
| --- | ---: | ---: | ---: |
| 首版确认缺陷簇 | 3 | 2 | 2 |
| 精确规则检出 TP / FN | 13 / 0 | 7 / 0 | 7 / 0 |
| 首版确认失败修复 | 13/13 | 7/7 | 7/7 |
| 确认误报规则项 | 0* | 3 | 4 |
| 最终 iOS 原始评分：通过/失败/未评估 | 82/0/2 | 76/0/8 | 76/0/8 |
| 实现＋自查＋修复 | 24:09.5 | 21:58.1 | 20:50.0 |

*无 Skill 另有2项未裁定发现，含类似AX包装节点质疑；0项确认误报不代表没有可疑误判。原始评分里的部分通过还带有未测子方面，例如R13的物理触摸区域，**不能解释为整条要求完整通过**。独立覆盖附录进一步列明范围：完整要求通过率无法得出；排除已知触摸区域缺证据后，最终iOS可能完整支持的项数至多为75/69/69，这些仍不是已验证通过数。

三组都找全并修复了各自已确认的缺陷；两组 Skill 的极端长内容目标搜索留下额外6项未评估。新观测器是三组共享能力，不能把其收益算作 v2 独享收益。一个任务、每组一次运行、共享硬件和缓存，也不足以证明质量或速度的因果提升。

[完整新报告、图片与覆盖附录](validation/fresh-blind/README.md)、[可复算统计](validation/fresh-blind/result-summary.json)、[首轮原因分析](validation/improvement-analysis.md)。本轮保留了负面结果，没有针对新隐藏用例继续调优后重算。

## 首轮盲测：未观察到额外收益

2026-10-18，独立固定附件传输队列的设计与验收，以相同模型设置、宿主和工具，对比有/无 Skill。首版自查封存后才执行隐藏场景，匿名评分封存后才揭盲；完成 56 次有效原生采集和 4 次干净检出复跑。

| 指标 | 无 Skill | 有 Skill |
| --- | ---: | ---: |
| iOS 首版失败规则项 | 3 | 3 |
| 自查漏检 | 1/3，33.3% | 1/3，33.3% |
| 一轮修复 | 3/3 | 3/3 |
| 保留场景确认新失败 | 0 | 0 |
| 实现＋自查＋修复耗时 | 14:05.7 | 13:37.7 |

三个失败项来自一个窄屏重排缺陷簇。Android 未确认首版缺陷，漏检/修复率分母为零，记 N/A。每组最终 368 个规则项中 223 通过、145 未完整评估，不能称为全部通过。**本轮没有观察到 Skill 的额外检出或修复优势**；单次小样本与共享缓存也不支持提速结论。

完整[盲测报告与前后图片](validation/blind-comparison/README.md)、[可复算统计](validation/blind-comparison/result-summary.json)、[冻结源码](validation/blind-comparison/implementations/)和[独立设计/验收](validation/blind-comparison/design-team/public/brief.md)已归档。报告保留程序性盲法、基础设施修正、iOS 交互和屏幕外视觉的证据限制。Skill 在实验中保持原样。

## 之前的新增功能验证

2026-10-18 在固定上游提交上开发两个新增功能，独立设计与验收标准先于实现提交到 Git，未向生产代码注入已知错误：

| 项目 | 新增 UI | 最终结果 | 源码修正 |
| --- | --- | --- | --- |
| [Android Reply](https://github.com/android/compose-samples) | 邮件卡片附件摘要：数量、首个描述、长文省略、空态隐藏 | **5/5** 场景通过；真实 Activity 点击复验通过 | 首版达标，0 轮；未人为制造错误 |
| [iOS AlertToast](https://github.com/elai950/AlertToast) | 可选上传进度 HUD：百分比、进度条、长标题、旧调用兼容 | **6/6** 场景通过；旧调用像素不变 | 看图发现系统灰轨道偏离浅蓝参考，1 轮样式修正 |

干净检出固定上游提交、应用功能补丁和安装宿主后，两端又各实际渲染 1 次；结果与最终同状态图片一致。

![独立参考、首版及最终结果](validation/feature-development/comparison.png)

完整的[新增功能开发报告](validation/feature-development/README.md)、[设计冻结清单](validation/feature-development/design/freeze.json)、[机器可读结果](validation/feature-development/result-summary.json)。之前的[受控回归试验](validation/native-ui-pilot/README.md)单独保留，不能与新增开发试验混为一谈。

这一轮新增功能试验本身没有无 Skill 对照组，不能单独据此声称提升了某个百分比的 PR 质量。首次快速视觉检查曾漏过轨道色，详细设计核对才发现；原始通过、后续失败及修正记录均保留。字号、颜色、间距能否精确观测取决于平台和采样对象。

## 通用观测与反馈工具 v3 / v4 / v5 / v6 / v7 / v8 / v9

v9 增加[需求路由、统一执行计划与定向复验](native-ui-agent/references/decision-feedback.md)：`requirement_routes.py` 把必需需求绑定到状态与断言，区分环境、契约、证据和产品诊断；`execution_plan.py` 从同一份独立计划生成动作与采集范围，保留实际源码、输入、图片和覆盖回执；`retest_plan.py` 按原始失败、实际改动与批准的回归依赖选择复验状态。定向采集遗漏的状态明确延期到最终完整验收，不能混成通过。iOS 将同一新鲜状态扫描用于该状态的目标观测，减少重复扫描，仍保留真实派发、即时帧和版本绑定。

v8 增加[契约绑定的视觉观测](native-ui-agent/references/atomic-review.md)：独立设计先固定颜色、画布、换行、遮挡等原子规则及责任层；工具生成发现 ID、预期、单位和来源，模型只提交原图中的实际观察。配色由原始 PNG 与原生节点坐标自动测量，模型不能填写测得颜色或改预期。缺少原生映射、状态不一致、非平色或证据冲突仍为未评估。

共享评估器校验真实运行环境，数值事实由工具计算，定性结论与产品责任需两个独立上下文一致；格式拒绝与真实产品误报分别统计。它没有增加通用 SwiftUI 计算样式接口。[工程实现与限制](validation/atomic-forward/ENGINEERING.md)、[中性完整示例](native-ui-agent/assets/atomic-example/)。

新版把 AX 容器与实际控件叶节点判定、长内容反馈定位、输入与回调绑定、逐状态滚动覆盖，以及类型化断言做成可执行工具。歧义、覆盖缺口、无运行时依据的属性保留为未评估；源码声明不能替代实际生效的样式。实测通用控件包括 Button 和 Switch，Android 语义点击不等于操作系统物理触摸。

v4 增加单次公开 iOS AX 快照遍历、经来源与产物校验的编译缓存、动作即时收据后有界重新定位，以及减少冗余采图的通用执行能力。输入、进程、动作、完整滚动证据均重新生成；不复用旧截图。回调的成功派发门控也应用于共同基线。[本轮实现和通用探针](validation/dispatch-forward/ENGINEERING.md)与盲测结果分别公开。

v5 增加有界的动作后多目标观测、严格绑定输入/进程/事件的原始帧合并，以及状态×检查方面的断言编译。目标覆盖不等于完整内容或不存在证明；回调即时区间保持不变。编译器保证声明矩阵的完整性，不能保证预期值正确。[状态证据协议](native-ui-agent/references/state-evidence.md)和[本轮工程与边界](validation/state-forward/ENGINEERING.md)给出可执行接口。

接入与边界见[原生工具协议](native-ui-agent/references/native-tools.md)、[独立通用能力验证](validation/tool-capabilities/REPORT.md)与[新版两组试验](validation/tool-forward/README.md)。业务试验调用真实生产模块中的新增组件，但不覆盖原应用完整页面、导航或后端。

## 前一轮覆盖能力改进

[首轮分析](validation/improvement-analysis.md)把“一个缺陷簇的规则归因遗漏”与“缺少原生运行时证据”分开。新版增加需求×场景×检查方面的证据账本、完整滚动采样要求，以及可接入真实生产 View 的独立 iOS App + XCUITest 观测器。旧版材料和原始得分继续保留，未用旧失败条件定义新版成功。

`coverage.py`检查计划缺项、证据指纹和方法约束；运行时动作不能由源码或视觉判断代替。它不会判断证据的语义真实性。iOS观测器记录实际 AX、屏幕点坐标、截图映射、真实点击和回调，以及同进程调用方更新；它不提供通用 SwiftUI 字号、padding、颜色树。缺失属性继续保留为未评估。

接入方式见[覆盖协议](native-ui-agent/references/coverage.md)、[iOS观测器契约](native-ui-agent/assets/ios-observer/CONTRACT.md)。[独立能力探针](validation/observer-probes/README.md)保留成功与失败记录；生产接入还需让桥接真正导入并调用目标模块，不能只验证一份未使用生产包的简单 View。

## 工作方式

1. 按当前需求、代码改动、调用位置和业务文字定位真实组件，不要求全项目登记业务 ID。
2. 实现前固定独立设计、规则来源及相关状态。新设计线框与原生截图不是同一种像素基准。
3. 生成薄测试宿主，调用生产 UI，控制数据、主题、时间与动画。
4. `capture` 执行真实原生命令，保存本轮图片、原生报告、源码/参考指纹和命令日志。
5. Agent 阅读实际图；`review` 汇总绑定本轮证据的视觉结论与数值/像素断言。
6. 有问题时修改生产源码，重新构建和渲染；组件通过后另做实际页面复验。

`captured` 只表示证据采集成功。缺测试、缺图、缺参考、无测量或未审图都不等于样式通过。不会自动覆盖正式 golden，也不能用旧截图声明新代码通过。

## 使用 Skill

将 [`native-ui-agent/`](native-ui-agent/SKILL.md) 作为宿主 coding agent 可加载的 Skill 目录，或让 agent 直接读取其 `SKILL.md`。该目录可独立复制；`validation/` 是工程接入及验证材料。

只使用 Skill 源码时，可以稀疏拉取这个目录；完整验证档案包含大量原始截图和日志：

```sh
git clone --filter=blob:none --sparse https://github.com/KamisamaJin/native-ui-agent.git native-ui-agent-repo
git -C native-ui-agent-repo sparse-checkout set native-ui-agent
```

示例需求：

> 使用 native-ui-agent，在现有邮件卡片中增加附件摘要。先固定设计参考和验收，再复用工程主题、数据和组件生成测试宿主，渲染普通、长描述、深色和窄屏状态；按图与原生测量修正，提供页面复验及证据。

Skill 目前给出 SwiftUI/UIKit、Compose/Views 的接入指导；仓库实跑覆盖的是 **SwiftUI 和 Compose**。它不自动适配任意旧项目，也不替代业务数据、导航和后端契约测试。

## 契约绑定的样式验收

精确样式验收走 `design_contract.py → 原生 observer → review_contract.py`。先由独立设计方批准契约、原子采样策略及其摘要，再生成计划并采集；开发实现不能自行更新批准摘要。人工和 AI 使用同一个观察接口：从工具目录选择 `review_id`，只填写实际布尔观察、理由及原始帧索引。预期、单位、颜色实际值和结论均由工具生成。

```sh
python3 native-ui-agent/scripts/review_contract.py catalog \
  --plan generated/plan.json --design-lock approved-lock.json --design-sha256 LOCK_SHA \
  --policy policy.json --policy-sha256 POLICY_SHA --platform ios --output catalog.json
python3 native-ui-agent/scripts/review_contract.py review \
  --plan generated/plan.json --design-lock approved-lock.json --design-sha256 LOCK_SHA \
  --policy policy.json --policy-sha256 POLICY_SHA --platform ios \
  --observation capture/observation.json --submission observations.json --output new-review
```

Android 使用同样接口，将平台改为 `android`。独立验收再由 `acceptance.py` 合并两份分别产生的判断；意见冲突保留 U，不能修改数值事实。完整输入与命令见[原子验收协议](native-ui-agent/references/atomic-review.md)和[契约生成协议](native-ui-agent/references/design-contract.md)。以下通用 Runner 是基础图片循环入口，其自由格式视觉报告不能替代上述契约绑定。

## Runner

Python 3.9+，依赖见 [requirements.txt](native-ui-agent/scripts/requirements.txt)：

```sh
python3 -m pip install -r native-ui-agent/scripts/requirements.txt
python3 native-ui-agent/scripts/ui_loop.py capture \
  --project /path/to/native-project --profile /path/to/case.json \
  --output /path/to/new-evidence-directory
```

Agent 看图后按[协议](native-ui-agent/references/protocol.md)写 `visual-findings.json`：

```sh
python3 native-ui-agent/scripts/ui_loop.py review \
  --capture /path/to/new-evidence-directory/capture.json \
  --findings /path/to/visual-findings.json --output /path/to/new-review-directory
```

每个 profile 对应一个组件状态、一张 actual 图；项目命令使用 argv 数组执行。三类检查分别保留方法和边界：

| 检查 | 能证明什么 |
| --- | --- |
| visual | Agent/人工对实际图与独立参考的判断；可能漏检 |
| numeric | 宿主实际提供的特定测量与期望比较；缺数据为 needs_review |
| pixel | 同尺寸原生图的区域/整图 RGBA 差异；不证明业务或样式属性语义 |

平台接入看[平台适配](native-ui-agent/references/platforms.md)，配置结构看 [Android 示例](native-ui-agent/assets/profile.example.json)、[iOS 示例](native-ui-agent/assets/profile.ios.example.json)。

## 复跑双端新增功能

需要 macOS、已完成首次设置的 Xcode、已安装 iOS 模拟器、Android SDK 36 和 JDK 21；实跑版本与命令详见[报告](validation/feature-development/README.md#复跑)。

```sh
python3 validation/feature-development/prepare.py \
  --workspace /absolute/path/to/new-workspace \
  --android-sdk /absolute/path/to/Android/sdk \
  --java-home /absolute/path/to/jdk-21/Contents/Home \
  --ios-device YOUR_INSTALLED_SIMULATOR_UUID
```

此入口只接受新目录，检出固定提交、应用 host/生产功能补丁、复制测试宿主并生成本机 profiles。不会覆盖已有应用工作目录。功能交付为完整补丁和新文件，不把整个上游仓库及 SDK 上传到这里。

归档 capture 保留当时绝对路径和环境供追溯；迁移机器时使用 `prepare.py` 生成本机配置。不同系统/渲染器可能改变像素，不能直接更新基准消除差异。

## 验证

```sh
python3 -B -m unittest discover -s native-ui-agent/tests -v
python3 validation/feature-development/verify_evidence.py
python3 validation/blind-comparison/verify_evidence.py
python3 validation/observer-probes/verify_preflight.py
python3 validation/fresh-blind/verify_evidence.py
python3 validation/tool-forward/verify_capabilities.py
python3 validation/tool-forward/verify_engineering.py
python3 validation/tool-forward/verify_frozen.py --include-private
python3 validation/tool-forward/metrics.py --self-test
python3 validation/tool-forward/verify_evidence.py
python3 validation/tool-forward/verify_protocol.py
python3 validation/tool-forward/build_summary.py --check
python3 validation/tool-forward/build_tables.py --check
python3 validation/tool-forward/build_failure_index.py
python3 validation/tool-forward/verify_artifacts.py
python3 -B validation/atomic-forward/test_metrics.py
python3 -B validation/publications/atomic-v8/verify.py
python3 -B validation/feedback-forward/test_metrics.py
python3 -B validation/feedback-forward/test_delivery_metrics.py
python3 -B validation/feedback-forward/test_final_outcome_metrics.py
python3 -B validation/feedback-forward/test_implementation_audit.py
python3 -B validation/feedback-forward/test_source_outcomes.py
python3 -B validation/feedback-forward/verify.py
python3 -B validation/feedback-forward/benchmark_summary.py --check
python3 -B validation/feedback-forward/build_summary.py --check
python3 -B validation/feedback-forward/build_tables.py --check
python3 -B validation/feedback-forward/build_failure_index.py --check
python3 -B validation/feedback-forward/build_gallery.py --check
python3 -B validation/feedback-forward/artifacts.py
```

当前工具冻结前通过 132 项单元测试。[v9 复算入口](validation/feedback-forward/REPRODUCE.md)说明原始来源、逐状态覆盖、完整自验、独立双评和成本复算。旧轮次的工具及根目录依赖按原字节归档；v8 使用上面的历史视图入口，v7 使用 `python3 -B validation/publication_history.py multitask-v7 verify_tools.py` 和同入口的 `artifacts.py`，避免拿新工具覆盖旧分数。

历史不含本机缓存的异地 Git 归档核验见[旧记录](validation/fresh-blind/verification.json)；tool-forward 轮次当时的 55 项单元测试与 15 项验证见[该轮记录](validation/tool-forward-verification.json)。

第一条验证 runner、覆盖账本和观测器的协议与失效行为；后续命令跨机器审计归档图片、报告、原生测试数、冻结哈希、盲测封存与统计运算，不运行原生 SDK 或模型。GitHub CI 执行这些检查，不声称重新运行双端模拟器。

## 目录

```text
native-ui-agent/                  可复制的 Skill、runner、协议与测试
validation/feature-development/  新增 UI：冻结设计、功能补丁、宿主、复跑入口与证据
validation/blind-comparison/     首轮有/无 Skill 盲测及冻结v1
validation/fresh-blind/          全新预约UI：无Skill/v1/v2、预注册与原生证据
validation/tool-forward/         全新退款UI：旧v2/新v3、配对采集与完整评分
validation/dispatch-forward/     成功派发前提、采集优化与旧v3/新v4
validation/state-forward/        逐状态覆盖与旧v4/新v5
validation/contract-forward/     独立设计契约与旧v5/新v6
validation/multitask-forward/    精度边界、三任务旧v6/新v7
validation/atomic-forward/       绑定发现、原子像素断言与三任务旧v7/新v8
validation/feedback-forward/     需求路由、统一执行、同首版PR的旧v8/新v9盲测
validation/publications/atomic-v8/ 原字节历史视图与旧v8发布依赖回放
validation/tool-capabilities/    通用叶节点、长内容与逐状态覆盖原生验证
validation/observer-probes/      独立通用观测能力探针及原始失败
validation/native-ui-pilot/       历史受控回归试验、宿主接入记录及上游许可
```

## License

原创 Skill、runner、文档和宿主代码使用 [MIT](LICENSE)。上游派生组件补丁、截图与生成报告保留各自许可，见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。克隆工程、构建缓存、SDK、签名文件和本地环境配置由 `.gitignore` 排除。本项目独立于 Android、Apple、Point-Free 及上述开源维护者。
