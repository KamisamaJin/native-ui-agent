from pathlib import Path
import json,time,hashlib
O=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward/design-review/one');start=json.loads((O/'started.json').read_text())['startedAtUnix'];finish=int(time.time());base='validation/atomic-forward/design-v1/'
blockers=[
 {'id':'B1','tasks':['T1','T2','T3'],'files':[base+t+'/'+s+'/policy.json' for t in ['T1','T2','T3'] for s in ['public','private']],'pointers':['/atoms/0/sampling/region','public/BRIEF.md: Layout and visual ownership, continuous empty canvas gutter at least12'],'reason':'The canvas strip x=[0.02,0.035] exceeds the minimum guaranteed12-unit empty gutter in P1: child width358 makes its outer edge12.53. A child beginning at the permitted12-unit inset can occupy about9.9% of this strip; minimum_support0.95 then makes an otherwise conforming canvas unassessable. Android requested390 has the same issue after the pinned screen encoding. The reference happens to use16-unit insets, which does not repair the public minimum guarantee.','impact':'Avoidable U for a conforming implementation; the selected canvas color atom is not guaranteed to sample its declared role.','minimumRevision':'In a new preserved design revision, put the entire canvas strip inside the guaranteed gutter for all approved widths, e.g. x=[0.02,0.03], or explicitly guarantee at least13 empty units (including future offered width402). Update policy/approval digests and task/cohort seals. Keep the tool frozen.'},
 {'id':'B2','tasks':['T2'],'files':[base+'T2/public/reference-P2-expanded.svg',base+'T2/public/reference-P2-expanded.png',base+'T2/public/reference-P2-expanded.meta.json'],'pointers':['SVG text at x40 y1337.56: Maintenance-held','SVG text at x48 y2811.35: pressure-gauge'],'reason':'The independently supplied narrow reference is itself clipped. Maintenance-held extends beyond the216-unit canvas and loses the final letter; pressure-gauge spills out of its card into the right gutter and reaches the image edge. Original PNG crops in this review show both. Thus the visual baseline contradicts the brief requirement that every word remain readable and the continuous empty canvas gutter.','impact':'A builder cannot faithfully follow this reference and also satisfy the stated wrapping/ownership rules; visual judges would receive a contradictory approved source.','minimumRevision':'Reflow these unbreakable hyphenated words into additional readable lines (or use a declared word-breaking rule) and grow the relevant blocks. Regenerate the independent SVG/PNG/meta and preserve a new task/cohort seal; do not alter candidate tooling.'}
]
nonblocking=[
 {'id':'N1','tasks':['T1','T2','T3'],'files':[base+t+'/'+s+'/reference.json' for t in ['T1','T2','T3'] for s in ['public','private']],'pointers':['/cases/*/states/baseline/activationEvents','/cases/*/states/blocked/activationEvents','/cases/*/states/replaced/activationEvents'],'reason':'Unused typed activationEvents in these states contain the eventual submission callback even though the original route has no successful activation there. The contract explicitly makes these cells N/A, so the compiled selected ledger is correct. Remove unused fields or use an empty list so the public typed reference does not suggest contradictory behavior.'},
 {'id':'N2','tasks':['T1','T2','T3'],'files':[base+t+'/public/BRIEF.md' for t in ['T1','T2','T3']],'reason':'State explicitly that layout topology and several central interaction paths are outside this selected ledger: T1 grid breakpoint and column count; T2 rail/severity/dossier placement and moving the open dossier to another selected incident; T3 grouping, toggling off and preserving other selections. The current generic wrapping/overlap questions cannot certify those features. This is a scope/interpretation improvement, not a demand to increase the denominator.'},
 {'id':'N3','tasks':['T1','T2','T3'],'files':[base+t+'/public/BRIEF.md' for t in ['T1','T2','T3']],'reason':'Clarify the unavailable reason source. The brief says unavailable entries remain visible with a reason, but models expose only available/detail (plus severity in T2), and T1/T3 reference c shows generic instructions plus Unavailable rather than a reason. Also name the invariant global detail source in T1/T3 and the no-selection dossier location in T2. These do not change the selected expectations but reduce full-brief implementation ambiguity.'},
 {'id':'N4','tasks':['T1'],'files':[base+'T1/public/BRIEF.md'],'reason':'Define enlarged text precisely for the responsive breakpoint (for example Dynamic Type above large and fontScale above1.0). The approved P1/P2/H1 cases themselves are unambiguous.'}
]
shared={'bindingReview':'Public Swift/Kotlin signatures match adapter calls and fixture keys; real public production components are imported, not reconstructed. Native selected traits belong on a single native choice control; c has native disabled semantics. Canvas is a containing semantic group retaining descendants.','ledger':'Per case/platform:98 cells,81 required and17 explicit N/A. Seven iOS title-native-weight cells remain selected U; Android reads native text font_weight. Control/current state assertions do not use callbacks as proxies.','callbackReview':'T1/T2 successful callback action indices1,2,6,7; caller replacement5. T3 successful indices1,3,7,8; caller replacement6. Expanded/submitted sweep states correctly use stimulus_action to point at the preceding successful activation. Disabled blocked checkpoints are N/A for activation callbacks, not a false quietness pass.','environmentReview':'Canonical design lock, reference source bytes, policy and environment approval digests match. iOS fixed600pt viewport and width minus32 child inset agree with host. Android requested dimensions use the pinned Float32/Paparazzi encoding, not an exact postconversion390dp claim. Hidden H1 uses the same rules/methods/ownership, width312/dark/RTL/xxLarge or fontScale1.2 within the public brief.','observationLimits':'No SDK, simulator, Gradle or native build executed. Static schema/source and independent reference review cannot certify native compilation or actual runtime semantics. Unavailable boxes, color support/mapping, physical touch and generic SwiftUI style remain unassessed.'}
tasks={
 'T1':{'overall':'revise','blockerIds':['B1'],'complexity':'Six-slot responsive grid, single selection, global disclosure, unavailable control, long content and authoritative model replacement are substantive. P1 reaches the two-column branch; P2/H1 one-column branches.','interactionDistinctness':'Layout differs materially from T2 and state semantics from T3. The selected T1/T2 action graphs are identical, so the score alone does not establish their interaction difference.','referenceReview':'P1/P2/H1 PNGs inspected via contact sheet and original-size detail crops; no gutter intrusions found by the additional reference pixel audit.','selectedStateReview':'Summaries, selectedA, enablement, disclosure reset, callback stimulus indices and target selector list agree across public and hidden cases.',**shared},
 'T2':{'overall':'revise','blockerIds':['B1','B2'],'complexity':'Six chronological cards, noninteractive leading rail, severity, selection-dependent inline dossier, disclosure and model replacement form a substantive timeline component.','interactionDistinctness':'Inline dossier position/movement is a real difference from the global disclosure in T1/T3. The selected route never changes selection while the dossier remains open, so that difference is full-brief scope only.','referenceReview':'P1/H1 readable at inspected scale; P2 has confirmed clipped/overflowing words at the cited SVG baselines.','selectedStateReview':'All selected current-state facts and callback indices match the fixtures/route. The selected ledger has no hierarchy atom for the timeline arrangement.',**shared},
 'T3':{'overall':'revise','blockerIds':['B1'],'complexity':'Grouped independent multi-select, ordered label summary and summed estimate, authoritative incoming set replacement and disclosure create a different state structure. P1/P2 use20+35=55min; hidden uses25+40=65min.','interactionDistinctness':'The expanded route actually holds both a and b; replacement retains incoming b and reselecting a restores a,b. This is more than a renamed single-select task, although deselection is not sampled.','referenceReview':'P1/P2/H1 PNGs inspected; no gutter intrusion detected by the additional reference pixel audit.','selectedStateReview':'Summed summaries, selectedA, submission a,b, update quietness and target maps agree across all cases.',**shared}
}
report=f'''# 独立设计复核 one

结论：**revise**。开始 Unix {start}，结束 Unix {finish}，实际用时 {finish-start} 秒。本复核只读取三任务公共/私有设计、设计接口、冻结 candidate-v8 工具及通用宿主源码/文档、工具 gate；没有候选实现，也没有运行 SDK、编译器或原生测试。没有读取 assignment、历史业务结果或另一复核者意见。

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
'''
(O/'REVIEW.md').write_text(report)
review={'startedAtUnix':start,'finishedAtUnix':finish,'overall':'revise','tasks':tasks,'blockers':blockers,'nonblocking':nonblocking,'inputHashes':json.loads((O/'input-hashes.json').read_text()),'validation':'SDK-free static review; verification-audit.json has no structural issues; no candidate implementation inspected.'}
(O/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'overall':'revise','startedAtUnix':start,'finishedAtUnix':finish,'elapsedSeconds':finish-start,'blockers':[x['id'] for x in blockers]}))
