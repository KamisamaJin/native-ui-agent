# 匿名 common-cause 与发现归因裁定

本裁定在两个独立质量 panel 封存之后进行，仅知道初版为 `candidate-d1cbcd54`。另外两份保持匿名；未读取 condition map、participant 自评分、controller traces、历史研究或非匿名 claim 引用路径。未运行 SDK、修改产品/工具、改变期望/阈值或重评分原始 panel。

## 产品原因匹配

双方共同认可、原始 source 与 native 事实支持 **2 个独立 iOS accessibility/testability 原因**。每项在不同输入、option 和状态中重复出现只计一次。

| 独立原因 | candidate-d1cbcd54（初版） | candidate-2cf4bb56 | candidate-e5677eae |
|---|---|---|---|
| `ios-canvas-child-identity` | true | false | false |
| `ios-option-native-semantics` | true | false | false |

`ios-canvas-child-identity`：初版在未明确 contain 的 VStack 上设置 `listening.canvas`。public/private 原始 ready snapshot 3 的 11 个子元素都暴露为 `listening.canvas`，所需 title/text/switch/action/option 标识缺失。两份最终 source 增加 `.accessibilityElement(children: .contain)`，原始最终 native 树出现一个 canvas 和独立子标识，批准路线中的动作派发成功。证明来自 native 身份事实，不来自源码中写了字符串。

`ios-option-native-semantics`：初版对 option Button 额外使用 `.accessibilityElement(children: .ignore)`。原始 native 树的 role-1 外层拥有 em-dash 标签，内层 role-9 button 没有所需 ID，标签为平台拼接的逗号版本。两份最终 source 删除这一合成层，最终 role-9 option buttons 直接暴露所需 ID、精确 em-dash 标签和选中语义。双方独立确认该问题。

两项分开计数：root canvas containment 与 option wrapper 是不同修正位置，分别约束全体子身份与每个原生 option button 的角色/标签。单独修复任一处不逻辑保证另一项要求成立；相同源码位置造成的跨状态/输入重复表现则合并。没有把不可执行 selector 后的验证/回调检查扩成新的业务原因。

business_behavior、style、api 均无双方共同证实的产品原因。它们的零项是当前证据中的确认数，不能解释为领域已穷尽验证。两份最终版本对这两个已匹配原因没有确认残留或新增回归；完整交付仍受下述 F/U 约束。

## 严格 F、误报与 U

两个 panel 的 source Boolean 判定与 runtime status 一致。visual 选择的帧与理由元数据保留各自原文。没有覆盖它们的原始判定。

| candidate | 每个 panel 的 runtime 总计 P/F/U（public + private、两平台） | 每个 panel 的 source 总计 P/F/U（两个 scope） |
|---|---:|---:|
| candidate-d1cbcd54 | 472 / 4 / 420 | 110 / 0 / 8 |
| candidate-2cf4bb56 | 883 / 0 / 13 | 112 / 0 / 6 |
| candidate-e5677eae | 883 / 0 / 13 | 112 / 0 / 6 |

初版 iOS 的 `validation/error-present`、`started/summary-present` 各在 public/private 一次，共 **4 个唯一原始严格 F**。双方都判为 conditional-presence oracle 的 false alarm：原始 steps 1–10 的 `attempted=false`、`succeeded=false`，截图仍为空编辑，事件修订为 0。不能以未发生的 Start 触发条件要求错误/成功摘要出现。它们保持原始 F，并与两个独立原生可访问性产品原因分开。对这些业务状态的事实仍未裁定，不因此变成业务 pass。双方 product-attributed raw alarms 为 0，未裁定的 raw-F 归因为 0；双方 product extras 并非 0，而是跨 panel 去重后 4 个 scope 表现匹配 2 个原因。

每个 panel 的 source F 和 manual F 都是 0。原始 native automatic 与补充原始 manual/visual 后的 evaluated 计数分别记录在 `raw-status-inventory.json`，没有将两个阶段混合或回写。

两个最终版本每个平台 public runtime 为 224 P / 0 F / 0 U；private 分别为 iOS 217 P / 0 F / 7 U，Android 218 P / 0 F / 6 U。长内容的 U 都是同一 coherent frame 中缺少 unique、fully visible native rectangle 的几何观测边界。可读的滚动拼接画面或 source `.frame(minHeight:)` 不能替代该 native box；缺少这种 box 同样不能证明 control 太小。panel-one 将 5 个 private 几何 extra 归因 collector，panel-two 写 uncertain，两者原始标签均保留，按未确定的 native requirement outcome 处置，没有强制一致。

