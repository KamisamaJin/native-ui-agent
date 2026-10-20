#!/usr/bin/env python3
"""Source-independent atomic expansion and mandatory stimulus preconditions.

No business UI judging. The independent evaluator supplies scoped raw evidence;
this shared check prevents it from turning an undelivered stimulus into a callback
behavior PASS/FAIL. The public artifact schema precedes fresh business outputs.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

R = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('frozen_native_checks', R / 'candidate-v4/scripts/native_checks.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value): return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def expand(oracle, phase):
    assert phase in {'d0', 'final'}
    rows = []
    seen = set()
    for case in oracle['cases']:
        if phase == 'd0' and case['split'] != 'initial': continue
        assert len(case['models']) <= 2 and len(case['checkpoints']) > 0
        assert sum(c['trigger']['type'] != 'initial' for c in case['checkpoints']) <= 8
        assert sum(c.get('full_content') is True for c in case['checkpoints']) <= 2
        for checkpoint in case['checkpoints']:
            trigger = checkpoint['trigger']
            assert trigger['type'] in {'initial', 'activate', 'replaceModel'}
            assert checkpoint['model'] in case['models']
            for item in checkpoint['assertions']:
                assert 'expected' in item and item['category'] in {'business', 'visual', 'integration', 'source_api', 'capability'}
                for platform in item.get('platforms', [item['platform']] if 'platform' in item else ['ios', 'android']):
                    assert platform in {'ios', 'android'}
                    row = copy.deepcopy(item)
                    row.update(platform=platform, key='/'.join([case['id'], checkpoint['id'], item['id']]),
                               caseId=case['id'], stateId=checkpoint['id'], modelId=checkpoint['model'],
                               trigger=trigger, full_content=checkpoint.get('full_content', False),
                               aspect=item.get('aspect', item['method']), sourceOnly=False)
                    if row['category'] == 'business' and trigger['type'] != 'initial':
                        assert row.get('requires_stimulus') is True, 'Post-stimulus business assertion lacks precondition'
                    identity = (platform, row['key']); assert identity not in seen
                    seen.add(identity); rows.append(row)
    for item in oracle.get('source_assertions', []):
        for platform in item.get('platforms', [item['platform']] if 'platform' in item else ['ios', 'android']):
            row = copy.deepcopy(item)
            row.update(platform=platform, key='source/' + item['id'], caseId='source', stateId='source',
                       category='source_api', aspect='source_api', sourceOnly=True, method='source_api',
                       requires_stimulus=False)
            identity=(platform,row['key']); assert identity not in seen
            seen.add(identity); rows.append(row)
    return rows


def stimulus_gate(row, mapping, observation):
    """The actual common gate is authoritative for callback behavior preconditions."""
    if row['sourceOnly']: return {'required': False, 'established': True}
    required = row['method'] == 'callback' or row.get('requires_stimulus') is True
    if not required: return {'required': False, 'established': True}
    index = mapping.get('trigger_action_index')
    steps = (observation or {}).get('steps', [])
    if type(index) is not int or not 0 <= index < len(steps):
        return {'required': True, 'established': False, 'reason': 'No actual native stimulus record'}
    trigger = row['trigger']['type']
    if trigger not in {'activate', 'replaceModel'}:
        return {'required': True, 'established': False, 'reason': 'No activation/replacement stimulus at this checkpoint'}
    step = steps[index]
    if row['method'] == 'callback':
        expected = row['expected']; assert isinstance(expected, list)
    else:
        # Test establishment only; other assertions judge their own actual UI
        # aspect. This must not hide a separately failing callback assertion.
        expected = [v.get('event') if isinstance(v, dict) else v for v in step.get('callback_delta', [])]
    verdict = checks.callback_verdict(step, expected, row['platform'],
                                     row.get('required_method', row['trigger'].get('method')),
                                     'caller_update' if trigger == 'replaceModel' else 'activation')
    return {'required': True, 'established': verdict['stimulus_established'], 'verdict': verdict}


def validate_precondition_outcome(row, graded, mapping, observation):
    assert graded['outcome'] in {'PASS', 'FAIL', 'UNASSESSED'}
    gate = stimulus_gate(row, mapping, observation)
    if graded['outcome'] != 'UNASSESSED' and gate['required']:
        assert gate['established'], 'P/F without demonstrated requested native stimulus: ' + row['key']
        if row['method'] == 'callback':
            expected = {'passed': 'PASS', 'failed': 'FAIL', 'unassessed': 'UNASSESSED'}[gate['verdict']['status']]
            assert graded['outcome'] == expected, 'Callback grade contradicts shared behavior gate: ' + row['key']
    return gate


def self_test():
    row={'platform':'ios','key':'generic/action/event','sourceOnly':False,'category':'business',
         'method':'callback','expected':['done'],'requires_stimulus':True,'trigger':{'type':'activate'}}
    before={'pid':1,'instance':'generic','fixture_index':0,'input_sha256':'fixed','event_revision':0}
    step={'outcome':'unavailable','callback_delta':[],'binding_after':before,
          'dispatch':{'attempted':False,'succeeded':False}}
    mapping={'trigger_action_index':0};observation={'steps':[step]}
    for outcome in ['PASS','FAIL']:
        try: validate_precondition_outcome(row,{'outcome':outcome},mapping,observation)
        except AssertionError: pass
        else: raise AssertionError('An undelivered stimulus was graded as behavior')
    validate_precondition_outcome(row,{'outcome':'UNASSESSED'},mapping,observation)
    step.update(outcome='tapped',dispatch={'attempted':True,'succeeded':True,'stimulus':'activation','method':'xcui_tap',
                'binding_before':before,'event_start':0,'event_end':0,'matches':1,'native_controls':1,'enabled':True})
    validate_precondition_outcome(row,{'outcome':'FAIL'},mapping,observation)
    try: validate_precondition_outcome(row,{'outcome':'PASS'},mapping,observation)
    except AssertionError: pass
    else: raise AssertionError('Successfully delivered missing callback was called PASS')
    print('Shared stimulus precondition rejects both false PASS and false FAIL; no business example used.')


if __name__ == '__main__': self_test()
