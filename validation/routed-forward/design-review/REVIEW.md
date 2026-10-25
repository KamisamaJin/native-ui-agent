# Independent design review

Decision: **needs_revision**. 第二人批准尚未授予。审查时间：2026-10-25T06:14:52.353798Z。

已在 design/SEAL.json 出现后才读取设计。59 个封存文件哈希一致；设计自带无 SDK verifier 通过。公开/私有需求、API、bridge、源审查台账、规则、状态、逻辑动作和期望指针结构一致，私有仅替换输入或环境及其派生值。本报告不披露私有值。

本轮仅审设计与允许的通用契约/观测实现；未读取产品实现、旧业务/试验结果、controller 或 assignment，未运行 SDK、未注入缺陷，未修改设计、工具或产品。

## 原始发现

### D01 · P1 · 精确垂直顺序与 replacement 后仅有新文案没有完整验收命题

R04 由 O-copy 独占 runtime 覆盖，但其路由只有标签和 content-complete。content 问题检查文案存在与 verbatim，仅对 option 使用 ordered；没有检查标题、说明、note、switch、status、条件文案、primary、Cancel、footer 的完整垂直顺序。R26 的 only the new copy 也没有旧文案排除命题。非重叠和正确标签不能建立这两项事实，ledger 对 R04/R26 均未提供 source-only 补足。

条目覆盖完整的结构校验可通过，验收命题仍遗漏公开要求的部分含义。

设计修订要求：为公开顺序以及 replacement 后旧文案不得残留指定明确、独立且可回答的 runtime/visual 命题或明确 source-only 审查归属；保持原有 presence、wrapping、overlap 原子独立，并更新 ledger/routes/locks。

证据：

- `validation/routed-forward/design/public/requirements.md:9`
- `validation/routed-forward/design/public/requirements.md:53`
- `validation/routed-forward/design/public/reference.json:236#/questions/content`
- `validation/routed-forward/design/public/routes.json:8#/routes/O-copy`
- `validation/routed-forward/design/public/routes.json:130#/routes/O-route-behavior`
- `validation/routed-forward/design/public/source-review-ledger.json:51#/clauses/3`
- `validation/routed-forward/design/public/source-review-ledger.json:421#/clauses/25`

### D02 · P2 · leading alignment 没有被 runtime 问题或 source audit 覆盖

R22 含 use leading alignment；ledger 只归 O-long-content，routes 只归 text-wrap。/questions/wrapping 问可读、换行与截断等，没有对齐命题；其余问题也不检查对齐，audit-index 没有 R22 对齐的 source-only 条目。R19 的单列及 padding 审查并不等价于文字 leading 对齐。

一个满足所有现有问题的居中文字布局仍可违反这条公开要求；本审查没有创建或运行此类实现。

设计修订要求：明确 leading 对齐适用的文字/控件范围，并把该语义交给明确的 source-only 审查或独立 visual 命题。

证据：

- `validation/routed-forward/design/public/requirements.md:45`
- `validation/routed-forward/design/public/reference.json:240#/questions/wrapping`
- `validation/routed-forward/design/public/routes.json:115#/routes/O-long-content`
- `validation/routed-forward/design/public/source-review-ledger.json:361#/clauses/21`
- `validation/routed-forward/design/public/audit-index.json#/items`

### D03 · P2 · 同步进入 started 的时序条件没有验收归属

O-success 检查 activation-events、status-label、summary-present、summary-label，均为成功 dispatch 后的 callback interval 或 checkpoint 事实。通用 callback_verdict 验证唯一启用控件、同 input epoch、进程与事件区间，不验证 started 变更是否同步发生；checkpoint 的后续状态也不能证明同步。R10 的 source_audit_ids 为空，其他 source 条目没有补充此时序条件。

现有验收可说明最终 checkpoint 内容和准确回调，不能说明公开要求中的 synchronously。

设计修订要求：为 synchronously 明确可实现、可核对的语义边界和相应 source-only/runtime 归属，或公开修订该要求；不要把后续截图或空区间当作同步证明。

证据：

- `validation/routed-forward/design/public/requirements.md:21`
- `validation/routed-forward/design/public/routes.json:54#/routes/O-success`
- `validation/routed-forward/design/public/source-review-ledger.json:141#/clauses/9`
- `native-ui-agent/scripts/native_checks.py:127`

### D04 · P2 · primary 固定百分比像素采样区缺少避开文字的几何保证

