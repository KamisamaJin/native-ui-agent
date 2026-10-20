# 未计分的评估器分歧审计

这是原始评分、原始发现匹配全部封存之后的只读核对，不是新一轮盲测，也没有改写任何评分、预期、产品或修复信用。

T2 独立视觉评分在两组的原始和最终截图中均判这些状态 P，因此把新版原始两条颜色发现标为 FP。原始发现却附有原图摘要、原生控件矩形、采样坐标和 RGB 值。核对结果如下；两组匿名源码的独立 common 采集均一致：

| 原始状态/控件 | brief 指定禁用填充 | D0 原图平坦区域 | FINAL 原图平坦区域 | 冻结视觉评分 |
|---|---|---|---|---|
| P1 / leveled / mixer.primary | `#C8D7E5` | `#E3EBF2` | `#C8D7E5` | 两组均 P→P |
| P2 / loaded / mixer.voiceMinus | `#405971` | `#283A4D` | `#405971` | 两组均 P→P |

[BRIEF.md](design-v2/T2/public/BRIEF.md) 明确规定 disabled controls use border fill，以及 primary 在禁用时使用 border fill。独立原始视觉判断只认为“subdued disabled appearance”可见，未核实这条具体颜色要求。原始发现未在看到独立答案后改写。

[完整机器记录](grader-disagreements.json)保留八个对称 common 样本的原图/观测/评分 SHA、状态、唯一禁用原生控件矩形、截图与 app frame 的实际比例、采样点及 5×5 区域全部颜色。原始两张自测图的记录采样也逐字节复核。使用的是原始图片，没有生成新渲染、修图、加阈值或补采样本。

这些是截图最终呈现的颜色，不是 SwiftUI 内部计算颜色的反射值。此审计不新增冻结验收单元、不把原始 palette 描述转换为另一种期望格式，也不增加产品检出或修复分母。分歧显示定性 AI 评分不足以充当完整金标准：不能把两条 evaluator-labelled FP 直接宣称为两个真实误报，也不能把这个事后发现算作新版优势。真正的误报率需要可靠的外部裁决，当前不可确定。

复算：`python3 -B validation/multitask-forward/audit_grader_disagreements.py`。原始评分、封存账本和原始独立判断仍保持原样。
