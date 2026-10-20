#!/usr/bin/env python3
# coding: utf-8
"""Generate human tables from replayable metrics, keeping unavailable denominators."""
import argparse,json
from pathlib import Path
R=Path(__file__).resolve().parent

def pct(v):return 'N/A'if v is None or isinstance(v,str)else f'{v*100:.2f}%'
def sec(v):return f'{v:.3f}s'
def wall(v):return f'{int(v//60)}:{v%60:04.1f}'
def build():
 d=json.loads((R/'result-summary.json').read_text());arms=d['arms'];old,new=[arms[k]for k in ['baseline-v5','candidate-v6']];cost=[d['costs']['units'][x['unit']]for x in [old,new]]
 lines=['# 可复算指标与成本','','两组都使用 Skill，v5 手写自测计划，v6 由独立契约生成；共同验收使用同一个冻结 v6 观测与评分策略。`F` 为冻结原子行，不是独立 bug。','', '| 指标 | v5 | v6 |','| --- | ---: | ---: |']
 vals=[('首版公共 P / F / U / N/A',*[f"{x['d0Public']['P']} / {x['d0Public']['F']} / {x['d0Public']['U']} / {x['d0Public']['N/A']}"for x in [old,new]]),('首版公共 U / applicable',*[f"{x['d0Public']['U']}/{x['d0Public']['applicable']}，{pct(x['d0Public']['unassessedShare'])}"for x in [old,new]]),('冻结 F 原始合并漏检',*[f"{x['detection']['combined']['missed']}/{x['detection']['combined']['naturalFrozenFRows']}，{pct(x['detection']['combined']['missShare'])}"for x in [old,new]]),('冻结映射 TP / FP / 未裁定主张',*[f"{x['claims']['TP']} / {x['claims']['FP']} / {x['claims']['uncertain']}"for x in [old,new]]),('条件误报发现占比 FP/(TP+FP)',*[pct(x['claims']['conditionalFDR'])for x in [old,new]]),('含未知主张保守范围',*['N/A'if x['claims']['unknownConservativeBounds']is None else'–'.join(pct(v)for v in x['claims']['unknownConservativeBounds'])for x in [old,new]]),('经典 FPR', 'N/A：无完整 TN 分母','N/A：无完整 TN 分母'),('原始 F → 最终 P / F / U',*[f"{x['repair']['counts']['P']} / {x['repair']['counts']['F']} / {x['repair']['counts']['U']}，{pct(x['repair']['success'])}"for x in [old,new]]),('最终全部 P / F / U / N/A',*[f"{x['finalAll']['P']} / {x['finalAll']['F']} / {x['finalAll']['U']} / {x['finalAll']['N/A']}"for x in [old,new]]),('最终全部未评估占比',*[f"{x['finalAll']['U']}/{x['finalAll']['applicable']}，{pct(x['finalAll']['unassessedShare'])}"for x in [old,new]]),('最终隐藏 P / F / U',*[f"{x['finalHidden']['P']} / {x['finalHidden']['F']} / {x['finalHidden']['U']}"for x in [old,new]]),('实现→自身最终证据封存，含等待',*[wall(x['continuousImplementationToOwnFinalSealSeconds'])for x in cost]),('模型阶段墙钟总和',*[sec(x['modelPhaseWallSumSeconds'])for x in cost]),('自身采集命令时间总和，含原失败/重试',*[sec(x['ownNativeCommandWallSumSeconds'])for x in cost]),('等待及协调',*[sec(x['waitingAndCoordinationSeconds'])for x in cost]),('共同上游 bootstrap',*[sec(x['setupWallSeconds'])for x in cost])]
 lines += ['| '+' | '.join(v)+' |'for v in vals]
 lines += ['','冻结高度 F 是 47.99994dp 与 48dp 的数值分辨率边界，保留原判定但不能证明有意义的产品尺寸缺陷。排除这些未确认产品缺陷后，两组自然产品/业务缺陷漏检率、误报率和修复率均无有效分母；不能用原始 F→P 宣称质量提升。','', '| 最终测量类 | v5 P/F/U/N/A | v6 P/F/U/N/A |','| --- | ---: | ---: |']
 for k in old['finalByClass']:lines.append('| '+k+' | '+' | '.join('/'.join(str(x['finalByClass'][k][s])for s in ['P','F','U','N/A'])for x in [old,new])+' |')
 lines += ['','| 最终场景/平台 | v5 P/F/U/N/A | v6 P/F/U/N/A |','| --- | ---: | ---: |']
 for k in old['finalByCasePlatform']:lines.append('| '+k+' | '+' | '.join('/'.join(str(x['finalByCasePlatform'][k][s])for s in ['P','F','U','N/A'])for x in [old,new])+' |')
 lines += ['','| 同源码原生类配对 | v5 U/applicable | v6 U/applicable | 增/失/冲突 | v5→v6命令秒数 |','| --- | ---: | ---: | ---: | ---: |']
 for alias,p in d['pairs'].items():lines.append(f"| {alias} | {p['v5']['U']}/{p['v5']['applicable']} | {p['v6']['U']}/{p['v6']['applicable']} | {p['gained']}/{p['lost']}/{p['assessedConflicts']} | {p['costs']['v5']['commandWallSeconds']:.3f} → {p['costs']['v6']['commandWallSeconds']:.3f} |")
 p=d['pairTotals'];lines += [f"| 合计 | {p['v5']['U']}/{p['v5']['applicable']} | {p['v6']['U']}/{p['v6']['applicable']} | {p['gained']}/{p['lost']}/{p['assessedConflicts']} | {p['commandWallSeconds']['v5']:.3f} → {p['commandWallSeconds']['v6']:.3f} |",'', '配对只比较原生类，v6 复用首版共同语料与 native-base 原始字节，v5 实际另采；视觉/API/input不计采集器收益。执行顺序、构建缓存、共享机器和单次样本限制耗时归因。', '', '## 业务漏检与修复分母', '', '| 类别 | v5 首版 F / 漏检 | v6 首版 F / 漏检 |', '| --- | ---: | ---: |']
 for k in ['business_current','business_transition','style_native']:
  lines.append('| '+k+' | '+' | '.join(f"{x['detection']['byClass'][k]['naturalFrozenFRows']} / {x['detection']['byClass'][k]['missed']}，{pct(x['detection']['byClass'][k]['missShare'])}"for x in [old,new])+' |')
 lines += ['', '当前业务事实与成功派发后的回调分别计数；失败/禁用刺激后的空事件不证明 handler 正确或错误。未评估仍在适用分母中。原始主张、确切行匹配、修复转移和每个新增/丢失观测见 JSON 账本。', '', '成本包含实际等待和共同 width 适配重试；工具研发、独立设计、共同验收及配对实验分别记录，不作为某组开发速度。未取得 token/账单，未估算费用。', '']
 lines += ['', '## 共同实验开销', '', '| 评分阶段：匿名双组交付→双组封存 | 墙钟秒数 |', '| --- | ---: |']
 for stage,value in d['costs']['sharedGradingStages'].items():lines.append('| '+stage+' | '+sec(value['deliveryToDualSealWallSeconds'])+' |')
 lines += ['', '首个实现开始→四阶段评分完成并揭盲：'+wall(d['costs']['sharedExperimentImplementationToRevealWallSeconds'])+'。评分区间包含通知、协调及等待，可与其他阶段重叠，不能相加为某组活跃时间或费用。全部共同/配对采集命令及资源秒数另见 costs.json 的 experimentOnlyAcquisitions；工具研发和批准前设计不是本轮分组开发速度。', '']
 return '\n'.join(lines)
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();text=build();out=R/'TABLES.md'
 if a.write:out.write_text(text)
 else:assert out.read_text()==text
 print('PASS: tables equal fixed metrics')
if __name__=='__main__':main()
