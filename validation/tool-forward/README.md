# 通用工具能力改进与新增 UI 盲测

本目录保存新版原生观察能力的前向验证与两组复杂新增组件试验。业务任务为 `ReturnResolutionCard`：调用方控制退款/余额/换货选择、规格、确认、说明、金额、提交与完成状态；同时检查窄屏、长文本、深色、RTL 和放大字体。两组均从固定版本的 Reply / AlertToast 新建源码，不从旧试验复制业务组件。

最终结果在完成独立评分、自查匹配与揭盲后发布。当前文件先记录可复核的方法和复现边界，不把截图采集完成当作验收通过。

## 试验边界

- [预注册协议](PREREGISTRATION.md)先于业务实现；[指标口径](METHODS.md)先于评分结果读取与自查。
- 新工具在协调者读取新业务设计前冻结。独立设计者不读工具、旧缺陷或历史结果；原始设计与从数量出发的前瞻性规模修订都保留。
- 两组使用相同模型配置和时间预算：首版 25 分钟、自查 12 分钟、一次修复 15 分钟。首版允许编译和一次公开示例集成，自查前不得看产品截图。
- 六个初始场景、两个保留场景。双方最终源码均封存后才生成保留场景具体输入。相同验收项不得因结果改变。
- 独立评估者看匿名生产源码和原生证据；不看分组、Skill、自查与修复报告。全部初始评分先于自查，全部最终评分先于发现匹配，匹配先于揭盲。
- 两组业务质量均由同一个新版观察器采集，避免给评分方不同的测量能力。旧工具组另以相同首版源码执行旧采集器；它的自查只获得旧采集证据。该配对用于区分采集能力和实现差异。
- 共享文件系统与可辨识的证据格式只能实现程序性盲法。只有一个新任务、每组一次实现，两个平台相关，不能声称统计显著或普遍的质量/速度因果提升。

每组初始阶段有 **2,209 个原子项**，其中 379 个源码/API 项、1,830 个运行时项；最终有 **2,897 项**，其中相同 379 个源码/API 项、2,518 个运行时项。参数组逐成员计数，缺证据保留未评估。

## 公共修复与工具差异

两个首版公开示例的 iOS 集成都遇到 XCUI 非有限坐标引起的 JSON 序列化异常。原始工具和失败尝试保留。经无业务 UI 的真实原生探针后，两组均应用相同数值传输补丁：无效数值为 null，附路径与原生值诊断，不生成虚假零坐标。它不改变控件选择、交互、滚动、状态或业务逻辑，不能算作新版独有收益。

原版工具保存在 `tool-v2/`、`tool-v3/`；仅加公共传输补丁的实际采集包为 `runtime-tool-v2/`、`runtime-tool-v3/`。[补丁冻结记录](transport-amendment/freeze.json)逐文件列出 SHA。所有未成功的原生尝试和诊断都保留。

新版独有能力包括原生祖先关系支持的实际控件判定、冲突时拒绝猜测、长内容反馈定位、输入/回调绑定的逐状态滚动覆盖，以及类型化原生断言。旧图已充分支持的事实仍获得同等证据信用，不能仅因缺少新 JSON 字段判为未评估。

独立能力试验见 [REPORT](../tool-capabilities/REPORT.md)，保留 6 次真实原生测试、232 张截图与失败对照。根协调者的通用工程记录另存于 `engineering/`，不与新业务质量结果相加冒充独立样本。

## 可观测范围

iOS 是真实 App + XCUITest，记录 AX、屏幕点、截图、实际 XCUI 点击与回调、同进程调用方更新。Android 是持续挂载的 ComposeView + Paparazzi，记录实际语义、TextLayout、触摸边界、ScrollState 和 OnClick。Android 语义动作不等于操作系统物理触摸；本轮 iOS 的 accessibilityActivate 请求实际路由到 XCUI tap，不证明执行了 AX performAction。

SwiftUI 不存在本工具可直接读取的通用运行时字号、padding、颜色树。源码声明不替代运行时值，AX frame 不替代完整物理触摸区域；这些方面若缺少充分的像素或原生证据，保留未评估。被观察器拒绝分发的 disabled 动作也不能作为真实点击后无回调的证明。

业务试验使用公开设计规定的局部 `rr.*` 标识与薄数据桥。通用探针另有按可见 label/role 定位的验证，但本轮业务结果不证明仅凭模糊文字就能定位任意无标识旧项目。向量参考也不是可直接做逐像素回归的原生 golden；模型审图与原生数值测量分别记录证据方法。

