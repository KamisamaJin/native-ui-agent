# 独立设计契约判断

批准本轮封存的 public / private MenuChangeReviewPanel 需求与测试契约进入实现。未发现设计期阻塞错误。批准对象仅为两个原始 scope seal 所绑定的设计字节；这不是产品、SDK 编译、原生采集、像素测量或图像验收通过。

两 scope 的 seal 文件字节、canonical seal、design lock、全文件清单及 INDEPENDENCE 文件映射一致。审查前后的全部设计文件身份一致。INDEPENDENCE 的历史独立性是作者的原始声明，哈希不能反向证明其过去读过什么；本审查者没有读取历史业务、实验结果、产品实现或截图，也没有修改输入。作者 scope 内的 approval.json 仍是 awaiting_independent_design_review；本目录 approval.json 才是此次独立原始判断。

公开规则可独立推导两条连续路径。公开余额依次为无选项、1200、2300、1400、1400、100、−2600、−2600 分；私有为无选项、−1225、−2200、−2850、−2850、无选项、−1625、−1625 分。公开修订保留 roast、将 13 夹到 12 并保留正信用；私有修订使 chickpea 不可用，清选但保留 8 份、撤销零信用，再选择 aubergine 夹到 7。两者都清 acceptance/sent。发送事件均使用当前 request/revision/option/count/credit/带符号余额；修订事件区间为空。独立推导逐项吻合 reference.expected。

public/private 的通用 README 规则、API、规则集合、布局/字体/色板、定性问题、责任、路由和桥接相同。私有只改变有效调用者数据、动作和环境，没有新增秘密产品要求。所选状态不是全分支或笛卡尔积覆盖；同快照重组、不同 requestID 重置和未观察编辑区间的回调静默等仍须依据公开规则审查源码，不能获得额外原生检测信用。

独立重算四份计划均为 39 × 8 = 312 个格：303 条适用断言、9 个有明确原因的 N/A。N/A 仅分离初始 checkpoint、原生活化事件和 caller-update 事件的不同区间。所有适用规则、必需 ID、绑定、typed source datum、目标及生成值一致；没有未拥有断言。29 个 control 原子、1 个实际控制框高度原子、2 种事件原子和 7 个 manual 原子没有混为同一种证据。

17 项必需 source claim 和独立 source_obligation_routes/routes.reason 关联完整，39 项 native/image responsibility 与规则逐一相容。这里没有运行冻结 router 的 source 路由，也不把文字关联当成 source review。后续默认 responsibility gate 仍须将 component/bridge subject 绑定实际文件并取得独立、当前、带行号的源码观察。component.api 的兼容性源码判断不能单独证明 SDK 实际成功编译。

布局的 pt/dp、字体的 iOS 基础 pt / Android sp、weight 和双主题 ARGB 与公开表一致。精确字体/间距/色板是源码义务；没有把源码声明当作 SwiftUI computedStyle。实际字体层级、标题完整换行、选项描述无裁切、余额无重叠分别是四个单一方面的图像命题。52 pt/dp 规则明确测量实际 send accessibility/control box，既不推断 padding，也不证明物理触摸区域。结构 SVG 明确不构成像素基准。

三处像素策略有明确、可通过合理实现满足的对象，但尚无原生成功证据：

- canvas-fill 使用 menu.canvas 的 semantic box，组件拥有包括 16 单位外 gutter 的背景；x 为框宽的 0.5%–2.5%，y 为 5%–95%，visible_fragment。按公开 390 / 私有 320 宽度，横向范围约 1.95–9.75 / 1.6–8，落在 16 单位 gutter 内；不是 observer 的 host canvas。
- summary-fill 使用 menu.summary 的 semantic box，要求容器保留子文本而非合并成叶节点；x 为 1.5%–3%，y 为 10%–90%，visible_fragment。对于占据可用宽度、两侧 16 单位根 gutter 的卡片，横向范围约 5.37–10.74 / 4.32–8.64，在 12 单位 card padding 内、避开 1 单位 border；上下中部也可避开圆角。该几何推理不是原生语义框实测。
- send-fill 使用实际 menu.submit control box，x 为 2.5%–4.5%，y 为 30%–70%，fully_visible。普通满宽实色 native button 的 16 单位水平 padding 可提供此文字外侧区域；正文可增高。不能用文字 AX 框或隐藏副本代替按钮框。

三者均固定 minimum_pixels=12、minimum_support=0.9、channel_tolerance=1。没有为了通过改变阈值。是否导出唯一容器/控制框、框是否含 padding、部分可见片段如何落入实际 viewport、PNG 映射/颜色支持、最少像素与支持率是否达到，均须以后原始 native/PNG 证据证明。缺失或不足保持 unavailable/unknown；不能猜测通过，也不能自动归因产品失败。这个尚待采集的事实不构成当前设计逻辑矛盾。

Swift 桥接仅 JSON 解码后直接调用导入的生产 API，再转发 submission.wireValue；Kotlin 桥接逐字段构造同一 DTO 并直接调用生产组件。没有业务计算、局部状态、克隆 UI、.id 或 key 重建。两 scope 桥接逐字节相同，launch 绑定实际桥接字节和 fixture canonical digest；修订保持同一调用位置，协调状态属于生产组件。未来 host 的真实 identity 保持仍须实现/集成证据，不能由这次设计批准代证。

纯 JSON prepare.py --verify 成功，且未改写输入；另有不导入冻结工具实现的独立状态/矩阵核算。未重跑作者声明的 baseline-v11 重建，也没有把作者该声明当成本审查的实测结论。
