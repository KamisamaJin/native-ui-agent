#!/usr/bin/env python3
"""Describe every sealed panel disagreement; never adjudicate or rescore one."""
import argparse
from functools import lru_cache
from pathlib import Path
import experiment as ex
import evaluation_adapter as evaluation

R = Path(__file__).resolve().parent


@lru_cache(None)
def state_images(phase, task, alias, platform, case, state_id):
    base = R / 'evaluation-inputs' / phase / task / alias / platform / case
    meta = ex.read(base / 'inputs.json')
    plan = ex.read(base / 'plan.json')
    state = next(v for v in plan['states'] if v['id'] == state_id)
    found, complete, reason, _ = evaluation.native.bound_state_evidence(
        ex.read(R / meta['observation']), state)
    images = sorted({ex.sha(R / meta['root'] / s['screenshot'])
                     for _, s in found if s.get('screenshot') and
                     (R / meta['root'] / s['screenshot']).is_file()})
    return {'imageSHA256Set': images, 'complete': complete, 'reason': reason}


def render():
    ex.gate.authorize(R / 'gates', 'reveal', R)
    sections = []
    for phase in ['d0', 'final']:
        for path in sorted((R / 'evaluation' / phase).glob('*/*/*/*/acceptance.json')):
            task, alias, platform, case = path.parts[-5:-1]
            for row in ex.read(path)['rows']:
                if not row['panel_disagreement']:
                    continue
                sections += ['## ' + '/'.join([phase, task, alias, platform, case, row['id']]),
                             '[Unchanged acceptance row](' + str(path.relative_to(R)) + ')',
                             'Merged status: **' + row['status'] + '**. No tie-breaker was used.']
                for panel, judgment in zip(['one', 'two'], row['judges']):
                    link = '/'.join(['judgments', phase, panel, task, alias, platform, case, 'judge.json'])
                    sections += ['### Panel ' + panel + ' — ' + judgment['status'],
                                 judgment.get('reason', '').replace('\n', ' '),
                                 '[Original sealed judgment](' + link + ')']
                if case in ['P1', 'P2']:
                    paths = [R / 'evaluation' / stage / task / alias / platform / case / 'acceptance.json'
                             for stage in ['d0', 'final']]
                    statuses = [next(v['status'] for v in ex.read(p)['rows'] if v['id'] == row['id'])
                                for p in paths]
                    corpora = [ex.read(R / 'common-corpora' / task / alias / stage / 'corpus.json')
                               for stage in ['d0', 'final']]
                    runs = [next(v for v in c['platformRuns'][platform] if v['case'] == case)
                            for c in corpora]
                    evidence = [state_images(stage, task, alias, platform, case, row['state'])
                                for stage in ['d0', 'final']]
                    equal_images = bool(evidence[0]['imageSHA256Set']) and (
                        evidence[0]['imageSHA256Set'] == evidence[1]['imageSHA256Set'])
                    sections += ['D0 → FINAL status: `' + ' → '.join(statuses) + '`; '
                                 'entire production source unchanged: **' + str(corpora[0]['source'] == corpora[1]['source']) + '**; '
                                 'fixture/action/bridge launch hashes unchanged: **' + str(runs[0]['inputHashes'] == runs[1]['inputHashes']) + '**; '
                                 'recorded coherent-state PNG SHA sets identical: **' + str(equal_images) + '**; '
                                 'full-content coverage D0 / FINAL: **' + ' / '.join(str(v['complete']) for v in evidence) + '**.']
    count = sum(s.startswith('## ') for s in sections)
    return '\n\n'.join([
        '# Preserved qualitative disagreements',
        f'{count} sealed qualitative panel disagreements across D0 and FINAL. This is a '
        'post-acquisition, unscored descriptive index of every disagreement; it does not '
        'change expectations, original claims, acceptance, causes or metric denominators.',
        'Both opinions remain visible. A screenshot/source/launch equality comparison '
        'describes evidence stability, not which opinion is correct. Identical visual '
        'evidence can still receive different model interpretations. Missing coverage '
        'is a separate limitation, and AI agreement can share systematic errors. '
        'No extra SDK acquisition or third-judge override was performed.',
        *sections,
        '[Frozen metrics](TABLES.md) · [Failure index](FAILURES.json) · [Reliability limits](ENGINEERING.md)'
    ]) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    content = render()
    path = R / 'DISAGREEMENTS.md'
    if args.check:
        assert path.read_text() == content
    else:
        assert not path.exists()
        path.write_text(content)
    print('PASS preserved qualitative disagreement index (no rescoring)')


if __name__ == '__main__':
    main()
