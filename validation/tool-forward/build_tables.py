#!/usr/bin/env python3
"""Render arithmetic-only comparison tables from the sealed result summary."""
import argparse
import json
from pathlib import Path

R = Path(__file__).resolve().parent


def ratio(value):
    n, d = value['numerator'], value['denominator']
    return f'{n}/{d}，{100 * value["value"]:.1f}%' if value['value'] is not None else f'N/A（{n}/{d}）'


def outcomes(value):
    return '/'.join(str(value[key]) for key in ['PASS', 'FAIL', 'UNASSESSED'])


def seconds(value):
    return 'N/A' if value is None else f'{value:,.3f} s'


def render(data):
    arms = [data['arms'][key] for key in ['baseline_v2', 'candidate_v3']]
    lines = ['# 两组完整统计', '',
             '按封存评分与匹配结果复算。列顺序固定为旧 v2、新 v3；两组均使用 Skill。P/F/U 分别表示通过、失败、未评估。百分比四舍五入，原始分子分母保留。', '']

    def table(title, rows):
        lines.extend([f'## {title}', '', '| 指标 | 旧 v2 | 新 v3 |', '| --- | ---: | ---: |'])
        lines.extend('| ' + ' | '.join([label] + values) + ' |' for label, values in rows)
        lines.append('')

    table('自查和修复，双端合计', [
        ('确认误报发现占比 FP/(TP+FP)', [ratio(a['self_review']['all']['confirmed_false_discovery_share']) for a in arms]),
        ('精确检出 TP / FP / FN', [' / '.join(str(a['self_review']['all'][k]) for k in ['TP', 'FP', 'FN']) for a in arms]),
        ('漏检率 FN/(TP+FN)', [ratio(a['self_review']['all']['miss_rate']) for a in arms]),
        ('原始发现条数', [str(a['self_review']['original_finding_count']) for a in arms]),
        ('原始发现分类', ['，'.join(f'{key}: {value}' for key, value in sorted(a['self_review']['finding_classifications'].items())) or '无发现' for a in arms]),
        ('未裁定原子项数', [str(a['self_review']['all']['uncertain_assessment_keys']) for a in arms]),
        ('首版确认失败修复 F→P/F', [ratio(a['repair']['repair_success']) for a in arms]),
        ('确认回归 P→F', [str(len(a['repair']['confirmed_regressions'])) for a in arms]),
        ('新被观测到的问题 U→F', [str(len(a['repair']['newly_observed_failures'])) for a in arms]),
        ('新增保留场景 P/F/U', [outcomes(a['repair']['additional_final_assessments']) for a in arms]),
    ])
    lines.extend(['这里的“误报率”为发现占比；没有完整已检查负例集合，经典 FP/(FP+TN) 无法得出。未裁定发现不硬算 TP/FP；F→U 不算修好。原始发现分类、重复映射和逐项清单保留在 result-summary.json 与独立匹配文件。', ''])
    rows = []
    for scope, name in [('runtime', '运行时'), ('source', '源码/API')]:
        rows.extend([
            (f'{name} 确认误报发现占比', [ratio(a['self_review'][scope]['confirmed_false_discovery_share']) for a in arms]),
            (f'{name} 精确检出 TP / FP / FN', [' / '.join(str(a['self_review'][scope][k]) for k in ['TP', 'FP', 'FN']) for a in arms]),
            (f'{name} 漏检率', [ratio(a['self_review'][scope]['miss_rate']) for a in arms]),
            (f'{name} 首版确认失败修复', [ratio(a['repair'][scope]['repair_success']) for a in arms]),
            (f'{name} 未解决 F→F / F→U', [str(a['repair'][scope]['initial_to_final']['FAIL']['FAIL']) + ' / ' + str(a['repair'][scope]['initial_to_final']['FAIL']['UNASSESSED']) for a in arms]),
        ])
    table('运行时与源码/API的自查、修复分层', rows)
    rows = []
    for phase, label in [('d0', '首版'), ('final', '最终')]:
        for scope, name in [('runtime', '运行时'), ('source', '源码/API'), ('all', '合计')]:
            rows.append((f'{label} {name} P/F/U', [outcomes(a['grades'][phase][scope]) for a in arms]))
            rows.append((f'{label} {name} 未评估比例', [ratio(a['grades'][phase][scope]['unassessed_ratio']) for a in arms]))
    table('未评估与完整分母', rows)
    for platform in ['android', 'apple']:
        table(f'{platform} 分层', [
            ('确认误报发现占比', [ratio(a['self_review']['by_platform'][platform]['confirmed_false_discovery_share']) for a in arms]),
            ('漏检率', [ratio(a['self_review']['by_platform'][platform]['miss_rate']) for a in arms]),
            ('首版运行时 P/F/U', [outcomes(a['grades']['d0']['by_platform'][platform]['runtime']) for a in arms]),
            ('最终运行时 P/F/U', [outcomes(a['grades']['final']['by_platform'][platform]['runtime']) for a in arms]),
            ('首版运行时未评估比例', [ratio(a['grades']['d0']['by_platform'][platform]['runtime']['unassessed_ratio']) for a in arms]),
            ('最终运行时未评估比例', [ratio(a['grades']['final']['by_platform'][platform]['runtime']['unassessed_ratio']) for a in arms]),
            ('首版确认失败修复', [ratio(a['repair']['by_platform'][platform]['repair_success']) for a in arms]),
        ])
    table('开发阶段记录墙钟', [
        (label, [seconds(a['phase_times'][phase]['elapsedSeconds']) for a in arms])
        for phase, label in [('d0', '首版实现'), ('readonly_review', '只读自查'), ('repair', '一次修复')]]
        + [('三阶段日历合计', [seconds(sum(a['phase_times'][p]['elapsedSeconds'] for p in ['d0', 'readonly_review', 'repair'])) for a in arms])])
    lines.extend(['旧 v2 首版报告跨越服务/容量中断，源码修改时间及原生命令完成记录在预算内；上表保留原始日历时间。精确活跃推理/排队拆分不可得，不能据此宣称工具提速。阶段内原生验证已经包含在阶段墙钟中；与命令耗时相加会重复计费。', ''])
    table('自查实际收到的证据语料与采集成本', [
        ('采集命令数', [str(len(a['self_review_evidence_corpus']['cost']['captures'])) for a in arms]),
        ('截图数', [str(sum(r['snapshots'] for r in a['self_review_evidence_corpus']['cost']['captures'])) for a in arms]),
        ('命令耗时之和', [seconds(a['self_review_evidence_corpus']['cost']['command_seconds_sum']) for a in arms]),
        ('记录墙钟跨度', [seconds(a['self_review_evidence_corpus']['cost']['recorded_span_seconds']) for a in arms]),
    ])
    lines.extend(['这些语料先采集完成，再进入同预算的只读自查；采集成本必须保留。新组复用自己的主评分首版采集，旧组只获得旧采集器的配对语料。它们与下表的测量记录存在复用，不能相加后重复统计，也不能只报自查/修复分钟数就宣称端到端更快。', ''])
    rows = []
    for phase, label in [('d0', '首版评分采集'), ('final', '最终评分采集')]:
        for platform in ['android', 'ios']:
            for key, name in [('command_seconds_sum', '命令耗时之和'), ('recorded_span_seconds', '记录墙钟跨度')]:
                rows.append((f'{label} {platform} {name}', [seconds(a['native_capture_times'][phase]['by_platform'][platform][key]) for a in arms]))
            rows.append((f'{label} {platform} 截图数', [str(a['native_capture_times'][phase]['by_platform'][platform]['native_snapshots']) for a in arms]))
            if platform == 'ios':
                for key, name in [('native_summary_test_span_seconds_sum', '原生摘要中的测试会话跨度之和'), ('post_test_finish_archive_seconds_sum', '测试结束后归档跨度之和')]:
                    rows.append((f'{label} iOS {name}', [seconds(a['native_capture_times'][phase]['by_platform']['ios'][key]) for a in arms]))
    table('统一评分采集成本', rows)
    table('原生执行失败记录', [
        (f'{label} 原生命令非零退出', [str(sum(r['exit_code'] != 0 for r in a['native_capture_times'][phase]['captures'])) for a in arms])
        for phase, label in [('d0', '首版'), ('final', '最终')]] + [
        (f'{label} 完全缺少 observation', [str(sum(not r['observation_available'] for r in a['native_capture_times'][phase]['captures'])) for a in arms])
        for phase, label in [('d0', '首版'), ('final', '最终')]])
    lines.extend(['两组质量测量均使用新版采集器。最终各两个 iOS 槽并行，首版串行；命令耗时之和不是总墙钟，也不能将初始与最终的墙钟差解释成 Skill 收益。测试会话跨度来自原生摘要，不是隔离的 AX CPU 时间；测试结束后归档包含摘要读取、附件导出和档案整理，不是隔离的导出 CPU 时间，缺时间戳保留 N/A。逐条开始/结束、退出码与原始批次排程另存 operator-records/ 和 failure-index.json。', ''])
    paired = data['paired_observation']
    lines.extend(['## 相同源码、相同输入的采集器配对', '',
                  '| 指标 | 旧采集器 | 新采集器 |', '| --- | ---: | ---: |',
                  f'| 运行时 P/F/U | {outcomes(paired["legacy"]["runtime"])} | {outcomes(paired["current"]["runtime"])} |',
                  f'| 运行时未评估比例 | {ratio(paired["legacy"]["runtime"]["unassessed_ratio"])} | {ratio(paired["current"]["runtime"]["unassessed_ratio"])} |', '',
                  f'新获得可评估证据 {len(paired["newly_assessed"])} 项，失去可评估证据 {len(paired["no_longer_assessed"])} 项，P/F 判定差异 {len(paired["confirmed_outcome_disagreements"])} 项。这是同一份旧组首版源码的观察差异，不是产品修复。旧原始图片若已经充分支持判断，仍获得同等信用。', '',
                  '旧/新采集器命令耗时之和分别为 ' + seconds(paired['native_capture_times']['command_seconds_sum']) + ' / ' + seconds(paired['current_native_capture_times']['command_seconds_sum']) + '；记录墙钟跨度为 ' + seconds(paired['native_capture_times']['recorded_span_seconds']) + ' / ' + seconds(paired['current_native_capture_times']['recorded_span_seconds']) + '。旧采集既用于旧组自查，也用于这项配对；新增采集覆盖和额外成本同时报告。这不是隔离硬件的性能基准。', '',
                  '两者使用相同源码、业务数据和冻结的动作意图；旧接口不支持 sweep，冻结操作器将其映射为 capture。实际动作序列保留在各 capture.json 中，滚动和截图数量并不相同。', '',
                  '## 公共基础设施与通用能力验证成本', '',
                  '| 类别 | 原生测试数 | 原生命令跨度之和 | 截图数 |', '| --- | ---: | ---: | ---: |'])
    for key, label in [('generic_tool_engineering', '通用工具工程探针'), ('independent_generic_validation', '独立通用能力验证'), ('common_numeric_transport_probe', '两组共同数值传输补丁探针')]:
        cost = data['engineering_native_costs'][key]
        lines.append(f'| {label} | {cost["native_tests"]} | {seconds(cost["native_seconds_sum"])} | {cost["snapshots"]} |')
    lines.extend(['', '上述成本不等于模型工程活跃时间，也不是新增业务独立样本。共同数值传输修复、宿主/薄桥与用例名称编排修复均不算新版独有收益。', '',
                  '分场景、逐状态、检查方面和缺失方法详见 [完整统计 JSON](result-summary.json)、[原子账本](assessment-ledger.csv)、[原始失败索引](failure-index.json)。一个需求、每组一次实现、两个相关平台；这些计数只支持描述性比较。', ''])
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    content = render(json.loads((R / 'result-summary.json').read_text()))
    path = R / 'TABLES.md'
    if args.check:
        assert path.read_text() == content
    else:
        assert not path.exists(), 'Preserve published tables'
        path.write_text(content)
    print('Comparison tables reproduce sealed arithmetic; no UI judgement.')


if __name__ == '__main__':
    main()
