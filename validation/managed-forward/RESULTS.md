# v12 阶段报告：默认门控完成，业务配对实验尚未启动

本轮完成了资源管理、动作前置条件和证据责任校验的实际默认链路，并做了独立中性任务与真实 Android SDK 验证。**没有完成用户要求的全新复杂业务双组盲测。** iOS 环境仍被 Xcode 首次组件安装阻断，所有业务质量、交付率和成本比较保留 N/A。

## 实际代码行为

| 能力 | 默认执行位置 | 已建立的边界 |
| --- | --- | --- |
| 资源生命周期 | `feedback_loop.run_cycle → Resources → execution_plan.run_execution` | 正向所有权、进程启动握手、租约、双份持久日志、磁盘预算、超时/信号/崩溃恢复；先收尾再发布 cycle。无法证明归属时保留并拒绝接受。 |
| 动作前置条件 | `compile_actions → 两端原生模板 → verify_observation` | 前序成功派发、显式独立分支、原生目标唯一且启用、可选当前属性与回调依赖；原始动作与执行回执精确绑定，不能仅信任 producer 的 success 字段。 |
| 证据责任 | `compile_contract → subject/type preflight → source/image/native admission` | 责任声明取自独立设计锁；桥接不能冒充生产组件、静态源码不能冒充运行时样式或宿主行为。原始实际值与文件/图像绑定，缺证据保留 U。类型兼容不等于事实为真或产品责任已确认。 |
| 失败产物 | SDK 直接向每次运行的日志文件写入 | 中途取消保留已产生的真实构建日志；错误、清理错误、部分图和未接受状态分别保存。 |

详见 [默认配置与接口](../../native-ui-agent/references/managed-execution.md)。这不是通用的 SwiftUI computed-style 接口；Android 此处是 Paparazzi/layoutlib 与 Compose 语义动作，不能外推 OS 物理点击、导航或生命周期。

## 独立小任务与原始失败

独立制定者先封存 [129 行判据](probes/spec/README.md)，没有读取历史业务题目。后续只在新目录复跑，原 spec、判据、失败输出不重写。工具作者与验证者是独立上下文的 AI，并非人类金标准，也不是防恶意访问的安全隔离。

| 运行 | 待测版本 | P | F | U | 结果范围 |
| --- | --- | ---: | ---: | ---: | --- |
| attempt-1 | 开发中工具 | 92 | 6 | 31 | 首轮工程结果，含后代回收、坏日志恢复与动作替换校验失败。 |
| attempt-2 | candidate-v12 | 101 | 3 | 25 | 冻结复跑暴露启动时身份不可用、Python 路径呈现变化引起的恢复误拒绝。 |
| attempt-3 | candidate-v12.1 | 106 | 0 | 23 | 原 spec 通用行为通过；保留原生补证分母。 |
| attempt-4 | candidate-v12.2 | 106 | 0 | 23 | 平台选项先校验、独立 iOS 桥接的平台传递修正后复跑。 |
| attempt-5 | candidate-v12.3 | 106 | 0 | 23 | SDK 日志改为运行中落盘后，仍按相同原 spec 复跑；未做执行后判定校正。 |
| attempt-6 | candidate-v12.4 | 106 | 0 | 23 | 修复远端 CI 暴露的旧包单文件加载依赖回归后，原 spec 复跑及冻结后验均通过。 |

最新候选及后续原 spec 复跑见 [LATEST-ENGINEERING.json](LATEST-ENGINEERING.json)。106P 中 **27 项是真实临时进程/文件，79 项是合成协议检查**；23U 不能从单元测试或成功 CLI 推导为原生通过。原生补证另外列示，不覆盖这张表。首轮 raw 与 adjudication 也都保留，不能将所有原始拒绝都归为产品缺陷。

通用修复依据是独立中性任务：真实忽略 SIGTERM 的后代、被中断写入的资源日志、被替换的原始动作、同一进程合法的解释器路径变化、非法平台选项与中途 SDK 日志丢失。没有使用下一轮业务需求或向产品注入缺陷来获得分母。v12.3 的 164 项工具测试通过且前后源码摘要一致，见 [原始执行记录](operators/engineering-1794232500545834000.json) 及同名 `.log`；远端 CI 之后新增的隔离解释器回归使当前工具测试增至 165 项。

