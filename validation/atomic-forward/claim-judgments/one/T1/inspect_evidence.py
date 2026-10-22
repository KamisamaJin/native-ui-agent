#!/usr/bin/env python3
"""Read only the permitted T1 transport, original evidence and common D0 inputs."""
import sys
sys.dont_write_bytecode = True
import collections
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

BASE = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/atomic-forward')
OUT = BASE / 'claim-judgments/one/T1'
sys.path.insert(0, str(BASE / 'candidate-v8/scripts'))
import native_pixels
from native_checks import resolve

def read(path):
    return json.loads(path.read_text())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

policy = read(BASE / 'design-v2/T1/public/policy.json')
sampling = next(a['sampling'] for a in policy['atoms'] if a['rule_id'] == 'primary-surface-color')
inspection = {'original_color_claims': [], 'original_grid_claims': [], 'common_product_rows': {},
              'common_input_integrity': [], 'original_plan_checks': [], 'tool_sha256': {}}
for name in ['native_pixels.py', 'native_checks.py', 'review_contract.py', 'design_contract.py']:
    p = BASE / 'candidate-v8/scripts' / name
    inspection['tool_sha256'][str(p.relative_to(BASE))] = digest(p)

common_paths = []
for source in ['source-a', 'source-b']:
    transport = read(BASE / f'evaluation-inputs/claims/T1/{source}/claims.json')
    for claim in transport['claims']:
        if claim['original_status'] != 'failed':
            continue
        original = claim['original']
        root = BASE / claim['observation_root']
        observation = read(root / 'observation.json')
        if claim['origin'] == 'machine':
            plan_path = BASE / claim['original_json'].split('/own-checks/')[0] / f'initial-agent-output/plans/{claim["case"]}/{claim["platform"]}/plan.json'
            plan = read(plan_path)
            actual_plan = next(a for a in plan['assertions'] if a['id'] == original['id'])
            inspection['original_plan_checks'].append({'claim_id': claim['claim_id'], 'path': str(plan_path.relative_to(BASE)),
                                                       'sha256': digest(plan_path), 'equals_transport_original_plan': actual_plan == claim['original_plan']})
            samples = []
            for index in original['snapshot_indices']:
                snap = observation['snapshots'][index]
                samples.append({'snapshot_index': index, 'state_id': snap['state_id'], 'capture_consistent': snap['capture_consistent'],
                                'binding': snap['binding'], 'binding_after_capture': snap['binding_after_capture'],
                                'submit': resolve(snap, {'identifier': 'workshop.submit'}, 'ios'),
                                'sample': native_pixels.sample(snap, {'identifier': 'workshop.submit'}, 'ios', root, sampling)})
            inspection['original_color_claims'].append({'claim_id': claim['claim_id'], 'original_expected': claim['original_plan']['expected'],
                                                        'original_unit': claim['original_plan']['unit'], 'samples': samples})
        elif not claim.get('duplicate_of'):
            evidence = original.get('evidence', [])
            shots = [Path(e['path']).name for e in evidence if e['path'].endswith('.png')]
            facts = []
            for index, snap in enumerate(observation['snapshots']):
                if Path(snap.get('screenshot', '')).name not in shots:
                    continue
                facts.append({'snapshot_index': index, 'state_id': snap['state_id'], 'screenshot': snap['screenshot'],
                              'capture_consistent': snap['capture_consistent'], 'runtime': snap['runtime'],
                              'native_boxes': {ident: [{'frame': n['frame'], 'image_frame': n.get('image_frame'), 'enabled': n.get('enabled')}
                                                       for n in snap['nodes'] if n.get('identifier') == ident]
                                               for ident in ['workshop.canvas', 'workshop.choice.a', 'workshop.choice.b']}})
            inspection['original_grid_claims'].append({'claim_id': claim['claim_id'], 'original_expected': original['expected'],
                                                       'original_unit': original['unit'], 'facts': facts})

    rows = []
    for platform in ['android', 'ios']:
        for case in ['P1', 'P2']:
            input_path = BASE / f'evaluation-inputs/d0/T1/{source}/{platform}/{case}/inputs.json'
            inputs = read(input_path)
            checks = []
            for relative, expected in inputs['original_files'].items():
                path = BASE / relative
                actual = digest(path) if path.is_file() else None
                checks.append({'path': relative, 'expected': expected, 'actual': actual, 'matches': actual == expected})
            inspection['common_input_integrity'].append({'path': str(input_path.relative_to(BASE)), 'sha256': digest(input_path), 'files': checks})
            acceptance_path = BASE / f'evaluation/d0/T1/{source}/{platform}/{case}/acceptance.json'
            acceptance = read(acceptance_path)
            for row in acceptance['rows']:
                if row['status'] != 'failed' or row.get('cause_category') != 'product':
                    continue
                key = f'{case}/{platform}/{row["id"]}'
                root = BASE / inputs['root']
                observation = read(BASE / inputs['observation'])
                samples = []
                for index in row['authoritative']['snapshot_indices']:
                    snap = observation['snapshots'][index]
                    samples.append({'snapshot_index': index, 'state_id': snap['state_id'], 'capture_consistent': snap['capture_consistent'],
                                    'submit': resolve(snap, {'identifier': 'workshop.submit'}, platform),
                                    'sample': native_pixels.sample(snap, {'identifier': 'workshop.submit'}, platform, root, sampling)})
                    common_paths.append({'path': str(root / snap['screenshot']), 'key': key, 'snapshot_index': index,
                                         'sha256': digest(root / snap['screenshot'])})
                rows.append({'key': key, 'acceptance_path': str(acceptance_path.relative_to(BASE)), 'acceptance_sha256': digest(acceptance_path),
                             'status': row['status'], 'cause_category': row['cause_category'], 'expected': row['expected'], 'unit': row['unit'],
                             'samples': samples})
    inspection['common_product_rows'][source] = rows

sheet = Image.new('RGB', (4 * 402, 2 * 904), '#d8d8d8')
draw = ImageDraw.Draw(sheet)
for i, item in enumerate(common_paths):
    image = Image.open(item['path']).convert('RGB')
    image.thumbnail((402, 874))
    x, y = (i % 4) * 402, (i // 4) * 904
    sheet.paste(image, (x, y + 30))
    draw.text((x + 3, y + 5), f'{i + 1} {item["key"]} #{item["snapshot_index"]}', fill='black')
sheet.save(OUT / 'common-d0-product-inspection.png')
inspection['common_product_screenshot_manifest'] = common_paths
(OUT / 'native-inspection.json').write_text(json.dumps(inspection, indent=2) + '\n')
print('Original color facts:', [(c['claim_id'], [hex(s['sample'].get('argb', 0)) for s in c['samples']]) for c in inspection['original_color_claims']])
print('Original grid facts:', [(c['claim_id'], [(f['state_id'], f['native_boxes']['workshop.canvas'][0]['frame']['width']) for f in c['facts']]) for c in inspection['original_grid_claims']])
print('Common product facts:', {s: [(r['key'], [hex(v['sample'].get('argb', 0)) for v in r['samples']]) for r in rows] for s, rows in inspection['common_product_rows'].items()})
print('Common input mismatches:', [f for c in inspection['common_input_integrity'] for f in c['files'] if not f['matches']])
print('Original plan mismatches:', [p for p in inspection['original_plan_checks'] if not p['equals_transport_original_plan']])
