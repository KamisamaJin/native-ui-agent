"""Freeze prepared test inputs and launch requests; performs no native operation."""
from pathlib import Path
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT.parent / 'development/candidate-attempt-1'

def load(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def main():
    if (ROOT / 'SEAL.json').exists():
        raise SystemExit('Existing neutral inputs are sealed; create a new revision instead.')
    approval = load(ROOT / 'APPROVAL.json')
    requests = []
    oracle_cases = []
    for case in ['ordinary400', 'narrow280-large']:
        plan = load(ROOT / ('generated/' + case + '/design/plan.json'))
        fixture = load(ROOT / ('inputs/' + case + '.json'))
        oracle_cases.append({'case': case, 'required_assertion_ids': plan['required_assertion_ids'],
            'required_state_definitions': plan['states'],
            'required_environment': {'theme': 'light', 'dynamic_type': fixture['dynamic_type'], 'direction': 'ltr', 'offered_width_pt': fixture['width'], 'viewport_height_pt': 600},
            'required_action_facts': [
                {'action_index': 1, 'outcome': 'tapped', 'method': 'xcui_tap', 'attempted': True, 'succeeded': True, 'callback_delta': ['notes.reviewed.A'], 'input_index': 0},
                {'action_index': 2, 'outcome': 'updated', 'method': 'caller_fixture_update', 'attempted': True, 'succeeded': True, 'callback_delta': [], 'input_before': 0, 'input_after': 1, 'same_instance': True},
                {'action_index': 4, 'outcome': 'blocked_disabled', 'enabled': False, 'dispatch_attempted': False, 'callback_delta_literal': [], 'callback_behavior_verdict': 'not_assessed_for_blocked_dispatch'},
            ],
            'completion_rules': [
                'Reconstruct the original plan and execution manifest from the pinned design lock before reading results.',
                'Retain all 66 required rows, including every manual unassessed row; never promote captured or process success to product success.',
                'Check exact native state/input/process/event binding and actual environment before evaluating product facts.',
                'Ready and replaced require top-to-bottom overlapping native coverage with a real bottom; target checkpoints need every declared target in their own state binding.',
                'Review all full-content images for layout and wrapping, and exact target frames for surface/action appearance; bind decisions to original screenshot SHA256 values.',
                'Log missing coverage, torn geometry, ambiguous selectors, unsupported properties and observer errors separately from confirmed component defects.',
                'Compare both strategies only after source, input and required state/target/callback equality is verified. No outcome or speed advantage is assumed.',
            ]})
        for strategy in ['legacy', 'coalesced']:
            generated = ROOT / 'generated' / case / strategy
            argv = [sys.executable, '-B', str(SNAPSHOT / 'scripts/execution_plan.py'),
                '--run', '--execution', str(generated / 'execution.json'),
                '--plan', str(ROOT / 'generated' / case / 'design/plan.json'),
                '--design-lock', str(ROOT / 'design/lock.json'), '--design-sha256', approval['design_lock_sha256'],
                '--fixtures', str(ROOT / 'inputs' / (case + '.json')), '--bridge', str(ROOT / 'source/Bridge.swift'),
                '--launch-source', 'launch', '--launch-pointer', '/' + case, '--strategy', strategy,
                '--source-root', str(ROOT / 'source/Bridge.swift'),
                '--simulator', 'CA7BB2E0-0C2B-49C1-B368-5D0DC816F4D2',
                '--developer-dir', '/Applications/Xcode.app/Contents/Developer', '--sdk', 'iphonesimulator',
                '--build-cache', str(ROOT / 'build-cache'), '--output', str(ROOT / 'captures' / case / strategy)]
            requests.append({'case': case, 'strategy': strategy, 'execution_manifest': str(generated / 'execution.json'),
                             'argv': argv, 'executed': False})
    write('oracle.json', {'version': 1, 'frozen_before_launch': True,
         'design_lock_sha256': approval['design_lock_sha256'], 'cases': oracle_cases,
         'unsupported_claims': ['Public SwiftUI AX cannot prove computed fonts, colors, internal padding or physical touch bounds.', 'This component host cannot prove integration in an unrelated production app.']})
    write('launch-requests.json', {'version': 1, 'native_launch_authorized_to_parent_after_seal': True,
         'native_launch_performed_by_preparer': False, 'owned_simulator_runtime': 'iOS 26.5', 'requests': requests})
    files = {str(p.relative_to(ROOT)): sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name != 'SEAL.json' and '__pycache__' not in p.parts}
    consumed = [SNAPSHOT / 'SKILL.md']
    consumed += [SNAPSHOT / 'references' / name for name in ['platforms.md', 'native-tools.md', 'state-evidence.md', 'design-contract.md', 'decision-feedback.md', 'native-precision.md']]
    consumed += sorted((SNAPSHOT / 'scripts').glob('*.py'))
    consumed += [SNAPSHOT / 'assets/ios-observer' / name for name in ['ObserverApp.swift', 'ObserverTests.swift', 'CONTRACT.md']]
    repo = ROOT.parents[2]
    consumed += [repo / 'native-ui-agent/assets/ios-observer' / name for name in ['ObserverApp.swift', 'ObserverTests.swift', 'CONTRACT.md', 'ProbeBridge.swift']]
    # Included scripts pin potential runtime imports too; unread scripts are not an information source.
    seal = {'version': 1, 'sealed_unix': time.time(), 'status': 'frozen_before_native_launch',
        'source_and_test_inputs_sha256': files,
        'snapshot_and_host_interface_sha256': {str(p): sha(p) for p in consumed},
        'design_lock_sha256': approval['design_lock_sha256'], 'routes_sha256': approval['routes_sha256'],
        'bridge_sha256': approval['bridge_sha256'],
        'native_sdk_execution_performed': False, 'device_manipulation_performed': False, 'web_used': False,
        'rule': 'Do not alter any listed neutral source or input before capture. Additional capture/review artifacts may be created in new paths. Preserve this seal and this attempt.'}
    write('SEAL.json', seal)
    print(json.dumps({'seal_path': str(ROOT / 'SEAL.json'), 'seal_file_sha256': sha(ROOT / 'SEAL.json'),
                      'neutral_files': len(files), 'external_pins': len(seal['snapshot_and_host_interface_sha256']),
                      'design_lock_sha256': approval['design_lock_sha256'], 'bridge_sha256': approval['bridge_sha256']}, indent=2))

if __name__ == '__main__':
    main()