## 真实 Android 补证

使用固定 Reply/AlertToast 宿主与单独的中性 Counter 组件。原生桥接直接调用生产 Counter，输入、源码、动作、事件 epoch、原图、JUnit 和执行工具源码都随包留存。

| 用例 | 原始事实 | 可支持的结论 |
| --- | --- | --- |
| 正常动作、回调依赖与调用方更新 | 1 个真实 JUnit test；6P/0F/0U，另有 2 项 source-only 审查 | 当前中性组件配置内的 native/source 门控关闭，非业务 PR 完整交付。 |
| 禁用、缺失、歧义目标与依赖分支 | 8P/0F/6U；独立分支仍采集 | 六个因果状态未知符合事先判据，不算六个产品失败或六次修复。 |
| bridge subject 错指组件文件 | SDK 前阻断，无原生执行 | 默认责任/主体校验已执行。 |
| Gradle NO-SOURCE、命令退出 0 | 测试数 0、observer 非零、无 observation | 不将构建命令成功误判为原生测试成功；原宿主文件已恢复且摘要一致。 |
| 第一次 SDK SIGTERM | PNG 截断、没有取消后进程组原始存活样本 | **仅部分支持**，失败前置条件保留，不称为完整首帧或完整回收。 |
| 后续独立 SIGTERM 资格验证 | 完整解码首帧、登记 SDK 进程组取消前存活，之后采样为空；源不变、无 accepted cycle | 支持该次 Android SDK **进程组**回收；不证明逃逸 daemon、全 OS 进程树或 iOS 设备租约。 |
| 最新 v12.3 SDK SIGTERM | 原始构建日志前缀 2412 字节完整保留，取消前后日志摘要留存 | 新日志落盘修复获得真实 SDK 补证。 |

原始独立 SDK 审查为 [6 行 Android 范围关闭、2 行部分支持、15 行仍 U](probes/native-review/REPORT.md)，新包审查单独保存在 [addendum-v12.3](probes/native-review/addendum-v12.3)。新候选原生包在 [qualification-v12.3](evidence/qualification-v12.3/SEAL.json)，原取消包、旧候选与后续补证均分开留存。被归档的旧 per-run cache 用原始 manifest 加归档成员映射追溯，没有改写 manifest 以掩盖清理。

一次最新中性 Android 正例的**整个命令墙钟为 9.304 秒**；外部每秒采样，观测峰值 **132,231,168 字节（126.11 MiB）**，组内含指定工作目录、构建目录、资源根和该次输出，无预算超限。见 [实际命令](operators/v12.3-positive-meter.command.json)、[磁盘采样](operators/v12.3-positive-meter.summary.json)。这是暖共享 SDK 环境中的一次中性资格测试，没有对照组；不是单 PR 耗时，也不证明提速。目录 allocated bytes 不是 APFS 精确物理占用，采样峰值也不是连续瞬时峰值；全局 SDK/Gradle 缓存未计作该组件独占。

## 业务盲测与阻塞

[实验协议](PROTOCOL.json) 已固定：两组完整冻结工具、全新独立设计、一次自然编写初版、同字节双组复制、独立 D0 计费、两组最终源/自验封存后才隐藏评估、匿名独立判断与共因匹配封存后揭盲。不注入缺陷；基础设施修复另列，未接受的端点不能计成功交付节省。

当前 **0 份业务初始 PR、0 组修复运行**，业务设计尚未派发。既有的小任务不充当复杂业务实验。Xcode 27.2 许可检查已通过，但首次组件检查仍返回 69；已安装 CoreSimulator 1174.9.2，而新 simctl 要求 1174.21。组件初始化等待，非交互管理员操作需要密码，已请求用户在 Xcode 完成安装。没有创建新 iOS 模拟器，没有删除或停止用户共享设备/服务。[原诊断](operators/ios-prerequisite.json) 与 [最新明确命令结果](operators/ios-prerequisite-recheck.json) 均保留。

| 用户要求的配对结果 | v11 基线 | v12 默认门控 |
| --- | --- | --- |
| 最终真实漏检 / 修复率 | N/A，未运行 | N/A，未运行 |
| 新增确认回归 | N/A，未运行 | N/A，未运行 |
| 完整交付率 | N/A，0 个尝试 | N/A，0 个尝试 |
| 单 PR 端到端耗时 / 成功交付成本 | N/A | N/A |
| 峰值磁盘占用比较 | N/A | N/A |

