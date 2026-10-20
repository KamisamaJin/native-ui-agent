#!/usr/bin/env python3
"""Render published tables from measured grades/costs, without manual arithmetic."""
import argparse
from contract import R,read
def pct(v):return 'N/A（零分母）'if v['value']is None else f"{v['numerator']}/{v['denominator']}，{100*v['value']:.1f}%"
def duration(s):
 n=round(s);return f'{n//3600}:{n//60%60:02d}:{n%60:02d}'if n>=3600 else f'{n//60}:{n%60:02d}'
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(v)for v in row)+' |'for row in rows])
def render():
 assert (R/'private/assignment-release.json').is_file()
 m=read(R/'result-summary.json');c=read(R/'cost-summary.json');o=read(R/'observation-summary.json');ids=['submission-e572b1','submission-3d6389'];labels=['common-v3 + 共同派发修复','candidate-v4'];arms=[m['arms'][x]['all']for x in ids];costs=[c['arms'][x]for x in ids]
 rows=[]
 for name,path in [('业务漏检（成功原生派发后）',('primaryBusiness','missRate')),('确认发现误报占比（运行时原子行）',('runtimeDescriptive','falseDiscoveryShare')),('全部运行时漏检（描述性）',('runtimeDescriptive','missRate')),('首版运行时失败→最终通过',('runtimeRepair','successRate')),('首版业务失败→最终通过',('primaryBusinessRepair','successRate'))]:rows.append([name,*[pct(a[path[0]][path[1]])for a in arms]])
 rows += [['D0 运行时未评估',*[pct(a['d0']['runtime_total']['unassessedFraction'])for a in arms]],['最终运行时未评估（六场景）',*[pct(a['final']['runtime_total']['unassessedFraction'])for a in arms]],['连续实现开始→自身最终语料封存',*[duration(x['continuousWallSeconds'])for x in costs]],['必需阶段墙钟之和',*[duration(x['sequentialSegmentSumSeconds'])for x in costs]],['队列、屏障和未分配间隔',*[duration(x['barrierQueueAndUnallocatedGapSeconds'])for x in costs]]]
 text='# 指标与成本\n\n'+table(['双端合计',*labels],rows)+'\n\n两组均使用 Skill。原子行重复症状不等于独立缺陷数量；未裁定/未映射发现单列，不自动算误报。没有完整 TN 宇宙，因此不报告经典 FP/(FP+TN)。零自然业务反例分母为 N/A。\n'
 text+='\n冻结 F 行不等于独立产品缺陷数：两组最终 Android 各有两行 `47.99994 dp < 48 dp` 的数值边界失败；candidate-v4 的八个首版业务 F 是同一个装饰勾号合并进 AX 名称的契约问题。原始分数保留，解释与预览排查更正见 [RESULTS.md](RESULTS.md)。\n'
 text+='\n## 各平台与分母\n\n'
 for sid,label in zip(ids,labels):
  text+='### '+label+'\n\n'
  rs=[]
  for p in ['ios','android']:
   a=m['arms'][sid]['platforms'][p]
   for phase in ['d0','final']:
    for bucket in ['runtime_business','runtime_visual','runtime_integration','runtime_capability','input_member_integration','source_api']:
     x=a[phase][bucket];rs.append([p,phase,bucket,x['required'],x['P'],x['F'],x['U']])
  text+=table(['平台','版本','分母','必需','P','F','U'],rs)+'\n\n'
  a=m['arms'][sid]['all'];text+=f"确认原始发现 {a['claims']['originalConfirmed']} 条；未映射确认发现 {len(a['claims']['unmappedConfirmedFindingIDs'])} 条；不确定发现 {len(a['claims']['uncertainFindingIDs'])} 条。最终新评估失败 {len(a['newlyAssessedFailures'])} 行，P→F 回归 {len(a['regressions'])} 行。\n\n"
 text+='## 开发阶段耗时\n\n'
 rs=[]
 for sid,label in zip(ids,labels):
  x=c['arms'][sid]
  for key,caption in [('implementation','实现（包含公开集成）'),('initialCollection','首轮反馈采集（含首次翻译尝试）'),('review','只读看图自查'),('repair','一次源码修复'),('finalCollection','最终六场景采集')]:
   v=x[key];rs.append([label,caption,duration(v.get('wallSeconds',v.get('acquisitionWallSeconds',0))),duration(v.get('commandSumSeconds',0))if'commandSumSeconds'in v else'—',duration(v.get('archiveWallSeconds',0))if'archiveWallSeconds'in v else'—'])
 text+=table(['工具','阶段','墙钟','并行命令秒数之和','归档墙钟'],rs)+'\n\n连续总时长包含真实屏障和队列；阶段之和不是活跃推理或一次无中断吞吐。并行命令之和不能当作端到端墙钟。公开集成已包含在实现阶段，不重复加总。\n'
 text+='\n## 同一 D0 源码的新旧工具配对\n\n'
 rs=[]
 for sid,label in zip(ids,labels):
  for p in ['ios','android']:
   x=c['sameSourceD0Acquisition'][sid][p];rs.append([label+' 的 D0',p,duration(x['commonV3CommandSeconds']),duration(x['candidateV4CommandSeconds']),f"{100*x['reductionFraction']:.1f}%"])
 text+=table(['固定源码','平台','common-v3 命令之和','candidate-v4 命令之和','减少'],rs)+'\n\n'
 rs=[]
 for sid,label in zip(ids,labels):
  for p in ['all','ios','android']:
   x=m['sameSourceD0'][sid][p]['runtime_total'];rs.append([label+' 的 D0',p,x['required'],x['gained'],x['lost'],x['net'],len(x['conflictingAssessedKeys'])])
 text+=table(['固定源码','平台','必需运行时','U→P/F','P/F→U','净增','P↔F 冲突'],rs)+'\n\n这些是同源码观测配对，仍有执行次序、共享机器和编译缓存影响；不是各优化开关的独立消融。通用门控修复、输入翻译与评估格式校准两组共享。\n'
 text+='\n## 逐状态与动作目标观测\n\n'
 rs=[]
 for family in ['own-d0','own-final','audit-v4-d0','audit-v3-d0']:
  for sid,label in zip(ids,labels):
   key=family+'/'+sid
   if key not in o['corpora']:continue
   x=o['corpora'][key]['totals'];rs.append([label,family,f"{x['completeFullStates']}/{x['requiredFullStates']}",f"{x['establishedActivations']}/{x['requiredActivations']}",f"{x['afterSemanticFullyVisible']}/{x['requiredActivations']}"])
 text+=table(['来源实现','采集批次','完整滚动状态','成功原生派发','动作后语义目标完整可见'],rs)+'\n\n可见性是原生几何事实，不等于动作成功或业务正确。禁用/未执行动作、消失目标和未知属性均保留；全部逐项收据在 observation-summary.json。\n'
 text+='\n## 实验额外成本与未知项\n\n'
 audit_rows=[r for rows in c['experimentOnlyAcquisition'].values()for r in rows]
 text+=f"实验额外同源码/统一评分采集 {len(audit_rows)} 条命令，并行命令之和 {duration(sum(r['wallSeconds']for r in audit_rows))}，开始均晚于两组开发周期结束。通用工程验证另有 {c['genericEngineeringAcquisition']['nativeTests']} 次测试、{c['genericEngineeringAcquisition']['snapshots']} 张快照，命令之和 {duration(c['genericEngineeringAcquisition']['commandSumSeconds'])}。它们不计为业务样本。\n\n模型 token 与账单未由宿主提供，记未知；不以估算替代测量。完整逐命令 build/cache/native 子耗时、原始连续起止及间隔见 cost-summary.json；独立评分与共同工程时间线另见 RESULTS.md。\n"
 return text
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();out=R/'TABLES.md';value=render()
 if a.write:assert not out.exists();out.write_text(value)
 else:assert out.read_text()==value,'Published tables do not reproduce'
 print('PASS: tables reproduce from sealed grades and measured timestamps')
if __name__=='__main__':main()
