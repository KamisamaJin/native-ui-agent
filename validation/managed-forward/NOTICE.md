# 范围与许可

本目录的工具、Counter、独立协议判据、AI 审查和研究脚本是原仓库 MIT 许可下的原始新增材料，不是 Apple、Android 或相关开源项目的官方测试套件。

Reply 宿主固定 android/compose-samples `53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79`，Apache-2.0；AlertToast 宿主固定 elai950/AlertToast `76a1c1793cd3443001c20c6033beb84453b25d9f`，MIT。原始上游许可保存在 [evidence/probes/licenses](evidence/probes/licenses)，固定准备身份见 [upstreams.json](evidence/probes/upstreams.json)。截图及原生报告是集成记录，不改变上游源码、资产、依赖的许可。

不分发 Xcode、模拟器运行时、SDK、依赖缓存或完整工作 checkout。原始失败收据中的绝对路径、PID、开始时间、设备及工具版本用于审计，不证明这些临时对象现在仍然存在。压缩的中性协议 cache 只保留独立探针产生的小文件与记录，不含 SDK 镜像或构建缓存。

独立审查由不同上下文的 AI 完成，封存只固定字节与流程，不能证明需求完备或等同人类金标准。Android 结果限于 Paparazzi/layoutlib/Compose 语义行为；没有 iOS 实跑或完整业务双组结果。
