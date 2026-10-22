# Independent design review one — design-v2

结论：**approve**。T1、T2、T3 均未发现会阻断公平性、可执行性或正确验收的设计问题。两条非阻断文档建议列于下方。此结论只批准当前封存设计进入实现阶段，不是对任何未来实现的通过判断。

真实开始 Unix：1792633419；真实结束 Unix：1792633717.867041；用时 298.9 秒。复核期间没有 SDK/原生运行、生产实现、工具改动、提交或 push，也没有使用或联系其他 agent。只在本目录写输出。

读取边界遵循任务要求。未打开旧设计、既有 review/其他评估、attempt/revision 记录、assignment 或旧业务案例。没有遍历 gates/tools.json member 清单。获准的 DELIVERY.md 自带修订摘要；该摘要不是本复核结论的证明。最初文件名定位曾显示部分排除目录的路径，但未读取其内容。完整 inputHashes 位于 review.json；它记录封存输入字节身份，不表示逐个验证日志构成设计正确性的证据。

## 三项判断

- **T1 approve**：P1 的子宽度358、普通字体对应双列；P2 的子宽度216、大字体对应单列。参考图保留时间/工位、不可用原因、全局安全说明、汇总及提交的阅读顺序。API 和两端桥仅解码输入、调用真实生产公开接口、归一回调，没有副本 UI 或桥内业务状态。原始路线上的选择、打开、禁用观察、调用方替换、再次选择、提交分别有明确语义。替换令 a 不可用并清空选择，随后选 b 的 typed 汇总/启用/回调均正确。
- **T2 approve**：外置不可交互 leading rail 与按钮内部的时间标签、uppercase severity 一致；展开时仅被选项 detail 以内联 dossier 出现，无选择时 model.guidance 位于全局披露后。P1、P2 原图与 SVG 无结构冲突；另看 H1 原图确认 RTL rail/对齐。与 T1 的全局详情、网格拓扑相比，其详情位置与选择的耦合实质不同。移动打开 dossier 的行为没有被当前路线验证，这一点在未入 ledger 的范围中明确披露。
- **T3 approve**：分组多选、列表顺序汇总、分钟求和与权威输入替换有独立业务含义。公开 expanded 的 a+b=55 分钟，与 fixture 字段相符；H1 使用其新分钟数重新推导，一样没有引入新规则。替换到 b，再点 a，提交规范化 ID 集合的路线与 typed source、Swift/Kotlin API 和桥一致。分组、汇总面板位置、取消某一选择保留其他选择均仍是 full brief 的义务，当前 selected ledger 未声称已经认证这些方面。

三任务共享若干封存工具能力与状态名称，但不是同一界面换领域文案：T1 的响应式二维网格/全局说明、T2 的时间线/选中内联详情、T3 的分组独立多选/数值聚合具有不同布局和交互结构。每项都包含长内容、禁用项、持久用户状态、披露与同实例 caller replacement，复杂度足够。

## 验收与原子样式

从原始 fixture 和动作按公开业务规则重新推导九个 case、七个状态的 summary、selectedA、submit enablement、disclosure label、成功动作回调、quiet replacement 和主按钮颜色，均与 typed reference 一致。两个平台原始 route、checkpoint map 的 input/action/stimulus 索引一致。expanded/submitted 在 sweep 前的原生激活动作上取事件区间；禁用点击仅独立检查 enabled，不把空事件区间当作成功回调。三项 H1 的 rule identities、方法、责任与公开版本相同，输入仅改变已公开允许的数据和环境组合。

三类颜色分别针对组件 canvas、实际带 padding 的 notice panel、真实 submit button。API 要求语义框对应容器/控件，不能拿文字叶子代替。canvas x=[.02,.03] 在全部获准宽度下均位于12单位连续侧边空白内（最大370×.03=11.1）；notice/submit 的 x=[.025,.045] 位于16单位内部横向 padding，y=[.2,.8] 避开圆角端部。原始九张 PNG 按各自 SVG 对应 box 和 policy 区域做独立像素检查，27个源绘图采样均满足95%纯色支持。详见 reference-region-check.json。该检查只证明参考源和采样角色相容，未来原生语义框缺失、映射不明或颜色支持不足仍必须 U，不能据此预判原生通过，也不能认证未采样画布。

wrapping 与 overlap 是两项独立命题；前者明确按当前选择/披露规则排除合法隐藏内容，要求缺失 required text 为 unknown、可见 clipping/ellipsis 为 false，完整状态覆盖仍是前提。每 case/platform 的98 cells 中81 required、17 N/A 与具体适用性一致：回调3个无成功刺激状态、replacement的6个非替换状态、两项视觉规则的各4个 target-only 状态。iOS title-native-weight 的7个 required cells 必须保留 U，没有用视觉猜测替代原生计算样式。geometry 只声称原生 control/accessibility box 最小高度，不声称 framework padding、glyph geometry 或物理点击区域。

54个 candidate-v8 文件与 freeze 摘要一致。原始 source 字节、contract 嵌入锁、canonical design lock/policy/environment approvals、两端 fixture/action/environment、reference SVG/PNG 摘要及310个获准 cohort 成员一致。Android 保留 paparazzi-float32-screen-config-v1；iOS 环境的 offered width、600高、Dynamic Type 与输入对应。这些是身份和可复核性证据；没有把18/18编译或 schema 成功当作设计正确。

## 阻断问题

无。

## 非阻断建议

1. **N1 — T3/public/API.md，Swift model 段落 “nullable selection is JSON null”**：T3 的 initialSelectedIDs 明确为非可选数组/List，桥与所有 fixture 均如此，该继承句不适用。当前显式类型已消歧；未来保留新修订时删去该句或说明空选择为 []，不要改写本封存版本。
2. **N2 — T3/public/BRIEF.md 首段及 API.md semantic-ID 表 “any incoming ID”**：分组仅定义 a,b / c / d,e,f，没有新增 ID 的 group 字段或兜底规则。当前 P1/P2/H1 都固定 a–f，故不会影响当前验收；如未来拓展 ID 宇宙，应预先明确有效六 ID 限制或补充分组来源，再封存新 case。

本复核按 selected ledger 的诚实边界批准当前设计。full brief 中未入 ledger 的 topology、间距、其余字型/颜色、开放详情迁移、deselect 等要求不能因本次 approve 或未来 selected-ledger 成功而被称为已验证。
