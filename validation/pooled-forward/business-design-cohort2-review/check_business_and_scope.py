#!/usr/bin/env python3
"""Independent design arithmetic and metadata review. No UI/native observations."""
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import traceback
from run_pure_checks import C, O, R, MAPPING, SEAL, load, save, digest, sha_bytes

sys.dont_write_bytecode = True
sys.path.insert(0, str(R / 'cache/design-schema-python'))
from jsonschema import Draft202012Validator
sys.path.insert(0, str(R / 'candidate-v13.9/scripts'))
import design_contract as design
import execution_plan

# Independently transcribed from the five published briefs, not from author code.
SPECS = {
    'catering-package': dict(roots={'buffet': 'Buffet package', 'boxed': 'Boxed package'},
        details={'reusable': 'Reusable service', 'compostable': 'Compostable service'}, prefix='catering', number='guestCount',
        summary=('Package', 'Service', 'guests'), noun='package', detailnoun='service', ack='dietary counts',
        action='catering order', receipt='Catering order recorded.'),
    'training-pathway': dict(roots={'guided': 'Guided cohort', 'independent': 'Independent lab'},
        details={'certificate': 'Certificate assessment', 'practice': 'Practice only'}, prefix='training', number='completedHours',
        summary=('Pathway', 'Mode', 'completed hours'), noun='pathway', detailnoun='participation mode', ack='learning commitment',
        action='training enrollment', receipt='Training enrollment recorded.'),
    'subscription-capacity': dict(roots={'scale': 'Scale plan', 'team': 'Team plan'},
        details={'annual': 'Annual billing', 'monthly': 'Monthly billing'}, prefix='capacity', number='seatCount',
        summary=('Plan', 'Term', 'seats'), noun='plan', detailnoun='billing term', ack='capacity commitment',
        action='capacity change', receipt='Capacity change recorded.'),
    'visitor-preclearance': dict(roots={'research': 'Research floor', 'office': 'Office floor'},
        details={'research-badge': 'Research badge', 'visitor-escort': 'Visitor escort'}, prefix='visitor', number='guestCount',
        summary=('Area', 'Credential', 'visitors'), noun='access area', detailnoun='credential route', ack='visitor briefing',
        action='visitor clearance', receipt='Visitor clearance recorded.'),
    'candidate-disposition': dict(roots={'continue': 'Continue review', 'archive': 'Archive application'},
        details={'technical': 'Technical interview', 'recruiter': 'Recruiter screen', 'skills-gap': 'Skills gap', 'role-closed': 'Role closed'},
        prefix='candidate', number='portfolioScore', summary=('Disposition', 'Detail', 'portfolio points'), noun='disposition',
        detailnoun='next step or reason', ack='evidence review', action='candidate disposition', receipt='Candidate disposition recorded.')
}

def root_eligibility(task, x):
    if task == 'catering-package':
        return {'buffet': 6 <= x['guestCount'] <= x['buffetCapacity'],
                'boxed': x['guestCount'] <= x['boxedCapacity'] and x['vegetarianMeals'] >= x['vegetarianGuests']}
    if task == 'training-pathway':
        foundation = 'foundation' in x['completedModules']
        return {'guided': foundation and x['completedHours'] >= 8 and x['cohortSeats'] >= 1,
                'independent': foundation and x['completedHours'] >= 4 and x['deviceCredits'] >= 2}
    if task == 'subscription-capacity':
        return {'scale': 10 <= x['seatCount'] <= x['scaleQuota'],
                'team': 2 <= x['seatCount'] <= 25 and x['seatCount'] <= x['teamQuota']}
    if task == 'visitor-preclearance':
        both = x['sponsorActive'] and x['guestCount'] > 0
        return {'research': both and x['badgeTrainingComplete'] and x['guestCount'] <= x['researchCapacity'],
                'office': both and x['guestCount'] <= x['officeCapacity']}
    if task == 'candidate-disposition':
        return {'continue': x['portfolioScore'] >= 60 and x['reviewerCapacity'] >= 1, 'archive': not x['legalHold']}
    raise ValueError(task)

