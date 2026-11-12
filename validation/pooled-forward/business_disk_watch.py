#!/usr/bin/env python3
"""Sample each arm's positively declared study storage, without SDK commands.

Request directories are attributed by the controller's append-only enqueue events,
never by inspecting hidden designs or guessing process/device ownership. The
unchanged enclosing whole-study meter remains responsible for resource limits.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
from measure import Meter


def read(path):
    return json.loads(Path(path).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--stop', required=True, type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    manifest = read(run / 'manifest.json')
    base = {}
    for task in manifest['tasks']:
        for alias, arm in task['arms'].items():
            key = task['id'] + '/' + alias
            workspace = Path(arm['workspace']).resolve()
            # All private per-arm roots (sources, profiles, reviews, workflow,
            # resources) live under this positive, explicitly declared arm root.
            arm_root = workspace.parent
            if arm_root.name != alias or arm_root.parent.name != task['id']:
                raise ValueError('Explicit task/arm/workspace layout required for disk attribution')
            journals = [str(Path(v) / 'journal.json') for v in arm['resource_roots']]
            base[key] = {'paths': [str(arm_root), str(run / 'arms' / task['id'] / alias)],
                         'resource_journals': journals}
    spec = {'sample_seconds': 2, 'max_total_allocated_bytes': 32 * 2**30,
            'min_free_bytes': 5 * 2**30, 'filesystem_root': str(run), 'groups': base}
    admission = {'version': 1, 'manifest_sha256': hashlib.sha256((run / 'manifest.json').read_bytes()).hexdigest(),
                 'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 'base_spec': spec, 'request_attribution': 'original request_enqueued task/arm/request_id',
                 'scope': 'Sampled allocated private study bytes and journal-declared simulator directories; not exact transient/APFS/shared-SDK physical peak. Group peaks need not coincide. No hidden design inputs opened.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.with_suffix('.admission.json').open('x') as stream:
        json.dump(admission, stream, indent=2)
    attributed = set()
    with Meter(spec, args.output) as meter:
        args.output.with_suffix('.ready').write_text(str(time.time()) + '\n')
        while not args.stop.exists():
            events = sorted((run / 'events').glob('*.json'))
            with meter.lock:
                for path in events:
                    if path.name in attributed:
                        continue
                    event = read(path)
                    if event['kind'] == 'request_enqueued':
                        key = event['task'] + '/' + event['arm']
                        request = event['request_id']
                        if len(request) != 32 or any(c not in '0123456789abcdef' for c in request):
                            raise ValueError('Invalid original controller request identity')
                        meter.groups[key]['paths'].append(str(run / 'requests' / request))
                    attributed.add(path.name)
            if meter.error:
                raise RuntimeError(meter.error)
            time.sleep(.5)


if __name__ == '__main__':
    main()
