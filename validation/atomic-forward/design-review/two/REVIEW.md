# 独立设计复核 two

结论：**revise**。三种交互结构有实质区别，复杂度适合本次实验；阻断点来自需求本身的未定义/冲突语义，不来自候选实现、已有错误或工具评分。未修改 sealed 提案、工具或生产代码，未启动 SDK。

## 阻断项

**B1 — 三项都要求“不可用原因”，接口却只提供可用状态。** 三个 `public/BRIEF.md:10` 要求不可用项显示 reason；`API.md:3,5` 的条目只有 `available`、普通 label/detail，以及 T2 severity/T3 minutes。T1 `cases/P1/fixtures.json#/initial/slots/2` 和 `/updates/0/slots/0` 的 detail 是一般安全说明；T3 `/initial/services/2` 是交车说明。原图仅追加 “Unavailable”，没有原因。T2 的 severity/事件内容也没有被定义成可用性原因，尤其 caller 可把 watch 条目禁用。实现方若满足“原因”就必须自行编造业务信息。最小修订是在新版本明确只要求固定不可用状态文字；若确实需要原因，则先补充 typed reason、fixture 数据、桥接和参考。该问题影响完整 brief，不能因 selected 只检查 enabled 而忽略。

**B2 — T2 标记的内外位置冲突。** `T2/public/BRIEF.md:8` 要求 time/severity marker 在 select button 外；`reference-P1-expanded.svg:1` 第一卡片矩形为 x=28、y=282.2、w=314、h=86.8，而带时间的 label 位于 x=48、y=314.2，WATCH 位于 x=48、y=341，均在卡片内；外侧只有 x=21 的 rail。P2 和 H1 PNG 同样如此。API 把 choice 绑定到真实选择按钮，不能靠未声明的内部激活边界消解两种层级。最小修订可明确“只有 rail 在按钮外，时间标签和 severity 在按钮内”，与原图一致；如意图是外部标记，则重画并声明其数据和激活边界。

**B3 — 换行布尔问题未排除刻意隐藏的文本。** 三项 public/private `reference.json#/questions/wrapping/value` 都要求所有 choice labels/details、disclosure content words 可读；contract 在关闭 disclosure 的 baseline/submitted 仍预期 true。T2 expanded 也刻意隐藏未选 incident 的 details。字面解释可把正确的折叠判为不可读；另一种解释会自行缩小为当前应显示内容。需在新封存版本明确问题只评价按当前状态规则应显示的文本，排除刻意隐藏内容，并说明缺失必需文本如何处理，避免缺失内容成为 vacuous wrapping pass。保留 wrapping/overlap 分离和缺完整覆盖时的 U。

## 设计与可执行性判断

- T1 的响应式网格、T2 的单列时间线与行内档案、T3 的分组多选/累计估时不是换域改名。六条目、长文本、披露、调用方 revision 替换和回调构成了足够的状态与布局复杂度。
- 独立按 brief 顺序推导了九个 case 的选定业务值和事件：summary、selection、enablement、披露标签、累计分钟及 callback action index 均一致。T1/T2 每 case 9 动作，T3 10 动作，均为 7 个 selected states。expanded/submitted 的 `stimulus_action` 正确回指真正 tap，而非后续 sweep。disabled 检查没有冒充成功回调刺激；replacement quietness 使用 caller_update。
- H1 的 rule IDs、methods、ownership 与公开相同；变化限于公开许可的数据、分钟、方向、字体、宽度与主题组合。没有发现隐藏新要求。
- 源码层面，冻结 iOS 宿主提供 600pt ScrollView、16pt 横向 inset、24pt 顶部 inset、原位 caller update、方向/主题/Dynamic Type；所选 offered widths 248/312/390 均在接口允许范围。Android 提供对应 eager parent scroll、2.75 density screen 编码、fontScale、native layout direction 和真实 semantic OnClick。桥接只解码并调用公开生产 API，Swift 参数顺序、Kotlin 命名参数和事件映射匹配。未运行 SDK，因此这是源契约可执行性复核，不是此次设备运行已成功的宣称。
- `native_checks.callback_verdict` 强制 attempted/succeeded、真实方法、唯一 enabled control、同输入/进程与精确事件区间；caller replacement 必须推进一个输入。该门控足以拒绝把未派发空回调当成功。
- canvas、notice、submit 分成三颗颜色原子，owner 在 brief/API/policy 中均为 component，outer host 背景另属宿主。canvas 要求真实容器框而非 text leaf；12-unit 连续空 gutter 与 notice/button 16-unit padding 为侧边采样提供了产品语义。归一化区域避开 glyph 与圆角；canvas 使用 visible fragment，其他填充要求 fully visible。95% support、24 pixels、opaque ARGB、零 channel tolerance 明确；不充分支持、映射/框缺失或冲突仍为 U，没有从候选像素反推区域。
- wrapping 与 overlap 两颗视觉原子方面独立，除 B3 的可见性量词外，没有把颜色、层级、布局和回调塞进同一视觉判断。iOS title native weight 明确保留 selected U；没有视觉替代 native style。N/A 分别来自无成功激活、非 replacement、仅 target scope 而非全文扫图，理由成立。
- 全部批准 lock/policy/environment 的 canonical digests、source hashes 一致；本地冻结 candidate-v8/ 下 54 文件与 gate 摘要一致。`verification.json` 是语义及完整性检查记录，不是 schema 通过即设计通过的主张。`input-hashes.json` 固定本复核输入身份。

## 非阻断建议

N1：`BRIEF.md:32` 的通用未覆盖清单可增加各任务核心结构未入 selected ledger 的明示项，例如 T1 列数切换、T2 rail/dossier 的位置与迁移、T3 分组/estimate panel。当前 wrapping/overlap 不认证这些义务；无需为增加分数扩张 ledger。

N2：删除或标注非刺激状态中未被使用的 `activationEvents`。baseline/blocked/replaced 数据里残留未来 submit 事件，实际 contract 已 N/A，所以不影响生成断言，但容易误读。

N3：清理 T1/T3 brief 的 incident/dossier/T2 模板句和 T3 API 的 nullable-selection 句；当前 typed API/fixtures 已足够明确，这是编辑清晰度问题。

## 范围与时间审计

本上下文未联系其他复核者或 agent，未查看 assignment、其他复核、旧任务或旧缺陷的正文。公共与私有 contact sheet 的九张参考均已查看，并单独检查 T2 原始 PNG/SVG。

**范围偏差披露：** 初次检查 `gates/tools.json` 完整性时，程序遍历了 candidate-v8 member 的全部文件清单；该 member 还包含允许范围外文件。额外 1201 文件的原始字节仅用于 SHA256，没有解码、输出或用于设计判断。此后保存的逐文件核验结果收窄到 candidate-v8/。这属于 hash-only 读取越界，不能声称读范围完全合规；由复核协调者决定是否需要替换本份上下文。设计发现仅依据指定设计、接口和冻结工具源码/文档。

真实开始/结束 Unix 时间记录在 `timing.json` 和 `review.json`。除指定复核目录外未写入文件；封存后不再修改。
