"""SDK-free independent T1 design reconstruction; never imports product code."""
import copy
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'validation/feedback-forward'
DESIGN = BASE / 'design/T1/public'
OUT = Path(__file__).resolve().parent / 'reconstruction-attempt3'
FROZEN = BASE / 'candidate-v9'
sys.dont_write_bytecode = True
sys.path.insert(0, str(FROZEN / 'scripts'))
import design_contract as dc
import execution_plan as ep
import review_contract as rc
import requirement_routes as rr
import native_checks as nc

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(rel, value):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as s:
        s.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

checks = []
def check(label, fn, expect_rejection=False):
    start = time.time()
    try:
        result = fn()
        if expect_rejection:
            raise AssertionError('Expected rejection did not occur')
        checks.append(dict(name=label, startedAtUnix=start, finishedAtUnix=time.time(), status='passed'))
        return result
    except ValueError as e:
        if not expect_rejection:
            raise
        checks.append(dict(name=label, startedAtUnix=start, finishedAtUnix=time.time(), status='expected_rejection', reason=str(e)))

def same(a, b):
    assert a == b
    return True

def seal_check():
    seal = dc.load(DESIGN / 'SEAL.json')
    for rel, digest in seal['files'].items():
        assert sha(DESIGN / rel) == digest, rel
    return {'files': len(seal['files']), 'matched': True}

seal_result = check('all supplied design seal byte hashes', seal_check)
approval = dc.load(DESIGN / 'approval.json')
lock = dc.load(DESIGN / 'design-lock.json')
lock_sha = approval['design_lock_sha256']
check('frozen seal reconstruction equals supplied design lock', lambda: same(dc.seal(DESIGN / 'contract.json', DESIGN), lock))
check('lock canonical SHA and all typed source expressions', lambda: dc.validate_lock(lock, lock_sha))
reference = lock['sources']['reference']['document']
policy = dc.load(DESIGN / 'policy.json')
routes = dc.load(DESIGN / 'routes.json')
bindings = dc.load(DESIGN / 'bindings.json')
crosswalk = dc.load(DESIGN / 'requirement-crosswalk.json')
check('sealed crosswalk and published crosswalk clauses agree', lambda: same(reference['requirement_crosswalk'], crosswalk['clauses']))
check('sealed compatibility and published compatibility agree', lambda: same(reference['compatibility'], dc.load(DESIGN / 'compatibility.json')))
check('checker interface byte SHA pin', lambda: same(sha(BASE / 'check_minimum_api.py'), reference['compatibility']['shared_checker']['sha256']))
source_policy = dc.load(DESIGN / 'implementation-audit.json')
spec = importlib.util.spec_from_file_location('scoped_implementation_audit', ROOT / 'tools/implementation_audit.py')
ia = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ia)
assert ia.d is dc
defs = check('shared source-audit actual definitions API using preloaded frozen design_contract', lambda: ia.catalog(lock, lock_sha, source_policy, approval['implementation_audit_sha256'], OUT / 'no-production-source', DESIGN, definition_only=True))
save('source-audit-definitions.json', defs)
check('source-audit definitions reproduce design author output', lambda: same(defs, dc.load(DESIGN / 'compiled/source-audit-definitions.json')))
check('definition-only catalog cannot bind actual acceptance', lambda: ia.bind(defs, {}), True)

