# 新增 Android 提供者资格证据附录

本附录保留原 `native-review/REPORT.md`、其截断首帧的部分支持结论、前三轮结果及所有旧清理记录。仅审查新增 v12.2/v12.3 正例与取消包，不设计业务任务，也不作业务 PR 质量结论。所有判断的原始绝对路径、SHA256、工具版本及重算值见 [decisions.json](./decisions.json)、[readset.json](./readset.json) 和 [raw-integrity.json](./raw-integrity.json)。

## 版本与完整性

四个包的 portable 摘要均匹配实际字节；两个新增 SEAL 的所有条目也匹配。各包的完整运行时工具集合分别精确匹配它所声明的 candidate-v12.2 或 candidate-v12.3，而不是用最新候选身份替换旧 SDK 执行。运行时闭包与生产 Counter 快照交叉核验见 [runtime-closure.json](./runtime-closure.json)。

独立重算仅导入冻结 candidate-v12.3 的校验器，不启动 SDK、不依赖主 study/cache 的活文件。原捕获的版本身份仍按实际工具快照记录。

## 新正例

v12.2 和 v12.3 均实际发现并执行 `org.nativeobserver.NativeObserverTest.capture`：各一项测试，0 skipped/failed/error。由独立锁、原 fixtures/bridge、实际 observation、原图重建后，两包均为 **6P/0F/0U**，环境均为 P，动作/回调门控与原 automatic 一致。

各包的源码前后指纹一致；组件 SHA 与封存的生产 Counter 快照及原生 manifest 一致；final 资源收据没有 cleanup error 或 owned leftovers；accepted cycle 钉住了实际完成后的 resources.json。这里的 accepted 仅是中性计数器批准契约的状态。

已查看新 v12.3 包中 Tally 1、调用方替换后的 Tally 8，以及取消包的完整 Tally 0 首帧。图片字节与对应版本的 native manifest/记录一致。原生方法仍是 Paparazzi JVM/layoutlib 中的 Compose semantic OnClick 与连续 ComposeView 输入更新，不提供 OS 物理触摸、Activity 生命周期或 iOS 信用。

## 新取消证据关闭了原先缺失的精确组范围

关联的独立记录位于 `probes/native/cancel-sdk-v2/result.json` 和 `probes/native/cancel-sdk-v3/result.json`，不在 portable 子包中；本附录将它们的完整摘要纳入 readset，并逐项与包内图像、lease/event/resource/error 字节交叉核验，没有使用记录内的 PASS 字段作为判据。

两个新取消测试均在完整可解码的首帧之后实际 SIGTERM：首帧 SHA256 是 `4237b1945ac0cc9111927dd9db5cba4208b8b4fa962caf258157e08b13c0111e`，实际解码尺寸 649×1000。取消前都记录了同一 owned PGID 中三个活体成员，包括 Python launcher、Android observer 和 Java 进程。leader 的 PID、创建时间、PGID、命令摘要及随机令牌与持久 lease 一致。

取消后该确切组为空：v12.2 首个空组采样距信号约 **0.212 秒**，v12.3 约 **0.237 秒**，均在原 10 秒界限内。两者均非零退出，保留 primary InterruptedError/signal15、not_accepted service-error，没有发布 cycle，收据无 owned leftovers/cleanup error，记录的源码哈希不变，保留测试目录已移除。

因此 `N05/SDK-SIGTERM` 在这两个版本的**记录过的 Android owned process group 范围内可关闭**，此前“缺少取消后精确组采样”的证据缺口由新包补足。它不证明逃逸到其他组的 daemon、OS 设备、SIGINT、manager SIGKILL 或 iOS。原 v1 包仍保留原先的部分支持判断。

## v12.3 的日志耐久性

已读 `qualify_cancel.py`：它在完整解码帧且 owned SDK 组存活时，直接保存当时 `capture/native/test.log` 的真实前缀，随后只向自己启动的外层控制器发送 SIGTERM，不替待测工具做进程组清理。

我独立比较了 `pre-cancel-sdk-prefix.log` 与封存的取消后 test.log：取消前已有 **2412 字节**，SHA256 `b6018dfd724c0d55b8ed873b23cde1b9db704262d69606632e892d984e1b0081`；取消后 2412 字节全部保留，原始前缀逐字节匹配。这是实际 Android SDK 日志在运行中已落盘、取消后仍保留的证据，不是源码声明或重建的错误文案。

v12.3 取消包另外保留了一张后续中断帧 `002-state_front_0.png`，完整解码报 Truncated File Read。它不影响此前两张完整帧已取得的事实，也没有获得完整图像/状态通过信用。该部分产物及旧 v1 截断帧均未修补或删除。

## 保留的边界

本附录没有新的 iOS SDK 产物，也没有 SIGINT 或 iOS adapter 中断 manifest 的实际提供者测试。相关源码/通用测试改动不能补出这些 SDK 信用。未执行的 OS 设备租约、host/system 层、有效字体/padding、旧图回放及更广进程生命周期范围继续按原审查保留。

attempt-5 的原 129 行通用重跑另存，不能把本附录实际 SDK 结论改写成该重跑的合成/通用行信用。原始 SDK 审查和新附录按各自版本与范围并列保存。
