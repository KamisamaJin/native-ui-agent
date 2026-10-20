# 复现与证据范围

SDK-free 校验可在检出仓库后执行：

```sh
python3 -m pip install -r native-ui-agent/scripts/requirements.txt
python3 -B -m unittest discover -s native-ui-agent/tests -v
python3 -B validation/contract-forward/verify_tools.py
python3 -B validation/contract-forward/verify_generic.py
python3 -B -m unittest discover -s validation/contract-forward/design/private -p 'test_*.py'
python3 -B validation/contract-forward/verify_trial.py
python3 -B validation/contract-forward/verify_evaluation.py
python3 -B validation/contract-forward/costs.py
python3 -B validation/contract-forward/expectation_audit.py
python3 -B validation/contract-forward/failure_index.py
python3 -B validation/contract-forward/metrics.py
python3 -B validation/contract-forward/build_tables.py
python3 -B validation/contract-forward/build_gallery.py
python3 -B validation/contract-forward/artifacts.py
```

这些命令重放确定性校验、冻结评分、哈希和统计，不能把 AI 视觉/API 审查变成人类金标准，也不代表所有组件测试通过。预期被篡改的负例应被拒绝；已记录的原生失败是被验证的数据，不是需要偷偷消除的 CI 错误。

原生重跑需要 macOS、已完成首次设置的 Xcode/iOS Simulator、JDK、Android SDK，以及可解析上游依赖的网络。实际版本与完整 argv/log 保存于 `operators/`、各语料 `*-command.json` 和 `manifest.json`。检查点固定 Reply `53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79`、AlertToast `76a1c1793cd3443001c20c6033beb84453b25d9f`。

`experiment.py restore` 只恢复本试验 cache 中的衍生工作区。`experiment.py collect --help` 提供新的输出/归档目录；不要覆盖任何已封存目录。`--width-compat` 选择单独保存的共同 iOS frontend 副本，Android 仍是对应冻结版本。按已记录 argv 更新本机 SDK/模拟器路径后运行；新运行的数据与当前发布的历史分开存放。完整流程和阶段限制在 [OPERATIONS.md](OPERATIONS.md) 与 [预注册](PREREGISTRATION.md)。

源码 capsule、原始 fixture/action、编译宿主、PNG、AX/Compose 语义树、派发和回调收据均归档。DerivedData、xcresult、SDK 缓存和自动系统诊断视频未进入 Git；portable-scope.json 保存视频哈希、字节数和排除原因，失败日志及断言截图保留。每个 portable-sha256.json 对应具体归档，不被后续修复覆盖。

设计、匿名评分、原始自查、修复和揭盲分别封存。两组均使用 Skill，比较 v5/v6；一个任务、共享机器和可识别格式，只能称程序性盲测，不能声称安全隔离或统计显著。生产模块中的新组件由薄宿主调用；没有覆盖原 App 的完整导航、后端或任意旧工程的自动无接入测试。

Android 本轮使用 Reply 的 Paparazzi/Layoutlib + Compose JVM 宿主和语义 OnClick，iOS 使用真正 Simulator App + XCUITest。两者都调用生产模块，但 Android 数据不证明操作系统物理触摸/设备集成。