summary = []
semantic = []
for case in ['P1', 'P2']:
    fixtures = dc.load(DESIGN / 'cases' / case / 'fixtures.json')
    models = [fixtures['initial']] + fixtures['updates']
    assert len(models) == 2
    assert models[0]['id'] != models[1]['id']
    for model in models:
        assert all(isinstance(model[k], str) for k in ['id','title','destination','temperatureRange'])
        assert all(type(model[k]) is bool for k in ['sealIntact','coolantReady'])
        assert len(model['notes']) == 8
        assert len({n['id'] for n in model['notes']}) == len(model['notes'])
        assert all(isinstance(n[k], str) for n in model['notes'] for k in ['id','title','body'])
    assert dc.digest(models[0]) == reference['cases'][case]['original_initial_sha256']
    assert dc.digest(models[1]) == reference['cases'][case]['original_update_sha256']
    for platform in ['ios', 'android']:
        key = case + '/' + platform
        actions = dc.load(DESIGN / 'cases' / case / ('actions.'+platform+'.json'))
        compiled = check('compile_contract ' + key, lambda: dc.compile_contract(lock, lock_sha, case, platform, bindings, actions))
        plan, enriched = compiled
        target = DESIGN / 'compiled' / case / platform
        check('published compiled plan/actions match '+key, lambda: same([plan, enriched], [dc.load(target/'plan.json'),dc.load(target/'actions.json')]))
        save('reconstructed/'+key+'/plan.json', plan)
        save('reconstructed/'+key+'/actions.json', enriched)
        cat = check('review_contract.catalog '+key, lambda: rc.catalog(plan, lock, lock_sha, policy, approval['policy_sha256'], platform))
        coverage = check('requirement_routes.audit '+key, lambda: rr.audit(lock, lock_sha, plan, routes, approval['routes_sha256']))
        bridge = DESIGN / ('Bridge.swift' if platform == 'ios' else 'ObserverBridge.kt')
        execution = check('execution_plan.compile_execution '+key, lambda: ep.compile_execution(plan, lock, lock_sha, fixtures, sha(bridge), launch_ref={'source':'reference','pointer':'/launch/'+case+'/'+platform}))
        check('execution_plan.verify_execution '+key, lambda: ep.verify_execution(execution, plan, lock, lock_sha, fixtures, sha(bridge)))
        supplied_catalog = dc.load(target/'review-catalog.json')
        assert supplied_catalog.pop('catalog_sha256') == dc.digest(cat)
        check('published execution/catalog/coverage match '+key, lambda: same([execution,cat,coverage], [dc.load(target/'execution.json'),supplied_catalog,dc.load(target/'coverage.json')]))
        assert not coverage['must_route_gaps']
        assert not coverage['unowned_assertions']
        assert len(execution['actions']) == 13 <= 40
        save('reconstructed/'+key+'/review-catalog.json', cat)
        save('reconstructed/'+key+'/coverage.json', coverage)
        save('reconstructed/'+key+'/execution.json', execution)
        states = plan['states']
        assert len(states) == 9
        assert {s['id'] for s in states if s['coverage']=='full_content'} == {'overview','permitted','requested','requested-closed','replaced'}
        event_rows = []
        ack = False; requested = False; expanded = False; index = 0
        expected_at = {}
        receipts = {}
        for ai, action in enumerate(execution['actions']):
            model = models[index]
            receipt = []
            if action['type'] == 'tap':
                name = action['target']['identifier']
                if name == 'transfer.disclosure': expanded = not expanded
                elif name == 'transfer.choice':
                    assert not requested
                    ack = not ack
                    receipt = ['transfer.ack:'+model['id']+':'+str(ack).lower()]
                elif name == 'transfer.primary':
                    assert model['sealIntact'] and model['coolantReady'] and ack and not requested
                    requested = True
                    receipt = ['transfer.release:'+model['id']]
            elif action['type'] == 'apply_next_fixture':
                index += 1; ack = requested = expanded = False
            receipts[ai] = receipt
            model = models[index]
            status = ('Seal needs attention' if not model['sealIntact'] else 'Coolant not ready' if not model['coolantReady'] else 'Release requested' if requested else 'Ready for release' if ack else 'Awaiting check')
            expected_at[ai] = {'title-label':model['title'], 'subtitle-label':model['destination']+' · '+model['temperatureRange'], 'status-label':status, 'status-text-label':status, 'disclosure-label':'Hide handling' if expanded else 'Review handling','disclosure-enabled':True, 'choice-label':'Seal check confirmed' if ack else 'Confirm seal checked', 'choice-selected':ack,'choice-enabled':not requested,'primary-label':'Requested' if requested else 'Release transfer','primary-enabled':model['sealIntact'] and model['coolantReady'] and ack and not requested}
        for state in states:
            expected = expected_at[state['after_action']]
            for row in [a for a in plan['assertions'] if a['state']==state['id']]:
                rid = row['requirement_id']
                if rid in expected: assert row['expected']==expected[rid], (key,state['id'],rid)
                if row['kind']=='event':
                    ai = state.get('stimulus_action',state['after_action'])
                    assert row['action_index']==ai
                    assert row['expected']==receipts[ai], (key,state['id'],rid)
                    assert execution['actions'][ai]['type'] in {'tap','apply_next_fixture'}
                    assert (row.get('stimulus')=='caller_update') == (execution['actions'][ai]['type']=='apply_next_fixture')
                    event_rows.append({'state':state['id'],'rule':rid,'action_index':ai,'expected':row['expected'],'stimulus':row.get('stimulus','activation')})
                if rid=='status-fill':
                    assert row['expected']==int(reference['palette'][reference['status_role_mapping'][expected['status-label']]['value']]['value'][1:],16)
                if rid=='primary-fill':
                    role = 'enabled' if expected['primary-enabled'] else 'disabled'
                    assert row['expected']==int(reference['palette'][role]['value'][1:],16)
        semantic.append({'scenario':case,'platform':platform,'state_expectations_match_independent_business_simulation':True,'event_rows':event_rows})
        summary.append({'scenario':case,'platform':platform,'states':len(states),'actions':len(execution['actions']),'full_states':[s['id'] for s in states if s['coverage']=='full_content'],'assertions':len(plan['assertions']),'cells':len(plan['matrix_contract']['cells']),'required_cells':sum(c['disposition']=='required'for c in plan['matrix_contract']['cells']),'na_cells':sum(c['disposition']=='not_applicable'for c in plan['matrix_contract']['cells']),'runtime_must_route_gaps':coverage['must_route_gaps'],'unowned_assertions':coverage['unowned_assertions'],'catalog_rows':len(cat['rows']),'plan_sha256':dc.digest(plan),'execution_sha256':execution['execution_sha256']})
        if case=='P1' and platform=='ios':
            tampered = copy.deepcopy(plan);tampered['assertions'][0]['expected']='changed'
            check('frozen verify_generated rejects changed expected', lambda: dc.verify_generated(tampered,lock,lock_sha,platform), True)
            altered = copy.deepcopy(execution);altered['actions'][10]['type']='checkpoint'
            check('frozen verify_execution rejects removed caller update', lambda: ep.verify_execution(altered,plan,lock,lock_sha,fixtures,sha(bridge)), True)

