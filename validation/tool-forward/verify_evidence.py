#!/usr/bin/env python3
"""Cache-free checks of sealed trial inputs, complete grades and arithmetic.

Requires the final report-index.json. This script validates provenance and exact
denominators; it does not recreate the independent visual/semantic judgements.
"""
import hashlib
import json
from pathlib import Path

from metrics import index_grade
from verify_frozen import main as verify_frozen

R = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def portable_path(recorded):
    path = Path(recorded)
    if not path.is_absolute():
        return R / path
    marker = '/validation/tool-forward/'
    assert marker in recorded, 'Unmapped non-portable evidence path: ' + recorded
    return R / recorded.split(marker, 1)[1]


def validate_grade(path, phase, submission=None, legacy=False):
    grade = read(path)
    plan = read(R / 'private' / (phase + '-required-assessments.json'))
    expected = {(r['platform'], r['key']): r for r in plan['assessments']}
    actual = index_grade(grade)
    assert len(expected) == len(plan['assessments'])
    assert set(actual) == set(expected), str(path)
    assert grade['oracleSHA256'] == plan['oracle_sha256']
    assert grade['phase'] == phase.upper()
    checked = set()
    locators = {}
    for key, row in actual.items():
        required = expected[key]
        for field in ['expected', 'aspect', 'target', 'criterion']:
            assert row[field] == required[field], (path, key, field)
        assert row['sourceOnly'] == (required['scope'] == 'source')
        assert row['reason']
        if row['outcome'] in {'PASS', 'FAIL'}:
            assert row['exactSources'], (path, key, 'unsupported decision')
            if not row['sourceOnly']:
                assert row['bindingStatus'] == 'ESTABLISHED', (path, key, 'unbound runtime decision')
        for source in row['exactSources'] + row['consideredSources']:
            p = portable_path(source['path'])
            assert p.is_file(), (path, key, p)
            if submission is not None:
                parts = p.relative_to(R).parts
                if parts[0] == 'evidence':
                    assert parts[1:3] == (phase, submission), (path, key, 'wrong phase/arm evidence', p)
                    assert not legacy or row['sourceOnly'], (path, key, 'legacy runtime borrowed current collector evidence', p)
                if parts[0] == 'paired-evidence':
                    assert legacy and parts[1] == 'd0', (path, key, 'main grade borrowed legacy evidence', p)
                if parts[0] == 'implementations':
                    assert parts[1:3] == (phase, submission), (path, key, 'wrong production capsule', p)
            if 'sha256' in source and (str(p), source['sha256']) not in checked:
                assert sha(p) == source['sha256'], (path, key, p)
                checked.add((str(p), source['sha256']))
            if source.get('locator'):
                locators.setdefault(p, {})[json.dumps(source['locator'], sort_keys=True)] = source['locator']
    for p, values in locators.items():
        pointers = [v for v in values.values() if v['kind'] == 'json-pointer']
        if pointers:
            document = read(p)
            for locator in pointers:
                value = document
                pointer = locator['pointer']
                assert pointer == '' or pointer.startswith('/')
                for token in pointer.split('/')[1:] if pointer else []:
                    token = token.replace('~1', '/').replace('~0', '~')
                    value = value[int(token)] if isinstance(value, list) else value[token]
        lines = [v for v in values.values() if v['kind'] == 'lines']
        if lines:
            count = len(p.read_text().splitlines())
            assert all(1 <= v['start'] <= v.get('end', v['start']) <= count for v in lines)
        regions = [v for v in values.values() if v['kind'] == 'pixel-region']
        if regions:
            from PIL import Image
            with Image.open(p) as image:
                width, height = image.size
            assert all(v['x'] >= 0 and v['y'] >= 0 and v['width'] > 0 and v['height'] > 0
                       and v['x'] + v['width'] <= width and v['y'] + v['height'] <= height for v in regions)
    return len(actual)


