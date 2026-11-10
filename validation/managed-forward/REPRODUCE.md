# 离线复核

从仓库根运行，Python 3.11、Pillow 依赖见 native-ui-agent/scripts/requirements.txt。需要完整验证档案；稀疏检出 Skill 不能运行全历史 CI。下面的证据复算不启动 SDK，不操作设备。

```sh
python3 -B -m unittest discover -s native-ui-agent/tests
python3 -B -m unittest discover -s validation/managed-forward -p 'test_measure.py'
python3 -B validation/publications/check_historical_aliases.py
python3 -B validation/managed-forward/verify_probes.py --tracked
python3 -B validation/managed-forward/verify_business.py --tracked --replay
python3 -B validation/managed-forward/build_business_metrics.py --check
```

工具测试会在测试私有临时目录建立真实进程并终止自己登记的进程组；限制进程身份查询的 sandbox 可能需允许此操作。证据复算只读取原记录，不重新执行这些进程。完整 CI 另外运行原历史版本全套校验，旧评分不使用更新后工具；历史入口只允许受控目录中同 SHA 的原始字节别名。

verify_probes.py 检查原 129 行判据、历次候选/失败、最新工具身份、归档路径映射、原生动作/输入/源码/图像、资源记录与有限资格。106P/0F/23U 的真实/合成/未知分母保留。SDK 资格另列，不凭单元测试补齐原生未知。

verify_business.py 检查完整屏障链 tools→design→initial→self-finals→quality→reveal；全部原始 seal、初版双组同字节、截止锁、两次诊断预算、命令源/宿主身份、原资源收尾、独立绑定、最终指标和实际清理。--tracked 检查非 cache 文件已经入 Git；--replay 共重算 18 组：公开原自动结果 6 组，隐藏原双评绑定 12 组。它按原版本在新进程中加载完整工具，把封存 compiled subject 与真实原图重定位到当前检出，不修改原 manifest、预期、单位、阈值、数值事实或原审查。

初始隐藏参考是两组最终源码关闭后采集的共同基准，用于独立归因，不能给任一修复者记额外检出信用。完整 bundle 离线绑定的 v1/v2 接入失败、最后 v3 的原命令与摘要都保留，不再调用 SDK。发布核验开发时的设计 seal schema 和 macOS 大小写 glob 接入问题也单独记录，未修改原 seal 或产品结论。

新 native 运行接入参见 [managed-execution.md](../../native-ui-agent/references/managed-execution.md)。归档里的绝对路径、PID、设备 UUID 是原运行身份，不是可直接移植的配置。当前工作缓存和全部 12 个实验自建设备已退役；重放不要求它们存在。实际缓存清理收据是 [CLEANUP-2.json](CLEANUP-2.json)，此前阶段 CLEANUP.json 不覆盖新阶段。

本轮业务原生全量运行已完成；重新开展实验必须重新批准全新设计、封存工具、按同初版和截止规则执行，不能把本轮已知视觉原因重命名成盲测。范围/许可见 [NOTICE.md](NOTICE.md)。
