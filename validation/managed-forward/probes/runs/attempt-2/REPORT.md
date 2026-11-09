# 冻结候选独立探针复跑

仅执行 `validation/managed-forward/candidate-v12` 的公开接口。冻结清单原始 SHA256 是 `40959a3f3fddf55e198cc4a15ab37ea70097220d9e968db191b3fd434ca76349`。运行前后完整核验 71 个文件及精确目录清单，全部匹配；没有从 live `native-ui-agent` 导入工具。模块实际路径、逐调用源码摘要、冻结核验及原始输出均已保存。

候选尚未通过整套封存探针：**101P / 3F / 25U**。P 是各行明确范围内的协议结果，合成原生格式样本不取得 SDK、设备或产品行为信用。

| 范围 | P | F | U |
|---|---:|---:|---:|
| 真实临时进程与文件，27 行 | 22 | 3 | 2 |
| 明确标注合成的协议校验，81 行 | 79 | 0 | 2 |
| 本子任务未执行的原生补证，21 行 | 0 | 0 | 21 |
| 合计 | 101 | 3 | 25 |

完整逐行分母与证据路径见 [summary.json](./summary.json)。首次自动记录为 100P/6F/23U；下述前置条件与判据校正单独记录在 [adjudications.json](./adjudications.json)，未删除或覆盖任何原始返回。

## 剩余三个失败

- `R05/SIGKILL-after-acquire`
- `R05/SIGKILL-after-first-release`
- `R05/truncated-final-journal-record`

三个用例均真正启动了本轮进程树，随后只 SIGKILL 本轮管理者，再调用冻结副本的公开 `cleanup`。入口都返回 `Prior process identity changed; no process or resource reclaimed`。完整 10 秒窗口后，本轮任务体和后代仍存活并持续更新心跳；借用哨兵、源码、共享缓存和原始证据保持原样。独立兜底回收在判据与原始快照落盘之后执行，不赋予工具回收通过信用。

`SIGKILL-after-first-release` 实际调用了公开 `release('scratch')`，确认首目录消失，再启动使用第二目录的新进程树。故该失败不来自模拟释放边界。截断 journal 的用例保留了截断前、截断后和备份的原始字节；工具记录 `journal_recovered` 并选中备份 generation，之后仍在相同进程身份检查处中止，不能把它归因为备份恢复没有运行。

这三行具有相同恢复阻断症状，不能计作三个独立产品缺陷。资源工具 SHA256 在所有相关调用前后均为 `13394580bcde4f863c344b1fd684ec27344d593e493a4894e3d097b3ea907ed4`。

## 身份诊断与启动错误

另用一个本轮自建进程进行了只读身份比较，没有增加封存评分行。记录显示，同一 PID、启动时间、进程组和不透明令牌保持不变，但 journal 中的解释器首路径为 `.../usr/bin/python3`，运行稳定后 `ps -ww` 返回 `.../Python.app/Contents/MacOS/Python`。整段身份文本因而不同。结合冻结源码对整段 `ps` 文本的严格相等比较，可以推断这是恢复误拒绝的直接原因；原始全字符串见 `raw/diagnostic-only__launcher-identity-comparison/read-only-identity-comparison.json`。

另外三次实际启动出现 `Owned process start identity unavailable`：R03 忽略 SIGTERM 用例、R06 的初始包装命令、R10 的第二个独立会话。原工具没有保存这些失败时的完整 `ps` 结果，不能把尚未启动的树当成成功回收。

因此 R03 的忽略 SIGTERM 判据与 R10 的两个独立活体会话隔离判据保留 U，未推断取消/隔离失败。R06 的两次公开 cleanup 实际都返回 0、没有 owned leftovers，且保护对象不变；其原始 F 来自验证器额外要求初始包装命令退出 0。该额外条件不在封存的 cleanup 幂等判据中，因此该行按实际两次 cleanup 证据为 P，启动错误仍另列且原始结果保留。

## 本轮已验证的范围

正常返回、非零返回、任务异常、公开 timeout、普通 SIGINT/SIGTERM、同名可执行文件的借用保护均取得实际进程/文件证据。新公开 `finish()` 的重复调用保留原收据和原事件历史；独占租约、已有无主对象、路径替换/符号链接/越界记录、错误 PID/启动身份、真实权限拒绝及保护对象等行按原判据执行。

动作依赖的 34 行协议样本全部符合判据，包括新公开 `callback_dependencies` 对“派发成功”和“回调断言通过”的区分，以及上一轮原始动作替换负例的拒绝。责任与证据范围通过了既有 review/acceptance 校验；组件、host、system 和不明确责任的四行还直接调用了冻结的 `evidence_responsibility`，使用独立批准策略及实际颜色板的自动 F，没有替换工具返回的事实结论。

仍有 23 行原生证据待补：21 个 N 系列原生变体，以及真实测试数/旧图新鲜性两个 E08 变体。本子任务没有调用 SDK、创建/删除原生设备或修改全局设备状态，所有合成原生记录都明确标注其范围。25 个 U 的其余两行就是上文未达到实际启动前置条件的资源变体。

## 完整性

封存 spec 的 SHA256 仍为 `2d4bdc875ae0ae1914992ef409684d03b9ae82aec04005289d5b8a09960eee4e`，其所有固定文件均未改变。attempt-1 的原始清单及 3170 个文件逐一核验未改变。候选文件、live 生产实现、spec 和首轮原始记录均未修改。

所有临时文件位于 attempt-2 cache。最终只对记录过的 PID 加随机令牌和确切 fixture 路径核对，确认没有遗留的匹配探针进程；未进行全局进程清理或设备清理。详见 `post-verdict-fixture-teardown.json`、`freeze-verification-before.json`、`freeze-verification-after.json` 与本轮 `run-manifest.json`。