def detail_eligibility(task, x, root):
    valid = root is not None and root_eligibility(task, x)[root]
    if task == 'catering-package':
        return {'reusable': valid and root == 'buffet' and x['reusableSets'] >= x['guestCount'],
                'compostable': valid and x['compostableSets'] >= x['guestCount']}
    if task == 'training-pathway':
        return {'certificate': valid and root == 'guided' and x['completedHours'] >= 12 and x['assessmentSlots'] >= 1,
                'practice': valid and x['practiceSeats'] >= 1}
    if task == 'subscription-capacity':
        return {'annual': valid and root == 'scale' and x['prepaidMonths'] >= 12,
                'monthly': valid and x['accountBalanceCents'] >= 0}
    if task == 'visitor-preclearance':
        return {'research-badge': valid and root == 'research' and x['verifiedIDs'] >= x['guestCount'] and x['labInductions'] >= x['guestCount'],
                'visitor-escort': valid and x['escortCount'] >= x['guestCount']}
    if task == 'candidate-disposition':
        return {'technical': valid and root == 'continue' and x['portfolioScore'] >= 75 and x['technicalSlots'] >= 1,
                'recruiter': valid and root == 'continue' and x['recruiterSlots'] >= 1,
                'skills-gap': valid and root == 'archive' and x['assessmentCount'] >= 1,
                'role-closed': valid and root == 'archive' and x['openRoleCount'] == 0}
    raise ValueError(task)

def empty():
    return {'root': None, 'detail': None, 'ack': False, 'recorded': False}

def visible(task, x, local):
    spec = SPECS[task]
    root, detail = local['root'], local['detail']
    roots, details = root_eligibility(task, x), detail_eligibility(task, x, root)
    valid = bool(root is not None and roots[root] and detail is not None and details[detail])
    root_label = spec['roots'][root] if root else 'Not chosen'
    detail_label = spec['details'][detail] if detail else 'Not chosen'
    if local['recorded']: status = 'Recorded. Selections are locked for this request.'
    elif not any(roots.values()): status = 'No ' + spec['noun'] + ' is eligible for these request details.'
    elif root is None: status = 'Choose a ' + spec['noun'] + '.'
    elif detail is None: status = 'Choose a ' + spec['detailnoun'] + ' for ' + root_label + '.'
    elif not local['ack']: status = 'Confirm the ' + spec['ack'] + ' to continue.'
    else: status = 'Ready to record ' + spec['action'] + '.'
    a, b, suffix = spec['summary']
    result = {'title-label': x['title'], 'context-label': x['context'], 'notes-label': '\n\n'.join(x['notes']),
              'status-label': status,
              'summary-label': f'{a}: {root_label}. {b}: {detail_label}. {x[spec["number"]]} {suffix}.',
              'receipt-label': spec['receipt'] if local['recorded'] else 'No request recorded.',
              'submit-enabled': valid and local['ack'] and not local['recorded'],
              'ack-enabled': valid and not local['recorded'], 'ack-selected': local['ack']}
    for key, eligible in roots.items():
        result['root-' + key + '-enabled'] = eligible and not local['recorded']
        result['root-' + key + '-selected'] = key == root
    for key, eligible in details.items():
        result['detail-' + key + '-enabled'] = bool(eligible and not local['recorded'])
        result['detail-' + key + '-selected'] = key == detail
    return result

