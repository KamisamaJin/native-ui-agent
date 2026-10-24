from pathlib import Path
import copy
import hashlib
import json
import sys
import time
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parents[1]
NEUTRAL = BASE / 'neutral'
SNAPSHOT = BASE / 'development/candidate-attempt-1'
sys.path.insert(0, str(SNAPSHOT / 'scripts'))
import design_contract as design
import execution_plan
import native_checks

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads(path.read_text())
def save(name, value): (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def main():
    begun = time.time()
    seal = load(NEUTRAL / 'SEAL.json')
    checks = {name: sha(NEUTRAL / name) == expected for name, expected in seal['source_and_test_inputs_sha256'].items()}
    assert all(checks.values())
    lock = load(NEUTRAL / 'design/lock.json')
    approval = load(NEUTRAL / 'APPROVAL.json')
    plan = load(NEUTRAL / 'generated/ordinary400/design/plan.json')
    design.verify_generated(plan, lock, approval['design_lock_sha256'], 'ios')
    all_results = []
    input_map = {str(NEUTRAL / 'SEAL.json'): sha(NEUTRAL / 'SEAL.json')}
    for arm in ['legacy', 'coalesced']:
        cap = BASE / 'neutral-captures' / ('ordinary400-r1-' + arm)
        obs = load(cap / 'observation.json'); manifest = load(cap / 'manifest.json')
        execution = load(NEUTRAL / ('generated/ordinary400/' + arm + '/execution.json'))
        assert load(cap / 'fixtures.json') == execution['config']
        assert load(cap / 'actions.json') == execution['actions']
        assert sha(cap / 'compiled-project/Bridge.swift') == approval['bridge_sha256']
        for path in cap.rglob('*'):
            if path.is_file(): input_map[str(path)] = sha(path)
        report = native_checks.evaluate(plan, obs, 'ios', root=cap,
            observation_sha256=sha(cap / 'observation.json'), design_lock=lock, design_sha256=approval['design_lock_sha256'])
        save(arm + '-recomputed-automatic.json', report)
        assert report == load(cap / 'automatic.json')
        receipt = execution_plan.coverage_receipt(execution, obs)
        save(arm + '-recomputed-coverage.json', receipt)
        assert receipt == load(cap / 'required-coverage.json')
        states = []
        image_catalog = []
        for state in plan['states']:
            evidence, complete, reason, _ = native_checks.bound_state_evidence(obs, state)
            bindings = []
            target_rows = []
            for target in next(r for r in execution['required_coverage'] if r['state_id'] == state['id'])['targets']:
                rows = []
                for index, snap in evidence:
                    resolved = native_checks.resolve(snap, target, 'ios')
                    semantic = resolved.get('semantic', {})
                    if resolved.get('facts', {}).get('unique') and semantic.get('intersects_viewport'):
                        rows.append({'index': index, 'fully_within_viewport': semantic.get('fully_within_viewport'),
                                     'label': semantic.get('label'), 'enabled': resolved.get('facts', {}).get('enabled'),
                                     'frame': semantic.get('frame'), 'capture_consistent': snap.get('capture_consistent')})
                assert rows
                target_rows.append({'selector': target, 'observations': rows})
            for index, snap in evidence:
                image_path = cap / snap['screenshot']
                assert image_path.is_file()
                assert snap['capture_consistent'] is True
                assert snap['binding'] == snap['binding_after_capture']
                with Image.open(image_path) as im:
                    assert im.size == (1206, 2622)
                row = {'state': state['id'], 'snapshot_index': index, 'name': snap['name'],
                       'source_png': str(image_path), 'sha256': sha(image_path), 'binding': snap['binding'],
                       'runtime': snap['runtime'], 'viewport': snap['viewport']}
                image_catalog.append(row); bindings.append(snap['binding'])
            assert len({design.digest(b) for b in bindings}) == 1
            states.append({'state_id': state['id'], 'required_scope': state['coverage'], 'complete': complete,
                           'reason': reason, 'indices': [i for i, _ in evidence], 'binding': bindings[0], 'targets': target_rows})
            # Supplemental readable sheets crop only the measured viewport; originals remain evidence.
            indices = [i for i, _ in evidence]
            selected = indices if state['coverage'] == 'full_content' else sorted(set(next(i['index'] for i in row['observations'] if i['fully_within_viewport']) for row in target_rows if row['selector']['identifier'] in ['notes.middle', 'notes.action']))
            for batch_start in range(0, len(selected), 4):
                batch = selected[batch_start:batch_start + 4]
                canvas = Image.new('RGB', (1206, 940 * ((len(batch) + 1) // 2)), 'white')
                draw = ImageDraw.Draw(canvas)
                for pos, index in enumerate(batch):
                    snap = obs['snapshots'][index]; vp = snap['viewport']
                    im = Image.open(cap / snap['screenshot']).convert('RGB')
                    left, top = (pos % 2) * 603, (pos // 2) * 940
                    draw.text((left + 5, top + 10), f'{arm} {state["id"]} original index {index}', fill='black')
                    crop = im.crop((int(vp['x'] * 3), int(vp['y'] * 3), int((vp['x'] + vp['width']) * 3), int((vp['y'] + vp['height']) * 3)))
                    canvas.paste(crop.resize((600, 900)), (left, top + 35))
                path = ROOT / 'images' / f'{arm}-{state["id"]}-{batch_start // 4}.jpg'
                canvas.save(path, quality=96)
        dispatch = []
        for index in [1, 2, 4]:
            step = obs['steps'][index]
            result = native_checks.callback_verdict(step, ['notes.reviewed.A'] if index == 1 else [], 'ios',
                stimulus='caller_update' if index == 2 else 'activation')
            dispatch.append({'action_index': index, 'outcome': step['outcome'], 'dispatch': step['dispatch'],
                'callback_delta': step['callback_delta'], 'binding_after': step['binding_after'],
                'immediate_after': step.get('immediate_after'), 'after': step['after'], 'callback_verdict': result})
        assert dispatch[0]['callback_verdict']['status'] == 'passed'
        assert dispatch[1]['callback_verdict']['status'] == 'passed'
        assert dispatch[2]['callback_verdict']['status'] == 'unassessed'
        save(arm + '-image-catalog.json', image_catalog)
        all_results.append({'arm': arm, 'capture': str(cap), 'manifest_status': manifest['status'],
            'native_test_count': manifest['native_test_count'], 'native_counts': report['counts'],
            'required_coverage_satisfied': receipt['satisfied'], 'states': states, 'dispatch': dispatch,
            'issues': obs['issues'], 'serialization_diagnostics': obs['serialization_diagnostics'],
            'actual_environment': manifest['actual_environment'], 'actual_viewport': manifest['actual_viewport'],
            'source_hashes': manifest['source_hashes'], 'timings': manifest['timings'],
            'capture_wall_seconds': manifest['finished_at'] - manifest['started_at'],
            'build_cache_hit': manifest['build_cache']['hit'], 'snapshot_count': len(obs['snapshots'])})
    save('inputs-sha256.json', {'recorded_unix': begun, 'files': input_map})
    save('native-inspection.json', {'version': 1, 'started_unix': begun, 'finished_unix': time.time(),
        'sealed_inputs_unchanged': checks, 'runs': all_results,
        'independence_limit': 'Uses frozen checker reconstruction and raw observation consistency; visual review is separate. No SDK executed.'})
    print(json.dumps({'status': 'native_reconstruction_complete', 'runs': [{k: row[k] for k in ['arm', 'native_counts', 'required_coverage_satisfied', 'snapshot_count']} for row in all_results]}, indent=2))

if __name__ == '__main__': main()
