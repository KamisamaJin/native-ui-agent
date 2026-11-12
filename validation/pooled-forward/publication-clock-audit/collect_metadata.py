"""One-shot metadata-only snapshot, writes only the new explicit --output root.

No grade/output/claim/source/image ref is dereferenced. Public/control bodies
are not copied: only the below named clock/identity/source-ref keys are projected.
Allowed original episode START/END/CLOCK-CORRECTION bytes are copied unchanged.
"""
import argparse
import json
from pathlib import Path
import time

from clock_audit import SOURCE_PINS, TASKS, V2, V3, digest, need, parse

EVENT_KEYS = {'sequence', 'previous_sha256', 'kind', 'task', 'arm', 'action', 'request_id',
              'at_unix', 'at_clock', 'own_delivery_wall_seconds', 'source_sha256',
              'source_ref', 'source_lock', 'deadline_clock', 'deadline_at_unix'}
CONTROL_KEYS = {'version', 'kind', 'status', 'started_at_unix', 'started_at_monotonic',
                'finished_at_unix', 'finished_at_monotonic', 'at_unix', 'at_monotonic',
                'at_clock_gettime_monotonic', 'entry_wall_seconds', 'collector', 'scheduler'}
CONTROL_KEYS.add('runner')


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)
    path.chmod(0o444)


def build(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    need(root.is_dir() and not output.exists(), 'Original root required and snapshot must be fresh')
    output.mkdir(parents=True)
    refs = {}

    def copy(relative):
        p = root/relative
        need(p.is_file() and not p.is_symlink(), 'Missing/nonregular allowed metadata: '+relative)
        before = p.stat()
        data = p.read_bytes()
        after = p.stat()
        need((before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns), 'Metadata changed while reading')
        copy_name = 'raw/'+relative
        write(output/copy_name, data)
        refs[str(p)] = {'sha256': digest(data), 'copy': copy_name,
                        'observed_stat': {'inode': before.st_ino, 'size': before.st_size, 'mtime_ns': before.st_mtime_ns},
                        'copy_kind': 'byte-exact recorded clock/source metadata; refs remain opaque'}
        return {'path': str(p), 'sha256': digest(data)}

    for rel, expected in SOURCE_PINS.items():
        need(copy(rel)['sha256'] == expected, 'Frozen code/plan/manifest changed: '+rel)
    for task in TASKS:
        for arm in ['I', 'A', 'B']:
            for v in [1, 2, 3]:
                if v == 2 and (task, arm) not in V2 or v == 3 and (task, arm) not in V3:
                    continue
                base = 'cache/business/independent-evaluation/episodes/'+task+'/'+arm
                base += '/continuation' if v == 2 else '/remaining-first-execution-v3' if v == 3 else ''
                for name in ['START.json', 'END.json']:
                    copy(base+'/'+name)
    corrections = []
    for case in range(1, 6):
        for label in ['I', 'X', 'Y']:
            base = 'cache/business/blind-quality/episodes/Case'+str(case).zfill(2)+'-'+label+'/cause'
            for name in ['START.json', 'END.json']:
                copy(base+'/'+name)
            if (case, label) == (1, 'I'):
                copy(base+'/ORIGINAL-END.json')
                supplement = base.rsplit('/', 1)[0]+'/cause-supplement'
                for name in ['START.json', 'END.json']:
                    copy(supplement+'/'+name)
                corrections.append(copy(supplement+'/CLOCK-CORRECTION.json'))
            if label == 'I' and case in [1, 2]:
                corrections.append(copy(base+'/CLOCK-CORRECTION.json'))
    events, previous = [], None
    for i, p in enumerate(sorted((root/'cache/business/run-cohort2/events').glob('*.json'))):
        need(p.name == str(i).zfill(6)+'.json' and not p.is_symlink(), 'Event filename/regularity differs')
        data = p.read_bytes()
        value = parse(data)
        need(value['sequence'] == i and value['previous_sha256'] == previous, 'Original public raw event chain differs')
        previous = digest(data)
        events.append({'path': str(p), 'sha256': previous, 'clock_metadata': {k: value[k] for k in EVENT_KEYS if k in value}})
    controls = {}
    for version, folder, terminal in [(1, 'collection-operations', 'END.json'), (2, 'continuation-collection', 'FAILED.json'), (3, 'continuation-collection-v3', 'END.json')]:
        controls[str(version)] = {}
        for key, name in [('entry', 'ENTRY.json'), ('start', 'START.json'), ('terminal', terminal)]:
            p = root/'cache/business/independent-evaluation'/folder/name
            data = p.read_bytes()
            value = parse(data)
            controls[str(version)][key] = {'name': name, 'reference': {'path': str(p), 'sha256': digest(data)},
                                           'clock_metadata': {k: value[k] for k in CONTROL_KEYS if k in value},
                                           'metadata_counts': {k: len(value[k]) for k in ['retained_failed_acquisitions'] if k in value}}
    evidence = {'kind': 'independent-clock-metadata-snapshot-v1', 'original_root': str(root),
                'recorded_at_unix': time.time(), 'refs': refs, 'public_events': events,
                'collector_controls': controls, 'corrections': corrections,
                'projection_policy': {'public_event_keys': sorted(EVENT_KEYS), 'collector_control_keys': sorted(CONTROL_KEYS),
                                      'not_opened': 'No refs to grade/output/native outcome/service report/selfclaim/source/image/map bodies followed; original allowed START/END/correction records copied as bytes.'}}
    data = (json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
    write(output/'EVIDENCE.json', data)
    return {'evidence': str(output/'EVIDENCE.json'), 'sha256': digest(data), 'raw_copy_count': len(refs), 'public_clock_projection_count': len(events)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(build(args.root, args.output), sort_keys=True))
