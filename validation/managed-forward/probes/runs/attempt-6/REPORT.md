# candidate-v12.4 原封存 129 行复跑

本轮仅使用冻结 candidate-v12.4，清单 SHA256 为 `7056f1caf253284f3cd920ba6113384061abb359d2025747a0daeac0f35f2e2b`。运行前后完整核验 72 个文件和精确目录清单，全部匹配。与上一候选相比仅 `scripts/native_checks.py` 和 `tests/test_native_checks.py` 的摘要改变。

原始结果：**106P / 0F / 23U**。没有新失败、失败重试、执行后判定校正、SDK 执行或业务用例。

| 范围 | P | F | U |
|---|---:|---:|---:|
| 真实临时进程与文件，27 行 | 27 | 0 | 0 |
| 合成原生格式的协议校验，81 行 | 79 | 0 | 2 |
| 本复跑未执行的原生补证，21 行 | 0 | 0 | 21 |
| 合计 | 106 | 0 | 23 |

资源生命周期、实际派发前置条件、回调依赖、状态/输入/事件/图像绑定、原子分母、证据类型和责任校验继续符合原判据。所有实际资源前置条件均建立；没有把未启动或未执行写成通过。逐行结果与原始证据路径见 [summary.json](./summary.json)。

本次保持原 129 行，没有新增 `python -I`/importlib-only 的隔离加载测试。源码核验确认 legacy 读取器仅在 `guard_protocol==1` 时导入 action_guard，但这里不把主线程新增的单测或旧工程验证结果计成本子任务独立执行的用例。原远端 CI 失败日志/JSON 已只读记录摘要并核验未改变。

此前实际 SDK 包仍分别属于 **v12.1、v12.2、v12.3**；没有为 v12.4 虚构 SDK 执行。旧 SDK 审查及新附录保持原字节，不重算或改写其结论。本轮合成协议 P 不取得原生提供者、iOS、OS 物理触摸或业务 PR 质量信用，23 个原生缺证据行仍 U。

原 spec、旧候选、attempt-1 至 attempt-5 的 run-manifest 与全部非 cache 原始产物、旧失败、SDK 审查和既有清理记录均核验未变。此前 cache 的退休继续由既有归档映射追溯。

本轮执行前已声明 run-manifest 排除 disposable `cache/`。清理在验证该原始清单后进行，先归档 cache 的每个文件并核验原始 SHA，再仅删除 attempt-6/cache。新的归档、映射、进程身份检查及清理清单单列于 `probes/native-review/attempt-6-cleanup/`；raw、源码、原清单和 SDK 证据保持原样。
