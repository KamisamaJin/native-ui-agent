# 失败与未完成记录

68 次计划原生采集全部归档，共有 16 次命令非零退出；这些执行失败不等于 16 个业务缺陷。所有尝试均留下 observation，部分证据可用与完整验收通过仍需分别判断。逐条退出码、耗时、日志、封条与省略录像清单见 [failure-index.json](failure-index.json)。

| 原始采集目录 | 非零退出次数 |
| --- | ---: |
| `evidence/d0/submission-4f4364` | 6 |
| `evidence/d0/submission-b2e249` | 1 |
| `evidence/final/submission-4f4364` | 3 |
| `paired-evidence/d0` | 6 |

共同的失败及修复按时间保留：

- 首版公开集成：两组 iOS 均触发 XCUI 非有限坐标 JSON 异常。原始工具、报告与日志留在首版源码/报告档案；共同传输补丁及无业务 UI 原生探针见 [transport-amendment/freeze.json](transport-amendment/freeze.json)。
- 最终排程首次启动：错误地要求 C07/C08，而独立冻结输入为 H01/H02。双方均在原生命令启动前失败；[原始 traceback](operator-failures/pre-native-case-name.json)与[统一修订](operator-case-name-amendment.json)保留。
- 采集结束后归档：脚本误要求首版存在最终阶段监视清单。保留[原始失败与源文件](archival-correction.json)，修订只改变已有批次记录的归档兼容性，未重跑原生测试。
- 通用能力工程中的负例与失败：另见 [独立验证](../tool-capabilities/REPORT.md)和 `engineering/`，不混入新业务样本。

旧版、原始失败、修复前源码、首次评分、未裁定发现、重复映射、未评估项及保留场景均保留。系统自动诊断录像按文件记录 SHA、大小和省略原因；原件仍在本机忽略缓存，断言截图和失败日志均入库。

业务上的失败与证据缺口见 [完整统计](TABLES.md)、[逐原子项账本](assessment-ledger.csv)及封存评分。F→U 不算修好，未裁定不硬算误报，源码声明不填补原生观测缺口。独立评估产生的工作草稿与失败记录也保留在已公开 evaluator 目录，最终封条明确指定权威版本；不会用后续改写覆盖原结果。