这些 N/A 不是零缺陷、零成本或两组打平。目前的有效结论是默认保护机制获得了限定范围内的执行证据，**整体 native PR 质量和成功交付成本优势仍未经本轮验证**。

## 证据、清理和发布

所有冻结工具、原始失败、原生包、判据与归档摘要可离线重放。`verify_probes.py` 校验封存身份、实际图片/输入/源码、原检查结果和资源收尾；不会在 CI 启动模拟器或对外清理资源。此前 v11 的验证改用固定历史源码视图，不用 v12 的变化重写旧成绩。

首次[远端 CI](https://github.com/KamisamaJin/native-ui-agent/actions/runs/42633193301)的 164 项工具测试通过，但旧 `tool-forward/verify_engineering.py` 用 `importlib` 单文件加载 `native_checks` 时，因新增无条件导入 `action_guard` 而失败。组合测试的 `sys.path` 修改掩盖了这个**实际向后兼容回归**。v12.4 将该依赖延后到 protocol-1 观测包才加载；守卫协议的校验逻辑没有放宽。新增 `python -I` 隔离进程回归后，本地 165 项及原工程验证通过。见 [完整失败日志与分类](operators/ci-42633193301.json) 和新冻结候选。已有 SDK 包仍是各自 v12.1/v12.2/v12.3 执行，不给 v12.4 虚构一次新 SDK 信用；这些均在业务设计开始前发生。

第二次[远端 CI](https://github.com/KamisamaJin/native-ui-agent/actions/runs/42636803387)通过当前工具和原生证据检查，以及截至 v8 的历史校验，随后在 v9 历史重放因 `THIRD_PARTY_NOTICES.md` 摘要不符失败：历史入口读取了更新后的活文档。修复保留原摘要，只有活文件别名不匹配时才从受控 `historical-root` 目录选取**完全相同 SHA256 的原字节**；显式冻结基线错误仍拒绝。原 v9/v10 入口本身也保存为旧版本快照，确保 v11 的原清单仍可重放。[完整失败日志与分类](operators/ci-42636803387.json) 保留。

修复后 v9/v10/v11 均已本地完整重放通过，见 `operators/history-v*-alias-fix-2/` 下的原始日志、源指纹与资源收据；没有 SDK 执行或新业务评分。增加了 3 项历史来源控制，并将 276 个别名的摘要预检查前置到耗时评分之前；预检查不替代完整数据与评分重放。开发中发生的临时路径规范化、目录符号链接处理，以及受管临时根含 `cache` 导致旧过滤器误排除等本地失败也单独保留；未改旧过滤器、原评分或断言阈值。各次重放使用受管进程组和临时目录，结束后已清理；源指纹前后相同。

本地随后按工作流顺序执行余下离线检查，前 14 项通过；旧 `dispatch-forward/verify_evaluation.py` 的全量历史图像评分在本地驱动的 300 秒上限终止，未完成部分不算通过，也不属于产品缺陷或原生采集失败。[逐命令记录与原日志](operators/local-ci-after-compatibility/commands.json)、[超时记录](operators/local-ci-after-compatibility/timeout.json) 保留；没有调整评分预期、阈值或原实验数据。

主项目专用工作缓存已在闭包核验后清理：**4048 个文件、500,346,880 allocated bytes（477.17 MiB）**，主 cache 目录已不存在。[CLEANUP.json](CLEANUP.json) 保留实际前后统计与证据清单；独立探针自己的 per-run cache 归档另见各轮记录。没有创建新 iOS 模拟器，也没有清理用户设备、共享 SDK 缓存、旧证据或 Git 历史。

发布核验扩展时还出现过一次局部 Path 变量遮蔽 helper 的异常，已修复，失败源码与原始退出记录保存在 [operators/verifier-development-failure.json](operators/verifier-development-failure.json)，不混入工具探针或产品结果。宿主归档曾包含 bootstrap 生成的 JDK 依赖 jar，发布前已排除并保留原清单、摘要与原因，见 [scope-amendment.json](evidence/host-setup/scope-amendment.json)；不分发 SDK 二进制。复核见 [REPRODUCE.md](REPRODUCE.md)。
