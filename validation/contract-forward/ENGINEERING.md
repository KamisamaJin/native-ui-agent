# v6：把独立期望变成执行约束

上一轮失败不只是少看了截图：同一实现上下文把设计理解错，再把相同错误写进自测 expected。逐状态矩阵保证了声明项齐全，却没有核验值是否来自独立设计。新增更多图片无法修正这条共享假设。原始分析保存在 [ANALYSIS.md](ANALYSIS.md)。

本次通用实现先在无关的长内容组件上验证并冻结，然后才设计 Workshop enrollment card。没有读取本轮业务结果后修改冻结工具或按某个字体/组件写专用分支。

| 层 | 可执行保证 | 明确边界 |
| --- | --- | --- |
| 独立设计 | `design_contract.py seal` 检查 owner、approval 引用、来源文件 SHA、JSON Pointer、类型、原生单位、逐状态 disposition、动作路线 | 字符串 owner 与哈希不能证明作者独立，也不能证明语义理解正确；批准摘要应置于实现方自测计划之外 |
| 预期生成 | 只接受来源表达式或同单位加减、带来源的无量纲乘法；容差也必须有独立来源 | 没有隐式 pt/dp/sp 转换；引用正确文件的错误 token 仍需设计审查 |
| 目标绑定 | bindings 只包含逻辑目标到 identifier/label/role 的选择器 | 选择器不能覆盖 expected；来源正确也不能证明选中了正确运行时节点 |
| 执行防篡改 | `native_checks.py` 必须同时接收外部 lock 和摘要；从契约重建全部计划，核验值、容差、状态和路线 | 旧手写计划仍可运行，但报告标为 `unverified_supplied_expectations`；不能声称有相同保护 |
| 样式 | Android 原生 TextLayout 的字号、字重、颜色等；唯一且完整可见、同帧原生边界的宽高/间距/inset | 当前 iOS AX 不提供通用 SwiftUI 计算字号/颜色；AX/Compose semantic box 不等于 layout allocation、padding 属性或物理 hit area |
| 采集成本 | 根据当前原生几何选择较近的未观察目标；一个一致视口供多个目标复用；保留每次实际滚动后的截图 | 导航估计不作为断言事实；不能减少声明状态/目标来制造提速；失败搜索保留 U |

成功原生派发和同一输入/进程/事件区间的回调门控与 v5 AST 一致。禁用、未找到目标、失败派发后的空事件不会被判为业务通过。

## 先于业务的控制

- 根控制：同一中性源码/输入下 iOS、Android 各四次实际采集；冷/暖 v5/v6 共八条命令。原始错误地把 SwiftUI `.frame` 当 AX 宽度造成的八个 F 保留在 alpha 记录，之后明确 layout_box 为 U，数值与动作未变，只有范围校准。
- 独立上下文 forward test：Reading Notes，113 张原图，16 次负例来源/计划篡改拒绝，以及额外 trusted-mode 降级拒绝记录。详见 [独立总结](independent-generic/FINAL-SUMMARY.md)。它支持防篡改机制和平台边界，不代表业务缺陷检出率。
- 单元测试包括来源变动、重复 JSON 键、非有限数、单位/颜色、无来源容差、选择器覆盖、计划修改与矩阵删减；当前共 88 项。
- 原始控制、失败、范围校准和冻结 SHA 均公开；不是用新工具重跑后覆盖旧失败。

## 共同基础设施修正

独立新设计选择 300pt/360pt，但两组冻结 iOS frontend 都只接受 320/390。原始两次 P2 调用在原生测试前 exit2，完整保留。原生宿主本来可传 CGFloat width；共同补丁只把 frontend 改为有限数 160–1024。两组相同补丁、相同设计/源码/动作，先通过无关 340pt 实际原生探针，再只重试缺失的 P2。

[共同修正元数据](COMMON-WIDTH-AMENDMENT.json)固定两个运行副本的完整文件 SHA；原始 v5/v6 冻结副本不变。实际可视范围仍由 native viewport 和图像决定，允许输入不等于完整覆盖。iOS 实际宿主高度为 600pt，Android 依其 fixture 的 640dp；未选择高度相等断言，不能把两者当作同一 640 画布。所有等待、原始失败及重试都进入成本；共同修复不计为 v6 收益。

盲测完成后发布的 live runner 包含这一已实测共同 width 修正。历史发布材料通过 `validation/publications/state-v5` 保存旧 mutable 别名字节；旧 manifest/得分没有重写。
