#!/usr/bin/env python3
"""Keep the failed primary evaluation and posthoc shared repair side by side."""
import argparse,json
from pathlib import Path
R=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
def pct(x):return'N/A'if x is None else f'{x*100:.2f}%'
def make():
 primary=read(R/'metrics.json');fixed=read(R/'supplement-metrics.json');lines=['# 共享基础设施修复的单独复核','','原始盲测评分保留 Android 环境校验失败及其 U。下表的修正复核只转换已知 Compose 方向枚举，使用原始源代码、输入、原生观测和原始自测发现。它发生在发现评分接口问题之后，属于事后复核，证据强度低于预注册主试验。该修复同时应用于两组，不能算作 v7 收益。','','| 组别 | 评分层 | 阶段 | P | F | U | N/A | 未评估/适用 |','|---|---|---|---:|---:|---:|---:|---:|']
 for tool in ['baseline-v6','candidate-v7']:
  for label,m in [('原始封存',primary),('共享修正复核',fixed)]:
   for stage in ['D0','FINALPublic','FINALHidden','FINAL']:
    r=m['pooled'][tool]['quality'][stage];lines.append('| '+' | '.join([tool,label,stage]+[str(r['counts'][s])for s in ['P','F','U','N/A']]+[pct(r['pooledUnassessedRatio'])])+' |')
 lines+=['','严格按原始描述符匹配检出；不能在看到独立预期后补全原始发现。下表沿用冻结确定性身份账本，FP 含预期/单位不一致，不能全解读为错误产品报警；账本拒绝比例为 FP/(TP+FP)，未知项保留；没有完整 TN 标注，经典 FPR 为 N/A。','','| 组别 | 评分层 | 原始发现 TP/FP/U | 产品簇检出 | 产品行漏检率 | 严格账本拒绝比例 | 公开产品簇修复 |','|---|---|---|---|---:|---:|---|']
 for tool in ['baseline-v6','candidate-v7']:
  for label,m in [('原始封存',primary),('共享修正复核',fixed)]:
   r=m['pooled'][tool];d=r['detection']['combined'];rep=r['repair'];lines.append('| '+' | '.join([tool,label,'/'.join(str(d['counts'][s])for s in ['TP','FP','U']),f"{d['detectedProductClusters']}/{d['confirmedProductClusters']} ({pct(d['pooledClusterRecall'])})",pct(d['pooledRowMissRate']),pct(d['conditionalFalseDiscoveryRatio']),f"{rep['repairedClusters']}/{rep['confirmedClusters']} ({pct(rep['pooledClusterRepairRate'])})"])+' |')
 lines += ['', '注意：新增画布 F 的原因标签并不一致。T1 将新版表现列为宿主/组件责任未知，T2 将两组表现列为宿主问题，T3 将旧版表现列为产品遗漏。原始 F 和所有分类均保留；修正后的 5/6 与 5/5 修复率依赖这些有分歧的标签，不能据此宣称新版质量优势。见 [RESULTS.md](RESULTS.md) 的责任边界说明和 [quality-breakdown.json](quality-breakdown.json) 的逐任务原因分区。']
 pair=fixed['correctedCollectorSessions']['pooled'];lines += ['',f"修正环境校验后的同源采集配对：{pair['denominator']} 项，U→已评估 {pair['unknownToAssessed']}，已评估→U {pair['assessedToUnknown']}，P/F 冲突 {pair['assessedConflicts']}；原始 U 数 {pair['aCounts'].get('U',0)}→{pair['bCounts'].get('U',0)}。不同采集时序会影响结果；这不是独立产品质量试验。"]
 lines+=['','逐任务、公开/隐藏、原始→修正状态转换见 [supplement-metrics.json](supplement-metrics.json)。每条修正评分及新增失败原因分类见 [supplement/](supplement/)。原始结果见 [TABLES.md](TABLES.md)，完整范围和未覆盖项见各独立 summary。额外复核没有原生采集或产品修复；独立评估耗时单列在 [costs.json](costs.json) 的 sharedEnvironmentSupplement。','']
 return'\n'.join(lines)
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();out=R/'SHARED-INFRASTRUCTURE.md';text=make()
 if a.write:assert not out.exists();out.write_text(text)
 else:assert out.read_text()==text
 print('PASS: original and separately corrected tables match sealed metrics')
if __name__=='__main__':main()