source_ids = {r['id'] for r in defs['rows']}
runtime_ids = set(lock['contract']['required_rule_ids'])
for clause in crosswalk['clauses']:
    assert set(clause['runtime_rule_ids']) <= runtime_ids
    assert set(clause['source_audit_ids']) <= source_ids
    assert clause['runtime_rule_ids'] or clause['source_audit_ids'] or clause['other_verification_routes']
    original = ROOT / clause['original_source']['path']
    assert original.name in {'BRIEF.md','API.md'} and 'design-proposals/v1/design/T1/public' in str(original)
    assert sha(original)==clause['original_source']['sha256']
    assert 1<=clause['original_source']['line']<=len(original.read_text().splitlines())

for platform in ['ios','android']:
    v = nc.callback_verdict({'callback_delta':[],'dispatch':{'attempted':False,'succeeded':False}},[],platform)
    assert v['status']=='unassessed'
    check('callback_verdict does not credit empty undelivered interval '+platform,lambda: same(v['status'],'unassessed'))

save('mechanical-checks.json', {'commands':[{'argv':['python3','-B',str(Path(__file__).resolve())],'startedAtUnix':checks[0]['startedAtUnix'],'finishedAtUnix':time.time(),'scope':'Pure Python source parsing/reconstruction. No SDK, product source, native process, capture, runtime judgment, link or launch.'}], 'checks':checks,'design_seal':seal_result,'summary':summary,'source_audit_definitions_count':len(defs['rows']),'crosswalk_clause_count':len(crosswalk['clauses']),'rejected_authoring_or_parser_attempts':[{'script':'review-checks-attempt1.py','log':'reconstruction.log','reason':'Reviewer harness initially compared the sealed clauses list to the published metadata wrapper rather than its clauses member. Corrected only the local review harness.'}], 'intentional_negative_checks':[c for c in checks if c['status']=='expected_rejection']})
save('semantic-checks.json',semantic)
print(json.dumps({'status':'passed','checks':len(checks),'summary':summary,'source_audits':len(defs['rows']),'crosswalk_clauses':len(crosswalk['clauses'])},indent=2))
