# Independent design review · v2

Decision: **needs_revision**。第二人批准尚未授予。审查时间：2026-10-25T06:26:46.284099Z。

v2 的66个封存文件及无SDK结构校验通过；首轮 design-review 原失败报告的文件哈希已复核且未改写。D02–D05已在设计层处理，D01的垂直顺序已补足；仍需澄清旧文案排除的匹配边界。

## 唯一未解决发现

### V2-01 · P2 · 旧文案排除的匹配边界未明确，与公开共享子串输入存在歧义

新的 replacement-exclusion 原子已取得明确 runtime/visual 归属，但 /questions/replacement_exclusion 要求所有不同于 replacement 的 initial strings 从 visible UI 消失。它只豁免完全相同的字段值，没有规定排除检查针对完整字段/独立文案实例，还是针对任何可见子串。公开 initial option[2].title 为 Harbor bells，replacement 为 Harbor bells — still unavailable：两字段不同，但正确的新标题仍包含旧字符串。按子串缺席解释，合规的新标题会使该原子失败；按独立完整字段解释可以通过。设计尚未固定这两种解释的边界。

缺口已从缺少验收归属收敛为 oracle 判定歧义；不能在实现前批准唯一、可重复的排除性判定。此发现来自封存公开输入的字符串包含关系，未创建产品实现或注入缺陷。

设计修订要求：明确 stale-copy 排除针对 superseded 字段/独立文案实例，并规定与合法新文案共享子串或词组时的处理；使公开共享子串输入在显示正确 replacement 且无额外旧字段时能被无歧义判定。保持新文案 presence 与 stale-copy exclusion 两个原子独立，不必改变产品代码或 hidden 输入。

公开证据：

- `design/public/reference.json#/questions/replacement_exclusion`（269行）
- `design/public/reference.json#/inputs/initial/options/2/title`（758行）：`Harbor bells`
- `design/public/reference.json#/inputs/replacement/options/2/title`（785行）：`Harbor bells — still unavailable`
- `design/public/policy.json#/atoms/4`：独立的 replaced-only visual exclusion 原子

## D01–D05复核

| 发现 | 本轮结论 |
|---|---|
| D01 | 部分解决：顺序原子完整；排除原子真实存在，但V2-01仍待澄清。 |
| D02 | 已解决：A-leading明确所有文字及trailing switch，独立源码审查。 |
| D03 | 已解决：同handler先赋state再callback归source-only；post-action状态/回调不冒充render timing。 |
| D04 | 已解决于设计层：ROI严格位于明示fill侧带且避开圆角；依赖后续源码组合、原生尺寸和原图像素各自通过。 |
| D05 | 已解决于设计层：R01范围限于预记录production bytes，新增文件source audit与三道全root integration gate分开。 |

## 证据与未观测边界

- ROI数学复核：`0.03×358=10.74<16`；上下间距至少`0.35×48=16.8>12`。这是条件几何论证，尚无原生/像素结果。原minimum pixel/support/tolerance保持不变。
- 三道gate的方法文件hash与83文件baseline的raw/canonical hash均匹配。只读核对stock→initial的exact change、initial→final的allowed change、capture前后fingerprint及capsule映射；未执行gate。
- 没有receipt的integration gate保持unverified；不作runtime regression、roots之外文件、computed styles或物理hit区声明。
- 公开/私有的需求、API、桥接、台账、规则、动作、指针与新policy语义一致；私有只换输入/环境及派生值。本报告未披露私有值。
- 未读取产品实现、assignment文件或旧试验结果，未跑SDK、未注入缺陷，未改设计、工具或产品。

各项原始证据的hash/pointer、27条要求及6个checkpoint的复核见 `review.json`。本轮新报告封存在 `design-review-v2/`；首轮报告保持原样。
