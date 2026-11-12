"""Seal/clock ledger operations only. Product judgments are never synthesized."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re

from quality_clock import interval, point


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def ref(path):
    return {'path': str(Path(path)), 'sha256': sha(path)}


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(0o444)


def pinned(value):
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'} or sha(value['path']) != value['sha256']:
        raise ValueError('Exact original file reference differs')
    return load(value['path'])


def verify_seal(path, expected, group, judge, phase='cause'):
    path = Path(path)
    if path.is_symlink() or not re.fullmatch('[0-9a-f]{64}', expected) or sha(path) != expected:
        raise ValueError('External original grade seal pin differs')
    seal = load(path)
    kind = 'independent-blind-cause-grade-seal' if phase == 'cause' else 'independent-blind-alarm-grade-seal'
    if seal.get('version') != 1 or seal.get('kind') != kind or seal.get('anonymous_group') != group or seal.get('judge_id') != judge:
        raise ValueError('Independent grade scope/kind differs')
    members = {}
    for member in path.parent.rglob('*'):
        if member.is_symlink():
            raise ValueError('Grade output symlink is forbidden')
        if member.is_file() and member != path:
            members[member.relative_to(path.parent).as_posix()] = member
        elif not member.is_dir() and member != path:
            raise ValueError('Nonregular grade output member')
    if set(members) != set(seal['files']) or 'grade.json' not in members:
        raise ValueError('Every original grade output must be sealed')
    for name, value in seal['files'].items():
        relative = PurePosixPath(name)
        if (relative.is_absolute() or str(relative) != name or '..' in relative.parts or
                not re.fullmatch('[0-9a-f]{64}', value) or sha(members[name]) != value):
            raise ValueError('Original grade output pin differs')
        if members[name].stat().st_mode & 0o222:
            raise ValueError('Submitted grade output is not readonly')
    grade = load(members['grade.json'])
    if grade.get('anonymous_group') != group or grade.get('judge_id') != judge:
        raise ValueError('Grade body belongs to another context')
    return {'seal': ref(path), 'grade': ref(members['grade.json']), 'members': len(members)}


def correct_episode(episode, output=None, original_end=None):
    """Append a clock correction; retain original START/END and all judgments."""
    episode = Path(episode)
    start_path = episode / 'START.json'
    end_path = Path(original_end) if original_end else episode / 'END.json'
    start, end = load(start_path), load(end_path)
    correction = {'version': 1, 'kind': 'original-episode-append-only-clock-correction',
                  **point('recorded'), 'original_start': ref(start_path), 'original_end': ref(end_path),
                  'corrected_interval': interval(start, end),
                  'scope': 'Timing only. Original raw fields, outcomes, grades, source windows, criteria and denominators remain unchanged. Never use a cross-process process-relative monotonic delta as cost.'}
    destination = Path(output) if output else episode / 'CLOCK-CORRECTION.json'
    save(destination, correction)
    return {'correction': ref(destination), 'interval': correction['corrected_interval']}


def correct_split_cause(episode):
    """Correct a retained original-plus-supplement episode without regrading."""
    episode = Path(episode)
    aggregate_path = episode / 'END.json'
    aggregate = load(aggregate_path)
    first = pinned(aggregate['original_episode'])
    second = pinned(aggregate['complete_input_supplement_episode'])
    first_start_path = episode / 'START.json'
    first_start = load(first_start_path)
    second_start = pinned(second['start'])
    components = [interval(first_start, first), interval(second_start, second)]
    if any(not x['wall_clock_basis'].startswith('recorded Unix') for x in components):
        raise ValueError('This legacy split correction requires original Unix fallback episodes')
    wait = second_start['started_at_unix'] - first['finished_at_unix']
    if wait < 0:
        raise ValueError('Split episode order overlaps; retain discrepancy for explicit review')
    result = {'version': 1, 'kind': 'original-split-cause-append-only-clock-correction',
              **point('recorded'), 'original_aggregate': ref(aggregate_path),
              'original_first_start': ref(first_start_path), 'original_first_end': aggregate['original_episode'],
              'original_second_start': second['start'], 'original_second_end': aggregate['complete_input_supplement_episode'],
              'component_intervals': components, 'active_episode_wall_seconds': sum(x['wall_seconds'] for x in components),
              'inter_episode_research_wait_seconds': wait,
              'complete_span_seconds': second['finished_at_unix'] - first_start['started_at_unix'],
              'original_reported_active_seconds': aggregate.get('active_episode_wall_seconds'),
              'original_reported_wait_seconds': aggregate.get('inter_episode_research_wait_seconds'),
              'scope': 'Recorded Unix endpoints correct legacy cross-process monotonic arithmetic. Original episodes, grades and missing-input corrections remain retained; nonoverlapping active pair episodes counted once each and research wait separate. No quality or source-window change.'}
    destination = episode / 'CLOCK-CORRECTION.json'
    save(destination, result)
    return {'correction': ref(destination), 'active_seconds': result['active_episode_wall_seconds'], 'research_wait_seconds': wait}


def close_pair(episode, group, seals, *, phase='cause'):
    episode = Path(episode)
    start_path = episode / 'START.json'
    start = load(start_path)
    if start.get('anonymous_group') != group or start.get('judges') != ['J1', 'J2']:
        raise ValueError('Original two-context episode start differs')
    for name in ['packet_seal', 'complete_input', 'integrity']:
        if name in start:
            pinned(start[name])
    if set(seals) != {'J1', 'J2'}:
        raise ValueError('Exactly two independent sealed outputs required')
    verified = {judge: verify_seal(row['path'], row['sha256'], group, judge, phase)
                for judge, row in seals.items()}
    end = {'version': 2, 'kind': 'parallel-independent-' + phase + '-episode-end',
           'anonymous_group': group, 'judges': ['J1', 'J2'], 'status': 'sealed',
           'start': ref(start_path), 'outputs': verified, **point('finished'),
           'scope': 'Actual original START through two grade seals and integrity verification. Parallel pair wall is counted once. No quality decision or consensus is inferred from sealed outputs.'}
    measured = interval(start, end)
    end.update(wall_seconds=measured['wall_seconds'], wall_clock_basis=measured['wall_clock_basis'],
               interval_details=measured)
    destination = episode / 'END.json'
    save(destination, end)
    return {'end': ref(destination), 'wall_seconds': end['wall_seconds'], 'basis': end['wall_clock_basis']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    correction = commands.add_parser('correct-clock')
    correction.add_argument('--episode', required=True, type=Path)
    correction.add_argument('--output', type=Path)
    correction.add_argument('--original-end', type=Path)
    split = commands.add_parser('correct-split-cause-clock')
    split.add_argument('--episode', required=True, type=Path)
    pair = commands.add_parser('close-pair')
    pair.add_argument('--episode', required=True, type=Path)
    pair.add_argument('--group', required=True)
    pair.add_argument('--phase', choices=['cause', 'alarm'], default='cause')
    for judge in ['j1', 'j2']:
        pair.add_argument('--' + judge + '-seal', required=True, type=Path)
        pair.add_argument('--' + judge + '-sha256', required=True)
    args = parser.parse_args()
    if args.command == 'correct-clock':
        result = correct_episode(args.episode, args.output, args.original_end)
    elif args.command == 'correct-split-cause-clock':
        result = correct_split_cause(args.episode)
    else:
        result = close_pair(args.episode, args.group,
                            {'J1': {'path': args.j1_seal, 'sha256': args.j1_sha256},
                             'J2': {'path': args.j2_seal, 'sha256': args.j2_sha256}}, phase=args.phase)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
