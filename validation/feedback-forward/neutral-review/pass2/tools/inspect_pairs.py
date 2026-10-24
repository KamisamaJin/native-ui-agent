from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import sys
import time
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parents[1]
NEUTRAL = BASE / 'neutral'
SNAPSHOT = BASE / 'development/candidate-attempt-1'
sys.path.insert(0, str(SNAPSHOT / 'scripts'))
import design_contract as design
import native_checks
import execution_plan

def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, v): (ROOT / name).write_text(json.dumps(v, indent=2, ensure_ascii=False) + '\n')

def make_sheet(name, cap, obs, selected, cols):
    width = 400 if obs['snapshots'][selected[0]]['viewport']['width'] == 400 else 280
    cell_width = int(width * 1.5) + 8
    canvas = Image.new('RGB', (cell_width * cols, 940 * math.ceil(len(selected) / cols)), 'white')
    draw = ImageDraw.Draw(canvas)
    refs = []
    for n, index in enumerate(selected):
        snap = obs['snapshots'][index]; vp = snap['viewport']
        path = cap / snap['screenshot']; im = Image.open(path).convert('RGB')
        left, top = (n % cols) * cell_width, (n // cols) * 940
        draw.text((left + 3, top + 8), f'{name} i{index}', fill='black')
        crop = im.crop((round(vp['x'] * 3), round(vp['y'] * 3), round((vp['x'] + vp['width']) * 3), round((vp['y'] + vp['height']) * 3)))
        canvas.paste(crop.resize((int(width * 1.5), 900)), (left, top + 35))
        refs.append({'index': index, 'state': snap.get('state_id'), 'png': str(path), 'sha256': sha(path)})
    out = ROOT / 'images' / (name + '.jpg'); canvas.save(out, quality=97)
    return {'sheet': str(out), 'sources': refs, 'transform': 'Measured viewport crop from original 3x PNG; 50% resize and labelled grid. Original PNGs remain acceptance evidence.'}

def main():
    begun = time.time()
    seal = load(NEUTRAL / 'SEAL.json'); approval = load(NEUTRAL / 'APPROVAL.json'); lock = load(NEUTRAL / 'design/lock.json')
    unchanged = {p: sha(NEUTRAL / p) == h for p, h in seal['source_and_test_inputs_sha256'].items()}
    assert all(unchanged.values())
    assert all(sha(Path(p)) == h for p, h in seal['snapshot_and_host_interface_sha256'].items())
    inputs = {str(NEUTRAL / 'SEAL.json'): sha(NEUTRAL / 'SEAL.json')}
    runs = []; sheets = []; colors = []
    for case in ['ordinary400', 'narrow280-large']:
        fixture = load(NEUTRAL / ('inputs/' + case + '.json'))
        fixtures = [fixture['initial'], *fixture['updates']]
        plan = load(NEUTRAL / 'generated' / case / 'design/plan.json')
        expected_input_hashes = [design.digest(f) for f in fixtures]
        for repeat in [1, 2]:
            for arm in ['legacy', 'coalesced']:
                name = f'{case}-r{repeat}-{arm}'; cap = BASE / 'neutral-captures' / name
                obs = load(cap / 'observation.json'); manifest = load(cap / 'manifest.json')
                execution = load(NEUTRAL / 'generated' / case / arm / 'execution.json')
                assert load(cap / 'fixtures.json') == execution['config']
                assert load(cap / 'actions.json') == execution['actions']
                assert sha(cap / 'compiled-project/Bridge.swift') == approval['bridge_sha256']
                for path in cap.rglob('*'):
                    if path.is_file(): inputs[str(path)] = sha(path)
                report = native_checks.evaluate(plan, obs, 'ios', root=cap, observation_sha256=sha(cap / 'observation.json'), design_lock=lock, design_sha256=approval['design_lock_sha256'])
                assert report == load(cap / 'automatic.json')
                save(name + '-native.json', report)
                receipt = execution_plan.coverage_receipt(execution, obs)
                assert receipt == load(cap / 'required-coverage.json')
                save(name + '-coverage.json', receipt)
                frame_rows = []
                for snap in obs['snapshots']:
                    binding = snap['binding']
                    assert binding['input_sha256'] == expected_input_hashes[binding['fixture_index']]
                    assert snap['binding_after_capture'] == binding and snap['capture_consistent'] is True
                    actual = snap['runtime']['actual_environment']
                    assert actual == {'direction': 'ltr', 'display_scale': 3, 'dynamic_type': fixture['dynamic_type'], 'theme': 'light'}
                    assert snap['viewport']['width'] == fixture['width'] and snap['viewport']['height'] == 600
                    image_sha = sha(cap / snap['screenshot'])
                    assert image_sha in manifest['image_hashes'].values()
                    assert len(snap['callbacks']) == binding['event_revision']
                    assert all(c['event'] == 'notes.reviewed.A' and c['fixture_index'] == 0 for c in snap['callbacks'])
                    frame_rows.append({'index': snap['index'], 'state': snap.get('state_id'), 'binding': binding, 'image_sha256': image_sha})
                state_rows = []
                target_style_frames = []
                for state in plan['states']:
                    evidence, complete, reason, _ = native_checks.bound_state_evidence(obs, state)
                    required = next(r for r in execution['required_coverage'] if r['state_id'] == state['id'])
                    targets = []
                    for target in required['targets']:
                        samples = []
                        for i, snap in evidence:
                            resolved = native_checks.resolve(snap, target, 'ios'); node = resolved.get('semantic', {})
                            if resolved.get('facts', {}).get('unique') and node.get('intersects_viewport'):
                                samples.append({'index': i, 'label': node.get('label'), 'fully_visible': node.get('fully_within_viewport'), 'frame': node.get('frame'), 'facts': resolved['facts']})
                        assert samples and any(s['fully_visible'] for s in samples)
                        targets.append({'selector': target, 'samples': samples})
                    assert len(targets) == 9
                    all_indices = [i for i, _ in evidence]
                    bindings = {design.digest(snap['binding']) for _, snap in evidence}
                    assert len(bindings) == 1
                    row = {'state': state['id'], 'required_scope': state['coverage'], 'complete': complete,
                           'reason': reason, 'indices': all_indices, 'targets': targets, 'binding': evidence[0][1]['binding']}
                    if state['coverage'] == 'full_content':
                        assert complete
                        intervals = []
                        for i, snap in evidence:
                            vp = snap['viewport']; content = snap['runtime']['content_frame']
                            offset = max(0, vp['y'] - content['y'])
                            intervals.append([offset, min(content['height'], offset + vp['height'])])
                        intervals.sort(); end = 0
                        for start, stop in intervals:
                            assert start <= end
                            end = max(end, stop)
                        assert intervals[0][0] == 0
                        native_state = next(s for s in obs['state_captures'] if s['state_id'] == state['id'])
                        assert end == native_state['content_height']
                        last = obs['snapshots'][all_indices[-1]]
                        sentinel = next(n for n in last['nodes'] if n.get('identifier') == '__observer.bottom')
                        assert sentinel['fully_within_viewport'] is True
                        row.update(raw_intervals=intervals, native_content_height_pt=end, viewport_count=end / 600, gap_pt=0, bottom_sentinel_snapshot=last['index'])
                        # Every remaining full sequence is inspected; pass1's already sealed r1 ordinary sequence is not duplicated.
                        if not (case == 'ordinary400' and repeat == 1):
                            cols, batch = (2, 4) if case == 'ordinary400' else (3, 6)
                            for pos in range(0, len(all_indices), batch):
                                sheets.append(make_sheet(f'{name}-{state["id"]}-{pos // batch}', cap, obs, all_indices[pos:pos + batch], cols))
                    else:
                        style = [next(s['index'] for s in t['samples'] if s['fully_visible']) for t in targets if t['selector']['identifier'] in ['notes.middle', 'notes.action']]
                        target_style_frames += style
                    state_rows.append(row)
                    # Store original action pixel diagnostics with no new acceptance-policy credit.
                    action_index = next(s['index'] for t in targets if t['selector']['identifier'] == 'notes.action' for s in t['samples'] if s['fully_visible'])
                    snap = obs['snapshots'][action_index]
                    node = next(n for n in snap['nodes'] if n.get('identifier') == 'notes.action')
                    f = node['image_frame']; box = (round(f['x'] + 30), round(f['y'] + 10), round(f['x'] + f['width'] - 30), round(f['y'] + f['height'] - 10))
                    im = Image.open(cap / snap['screenshot']).convert('RGB'); c = Counter(im.crop(box).getdata())
                    colors.append({'run': name, 'state': state['id'], 'index': action_index, 'png': str(cap / snap['screenshot']), 'png_sha256': sha(cap / snap['screenshot']), 'interior_box': box,
                        'colors': [{'rgb': '#%02X%02X%02X' % rgb, 'count': count} for rgb, count in c.most_common(5)]})
                if not (case == 'ordinary400' and repeat == 1):
                    sheets.append(make_sheet(name + '-targets', cap, obs, sorted(set(target_style_frames)), 2))
                events = []
                for index in [1, 2, 4]:
                    step = obs['steps'][index]
                    verdict = native_checks.callback_verdict(step, ['notes.reviewed.A'] if index == 1 else [], 'ios', stimulus='caller_update' if index == 2 else 'activation')
                    assert verdict['status'] == ('unassessed' if index == 4 else 'passed')
                    events.append({'action_index': index, 'outcome': step['outcome'], 'dispatch': step['dispatch'], 'callback_delta': step['callback_delta'], 'binding_after': step['binding_after'], 'immediate_after': step['immediate_after'], 'after': step['after'], 'callback_verdict': verdict})
                assert obs['issues'] == [] and obs['serialization_diagnostics'] == []
                runs.append({'name': name, 'case': case, 'repeat': repeat, 'arm': arm, 'native_counts': report['counts'],
                    'supported_statuses': {r['id']: r['status'] for r in report['assertions'] if r['status'] != 'unassessed'},
                    'required_coverage': receipt['satisfied'], 'states': state_rows, 'events': events, 'frames': frame_rows,
                    'actual_environment': manifest['actual_environment'], 'actual_viewport': manifest['actual_viewport'],
                    'native_test_count': manifest['native_test_count'], 'snapshot_count': len(obs['snapshots']),
                    'source_hashes': manifest['source_hashes'], 'timings': manifest['timings'], 'started_unix': manifest['started_at'], 'finished_unix': manifest['finished_at']})
    comparisons = []
    for case in ['ordinary400', 'narrow280-large']:
        group = [r for r in runs if r['case'] == case]
        baseline = group[0]['supported_statuses']
        assert all(r['supported_statuses'] == baseline for r in group)
        comparisons.append({'case': case, 'same_supported_assertion_id_status_map': True,
                            'native_supported_count': len(baseline), 'runs': [r['name'] for r in group],
                            'newly_missing_required_native_evidence': []})
    save('inputs-sha256.json', {'recorded_unix': begun, 'files': inputs})
    save('image-sheets.json', {'sheets': sheets})
    save('rendered-color-diagnostics.json', {'purpose': 'Original PNG diagnostic picking only; no independently frozen automatic pixel policy was added.', 'rows': colors})
    save('native-audit.json', {'version': 1, 'started_unix': begun, 'finished_unix': time.time(), 'frozen_neutral_files_unchanged': unchanged,
        'runs': runs, 'comparisons': comparisons, 'no_sdk_executed': True})
    print(json.dumps({'runs': len(runs), 'sheets': len(sheets), 'comparisons': comparisons}, indent=2))

if __name__ == '__main__': main()