初版 iOS 的 U 还包括原生 selector、几何、未派发回调和依赖动作的视觉状态；成功 caller replacement 前没有成功置脏，因此 dirty-state reset 未被练习。panel-two 在两个 scope 单列该限制，panel-one 没有对应独立 extra，但原始 dependent visual actuals 同为 null。保持 unresolved，不升级为产品共识，也不以空状态 replacement 证明 reset。

每份 candidate 的 `A-bridge-boundary`、`A-evidence-boundary`、`A-callback-evidence` source U，来自声明 scope 只包括两个 production component，而命题涉及 bridge、review 方法或 observer/预注册策略。它们属于证据/方法边界，不是直接产品缺陷。其他 scope 的桥接源码、native 派发 receipts 可以支持底层命题的有限部分；本裁定不把这些材料补入原 source row，不重评分，不宣称完整 universal obligation 已过。初版额外 `A-identifiers` source U 也保留，独立 native 缺陷在另一个 scope 证实。

因此所有 candidate 的原始 mandatory source-audit U 仍存在，两份最终版本的 private 几何 U 也存在。按预先协议，不能推定完整交付成功。

## 参与者原始发现

只核实 supplied 原始 affirmative product statements；其非匿名 evidence 引用保持引用内容，未打开。历史 request-1/request-2 的中间过程和准确历史复测次数不能由最终匿名 capsule 独立验证，另列 verification limits。

| 匿名最终 candidate | 原始正向 product 陈述数 | 匹配的独立确认原因 | false product claim | 未确定正向 product cause | 已确认初版原因漏检 |
|---|---:|---:|---:|---:|---:|
| candidate-2cf4bb56 | 2 | 2 | 0 | 0 | 0 / 2 |
| candidate-e5677eae | 1（合并陈述） | 2 | 0 | 0 | 0 / 2 |

`candidate-2cf4bb56` 的 `IOS-IDENTIFIERS-D0` 和 `IOS-OPTION-SEMANTICS` 分别匹配两个原因。`candidate-e5677eae` 的 `IOS-AX-IDENTIFIERS` 同时明确陈述 canvas 标识和 option wrapper/native label，因此覆盖两个原因，但始终是一个原始陈述、一个 participant 样本。原因匹配不能制造两个独立样本。

两者都明确把原始未派发后的 post-action F/未采样配置列为限制，没有把自动报警直接当产品发现，也没有声称 computed font/physical hit 或完整交付通过。`candidate-2cf4bb56` 的 request-1 依赖状态历史在允许匿名材料中不可核实，保留为 unverified intermediate history，不据此增减正向 cause 发现。初版没有 supplied participant claim capsule，发现/漏检/FDR 指标为 N/A。

alarm FDR 与 participant claim FDR 的分母不同；classic FPR 缺少 true-negative population，为 N/A。零分母也必须为 N/A，不能导出 100% 或零错误性能。上述 claim 匹配没有把重复 panel、route、option 或截图当独立观察单位。

## 证据与封存

- `causes.json` 是主裁定，包含所有 candidate 的 true/false/null 映射、unresolved、逐 manifestation disposition 和逐 claim mapping。
- `coverage-check.json` 核实 8 条 panel alarm 记录、24 条 extra 记录、40 条 source U 记录全部有明确 disposition；双方所有 product extras 均映射原因，原始 source/manual F 均为 0。
- `raw-status-inventory.json` 保留各 panel 的原始 source/runtime/manual/visual 和原始 automatic 的非通过 ID、原因及计数。
- `evidence-review.json` 记录直接复核的六份 iOS native/source 摘录和四张原始 public iOS 图。PNG 只佐证可见状态；原生身份/角色/标签来自原始 native JSON。没有重新测量 computed font、padding、native geometry 或物理 hit region。
- `input-file-sha256.json` 标记本裁定直接使用的原始输入；两个 panel 的完整 seal 各 80、77 个文件均逐字节哈希验证，无不匹配。
- `timing-start.json`、`timing.json` 是原始时钟记录。instrumented start 在初始文件清单及 protocol/schema/identity 读取后才写入，不能当作完整 author cost。没有伪造未记录的 intake 时间。
- `SEAL.json` 逐文件精确 SHA-256 封存该目录下的交付物；seal 本身不自哈希。封存后不得改写后再将其称为原封存结果。

这是独立 AI 判断，不是 human gold。条件仍未揭示，结论不包含任何 condition 比较或工具方向推断。
