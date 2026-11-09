# 原始 Android SDK 补证独立审查

本审查另列于前三轮之外，保留 attempt-3 原始 **106P/0F/23U**。没有重写原 spec、旧结果、冻结候选或生产实现，也不形成业务 PR 质量结论。所有逐行判断都在 [decisions.json](./decisions.json) 引用原始绝对路径、完整 SHA256 和对应步骤；原始包清单与摘要见 [readset.json](./readset.json)。

对原 23 个 U 行的补证结论是：**6 行可在 Android 提供者范围内关闭，2 行部分支持，15 行仍 U**。这些不是新的跨平台总通过数。

## 原始包核验

六个提供包的 portable 摘要均与实际字节匹配，prepared/prepared-positive 独立契约的 pre-SDK seal 均匹配。正、负 SDK 包携带的 tool-runtime 全部与 candidate-v12.1 冻结内容一致；这批 SDK 证据绑定该候选，不能自动当作其他候选的新 SDK 执行。

两份实际 JUnit 均发现并执行 `org.nativeobserver.NativeObserverTest.capture`，各 1 test、0 skipped、0 failures、0 errors。日志可见 Paparazzi/layoutlib。桥接源码直接导入并调用主源码 `NeutralCounter(seed, onEvent)`；生产快照 SHA 与 capture 的前后源码指纹及原生 manifest 一致，未发现近似 UI 替身。

我用冻结校验器从原 observation、独立 lock/plan、原 fixtures 和原图重新计算：正例 **6P/0F/0U**，负例 **8P/0F/6U**，与原 automatic 的逐项状态一致。环境编码经重算均为 P。390dp 请求、实际 1072×1650 原生像素和 389.81818×600dp 的 provider 编码一致；PNG 为 649×1000，不从其像素推断精确字号、内部 padding 或物理触摸区域。核验与重算完整结果见 [integrity.json](./integrity.json)、[recomputed-checks.json](./recomputed-checks.json) 和 [source-crosschecks.json](./source-crosschecks.json)。

已查看全部三种唯一、可完整解码的原图内容，29 张成功包 PNG 按字节归并为 Tally 0、1、8 三种状态。每帧输入/事件绑定仍逐帧核对，没有因图片字节相同而合并状态信用。

## 可关闭的六行，限定 Android Paparazzi/Compose 语义路线

- `N03/real-successful-dispatch`：实际唯一启用按钮的 `compose_onclick` 成功，回调一次 increment，同绑定帧从 Tally 0 变成 Tally 1。
- `N03/real-disabled`：禁用按钮没有实际派发或事件；依赖步骤被阻断，因果状态保留 U。
- `N03/real-missing`：目标匹配数为零，没有派发；后续依赖步骤没有获得动作或因果状态信用。它不是全 App 不存在该目标的证明。
- `N03/real-ambiguous`：一个语义容器含两个实际 OnClick 控件，工具没有取第一个点击；依赖步骤阻断，独立分支继续。
- `N03/real-caller-update`：输入索引 0→1、输入哈希改变、事件版本保持，单个持续附着的 ComposeView 显示 Tally 8。`instance` 是该运行会话 UUID，不能冒充 OS App PID。
- `E08/zero-native-tests`：实际 Gradle `neutralNoTests` 为 NO-SOURCE 且命令退出 0，但 observer 返回 error/退出 1、test_count 0，无 observation；没有把 Gradle 成功当成原生测试通过。

正例还实际验证了声明的 callback_dependencies。负例的六个未建立因果状态没有被空回调区间或已有匹配标签改成 P/F；原 `invalid_or_incomplete_capture` 和 `not_accepted` 是该协议负例的预期范围，不是产品缺陷。

## 部分支持的两行

`N04/component-native-evidence` 支持真实组件的当前标签、启用状态、回调和调用方更新事实。源实际值与 `remember(seed)`、Count handler、桥接转发相符；source 证据保持 source 范围。错误 bridge subject 指向组件源码时，实际 responsibility-negative 在 SDK 前阻断。提供包没有完整的 host/system 视觉分层契约，也没有 computed font/padding 测量，因此不关闭更广泛的责任/样式声明。

`N05/SDK-SIGTERM` 支持实际 Android SDK 运行中 signal 15 取消、primary InterruptedError 保留、service-error 为 not_accepted、没有 cycle.json、资源收据中 owned leftovers 为空及保留部分产物。但没有取消后 PID/进程组的原始存活采样，不能独立确认所有 native 子进程或单次 Gradle daemon 的有界回收。

该取消包还存在一个明确的观察限制：其 `000-state_initial_0.png`（SHA256 `3260f5df71a53d8ea4490cdcd9e0f7486fe260b30205a4331633940b00dcb2cf`）只有可读取的 PNG 头，完整 verify/load 均报 **OSError: Truncated File Read**。不能把“文件已出现”当成“完整首帧已取得”。这是一份中断时保留的部分产物，不据此制造产品问题。详见 [image-audit.json](./image-audit.json)。

## 仍 U 的范围

没有 OS 设备启动前态、借用设备保护/恢复或活体设备租约证据，N01/N02 的八行仍 U。没有真实失败的调用方更新、host/system 分层原生审查、已请求但不支持的有效样式属性、SDK SIGINT、manager SIGKILL 后 SDK reconcile，以及真实旧图复制/回放负例，相关七行也仍 U。逐行理由和原始引用均保留在 decisions.json。

Paparazzi 是这里实际运行的 JVM/layoutlib 渲染提供者；原始模板直接调用 Compose Semantics OnClick，且 `showSystemUi=false`，明确无 Activity/navigation/lifecycle 信用。它不能证明 OS 物理触摸、OS 手势、设备生命周期或 iOS。提供的 Swift 源码和 iOS 契约没有相应 XCUITest/原生执行产物。

## 三轮 cache 清理与原始证据保留

核验发现原 run-manifest 实际仍包含 3248 个 cache 文件条目，与“已排除”的描述不一致。我没有重写原 manifest：先逐项验证所有原始摘要，再把三个 per-run cache 压缩归档并核验归档内每个文件 SHA，随后仅删除这三个 cache 目录。归档与原路径/成员映射保存在本审查目录。

原 manifest 文件、raw、非 cache 源码、spec、冻结目录、主 `validation/managed-forward/cache` 及所有 SDK 补证包均保留。旧 manifest 的 cache 路径会因本次授权清理而不再存在，应通过归档和删除记录追溯；不能再声称所有旧路径仍存在。实际清理与后验核验见 [cleanup.json](./cleanup.json)、[cache-archive-index.json](./cache-archive-index.json) 和 [pre-cleanup-integrity.json](./pre-cleanup-integrity.json)。残留进程仅按此前记录的 PID、创建时间、进程组、随机令牌和确切来源路径核对，不按名称或全局扫描回收。
