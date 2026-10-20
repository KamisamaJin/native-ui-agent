# 指标与成本

| 双端合计 | common-v3 + 共同派发修复 | candidate-v4 |
| --- | --- | --- |
| 业务漏检（成功原生派发后） | N/A（零分母） | 6/8，75.0% |
| 确认发现误报占比（运行时原子行） | 0/5，0.0% | 0/8，0.0% |
| 全部运行时漏检（描述性） | 7/12，58.3% | 14/22，63.6% |
| 首版运行时失败→最终通过 | 12/12，100.0% | 20/22，90.9% |
| 首版业务失败→最终通过 | N/A（零分母） | 8/8，100.0% |
| D0 运行时未评估 | 1092/2262，48.3% | 1027/2262，45.4% |
| 最终运行时未评估（六场景） | 1625/3470，46.8% | 1545/3470，44.5% |
| 连续实现开始→自身最终语料封存 | 1:30:15 | 52:26 |
| 必需阶段墙钟之和 | 1:21:56 | 17:27 |
| 队列、屏障和未分配间隔 | 8:19 | 34:59 |

两组均使用 Skill。原子行重复症状不等于独立缺陷数量；未裁定/未映射发现单列，不自动算误报。没有完整 TN 宇宙，因此不报告经典 FP/(FP+TN)。零自然业务反例分母为 N/A。

冻结 F 行不等于独立产品缺陷数：两组最终 Android 各有两行 `47.99994 dp < 48 dp` 的数值边界失败；candidate-v4 的八个首版业务 F 是同一个装饰勾号合并进 AX 名称的契约问题。原始分数保留，解释与预览排查更正见 [RESULTS.md](RESULTS.md)。

## 各平台与分母

### common-v3 + 共同派发修复

| 平台 | 版本 | 分母 | 必需 | P | F | U |
| --- | --- | --- | --- | --- | --- | --- |
| ios | d0 | runtime_business | 430 | 277 | 0 | 153 |
| ios | d0 | runtime_visual | 227 | 207 | 12 | 8 |
| ios | d0 | runtime_integration | 90 | 90 | 0 | 0 |
| ios | d0 | runtime_capability | 384 | 0 | 0 | 384 |
| ios | d0 | input_member_integration | 405 | 405 | 0 | 0 |
| ios | d0 | source_api | 57 | 57 | 0 | 0 |
| ios | final | runtime_business | 678 | 464 | 0 | 214 |
| ios | final | runtime_visual | 341 | 329 | 0 | 12 |
| ios | final | runtime_integration | 136 | 136 | 0 | 0 |
| ios | final | runtime_capability | 580 | 0 | 0 | 580 |
| ios | final | input_member_integration | 630 | 630 | 0 | 0 |
| ios | final | source_api | 57 | 57 | 0 | 0 |
| android | d0 | runtime_business | 430 | 287 | 0 | 143 |
| android | d0 | runtime_visual | 227 | 207 | 0 | 20 |
| android | d0 | runtime_integration | 90 | 90 | 0 | 0 |
| android | d0 | runtime_capability | 384 | 0 | 0 | 384 |
| android | d0 | input_member_integration | 405 | 405 | 0 | 0 |
| android | d0 | source_api | 56 | 56 | 0 | 0 |
| android | final | runtime_business | 678 | 464 | 0 | 214 |
| android | final | runtime_visual | 341 | 314 | 2 | 25 |
| android | final | runtime_integration | 136 | 136 | 0 | 0 |
| android | final | runtime_capability | 580 | 0 | 0 | 580 |
| android | final | input_member_integration | 630 | 630 | 0 | 0 |
| android | final | source_api | 56 | 56 | 0 | 0 |

确认原始发现 12 条；未映射确认发现 7 条；不确定发现 1 条。最终新评估失败 0 行，P→F 回归 0 行。

### candidate-v4

| 平台 | 版本 | 分母 | 必需 | P | F | U |
| --- | --- | --- | --- | --- | --- | --- |
| ios | d0 | runtime_business | 430 | 308 | 0 | 122 |
| ios | d0 | runtime_visual | 227 | 207 | 12 | 8 |
| ios | d0 | runtime_integration | 90 | 90 | 0 | 0 |
| ios | d0 | runtime_capability | 384 | 0 | 0 | 384 |
| ios | d0 | input_member_integration | 405 | 405 | 0 | 0 |
| ios | d0 | source_api | 57 | 57 | 0 | 0 |
| ios | final | runtime_business | 678 | 501 | 0 | 177 |
| ios | final | runtime_visual | 341 | 328 | 1 | 12 |
| ios | final | runtime_integration | 136 | 136 | 0 | 0 |
| ios | final | runtime_capability | 580 | 0 | 0 | 580 |
| ios | final | input_member_integration | 630 | 630 | 0 | 0 |
| ios | final | source_api | 57 | 57 | 0 | 0 |
| android | d0 | runtime_business | 430 | 308 | 8 | 114 |
| android | d0 | runtime_visual | 227 | 210 | 2 | 15 |
| android | d0 | runtime_integration | 90 | 90 | 0 | 0 |
| android | d0 | runtime_capability | 384 | 0 | 0 | 384 |
| android | d0 | input_member_integration | 405 | 405 | 0 | 0 |
| android | d0 | source_api | 56 | 56 | 0 | 0 |
| android | final | runtime_business | 678 | 505 | 0 | 173 |
| android | final | runtime_visual | 341 | 316 | 2 | 23 |
| android | final | runtime_integration | 136 | 136 | 0 | 0 |
| android | final | runtime_capability | 580 | 0 | 0 | 580 |
| android | final | input_member_integration | 630 | 630 | 0 | 0 |
| android | final | source_api | 56 | 56 | 0 | 0 |

