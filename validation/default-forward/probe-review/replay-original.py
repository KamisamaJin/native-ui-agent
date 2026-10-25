#!/usr/bin/env python3
"""Disclosed SDK-free compatibility replay; never edits the live service.

The approved typed contract is supplied by this adapter, NOT derived by the
service. The only mocked operation is execution_plan's native subprocess
transport; contract compilation, routes, diagnosis, planning, source identity,
receipts, repeated-history handling, and admission execute unmodified.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import traceback
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parent / 'probe-design'
parser = argparse.ArgumentParser()
parser.add_argument('--scripts', type=Path, default=HERE / 'tool-snapshot')
parser.add_argument('--output', type=Path, default=HERE / 'replay-1')
args = parser.parse_args()
sys.dont_write_bytecode = True
sys.path.insert(0, str(args.scripts.resolve()))
import design_contract as d
import execution_plan as xp
import feedback_loop as loop
import native_checks

OUT = args.output.resolve()
OUT.mkdir(parents=True, exist_ok=False)
CATALOG = json.loads((DESIGN / 'evidence/observations.json').read_text())
HISTORY = json.loads((DESIGN / 'evidence/complete-history-v2.json').read_text())['steps']
results = []


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p, v):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, indent=2) + '\n')


def record(name, operation):
    try:
        detail = operation()
        results.append({'probe': name, 'reproduced': True, 'detail': detail})
    except Exception as exc:
        results.append({'probe': name, 'reproduced': False, 'exception': repr(exc), 'traceback': traceback.format_exc()})
    write(OUT / 'summary.json', results)


def tree_value(tree, ident):
    if tree.get('identifier') == ident: return tree.get('name')
    for child in tree.get('children', []):
        found = tree_value(child, ident)
        if found is not None: return found


def flatten(tree, parent=None, nodes=None):
    nodes = [] if nodes is None else nodes
    nid = str(len(nodes))
    frame = tree.get('frame', [0, 0, 430, 740])
    node = {'node_id': nid, 'parent_id': parent, 'identifier': tree.get('identifier'),
            'label': tree.get('name', ''), 'role': tree['type'].lower(),
            'role_raw': {'StaticText': 48, 'Button': 9, 'Other': 1}.get(tree['type'], -1),
            'frame': dict(zip(['x', 'y', 'width', 'height'], frame)),
            'enabled': tree.get('enabled', True), 'intersects_viewport': True,
            'fully_within_viewport': True, 'hittable': True}
    nodes.append(node)
    for child in tree.get('children', []): flatten(child, nid, nodes)
    return nodes


def setup(name, observations, properties, *, version='v2'):
    root = OUT / name; root.mkdir()
    production = root / 'production'
    shutil.copytree(DESIGN / 'sources' / version, production)
    bridge = root / 'Bridge.swift'
    bridge.write_text('// Synthetic transport boundary only; no SDK compilation is claimed.\n')
    fixtures = {'initial': {}, 'updates': []}
    states = [{'id': f'checkpoint-{i:02}', 'input_index': 0, 'after_action': i, 'coverage': 'full_content'} for i in range(len(observations))]
    actions = [{'type': 'checkpoint'}] if len(observations) == 1 else [
        {'type': 'checkpoint'} if i == 0 else {'type': 'tap', 'target': step['operation'][9:-1]}
        for i, step in enumerate(HISTORY)]
    rules = []; bindings = {}; values = {}; expected = {}
    for rid, ident, prop, values_for_states in properties:
        rules.append({'id': rid, 'kind': 'control', 'target': ident, 'property': prop})
        bindings[ident] = {'identifier': ident, 'role': 'button' if ident.endswith(('primary', 'step', 'reset')) else 'text'}
        expected[rid] = []
        values[rid] = {}
        for i, (state, value) in enumerate(zip(states, values_for_states)):
            expected[rid].append({'value': value, 'unit': 'bool' if isinstance(value, bool) else 'string'})
            values[rid][state['id']] = {pl: {'source': 'approved', 'pointer': f'/expected/{rid}/{i}'} for pl in ['ios', 'android']}
    for action in actions:
        if action.get('target'): bindings.setdefault(action['target'], {'identifier': action['target'], 'role': 'button'})
    source = {'expected': expected, 'launch': {'fixtures_sha256': d.digest(fixtures), 'bridge_sha256': sha(bridge), 'scenario': 'neutral', 'platform': 'ios'},
              'obligations': [{'id': rid, 'clause': f'Neutral approved subset: {rid}', 'priority': 'must', 'states': [s['id'] for s in states], 'risk': 'behavior'} for rid, *_ in properties]}
    write(root / 'approved.json', source)
    contract = {'version': 1, 'design_owner': 'independent-neutral-probe-adapter',
                'approval_reference': str(DESIGN / 'SHA256SUMS'),
                'sources': [{'id': 'approved', 'path': 'approved.json', 'sha256': sha(root / 'approved.json')}],
                'rules': rules, 'required_rule_ids': [r['id'] for r in rules],
                'scenarios': {'neutral': {'states': states, 'actions': actions, 'values': values}}}
    write(root / 'contract.json', contract)
    lock = d.seal(root / 'contract.json', root); lock_sha = d.digest(lock)
    bound = copy.deepcopy(actions)
    for a in bound:
        if a.get('target'): a['target'] = bindings[a['target']]
    plan, _ = d.compile_contract(lock, lock_sha, 'neutral', 'ios', bindings, bound)
    routes = {'version': 1, 'index': {'source': 'approved', 'pointer': '/obligations'}, 'routes': {
        rid: {'rule_ids': [rid], 'reason': 'Independent neutral typed subset.', 'regression_obligations': []} for rid, *_ in properties}}
    env = {'width': 430, 'height': 740, 'direction': 'ltr', 'theme': 'light', 'dynamic_type': 'large'}
    for file, value in [('plan', plan), ('lock', lock), ('fixtures', fixtures), ('routes', routes), ('environment', env)]: write(root / (file + '.json'), value)
    config = {'plan': str(root / 'plan.json'), 'design_lock': str(root / 'lock.json'), 'design_sha256': lock_sha,
              'fixtures': str(root / 'fixtures.json'), 'bridge': str(bridge), 'routes': str(root / 'routes.json'), 'routes_sha256': d.digest(routes),
              'source_roots': [str(production)], 'launch_ref': {'source': 'approved', 'pointer': '/launch'},
              'environment': str(root / 'environment.json'), 'environment_sha256': d.digest(env), 'native_options': {'simulator': 'synthetic-transport'}}
    write(root / 'config.json', config)
    return root, config, plan, observations


def transport(bundle, *, no_packet=False, missing_png=False, replacement=None, pending_first=False):
    root, config, plan, oids = bundle
    def native(argv, **kwargs):
        output = Path(argv[argv.index('--output') + 1]); output.mkdir()
        if no_packet: return SimpleNamespace(returncode=65)
        emitted_actions = d.load(Path(argv[argv.index('--actions') + 1]))
        emitted_config = d.load(Path(argv[argv.index('--fixtures') + 1]))
        observation = {'artifact_origin': 'synthetic-fixture-transport', 'snapshots': [], 'steps': [], 'state_captures': []}
        for i, action in enumerate(emitted_actions):
            state = next((s for s in plan['states'] if s['after_action'] == i), None)
            if not state or state['id'] not in [s['state_id'] for s in emitted_config['execution_states']]: continue
            oid = replacement.get(i, oids[i]) if replacement else oids[i]
            evidence = CATALOG[oid]
            tree = d.load(DESIGN / evidence['native_tree']['path'])
            nodes = flatten(tree)
            binding = {'instance': 'synthetic-launch-1', 'pid': 100, 'fixture_index': 0,
                       'input_sha256': d.digest({}), 'event_revision': i}
            screenshot = f'frame-{i:02}.png'
            if not missing_png: shutil.copyfile(DESIGN / evidence['screenshot']['path'], output / screenshot)
            snapshot = {'screenshot': screenshot, 'state_id': state['id'], 'binding': binding,
                        'binding_after_capture': binding, 'capture_consistent': True, 'nodes': nodes,
                        'viewport': {'x': 0, 'y': 0, 'width': 430, 'height': 740},
                        'runtime': {'content_frame': {'x': 0, 'y': 0, 'width': 430, 'height': 740},
                                    'actual_environment': {'direction': 'ltr', 'theme': 'light', 'dynamic_type': 'large'}},
                        'control_groups': []}
            for target in emitted_config['observation_targets']:
                matches = [n for n in nodes if native_checks.same_selector(n, target)]
                group = {'selector': target, 'match_count': len(matches), 'resolution': 'missing' if not matches else 'ambiguous_semantic'}
                if len(matches) == 1:
                    group.update(semantic=matches[0], control=matches[0], resolution='unique_native_control')
                snapshot['control_groups'].append(group)
            first_index = len(observation['snapshots'])
            if pending_first and i == 0:
                pending = copy.deepcopy(snapshot)
                pending['nodes'] = flatten(d.load(DESIGN / CATALOG['pause-pending-v2']['native_tree']['path']))
                pending['screenshot'] = 'pending.png'
                for group in pending['control_groups']:
                    matches = [n for n in pending['nodes'] if native_checks.same_selector(n, group['selector'])]
                    group.update(match_count=len(matches))
                    if len(matches) == 1: group.update(semantic=matches[0], control=matches[0], resolution='unique_native_control')
                shutil.copyfile(DESIGN / CATALOG['pause-pending-v2']['screenshot']['path'], output / 'pending.png')
                observation['snapshots'].append(pending)
            observation['snapshots'].append(snapshot)
            observation['steps'].append({'state_id': state['id'], 'binding_after': binding, 'after': i})
            observation['state_captures'].append({'state_id': state['id'], 'binding': binding, 'after_action': i,
                                                   'snapshot_indices': list(range(first_index, len(observation['snapshots']))),
                                                   'top_reached': True, 'bottom_reached': True, 'stable_binding': True})
        write(output / 'observation.json', observation)
        kwargs['stdout'].write('Synthetic native transport emitted only frozen tree/PNG fixture facts.\n')
        return SimpleNamespace(returncode=0)
    return native


def cycle(bundle, directory, *, transport_options=None, **kwargs):
    with patch.object(xp.subprocess, 'run', side_effect=transport(bundle, **(transport_options or {}))):
        return loop.run_cycle(bundle[1], bundle[0] / directory, **kwargs)


def raw_boundary():
    case = json.loads((DESIGN / 'inputs/cases.json').read_text())[0]
    config = OUT / 'raw-case.json'; write(config, case)
    cmd = [sys.executable, '-B', str(args.scripts / 'ui_loop.py'), 'native', '--config', str(config), '--output', str(OUT / 'raw-cycle'), '--intake']
    result = subprocess.run(cmd, capture_output=True, text=True)
    write(OUT / 'raw-request-run.json', {'argv': cmd, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    assert result.returncode == 2 and "'plan'" in result.stderr
    return {'classification': 'unsupported_raw_intake_format_not_runtime_wrong_decision', 'error': result.stderr.strip()}


def absent_target():
    b = setup('absence', ['idle-0-v2'], [('step-absent', 'session.step', 'present', [False])])
    result = cycle(b, 'cycle', final=True)
    auto = d.load(b[0] / 'cycle/capture/automatic.json')
    cov = d.load(b[0] / 'cycle/capture/execution-coverage.json')
    assert auto['status'] == 'passed' and result['status'] == 'invalid_or_incomplete_capture' and not cov['satisfied']
    return {'automatic_status': auto['status'], 'cycle_status': result['status'], 'missing_states': cov['missing_states'],
            'finding': 'Approved presence=false passes native assertion, but execution coverage requires observing the intentionally absent target.'}


def semantic_targets():
    details = []
    for name, rid, ident, prop in [('missing', 'step-present', 'session.step', 'present'), ('ambiguous', 'primary-unique', 'session.primary', 'unique')]:
        b = setup(name, ['running-2-v1'], [(rid, ident, prop, [True])], version='v1')
        result = cycle(b, 'cycle')
        auto = d.load(b[0] / 'cycle/capture/automatic.json'); diag = d.load(b[0] / 'cycle/after-diagnostics.json')
        route = d.load(b[0] / 'cycle/after-routes.json')
        assert auto['status'] == 'failed' and not diag['items']
        previous = b[0] / 'cycle/capture/result.json'
        (b[0] / 'production/PulseLab/SessionView.swift').write_bytes((DESIGN / 'sources/v2/PulseLab/SessionView.swift').read_bytes())
        repaired = cycle(b, 'repaired-cycle', previous=previous, previous_sha=sha(previous),
                         transport_options={'replacement': {0: 'running-2-v2'}})
        assert d.load(b[0] / 'repaired-cycle/retest-plan.json')['source_changed']
        assert d.load(b[0] / 'repaired-cycle/capture/automatic.json')['status'] == 'passed'
        assert d.load(b[0] / 'repaired-cycle/admission.json')['status'] == 'accepted'
        details.append({'case': name, 'automatic_status': auto['status'], 'diagnostic_items': len(diag['items']),
                        'next_actions': [t['action'] for t in route['tasks']], 'cycle_status': result['status'],
                        'fresh_repaired_source_rechecked': repaired['status']})
    return {'classification': 'safe_refusal_but_source_diagnosis_gap', 'cases': details,
            'finding': 'Definite missing/duplicate semantic failures get generic diagnose_product but no source/topology diagnostics because diagnose() skips failed rows.'}


def partial_and_bounded():
    b = setup('no-packet', ['running-2-v2'], [('phase', 'session.phase', 'label', ['Running'])])
    first = cycle(b, 'cycle-1', transport_options={'no_packet': True})
    previous = b[0] / 'cycle-1/capture/result.json'
    second = cycle(b, 'cycle-2', previous=previous, previous_sha=sha(previous), history=[{'path': str(b[0] / 'cycle-1/cycle.json'), 'sha256': sha(b[0] / 'cycle-1/cycle.json')}], transport_options={'no_packet': True})
    assert first['status'] == 'invalid_or_incomplete_capture' and second['status'] == 'blocked_repeated_unchanged_evidence'
    bad = setup('missing-png', ['running-2-v2'], [('phase', 'session.phase', 'label', ['Running'])])
    try:
        cycle(bad, 'cycle', transport_options={'missing_png': True})
        raise AssertionError('Expected rejection of missing PNG')
    except ValueError as exc:
        assert 'Native image missing' in str(exc)
        write(bad[0] / 'uncaught-error.json', {'type': type(exc).__name__, 'error': str(exc), 'capture_receipt_exists': (bad[0] / 'cycle/capture/result.json').exists(), 'cycle_receipt_exists': (bad[0] / 'cycle/cycle.json').exists()})
    return {'no_packet': first['status'], 'repeat_with_pinned_history': second['status'],
            'missing_png': 'ValueError escapes without capture/result.json or cycle.json; CLI normalizes it to exit 2.',
            'classification': 'missing_packet_safe_bounded; partial_packet_diagnostic_receipt_gap'}


def complete_and_fresh_source():
    oids = [s['after'] for s in HISTORY]
    trees = [d.load(DESIGN / CATALOG[oid]['native_tree']['path']) for oid in oids]
    props = [('phase', 'session.phase', 'label', [tree_value(t, 'session.phase') for t in trees]),
             ('count', 'session.count', 'label', [tree_value(t, 'session.count') for t in trees]),
             ('primary-unique', 'session.primary', 'unique', [True] * len(oids)),
             ('preview-unique', 'preview.primary', 'unique', [True] * len(oids))]
    b = setup('clean-and-edit', oids, props)
    first = cycle(b, 'clean', final=True)
    assert first['status'] == 'verified_capture'
    assert d.load(b[0] / 'clean/admission.json')['status'] == 'accepted'
    previous = b[0] / 'clean/capture/result.json'; original_sha = sha(previous)
    clone = b[0] / 'clone'; shutil.copytree(b[0] / 'production', clone)
    adoption_path = b[0] / 'adoption.json'
    loop.adopt_capture(previous, original_sha, [clone], adoption_path)
    current = b[0] / 'production/PulseLab/SessionView.swift'
    current.write_bytes((DESIGN / 'sources/v3/PulseLab/SessionView.swift').read_bytes())
    intake = loop.run_cycle(b[1], b[0] / 'edited-intake', previous=previous, previous_sha=original_sha, intake=True)
    planning = d.load(b[0] / 'edited-intake/retest-plan.json')
    assert planning['source_changed'] and planning['changed_files'] == ['0/PulseLab/SessionView.swift']
    final = cycle(b, 'edited-final', previous=previous, previous_sha=original_sha, final=True,
                  transport_options={'replacement': {12: 'idle-2-v3'}})
    assert d.load(b[0] / 'edited-final/capture/automatic.json')['status'] == 'failed'
    assert d.load(b[0] / 'edited-final/admission.json')['status'] == 'not_accepted'
    cloned_config = copy.deepcopy(b[1]); cloned_config['source_roots'] = [str(clone)]
    cloned_config['adoption'] = {'path': str(adoption_path), 'sha256': sha(adoption_path)}
    (clone / 'PulseLab/SessionView.swift').write_bytes(current.read_bytes())
    loop.run_cycle(cloned_config, b[0] / 'clone-intake', previous=previous, previous_sha=original_sha, intake=True)
    assert d.load(b[0] / 'clone-intake/retest-plan.json')['source_changed']
    assert sha(previous) == original_sha
    image = b[0] / 'clean/capture/native/frame-00.png'
    original_image = image.read_bytes(); image.write_bytes(original_image + b'changed')
    try:
        loop.run_cycle(b[1], b[0] / 'tampered-intake', previous=previous, previous_sha=original_sha, intake=True)
        raise AssertionError('Expected image tamper rejection')
    except ValueError as exc:
        assert 'Original capture image missing' in str(exc)
        write(b[0] / 'tamper-rejected.json', {'error': str(exc)})
    finally: image.write_bytes(original_image)
    return {'clean_typed_subset': 'accepted', 'fresh_source_changed_files': planning['changed_files'],
            'edited_final_native_report': 'failed', 'edited_final_admission': 'not_accepted',
            'clone_adoption_then_edit': 'source_changed detected', 'image_tamper': 'rejected',
            'scope': 'Typed phase/count/identity subset only; this does not satisfy the complete frozen prose/visual oracle.'}


def intake_cannot_final():
    b = setup('intake-final', ['idle-0-v2'], [('phase', 'session.phase', 'label', ['Idle'])])
    try:
        loop.run_cycle(b[1], b[0] / 'cycle', intake=True, final=True)
        raise AssertionError('Expected intake/final rejection')
    except ValueError as exc:
        assert 'Intake is diagnostic only' in str(exc)
        return {'rejected': str(exc)}


def pending_then_settled():
    b = setup('pending-then-settled', ['paused-2-v2'], [('phase', 'session.phase', 'label', ['Paused'])])
    first = cycle(b, 'pending-cycle', transport_options={'pending_first': True})
    report = d.load(b[0] / 'pending-cycle/capture/automatic.json')
    assert report['assertions'][0]['status'] == 'unassessed'
    previous = b[0] / 'pending-cycle/capture/result.json'
    second = cycle(b, 'settled-default-cycle', previous=previous, previous_sha=sha(previous),
                   history=[{'path': str(b[0] / 'pending-cycle/cycle.json'), 'sha256': sha(b[0] / 'pending-cycle/cycle.json')}])
    assert second['status'] == 'blocked_repeated_unchanged_evidence' and not second['native_executed']
    recovery = cycle(b, 'settled-final-cycle', previous=previous, previous_sha=sha(previous), final=True,
                     history=[{'path': str(b[0] / 'pending-cycle/cycle.json'), 'sha256': sha(b[0] / 'pending-cycle/cycle.json')}])
    assert recovery['status'] == 'verified_capture'
    assert d.load(b[0] / 'settled-final-cycle/admission.json')['status'] == 'accepted'
    return {'first_report': report['assertions'][0]['status'], 'first_reason': report['assertions'][0]['reason'],
            'default_next_cycle': second['status'], 'new_native_capture_attempted': second['native_executed'],
            'explicit_final_recovery': recovery['status'],
            'finding': 'History signature equates unchanged source/plan/states/unresolved IDs with unchanged evidence; a normal settled-state recapture is blocked before observing the now settled native state. Final bypass remains available.'}


for name, op in [('raw-intake-boundary', raw_boundary), ('approved-target-absence', absent_target),
                 ('missing-and-ambiguous-targets', semantic_targets), ('partial-and-bounded-evidence', partial_and_bounded),
                 ('clean-history-fresh-source-and-provenance', complete_and_fresh_source), ('intake-final-boundary', intake_cannot_final),
                 ('pending-to-settled-history', pending_then_settled)]:
    record(name, op)
write(OUT / 'tool-hashes.json', {p.name: sha(p) for p in sorted(args.scripts.glob('*.py'))})
print(json.dumps(results, indent=2))
raise SystemExit(0 if all(r['reproduced'] for r in results) else 1)
