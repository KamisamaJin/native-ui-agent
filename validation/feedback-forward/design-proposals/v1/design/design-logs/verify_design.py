#!/usr/bin/env python3
"""Static reconstruction using frozen Skill scripts; never invokes an SDK."""
from pathlib import Path
import sys, json, hashlib, datetime
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'candidate-v9'/'scripts'))
import design_contract as dc
import execution_plan as ep
import requirement_routes as rr
import review_contract as rc
import acceptance
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
results=[]
for task in ['T1','T2']:
    public=ROOT/task/'public';private=ROOT/task/'private'
    hidden=load(private/'reference.json')['cases']['H1']
    unique=[]
    for m in [hidden['caller']['initial'],*hidden['caller']['updates']]:
        for key in ['id','title','destination','language']:
            if key in m:unique.append(m[key])
    unique += [r['body'] for r in hidden['rows']]
    for p in public.rglob('*'):
        if p.is_file() and p.suffix in ['.json','.md','.swift','.kt','.svg']:
            text=p.read_text()
            assert not any(v in text for v in unique),(p,'Private caller value leaked')
    assert sha(public/'Bridge.swift')==sha(private/'Bridge.swift')
    assert sha(public/'ObserverBridge.kt')==sha(private/'ObserverBridge.kt')
    for scope in ['public','private']:
        base=ROOT/task/scope;approval=load(base/'approval.json');lock=load(base/'design-lock.json')
        locksha=dc.digest(lock);policy=load(base/'policy.json');routes=load(base/'routes.json')
        assert approval['design_lock_sha256']==locksha
        assert approval['policy_sha256']==dc.digest(policy)
        assert approval['routes_sha256']==dc.digest(routes)
        dc.validate_lock(lock,locksha)
        actual={str(p.relative_to(base)):sha(p) for p in base.rglob('*') if p.is_file() and p.name!='SEAL.json'}
        assert actual==load(base/'SEAL.json')['files'],(base,'Seal mismatch')
        for case,scenario in lock['contract']['scenarios'].items():
            assert [s['id'] for s in scenario['states']]==['overview','permitted','requested','replaced']
            assert all(s['after_action']>=0 and s['coverage']=='full_content' for s in scenario['states'])
            assert scenario['states'][-1]['stimulus_action']==6
            assert scenario['states'][-1]['after_action']==7
            f=load(base/'cases'/case/'fixtures.json')
            for platform in ['ios','android']:
                out=base/'compiled'/case/platform
                plan=load(out/'plan.json');actions=dc.verify_generated(plan,lock,locksha,platform)
                assert actions==load(out/'actions.json')
                routeaudit=rr.audit(lock,locksha,plan,routes,dc.digest(routes))
                assert routeaudit==load(out/'coverage.json')
                assert not routeaudit['must_route_gaps'] and not routeaudit['unowned_assertions']
                bridge=base/('Bridge.swift' if platform=='ios' else 'ObserverBridge.kt')
                execution=load(out/'execution.json')
                ep.verify_execution(execution,plan,lock,locksha,f,sha(bridge))
                assert execution['scope']=='full'
                assert execution['launch_ref']=={'source':'reference','pointer':f'/launch/{case}/{platform}'}
                assert execution['actions']==load(out/'execution-inputs'/'actions.json')
                assert execution['config']==load(out/'execution-inputs'/'fixtures.json')
                catalog=rc.catalog(plan,lock,locksha,policy,dc.digest(policy),platform)
                assert load(out/'review-catalog.json')==dict(catalog,catalog_sha256=dc.digest(catalog))
                environment=load(base/'cases'/case/f'environment.{platform}.json')
                assert approval['environment_sha256'][case][platform]==dc.digest(environment)
                assert acceptance.environment({'snapshots':[]},environment,platform)['status']=='U'
                assert environment['width']==f['width'] and environment['height']==600
                assert environment['direction']==f['direction'] and environment['theme']==f['theme']
                if platform=='ios':assert environment['dynamic_type']==f['dynamic_type']
                else:
                    assert environment['font_scale']==f['fontScale']
                    assert environment['dimension_encoding']=='paparazzi-float32-screen-config-v1'
                assert all(a['kind']!='geometry' or a['measurement']=='accessibility_box' for a in plan['assertions'])
                assert all(a['kind']!='event' or execution['actions'][a['action_index']]['type'] in ['tap','apply_next_fixture'] for a in plan['assertions'])
                assert all(a['kind']!='event' or a.get('stimulus')!='caller_update' or a['action_index']==6 for a in plan['assertions'])
                results.append({'task':task,'scope':scope,'case':case,'platform':platform,
                    'assertions':len(plan['assertions']),'matrix_cells':len(plan['matrix_contract']['cells']),
                    'must_obligations':sum(x['priority']=='must' for x in routeaudit['obligations']),
                    'not_applicable_cells':sum(x['disposition']=='not_applicable' for x in plan['matrix_contract']['cells']),
                    'must_route_gaps':0,'reconstructed':True,'native_execution':False})
put(ROOT/'design-logs'/'static-verification.json',{'status':'static_reconstruction_passed',
    'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'case_platform_pairs':results,
    'privacy_scan':'No unique H1 caller values or H1 paragraphs occur in public files; public/private bridge bytes match.',
    'scope_limit':'Static completeness and schema identity only. No SDK, product source, product implementation or runtime observation was accessed. Native environment evidence remains U until a real run.'})
seal=load(ROOT/'DESIGN-SEAL.json');seal['timestamp']=datetime.datetime.now(datetime.timezone.utc).isoformat()
seal['files']={str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='DESIGN-SEAL.json'}
put(ROOT/'DESIGN-SEAL.json',seal)
assert all(sha(ROOT/name)==digest for name,digest in seal['files'].items())
print(json.dumps({'status':'static_reconstruction_passed','pairs':len(results),'sealed_files':len(seal['files'])}))