def simulate(task, family):
    p = C / family / 'tasks' / task
    fixtures = load(p / 'ios/fixtures.json')
    android_fixtures = load(p / 'android/fixtures.json')
    inputs = [fixtures['initial']] + fixtures['updates']
    assert inputs == [android_fixtures['initial']] + android_fixtures['updates']
    schema = load(C / 'public/tasks' / task / 'fixture.schema.json')
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for x in inputs:
        validator.validate(x)
        assert set(x) == set(schema['properties']) == set(schema['required'])
        assert not any(re.search(r'(^|_)(ready|selected|expected|decision|state|test|private|fixtureIndex)($|_)', key, re.I) for key in x)
    flow, expected = load(p / 'flow.json'), load(p / 'outcomes.json')
    actions = flow['logical_actions']
    assert len(actions) == (18 if family == 'public' else 21) and len(actions) <= 25
    assert len(flow['states']) == (11 if family == 'public' else 13)
    local, input_index = empty(), 0
    current = inputs[0]
    action_events = []
    states = []
    by_after = {s['after_action']: s for s in flow['states']}
    for index, action in enumerate(actions):
        events = []
        before_visible = visible(task, current, local)
        for condition in action.get('preconditions', []):
            target = condition['target']
            atom = target.replace(':', '-') + '-' + condition['property']
            if target == 'ack': atom = 'ack-' + condition['property']
            if target == 'submit': atom = 'submit-' + condition['property']
            assert condition['op'] == 'eq' and before_visible[atom] == condition['expected'], (task, family, index, condition)
        if action['type'] == 'tap':
            target = action['target']
            assert any(c['target'] == target and c['property'] == 'enabled' and c['expected'] is True for c in action['preconditions'])
            if target.startswith('root:'):
                root = target.split(':', 1)[1]
                assert before_visible['root-' + root + '-enabled']
                if local['root'] != root: local = dict(local, root=root, detail=None, ack=False)
            elif target.startswith('detail:'):
                detail = target.split(':', 1)[1]
                assert before_visible['detail-' + detail + '-enabled']
                if local['detail'] != detail: local = dict(local, detail=detail, ack=False)
            elif target == 'ack':
                assert before_visible['ack-enabled']
                local['ack'] = not local['ack']
            elif target == 'submit':
                assert before_visible['submit-enabled']
                assert any(c['target'] == 'ack' and c['property'] == 'selected' and c['expected'] is True for c in action['preconditions'])
                spec = SPECS[task]
                events = ['|'.join([spec['prefix'], current['entityID'], str(current['revision']), local['root'], local['detail'], str(current[spec['number']])])]
                assert action['expect_callback'] == events[0]
                local['recorded'] = True
            else: raise AssertionError(target)
        elif action['type'] == 'apply_next_fixture':
            input_index += 1
            incoming = inputs[input_index]
            if (current['entityID'], current['revision']) != (incoming['entityID'], incoming['revision']):
                local = empty()
            elif local['root'] is not None and not root_eligibility(task, incoming)[local['root']]:
                local = empty()
            elif local['detail'] is not None and not detail_eligibility(task, incoming, local['root'])[local['detail']]:
                local = dict(local, detail=None, ack=False, recorded=False)
            current = incoming
        else:
            assert action['type'] == 'sweep'
        action_events.append(events)
        if index in by_after:
            state = by_after[index]
            callback_delta = action_events[state.get('stimulus_action', index)]
            observed = {'input_index': input_index, 'local': copy.deepcopy(local), 'visible': visible(task, current, local), 'callback_delta': callback_delta}
            assert expected[state['id']] == observed, (task, family, state['id'], expected[state['id']], observed)
            states.append({'id': state['id'], 'passed': True, 'expected_sha256': digest(observed), 'coverage': state['coverage']})
    assert set(expected) == {s['id'] for s in flow['states']}
    return {'task': task, 'family': family, 'passed': True, 'input_count': len(inputs), 'state_count': len(states),
            'original_action_count': len(actions), 'states': states, 'native_execution': False}

