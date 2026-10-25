#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Format original closed metrics and failure pointers; no verdict overrides."""
import argparse,json
from pathlib import Path
import study as s
R=s.R

def documents():
 result=s.read(R/'results.json');cost=s.read(R/'costs.json');bench=s.read(R/'benchmark-results.json');audit=s.read(R/'execution-audit.json')
 rows={v['condition']:v for v in result['summary']['arms']};old=rows['baseline'];new=rows['default'];bycost={v['unit']:v for v in cost['arms']};oc=bycost[old['unit']];nc=bycost[new['unit']]
 f=lambda v:f'{v/60:.2f}';p=lambda v:f'{v*100:.2f}%';fmt=lambda v:f"{v['passed']} / {v['failed']} / {v['unassessed']}"
 initial=R/s.read(R/'operators/active-D0.json')['path'];failed=s.read(R/'corpora/initial/public/corpus.json');retry=s.read(initial/'corpus.json');debug=retry['startedAtUnix']-failed['startedAtUnix']
 source_unknown=[v['id']for v in s.read(R/'self-review'/new['unit']/'source-only/bound.json')['rows']if v['status']=='unassessed']
 table=f'''# v11 同一初始 PR 双组盲测

基线是冻结的 v10；新版是冻结的 v11。两组共享原生后端、独立设计、一次自然初始实现、首采和原始看图实际值，比较的是自动审查导入与工作类型派发。不是“有测试”对“无测试”。条件在双评和独立原因匹配封存之后揭示；没有产品缺陷注入。

| 结果，单个双端组件 PR | v10 基线 | v11 新版 |
| --- | ---: | ---: |
| 确认初版缺陷，iOS 可访问性/可测性 | 2 | 2 |
| 确认发现 / 漏检 / 残留 / 回归 | 2 / 0 / 0 / 0 | 2 / 0 / 0 / 0 |
| 已确认上述缺陷修复率 | 100% | 100% |
| 业务逻辑、视觉样式缺陷分母及其漏检/修复率 | 0；N/A | 0；N/A |
| 正向产品发现的误报，占已裁定原因 | 0/2；0% | 0/2；0% |
| 共有初版公开原始告警的误报占比 FDR | 2/2；100% | 2/2；100% |
| 最终原始 F；最终告警 FDR | 0；N/A | 0；N/A |
| 最终公开 native/image P / F / U，448 项 | {fmt(old['public'])} | {fmt(new['public'])} |
| 最终隐藏 native/image P / F / U，448 项 | {fmt(old['private'])} | {fmt(new['private'])} |
| 最终 native/image 合计，896 项 | {fmt(old['all'])} | {fmt(new['all'])} |
| native/image 未评估比例 | {p(old['all']['unassessed']/896)} | {p(new['all']['unassessed']/896)} |
| 两场景 source-only 审查，118 项 | {fmt(old['source_all_scope_counts'])} | {fmt(new['source_all_scope_counts'])} |
| source-only 未评估比例 | {p(old['source_all_scope_counts']['unassessed']/118)} | {p(new['source_all_scope_counts']['unassessed']/118)} |
| 完整成功交付 | 0/1 | 0/1 |
| 诊断请求；每次两平台 | 1 | 2 |
| 诊断＋最终实际原生运行次数 | 4 | 6 |
| 分段合计至失败自验端点，分钟 | {f(oc['normal_workflow_endpoint_seconds'])} | {f(nc['normal_workflow_endpoint_seconds'])} |
| 作者派发至最终自验绑定的真实累计墙钟，分钟 | {f(oc['author_dispatch_to_full_self_wall_seconds'])} | {f(nc['author_dispatch_to_full_self_wall_seconds'])} |
| 原始最终实际值已写完、尚未绑定的分段端点，分钟 | {f(oc['normal_workflow_original_actuals_ready_seconds'])} | {f(nc['normal_workflow_original_actuals_ready_seconds'])} |
| 实际值写完至绑定的协调/执行等待，秒 | {oc['actuals_ready_to_admission_binding_seconds']:.2f} | {nc['actuals_ready_to_admission_binding_seconds']:.2f} |
| 成功交付成本 | N/A | N/A |

P/F/U 是通过/失败/未评估。源码审查是声明/逻辑判断，不是运行时计算样式。两组各有 13 个原生几何 U 和 6 个 source U，联合门控均不通过；不能把“零最终 F”写成成功交付。source U 是三个职责问题在公开/隐藏各出现一次，不能当作六个产品缺陷。原始 source/native 计数不混成独立样本。

共有初版公开两条 F、隐藏两条 F 共四个唯一告警，双评与独立匹配均判为未成功派发交互后的条件误报；两份 panel 共八条归因记录不是八个独立告警。它们未被重新改成 P/U。没有定义真阴性总体，经典 FPR 为 N/A。参与者两个正向产品原因都被确认；基线用一个合并陈述覆盖两个原因，新版用两个陈述，不能当作样本量不同。

## 时间分解

| 墙钟阶段，分钟 | v10 | v11 |
| --- | ---: | ---: |
| 共用初始作者＋编译 | {f(oc['source_authoring_seconds'])} | {f(nc['source_authoring_seconds'])} |
| 共用首采原生运行 | {f(oc['shared_D0_native_seconds'])} | {f(nc['shared_D0_native_seconds'])} |
| 共用首图审查与两份绑定 | {f(oc['shared_D0_review_and_binding_seconds'])} | {f(nc['shared_D0_review_and_binding_seconds'])} |
| 交接到源码关闭，含 API 检查和诊断 | {f(oc['handoff_to_source_closed_seconds_including_API'])} | {f(nc['handoff_to_source_closed_seconds_including_API'])} |
| 源码关闭到新鲜完整自动检查端点 | {f(oc['source_closed_to_native_automatic_endpoint_seconds'])} | {f(nc['source_closed_to_native_automatic_endpoint_seconds'])} |
| 最终原图/源码实际值审查及协调绑定 | {f(oc['native_endpoint_to_required_final_actuals_seconds'])} | {f(nc['native_endpoint_to_required_final_actuals_seconds'])} |

分段合计是预先定义的作者＋D0 采集/审查＋各组交接至最终绑定，不等于排除了所有共同准备的实际累计墙钟。原始共用首采曾在 SDK 启动前因环境文件路径失败，共享适配修复等待约 {f(debug)} 分，原包与旧 gate registry 完整保留；累计墙钟也包含这些准备/调度间隔。不能把这部分成本算成新版收益。

原始实际值 ready 时间来自参与者原始报告，后来通过绑定校验；它是**尚未批准的端点**。协调等待两组不同，不能从接近的最终墙钟推导服务等速，也不能把 ready 时间当已接受交付。成功交付分母为 0，失败端点不能换算成成功 PR 成本。没有 USD/token 计费记录。
'''
 report=f'''# v11：分流已实证，复杂 PR 的质量与成功成本优势仍未证实

**做成了实际工具能力：**默认链路自动读取按 capture 注册的原始审查结果，校验源码、计划、输入/动作状态和图像身份，再路由/诊断/复验；待看图、修源码、测量争议和实际原生采集分开。相同源码的这些非采集工作不启动 SDK。定向包审查关闭后自动安排剩余全量，最终新图审查可在原包闭环。注册表追加保存，冲突要显式修订；旧图不能接受新源码。144 项工具测试通过，独立十案例合成重放 9/10；保留 C08 对严格 F/U 的规格差异，未调阈值去迎合。

## 先做的同代码、同覆盖速度验证

中性折纸组件先独立固定三状态、28 个适用断言、2 个 N/A、6 个看图项；工具/方法封存后执行 AB/BA 顺序。两组用相同原生后端、源码、输入、设备与完整覆盖；D0 和新鲜最终图分别原图审查。

旧反馈两次 {bench['old_feedback_service_seconds'][0]:.3f}/{bench['old_feedback_service_seconds'][1]:.3f} 秒；新反馈 {bench['new_feedback_service_seconds'][0]:.3f}/{bench['new_feedback_service_seconds'][1]:.3f} 秒，平均反馈服务提速 {p(bench['mean_service_reduction'])}，新版零 SDK 调用且重建 28P/0F/0U。两份 fresh full final 都新采集并绑定原图，通过 28 项。核心收益是已有实际观察真正被使用，而不是少测。

完整固定覆盖的原生＋实际看图处理分项合计为 {bench['full_coverage_processing']['old']['processing_seconds']:.2f} / {bench['full_coverage_processing']['new']['processing_seconds']:.2f} 秒。该合计不含跨条件协调和绑定开销，是中性组件处理量，**不能当作复杂 PR 端到端提速**。实际时间和限制见 [benchmark-results.json](benchmark-results.json)、[benchmark-method.json](benchmark-method.json)；预发布 pilots 和 preflight 失败保留并排除。

## 全新需求的自然初始 PR 盲测

ListeningBreakPanel 在 AlertToast/Reply 各新增一个文件，包含选择、验证、开始、重选、取消、dirty 状态替换、长内容与缩放。独立设计和两轮未批准审查均在实现前保留；v3 批准才开始写代码。旧文案排除的歧义只澄清完整字段匹配，未更换数据或样式。初始作者仅做编译，两端首试通过；同一初版原字节复制给两组后才首采，不注入错误。

两组源码、自验实际值和 claims 全关闭后才运行隐藏数据/环境；双评原判断关闭后独立匹配 common causes，再揭示条件。两组共用同一原始 D0 和原图实际值，以及相同 actuals 输入界面；基线保留 v10 派发逻辑，新版为 v11。共享环境路径适配、原生后端与模板展示都不算新版收益。

确认两个初版 iOS accessibility/testability 原因：canvas 标识覆盖后代、option 包装层和原生按钮叶节点的命名/选择语义错位。两组都修复，Android 生产源码均未改，未确认新回归。未发现可比较的确认业务逻辑或视觉样式缺陷分母，业务/样式漏检和修复率是 N/A。结果和全部成本见 [TABLES.md](TABLES.md)，原始闭合数据见 [results.json](results.json)。这是 n=1 配对探索，不是人类 gold 或总体统计优势。

## 未评估和误报为什么没有随分流消失

1. 隐藏长内容中部分控件跨越视口，现有几何规则要求整个原生框完整可见；最后各有 iOS 7、Android 6 项尺寸 U。全量滚动覆盖完成也不等于整个大控件在一帧可见。没有把 source 的 minHeight 或截图外观冒充测量通过。
2. source-only 三条 {', '.join(source_unknown)} 要求证明桥接/证据规则/派发前置，却只绑定了组件生产文件。职责与证据不匹配，两组均诚实保留 U。独立设计审查虽补充了集成 diff gates，仍漏掉这组审核方法归属；这也是保留的失败。
3. 四条初版原始 F 是未派发交互后的 error/summary 条件期待。回调有成功派发前置不代表所有后续状态断言都有完整有效性证明。两个 panel 判为条件误报；原始 F 不改写。初版未完成的 dirty/状态路径也不能推定已经验证。

这些是共享评估/证据边界，不是 v11 导入结果后新增的产品错误。公开最终 native/image 两组均 448P/0F/0U，隐藏均 435P/0F/13U；source 两场景均 112P/0F/6U。没有完整成功交付样本，成功交付成本为 N/A。

## 成本瓶颈与归因

新版实际导入原始审查的 cycle 为 8/8，最终原图闭环两次均调用路由与派发；基线对应 cycle 未导入原始 actuals。实际选择和调用已重放 [execution-audit.json](execution-audit.json)。这证明默认接线生效，但此 PR 修复都改了源码，两组都必须 fresh capture，没有产生可供省掉的重复不变源码采集。新版先修复 canvas，首轮仍保留 option 语义问题，再作第二轮；基线一次处理两处。分别 2 / 1 次诊断，实际原生调用 6 / 4 次。这一条 PR 的修复策略/模型差异，不能归为调度算法的总体因果效果。

从作者派发到最终自验绑定的实际累计墙钟，v10/v11 为 {f(oc['author_dispatch_to_full_self_wall_seconds'])}/{f(nc['author_dispatch_to_full_self_wall_seconds'])} 分；分段合计为 {f(oc['normal_workflow_endpoint_seconds'])}/{f(nc['normal_workflow_endpoint_seconds'])} 分。最终原始实际值 ready 的分段端点为 {f(oc['normal_workflow_original_actuals_ready_seconds'])}/{f(nc['normal_workflow_original_actuals_ready_seconds'])} 分，之后等待绑定分别 {oc['actuals_ready_to_admission_binding_seconds']:.2f}/{nc['actuals_ready_to_admission_binding_seconds']:.2f} 秒。旧组的协调等待较长，掩盖了一部分额外修复时间；不能只挑最终墙钟讲收益。

主要剩余成本在长内容原生执行、错误前置条件下的后续动作/扫描，以及原图和源码人工实际值审查。隐藏 iOS 修复版每组约 357 秒，初版约 543 秒，均是实际运行记录；不能用小中性组件的百分比外推。下一步需要在新的独立中性规格里验证：状态/动作前置证据与失败依赖阻断、按比较算子证明部分可见框的有效界限、source/bridge/integration 的证据责任类型，以及有严格新图/命题同一性证明的审查复用。本轮封存后没有针对这些已知数据改评估器或调容差。

## AX 校准的实际边界

先封存的 UIKit 探针 V1 暴露 AX value 512 字节截断，612 条都无法解码；失败保留。V2 紧凑传输真实采集 612 条完整记录，149 条完整可见记录用于拟合/留出：12 个 fit 身份 87 行、6 个 heldout 身份 62 行；重复滚动记录相关。所有残差为零，factor=1 是模型下限，**没有验证正残差误差律**。

校准只增加诊断，不改原始 P/F/U、预期或容差。外部 AX 对象不能仅凭 OS/scale/尺寸相同被视为 identity UIKit leaf；缺少可验证原生 reference 时直接 outside scope。普通 SwiftUI 导出不获得探针的普遍精度担保。调用者 metadata 能证明记录匹配，不能证明运行时真实性；独立前后审查及这一限制都保留在 [calibration-review](calibration-review/REVIEW.md)。没有靠取整、epsilon 或放宽阈值让失败通过，也没有在本次业务数据上重新拟合。

一次性工程窗口约 {(s.read(R/'RELEASE.json')['releasedAtUnix']-s.read(R/'PRE-IMPLEMENTATION.json')['startedAtUnix'])/60:.2f} 分；release 到初始作者派发的中性验证/设计审查/宿主准备窗口约 {cost['common_pre_author_window_seconds']/60:.2f} 分。隐藏评估、双评、原因匹配和发布/CI 是额外研究/发布成本，原始时间均保留，不能摊成已证明的每 PR 节省。没有成功交付分母，也不计算回本 PR 数。

证据： [REPRODUCE.md](REPRODUCE.md)、[failure-index.json](failure-index.json)、[GALLERY.md](GALLERY.md)、[NOTICE.md](NOTICE.md)。iOS 为真实 Simulator/XCUITest；Android 为 Paparazzi/Compose JVM host 的语义 OnClick，不是 emulator touch。字体/padding 的 source 审查不是计算样式；iOS14 module/caller 检查不是 iOS14 运行/链接证明。SDK缓存不发布，独立 AI 判断仍有局限。
'''
 gallery='# Original component captures\n\nImages are original screenshots; no reconstructed replacement or rebaselining. Accessibility fixes may leave the visible component unchanged. See raw native trees and source causes alongside images.\n\n'
 for label,row in [('v10',old),('v11',new)]:
  for phase in ['public','private']:
   for pl in ['ios','android']:
    case=next((R/'design'/phase/'cases').iterdir()).name;base=R/'corpora'/row['unit']/('final-public'if phase=='public'else'private')/pl/case
    if phase=='public':base=base/'capture'
    obs=s.read(base/'native/observation.json');import native_checks
    plan=s.read(base/'parent-plan.json');state=next(v for v in plan['states']if v['id']=='ready');frames=native_checks.bound_state_evidence(obs,state)[0]
    if frames:
     image=base/'native'/frames[0][1]['screenshot'];gallery+=f"## {label} / {phase} / {pl}\n\n![Original ready viewport]({image.relative_to(R)})\n\n"
 return {'TABLES.md':table,'RESULTS.md':report,'GALLERY.md':gallery}
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 for name,text in documents().items():
  if a.check:assert(R/name).read_text()==text,name
  else:(R/name).write_text(text)
 print('PASS derived report/table/gallery '+('unchanged'if a.check else'written'))
if __name__=='__main__':main()
