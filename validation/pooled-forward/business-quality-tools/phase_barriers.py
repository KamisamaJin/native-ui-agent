"""Pure review-record barriers. Sealed review is not a product pass."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


GROUPS = {f'Case0{i}-{version}' for i in range(1, 6) for version in ['I', 'X', 'Y']}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def original(reader, ref):
    need(isinstance(ref, dict) and set(ref) == {'path', 'sha256'}, 'Exact recorded reference required')
    need(isinstance(ref['sha256'], str) and re.fullmatch('[0-9a-f]{64}', ref['sha256']), 'External SHA256 required')
    raw = reader.read_bytes(ref['path'])
    need(sha(raw) == ref['sha256'], 'Original review/input bytes differ')
    return json.loads(raw)


def verify_role_seal(reader, ref, group, judge, phase):
    seal = original(reader, ref)
    expected_kind = 'independent-blind-' + phase + '-grade-seal'
    need(seal.get('kind') == expected_kind and seal.get('version') == 1 and
         seal.get('anonymous_group') == group and seal.get('judge_id') == judge,
         'Independent role seal belongs to another scope or phase')
    root = Path(ref['path']).parent
    physical = reader.directory(str(root))
    members = {p.relative_to(physical).as_posix() for p in physical.rglob('*') if p.is_file()}
    need(members == set(seal['files']) | {'SEAL.json'} and 'grade.json' in seal['files'], 'Review output namespace differs')
    for name, expected in seal['files'].items():
        p = PurePosixPath(name)
        need(not p.is_absolute() and str(p) == name and '..' not in p.parts and '\\' not in name,
             'Unsafe review member')
        raw = reader.read_bytes(str(root / name))
        need(sha(raw) == expected, 'Original sealed review member differs')
    grade = reader.read_json(str(root / 'grade.json'))
    need(grade.get('anonymous_group') == group and grade.get('judge_id') == judge,
         'Review body context identity differs')
    return {'seal': ref, 'member_count': len(seal['files']),
            'grade': {'path': str(root / 'grade.json'), 'sha256': seal['files']['grade.json']}}


def verify_index(reader, ref, phase='cause'):
    need(phase in {'cause', 'alarm'}, 'Unknown review phase')
    index = original(reader, ref)
    need(index.get('version') == 1 and index.get('kind') == 'global-independent-' + phase + '-grade-barrier',
         'Wrong global review-record barrier')
    rows = index.get('groups')
    need(isinstance(rows, list) and len(rows) == 15 and {r['group'] for r in rows} == GROUPS,
         'All fifteen original anonymous versions are required')
    need(index.get('review_record_barrier_closed') is True and index.get('product_quality_verified') is False,
         'A record barrier must not assert product quality')
    cause_rows = None
    if phase == 'alarm':
        need(index.get('first_cause_barrier') is not None, 'Original complete first-cause barrier required')
        verify_index(reader, index['first_cause_barrier'], 'cause')
        cause_rows = {row['group']: row for row in original(reader, index['first_cause_barrier'])['groups']}
    actor_names = []
    verified = []
    for row in rows:
        group = row['group']
        need(set(row['actors']) == set(row['seals']) == {'J1', 'J2'}, 'Exactly two independent contexts per version')
        names = list(row['actors'].values())
        need(all(isinstance(v, str) and v.startswith('/root/') for v in names), 'Registered original context names required')
        actor_names.extend(names)
        need(row.get('fork_turns') == 'none' and row.get('model_override') is None,
             'Fresh inherited-model context declaration differs')
        if cause_rows is not None:
            need(row['actors'] == cause_rows[group]['actors'], 'Alarm judgments must use the original own-version contexts')
        need(isinstance(row.get('inputs'), list) and row['inputs'], 'Original immutable input references are required')
        matched_input = False
        for input_ref in row['inputs']:
            document = original(reader, input_ref)
            if document.get('kind') == 'anonymous-fixed-version-input-seal' and document.get('anonymous_group') == group:
                matched_input = True
        need(matched_input, 'Original own-version anonymous packet input seal is missing')
        end = original(reader, row['episode_end'])
        need(end.get('anonymous_group') == group, 'Original review episode belongs to another version')
        recorded = end.get('grade_seals')
        if recorded is None:
            recorded = {judge: item['seal'] for judge, item in end.get('outputs', {}).items()}
        need(recorded == row['seals'], 'Barrier changes original effective role seals')
        verified.append({'group': group, 'roles': {
            judge: verify_role_seal(reader, row['seals'][judge], group, judge, phase)
            for judge in ['J1', 'J2']}})
    need(len(actor_names) == len(set(actor_names)) == 30, 'A context must not grade a sibling version')
    return {'version': 1, 'status': 'verified', 'phase': phase, 'groups': 15,
            'distinct_contexts': 30, 'index': ref, 'verified_roles': verified,
            'scope': 'Recorded review/input/seal/context barrier only. No product pass, consensus, alarm truth, correspondence, delivery, SDK execution or mapping reveal is inferred.'}


def make_index(reader, rows, phase='cause', *, causal_predecessor=None, timestamp=None):
    """Build a value from explicit original role refs; caller pins saved bytes."""
    value = {'version': 1, 'kind': 'global-independent-' + phase + '-grade-barrier',
             'groups': rows, 'recorded_at': timestamp, 'review_record_barrier_closed': True,
             'product_quality_verified': False,
             'scope': 'All fifteen versions, two independent inherited-model contexts each; retained original judgments including false/unknown, without coordinator quality synthesis.'}
    if phase == 'alarm':
        need(causal_predecessor is not None, 'Complete first-cause barrier required before alarm barrier')
        verify_index(reader, causal_predecessor, 'cause')
        value['first_cause_barrier'] = causal_predecessor
    return value
