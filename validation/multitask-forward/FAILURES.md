# 失败与未评估记录

本轮保留原始源码、编译失败、采集记录、原始自测发现、独立评分和失败的评估尝试。完整可检索索引见 [failures.json](failures.json)，失败原因分类与未覆盖要求见各独立 [D0](evaluation/D0/) / [FINAL](evaluation/FINAL/) summary。原始严格分数不因原因解释而改写。

- **共享验收集成失败：**原始独立 oracle 直接比较 Compose `Ltr` 与契约 `ltr`，使所有 Android 适用评分被完整性前提压成 U。三个初次验收者分别识别了该错误。原始四阶段评分保持原样；[单独修正复核](SHARED-INFRASTRUCTURE.md)使用原始观测和明确枚举适配，不增加产品修复或检出信用。62 个原始合成验收器控制使用了契约拼写，未覆盖真实原生线格式；新增回归包含真实原生记录，仍不把测试通过当成普遍正确性保证。
- **评估器自身分歧：**两条 evaluator-labelled FP 的原始像素证据可以复核，且两组 common 图都呈现 D0 色差、FINAL 恢复指定禁用填充，原定性评分却前后均 P。见 [未计分审计](GRADER-DISAGREEMENTS.md)。原分数保留，不能把这两条称为已确认的真实误报；AI 评分不是完整金标准。
- **自然产品问题：**独立初次验收确认了 iOS 替换调用方数据后沿用旧选择、部分控件默认禁用态额外淡化等问题。相同原因的多状态表现合为缺陷簇；逐行原始 F、簇证据和最终修复结论都保留。重复任务中的同类机制不能当作更多独立失败类型。
- **真实观测缺口：**通用 SwiftUI 计算字号/颜色/文字布局没有公开原生观测证据，继续 U。未成功派发的刺激不能凭空回调推断“业务无回调正确”；这些 U 也保留。语义/AX 矩形不能直接证明字面 padding、全部布局分配、变换后的绘制边界、祖先裁剪或真实系统命中区域。22 个选定断言族之外的 brief 要求不自动获得覆盖信用。
- **数值测量边界：**中性 iOS 验证返回过 `51.999999999999986` 和滚动中变化的范围。原始严格 F 留在 [中性结果](generic-summary.json)及[观测限制](operators/root-neutral-limitations.json)，没有加 epsilon 或扩大设计容差；这些数值不能自动算作自然产品 bug。新方法只消除对已有原生样本继续运算时额外引入的误差。
- **工程控制与失败尝试：**首批中性调用因使用保留状态名，在原生 SDK 启动前被拒绝，见 [原始调用](generic-runs.json)和[原始预检](development/neutral-preflight-1/)。改成合法无关状态后实采，两版记录都保留。共享环境回归首次测试的路径拼写错误保留在 [attempt-1](operators/shared-environment-tests-attempt-1.log)；修正的是测试路径，不是产品、观测或预期。编译预检的失败和后续成功记录在源提交目录及 failures.json，不能混作原生验收采集失败或事后产品修复。
- **设计与封存：**最初任务组在实现前因交互结构过于相近整体退回，保留 [原设计](design/COHORT-SEAL.json)和[前置审查](operators/preimplementation-design-review.json)。真实提前启动负例被包装器在 SDK 前拒绝，见 [记录](operators/actual-wrapper-early-launch.json)。上轮提前 26.5 秒采集的偏差仍保留在旧轮次，不用本轮屏障抹去历史。

同源码测量对照、原始→最终公开修复、隐藏输入结果和端到端成本均单列于 [TABLES.md](TABLES.md)。原始评分与事后共享修正评分必须一起阅读。未知、未映射描述和未覆盖需求都不等于通过。

补充封存关闭器最初把目录传给仅接受文件的 gate，在写入收据或揭盲前失败。原始派发 helper 未改动；单独关闭适配器核查三个完整 SEAL，再展开全部精确文件。见 [失败记录](operators/supplement-close-failed-attempt.json)及 [关闭适配器](close_supplement_gate.py)。

干净导出曾发现发现账本重放仍依赖 cache 中的辅助像素记录路径，见 [原始失败](operators/export-audit/04.log)。相同字节已在修复前封存的 original-review 中；只修复重放器的精确路径翻译，不补证据或改变发现信用。见 [路径修复记录](operators/claim-evidence-portability-repair.json)。
