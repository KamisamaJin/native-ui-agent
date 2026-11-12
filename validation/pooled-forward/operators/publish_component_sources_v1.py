"""Publish exact, post-reveal final component bytes for ordinary code review."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPARISON = ROOT / 'operators/cohort2/coordination/FINAL-PRODUCTION-SOURCE-COMPARISON-v1.json'
EXPECTED = '42159a800527bda433dd116f52235861f579a390758d70b96e421fdd09aab0ee'
NAMES = {'T1': 'CateringPackagePlanner', 'T2': 'TrainingPathwayEnrollment',
         'T3': 'SubscriptionCapacityChange', 'T4': 'VisitorAccessPreclearance',
         'T5': 'CandidateDispositionReview'}


def checked(reference):
    path = Path(reference['path'])
    if not path.is_absolute() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Unsafe source reference')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != reference['sha256']:
        raise ValueError('Source reference differs')
    return raw


def main():
    comparison_ref = {'path': str(COMPARISON), 'sha256': EXPECTED}
    comparison = json.loads(checked(comparison_ref))
    if comparison['all_five_final_sources_byte_identical'] is not True:
        raise ValueError('This shared final view requires all five exact A/B pairs')
    prepared = []
    for pair in comparison['records']:
        task = pair['task']
        manifests = {arm: json.loads(checked(pair['arms'][arm]['source_manifest'])) for arm in ['A', 'B']}
        if manifests['A']['files'] != manifests['B']['files'] or len(manifests['A']['files']) != 85:
            raise ValueError('Final production manifest pair differs')
        for platform, member in [('ios', '0/AlertToast/' + NAMES[task] + '.swift'),
                                 ('android', '1/java/com/example/reply/ui/components/business/' + NAMES[task] + '.kt')]:
            idx, relative = member.split('/', 1)
            original_refs = []
            candidates = []
            for arm in ['A', 'B']:
                manifest = manifests[arm]
                meta = manifest['files'][member]
                original = Path(manifest['roots'][int(idx)]['path']) / relative
                reference = {'path': str(original), 'sha256': meta['sha256']}
                raw = checked(reference)
                if len(raw) != meta['bytes']:
                    raise ValueError('Final source byte length differs')
                candidates.append(raw)
                original_refs.append({'arm': arm, 'manifest': pair['arms'][arm]['source_manifest'],
                                      'original': reference})
            if candidates[0] != candidates[1]:
                raise ValueError('Final component source pair differs')
            prepared.append((task, platform, Path(relative).name, candidates[0], original_refs))
    output = ROOT / 'production-examples'
    if output.exists():
        raise ValueError('Fresh publication view required')
    output.mkdir()
    rows = []
    for task, platform, name, raw, sources in prepared:
        target = output / task / platform / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        rows.append({'task': task, 'platform': platform, 'published': str(target.relative_to(ROOT)),
                     'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'originals': sources})
    manifest = {'version': 1, 'kind': 'post-reveal-exact-final-component-publication',
                'source_comparison': comparison_ref, 'files': rows,
                'scope': 'Exact final component byte copies. Both arms are identical for all five final production trees. This view is for review, not a new SUT, independent judgment, current build or evidence alias.'}
    (output / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    (output / 'README.md').write_text(
        '# 最终组件源码\n\n'
        '这里是五个任务最终新增组件的原字节副本，便于直接审查。两组最终全部85个生产源码成员均逐字节一致，因此每个平台只展示一份共享的最终组件。'
        '每份文件的 A/B 原始路径、源码清单和 SHA256 见 `MANIFEST.json`。\n\n'
        '这些副本在独立评审封存和揭盲后生成，未作为测试预期、评审引用或新的运行输入。'
        '它们不是可独立运行的完整应用；原项目、桥接、初版与每次原生证据的精确来源保存在出版归档中。\n\n'
        '研究新增代码使用仓库 MIT 许可；上游 Reply/AlertToast 许可见仓库 `THIRD_PARTY_NOTICES.md`。\n')
    print(json.dumps({'output': str(output), 'components': len(rows), 'paired_originals': 2 * len(rows)}))


if __name__ == '__main__':
    main()
