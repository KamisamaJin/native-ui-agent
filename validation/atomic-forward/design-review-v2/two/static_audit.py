"""Independent SDK-free audit; reads only the explicitly permitted frozen inputs."""
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
BASE = ROOT / 'validation/atomic-forward'
OUT = BASE / 'design-review-v2/two'
sys.path.insert(0, str(BASE / 'candidate-v8/scripts'))
import design_contract as design
import review_contract as review
import acceptance

hashes = {}
checks = []
errors = []

def read(path):
    path = Path(path)
    raw = path.read_bytes()
    hashes[str(path.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
    return raw

def load(path):
    return design.strict_json(read(path).decode())

def check(name, condition, detail=None):
    row = {'check': name, 'passed': bool(condition)}
    if detail is not None:
        row['detail'] = detail
    checks.append(row)
    if not condition:
        errors.append(row)

freeze = load(BASE / 'candidate-v8-freeze.json')
check('Frozen inventory contains exactly 54 files', len(freeze['files']) == 54)
for rel, wanted in freeze['files'].items():
    path = BASE / 'candidate-v8' / rel
    check('frozen:' + rel, hashlib.sha256(read(path)).hexdigest() == wanted)

read(BASE / 'DESIGN-INTERFACE.md')
read(BASE / 'design-v2/DELIVERY.md')
load(BASE / 'design-v2/seal.json')

for task in ['T1', 'T2', 'T3']:
    td = BASE / 'design-v2' / task
    pubc = load(td / 'public/contract.json')
    pric = load(td / 'private/contract.json')
    check(task + ':public/private rules', pubc['rules'] == pric['rules'])
    check(task + ':public/private rule identities', pubc['required_rule_ids'] == pric['required_rule_ids'])
    public_policy = load(td / 'public/policy.json')
    private_policy = load(td / 'private/policy.json')
    check(task + ':hidden policy atoms unchanged', public_policy['atoms'] == private_policy['atoms'])
    check(task + ':hidden ownership unchanged', public_policy['ownership'] == private_policy['ownership'])
    read(td / 'seal.json')
    for side in ['public', 'private']:
        d = td / side
        for name in (['BRIEF.md', 'API.md', 'Bridge.swift', 'ObserverBridge.kt'] if side == 'public' else ['HELDOUT.md']):
            read(d / name)
        c = load(d / 'contract.json')
        ref = load(d / 'reference.json')
        lock = load(d / 'design-lock.json')
        bindings = load(d / 'bindings.json')
        policy = load(d / 'policy.json')
        approval = load(d / 'approval.json')
        generated_lock = design.seal(d / 'contract.json', d)
        check(task + ':' + side + ':exact lock', generated_lock == lock)
        check(task + ':' + side + ':approval lock digest', design.digest(lock) == approval['design_lock_sha256'])
        check(task + ':' + side + ':approval policy digest', design.digest(policy) == approval['policy_sha256'])
        for case, scenario in c['scenarios'].items():
            label = task + ':' + case
            fixtures = load(d / 'cases' / case / 'fixtures.json')
            checkpoint = load(d / 'cases' / case / 'checkpoint-map.json')
            check(label + ':checkpoint state equality', checkpoint['states'] == scenario['states'])
            models = [fixtures['initial']] + fixtures['updates']
            check(label + ':canonical input epochs', [x['canonical_input_sha256'] for x in checkpoint['model_inputs']] == [design.digest(m) for m in models])
            arr = 'services' if task == 'T3' else 'incidents' if task == 'T2' else 'slots'
            check(label + ':availability/reason invariant', all((x['available'] and x['unavailableReason'] == '') or (not x['available'] and isinstance(x['unavailableReason'], str) and len(x['unavailableReason']) > 0) for m in models for x in m[arr]))
            for platform in ['ios', 'android']:
                actions = load(d / 'cases' / case / ('actions.' + platform + '.json'))
                env = load(d / 'cases' / case / ('environment.' + platform + '.json'))
                check(label + ':' + platform + ':environment digest', design.digest(env) == approval['environment_sha256'][case][platform])
                expected_env = {'width': fixtures['width'], 'height': fixtures['viewportHeight'], 'direction': fixtures['direction'], 'theme': fixtures['theme']}
                if platform == 'ios':
                    expected_env['dynamic_type'] = fixtures['dynamic_type']
                else:
                    expected_env.update(font_scale=fixtures['fontScale'], dimension_encoding='paparazzi-float32-screen-config-v1')
                check(label + ':' + platform + ':environment vs host fixture', env == expected_env)
                check(label + ':' + platform + ':unobserved environment U', acceptance.environment({}, env, platform)['status'] == 'U')
                fresh_plan, fresh_actions = design.compile_contract(lock, approval['design_lock_sha256'], case, platform, bindings, actions)
                saved_plan = load(d / 'compiled' / case / platform / 'plan.json')
                saved_actions = load(d / 'compiled' / case / platform / 'actions.json')
                saved_catalog = load(d / 'compiled' / case / platform / 'catalog.json')
                fresh_catalog = review.catalog(fresh_plan, lock, approval['design_lock_sha256'], policy, approval['policy_sha256'], platform)
                fresh_catalog['catalog_sha256'] = design.digest(fresh_catalog)
                check(label + ':' + platform + ':fresh plan equality', saved_plan == fresh_plan)
                check(label + ':' + platform + ':fresh action equality', saved_actions == fresh_actions)
                check(label + ':' + platform + ':fresh catalog equality', saved_catalog == fresh_catalog)
                counts = {'required': len(fresh_plan['assertions']), 'not_applicable': sum(x['disposition'] == 'not_applicable' for x in fresh_plan['matrix_contract']['cells'])}
                check(label + ':' + platform + ':selected denominator', counts == {'required': 81, 'not_applicable': 17}, counts)
                check(label + ':' + platform + ':seven selected states', len(fresh_plan['states']) == 7)
                check(label + ':' + platform + ':under 40 actions', len(actions) <= 40)
                check(label + ':' + platform + ':typed minimum height', all(x['expected'] == 56 and x['unit'] == ('pt' if platform == 'ios' else 'dp') and x['op'] == 'gte' for x in fresh_plan['assertions'] if x['requirement_id'] == 'primary-control-height'))
                check(label + ':' + platform + ':selected native weight retained', len([x for x in fresh_plan['assertions'] if x['requirement_id'] == 'title-native-weight' and x['expected'] == 600 and x['unit'] == 'scalar']) == 7)
            # Independent replay of specified business rules, not component code.
            current = models[0]
            selected = set(current.get('initialSelectedIDs', [])) if task == 'T3' else ({current['initialSelectedID']} if current.get('initialSelectedID') else set())
            selected &= {x['id'] for x in current[arr] if x['available']}
            expanded = current['initialDetailsExpanded']
            index = 0
            last_events = []
            snapshots = {}
            prefix = {'T1': 'workshop', 'T2': 'river', 'T3': 'bicycle'}[task]
            for ai, action in enumerate(scenario['actions']):
                kind = action['type']
                if kind == 'apply_next_fixture':
                    index += 1
                    current = models[index]
                    selected = set(current.get('initialSelectedIDs', [])) if task == 'T3' else ({current['initialSelectedID']} if current.get('initialSelectedID') else set())
                    selected &= {x['id'] for x in current[arr] if x['available']}
                    expanded = current['initialDetailsExpanded']
                    last_events = []
                elif kind == 'tap':
                    target = action['target']
                    last_events = []
                    if target == 'disclosure':
                        expanded = not expanded
                        last_events = [prefix + ':details:' + ('open' if expanded else 'closed')]
                    elif target == 'submit' and selected:
                        verb = 'submit' if task == 'T3' else 'reserve' if task == 'T1' else 'acknowledge'
                        last_events = [prefix + ':' + verb + ':' + ','.join(sorted(selected))]
                    elif target in {'choiceA', 'choiceB', 'locked'}:
                        ident = {'choiceA': 'a', 'choiceB': 'b', 'locked': 'c'}[target]
                        item = next(x for x in current[arr] if x['id'] == ident)
                        if item['available']:
                            if task == 'T3':
                                if ident in selected: selected.remove(ident)
                                else: selected.add(ident)
                                last_events = [prefix + ':toggle:' + ident + ':' + str(ident in selected).lower()]
                            else:
                                selected = {ident}
                                last_events = [prefix + ':select:' + ident]
                chosen = [x for x in current[arr] if x['id'] in selected]
                if task == 'T3':
                    summary = ('Work: ' + ' + '.join(x['label'] for x in chosen) + ' · ' + str(sum(x['minutes'] for x in chosen)) + ' min') if chosen else 'No work selected · 0 min'
                else:
                    summary = ('Draft station: ' if task == 'T1' else 'Reviewing: ') + chosen[0]['label'] if chosen else ('No station selected' if task == 'T1' else 'No alert selected')
                noun = {'T1': 'safety briefing', 'T2': 'reading dossier', 'T3': 'handover notes'}[task]
                snapshots[ai] = {'summary': summary, 'selectedA': 'a' in selected, 'submitEnabled': bool(selected), 'disclosure': ('Hide ' if expanded else 'Show ') + noun, 'events': list(last_events)}
            for state in scenario['states']:
                expected = ref['cases'][case]['states'][state['id']]
                actual = snapshots[state['after_action']]
                check(label + ':' + state['id'] + ':business replay', all(expected[k]['value'] == actual[k] for k in ['summary', 'selectedA', 'submitEnabled', 'disclosure']))
                if state['id'] in {'selected', 'expanded', 'reselected', 'submitted'}:
                    stimulus = state.get('stimulus_action', state['after_action'])
                    check(label + ':' + state['id'] + ':event stimulus', expected['activationEvents']['value'] == snapshots[stimulus]['events'])
                if state['id'] == 'replaced':
                    check(label + ':replacement silence', expected['updateEvents']['value'] == [])
            meta = load(d / ('reference-' + case + '-expanded.meta.json'))
            svg = read(d / ('reference-' + case + '-expanded.svg'))
            png = read(d / ('reference-' + case + '-expanded.png'))
            audit = load(d / ('reference-' + case + '-text-fit-audit.json'))
            check(label + ':reference SVG hash', hashlib.sha256(svg).hexdigest() == meta['svg_sha256'])
            check(label + ':reference PNG hash', hashlib.sha256(png).hexdigest() == meta['png_sha256'])
            check(label + ':reference canvas width', meta['width_native'] == fixtures['width'] - 32)
            check(label + ':reference text gutter audit', audit['all_text_inside_canvas_gutter'] and all(x['x_min'] >= 12 and x['x_max'] <= meta['width_native'] - 12 for x in audit['lines']))
            # Recompute the approved canvas rectangle on the supplied drawing pixels.
            # This confirms reference suitability, not a production native pass.
            import io
            import math
            from PIL import Image
            from collections import Counter
            image = Image.open(io.BytesIO(png)).convert('RGB')
            roi = tuple(math.ceil(v - .5) for v in [image.width * .02, image.height * .05, image.width * .03, image.height * .95])
            histogram = Counter(image.crop(roi).getdata())
            color, amount = histogram.most_common(1)[0]
            rgb = ref['cases'][case]['colors']['canvas']['value'][-6:]
            wanted_rgb = tuple(int(rgb[i:i+2], 16) for i in [0, 2, 4])
            check(label + ':rendered reference canvas strip', color == wanted_rgb and amount / sum(histogram.values()) == 1.0, {'rgb': list(color), 'dominantSupport': amount / sum(histogram.values()), 'scope': 'independent reference only'})

(OUT / 'static-audit.json').write_text(json.dumps({'checks': checks, 'errors': errors, 'inputHashes': hashes}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'checks': len(checks), 'failures': errors, 'hashedInputs': len(hashes)}, ensure_ascii=False))
