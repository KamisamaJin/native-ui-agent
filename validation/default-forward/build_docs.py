#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Format closed results and original failure references; no scoring overrides."""
import argparse,json
from pathlib import Path
import study as s
R=s.R

def documents():
 result=s.read(R/'results.json');cost=s.read(R/'costs.json');audit=s.read(R/'execution-audit.json');arms=result['summary']['arms'];by={v['condition']:v for v in arms};cb={v['unit']:v for v in cost['arms']};v9=cb[by['manual']['unit']];v10=cb[by['default']['unit']]
 f=lambda n:f'{n/60:.2f}'
 difference=(v10['normal_workflow_endpoint_seconds']/v9['normal_workflow_endpoint_seconds']-1)*100
 pre=s.read(R/'PRE-IMPLEMENTATION.json')['startedAtUnix'];release=s.read(R/'RELEASE.json')['releasedAtUnix'];reveal=s.read(R/'operators/reveal.json')['revealedAtUnix'];panels=s.read(R/'operators/quality-panels-start.json')['dispatchedAtUnix'];hidden=s.read(R/'gates/hidden.json')['sealedAtUnix'];selfclose=s.read(R/'operators/all-self-barrier.json')['sealedAtUnix']
 table=f'''# v10 单 PR 配对结果

| 同一初始双端 PR | v9 手动入口 | v10 默认链路 |
| --- | ---: | ---: |
| 最终源码相对首版变化 | 无 | 无 |
| 确认产品缺陷 / 回归 | 0 / 0 | 0 / 0 |
| 真实漏检率 / 产品修复率 | N/A / N/A | N/A / N/A |
| 原始 TP / FP / 未裁定严格告警 | 0 / 0 / 1 | 0 / 0 / 1 |
| 公开最终 P / F / U | 325 / 1 / 0 | 325 / 1 / 0 |
| 隐藏场景 P / F / U | 326 / 0 / 0 | 326 / 0 / 0 |
| 合计 P / F / U；适用项 652 | 651 / 1 / 0 | 651 / 1 / 0 |
| 最终未评估比例 | 0% | 0% |
| 独立源码审查，两场景原子项 | 110 P | 110 P |
| 完整交付通过 | 0/1 | 0/1 |
| 内循环请求；每次两平台 | 1；ready | 1；工具选择六状态 |
| 默认复验规划调用 | 不适用；无可验证自愿调用记录 | 6 次，其中 2 次交接诊断 |
| 初始编写＋首采＋完整自验端点 | **{f(v9['normal_workflow_endpoint_seconds'])} 分** | **{f(v10['normal_workflow_endpoint_seconds'])} 分** |
| 成功交付成本 | N/A：无成功交付 | N/A：无成功交付 |

每个平台/场景有 163 个适用原子断言、41 个独立 N/A；四个平台/场景单元合计 652 适用、164 N/A。源码的 55 个条目每场景各审一次，原子值/单位来自独立契约；它们是源码声明和逻辑审查，不能当成运行时计算样式或未执行分支的原生事实。没有确认产品缺陷分母，N/A 不能写成 0% 漏检或 100% 修复。未裁定告警不能写成确认误报；已裁定告警 FDR 为 N/A，全部告警的可能误报占比为 0–100%；未定义真阴性总体，经典 FPR 为 N/A。

## 端点耗时拆分

| 墙钟阶段 | v9 | v10 |
| --- | ---: | ---: |
| 共用初始作者编写与编译 | {f(v9['source_authoring_seconds'])} 分 | {f(v10['source_authoring_seconds'])} 分 |
| 共用首版采集 | {f(v9['shared_D0_acquisition_seconds'])} 分 | {f(v10['shared_D0_acquisition_seconds'])} 分 |
| 交接至源码关闭，含反馈与 API 检查 | {f(v9['handoff_to_source_closed_seconds_including_API'])} 分 | {f(v10['handoff_to_source_closed_seconds_including_API'])} 分 |
| 源码关闭至完整原生/自动检查端点 | {f(v9['source_closed_to_native_automatic_endpoint_seconds'])} 分 | {f(v10['source_closed_to_native_automatic_endpoint_seconds'])} 分 |
| 最终图像/源码实际值审查与调度 | {f(v9['native_endpoint_to_required_final_actuals_seconds'])} 分 | {f(v10['native_endpoint_to_required_final_actuals_seconds'])} 分 |
| 合计，失败端点 | {f(v9['normal_workflow_endpoint_seconds'])} 分 | {f(v10['normal_workflow_endpoint_seconds'])} 分 |

本次新版失败端点多 {(v10['normal_workflow_endpoint_seconds']-v9['normal_workflow_endpoint_seconds'])/60:.2f} 分（{difference:.2f}%）。复验采集墙钟为 {v9['feedback_requests'][0]['collection_seconds']:.2f} / {v10['feedback_requests'][0]['collection_seconds']:.2f} 秒；旧组只采 ready，新版自动扩至六状态，覆盖不同，不能当成同覆盖渲染速度对比。反馈资源排队合计 {v9['feedback_requests'][0]['queue_seconds_sum']:.2f} / {v10['feedback_requests'][0]['queue_seconds_sum']:.4f} 秒，跨平台并行，不能直接从总墙钟相减。

最终复核/调度段相差 {(v10['native_endpoint_to_required_final_actuals_seconds']-v9['native_endpoint_to_required_final_actuals_seconds']):.2f} 秒，不是纯模型推理时间；单个配对也不能把它全部归因于工具。没有 token/货币账单。本次结果支持“这一次没有更便宜”，不支持总体成本优劣的统计结论。

## 共同准备与实验成本

- 预注册记录至工具发布：{(release-pre)/60:.2f} 分，独立中性前测及通用实现窗口；记录起点以前的仓库阅读/交接未完整计时。
- 发布至初始作者派发：{cost['common_pre_author_window_seconds']/60:.2f} 分，为独立设计、两次复核/契约修订及宿主/试验准备的共同窗口；不能冒充纯设计 CPU 时间，也没有计入上面的编写起点。
- 从工具发布算到两份完整自验，真实墙钟分别 {v9['release_through_full_self_wall_seconds']/60:.2f} / {v10['release_through_full_self_wall_seconds']/60:.2f} 分，含共同准备与屏障等待。
- 全员自验封存至隐藏采集完成：{(hidden-selfclose)/60:.2f} 分；独立双评启动至揭盲：{(reveal-panels)/60:.2f} 分。
- 预注册至揭盲研究墙钟：{(reveal-pre)/60:.2f} 分。发布/全历史 CI 另见公开 Actions；不混入本轮 PR 失败端点，也不据此宣称完整研究仅花了 14–17 分钟。

原始秒值见 [costs.json](costs.json)，判定与零分母见 [results.json](results.json)、[冻结指标算法](metrics.py)。
'''
 results='''# v10：默认调用已落地，盲测未体现质量或成功交付成本优势

本轮将需求路由、F/U 定位诊断、复验规划和统一原生执行接入默认入口。全新需求的同一份自然初始 PR 盲测中，两组最后均保持初始源码，未确认产品缺陷或回归，最终同为 **651 P / 1 F / 0 U**。原始严格告警责任不明，完整交付均未通过。真实漏检/修复率和成功交付成本为 N/A。

## 已经具体改变的能力

`ui_loop.py native` / `feedback_loop.run_cycle` 自动重建钉住的原始证据、路由、输出原生拓扑/源码定位诊断、测量实际源码变化、调用 `retest_plan.unresolved`、编译执行所选范围，再路由及门控。调用方不能传断言预期或手选状态。交接前 intake 和最终完整检查也由执行端强制运行。本轮记录 **6 次规划**，其选择逐次与实际执行清单重算一致；不再依赖 agent 想起调用规划 CLI。

诊断保留失败与未知的原始身份、状态绑定帧、精确候选/容器叶节点关系、当前源码字面位置及哈希；不能猜坐标、换选择器或把诊断写成通过。不完整原生采集会留下失败回执与开放任务。相同源码/问题最多允许两次无变化反馈采集，最终仍新鲜全量执行。

独立的全新中性状态机先于业务设计封存，复现并促成四类通用修复：预期“不存在”不再要求把节点找出来；失败定位项不再漏诊断；缺图保留可恢复失败单；未稳定状态可在限额内重采。原始失败与第二快照复跑均保留。这是 **SDK-free 合成传输前测**，不是四个真实业务 bug 修复。139 项工具单测通过。

## 对照与封存

独立上下文设计打印店取件授权组件：长内容、收取人选择、条件确认、禁用提交、回调和同进程调用方替换。源码前复核发现契约索引遗漏必需文案/状态/分支，保留 v1 并在实现前修订；没有根据业务运行结果改变期望。最终六状态、34 规则、每平台 163 适用断言，另有明确源码审查路径和运行时局限。

初始作者只看公开设计，实际模块/调用方编译通过后封存；首次渲染前，原字节复制给两组。两组均一轮反馈，无源码修改；随后源关闭、API 检查、完整公开采集、原始视觉/源码实际值全部封存，才执行隐藏的窄屏/大字体/深色/RTL 场景。再将三份源/原生证据匿名交给两个新评审上下文，两份原始判断及绑定复算全封存后揭盲。无缺陷注入，无按结果替换任务，无事后调阈值或修已知告警。

两组使用相同 coalesced 采集后端。预期不存在的采集语义、失败回执修复均共享；旧决策 CLI 通过共享执行清单兼容层和实际变更测量辅助器使用相同原始首采。不能将这些公共修复记成 v10 默认路由的质量收益。

16 次实际业务平台采集全有有效源码/输入/覆盖绑定。`verified_capture` 只说明采集有效，不表示样式断言通过或 PR 接受。严格屏障是程序化守卫，不能当作对有完整本机权限的恶意调用者的安全沙箱。

## 为什么没有转化成收益

1. **没有真实产品修复分母。** 两份最终源码与共同首版的每个生产字节相同；独立双评没有确认产品缺陷和新增回归。不能用更多发现/诊断/规划次数证明质量更好。
2. **原始样本的意义/精度边界仍阻塞交付。** iOS ready 的公开 AX 高度为 `47.99999999999994 pt`，固定判据是 `>=48 pt`。精确有理运算忠实保存该输入，不能提高 AX 原始样本的真实性。源码声明 48、原图完整，也不能反过来证明 AX 值为 48。双评均保留严格 F，既不认定产品缺陷，也不认定确认误报；隐藏场景通过不覆盖它。本轮未加 epsilon、取整或改源码绕过判据。
3. **调用路由与按行动类型高效调度仍有距离。** 原始自动包每个平台有 12 个待看图的定性 U；路由已要求视觉审查，但默认规划仍从原始自动报告重建，将这些待审项一并纳入原生复验，选出六状态。旧组只重采 ready。新鲜采集不能自行完成定性判断；它们最后由两组同样的实际值审查关闭。强制调用已解决，审查实际值进入下一次规划、按证据类型分派工作仍是成本瓶颈。

本轮没有新增定位 U，也没有证明新版对真实缺陷更敏感。未来若改调度，应先用无关混合证据探针验证：审查任务可以在同一源码/图像上闭合，源码变化后正确失效，只有需要新原生事实的任务才触发采集；不能针对本次高度值或业务组件改条件。本轮冻结代码及主结果不做这种事后修订。

## 结论适用范围

[完整对比与成本](TABLES.md)、[执行选择复算](execution-audit.json)、[两份原始盲评](quality-panels/)、[中性前后失败](probe-review/REVIEW.md)、[失败索引](failure-index.json)、[原图目录](GALLERY.md)、[复算方法](REPRODUCE.md)。

这是一个配对的组件级实验，非真实旧 App 的完整业务 PR，也非人类金标准。新增组件具有独立 ID/桥接契约；不证明任意旧项目无需适配。iOS 为实际 Simulator/XCUITest，最低 iOS14 仅模块/调用方 API typecheck；Android 为 Paparazzi/Compose JVM 语义动作，非设备触摸。通用 SwiftUI 计算字号/颜色/padding、物理命中区、完整页面导航/后端/生命周期不在本轮证明范围。源码通过不替代这些运行时事实。
'''
 reproduce='''# Reproduce

Portable replay requires Python 3.11 and Pillow (requirements under native-ui-agent/scripts). From repository root:

```sh
python3 -B -m unittest discover -s native-ui-agent/tests -v
python3 -B validation/default-forward/test_metrics.py
python3 -B validation/default-forward/probe-design/verify_manifest.py
python3 -B validation/default-forward/probe-review/replay_after.py --output validation/default-forward/cache/replay-new
python3 -B validation/default-forward/design/verify_design.py
python3 -B validation/default-forward/verify.py
python3 -B validation/default-forward/execution_audit.py > validation/default-forward/cache/execution-recomputed.json
python3 -B validation/default-forward/costs.py > validation/default-forward/cache/costs-recomputed.json
python3 -B validation/default-forward/derive_results.py > validation/default-forward/cache/results-recomputed.json
python3 -B validation/default-forward/build_docs.py --check
python3 -B validation/default-forward/artifacts.py --tracked
```

Output paths must be fresh. The replay asserts original F/U, rather than requiring the component to pass. JSON outputs must equal their original published counterparts. Neutral replay replaces native transport with a disclosed synthetic fixture. Portable CI performs no SDK rerender.

For a fresh actual native run, use a Mac with the recorded toolchain/runtime and create a new owned simulator. Bootstrap pinned upstreams with validation/dispatch-forward/bootstrap.py, supplying actual --java-home and --android-sdk (omit --local-upstreams to fetch pinned sources). Copy the selected source capsule's two production roots into that workspace and verify its entire source map. Use the unchanged design/public or design/private plan/lock/routes/fixture/bridge plus actual native options to construct the config described in native-ui-agent/references/default-feedback.md. Then use ui_loop.py native --config CONFIG --output NEW_DIR; final uses --final. Do not reuse historical process/fixtures/images or original simulator IDs. SDK products must be rebuilt from pinned inputs; build-cache hashes in recorded manifests are observed cache identities, not a promise to publish SDK binaries.

All stage/member file hashes and source/image identities are recorded. Original participant sources, first actuals, independent panels and strict numeric alarm remain unchanged. Root tools and metric algorithms were released before business design. Two design revisions are preserved; v2 completeness review preceded initial code. The post-source scripts only normalize evidence, bind original actuals, conservatively combine frozen judgments and format results. Nonempty confirmed-defect/extra-finding cases require explicit independent common-cause matching, not automatic zeroing.

Source/API module outputs already included in explicit seals are retained as compiler evidence. Simulator/SDK/runtime/build caches and full upstream checkouts are excluded. See NOTICE.md and repository THIRD_PARTY_NOTICES.md. Three owned study simulators were deleted after actual captures; no user devices were touched.
'''
 failures={'scope':'Original failures, unknown attribution and limits; no successful repair inferred','items':[
 {'kind':'neutral-tool-failure','path':'probe-review/REVIEW.md','detail':'Original absent-target coverage, failed locator diagnostic, missing-image receipt and settlement retry failures retained; second SDK-free snapshot passes.'},
 {'kind':'preimplementation-contract-gaps','path':'design-review/review.json','detail':'Independent caller-content/state/branch omissions. Original design-v1 retained; independently reviewed revision2 before source.'},
 {'kind':'unresolved-native-alarm','paths':['quality-panels/panel-one/alarm-judgments.json','quality-panels/panel-two/alarm-judgments.json'],'detail':'47.99999999999994 pt versus >=48 pt. Strict F, unresolved cause, all three source versions; no epsilon or product patch.'},
 {'kind':'unsuccessful-delivery','paths':['self-endpoints/unit-161a5d4a.json','self-endpoints/unit-42c9e268.json'],'detail':'Both full self endpoints not accepted; success cost N/A. Source-only/visual passes do not override strict F.'},
 {'kind':'default-scheduling-cost','path':'execution-audit.json','detail':'Original pending qualitative actuals expand unchanged-source native feedback to six states; no product-quality gain.'},
 {'kind':'operator-setup','path':'operators/barrier-initialization-failure.json','detail':'Missing stage registry rejected seal before author/native launch; initialized prospective graph and retried unchanged seal.'},
 {'kind':'source-root-compatibility','path':'operators/legacy-namespace-adapter.json','detail':'Common measured-declaration helper for isolated clones; no edited capture receipts or additional native validation credit.'},
 {'kind':'reviewer-attempts','path':'quality-panels/','detail':'Original draft/failed image inspection or binding attempts retained in each independent panel.'}]}
 return {'TABLES.md':table,'RESULTS.md':results,'REPRODUCE.md':reproduce,'failure-index.json':json.dumps(failures,indent=2,ensure_ascii=False)+'\n'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 for rel,text in documents().items():
  path=R/rel
  if a.check:assert path.read_text()==text,rel
  else:
   with path.open('x')as f:f.write(text)
 print('PASS fixed result/cost/failure documentation')
