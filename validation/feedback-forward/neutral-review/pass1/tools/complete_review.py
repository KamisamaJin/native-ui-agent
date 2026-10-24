"""Record the independent image judgments, then evaluate them with frozen tools."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import sys
import time
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parents[1]
NEUTRAL = BASE / 'neutral'
SNAPSHOT = BASE / 'development/candidate-attempt-1'
sys.path.insert(0, str(SNAPSHOT / 'scripts'))
import design_contract as design
import native_checks
import requirement_routes

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads(path.read_text())
def save(name, value): (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def main():
    approval = load(NEUTRAL / 'APPROVAL.json')
    lock = load(NEUTRAL / 'design/lock.json')
    plan = load(NEUTRAL / 'generated/ordinary400/design/plan.json')
    coverage = load(NEUTRAL / 'generated/ordinary400/coverage.json')
    results = []
    pixel_rows = []
    judgments = {
        'full-layout': ('passed', 'Reviewed both overlapping full-state sequences: heading and input summary precede cards 01–06, the review action, cards 07–10 and the footer. The real bottom is visible. All ten cards remain in order with distinct surfaces and gaps; no horizontal clipping or overlap was observed. Partial cards at viewport edges are covered in adjacent images.'),
        'text-wrapping': ('passed', 'At actual offered width 400 pt and large Dynamic Type, the current title/summary, all ten card headings and bodies, action label and footer are readable. Text wraps naturally without visible ellipses, horizontal truncation or overlaps. The disabled-color defect is assessed separately.'),
        'neutral-surfaces': ('passed', 'The original target frames show the white canvas, pale neutral card surface, dark heading and secondary text consistently. No unexpected card or text surface change is visible in this state. This is rendered appearance judgment, not a claim about computed SwiftUI properties.'),
        'action-appearance': ('passed', 'The fully visible native action is a rounded dark blue-gray surface with readable white text and agrees with the approved enabled appearance. Its 52 pt accessibility control height is independently established by the typed native assertion.'),
    }
    for arm in ['legacy', 'coalesced']:
        cap = BASE / 'neutral-captures' / ('ordinary400-r1-' + arm)
        obs = load(cap / 'observation.json')
        decisions = []
        for rule in plan['assertions']:
            if rule['kind'] != 'manual': continue
            state = next(s for s in plan['states'] if s['id'] == rule['state'])
            evidence, complete, reason, _ = native_checks.bound_state_evidence(obs, state)
            if rule['coverage'] == 'full_content':
                indices = [i for i, _ in evidence]
                assert complete
            else:
                indices = []
                for index, snap in evidence:
                    target = native_checks.resolve(snap, rule['target'], 'ios').get('semantic', {})
                    if target.get('fully_within_viewport'):
                        indices = [index]; break
                assert indices
            status, rationale = judgments[rule['requirement_id']]
            if rule['requirement_id'] == 'action-appearance' and rule['state'] in ['replaced', 'disabled']:
                status = 'failed'
                rationale = 'The original fully visible disabled action is visibly more faded than the frozen appearance. The approved fill is #DCE2E7 and label ink #55616C; original PNG diagnostic picking finds dominant inner fill #EDF0F3 and solid glyph core #A1A8AF. The 52 pt height, rounded shape and native disabled state pass separately. This is a rendered appearance failure, not a generic computed-color assertion or a callback failure.'
            refs = [{'path': obs['snapshots'][i]['screenshot'], 'sha256': sha(cap / obs['snapshots'][i]['screenshot'])} for i in indices]
            decisions.append({'id': rule['id'], 'method': 'visual', 'status': status,
                'reason': rationale, 'snapshot_indices': indices, 'evidence': refs})
            if rule['requirement_id'] == 'action-appearance':
                i = indices[0]; snap = obs['snapshots'][i]
                n = next(n for n in snap['nodes'] if n.get('identifier') == rule['target']['identifier'])
                frame = n['image_frame']
                box = (round(frame['x'] + 30), round(frame['y'] + 10), round(frame['x'] + frame['width'] - 30), round(frame['y'] + frame['height'] - 10))
                image = Image.open(cap / snap['screenshot']).convert('RGB')
                colors = Counter(image.crop(box).getdata())
                pixel_rows.append({'arm': arm, 'state': rule['state'], 'snapshot_index': i,
                    'source_png': str(cap / snap['screenshot']), 'source_sha256': sha(cap / snap['screenshot']),
                    'interior_pixel_box': box, 'colors': [{'rgb': '#%02X%02X%02X' % rgb, 'count': count} for rgb, count in colors.most_common(5)],
                    'purpose': 'Diagnostic eyedropper corroboration of manual visual review. This was not a preapproved automatic pixel sampling policy and earns no separate native_pixels verdict.'})
        manual = {'version': 1, 'reviewer': 'Independent neutral forward tester',
            'observation_sha256': sha(cap / 'observation.json'), 'decisions': decisions,
            'scope': 'Ordinary400 first pair only. Full sequences were inspected through index-labelled contact sheets built from original PNG viewports; representative original PNGs and immediate post-action images were also opened. No new reference or expectation was created from the candidate image.'}
        save(arm + '-manual.json', manual)
        report = native_checks.evaluate(plan, obs, 'ios', manual=manual, root=cap,
            observation_sha256=sha(cap / 'observation.json'), design_lock=lock, design_sha256=approval['design_lock_sha256'])
        save(arm + '-evaluated.json', report)
        routed = requirement_routes.route_findings(coverage, plan, report, obs)
        save(arm + '-routes.json', routed)
        admission = requirement_routes.admission(coverage, plan, report)
        save(arm + '-admission.json', admission)
        results.append({'arm': arm, 'counts': report['counts'], 'failed_ids': report['failed_assertion_ids'],
                        'native_only_counts': load(ROOT / (arm + '-recomputed-automatic.json'))['counts'],
                        'admission': admission['status'], 'blocking_obligations': admission['blocking_obligations']})
    save('rendered-color-diagnostics.json', {'version': 1, 'rows': pixel_rows})
    # Remove only obsolete sheets generated in this review folder before its grid layout was finalized.
    for arm in ['legacy', 'coalesced']:
        for state in ['reviewed', 'disabled']:
            for batch in [1, 2]:
                path = ROOT / 'images' / f'{arm}-{state}-{batch}.jpg'
                if path.exists(): path.unlink()
    save('completion.json', {'version': 1, 'completed_unix': time.time(), 'case': 'ordinary400', 'pair': 'r1',
        'results': results, 'required_coverage_preserved': True,
        'confirmed_component_root_causes': [{'id': 'disabled-rendered-palette',
            'violated_assertions_per_arm': ['replaced/action-appearance', 'disabled/action-appearance'],
            'source_location': str(NEUTRAL / 'source/Bridge.swift') + ':127',
            'cause_hypothesis': 'The plain button style applies an additional disabled appearance to an already explicitly colored label. The frozen source uses .buttonStyle(.plain) immediately before .disabled; this is a hypothesis, not a verified fix.',
            'source_changed': False}],
        'unknowns': ['Generic computed SwiftUI font, padding, color properties and physical touch bounds were never exposed or claimed.',
                     'Narrow/large-text case and reversed-order ordinary pair have not yet been delivered to this reviewer.',
                     'No second independent visual oracle has reviewed these judgments.'],
        'provenance_notes': ['The supplied legacy capture identifies baseline-v8 observer tools/templates, while coalesced identifies candidate-attempt-1. Both compiled the same sealed Bridge.swift and consumed the exact frozen strategy-specific configs/actions. No baseline file outside the supplied capture was opened.',
                             'The first pair is order/cold-boot confounded: native timings are retained as observed descriptive values; no general speed or causal claim follows from this pair alone.'],
        'no_sdk_execution_by_reviewer': True})
    print(json.dumps({'results': results}, indent=2))

if __name__ == '__main__': main()
