"""Render already authenticated v3 arithmetic; never infer missing quality."""
import argparse
import json
from pathlib import Path


def ratio(value):
    n, d = value['numerator'], value['denominator']
    return 'N/A（分母为 0）' if not d else f'{n}/{d}（{value["value"]:.1%}）'


def minutes(value): return 'N/A' if value is None else f'{value/60:.2f} 分钟'


def table(a, b, disk=None):
    if a['version'] != 3 or b['version'] != 3 or (a['arm'], b['arm']) != ('A', 'B'):
        raise ValueError('Exact fixed v3 A/B arithmetic required')
    if a['attempts'] != 5 or b['attempts'] != 5: raise ValueError('All five paired attempts required')
    rows = []
    def row(label, left, right): rows.append(f'| {label} | {left} | {right} |')
    for label, key in [('最终原始缺陷漏检', 'final_residual_miss_fraction'),
                       ('原始缺陷对应关系未确定', 'unresolved_initial_relation_fraction'),
                       ('初始真实缺陷检出', 'initial_detection_fraction'),
                       ('原始缺陷修复', 'repair_fraction'),
                       ('实际尝试修复中的成功率', 'attempted_repair_fraction')]:
        row(label, ratio(a[key]), ratio(b[key]))
    for label, phase in [('原公开循环缺陷告警误报占比', 'worker_public'),
                         ('封存后独立验收告警误报占比', 'independent_private_after_seal')]:
        row(label, ratio(a['alarm_by_phase'][phase]['false_discovery_fraction']), ratio(b['alarm_by_phase'][phase]['false_discovery_fraction']))
    row('未裁定缺陷告警', a['counts']['unresolved_alarm'], b['counts']['unresolved_alarm'])
    row('错误的正向验证声明', a['counts']['false_positive_validation'], b['counts']['false_positive_validation'])
    row('未裁定正向验证声明', a['counts']['unresolved_positive_validation'], b['counts']['unresolved_positive_validation'])
    row('新增回归（已确认 / 未确定）', f'{a["counts"]["regression"]} / {a["counts"]["unresolved_regression"]}',
        f'{b["counts"]["regression"]} / {b["counts"]["unresolved_regression"]}')
    row('完整交付率', ratio(a['complete_delivery_fraction']), ratio(b['complete_delivery_fraction']))
    row('必需未评估项', ratio(a['mandatory_coverage']['unassessed_fraction']), ratio(b['mandatory_coverage']['unassessed_fraction']))
    def partition(value):
        counts = value['mandatory_coverage']['counts']
        return f'{counts["passed"]} / {counts["failed"]} / {counts["unassessed"]} / {counts["not_applicable"]}'
    row('义务划分：P / F / U / 预先不适用', partition(a), partition(b))
    for label, key in [('五次公开验证/修复总耗时', 'all_attempt_public_seconds'),
                       ('单次公开验证/修复中位数', 'public_median_seconds'),
                       ('已测隐藏原生段＋机械绑定耗时', 'hidden_validation_seconds'),
                       ('每次成功交付成本：公开阶段', 'successful_delivery_seconds'),
                       ('每次成功交付成本：含自身隐藏验收', 'combined_successful_delivery_seconds')]:
        row(label, minutes(a['cost'][key]), minutes(b['cost'][key]))
    if disk is not None:
        def peak(arm):
            value = disk['arms'][arm]['largest_observed_per_pr_peak_bytes']
            return 'N/A（缺少完整窗口采样）' if value is None else f'{value/2**30:.3f} GiB'
        row('单 PR 最大采样分配字节峰值', peak('A'), peak('B'))
    text = '| 指标 | 对照：v12.6 + 共同修复 | 新版：v13.9 |\n| --- | ---: | ---: |\n' + '\n'.join(rows) + '\n'
    return text + ('\n误报占比为 FDF：已裁定错误缺陷告警 / 已裁定缺陷告警；未测量真阴性，不能称经典 FPR。'
                   '封存后告警不计作开发者检出或修复。未评估、未裁定和预先不适用分别保留。'
                   '公开阶段为既定 D0 入队到自身封存窗口；初版作者、设计、共同设施、初始参照、独立评审及匹配另列。'
                   '零完整交付时成功交付成本为 N/A。磁盘为指定窗口的非原子扫描观测，不是精确物理或瞬时峰值；各 PR 峰值没有相加。\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--a', required=True, type=Path); p.add_argument('--b', required=True, type=Path)
    p.add_argument('--disk', type=Path); p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    values = [json.loads(path.read_text()) for path in [args.a, args.b]]
    disk = json.loads(args.disk.read_text()) if args.disk else None
    result = table(*values, disk)
    with args.output.open('x') as stream: stream.write(result)


if __name__ == '__main__': main()
