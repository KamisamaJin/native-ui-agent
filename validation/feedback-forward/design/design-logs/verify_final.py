#!/usr/bin/env python3
"""SDK-free revision verifier under the explicitly approved state amendment.

This does not replace root's shared verifier or source-audit sidecar, and does not
modify or bypass any frozen runtime evaluator.
"""
from pathlib import Path, PurePosixPath
import sys,json,hashlib,datetime,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT.parent/'design-proposals'/'v1'/'design'
REVIEWS=ORIGINAL.parent/'review'
PRIOR=ROOT.parent/'design-proposals'/'v2'/'design'
LATEST_REVIEWS=PRIOR.parent/'review'
sys.path.insert(0,str(ROOT.parent/'candidate-v9'/'scripts'))
import design_contract as dc
import requirement_routes as rr
import execution_plan as ep
import review_contract as rc
import acceptance
from PIL import Image,ImageFont
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def put(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def check_seal(root,name='SEAL.json'):
    seal=load(root/name)
    for rel,wanted in seal['files'].items():assert sha(root/rel)==wanted,(root/rel,'changed sealed file')
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p!=root/name}
    assert actual==set(seal['files']),(root,'missing/unsealed file')
    return len(actual)

results=[];audit_results=[]
try:
    original_verified=check_seal(ORIGINAL,'DESIGN-SEAL.json')
    prior_verified=check_seal(PRIOR,'DESIGN-SEAL.json')
    for task in ['T1','T2']:
        check_seal(REVIEWS/task)
        check_seal(LATEST_REVIEWS/task)
        for scope in ['public','private']:
            base=ROOT/task/scope;prior=ORIGINAL/task/scope;approval=load(base/'approval.json')
            sealed_count=check_seal(base)
            lock=load(base/'design-lock.json');reference=lock['sources']['reference']['document'];locksha=dc.digest(lock)
            dc.validate_lock(lock,locksha)
            assert approval['design_lock_sha256']==locksha
            assert approval['official_review_sha256']==sha(REVIEWS/task/'review.json')
            assert approval['prior_proposal_seal_sha256']==sha(ORIGINAL/'DESIGN-SEAL.json')
            assert approval['prior_revision_2_seal_sha256']==sha(PRIOR/'DESIGN-SEAL.json')
            assert approval['official_review_2_sha256']==sha(LATEST_REVIEWS/task/'review.json')
            assert approval['compatibility_sha256']==dc.digest(reference['compatibility'])
            assert reference['compatibility']==load(base/'compatibility.json')
            assert reference['compatibility']['source_api_audit_id']=='ios-api14-availability'
            assert reference['compatibility']['future_source_api_check']['target']=='arm64-apple-ios14.0-simulator'
            assert 'future_build' not in reference['compatibility']
            checker=reference['compatibility']['shared_checker']
            assert checker['path']=='validation/feedback-forward/check_minimum_api.py'
            assert checker['sha256']==sha(ROOT.parent/'check_minimum_api.py')==approval['minimum_source_api_checker_sha256']
            assert checker['required_compiler_exit_codes']==[0,0] and checker['accepted_status']=='source_api_typechecked'
            assert '--deployment-target' in checker['argv'] and checker['argv'][-1]=='14.0'
            policy=load(base/'policy.json');routes=load(base/'routes.json');audits=load(base/'implementation-audit.json')
            assert approval['policy_sha256']==dc.digest(policy)
            assert approval['routes_sha256']==dc.digest(routes)
            assert approval['implementation_audit_sha256']==dc.digest(audits)
            assert audits=={'version':1,'index':{'source':'reference','pointer':'/implementation_audits'}}
            source_audits=dc.pointer(reference,'/implementation_audits')
            assert len(source_audits)==len({a['id'] for a in source_audits})
            for a in source_audits:
                assert set(a)=={'id','clause','priority','files','proposition','expected'}
                assert a['priority']=='must' and len(a['files'])==1
                assert a['clause'].strip()
                proposition,_=dc.expression(a['proposition'],lock['sources'])
                expected,_=dc.expression(a['expected'],lock['sources'])
                assert proposition=={'value':a['clause'],'unit':'string'}
                assert expected=={'value':True,'unit':'bool'}
                platform=a['id'].split('-')[0];assert platform in ['ios','android']
                file=a['files'][0]
                if file.startswith('@design/'):
                    assert file==('@design/Bridge.swift' if platform=='ios' else '@design/ObserverBridge.kt')
                    bridge=base/file[len('@design/'):]
                    assert sha(bridge)==sha(prior/bridge.name)
                    for launch in reference['launch'].values():assert launch[platform]['bridge_sha256']==sha(bridge)
                else:
                    assert file in approval['production_paths'][platform]
                    assert '..' not in PurePosixPath(file).parts and not PurePosixPath(file).is_absolute()
            definitions=load(base/'compiled'/'source-audit-definitions.json')
            assert definitions['mode']=='definition_only' and len(definitions['rows'])==len(source_audits)
            assert definitions['design_lock_sha256']==locksha and definitions['policy_sha256']==dc.digest(audits)
            assert {a['id'] for a in definitions['rows']}=={a['id'] for a in source_audits}
            assert all(meta['sha256'] is None for name,meta in definitions['files'].items() if not name.startswith('@design/'))
            for node in ['canvas','surface','ink']:
                assert all(p+'-'+node+'-noninteractive' in {a['id'] for a in source_audits} for p in ['ios','android'])
            assert all(p+'-uncapped-text-lines' in {a['id'] for a in source_audits} for p in ['ios','android'])
            runtime_ids=set(lock['contract']['required_rule_ids']);audit_ids={a['id'] for a in source_audits}
            for row in reference['requirement_crosswalk']:
                assert set(row['runtime_rule_ids'])<=runtime_ids and set(row['source_audit_ids'])<=audit_ids
            assert load(base/'requirement-crosswalk.json')['clauses']==reference['requirement_crosswalk']
            assert load(base/'design-corrections.json')['corrections']==reference['design_corrections']
            for correction in reference['design_corrections']:
                assert task=='T2' and correction['before']['value']=='#FFFFE5B3' and correction['after']['value']=='#FFE9EFF8'
            if task=='T1':assert 'Wi-Fi' not in reference['sampling_limits']['runtime'] and 'capacity' not in reference['sampling_limits']['runtime']
            audit_results.append({'task':task,'scope':scope,'source_only_audits':len(source_audits),
                'expected_provenance_valid':True,'source_actuals':'unassessed_no_product_source_exists'})
            for name in ['Bridge.swift','ObserverBridge.kt']:assert sha(base/name)==sha(prior/name)
            for case,scenario in lock['contract']['scenarios'].items():
                f=load(base/'cases'/case/'fixtures.json');old=load(prior/'cases'/case/'fixtures.json')
                assert f['initial']==old['initial'] and f['updates'][0]==old['updates'][0]
                previous=load(PRIOR/task/scope/'cases'/case/'fixtures.json')
                assert f['initial']==previous['initial'] and f['updates']==previous['updates']
                for model in [f['initial'],*f['updates']]:
                    assert isinstance(model['id'],str)
                    rows=model['notes' if task=='T1' else 'chapters']
                    assert all(isinstance(row['id'],str) for row in rows)
                    assert len(rows)==len({row['id'] for row in rows})
                assert dc.digest(old['initial'])==reference['cases'][case]['original_initial_sha256']
                assert dc.digest(old['updates'][0])==reference['cases'][case]['original_update_sha256']
                assert len(f['updates'])==(1 if task=='T1' else 2)
                states=scenario['states'];by_state={s['id']:s for s in states}
                assert len(states)==(9 if task=='T1' else 10)
                assert [s['id'] for s in states if s['coverage']=='full_content']==['overview','permitted','requested','requested-closed','replaced']
                assert all(s['after_action']>=0 for s in states)
                assert len(scenario['actions'])==(13 if task=='T1' else 14)
                expected=reference['cases'][case]['states']
                # Distinguishing business facts are checked against independent expected anchors.
                assert expected['cleared']['selected']['value']==(False if task=='T1' else True)
                assert expected['restored']['selected']['value']==(True if task=='T1' else False)
                assert expected['cleared']['enabled']['value'] is False
                assert expected['restored']['enabled']['value'] is True
                assert expected['requested']['choiceEnabled']['value'] is False
                assert expected['requested-closed']['disclosureEnabled']['value'] is True
                assert expected['requested-closed']['open']['value'] is False
                assert expected['requested-closed']['requested']['value'] is True
                if task=='T1':
                    assert expected['held-choice']['selected']['value'] is True
                    assert expected['held-choice']['enabled']['value'] is False
                    assert expected['held-choice']['status']==expected['replaced']['status']
                else:
                    m=f['updates'][1]
                    assert m['availableMB']<m['downloadSizeMB'] and m['meteredConnection'] is True
                    assert expected['competing-gates']['selected']['value'] is True
                    assert expected['competing-gates']['status']['value']=='Storage needed'
                    assert expected['competing-gates']['enabled']['value'] is False
                for p in ['ios','android']:
                    out=base/'compiled'/case/p;plan=load(out/'plan.json')
                    assert dc.verify_generated(plan,lock,locksha,p)==load(out/'actions.json')
                    coverage=rr.audit(lock,locksha,plan,routes,dc.digest(routes))
                    assert coverage==load(out/'coverage.json')
                    assert not coverage['must_route_gaps'] and not coverage['unowned_assertions']
                    bridge=base/('Bridge.swift' if p=='ios' else 'ObserverBridge.kt')
                    execution=load(out/'execution.json');ep.verify_execution(execution,plan,lock,locksha,f,sha(bridge))
                    assert execution['scope']=='full' and execution['launch_ref']=={'source':'reference','pointer':f'/launch/{case}/{p}'}
                    assert execution['actions']==load(out/'execution-inputs'/'actions.json')
                    assert execution['config']==load(out/'execution-inputs'/'fixtures.json')
                    cat=rc.catalog(plan,lock,locksha,policy,dc.digest(policy),p)
                    assert load(out/'review-catalog.json')==dict(cat,catalog_sha256=dc.digest(cat))
                    env=load(base/'cases'/case/f'environment.{p}.json')
                    assert env==load(prior/'cases'/case/f'environment.{p}.json')
                    assert approval['environment_sha256'][case][p]==dc.digest(env)
                    assert acceptance.environment({'snapshots':[]},env,p)['status']=='U'
                    events=[]
                    for a in plan['assertions']:
                        if a['kind']=='event':
                            s=by_state[a['state']];assert a['action_index']==s['stimulus_action']
                            action=execution['actions'][a['action_index']]
                            assert action['type']==('apply_next_fixture' if a.get('stimulus')=='caller_update' else 'tap')
                            assert not action.get('allow_disabled',False)
                            events.append({'assertion':a['id'],'action_index':a['action_index'],'stimulus':a.get('stimulus','activation')})
                    insets=[a for a in plan['assertions'] if a['requirement_id']=='status-leading-inset']
                    assert len(insets)==len(states)
                    assert all(a['expected']==16 and a['op']=='gte' and a['property']==('inset_left' if scope=='public' else 'inset_right')
                        and a['measurement']=='accessibility_box' and a['basis']=='semantic' for a in insets)
                    strip=next(a for a in policy['atoms'] if a['rule_id']=='status-leading-clear')['sampling']
                    assert strip['minimum_support']==1 and strip['region']==([0,0,.04,1] if scope=='public' else [.96,0,1,1])
                    palette=reference['palette']
                    status_colors={a['expected'] for a in plan['assertions'] if a['requirement_id']=='status-fill'}
                    assert status_colors=={int(palette[role]['value'][1:],16) for role in ['waiting','ready','requested','blocked']}
                    assert len([a for a in plan['assertions'] if a['requirement_id']=='status-fill'])==len(states)
                    for shape in ['status-rectangle','status-no-border','primary-rectangle','primary-no-border','primary-painted-allocation','ink-rectangle']:
                        assert any(a['requirement_id']==shape and a['kind']=='manual' and a['allowed_methods']==['visual'] for a in plan['assertions'])
                    results.append({'task':task,'scope':scope,'case':case,'platform':p,'states':len(states),'actions':len(execution['actions']),
                      'assertions':len(plan['assertions']),'runtime_must_route_gaps':0,'sealed_bundle_files':sealed_count,
                      'callback_bindings':events,'native_execution':False})
        hidden=load(ROOT/task/'private'/'reference.json')['cases']['H1']
        private_values=[]
        for m in [hidden['caller']['initial'],*hidden['caller']['updates']]:
            for k in ['id','title','destination','language']:
                if k in m:private_values.append(m[k])
        private_values.extend(r['body'] for r in hidden['rows'])
        for p in (ROOT/task/'public').rglob('*'):
            if p.is_file() and p.suffix in ['.json','.md','.swift','.kt','.svg']:
                assert not any(v in p.read_text() for v in private_values),(p,'private value leaked')
    # Inspect actual new static references; this is never a native result.
    inspections=[]
    for r in load(ROOT/'design-logs'/'static-reference-records.json'):
        path=ROOT/r['task']/r['scope']/'references'/r['case']/(r['state']+'.png')
        x,y,w,h=r['status_band'];outside=0
        with Image.open(path) as image:
            assert list(image.size)==r['png_size']
            pixels=image.convert('RGB')
            for yy in range(int(y),min(image.height,int(y+h))):
                for xx in list(range(0,int(x)))+list(range(int(x+w),image.width)):
                    outside+=pixels.getpixel((xx,yy))==(23,43,77)
        assert outside==0,(path,'reference status ink overflows')
        inspections.append({'task':r['task'],'scope':r['scope'],'case':r['case'],'state':r['state'],
            'status_ink_pixels_outside_band':outside,'reference_only':True})
    put(ROOT/'design-logs'/'static-verification.json',{'status':'static_reconstruction_passed_pending_root_verifier_and_independent_review',
        'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_archived_files_unchanged':original_verified,'revision_2_archived_files_unchanged':prior_verified,
        'compiled_pairs':results,'implementation_audit_indexes':audit_results,'static_reference_inspections':inspections,
        'privacy':'No unique H1 caller values or paragraphs occur in public files.',
        'limits':['No SDK, production source, implementation or native observation accessed.',
                  'Source audit expected anchors are validated; actual source audits remain unassessed.',
                  'Minimum14 source/API check is defined only; no SDK/module/typecheck/link/legacy-package/runtime result is claimed.',
                  'Empty native observations remain U; no actual environment P is asserted.',
                  'This amended author verifier does not replace root shared verification or unchanged runtime acceptance.']})
    manifest=load(ROOT/'DESIGN-SEAL.json');manifest['timestamp']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest['files']={str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p!=ROOT/'DESIGN-SEAL.json'}
    put(ROOT/'DESIGN-SEAL.json',manifest)
    check_seal(ROOT,'DESIGN-SEAL.json')
    print(json.dumps({'status':'static_reconstruction_passed','pairs':len(results),'reference_images':len(inspections),
         'top_seal_sha256':sha(ROOT/'DESIGN-SEAL.json'),'files':len(manifest['files'])}))
except Exception:
    out=ROOT/'design-logs'/('verification-unsuccessful-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'.txt')
    out.write_text(traceback.format_exc());raise
