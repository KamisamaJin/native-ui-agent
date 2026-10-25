#!/usr/bin/env python3
"""Rebuild sealed design products with pinned Python tools; never execute an SDK.

--seal is a one-time preimplementation operation. Normal invocation only verifies.
Private input values are intentionally omitted from printed output.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'candidate-v10/scripts'))
import design_contract as d
import execution_plan as xp
import requirement_routes as rr
import review_contract as rc
import acceptance

def read(path):return d.load(path)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):
    with path.open('x') as stream:stream.write(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def table(root):
    return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p != root/'SEAL.json'}
def verify_scope(name):
    scope=ROOT/name;approval=read(scope/'approval.json');lock=read(scope/'design-lock.json')
    locksha=approval['design_lock_sha256'];d.validate_lock(lock,locksha)
    assert lock==d.seal(scope/'contract.json',scope),'Original source/contract differs'
    reference=read(scope/'reference.json');bindings=read(scope/'bindings.json')
    assert reference==lock['sources']['reference']['document']
    policy=read(scope/'policy.json');routes=read(scope/'routes.json')
    assert approval['policy_sha256']==d.digest(policy)
    assert approval['routes_sha256']==d.digest(routes)
    expected_production={'ios':['Sources/AlertToast/CollectionAuthorizationCard.swift'],
       'android':['app/src/main/java/com/example/reply/ui/components/CollectionAuthorizationCard.kt']}
    assert approval['production_paths']==expected_production
    assert approval['approved_before_initial_implementation'] is True
    assert approval['api_minimum']=={'ios':'14.0'}
    assert approval['runtime_evidence_claim'] is False
    audit=read(scope/'SOURCE-STYLE-AUDIT.json');index=read(scope/'audit-index.json')
    assert approval['source_audit_sha256']==d.digest(audit)
    assert audit['reference_file_sha256']==sha(scope/'reference.json')
    assert len(index['items'])==len(audit['entries'])
    for row,item in zip(audit['entries'],index['items']):
        assert row['evidence_class']=='source-only' and item['method']=='source-only'
        assert item['expected']=={'source':'reference','pointer':row['source_pointer']}
        assert row['original_datum']==d.pointer(reference,row['source_pointer'])
        assert set(item['platforms'])<= {'ios','android'} and item['platforms']
        assert item['priority'] in {'must','advisory'}
        assert item['id']==row['id'] and item['clause'].startswith('Source-only:')
    cases=sorted(p.name for p in (scope/'cases').iterdir() if p.is_dir())
    assert len(cases)==1 and set(cases)==set(lock['contract']['scenarios'])
    assert set(approval['environment_sha256'])==set(cases)
    facts=[]
    for case in cases:
        fixtures=read(scope/'cases'/case/'fixtures.json')
        scenario=lock['contract']['scenarios'][case]
        assert len(scenario['states'])==6 and len(lock['contract']['rules'])==25
        for platform in ['ios','android']:
            compiled=scope/'compiled'/case/platform
            bridge=scope/('Bridge.swift' if platform=='ios' else 'ObserverBridge.kt')
            base=[]
            for source_action in scenario['actions']:
                action=dict(source_action)
                for field in ['target','after_target']:
                    if isinstance(action.get(field),str):action[field]=bindings[action[field]]
                base.append(action)
            plan,enriched=d.compile_contract(lock,locksha,case,platform,bindings,base)
            assert plan==read(compiled/'plan.json')
            execution=xp.compile_execution(plan,lock,locksha,fixtures,sha(bridge),
              launch_ref={'source':'reference','pointer':'/launch/'+case+'/'+platform})
            assert execution==read(compiled/'execution.json')
            assert execution['actions']==read(compiled/'actions.json')
            assert execution['config']==read(compiled/'fixtures.json')
            xp.verify_execution(execution,plan,lock,locksha,fixtures,sha(bridge))
            coverage=rr.audit(lock,locksha,plan,routes,approval['routes_sha256'])
            assert coverage==read(compiled/'coverage.json')
            assert not coverage['unowned_assertions'] and not coverage['must_route_gaps']
            catalog=rc.catalog(plan,lock,locksha,policy,approval['policy_sha256'],platform)
            assert catalog==read(compiled/'review-catalog.json')
            environment=read(scope/'cases'/case/('environment.'+platform+'.json'))
            assert approval['environment_sha256'][case][platform]==d.digest(environment)
            assert acceptance.environment({},environment,platform)['status']=='U'
            # An empty packet must remain U; schema validity alone is no runtime pass.
            assert environment['width']==fixtures['width'] and environment['height']==600
            assert environment['direction']==fixtures['direction'] and environment['theme']==fixtures['theme']
            assert all(s['coverage']=='full_content' for s in plan['states'])
            assert len(plan['assertions'])+sum(c['disposition']=='not_applicable' for c in plan['matrix_contract']['cells'])==150
            facts.append({'platform':platform,'rules':25,'states':6,'assertions':len(plan['assertions']),
              'na_cells':sum(c['disposition']=='not_applicable' for c in plan['matrix_contract']['cells']),
              'obligations':len(coverage['obligations']),'qualitative_atoms':sum(a['method']=='visual' for a in policy['atoms']),
              'pixel_atoms':sum(a['method']=='native_pixels' for a in policy['atoms'])})
    assert (scope/'reference.svg').is_file() and (scope/'reference.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    return {'scope':name,'design_lock_sha256':locksha,'checks':facts,
      'limits':'SDK-free design identity and derivation only; no production implementation, source-style audit, computed-style measurement or runtime/API pass.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seal',action='store_true');args=parser.parse_args()
    # Read only method files, never production/cache source. Verify every used method against RELEASE.
    release=read(ROOT.parent/'RELEASE.json')
    for script in ['design_contract.py','execution_plan.py','requirement_routes.py','review_contract.py','native_checks.py','native_pixels.py','observation_contract.py','native_geometry.py','acceptance.py','native_environment.py']:
        rel='candidate-v10/scripts/'+script
        assert sha(ROOT.parent/rel)==release['files'][rel], 'Frozen method differs: '+rel
    summaries=[verify_scope(name) for name in ['public','private']]
    # A held-out input route shares the original API and design intentions.
    for filename in ['Bridge.swift','ObserverBridge.kt','REQUIREMENTS.md','bindings.json','audit-index.json']:
        assert (ROOT/'public'/filename).read_bytes()==(ROOT/'private'/filename).read_bytes(), 'Cross-scope API/design drift: '+filename
    assert read(ROOT/'public/reference.json')['style']==read(ROOT/'private/reference.json')['style']
    assert read(ROOT/'public/contract.json')['rules']==read(ROOT/'private/contract.json')['rules']
    summary={'version':1,'kind':'SDK-free independent design reconstruction','frozen_release_file_sha256':sha(ROOT.parent/'RELEASE.json'),
             'scope_summaries':summaries,'production_source_read':False,'sdk_executed':False}
    if args.seal:
        assert not (ROOT/'SEAL.json').exists(),'Design already sealed; never silently reapprove'
        assert not (ROOT/'author_design.py').exists(),'Remove the authoring script before exposing only the public scope'
        save(ROOT/'VERIFICATION.json',summary)
        stamp=time.time()
        for name in ['public','private']:
            scope=ROOT/name
            save(scope/'SEAL.json',{'version':1,'sealedAtUnix':stamp,'scope':'Independent preimplementation design files; no production source or runtime proof.','files':table(scope)})
        save(ROOT/'SEAL.json',{'version':1,'sealedAtUnix':stamp,'scope':'Full original public/private design file maps, nested seals and SDK-free verifier.','files':table(ROOT)})
    else:
        assert read(ROOT/'VERIFICATION.json')==summary
        for scope in [ROOT/'public',ROOT/'private',ROOT]:
            assert read(scope/'SEAL.json')['files']==table(scope),'Sealed file identity differs: '+str(scope)
    print(json.dumps({'status':'verified','sdk_executed':False,'production_source_read':False,
                      'scopes':2,'rules_per_scope':25,'states_per_scope':6,
                      'assertions_per_platform':summaries[0]['checks'][0]['assertions'],
                      'all_assertions_owned':True,'design_seal_file_sha256':sha(ROOT/'SEAL.json')}))

if __name__=='__main__':main()