def profile_metadata(profile_id, profile):
    platform, task, family = profile['intended_platform'], profile['task'], profile['family']
    path = C / Path(profile['profile_path']).parent
    lock, plan, bindings, policy = [load(path / p) for p in ['lock.json', 'generated/plan.json', 'bindings.json', 'policy.json']]
    reference = load(path / 'reference.json')
    flow = load(path.parent / 'flow.json')
    expected = load(path.parent / 'outcomes.json')
    spec = SPECS[task]
    labels = [bindings['root:' + x]['label'] for x in spec['roots']] + [bindings['detail:' + x]['label'] for x in spec['details']]
    assert labels == list(spec['roots'].values()) + list(spec['details'].values())
    assert bindings['ack'] == {'label': 'I confirm the ' + spec['ack'], 'role': 'button'}
    assert bindings['submit'] == {'label': 'Record ' + spec['action'], 'role': 'button'}
    assert len(labels) == len(set(labels))
    for target in ['surface', 'title', 'context', 'notes', 'summary', 'status', 'receipt']:
        assert bindings[target]['identifier']
    assert all(x.get('role') == 'button' and set(x) == {'label', 'role'} for k, x in bindings.items() if k.startswith(('root:', 'detail:')))
    by_state = {s['id']: s for s in plan['states']}
    for state, expected_state in expected.items():
        for atom, value in expected_state['visible'].items():
            assert reference['states'][state][atom] == {'value': value, 'unit': 'bool' if type(value) is bool else 'string'}
    for assertion in plan['assertions']:
        assert assertion['expectation_provenance'] and assertion['source'] == 'design-lock:' + profile['design_sha256']
        for p in assertion['expectation_provenance']:
            assert p['source'] in lock['sources'] and p['sha256'] == lock['sources'][p['source']]['sha256']
            assert design.pointer(lock['sources'][p['source']]['document'], p['pointer']) == p['source_datum']
        if assertion['kind'] == 'geometry':
            assert assertion['op'] == 'gte' and assertion['expected'] == 48
            assert assertion['unit'] == ('pt' if platform == 'ios' else 'dp')
            assert assertion['basis'] == 'control' and assertion['measurement'] == 'accessibility_box'
        if assertion['kind'] == 'text_layout':
            assert platform == 'android'
            assert assertion.get('op', 'eq') == ('gte' if assertion['property'] == 'lines' else 'eq')
        if assertion['kind'] == 'event':
            stimulus = flow['logical_actions'][assertion['action_index']]
            assert stimulus['type'] == ('tap' if assertion['requirement_id'] == 'activation-events' else 'apply_next_fixture')
            assert assertion['expected'] == expected[assertion['state']]['callback_delta']
        if assertion['requirement_id'] in {'body-wrap', 'content-overlap', 'horizontal-fit', 'type-hierarchy'}:
            assert by_state[assertion['state']]['coverage'] == 'full_content'
            assert assertion['unit'] == 'bool' and assertion['expected'] is True
    for atom in policy['atoms']:
        if atom['method'] == 'native_pixels':
            s = atom['sampling']
            assert s['region'] == ([0.02, 0.2, 0.035, 0.8] if atom['rule_id'] == 'surface-fill' else [0.02, 0.25, 0.035, 0.75])
            assert s['minimum_pixels'] == 12 and s['minimum_support'] == 0.9 and s['channel_tolerance'] == 0
            assert s['visibility'] == ('visible_fragment' if atom['rule_id'] == 'surface-fill' else 'fully_visible')
        else:
            assert atom['method'] == 'visual' and atom['question']['source'] == 'reference'
            assert design.pointer(reference, atom['question']['pointer'])['unit'] == 'string'
    execution = load(path / 'execution/execution.json')
    config = load(C / profile['profile_path'])
    for index, action in enumerate(execution['actions']):
        assert action['depends_on'] == ([index - 1] if index else [])
    for state in flow['states']:
        action = execution['actions'][state['after_action']]
        assert action['capture_scope'] == state['coverage']
        if state['coverage'] == 'targets': assert action['after_targets']
    # Pure targeted compilation explicitly omits later truth, retaining the exact prefix.
    selected = flow['states'][1]['id']
    partial = execution_plan.compile_execution(plan, lock, config['design_sha256'], load(config['fixtures']), sha_bytes(Path(config['bridge']).read_bytes()), launch_ref=config['launch_ref'], states=[selected])
    assert partial['scope'] == 'targeted' and partial['selected_states'] == [selected]
    assert partial['executed_action_count'] == flow['states'][1]['after_action'] + 1
    assert plan == load(path / 'generated/plan.json')
    denominator = load(path / 'denominator.json')
    required = {x['assertion_id'] for x in denominator if x['disposition'] == 'required'}
    assert required == set(plan['required_assertion_ids'])
    cells = plan['matrix_contract']['cells']
    assert len(cells) == len(plan['states']) * len(lock['contract']['rules'])
    assert {(c['state'], c['requirement_id']) for c in cells} == {(s['id'], r['id']) for s in plan['states'] for r in lock['contract']['rules']}
    for c in cells:
        d = next(v for v in denominator if v['state'] == c['state'] and v['rule_id'] == c['requirement_id'])
        assert d['disposition'] == ('N/A' if c['disposition'] == 'not_applicable' else 'required')
        if d['disposition'] == 'N/A': assert d['reason']
    claims = reference['responsibilities']
    source = [x for x in claims if x['method'] == 'source']
    assert {(x['id'], x['owner'], x['subject'], x['priority']) for x in source} == {
        ('production-api', 'component', 'production_api', 'must'), ('thin-bridge', 'bridge', 'thin_bridge', 'must'),
        ('production-placement', 'integration', 'production_placement', 'must')}
    for arm in ['candidate-v13.9', 'baseline-v12.6-common-6']:
        cp = O / 'shared-preflight' / arm / profile_id
        compiled = load(cp / 'responsibility-capabilities.json')
        result = load(cp / 'RESULT.json')
        assert compiled['issues'] == []
        assert set(result['evidence_truth_still_unassessed']) == {x['id'] for x in claims}
        for claim in compiled['claims']:
            if claim['method'] != 'source':
                assert claim['rule_ids'] and claim['assertion_ids']
                assert set(claim['assertion_ids']) <= set(plan['required_assertion_ids'])
    if platform == 'ios':
        unavailable = [x for x in denominator if x['kind'] == 'text_layout']
        assert len(unavailable) == len(plan['states']) * 12 and all(x['disposition'] == 'N/A' for x in unavailable)
        assert all('TextLayout' in x['reason'] and 'not an evaluated pass' in x['reason'] for x in unavailable)
        assert not any(x['method'] == 'text_layout' for x in claims)
    return {'profile_id': profile_id, 'passed': True, 'required': len(required), 'denominator_cells': len(denominator),
            'full_content_states': sum(s['coverage'] == 'full_content' for s in plan['states']),
            'checkpoint_states': sum(s['coverage'] == 'targets' for s in plan['states']), 'source_duties_unassessed': 3,
            'all_native_groups_nonempty': True, 'targeted_scope_keeps_omissions_unassessed': True}

