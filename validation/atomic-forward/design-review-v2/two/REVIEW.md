# Independent design review — two

结论：**approve**。T1、T2、T3 均可进入实现；无阻断项。实际开始 Unix 1792633434，结束 Unix 1792633816，耗时 382 秒。本上下文没有接触候选实现、其他 reviewer、旧设计/评审、修订记录、assignment 或其他 study；仅按授权阅读设计-v2 的公开/隐藏文件、接口与冻结 candidate-v8 输入。

三项需求具备实质不同的交互结构：T1 是根据宽度和文字大小切换列数的时间网格与全局安全披露；T2 是时间线与随当前单选项移动的内联 dossier，另有无选择时的全局指导；T3 是分组多选、按列表顺序显示的实时求和估算与全局交接备注。它们共享宿主与原子账本不影响其需求差异。六张 P1/P2 PNG 和三张 H1 PNG 已实际查看，且核对了对应 SVG、元数据及关键源文件。

T1：P1 两列、P2 单列的参考拓扑符合明确的 child width≥320 与各平台字体门槛。公开及隐藏数据均保留六个条目，禁用项有独立非空原因；替换后清空/重置和随后选择 B、提交的摘要及事件正确。

T2：参考图的时间标签和大写 severity 在一个选择按钮内部，rail 独立且 RTL 镜像。选中详情只在展开的当前项下出现，未选中的 dossier 允许隐藏；无选择时使用 model.guidance。P2 长词字符未丢失，块高度随行数增加。公开数据、API、两平台桥接与当前可见文字规则一致。

T3：参考图具有三组多选条目、单独的估算区域和交接披露。初始 A、继而 B 的公开估算为 55 min；替换输入只保留 B，后续再选 A，摘要顺序和提交 ID 归一化均符合契约。H1 仅改变已允许的数据/配置，没有新增规则。

所有任务的 public/private rule identity、原子 policy 和 ownership 一致。独立按业务规则重放 9 条路线，七个选定状态的 summary、A 选择值、主按钮 enablement、披露标签及成功刺激回调全部吻合。expanded/submitted 的 stimulus_action 指向先前真实 tap，避免把 sweep 空事件当作回调成功；blocked 禁用尝试没有成功回调单元。replacement-callback-quiet 仅用于真正推进 fixture 的 caller update。Swift/Kotlin 桥只解码数据并调用公开生产 API，未复制 reducer 或构建替代测试视图。

原子方法与单位明确：主按钮高度 gte 56 pt/dp，标题字重 600 scalar，颜色为不透明 #AARRGGBB 的精确渲染色，wrapping 与 overlap 是两个独立且 source-backed 的 Boolean。每案例每平台共 98 单元，81 required / 17 N/A。N/A 由无成功刺激、无 caller update 或 target-only 观察范围分别解释；不会将 iOS 不可读取的标题字重改为 N/A 或视觉通过。七个 iOS 字重单元继续选中并保持 U。缺失必要文字、未完成 full-content sweep、缺少 native mapping 或色彩支持不足也必须保留 U。

采样测量的是所声明的角色：canvas ID 必须在组件所有内容的 container，保留子语义；notice 在实际有 padding 的 panel，submit 在真实主按钮。canvas strip x=[.02,.03]，在 offered width160–402、扣除宿主两侧16后，最外侧至多 11.1 native units，小于 12-unit 空白 gutter。notice/submit strip x=[.025,.045] 在最大面板宽度下也不越过16-unit内边距；y=[.2,.8] 避开半径10的角。九张参考 PNG 的 canvas strip 实测均为预期纯色、support100%，没有落在文字或宿主上。这是采样设计适用性检查，不能冒充尚未产生的 native 产品证据。

冻结宿主源码与数据形状相容：iOS 固定600pt viewport、显式 offered width、Dynamic Type、主题与方向；Compose 使用持续挂载状态、native OnClick 与 parent scroll，Android 环境明确采用 paparazzi-float32-screen-config-v1 的请求 dp→Float32→整数像素编码。18 组环境文件与 fixture、approval canonical digests 一致；空观察环境检查维持 U。未执行 SDK，不能声称已证明原生渲染成功。

复算保留的 design lock、plan、actions、catalog 与冻结编译器输出一致，463 项静态检查通过，54 个冻结 candidate-v8 文件哈希吻合。另对每张 SVG 检查20个当前应显示的文本串，未发现字符遗漏。输入256份哈希在 review.json 与 static-audit.json 中记录；未遍历其他 tools-gate 成员。

选择账本的边界已公开：网格列数、rail/dossier 位置、分组与多选取消等领域拓扑，以及其他间距/字体/交互分支，不由这14条规则全部数值认证；brief 仍要求实现它们。wrapping/overlap 不能代替这些义务，完整内容也不能靠 footer 或 bottom sentinel 一项证明。

非阻断 N1：`validation/atomic-forward/design-v2/T3/public/API.md` 开头 Swift API 段落仍写“nullable selection is JSON null”。真实 `initialSelectedIDs:[String]/List<String>`、fixture 和桥接均正确使用数组，空值为 `[]`；建议未来不可变修订中澄清该句。无需改变现有 rule、期望、工具或评分。
