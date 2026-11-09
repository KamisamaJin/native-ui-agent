# candidate-v12.2 最后一次原 spec 复跑

仅执行新冻结目录 `validation/managed-forward/candidate-v12.2`。冻结清单 SHA256 为 `64f6e8d5dbf0c2e1c75053094bf976049f15ba034435f5318502791bc33e2728`。运行前后完整核验 71 个文件及精确目录清单，全部一致；没有导入 live 或旧候选的工具实现。

全部原 129 行结果为 **106P / 0F / 23U**，没有执行后的判定校正或失败重试。

| 范围 | P | F | U |
|---|---:|---:|---:|
| 真实临时进程与文件，27 行 | 27 | 0 | 0 |
| 明确标注合成的协议校验，81 行 | 79 | 0 | 2 |
| 本轮未执行的原生补证，21 行 | 0 | 0 | 21 |
| 合计 | 106 | 0 | 23 |

所有资源变体均实际建立所需的进程/文件前置条件。正常、异常、超时、取消、忽略 SIGTERM 后代、三种崩溃/恢复、实际 release、重复 finish/cleanup、借用保护、错误身份/路径拒绝、并发租约、真实权限拒绝及原始证据保护均符合原判据。未再观察到旧的启动身份不可用或崩溃恢复误拒绝。

动作依赖、callback_dependencies、原始动作绑定、输入/事件/图像 epoch、原子分母、证据类型与责任范围的校验均符合原判据。合成原生格式记录仅获得协议校验信用；没有用其补充 SDK 通过。

23 个 U 保留不变：21 个 N 系列原生变体与 E08 的实际测试数/旧图新鲜性两行。独立 SDK 审查在 `probes/native-review/` 另列，所审原始 SDK 包绑定 candidate-v12.1；其 Android 提供者补证没有自动转成新候选的 SDK 执行。这里没有执行 iOS、OS 设备、物理触摸或完整真实 native final 接受流程。

已读取新公开 `Resources.native_options(platform=None)` 接口文档。此次原 spec 的通用部分使用直接的资源/动作/证据 API，不声称对新增的真实 iOS 资源接入取得了 SDK 证据；平台特定未执行范围继续 U。

前两个旧候选、原 spec、前三轮 run-manifest/非 cache 原始产物，以及已经封存的 SDK 审查和旧 cleanup 记录均核验未改变。前三轮 cache 已按之前授权单独归档清理，详情由旧 cleanup 记录追溯，不把已删除路径声称为仍存在。

本轮在执行前已声明：`run-manifest.json` 的固定产物列表排除可清理的 `cache/`。原 cache 字节会另外逐项哈希、压缩归档并验证，再按授权只删除本轮 cache；原 raw、源码、报告、run-manifest 和主 study/cache 保留。清理清单和归档映射仅写入新的 `probes/native-review/attempt-4-cleanup/`，不改旧 cleanup 记录。

逐行结果和原始证据路径见 [summary.json](./summary.json)，完整工具身份见 `freeze-verification-before.json`、`freeze-verification-after.json` 与逐调用输出。本轮没有业务 PR 质量结论。