确认原始发现 7 条；未映射确认发现 2 条；不确定发现 0 条。最终新评估失败 0 行，P→F 回归 0 行。

## 开发阶段耗时

| 工具 | 阶段 | 墙钟 | 并行命令秒数之和 | 归档墙钟 |
| --- | --- | --- | --- | --- |
| common-v3 + 共同派发修复 | 实现（包含公开集成） | 4:53 | — | — |
| common-v3 + 共同派发修复 | 首轮反馈采集（含首次翻译尝试） | 27:13 | 28:10 | 0:01 |
| common-v3 + 共同派发修复 | 只读看图自查 | 5:17 | — | — |
| common-v3 + 共同派发修复 | 一次源码修复 | 3:00 | — | — |
| common-v3 + 共同派发修复 | 最终六场景采集 | 41:32 | 42:55 | 0:01 |
| candidate-v4 | 实现（包含公开集成） | 3:53 | — | — |
| candidate-v4 | 首轮反馈采集（含首次翻译尝试） | 3:35 | 3:19 | 0:00 |
| candidate-v4 | 只读看图自查 | 4:43 | — | — |
| candidate-v4 | 一次源码修复 | 1:21 | — | — |
| candidate-v4 | 最终六场景采集 | 3:54 | 4:30 | 0:00 |

连续总时长包含真实屏障和队列；阶段之和不是活跃推理或一次无中断吞吐。并行命令之和不能当作端到端墙钟。公开集成已包含在实现阶段，不重复加总。

## 同一 D0 源码的新旧工具配对

| 固定源码 | 平台 | common-v3 命令之和 | candidate-v4 命令之和 | 减少 |
| --- | --- | --- | --- | --- |
| common-v3 + 共同派发修复 的 D0 | ios | 27:13 | 2:54 | 89.4% |
| common-v3 + 共同派发修复 的 D0 | android | 0:57 | 0:30 | 47.3% |
| candidate-v4 的 D0 | ios | 24:26 | 2:38 | 89.3% |
| candidate-v4 的 D0 | android | 0:59 | 0:25 | 57.1% |

| 固定源码 | 平台 | 必需运行时 | U→P/F | P/F→U | 净增 | P↔F 冲突 |
| --- | --- | --- | --- | --- | --- | --- |
| common-v3 + 共同派发修复 的 D0 | all | 2262 | 0 | 0 | 0 | 0 |
| common-v3 + 共同派发修复 的 D0 | ios | 1131 | 0 | 0 | 0 | 0 |
| common-v3 + 共同派发修复 的 D0 | android | 1131 | 0 | 0 | 0 | 0 |
| candidate-v4 的 D0 | all | 2262 | 2 | 3 | -1 | 0 |
| candidate-v4 的 D0 | ios | 1131 | 0 | 0 | 0 | 0 |
| candidate-v4 的 D0 | android | 1131 | 2 | 3 | -1 | 0 |

这些是同源码观测配对，仍有执行次序、共享机器和编译缓存影响；不是各优化开关的独立消融。通用门控修复、输入翻译与评估格式校准两组共享。

## 逐状态与动作目标观测

| 来源实现 | 采集批次 | 完整滚动状态 | 成功原生派发 | 动作后语义目标完整可见 |
| --- | --- | --- | --- | --- |
| common-v3 + 共同派发修复 | own-d0 | 16/16 | 30/38 | 38/38 |
| candidate-v4 | own-d0 | 16/16 | 30/38 | 38/38 |
| common-v3 + 共同派发修复 | own-final | 24/24 | 48/60 | 58/60 |
| candidate-v4 | own-final | 24/24 | 48/60 | 60/60 |
| common-v3 + 共同派发修复 | audit-v4-d0 | 16/16 | 30/38 | 38/38 |
| candidate-v4 | audit-v3-d0 | 16/16 | 30/38 | 37/38 |

可见性是原生几何事实，不等于动作成功或业务正确。禁用/未执行动作、消失目标和未知属性均保留；全部逐项收据在 observation-summary.json。

## 实验额外成本与未知项

实验额外同源码/统一评分采集 28 条命令，并行命令之和 33:15，开始均晚于两组开发周期结束。通用工程验证另有 15 次测试、241 张快照，命令之和 10:03。它们不计为业务样本。

模型 token 与账单未由宿主提供，记未知；不以估算替代测量。完整逐命令 build/cache/native 子耗时、原始连续起止及间隔见 cost-summary.json；独立评分与共同工程时间线另见 RESULTS.md。
