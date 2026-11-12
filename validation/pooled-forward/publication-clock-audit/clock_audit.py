"""Read-only recorded-clock audit. No grades, SDKs, source domains, or billing.

API: audit(reader, evidence) -> JSON-compatible ledger. reader.read_bytes(path)
must resolve only explicit original keys; this module never opens those paths.
The CLI uses a byte-pinned owned snapshot, with no original-path fallback.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath

BASIS = 'clock_gettime(CLOCK_MONOTONIC)'
TASKS = ['T1', 'T2', 'T3', 'T4', 'T5']
V2 = {('T2', 'I'), ('T3', 'I'), ('T4', 'I'), ('T5', 'I'), ('T1', 'A'), ('T1', 'B')}
V3 = {('T1', 'B')} | {(t, a) for t in TASKS[1:] for a in ['A', 'B']}
SOURCE_PINS = {
    'business-quality-tools/quality_clock.py': '8a91e9d25574483b7c3275350c0b04b90cdb8f6cba5b91da041968a0a5e5a45c',
    'business-quality-tools/grade_records.py': '691ab8b1ca698fdcac235b6c79041684f90434abe47d5a235e838c8d4052f8e4',
    'business-quality-tools/test_quality_clock.py': 'd11a7d4d63d572c05bd6cf1e7e9ad9bcb161d76b39e61e49ba6fe6507dad2e51',
    'business-quality-tools/test_grade_records.py': '9b6fb3567f79e1ddd267105879603568b815baa35030e4c55a7e70998ea9549e',
    'business-quality-tools/CLOCK-LEDGER-FREEZE.json': '61fc5c1ee0df642d547a08c50628e1e99edfd3abebae122e15cbee1ab32ff6e1',
    'operators/cohort2/coordination/BLIND-GRADING-OPERATIONS-v1.json': '0f45872611981ac1aa354987952fa7353e61edaebb22f9a5df828728f68b88bc',
    'business-tools-v4/blind_study.py': '1a52cc62be5cee0bad34fefe8b54a7479761ca5ea5e8981937a8a1ad11ae6b05',
    'operators/cohort2/coordination/collect_independent.py': 'd80522b8bb620e7b0a58a5da4a9bdb566c15a78d6cd3a69b7619023c335b7047',
    'operators/cohort2/coordination/collect_independent_v2.py': '6d8cdda538e115d01fea2116d2bc9d4397867a4bfe80536e7226d0ec5b5dd8a2',
    'operators/cohort2/coordination/collect_independent_v3.py': '3f52be8628c483aee62690d89f93db0f59f497c0605fa60c233620befaf30641',
    'operators/cohort2/coordination/independent_native.py': '3c305880a818ab87c21c0c1043064b02af5991633efc7d3ab8d31405c4990a5d',
    'operators/cohort2/coordination/independent_native_v2.py': '7c8cf014299ea94db1646d22bd09be69040aaf183a10e50a7fd824126dbb02d2',
    'operators/cohort2/coordination/independent_native_v3.py': '7672ec99ca986a149d303eb8e37fb81da71edf1826c6eb1273da534945ddf722',
    'operators/cohort2/coordination/prepare_cause_dispatch.py': 'bd80a52d2581e09ec212268a70cda98083c75a5ce49c4d725f1069a014528d7d',
    'operators/cohort2/coordination/prepare_cause_dispatch_v2.py': '3af11ef0173b02bf5e772cbd9ee2911a5a430d1a3abe3575b15ba26a590cf52b',
    'cache/business/run-cohort2/manifest.json': '9d7edd73e19b2164915d99dc1b852eb14f66d2d85049cbc14dd5d4096ce39d83',
    'cache/business/run-cohort2/INIT.json': '63084cce8dbf160a3884d4751c3934afdfe9085192cb6e0338abe78067ef42a4',
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _pairs(items):
    out = {}
    for key, value in items:
        need(key not in out, 'Duplicate JSON key')
        out[key] = value
    return out


def parse(data):
    return json.loads(data, object_pairs_hook=_pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def pinned(reader, ref):
    need(type(ref) is dict and set(ref) == {'path', 'sha256'}, 'Exact original reference required')
    need(type(ref['path']) is str and ref['path'].startswith('/'), 'Absolute original key required')
    data = reader.read_bytes(ref['path'])
    need(digest(data) == ref['sha256'], 'Original reference byte pin differs: ' + ref['path'])
    return parse(data)


class SnapshotReader:
    """Only externally pinned exact-copy inventory entries, never live originals."""
    def __init__(self, root, entries):
        self.root = Path(root).resolve()
        self.entries = entries

    def read_bytes(self, original):
        need(original in self.entries, 'Unregistered original key: ' + original)
        row = self.entries[original]
        relative = PurePosixPath(row['copy'])
        need(not relative.is_absolute() and '..' not in relative.parts and str(relative) == row['copy'], 'Unsafe snapshot path')
        path = self.root.joinpath(*relative.parts)
        need(not path.is_symlink() and path.resolve().is_relative_to(self.root), 'Snapshot escape/symlink')
        data = path.read_bytes()
        need(digest(data) == row['sha256'], 'Snapshot copy byte pin differs')
        return data


def interval(start, end, *, mode):
    """Interpret an explicitly qualified pair; do not infer a process from numbers.

    Modes: helper (quality_clock point), v3 (source-pinned collector alias),
    same-parent (source/ENTRY bound collector context), legacy (cross CLI/adopted).
    Missing or invalid duration is N/A, with raw fields retained. A partial kernel
    pair falls back to Unix only when a complete ordered Unix pair is recorded.
    """
    need(mode in {'helper', 'v3', 'same-parent', 'legacy'}, 'Unknown qualification')
    a, b = start.get('started_at_unix'), end.get('finished_at_unix')
    ma, mb = start.get('started_at_monotonic'), end.get('finished_at_monotonic')
    result = {
        'qualification': mode, 'started_at_unix': a, 'finished_at_unix': b,
        'raw_started_at_monotonic': ma, 'raw_finished_at_monotonic': mb,
        'raw_process_monotonic_delta_seconds': mb - ma if finite(ma) and finite(mb) else None,
        'original_reported_wall_seconds': end.get('wall_seconds'),
        'unix_seconds': b - a if finite(a) and finite(b) else None,
        'duration_seconds': None, 'basis': None, 'status': 'unmeasured',
        'limitations': [], 'kernel_bounds_seconds': None,
    }
    unix_valid = finite(a) and finite(b) and b >= a
    shared = [(start.get('started_at_clock_gettime'), end.get('finished_at_clock_gettime')),
              (start.get('started_at_clock_gettime_monotonic'), end.get('finished_at_clock_gettime_monotonic'))]
    present = [x for x in shared if x[0] is not None and x[1] is not None]
    if len(present) == 2 and present[0] != present[1]:
        result.update(status='invalid', basis='conflicting shared endpoint aliases')
        return result
    chosen = shared[0] if mode == 'helper' else shared[1] if mode == 'v3' else (None, None)
    if chosen[0] is not None and chosen[1] is not None:
        first, last = chosen
        valid = finite(first) and finite(last) and last >= first
        if mode == 'helper':
            valid = valid and start.get('shared_clock_basis') == BASIS and end.get('shared_clock_basis') == BASIS
        if not valid:
            result.update(status='invalid', basis='inconsistent recorded shared endpoints')
            return result
        result.update(duration_seconds=last-first, basis=BASIS + ('; v3 source-pinned alias' if mode == 'v3' else ''), status='measured')
        result['raw_shared_endpoints'] = [first, last]
        if mode == 'helper':
            bounds = [start.get('started_shared_clock_bounds'), end.get('finished_shared_clock_bounds')]
            if all(type(x) is list and len(x) == 2 and all(finite(y) for y in x) and x[0] <= x[1] for x in bounds):
                if not (bounds[0][0] <= first <= bounds[0][1] and bounds[1][0] <= last <= bounds[1][1]):
                    result.update(status='invalid', duration_seconds=None, basis='endpoint outside recorded bracket')
                    return result
                result['kernel_bounds_seconds'] = [bounds[1][0]-bounds[0][1], bounds[1][1]-bounds[0][0]]
            elif any(x is not None for x in bounds):
                result.update(status='invalid', duration_seconds=None, basis='malformed shared-clock brackets')
                return result
    elif mode == 'same-parent':
        if finite(ma) and finite(mb) and mb >= ma:
            result.update(duration_seconds=mb-ma, basis='time.monotonic; source/ENTRY-bound same collector parent', status='measured')
            result['limitations'].append('Same-parent provenance is recorded collector control/source evidence; these legacy episodes have no per-endpoint PID.')
        else:
            result.update(status='invalid', basis='invalid same-parent process interval')
            return result
    elif unix_valid:
        result.update(duration_seconds=b-a, basis='recorded Unix fallback; no complete comparable shared pair', status='measured')
        result['limitations'].append('Assumes no intervening system-clock jump; cross-CLI/adopted process origins are not joined.')
    else:
        result['basis'] = 'no complete ordered comparable endpoint pair'
        if finite(a) and finite(b) and b < a:
            result['status'] = 'invalid'
        return result
    if not unix_valid:
        result['limitations'].append('Unix timeline placement unavailable/invalid; comparable duration does not repair wall timestamps.')
    if finite(result['unix_seconds']):
        result['selected_minus_unix_seconds'] = result['duration_seconds'] - result['unix_seconds']
    if finite(end.get('wall_seconds')):
        result['reported_minus_selected_seconds'] = end['wall_seconds'] - result['duration_seconds']
    return result


def union(intervals):
    """Finite ordered intervals, overlap counted once; negative never clamped."""
    rows = sorted(intervals)
    for a, b in rows:
        need(finite(a) and finite(b) and b >= a, 'Invalid union interval')
    merged = []
    for a, b in rows:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(b, merged[-1][1])
        else:
            merged.append([a, b])
    return {'seconds': sum(b-a for a, b in merged), 'intervals': merged,
            'overlap_seconds_not_added': sum(b-a for a, b in rows)-sum(b-a for a, b in merged)}


def summarize(rows):
    valid = [r for r in rows if r['interval']['status'] == 'measured']
    placed = [r for r in valid if finite(r['interval']['started_at_unix']) and finite(r['interval']['finished_at_unix']) and r['interval']['finished_at_unix'] >= r['interval']['started_at_unix']]
    coverage = union([(r['interval']['started_at_unix'], r['interval']['finished_at_unix']) for r in placed])
    all_placed = len(placed) == len(rows)
    no_overlap = coverage['overlap_seconds_not_added'] < 1e-7
    return {'segment_count': len(rows), 'measured_segment_count': len(valid),
            'active_seconds_nonoverlapping': sum(r['interval']['duration_seconds'] for r in valid) if all_placed and no_overlap else None,
            'recorded_unix_coverage': coverage,
            'limitation': 'Union placement uses recorded Unix and assumes no clock jump. Selected durations use each declared comparable clock. No overlapping selected durations are summed; no monetary/model cost inferred.'}


def gap(previous, following):
    a, b = previous['interval']['finished_at_unix'], following['interval']['started_at_unix']
    return {'from_segment': previous['id'], 'to_segment': following['id'],
            'started_at_unix': a, 'finished_at_unix': b,
            'seconds': b-a if finite(a) and finite(b) else None,
            'basis': 'recorded Unix inter-segment gap; shared research/wait, not allocated to an arm',
            'status': 'recorded' if finite(a) and finite(b) and b >= a else 'invalid-or-unknown'}


def future_cost():
    return {key: {'status': 'pending/not audited', 'seconds': None} for key in
            ['alarm_pair_episodes', 'final_binding_episodes', 'common_cause_matching', 'unrecorded_common_research']}


def check_correction(reader, ref):
    v = pinned(reader, ref)
    if v['kind'] == 'original-episode-append-only-clock-correction':
        start, end = pinned(reader, v['original_start']), pinned(reader, v['original_end'])
        recomputed = interval(start, end, mode='helper')
        need(recomputed['status'] == 'measured' and v['corrected_interval']['wall_seconds'] == recomputed['duration_seconds'], 'Clock correction duration differs')
        for name, expected in [('unix_wall_seconds', recomputed['unix_seconds']),
                               ('raw_process_monotonic_delta_not_comparable', recomputed['raw_process_monotonic_delta_seconds']),
                               ('original_reported_wall_seconds', end.get('wall_seconds'))]:
            need(v['corrected_interval'][name] == expected, 'Clock correction raw evidence differs: '+name)
        return {'reference': ref, 'kind': v['kind'], 'verified_seconds': recomputed['duration_seconds'],
                'original_reported_wall_seconds': end.get('wall_seconds')}
    need(v['kind'] == 'original-split-cause-append-only-clock-correction', 'Unknown clock correction')
    aggregate = pinned(reader, v['original_aggregate'])
    need(v['original_first_end'] == aggregate['original_episode'] and v['original_second_end'] == aggregate['complete_input_supplement_episode'], 'Split correction refs differ')
    a, b = pinned(reader, v['original_first_start']), pinned(reader, v['original_first_end'])
    c, d = pinned(reader, v['original_second_start']), pinned(reader, v['original_second_end'])
    need(d['start'] == v['original_second_start'], 'Supplement START pin differs')
    first, second = interval(a, b, mode='legacy'), interval(c, d, mode='legacy')
    need(first['status'] == second['status'] == 'measured', 'Split correction unmeasured')
    active = first['duration_seconds'] + second['duration_seconds']
    wait = c['started_at_unix'] - b['finished_at_unix']
    need(wait >= 0 and v['active_episode_wall_seconds'] == active and v['inter_episode_research_wait_seconds'] == wait and v['complete_span_seconds'] == d['finished_at_unix']-a['started_at_unix'], 'Split correction arithmetic differs')
    need([x['wall_seconds'] for x in v['component_intervals']] == [first['duration_seconds'], second['duration_seconds']], 'Split component durations differ')
    need(v['original_reported_active_seconds'] == aggregate.get('active_episode_wall_seconds') and v['original_reported_wait_seconds'] == aggregate.get('inter_episode_research_wait_seconds'), 'Split correction must preserve raw aggregate numbers')
    return {'reference': ref, 'kind': v['kind'], 'verified_seconds': active, 'research_wait_seconds': wait,
            'original_reported_active_seconds': aggregate.get('active_episode_wall_seconds'),
            'original_reported_wait_seconds': aggregate.get('inter_episode_research_wait_seconds')}


def audit(reader, evidence):
    need(evidence.get('kind') == 'independent-clock-metadata-snapshot-v1', 'Wrong evidence kind')
    root = evidence['original_root'].rstrip('/')
    refs = evidence['refs']

    def original(relative):
        key = root + '/' + relative
        need(key in refs, 'Required clock/source reference missing: ' + relative)
        return {'path': key, 'sha256': refs[key]['sha256']}

    def read(relative):
        return pinned(reader, original(relative))

    for relative, expected in SOURCE_PINS.items():
        ref = original(relative)
        need(ref['sha256'] == expected and digest(reader.read_bytes(ref['path'])) == expected, 'Frozen source/control pin differs: ' + relative)
    freeze = read('business-quality-tools/CLOCK-LEDGER-FREEZE.json')
    for name, expected in freeze['files'].items():
        if name.startswith('HOST/') or name == 'README.md':
            continue
        need(SOURCE_PINS['business-quality-tools/'+name] == expected, 'Clock freeze membership differs')
    initial = read('cache/business/run-cohort2/INIT.json')
    need(initial['helper_sha256'] == SOURCE_PINS['business-tools-v4/blind_study.py'] and initial['manifest_sha256'] == SOURCE_PINS['cache/business/run-cohort2/manifest.json'], 'Public INIT/controller/manifest binding differs')

    events = evidence['public_events']
    previous = None
    for i, item in enumerate(events):
        e = item['clock_metadata']
        need(e['sequence'] == i and e['previous_sha256'] == previous and item['path'] == root+'/cache/business/run-cohort2/events/'+str(i).zfill(6)+'.json', 'Public event clock projection chain differs')
        previous = item['sha256']
    public = []
    for task in TASKS:
        for arm in ['A', 'B']:
            own = [x for x in events if x['clock_metadata'].get('task') == task and x['clock_metadata'].get('arm') == arm]
            firsts = [x for x in own if x['clock_metadata']['kind'] == 'request_enqueued' and x['clock_metadata'].get('action') == 'diagnostic']
            seals = [x for x in own if x['clock_metadata']['kind'] == 'self_sealed']
            need(firsts and len(seals) == 1, 'Exact first D0 and unique public self-seal required')
            a, b = firsts[0], seals[0]
            start, end = a['clock_metadata'], b['clock_metadata']
            duration = interval({'started_at_unix': start['at_unix'], 'started_at_clock_gettime': start['at_clock'], 'shared_clock_basis': BASIS},
                                {'finished_at_unix': end['at_unix'], 'finished_at_clock_gettime': end['at_clock'], 'shared_clock_basis': BASIS, 'wall_seconds': end['own_delivery_wall_seconds']}, mode='helper')
            need(duration['status'] == 'measured', 'Public D0/self-seal interval invalid')
            reported = end['own_delivery_wall_seconds']
            need(finite(reported) and reported >= 0 and reported <= duration['duration_seconds'], 'Reported public pre-append sample outside interval')
            public.append({'id': 'public/'+task+'/'+arm, 'task': task, 'arm': arm, 'interval': duration,
                           'd0': {'path': a['path'], 'sha256': a['sha256']}, 'self_seal': {'path': b['path'], 'sha256': b['sha256']},
                           'reported_own_wall_seconds': reported,
                           'self_seal_append_after_reported_sample_seconds': duration['duration_seconds']-reported,
                           'interpretation': 'Source samples reported own wall before append reads the event chain and samples the self-seal timestamp; both endpoints retained, no reset.'})

    controls = evidence['collector_controls']
    control_by_version = {}
    for version in [1, 2, 3]:
        row = controls[str(version)]
        a, b = row['entry']['clock_metadata'], row['terminal']['clock_metadata']
        source = 'operators/cohort2/coordination/collect_independent'+('' if version == 1 else '_v'+str(version))+'.py'
        need(a['scheduler' if version == 1 else 'collector'] == original(source), 'Collector ENTRY source binding differs')
        if version == 1:
            need(row['start']['clock_metadata']['runner'] == original('operators/cohort2/coordination/independent_native.py'), 'Original collector runner source pin differs')
        start = {'started_at_unix': a.get('started_at_unix', a.get('at_unix')),
                 'started_at_monotonic': a.get('started_at_monotonic', a.get('at_monotonic')),
                 'started_at_clock_gettime_monotonic': a.get('at_clock_gettime_monotonic')}
        end = {'finished_at_unix': b.get('finished_at_unix', b.get('at_unix')),
               'finished_at_clock_gettime_monotonic': b.get('at_clock_gettime_monotonic'),
               'wall_seconds': b.get('entry_wall_seconds')}
        duration = interval(start, end, mode='v3' if version == 3 else 'legacy')
        control_by_version[version] = {'version': version, 'entry': row['entry']['reference'], 'terminal': row['terminal']['reference'],
                                      'terminal_name': row['terminal']['name'], 'interval': duration,
                                      'reported_same_parent_entry_wall_seconds': b.get('entry_wall_seconds'),
                                      'retained_failed_acquisition_count': row['terminal'].get('metadata_counts', {}).get('retained_failed_acquisitions'),
                                      'interpretation': 'Parent control includes nested episodes; never add it to them. v2 reported entry wall is one same-parent sample; Unix placement is separate.'}

    private, private_groups, continuation_gaps = [], [], []
    for task in TASKS:
        for arm in ['I', 'A', 'B']:
            segments = []
            for version in [1, 2, 3]:
                if version == 2 and (task, arm) not in V2 or version == 3 and (task, arm) not in V3:
                    continue
                base = 'cache/business/independent-evaluation/episodes/'+task+'/'+arm
                base += '/continuation' if version == 2 else '/remaining-first-execution-v3' if version == 3 else ''
                a, b = read(base+'/START.json'), read(base+'/END.json')
                need((a['task'], a['arm']) == (task, arm) and b['start'] == original(base+'/START.json'), 'Private episode scope/START pin differs')
                if version == 1:
                    need((b['task'], b['arm']) == (task, arm), 'Private END scope differs')
                mode = 'legacy' if version == 1 and (task, arm) == ('T1', 'I') else 'v3' if version == 3 else 'same-parent'
                duration = interval(a, b, mode=mode)
                need(duration['status'] == 'measured', 'Private episode invalid/unmeasured')
                context = control_by_version[version]['interval']
                if mode != 'legacy':
                    need(context['started_at_unix'] <= a['started_at_unix'] <= b['finished_at_unix'] <= context['finished_at_unix'], 'Private interval outside source-bound collector control')
                if version > 1:
                    need(a['original_start'] == original('cache/business/independent-evaluation/episodes/'+task+'/'+arm+'/START.json'), 'Continuation original START differs')
                    key = 'original_resource_closed_end' if version == 2 else 'original_failed_end'
                    need(a[key] == original('cache/business/independent-evaluation/episodes/'+task+'/'+arm+'/END.json'), 'Continuation original END differs')
                if version == 3 and (task, arm) == ('T1', 'B'):
                    need(a['previous_continuation_end'] == original('cache/business/independent-evaluation/episodes/T1/B/continuation/END.json'), 'Failed v2 END continuation pin differs')
                if version == 1 and mode != 'legacy':
                    need(a['kind'] == 'independent-native-episode-start', 'Same-parent original START not collector-created')
                row = {'id': 'private/'+task+'/'+arm+'/v'+str(version), 'task': task, 'arm': arm, 'collector_version': version,
                       'status': b.get('status'), 'start': original(base+'/START.json'), 'end': original(base+'/END.json'), 'interval': duration,
                       'collector_entry': control_by_version[version]['entry'],
                       'source': original('operators/cohort2/coordination/collect_independent'+('' if version == 1 else '_v'+str(version))+'.py')}
                if version == 2:
                    row['original_cross_parent_inter_episode_wait_seconds_not_duration'] = a['inter_episode_wait_seconds']
                if 'adopted_first_operation' in b:
                    row['original_clamped_cross_origin_adoption_gap_not_duration'] = b['adopted_first_operation'].get('post_first_operation_adoption_gap_seconds')
                segments.append(row)
                private.append(row)
            gaps = [gap(a, b) for a, b in zip(segments, segments[1:])]
            continuation_gaps.extend(gaps)
            private_groups.append({'task': task, 'arm': arm, 'segments': [x['id'] for x in segments], 'summary': summarize(segments), 'shared_gaps_not_arm_cost': gaps})
    need(len(private) == 30 and len(private_groups) == 15, 'All private original and licensed segments required')
    need(next(x for x in private if x['id'] == 'private/T1/B/v2')['status'] == 'failed', 'Retained failed T1/B v2 segment required')

    cause, cause_groups = [], []
    for case in range(1, 6):
        for label in ['I', 'X', 'Y']:
            group = 'Case'+str(case).zfill(2)+'-'+label
            base = 'cache/business/blind-quality/episodes/'+group+'/cause'
            a, end_index = read(base+'/START.json'), read(base+'/END.json')
            need(a['anonymous_group'] == group and a['judges'] == ['J1', 'J2'], 'Cause START group/pair differs')
            refs_for_segments = [(original(base+'/START.json'), original(base+'/END.json'))]
            aggregate_ref = None
            if group == 'Case01-I':
                need(end_index['kind'] == 'independent-cause-version-final-seal-index', 'Original split cause index required')
                aggregate_ref = original(base+'/END.json')
                original_end = original(base+'/ORIGINAL-END.json')
                supplement = base.rsplit('/', 1)[0]+'/cause-supplement'
                need(end_index['original_episode'] == original_end and end_index['complete_input_supplement_episode'] == original(supplement+'/END.json'), 'Retained split cause refs differ')
                refs_for_segments = [(original(base+'/START.json'), original_end), (original(supplement+'/START.json'), original(supplement+'/END.json'))]
            segments = []
            for index, (ar, br) in enumerate(refs_for_segments):
                start, end = pinned(reader, ar), pinned(reader, br)
                need(start['anonymous_group'] == group and end['anonymous_group'] == group and end['start'] == ar, 'Cause component scope/START pin differs')
                mode = 'helper' if 'started_at_clock_gettime' in start else 'legacy'
                duration = interval(start, end, mode=mode)
                need(duration['status'] == 'measured', 'Cause interval invalid/unmeasured')
                row = {'id': 'cause/'+group+'/'+str(index+1), 'anonymous_group': group, 'anonymous_label': label,
                       'start': ar, 'end': br, 'interval': duration, 'parallel_actor_count': 2,
                       'wall_counting': 'Pair START to pair END counted once; no multiplication by two.'}
                cause.append(row)
                segments.append(row)
            cause_groups.append({'anonymous_group': group, 'anonymous_label': label, 'aggregate_end': aggregate_ref,
                                 'segments': [x['id'] for x in segments], 'summary': summarize(segments),
                                 'research_gaps': [gap(a, b) for a, b in zip(segments, segments[1:])]})
    need(len(cause_groups) == 15 and len(cause) == 16, 'All fifteen cause pairs and retained supplement required')
    corrections = [check_correction(reader, x) for x in evidence['corrections']]
    need(len(corrections) == 3, 'Retained original I1 aggregate/supplement and I2 corrections required')

    for version, control in control_by_version.items():
        nested = [x for x in private if x['collector_version'] == version]
        coverage = summarize(nested)['recorded_unix_coverage']
        a, b = control['interval']['started_at_unix'], control['interval']['finished_at_unix']
        clipped = [(max(a, x['interval']['started_at_unix']), min(b, x['interval']['finished_at_unix'])) for x in nested
                   if x['interval']['finished_at_unix'] >= a and x['interval']['started_at_unix'] <= b]
        nested_seconds = union(clipped)['seconds']
        control['nested_episode_unix_union_inside_control_seconds'] = nested_seconds
        control['parent_unix_wait_overhead_outside_nested_seconds'] = b-a-nested_seconds
        control['nested_union_including_preentry_adopted_interval'] = coverage

    timeline_rows = public+private+cause
    ordered = sorted(timeline_rows, key=lambda x: x['interval']['started_at_unix'])
    overall = summarize(ordered)['recorded_unix_coverage']
    between = [{'started_at_unix': a[1], 'finished_at_unix': b[0], 'seconds': b[0]-a[1],
                'interpretation': 'Uncovered elapsed Unix wall between these selected records; activity/actor/money attribution unknown, not measured research labor.'}
               for a, b in zip(overall['intervals'], overall['intervals'][1:])]
    return {'kind': 'independent-recorded-clock-cost-ledger-v1',
            'scope': 'Recorded clock/provenance correctness only. No grades, delivery verdicts, product comparison, mapping, source/image bodies or billing read.',
            'counts': {'public_delivery_scopes': len(public), 'private_task_arm_groups': len(private_groups), 'private_active_segments_including_failed': len(private), 'anonymous_cause_groups': len(cause_groups), 'cause_active_pair_segments_including_supplement': len(cause)},
            'public': public, 'public_by_arm': {a: summarize([x for x in public if x['arm'] == a]) for a in ['A', 'B']},
            'private': private, 'private_groups': private_groups,
            'private_by_arm': {a: summarize([x for x in private if x['arm'] == a]) for a in ['I', 'A', 'B']},
            'cause_pairs': cause, 'cause_groups': cause_groups,
            'all_cause_pair_serialization': summarize(cause),
            'cause_by_anonymous_label': {a: summarize([x for x in cause if x['anonymous_label'] == a]) for a in ['I', 'X', 'Y']},
            'collector_controls_not_additional_cost': list(control_by_version.values()), 'clock_corrections': corrections,
            'shared_continuation_gaps_not_added_or_allocated': continuation_gaps,
            'all_categories_unix_union_not_sum': overall, 'uncovered_intervals_between_recorded_episodes': between,
            'future_or_unmeasured_work': future_cost(),
            'unmeasured': {'model_billing': None, 'model_tokens': None, 'monetary_human_labor': None, 'disk_peak_cost': None},
            'limitations': ['No delivery-success denominator is read; no cost per complete delivery or treatment ratio is computed.',
                            'Shared gaps can overlap other recorded actors and each other; they are listed, never summed or assigned to A/B/X/Y.',
                            'Raw negative/zero/reported clocks remain original evidence; corrections do not reset native/public source windows.',
                            'No boot/session identifier is recorded. Cross-process kernel continuity is the recorded same-host cohort assumption, not a current freshness claim.',
                            'Snapshot byte pins bind recorded evidence, not present runtime behavior. Future alarm/binding episodes remain pending.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--evidence-sha256', required=True)
    args = parser.parse_args()
    raw = args.evidence.read_bytes()
    need(digest(raw) == args.evidence_sha256, 'External evidence pin differs')
    evidence = parse(raw)
    result = audit(SnapshotReader(args.evidence.parent, evidence['refs']), evidence)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
