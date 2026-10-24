#!/usr/bin/env python3
"""Display fixed metric outputs; no new classifications or defect grouping."""
import argparse
import study as s
R=s.R

def frac(a,b):return f'{a}/{b}，{a/b:.1%}'if b else'N/A（分母为零）'
def minutes(values,key):return f'{sum(v["cost"][key]for v in values)/len(values)/60:.2f}'
def build():
 s.gate.authorize(R/'gates','reveal',R);summary=s.read(R/'summary.json');groups={k:[v for v in summary['units'].values()if v['condition']==k]for k in ['baseline-v8','candidate-v9']}
 columns={}
 for key,values in groups.items():
  repair=[v['repair']for v in values];out=[v['finalOutcome']for v in values];detect=[v['originalDetection']['combined']for v in values];source=[v['sourceOutcome']for v in values]
  sums=lambda f:sum(f(v)for v in values)
  counts={k:sum(v['finalPublic']['counts'][k]for v in values)for k in ['passed','failed','unassessed','not_applicable']}
  fp=sum(len(v['finalKnownFalseAlarmRows'])for v in out);found=sum(len(v['detectedFinalPublicFailures'])for v in out);product=sum(v['confirmedFinalPublicMustProductFailures']for v in out);miss=sum(len(v['finalKnownFalseNegatives'])for v in out);unresolved=sum(len(v['finalUnresolvedProductFailures'])for v in out)
  alarm={k:sum(v['counts'][k]for v in detect)for k in ['TP','FP','U']}
  columns[key]={
   '相同初始 PR 的确认产品原子表现':str(sum(v['confirmedProductRows']for v in repair)),
   '原始发现 TP / FP / 未裁定':f'{alarm["TP"]} / {alarm["FP"]} / {alarm["U"]}',
   '原始告警条件误报占比 FP/(TP+FP)':frac(alarm['FP'],alarm['TP']+alarm['FP']),
   '原始严格 F→最终 P / F / U（不等于产品修复）':' / '.join(str(sums(lambda v,k=k:v['strictDiagnosticTransitions']['counts'][k]))for k in ['passed','failed','unassessed']),
   '确认产品行修复':frac(sum(v['rowFinalStatuses']['passed']for v in repair),sum(v['confirmedProductRows']for v in repair)),
   '确认缺陷簇修复':frac(sum(v['repairedClusters']for v in repair),sum(v['confirmedClusters']for v in repair)),
   '最终公开 P / F / U / N/A':' / '.join(str(counts[k])for k in counts),
   '最终公开未评估比例':frac(counts['unassessed'],sum(counts[k]for k in ['passed','failed','unassessed'])),
   '最终 MUST 产品 F；自身检出 / 漏检 / 未评估':f'{product}；{found} / {miss} / {unresolved}',
   '最终已知漏检率':frac(miss,product),
   '最终确认误报行 / 条件误报占比':str(fp)+'；'+frac(fp,fp+found),
   '新增确认产品回归行':str(sums(lambda v:len(v['delivery']['confirmedProductRegressions']))),
   '保留场景确认 MUST 产品 F 行':str(sum(len(v['hiddenConfirmedMustFailures'])for v in out)),
   '完整自身验收 accepted / PR 数':f'{sums(lambda v:bool(v["selfCheck"]["accepted"]))}/{len(values)}',
   '最低 iOS 源码/API 校验通过 / PR 数':f'{sums(lambda v:bool(v["selfCheck"]["minimumSourceAPIAccepted"]))}/{len(values)}',
   '源码审查自身 gate 通过 / PR 数':f'{sums(lambda v:bool(v["selfCheck"]["sourceAccepted"]))}/{len(values)}',
   '源码审查初始确认违约行 / 修复行':f'{sum(len(v["initialConfirmedSourceProductViolations"])for v in source)} / {sum(len(v["repaired"])for v in source)}',
   '源码审查最终违约 / 漏检 / 未评估':f'{sum(len(v["finalConfirmedSourceProductViolations"])for v in source)} / {sum(len(v["finalKnownMisses"])for v in source)} / {sum(len(v["finalUnresolved"])for v in source)}',
   '源码审查新增回归行':str(sum(len(v['newConfirmedSourceRegressions'])for v in source)),
   '接手→完整自身验收端点，均值/分钟':minutes(values,'handoffToCompleteSelfCheckSeconds'),
   '初始编写＋初始采集＋完整自身验收，均值/分钟':minutes(values,'authoringPlusEvidencePlusFullSelfCheckSeconds'),
   '初始编写开始→完整自身验收，实际墙钟均值/分钟':minutes(values,'observedInitialAuthorStartToSelfCheckSeconds'),
   '共同设计准备开始→完整自身验收，实际墙钟均值/分钟':minutes(values,'observedSharedDesignPreparationStartToSelfCheckSeconds'),
   '接手→原始完整采集及自动检查，均值/分钟':minutes(values,'handoffToAutomaticSeconds'),
   '内循环原生请求数':str(sums(lambda v:v['cost']['feedbackRequests'])),
   '原生设备排队资源秒数（不能直接加到延迟）':f'{sums(lambda v:v["cost"]["nativeQueueSumSeconds"]):.2f}',
   '已记录原生子进程资源秒数（可重叠）':f'{sums(lambda v:v["cost"]["recordedNativeSubprocessWallSumSeconds"]):.2f}',
   '原生返回后自动检查资源秒数（可重叠）':f'{sums(lambda v:v["cost"]["recordedAfterNativeAutomaticWallSumSeconds"]):.2f}',
   '缺失原生阶段计时的请求数':str(sums(lambda v:v['cost']['nativeTimingUnrecordedRequests'])),
  }
 lines=['# 指标与完整成本','','两项全新需求，每项只有一份自然产生的初始双端 PR，原字节复制给两个修复条件。两组都用 Skill；对照为 v8，实验为 v9。以下为描述性配对结果。','','| 固定口径，双任务汇总 | v8 | v9 |','| --- | ---: | ---: |']
 for row in columns['baseline-v8']:lines.append('| '+row+' | '+columns['baseline-v8'][row]+' | '+columns['candidate-v9'][row]+' |')
 lines+=['','原子表现可能重复同一根因；源码违约单独报告，不能与运行时表现相加当作独立 bug。零分母为 N/A；U 既不算修复也不算通过。经典 FPR 缺完整 TN 分母，不可得。AI 双评一致是研究判定，不是人类金标准。','','“完整自身验收端点”包括最终完整原生采集、看图、源码审查和实际 Swift 模块/调用方最低 API 校验，失败端点仍计成本。accepted=false 时不能声称成功交付耗时；成功交付成本不可得。原始自动端点保留以对应预注册主口径。','','可归属路径将相同的初始编写和初始采集全额计入两组，再加接手到自身完整端点。实际墙钟还包含等待另一任务封存、操作员排程等实验成本。原生资源时间可以重叠，不与墙钟相加。外部双评、开发本 Skill、设计修订和 CI 成本另列。tokens/金额未精确记录，保持未知。','','## 每项 PR 的原始端点','','| 任务 / 条件 | 初始编写分 | 初始采集分 | 接手→自动分 | 接手→完整自验分 | 可归属端到端分 | 实际墙钟分 | accepted |','| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
 for v in sorted(summary['units'].values(),key=lambda v:(v['task'],v['condition'])):
  c=v['cost'];keys=['sharedInitialAuthoringSeconds','sharedInitialEvidenceSeconds','handoffToAutomaticSeconds','handoffToCompleteSelfCheckSeconds','authoringPlusEvidencePlusFullSelfCheckSeconds','observedInitialAuthorStartToSelfCheckSeconds'];lines.append('| '+v['task']+' / '+v['condition']+' | '+' | '.join(f'{c[k]/60:.2f}'for k in keys)+' | '+str(v['selfCheck']['accepted'])+' |')
 lines+=['','## 同代码、同覆盖的采集对照','','| 中性配置 / 次数 | 旧秒数 | 合并采集秒数 | 下降 | 同覆盖且无已知结果损失 |','| --- | ---: | ---: | ---: | --- |']
 for v in summary['neutralPerformance']['pairs']:lines.append(f'| {v["case"]} / {v["repetition"]} | {v["legacySeconds"]:.3f} | {v["coalescedSeconds"]:.3f} | {v["reduction"]:.2%} | {v["speedEligible"]} |')
 lines+=['','这是共享后端优化的证据，两组修复均使用优化后后端，不算 v9 独有的修复决策优势。首次旧运行包含冷启动；反向顺序的暖运行仍保留。定向采集少覆盖状态，不混入这项同覆盖提速比较。','','## 实验完整墙钟','','包含设计/验收准备及失败方案、操作员排程和并发重叠，不能解释为精确活跃工时或摊销后的生产成本。发布和 CI 在这些阶段之后。','','| 阶段 | 分钟 |','| --- | ---: |']
 for key,value in summary['studySpans'].items():
  if key!='scope':lines.append(f'| {key} | {value/60:.2f} |')
 lines.append('')
 return '\n'.join(lines)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();value=build();path=R/'TABLES.md'
 if a.check:assert path.read_text()==value
 else:
  with path.open('x')as stream:stream.write(value)
 print('PASS fixed metric tables')