def numeric_domain_check():
    issues = []
    results = []
    for task in SPECS:
        public = C / 'public/tasks' / task
        schema = load(public / 'fixture.schema.json')
        input = load(public / 'ios/fixtures.json')['initial']
        validator = Draft202012Validator(schema)
        unsupported = []
        for field, declaration in schema['properties'].items():
            if declaration['type'] != 'integer': continue
            trial = dict(input, **{field: 2 ** 31})
            if validator.is_valid(trial): unsupported.append(field)
        api = (public / 'API.md').read_text()
        assert all('val ' + field + ': Int' in api for field in unsupported)
        bridge = (public / 'android/ObserverBridge.kt').read_text()
        assert all('fixture.get("' + field + '").asInt' in bridge for field in unsupported)
        result = {'task': task, 'integer_fields_accepting_2147483648_beyond_Kotlin_Int': unsupported,
                  'schema_boundaries_match_exact_native_API': not unsupported,
                  'scope': 'Pure schema/type-contract contradiction, no native observation or new sealed test case.'}
        results.append(result)
        if unsupported:
            issues.append({'id': 'INPUT-DOMAIN-' + task, 'priority': 'blocking-design', 'task': task,
                'summary': 'The schema claims valid native Int inputs outside the exact published Kotlin Int API/bridge range.',
                'evidence': {'schema': str((public / 'fixture.schema.json').relative_to(C)),
                             'brief': str((public / 'BRIEF.md').relative_to(C)), 'api': str((public / 'API.md').relative_to(C)),
                             'bridge': str((public / 'android/ObserverBridge.kt').relative_to(C)),
                             'fields': unsupported, 'schema_accepted_value': 2 ** 31, 'maximum_Kotlin_Int': 2 ** 31 - 1}})
    return {'passed': not issues, 'issues': issues, 'tasks': results}