primary-color 采样 x=2.5%..6%、y=35%..65%，但 R19 仅保证 16 native-unit 水平 padding，R22 要求 leading alignment。根据公开 offered width 与 inset/padding，action 宽度为 offeredWidth-72：公开 390 下区域为 x=7.95..19.08；公开允许的 430 下为 x=8.95..21.48。两个区域的右侧均越过 16-unit 内边距，进入合法 leading label 可绘制的区域。80% dominant 支持阈值并不能在设计层证明所有合法字体尺寸/字形都不会污染这个区域。

不能在实现前把此区域批准为通用的纯 fill 量测点；合规文字可能使像素 atom unassessed，或使结果依赖字形。此处是政策安全性发现，不声称已有渲染失败，也未伪造样本。

设计修订要求：在设计中给出对公开域成立的 ink-free 采样论证，或改用具有明确背景归属/留白保证的独立像素 policy；保持原图、AX 坐标和实际字体/padding 各自证据边界。

证据：

- `validation/routed-forward/design/public/requirements.md:39`
- `validation/routed-forward/design/public/requirements.md:45`
- `validation/routed-forward/design/public/policy.json:32#/atoms/1/sampling`
- `native-ui-agent/scripts/native_pixels.py:100`

### D05 · P1 · 保留 upstream 与单文件变更范围超出 source-only 证据目录

R01 全句只归 A-file-scope。source_self.catalog 为每个审查项仅绑定 approval.production_paths 的两个新增文件的 hash/bytes/line_count；没有整份提交文件清单、基线 diff 或 upstream 身份。仅阅读新增文件不能建立其他 upstream 文件未被更改或保留原行为。当前设计未把这一部分交给其他明确的证据计划。

A-file-scope 的 proposition 比它绑定的可复核证据范围更大；不能把该项 source actual=True 解释为 upstream 保留已验收。

设计修订要求：在设计中明确并绑定 upstream/变更范围的独立基线与审查证据，或把 R01 的 source-only 结论严格限于可从新增文件建立的事实，并为其余义务安排明确归属。本审查不修改 adapter 或其他工具。

证据：

- `validation/routed-forward/design/public/requirements.md:3`
- `validation/routed-forward/design/public/source-review-ledger.json:6#/clauses/0`
- `validation/routed-forward/design/public/audit-index.json:5#/items/0`
- `validation/routed-forward/design/public/approval.json#/production_paths`
- `validation/routed-forward/source_self.py:14`

## 已核对且保留的边界

- 公开业务语义完整，三个验证条件、success/renew、任意 Cancel、editing error 清理、等值/不等值 input replacement 与 current callback 边界均来自公开 prose/API；私有没有另加业务逻辑。
- 两个 bridge 只解码并转发真实回调参数；没有供应产品状态、强制身份、替代 UI 或合成结果。
- API 在设计层没有强制使用 iOS 14 后的能力；本轮不作可编译声明。
- 原生运行验收只要求 AX/Compose 可收集的标签、角色/唯一控件、enabled/selected/value、presence、native rectangle 与精确 callback interval。字体、padding 和大部分 color role 始终是 source-only。
- pt、dp、sp、scalar、argb、bool、events 的单位分离，AX 尺寸没有被解释成 computed font/padding 或真实物理 hit 区。
- 六个 checkpoint 路由与五个 event checkpoint 完整；空回调判定不能绕开成功 dispatch 或同进程 caller update 的证据门槛。
- 结构 verifier 的 passed 只说明 identity、schema、条目映射和 source pointer 再生成功，不能消除上述语义缺口。

## 逐条覆盖审查

| Clause | 归属/结果 | 发现 |
|---|---|---|
| R01 | needs_revision | D05 |
| R02 | covered | — |
| R03 | covered | — |
| R04 | needs_revision | D01 |
| R05 | covered | — |
| R06 | covered | — |
| R07 | covered | — |
| R08 | source_only | — |
| R09 | source_only | — |
| R10 | needs_revision | D03 |
| R11 | covered | — |
| R12 | covered | — |
| R13 | source_only | — |
| R14 | source_only | — |
| R15 | source_only | — |
| R16 | covered | — |
| R17 | source_only | — |
| R18 | needs_revision | D04 |
| R19 | source_only | — |
| R20 | source_only | — |
| R21 | covered | — |
| R22 | needs_revision | D02 |
| R23 | covered | — |
| R24 | covered | — |
| R25 | covered | — |
| R26 | needs_revision | D01 |
| R27 | source_only | — |

逐条解释及原始证据 hash/pointer 见 `review.json`。修改后应重新封存设计，并以本轮报告为不可改写的失败记录进行复审。
