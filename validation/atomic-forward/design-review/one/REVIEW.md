# 独立设计复核 one

结论：**revise**。开始 Unix 1792632548，结束 Unix 1792633004，实际用时 456 秒。本复核只读取三任务公共/私有设计、设计接口、冻结 candidate-v8 工具及通用宿主源码/文档、工具 gate；没有候选实现，也没有运行 SDK、编译器或原生测试。没有读取 assignment、历史业务结果或另一复核者意见。

## 阻断项

**B1 — 三任务的 canvas 采样区域越过公共保证的空白 gutter。**

文件：T1/T2/T3 的 public/private/policy.json，JSON 指针 `/atoms/0/sampling/region`；对应 public/BRIEF.md 的 canvas gutter 约束。公共 P1 的组件宽358，采样 x=[0.02,0.035] 对应7.16–12.53原生单位；brief 只保证至少12单位空白。一个严格遵守12单位 inset 的子面板可占采样条约9.9%，低于0.95纯色支持率。Android 编码后的357.818…宽仍有同一问题。参考图用16单位 inset，不代表所有合规实现都必须如此。结果会是合规 canvas 的无端 U，不能稳定测量所声明的独立 canvas role。

最小修订：在新的保留版本中把采样条完全放进保证的 gutter，例如 x=[0.02,0.03]；或明确保证至少13单位空白并检查全部允许宽度。重新固定 policy/approval/task/cohort 摘要，不改工具。

**B2 — T2/P2 独立参考原图已有裁字和溢出。**

文件：`T2/public/reference-P2-expanded.svg/.png/.meta.json`。SVG `text[x=40,y=1337.56]` 的 `Maintenance-held` 越出216单位画布，原 PNG 末字母被切掉；`text[x=48,y=2811.35]` 的 `pressure-gauge` 越出卡片进入右侧 gutter，到达图边。证据见 [原图词裁切](T2-P2-original-word-crop.png) 和 [原图卡片裁切](T2-P2-original-card-crop.png)。这同时违反全词可读和12单位空白 gutter；实现不能同时忠实复刻此图和满足这些文字要求。

最小修订：将长连字符词换行/断词并增加内容高度，重新生成独立 SVG/PNG/meta，保留新设计封存。无需改变任何观察工具。

## 三任务判断与接入

| 任务 | 独立复杂性/差异 | 复核结果 |
|---|---|---|
| T1 | 六项响应式网格、单选、全局安全信息、调用者替换 | revise：B1 |
| T2 | 时间线、leading rail/severity、跟随所选项的 inline dossier | revise：B1、B2 |
| T3 | 分组多选、总分钟数、集合替换、全局交接信息 | revise：B1 |

三种完整 brief 在视觉拓扑和 T3 状态结构上有实质差异，并非仅改名。P2 长文窄屏大字与实时 replacement 足以构成复杂组件。但 T1/T2 被选择的动作图完全相同；T2 在 open dossier 期间移动选择的独特交互没有进入采样，不能从这套分数声称已验证。T3 实际产生 a+b、55分钟，H1 则65分钟；替换保留 b 再加 a，确实验证了多选组合。

API/Bridge 逐项静态比对没有接入阻断：Swift public 类型和顺序、Kotlin 命名参数、Codable 键、severity/minutes、单选/多选回调映射都与模型一致。桥接只解码并调用生产 API，没有复制被测视图或持有 reducer。通用宿主确实调用 `ObserverBridge.make` / `Content`，提供16横向 inset、24上 inset、600 viewport、theme/type/direction。没有编译通过即设计正确的推断；本次没有编译。

每 case/platform 有98格，其中81 required、17有具体 N/A。iOS 的7个 title weight 格保留 selected U，未换成视觉字体通过；Android 可从真实 TextLayoutResult 读取 weight。几何只称 accessibility/control box，不称物理触摸区域或 padding。

静态解析了18个 case/platform 的 lock、typed anchors、生成 plan/actions、原始 fixtures/actions、selected target 列表和状态索引。未发现结构或摘要不一致（详见 verification-audit.json）。T1/T2 callback indices 为1/2/6/7、replacement5；T3 为1/3/7/8、replacement6。expanded/submitted 正确把 stimulus 指到前一个 tap，而不是 sweep；blocked-disabled 不被当作 callback 成功刺激。selected/current state 由真实标签/selected/enabled 决定，不使用 callback 代理。

公共 P1/P2 和私有 H1 的规则 ID、原子方法、采样参数、ownership 相同。H1 是公共要求内的312宽、暗色、RTL及数据/分钟数组合，不增加秘密规则。canonical design-lock/policy/environment approval、原始 reference 字节和 PNG/SVG metadata 哈希均匹配；冻结工具54个文件匹配 freeze，所检查关键工具匹配 gate。iOS600高度与 offered width-32 一致；Android 使用声明的 Float32 screen-config 编码，不能把实际389.818…误当违背390请求。

## 非阻断修订与分母范围

1. reference.json 在 baseline/blocked/replaced 的未被引用 activationEvents 填了最终提交回调，虽然 contract 明确 N/A，编译结果没有误判，仍宜删除或置空，避免公共 typed reference 暗示不可能的行为。
2. 明确 unavailable 的“原因”来自哪个字段；T1/T3 只有 available/detail，参考只写 Unavailable 加通用操作说明，没有独立原因。明确 T1/T3 全局 detail 恒取何处、T2 无选择时 general guidance 放何处；T1 也宜给出 enlarged text 的精确阈值。这些不影响当前选定 case 的确定预期。
3. 对完整 brief 尚未认证的部分，现有 exclusions 之外还应明确列出：T1 网格列数及 breakpoint；T2 时间线 rail、severity、dossier 的位置和选择跟随；T3 分组、取消单项后保留其他选择；选中背景处理、整幅 canvas 的全部区域、所有次要排版层级。wrapping/overlap 两个问题不能替代 hierarchy 或这些业务路径的验证。

完整分母外范围还包括：其余 spacing/card尺寸、body字号/ink、group heading、未选 secondary callback、重选幂等/取消路径、同 revision 重组状态保持、非当前三条路径的传入有效/无效 selection 组合、所有 intermediate state、任意输入长度、全部 availability 组合、无选择打开 disclosure、每处阅读/发音顺序、物理 hit area、父应用导航/lifecycle。brief 要求仍适用，当前 selected 分数没有证明它们。

九张独立 PNG 均查看了可接触表，并对 P2 原尺寸区域追加检查。T1/T3 和 T2 P1/H1 未发现外侧12单位 gutter 图像侵入；T2 P2 两处侵入已复核原像素。参考内容高度不作为原生像素/字体基准。颜色采样只证明指定区域 dominant rendered sRGB；不能由一条 gutter 推断整幅 canvas 均正确。缺失/混杂像素、映射缺失、原生不可观测样式、覆盖不足必须保持 U。