def main():
    rows, errors = [], []
    for task in SPECS:
        for family in ['public', 'private']:
            try: rows.append(simulate(task, family))
            except Exception as e:
                errors.append({'task': task, 'family': family, 'error': repr(e), 'traceback': traceback.format_exc()})
    save(O / 'business-state-checks.json', {'passed': not errors, 'families': rows, 'errors': errors,
        'native_execution': False, 'source_truth_approved': False, 'expected_table_truth_only': True})
    mapping = load(C / 'APPROVAL-MAPPING.json')
    profile_rows, profile_errors = [], []
    for pid, profile in mapping['profiles'].items():
        try: profile_rows.append(profile_metadata(pid, profile))
        except Exception as e:
            profile_errors.append({'profile_id': pid, 'error': repr(e), 'traceback': traceback.format_exc()})
    master = load(C / 'MASTER-DENOMINATOR.json')
    reconstructed = []
    for pid, profile in mapping['profiles'].items():
        denominator = load(C / Path(profile['profile_path']).parent / 'denominator.json')
        reconstructed += [dict(task=profile['task'], family=profile['family'], **c) for c in denominator]
    assert reconstructed == master['cells']
    assert Counter(c['disposition'] for c in reconstructed) == master['counts']
    identities = [(c['task'], c['family'], c['state'], c['rule_id'], c['platform']) for c in reconstructed]
    assert len(identities) == len(set(identities))
    assert master['native_actuals'] == 'not_run' and master['source_review_actuals'] == 'unassessed'
    save(O / 'metadata-denominator-checks.json', {'passed': not profile_errors, 'profiles': profile_rows, 'errors': profile_errors,
        'master_exact_reconstructed': True, 'counts': master['counts'], 'total_cells': len(reconstructed)})
    private_markers = set()
    for task in SPECS:
        f = load(C / 'private/tasks' / task / 'ios/fixtures.json')
        private_markers |= {x['entityID'] for x in [f['initial']] + f['updates']}
    leakage = []
    for p in (C / 'public').rglob('*'):
        if not p.is_file(): continue
        content = p.read_text()
        found = [m for m in private_markers if m in content]
        if found: leakage.append({'public_file': str(p.relative_to(C)), 'private_marker_count': len(found)})
        assert '/private/tasks/' not in content
    save(O / 'public-private-boundary-checks.json', {'passed': not leakage, 'leaks': leakage,
        'public_lock_sources_only_own_family': all(set(load(C / p['paths']['design_lock'])['sources']) == {'reference', 'launch'} for p in mapping['profiles'].values()),
        'private_markers_scanned': len(private_markers), 'public_worker_scope': 'Only public/tasks/<assigned-task>/**'})
    numeric = numeric_domain_check()
    save(O / 'input-domain-checks.json', numeric)
    print(json.dumps({'finite_business_families_passed': len(rows), 'business_errors': errors,
        'profile_metadata_passed': len(profile_rows), 'profile_errors': profile_errors,
        'leaks': leakage, 'numeric_domain_admitted': numeric['passed'], 'numeric_domain_issue_count': len(numeric['issues'])}))
    return 0 if not errors and not profile_errors and not leakage else 1

if __name__ == '__main__':
    raise SystemExit(main())