长内容采集上限和查找策略在业务试验中冻结。达到上限、覆盖缺口、执行失败与额外耗时保留，不通过降低字号、缩短输入或改验收来获得通过。

因已观察到原生采集和导出成本较大，在任何初始得分读取、自查或最终源码/保留输入披露之前，前瞻性固定了[最终阶段资源排程](resource-amendment-2.json)：两组各两个独立的 iOS 模拟器与干净检出，按相同奇偶场景分配；Android 各一个串行槽。每个场景仍调用原封不动的冻结采集命令，动作顺序、次数和上限不变。最终并行墙钟不能与初始串行墙钟相减后宣称 Skill 提速。

最终输入公开后，排程器将后两个保留场景误写成 `C07/C08`，两组在启动任何 iOS 原生命令前均因名称断言退出；真实冻结名称为 `H01/H02`。原始程序保留，[统一名称兼容修订](operator-case-name-amendment.json)只接受 manifest 中的八个独立名称，并让可携带档案监视器包含 `H*` 目录。`run_final_parallel_v2.py` 继续按同样的字典序奇偶排程，未改输入、工具、动作或上限。这属于公共编排修复。

## 文件与复现

`implementations/{d0,final}/` 保存生产源码变化及逐文件哈希；`evidence/` 保存两组统一测量证据；`paired-evidence/` 保存相同旧组首版源码的旧采集证据；`phase-reports/` 保存自查和修复报告。`harness/` 为冻结的公开 API 薄桥，业务 UI 位于实际生产模块中。

所有断言截图、原始 JSON、原生命令与失败日志进入可携带档案。DerivedData、xcresult 和依赖缓存不入库；自动 XCTest 诊断录像的省略项目保留 SHA、大小和原因，原件仍在本机忽略缓存。它们不替代任何断言截图。

`assessment-ledger.csv` 是逐原子项的紧凑索引，保留判定、原因、方法缺口、证据路径及来源数量。`grade_file` 与 `grade_result_pointer` 指向封存评分中的完整记录，包含全部精确证据、SHA 和字段/像素定位；完整依据保留在原始评分 JSON 中，不在 CSV 重复展开。

不需要 SDK 的完整性检查：

```sh
python3 -m pip install -r native-ui-agent/scripts/requirements.txt
python3 -B -m unittest discover -s native-ui-agent/tests -v
python3 validation/tool-forward/verify_capabilities.py
python3 validation/tool-forward/verify_engineering.py
python3 validation/tool-forward/verify_frozen.py --include-private
python3 validation/tool-forward/metrics.py --self-test
python3 validation/tool-forward/verify_evidence.py
python3 validation/tool-forward/build_summary.py --check
python3 validation/tool-forward/build_tables.py --check
python3 validation/tool-forward/build_failure_index.py
python3 validation/tool-forward/verify_artifacts.py
```

这些命令检查已归档证据与确定性原生事实，**不会重新执行原生 SDK，也不重新做模型视觉评判**。

真实重跑需要 macOS、Xcode/iOS Simulator、Android SDK 和 JDK 21。原环境为 Xcode 27.1 build 27A9275、iOS 26.5 / iPhone 17 Pro 模拟器、JBR 21.0.11，固定上游如下：

| 项目 | 固定提交 |
| --- | --- |
| android/compose-samples（Reply） | `53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79` |
| elai950/AlertToast | `76a1c1793cd3443001c20c6033beb84453b25d9f` |

用 `bootstrap.py --workspace <新目录> --java-home <JDK> --android-sdk <SDK> --submission <封存源码目录>` 创建干净宿主。它从固定上游检出，只加公共测试依赖，再应用所选源码。`harness/capture.py` 和 `run_trial_v2.py` 保存本次实际本机路径；换机器时应按归档命令替换 JDK、SDK、Xcode、模拟器 UUID 等环境路径，并将变更作为环境配置记录，不能声称原封不动的 Linux 原生重放。

直接使用对应冻结包 `scripts/ios_observe.py` 或 `scripts/android_observe.py` 的 CLI 可指定本机路径。输入为所选阶段的封存 fixture/actions，桥为 `harness/ReturnBridge.swift` / `harness/ObserverBridge.kt`。旧 Android 接口为前一版采样器的 factory 适配，保留旧采集策略，不声称前一发行版已经提供通用 CLI。

真机页面集成、旧 OS 运行时和人类金标准不在本轮验证范围内。部署版本检查只说明所用编译器接受指定最低目标，不等同于在相应旧系统上实际运行。
