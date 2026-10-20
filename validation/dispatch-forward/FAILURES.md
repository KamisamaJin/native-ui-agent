# 失败与未评估记录

原始命令、图片、收据、自查和编译日志全部保留。采集失败、业务失败与未评估不是同一个概念。

归档采集命令 80 条（含公开集成和首次翻译尝试），非零退出 4 条。通用工程探针另有 2 次有意缺失目标的原生非零退出。

## 非零采集命令

| 记录 | 退出码 | 秒 |
| --- | ---: | ---: |
| [evidence/administrative-first-d0/submission-3d6389/ios/C01-command.json](evidence/administrative-first-d0/submission-3d6389/ios/C01-command.json) | 2 | 0.070 |
| [evidence/administrative-first-d0/submission-3d6389/ios/C02-command.json](evidence/administrative-first-d0/submission-3d6389/ios/C02-command.json) | 2 | 0.051 |
| [evidence/administrative-first-d0/submission-3d6389/ios/C03-command.json](evidence/administrative-first-d0/submission-3d6389/ios/C03-command.json) | 2 | 0.053 |
| [evidence/administrative-first-d0/submission-3d6389/ios/C04-command.json](evidence/administrative-first-d0/submission-3d6389/ios/C04-command.json) | 2 | 0.055 |

首次输入翻译的 iOS preflight 拒绝没有执行原生测试；同批 Android 执行成功，但其映射已废弃。这 8 次都保留并计入对应初始反馈流程，不归为组件业务缺陷。

## 编译失败

- [private/submissions/submission-e572b1/repair.json](private/submissions/submission-e572b1/repair.json)，JSON pointer `/compilation_attempts/1`；原始错误与后续编译记录在同一不可变报告内。

## 独立验收 F / U

| 匿名报告 | F 行 | U 行 |
| --- | ---: | ---: |
| [d0/sample-716d41](design/private/evaluation/d0/sample-716d41/grade.json) | 22 | 1027 |
| [d0/sample-e318ec](design/private/evaluation/d0/sample-e318ec/grade.json) | 12 | 1092 |
| [final/sample-716d41](design/private/evaluation/final/sample-716d41/grade.json) | 3 | 1545 |
| [final/sample-e318ec](design/private/evaluation/final/sample-e318ec/grade.json) | 2 | 1625 |
| [paired-d0/sample-716d41](design/private/evaluation/paired-d0/sample-716d41/paired-grade.json) | 22 | 1026 |
| [paired-d0/sample-e318ec](design/private/evaluation/paired-d0/sample-e318ec/paired-grade.json) | 12 | 1092 |

完整原子 key、逐分母未评估原因与引用见 [failure-index.json](failure-index.json)。字号、padding、物理 hit 区域等运行时能力缺口继续保留；未成功派发后的回调区间不判为 handler 缺陷。修复前后同一 key 的 F→P/F/U、回归与新增可评估失败见 [result-summary.json](result-summary.json)。

## 共同基础设施记录

- [harness-failures/administrative.json](harness-failures/administrative.json)
- [harness-failures/clean-checkout-administration.json](harness-failures/clean-checkout-administration.json)
- [harness-failures/clean-checkout-bsdtar-sidecar.log](harness-failures/clean-checkout-bsdtar-sidecar.log)
- [harness-failures/clean-checkout-missing-dependency.log](harness-failures/clean-checkout-missing-dependency.log)
- [harness-failures/conventions-report-recovery.json](harness-failures/conventions-report-recovery.json)
- [harness-failures/failure-index-directory-filter.json](harness-failures/failure-index-directory-filter.json)
- [harness-failures/image-preview-discrepancy.json](harness-failures/image-preview-discrepancy.json)
- [harness-failures/operator-py-stdlib-shadow.txt](harness-failures/operator-py-stdlib-shadow.txt)
- [harness-failures/trial-operator-before-state-id-fix.txt](harness-failures/trial-operator-before-state-id-fix.txt)

独立通用探针还保留了错误画布色预期造成的视觉失败，以及首次映射别名导致的未评估；见 [ENGINEERING.md](ENGINEERING.md) 和 [独立通用验证](independent-generic/summary.json)。这些不是 WaterRound 样本，也不计为新版工具独享收益。
