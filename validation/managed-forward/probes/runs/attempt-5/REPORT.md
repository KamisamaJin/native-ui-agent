# candidate-v12.3 原封存 129 行复跑

仅使用冻结 candidate-v12.3，清单 SHA256 `13e3b62a8693a87db0e2e127af89053da90ad01d2c228ee1fdcca2fd2fa44ac7`。运行前后完整核验 72 个文件和精确目录清单，全部匹配。没有导入 live 或旧候选实现，没有新业务设计、SDK 重跑或业务 PR 质量判断。

原始结果：**106P / 0F / 23U**，没有新失败、失败重试或执行后判定校正。

| 范围 | P | F | U |
|---|---:|---:|---:|
| 真实临时进程与文件，27 行 | 27 | 0 | 0 |
| 合成原生格式的协议校验，81 行 | 79 | 0 | 2 |
| 本复跑未执行的原生补证，21 行 | 0 | 0 | 21 |
| 合计 | 106 | 0 | 23 |

真实资源用例全部建立了各自前置条件。正常结束、非零/异常退出、timeout、SIGINT/SIGTERM、忽略 SIGTERM 的后代、三种崩溃恢复、release、重复 finish/cleanup、并发租约、错误身份/路径拒绝、真实权限拒绝与借用/源码/缓存/证据保护均符合原判据。未观察到旧的启动身份不可用或崩溃恢复误拒绝。

动作、原始 action 身份、callback_dependencies、输入/事件/图像绑定、原子分母和证据责任协议均符合原判据。P 仅限各行声明范围；合成回执不获得 SDK 或 OS 信用。全部 129 行和原始证据路径见 [summary.json](./summary.json)。

实际 Android 提供者证据由新的 `probes/native-review/addendum-v12.3/` 独立复核：v12.2/v12.3 各自正例及取消资格按真实版本并列保存，未改写旧 SDK 审查，也未混入本次通用计数。iOS、OS 设备、物理触摸、逃逸 daemon、SDK SIGINT 等缺证据范围未被推断通过。

新日志流式落盘及中断诊断的实际 Android 范围见附录中的取消前后原始日志前缀/进程组检查；iOS 中断 manifest 的源码变化没有获得实际 iOS SDK 信用。

旧候选、原 spec、attempt-1 至 attempt-4 的 run-manifest 和全部非 cache 原始产物、旧 SDK 审查及旧清理记录均核验未改变。既有 cache 退休由各自的归档/清理记录追溯，没有声称已退休的路径仍存在。

本轮执行前已声明 run-manifest 排除 disposable `cache/`。清理只在验证该原始清单后执行，先归档全部 cache 字节并逐项核验，再删除本轮 cache。归档映射和清理清单仅写入新的 `probes/native-review/addendum-v12.3/attempt-5-cleanup/`。raw、源码、报告、原始清单和所有 SDK 证据保持原样。
