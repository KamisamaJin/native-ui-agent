# candidate-v12.6 原封存 129 行复跑

仅导入冻结 candidate-v12.6，清单 SHA256 `8ee8858c1aa6dca038b1b40e06731200cac7039be4d2b611ab8c9093e4bd9d82`。运行前后完整核验 72 个冻结文件及精确目录清单，全部匹配。未使用未合格工程快照 candidate-v12.5。

本轮原始结果 **106P / 0F / 23U**。真实进程/文件 27P；合成原生协议 79P/2U；本次未执行的原生补证 21U。原 129 行完整保留，没有新失败、重试或判据调整。原始异常/负例输出均保留在 raw；它们按原不变量评分，并未记成产品缺陷。

驱动只把原 attempt-6 的候选路径和冻结摘要常量替换为 v12.6；resource_worker.py 和 fixture_process.py 字节不变。每个工具调用仍保存运行前后摘要和原始响应。适配器没有替工具实现门控或清理；各资源行结束后才执行原探针自身 teardown，不影响不可变的先前判定。

v12.6 的新 request/execution 身份拆分及 source/native-only 收尾单元检查没有被新增为独立测试行。本轮只覆盖原 sealed129；无 SDK 执行、无真实 source-only final completion 复跑，因此不把主流程167个单测或实际 v12.4 iOS 包的信用迁移给 v12.6。新增负例 SDK 补证会另写独立附录，正例原报告和旧失败保持原字节。

原 spec、attempt-1 至 attempt-6 全部非 cache 原产物与原 run-manifest、旧候选清单和90个既有 SDK 审查/清理文件运行前后核验无变化。此前退休的 cache 继续由既有归档映射追溯。

执行前已声明 run-manifest 排除 disposable cache/。仅在原始 run-manifest 验证后归档、逐文件核验并删除本轮 attempt-7/cache；清理清单将单独封存于 probes/native-review/attempt-7-cleanup。raw、源码、冻结候选、原 spec、主 study cache 和 SDK 原包均保留。
