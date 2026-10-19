#!/usr/bin/env python3
"""Fixed C01/initial overview chosen before final scores, never a pass claim."""
import json
from pathlib import Path

R = Path(__file__).resolve().parent
index = json.loads((R / 'report-index.json').read_text())
assert index['blindness_complete']
lines = ['# 固定场景图片对照', '',
         '选择规则在最终源码/保留场景披露前固定：C01 的第一个原生快照，两个平台、两组、前后阶段全部展示。图片保持原始文件；它们不是整体验收通过证明。缺图时保留失败日志链接，不以旧图补位。', '',
         '| 平台 / 组 | 首版 | 修复后 |', '| --- | --- | --- |']
for platform in ['android', 'ios']:
    for submission, label in sorted(index['arm_labels'].items()):
        cells = []
        for phase in ['d0', 'final']:
            folder = R / 'evidence' / phase / submission / platform / 'C01'
            observation = folder / 'observation.json'
            if observation.is_file() and json.loads(observation.read_text()).get('snapshots'):
                snapshot = json.loads(observation.read_text())['snapshots'][0]
                image = (folder / snapshot['screenshot']).relative_to(R).as_posix()
                cells.append(f'<a href="{image}"><img src="{image}" width="260" alt="{platform} {label} {phase} C01 initial"></a>')
            else:
                log = (folder / 'operator.log').relative_to(R).as_posix()
                cells.append(f'[截图不可用，保留原始日志]({log})')
        lines.append(f'| {platform} / {label} | ' + ' | '.join(cells) + ' |')
lines.extend(['', '完整场景/状态/方面结果见 [原子账本](assessment-ledger.csv)；采集失败、覆盖缺口、无法评估的方法保留在原始证据及独立评分中。', ''])
(R / 'GALLERY.md').write_text('\n'.join(lines))
print('Wrote fixed original-screenshot gallery; no UI judgement or image editing.')
