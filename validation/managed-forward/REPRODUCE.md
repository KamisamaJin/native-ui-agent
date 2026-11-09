# 离线复核与继续条件

从仓库根运行，Python 3.11 与 Pillow 依赖见 `native-ui-agent/scripts/requirements.txt`。这些命令不启动 SDK，也不删设备。

```sh
python3 -B -m unittest discover -s native-ui-agent/tests
python3 -B -m unittest discover -s validation/managed-forward -p 'test_measure.py'
python3 -B validation/managed-forward/verify_probes.py --tracked
python3 -B validation/publications/routed-v11-replay/verify.py
```

最后一项使用临时历史索引，不更改当前 `.git` 对象或 index，核验旧版本的原始差异与证据。默认工具测试会在测试私有临时目录建立真实进程并终止自己登记的测试进程组；在禁止进程身份查询的 sandbox 中需要允许此项操作。离线探针复核只读取已经保存的原始记录，不重新运行这些进程。

`verify_probes.py` 会验证：

- 原独立 spec 与全部已封存运行的逐行分母、摘要和真实/合成界限；首轮失败不会因最新成功消失。
- 四个候选工具与完整 v11 基线的字节身份；当前发布工具等于最新候选。
- 老 manifest 中已经清理的 cache 文件，仍能通过原路径/归档成员映射和逐文件 SHA 找回。
- 原生包的实际 JUnit、guard 回执、源码、输入、图片与原检查结果；以捕获时附带的工具重算，不借当前实现给旧包加信用。
- 后续取消包的完整 PNG 与已登记进程组的前后采样，以及最新 SDK 流式日志前缀保留。原截断图片仍单独作为不完整证据保留。

新原生运行使用完整的默认入口，参数示例见 [managed-execution.md](../../native-ui-agent/references/managed-execution.md)。`probes/native/prepared*` 中的绝对路径是实际机器上的输入记录，并非可原样移植的用户配置。旧包离线重放只重定位已保存的字节；不更改预期、单位、原始来源和原始实际值。

继续完整业务实验前，应先完成 Xcode 管理员组件设置，并获得 iOS 原生小任务证据；再另建不可覆盖的 release 封存。按 [PROTOCOL.json](PROTOCOL.json) 产生全新独立需求与唯一自然初版，封存后复制到两组。不能用当前中性 Counter 或历史业务题目补成新实验；不能将后续工具修复悄悄加入冻结的某一组。当前没有业务设计、实现或隐藏评估可复算。

原始数据许可与上游授权见 [NOTICE.md](NOTICE.md)。本轮缓存实际清理记录为 `CLEANUP.json`；该文件和清理前后验证是执行结果，不应由用户手工填数。