def validate_captures(root, phase, submission=None, legacy=False):
    fixture_root = R / 'private/inputs' / phase
    fixture_manifest = read(fixture_root / 'manifest.json')
    cases = {r['case']: r for r in fixture_manifest['cases']}
    assert len(cases) == (6 if phase == 'd0' else 8)
    found = list(root.glob('*/*/capture.json'))
    assert len(found) == len(cases) * 2, str(root)
    snapshots = 0
    for platform in ['android', 'ios']:
        for case, entry in cases.items():
            folder = root / platform / case
            capture = read(folder / 'capture.json')
            spec = read(fixture_root / (case + '.json'))
            assert sha(fixture_root / (case + '.json')) == entry['sha256'] == capture['source_fixture_sha256']
            assert capture['action_protocol'] == spec['protocol']
            actions = [dict(a, type='capture') if legacy and a['type'] == 'sweep' else a for a in spec['actions']]
            assert capture['actual_actions'] == actions
            observation = folder / 'observation.json'
            if not observation.is_file():
                assert capture['status'] == 'unavailable'
                continue
            manifest = read(folder / 'manifest.json')
            assert manifest['native_test_count'] == 1
            # Native runners normalize the transport JSON, and Android merges
            # actions into fixtures. Compare values AND reconstruct the frozen
            # harness's exact original transport bytes, rather than assuming the
            # normalized archive has the original file's byte formatting.
            config = read(folder / 'fixtures.json')
            if platform == 'android':
                assert config.pop('actions') == actions
            else:
                assert read(folder / 'actions.json') == actions
            env = spec['environment']
            expected_config = {'initial': {'model': spec['model']},
                               'updates': [{'model': m} for m in spec.get('updates', [])],
                               'width': env['offeredWidth'], 'theme': env['appearance'],
                               'direction': env['layoutDirection'], 'fontScale': env['fontScale'],
                               'viewportHeight': 600, 'state_capture': spec.get('state_capture', True),
                               'max_scrolls': 80, 'required_identifiers': [],
                               'observation_targets': spec.get('observation_targets', []),
                               'canvas_color': '#101718' if env['appearance'] == 'dark' else '#FAF8F5',
                               'dynamic_type': {'large': 'large', 'extraExtraExtraLarge': 'xxxLarge',
                                                'accessibilityExtraExtraExtraLarge': 'accessibility5'}[env['appleContentSizeCategory']]}
            assert config == expected_config
            for kind, value in [('fixtures', expected_config), ('actions', actions)]:
                encoded = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()
                assert hashlib.sha256(encoded).hexdigest() == manifest['input_hashes'][kind]
            if submission:
                capsule = R / 'implementations' / phase / submission
                production = read(capsule / 'manifest.json')['files']
                hashes = manifest['source_hashes']
                for relative, digest in production.items():
                    prefix = 'reply/' if platform == 'android' else 'alerttoast/'
                    if not relative.startswith(prefix):
                        continue
                    suffix = '/' + relative[len(prefix):]
                    recorded = [v for k, v in hashes.items() if k.endswith(suffix)]
                    assert recorded == [digest], (folder, relative, recorded)
            data = read(observation)
            for snapshot in data['snapshots']:
                p = folder / snapshot['screenshot']
                assert p.is_file()
                assert manifest['image_hashes'][snapshot['screenshot']] == sha(p)
            snapshots += len(data['snapshots'])
    return len(found), snapshots


def main():
    index = read(R / 'report-index.json')
    verify_frozen()
    counts = []
    captures = snapshots = 0
    for submission, phases in index['grades'].items():
        for phase, entry in phases.items():
            p = R / entry['path']
            assert sha(p) == entry['sha256']
            counts.append(validate_grade(p, phase, submission))
            n, s = validate_captures(R / 'evidence' / phase / submission, phase, submission)
            captures += n
            snapshots += s
    n, s = validate_captures(R / 'paired-evidence/d0', 'd0', index['paired_submission'], True)
    captures += n
    snapshots += s
    paired = index['paired_grade']
    paired_path = R / paired['path']
    assert sha(paired_path) == paired['sha256']
    paired_assessments = validate_grade(paired_path, 'd0', index['paired_submission'], True)
    assert paired_assessments == 2209
    assert sorted(counts) == [2209, 2209, 2897, 2897]
    assert captures == 68
    print(json.dumps({'status': 'passed_complete_portable_trial', 'native_capture_attempts': captures,
                      'native_snapshots': snapshots, 'independent_assessments': sum(counts),
                      'same_source_paired_collector_assessments': paired_assessments,
                      'scope': 'Hashes, exact denominator and source/input bindings. Not a native SDK replay or new UI judgement.'}))


if __name__ == '__main__':
    main()
