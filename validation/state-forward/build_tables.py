#!/usr/bin/env python3
"""Generate human-readable comparisons directly from the fixed-row metrics."""
import argparse,json
from pathlib import Path
R=Path(__file__).resolve().parent
def pct(x):return 'N/A'if x is None else f'{x*100:.2f}%'
def clock(x):return f'{int(x//60)}:{x%60:04.1f}'
def triple(p):return f"{p['P']} / {p['F']} / {p['U']}"
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |'for row in rows])
def build():
 s=json.loads((R/'result-summary.json').read_text());arms=[s['arms'][v]for v in ['baseline-v4','candidate-v5']];out=['# 完整指标与成本','', '所有数字由 `metrics.py` 从固定评分行及原始主张复算；P/F/U 为通过/失败/未评估。D0只用四个公共场景，FINAL用全部六个场景。显式N/A、源/API、输入和刺激执行另列，不混入运行时覆盖。','']
 rows=[]
 for title,get in [('D0 公共运行时 P/F/U（8948行）',lambda a:triple(a['d0PublicRuntime'])),('FINAL 全部运行时 P/F/U（14324行）',lambda a:triple(a['finalRuntime'])),('FINAL 未评估比例',lambda a:pct(a['finalRuntime']['unassessedShare'])),('FINAL 公共 P/F/U',lambda a:triple(a['finalPublicRuntime'])),('FINAL 隐藏 P/F/U',lambda a:triple(a['finalHeldoutRuntime'])),('运行时合并漏检，原子F口径',lambda a:f"{a['detection']['allRuntime']['combinedMissed']}/{a['detection']['allRuntime']['naturalFRows']}，{pct(a['detection']['allRuntime']['combinedMissShare'])}"),('业务漏检率',lambda a:pct(a['detection']['business']['combinedMissShare'])),('原生样式漏检率',lambda a:pct(a['detection']['byClass']['runtime.style.native']['combinedMissShare'])),('F→P / F→F / F→U',lambda a:f"{a['repair']['FtoP']} / {a['repair']['FtoF']} / {a['repair']['FtoU']}"),('原始F→最终P',lambda a:f"{a['repair']['FtoP']}/{a['repair']['denominator']}，{pct(a['repair']['verifiedPassShare'])}")]:rows.append([title]+[get(a)for a in arms])
 out+=['## 不同实现的开发结果','',table(['指标','Skill v4','Skill v5'],rows),'','原子F不是独立bug数。新版46个原生字体F全部漏检；46个视觉F来自同一状态标记问题，7个覆盖F单独归类。两组各23个AX尺寸F在修复后成为48±2pt的U，不能算通过。业务无自然F，N/A不代表零漏检能力。','']
 rows=[]
 for a in arms:
  c=a['claims'];n=c['claimCounts'];m=a['claimPanels']['byOrigin']['manual_only'];allc=a['claimsAllActualReports']
  rows.append([a['unit'],f"{n.get('confirmedTrue',0)} / {n.get('confirmedFalse',0)} / {n.get('uncertainOrUnmapped',0)}",pct(c['conditionalFalseDiscoveryShare']),'–'.join(pct(x)for x in c['allUncertainConservativeInterval']),f"{pct(m['conditionalFalseDiscoveryShare'])}，另{m['claimCounts'].get('uncertainOrUnmapped',0)}项不确定",pct(allc['conditionalFalseDiscoveryShare'])])
 out+=['## 原始发现的误报与不确定性','',table(['单元（顺序v4/v5）','TP主张 / FP主张 / 不确定未映射','首次报告+手工条件FDR','全不确定两端界','手工单独条件FDR','含实际诊断重跑FDR'],rows),'','FDR = FP/(TP+FP)，只在可裁定正向主张中计算；缺完整TN集合，经典FPR不可得。重复主张和多行匹配不增加唯一检出数。旧组492条诊断失败重跑另列，主表用首次报告；限制/U/通过记录保留为非正向账本。条件FDR差异不能掩盖大量未知主张。','']
 rows=[]
 classes=sorted(arms[0]['finalByClass'])
 for c in classes:rows.append([c]+[f"{triple(a['finalByClass'][c])}；U {pct(a['finalByClass'][c]['unassessedShare'])}"for a in arms])
 out+=['## FINAL 按检查类别','',table(['类别','v4 P/F/U','v5 P/F/U'],rows),'','完整评分还逐平台、逐场景、逐状态保留。每组源/API10P、输入24P独立列出；physicalHit全部1184U，不由语义点击或源码声明补成通过。','']
 p=s['pairTotals'];rows=[]
 for alias,pair in s['pairs'].items():
  rows.append([alias,triple(pair['v4']),triple(pair['v5']),pair['gainedRows'],pair['lostRows'],pair['assessedConflicts'],pair['nativeOnly']['gainedRows']])
 rows.append(['合计',triple(p['v4']),triple(p['v5']),p['gainedRows'],p['lostRows'],p['assessedConflicts'],sum(x['nativeOnly']['gainedRows']for x in s['pairs'].values())])
 out+=['## 同源码采集器配对','',table(['固定源码','v4 P/F/U','v5 P/F/U','U→P/F','P/F→U','P↔F','其中原生类新增'],rows),'',f"未评估合计 {pct(p['v4']['unassessedShare'])} → {pct(p['v5']['unassessedShare'])}；新增2379P与45F，视觉与原生事实分开保留。没有丢失项或已裁定冲突。全量变化行见 paired-changes.json，独立版本还保留前后完整原子行。v5复用共同D0原件，没有再次采集或改判。",'']
 for alias,pair in s['pairs'].items():
  out += [f'### {alias} 按类别','',table(['类别','v4 U','v5 U','新增','丢失','冲突'],[[c,d['v4']['U'],d['v5']['U'],d['gainedRows'],d['lostRows'],d['assessedConflicts']]for c,d in pair['byClass'].items()]),'']
 rows=[]
 for a in arms:
  c=s['costs']['units'][a['unit']]
  rows.append([a['unit'],clock(c['continuousImplementationToOwnFinalSealSeconds']),clock(c['modelPhaseWallSumSeconds']),clock(c['ownNativeCommandWallSumSeconds']),clock(c['uncoveredWaitingAndCoordinationSeconds'])])
 out+=['## 开发端到端成本','',table(['单元（v4/v5）','实现开始→自身FINAL封存','实现+自查+修复阶段和','自身原生命令资源时间和','未覆盖等待/协调'],rows),'','连续终点包含真实等待和双组屏障。阶段和不是端到端时间；原生命令按每次一iOS槽+一Android槽并行，命令时间和不是墙钟时间。原始时间戳和每阶段记录在costs.json。Token及金额未测量。','']
 rows=[]
 for alias,pair in s['pairs'].items():
  for platform in ['ios','android','total']:
   old=pair['actualCommandWallSeconds']['v4'][platform];new=pair['actualCommandWallSeconds']['v5'][platform]
   rows.append([alias,platform,f'{old:.3f}',f'{new:.3f}',pct(new/old-1)])
 old=p['actualCommandWallSeconds']['v4'];new=p['actualCommandWallSeconds']['v5'];rows.append(['两源码','合计',f'{old:.3f}',f'{new:.3f}',pct(new/old-1)])
 out+=['## 配对采集成本（命令秒数和）','',table(['源码','平台','v4秒','v5秒','变化'],rows),'','此处包括真实编译/缓存校验、启动、采集和导出。v5先采、v4后采，共享Mac/依赖缓存、源码不同且硬件可能争用，不作无偏性能或因果速度推断。所有原始命令和build/native子计时保留。冻结前独立的暖机中性对照也观察到iOS +79.8%、Android +18.4%，额外导航有实际代价。','']
 rows=[]
 for stage in ['D0','FINAL','selfreview','paired-D0']:
  c=json.loads((R/'evaluation'/stage/'phase-costs.json').read_text());rows.append([stage,clock(c['continuousEvaluationWallSeconds'])])
 out+=['## 实验评估成本','',table(['独立评估阶段','连续时间'],rows),'','共同采集、同源码配对、独立评估、通用工程和发布/CI属于实验成本。各工作窗口可能重叠，不能把这些时间简单相加当作开发端到端成本。88次计划业务采集保留1891个快照记录和3次非零退出；另有冻结前通用运行证据。','']
 return '\n'.join(out)
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();text=build();path=R/'TABLES.md'
 if a.write:path.write_text(text)
 else:assert path.read_text()==text,'Table text differs from fixed metrics'
 print('PASS: fixed-row comparison tables')
if __name__=='__main__':main()
