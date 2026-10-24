from pathlib import Path
import hashlib
import json
import time

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parents[1]
NEUTRAL = BASE / 'neutral'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def canonical_sha(v): return hashlib.sha256(json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def main():
    seal = load(NEUTRAL / 'SEAL.json')
    external = {name: sha(Path(name)) == expected for name, expected in seal['snapshot_and_host_interface_sha256'].items()}
    assert all(external.values())
    fixture = load(NEUTRAL / 'inputs/ordinary400.json')
    inputs = [fixture['initial'], *fixture['updates']]
    hashes = [canonical_sha(v) for v in inputs]
    rows = []
    for arm in ['legacy', 'coalesced']:
        cap = BASE / 'neutral-captures' / ('ordinary400-r1-' + arm)
        obs = load(cap / 'observation.json'); manifest = load(cap / 'manifest.json')
        image_map = manifest['image_hashes']
        frame_checks = []
        for snap in obs['snapshots']:
            binding = snap['binding']
            assert binding['input_sha256'] == hashes[binding['fixture_index']]
            assert snap['binding_after_capture'] == binding
            assert snap['capture_consistent'] is True
            actual = snap['runtime']['actual_environment']
            assert actual == {'direction': 'ltr', 'display_scale': 3, 'dynamic_type': 'large', 'theme': 'light'}
            assert snap['viewport'] == {'height': 600, 'width': 400, 'x': 1, 'y': 62}
            image_sha = sha(cap / snap['screenshot'])
            assert image_sha in image_map.values()
            frame_checks.append({'index': snap['index'], 'state': snap.get('state_id'), 'binding': binding, 'image_sha256': image_sha})
        state_rows = []
        for state in obs['state_captures']:
            if state['state_id'] not in ['ready', 'replaced']: continue
            intervals = []
            for index in state['snapshot_indices']:
                snap = obs['snapshots'][index]
                vp = snap['viewport']; content = snap['runtime']['content_frame']
                offset = max(0, vp['y'] - content['y'])
                intervals.append([offset, min(content['height'], offset + vp['height'])])
                assert snap['binding'] == state['binding']
            intervals.sort()
            end = 0
            for start, stop in intervals:
                assert start <= end, ('gap', state['state_id'], intervals)
                end = max(end, stop)
            assert intervals[0][0] == 0
            assert end == state['content_height']
            last = obs['snapshots'][state['snapshot_indices'][-1]]
            sentinel = next(n for n in last['nodes'] if n.get('identifier') == '__observer.bottom')
            assert sentinel['fully_within_viewport'] is True
            state_rows.append({'state': state['state_id'], 'binding': state['binding'], 'native_derived_intervals': intervals,
                'content_height_pt': end, 'viewport_count': end / 600, 'gap_pt': 0,
                'bottom_snapshot_index': last['index'], 'bottom_sentinel': sentinel})
        # All original callback receipt records agree with actual event_revision and caller input.
        for snap in obs['snapshots']:
            callbacks = snap['callbacks']
            assert len(callbacks) == snap['binding']['event_revision']
            assert all(c['event'] == 'notes.reviewed.A' and c['fixture_index'] == 0 for c in callbacks)
        rows.append({'arm': arm, 'all_snapshot_checks': frame_checks, 'raw_full_content_checks': state_rows,
                     'source_bridge_equal': sha(cap / 'compiled-project/Bridge.swift') == seal['bridge_sha256']})
    (ROOT / 'raw-audit.json').write_text(json.dumps({'version': 1, 'audited_unix': time.time(), 'source_input_epoch_hashes': hashes,
        'external_pins_unchanged': external, 'runs': rows,
        'scope': 'Independent raw snapshot/input/image association, runtime environment, callback receipt and interval calculation; no rounded or global-union substitution.'}, indent=2) + '\n')
    print('Raw input epochs, all frame/image bindings and full-content interval calculations verified.')

if __name__ == '__main__': main()
