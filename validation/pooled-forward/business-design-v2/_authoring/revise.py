#!/usr/bin/env python3
"""Pure preimplementation representation revision. Original design remains immutable."""
from pathlib import Path
import copy,hashlib,json,os,shutil,subprocess,sys
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[2]
OLD=ROOT.with_name('business-design')
TOOLS=REPO/'validation/pooled-forward/candidate-v13.9/scripts'
ORIGINAL_SEAL='6e82784fde88cb617d1e68ee5cac6dab8514eeddd526eb77a95c34f3040dbd60'
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def digest(x):return sha(canonical(x))
def load(p):return json.loads(p.read_text())
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(x if isinstance(x,str) else json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def rename_strings(x):
    if isinstance(x,str):return 'start' if x=='initial' else x.replace('/states/initial/','/states/start/')
    if isinstance(x,list):return [rename_strings(v) for v in x]
    if isinstance(x,dict):return {k:rename_strings(v) for k,v in x.items()}
    return x
def statekeys(d):return {('start' if k=='initial' else k):v for k,v in d.items()}
def assert_original():
    assert sha((OLD/'SEAL.sha256').read_bytes())==ORIGINAL_SEAL
    lines=(OLD/'SEAL.sha256').read_text().splitlines();assert len(lines)==270
    for line in lines:
        expected,p=line.split('  ',1);assert sha((OLD/p).read_bytes())==expected,p

GUARD='''#!/usr/bin/env python3
"""External profile-admission check. It does not modify or extend frozen native tools."""
import argparse,hashlib,json
from pathlib import Path
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def digest(x):return hashlib.sha256(canonical(x)).hexdigest()
def verify(root,approval,approval_sha,platform,config):
    if digest(approval)!=approval_sha:raise ValueError('Approval manifest differs from externally pinned canonical digest')
    if platform not in approval['profiles']:raise ValueError('Unapproved platform')
    p=approval['profiles'][platform]
    for field in ('design_sha256','policy_sha256','routes_sha256','environment_sha256'):
        if config.get(field)!=p[field]:raise ValueError('Wrong approved '+field)
    for field in ('design_lock','plan','policy','routes','environment','fixtures','bridge'):
        actual=Path(config[field]).resolve();expected=(root/p['paths'][field]).resolve()
        if actual!=expected:raise ValueError('Wrong approved '+field+' path')
        data=actual.read_bytes();observed=hashlib.sha256(data).hexdigest() if field=='bridge' else digest(json.loads(data))
        if observed!=p['hashes'][field]:raise ValueError('Changed approved '+field+' bytes/content')
    plan=json.loads(Path(config['plan']).read_text())
    if plan['design_contract']['platform']!=platform or plan['design_contract']['lock_sha256']!=p['design_sha256']:raise ValueError('Plan/profile platform or lock mismatch')
    if config.get('launch_ref')!=p['launch_ref']:raise ValueError('Wrong sealed launch reference')
    return {'status':'admitted_profile','platform':platform,'design_sha256':p['design_sha256'],'plan_sha256':p['hashes']['plan'],'scope':'Only this intended-platform projection is approved. Opposite expression slots are schema-only, never runtime claims.'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--approval',type=Path,required=True);p.add_argument('--approval-sha256',required=True);p.add_argument('--platform',choices=['ios','android'],required=True);p.add_argument('--config',type=Path,required=True);a=p.parse_args()
    print(json.dumps(verify(a.root.resolve(),json.loads(a.approval.read_text()),a.approval_sha256,a.platform,json.loads(a.config.read_text()))))
if __name__=='__main__':main()
'''

steps=[]
def run(label,args):
    assert '--run' not in args and not any(v in args for v in ('ios_observe.py','android_observe.py'))
    argv=[sys.executable,'-B',*map(str,args)]
    completed=subprocess.run(argv,cwd=REPO,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
    rec=dict(label=label,argv=argv,exit_code=completed.returncode,stdout=completed.stdout,stderr=completed.stderr,native_run=False)
    path=ROOT/'_pure-checks'/f'{len(steps):03d}.json';write(path,rec);steps.append(rec)
    if completed.returncode:raise RuntimeError(label+': '+completed.stderr)
    return completed.stdout

def aspect(rule):
    rid=rule['id']
    if rule.get('allowed_methods')==['native_pixels']:return 'rendered_fill'
    if rid.endswith('-mark'):return 'content_presence'
    if rid.endswith('-wrap') or rid=='content-wrap':return 'wrapping'
    if rid=='content-overlap':return 'overlap'
    if rid in ('horizontal-fit','panel-corners','row-corners'):return 'clipping'
    return 'hierarchy'

def prepare_master(task,family):
    old=OLD/task/family;root=ROOT/task/family;root.mkdir(parents=True,exist_ok=True)
    for name in ('API.md','PIXEL-SCOPE.md','fixture.schema.json','ObserverBridge.swift','ObserverBridge.kt','fixtures.ios.json','fixtures.android.json','bindings.ios.json','bindings.android.json','environment.ios.json','environment.android.json','reference-initial.svg','reference-ready.svg'):
        shutil.copyfile(old/name,root/name)
    ref=rename_strings(load(old/'reference.json'));ref['states']=statekeys(ref['states'])
    changes=[]
    for platform,key in (('ios','titleWeight'),('android','titleWeight'),('android','bodyWeight')):
        item=ref['tokens'][platform][key];assert item['unit']=='number';changes.append(dict(pointer='/tokens/'+platform+'/'+key,old_unit='number',new_unit='scalar',unchanged_value=item['value']));item['unit']='scalar'
    write(root/'reference.json',ref)
    contract=rename_strings(load(old/'contract.json'))
    for scenario in contract['scenarios'].values():
        scenario['values']={rid:statekeys(states) for rid,states in scenario['values'].items()}
    write(root/'master-contract.json',contract)
    denom=rename_strings(load(old/'denominator.json'))
    for cell in denom['cells']:
        if cell['requirement']=='heading-native-weight':
            value=cell['platforms']['android'];assert value['unit']=='number';value['unit']='scalar'
    write(root/'denominator.json',denom)
    for name in ('outcomes.json','target-observations.json','routes.json','actions.ios.json','actions.android.json','launch.json'):
        write(root/name,rename_strings(load(old/name)))
    write(root/'master-policy.original.json',load(old/'policy.json'))
    brief=(old/'BRIEF.md').read_text()
    brief+='''

## V2 frozen-tool representation and admission

Business values, fixture/bridge bytes, exact propositions, action stimuli, guards and coverage are unchanged. The reserved explicit state ID initial is renamed start everywhere; this is identity syntax only. Numeric font-weight unit spelling is scalar rather than number, with the same600/400 values. The full shared denominator and explicit platform/state N/A cells remain in denominator.json.

Frozen design_contract has no per-platform N/A syntax. Use ios/contract.json and android/contract.json with their matching lock, plan, policy, routes and environment. Each namespace contains only rules actually applicable to its intended platform. The other platform's expression slot is required only by the frozen parser; it is expressly unapproved for runtime use and proves no measurement on that platform. There is no new iOS computed-font capability or new mandatory iOS unknown. Cross-platform use of a projected lock is forbidden by PROFILE-APPROVAL.json and admit_profile.py. The integration coordinator must run that admission check against actual config paths/hashes before any native acquisition.

The family root reference/denominator/outcomes/API/fixtures/bridges are the canonical shared design; master-contract.json records the complete original rule universe, not a frozen-parser input. Use the two platform namespaces for frozen tools. Their projection-map.json records every original denominator cell, including explicit N/A cells outside the parser's intended rule universe. No cell is silently deleted.

Frozen visual categories are coarse: hierarchy groups visual organization (size, weight, ink/contrast, spacing/inset) while clipping includes visible rounded corner boundaries. Every original primitive rule property, exact question and expected Boolean remains separate and unchanged. This is taxonomy compatibility, not new evidence capability. Native control facts, callbacks, opaque pixel fills and qualitative judgments remain separate.
'''
    write(root/'BRIEF.md',brief)
    write(root/'admit_profile.py',GUARD)
    write(root/'REPRESENTATION.json',dict(version=2,original_family=str(old.relative_to(REPO)),original_global_seal_sha256=ORIGINAL_SEAL,state_id_mapping={'initial':'start'},unit_representation_changes=changes,complete_denominator_cells=denom['total_cells'],business_values_changed=False,fixture_bytes_changed=False,bridge_bytes_changed=False,questions_changed=False,coverage_changed=False,tool_expressivity_gap='Frozen validator requires both platform expressions and supports only whole-cell N/A, with no rule-platform applicability. Intended-platform projected namespaces and external approval/admission enforce the real applicability. No qualified tool source changes.'))
    return root,ref,contract,denom

def project(root,ref,master,denom,platform):
    out=root/platform;out.mkdir(parents=True,exist_ok=True);scenario_name=next(iter(master['scenarios']));sc=master['scenarios'][scenario_name]
    rules=[];values={};excluded=[];projection=[]
    for rule in master['rules']:
        rid=rule['id'];applicable=[]
        for sid,cell in sc['values'][rid].items():
            datum=cell.get(platform,cell)
            applicable.append('not_applicable' not in datum)
        if not any(applicable):excluded.append(rid);continue
        rules.append(copy.deepcopy(rule));values[rid]={}
        for sid,cell in sc['values'][rid].items():
            datum=cell.get(platform,cell)
            if 'not_applicable' in datum:values[rid][sid]={'not_applicable':datum['not_applicable']}
            else:
                other='android' if platform=='ios' else 'ios'
                otherdatum=cell.get(other,{})
                otherexpr=otherdatum if set(otherdatum)=={'source','pointer'} else datum
                values[rid][sid]={platform:copy.deepcopy(datum),other:copy.deepcopy(otherexpr)}
    keep={r['id'] for r in rules};rref=copy.deepcopy(ref)
    for responsibility in rref['responsibilities']:responsibility['rule_ids']=[rid for rid in responsibility['rule_ids'] if rid in keep]
    write(out/'reference.json',rref)
    launch={platform:load(root/'launch.json')[platform]};write(out/'launch.json',launch)
    sources=[]
    for id,name in (('reference','reference.json'),('launch','launch.json')):sources.append(dict(id=id,path=name,sha256=sha((out/name).read_bytes())))
    contract=dict(version=1,design_owner=master['design_owner'],approval_reference='PROFILE-APPROVAL.json + root REVISION-LEDGER.json; only '+platform+' projection approved, opposite expression slots schema-only',sources=sources,required_rule_ids=[r['id'] for r in rules],rules=rules,scenarios={scenario_name:dict(states=copy.deepcopy(sc['states']),actions=copy.deepcopy(sc['actions']),values=values)})
    write(out/'contract.json',contract)
    bindings=load(root/('bindings.'+platform+'.json'))
    logical={r['target'] for r in rules if 'target' in r}|{r['reference_target'] for r in rules if 'reference_target' in r}
    logical|={a[k] for a in sc['actions'] for k in ('target','after_target') if isinstance(a.get(k),str)}
    logical|={c['target'] for a in sc['actions'] for c in a.get('preconditions',[]) if isinstance(c.get('target'),str)}
    write(out/'bindings.json',{k:v for k,v in bindings.items() if k in logical})
    for name,new in ((f'actions.{platform}.json','actions.json'),(f'fixtures.{platform}.json','fixtures.json'),(f'environment.{platform}.json','environment.json'),('ObserverBridge.swift' if platform=='ios' else 'ObserverBridge.kt','ObserverBridge.swift' if platform=='ios' else 'ObserverBridge.kt')):shutil.copyfile(root/name,out/new)
    routes=load(root/'routes.json')
    for route in routes['routes'].values():route['rule_ids']=[r for r in route['rule_ids'] if r in keep]
    write(out/'routes.json',routes)
    # Execute the real frozen pure CLI; output lock is never manufactured by this author.
    run(str(out.relative_to(ROOT))+' seal',[TOOLS/'design_contract.py','seal','--contract',out/'contract.json','--root',out,'--output',out/'lock.json'])
    lock=load(out/'lock.json');locksha=digest(lock)
    policy=load(root/'master-policy.original.json');policy['design_lock_sha256']=locksha
    policy['approval_reference']='Intended '+platform+' projection only; original primitive questions unchanged; coarse frozen taxonomy recorded in projection-map.json'
    rulemap={r['id']:r for r in rules};policy['atoms']=[a for a in policy['atoms'] if a['rule_id'] in keep]
    for atom in policy['atoms']:atom['aspect']=aspect(rulemap[atom['rule_id']])
    targets={rulemap[a['rule_id']]['target'] for a in policy['atoms']};policy['ownership']={k:v for k,v in policy['ownership'].items() if k in targets}
    write(out/'policy.json',policy)
    run(str(out.relative_to(ROOT))+' compile',[TOOLS/'design_contract.py','compile','--lock',out/'lock.json','--lock-sha256',locksha,'--scenario',scenario_name,'--platform',platform,'--bindings',out/'bindings.json','--actions',out/'actions.json','--output',out/'generated'])
    planpath=out/'generated/plan.json';plan=load(planpath)
    run(str(out.relative_to(ROOT))+' review catalog',[TOOLS/'review_contract.py','catalog','--plan',planpath,'--design-lock',out/'lock.json','--design-sha256',locksha,'--policy',out/'policy.json','--policy-sha256',digest(policy),'--platform',platform,'--output',out/'catalog.json'])
    run(str(out.relative_to(ROOT))+' route audit',[TOOLS/'requirement_routes.py','audit','--plan',planpath,'--design-lock',out/'lock.json','--design-sha256',locksha,'--routes',out/'routes.json','--routes-sha256',digest(routes),'--output',out/'route-audit.json'])
    routeaudit=load(out/'route-audit.json');assert not routeaudit['must_route_gaps'] and not routeaudit['unowned_assertions'],routeaudit
    bridge=out/('ObserverBridge.swift' if platform=='ios' else 'ObserverBridge.kt')
    run(str(out.relative_to(ROOT))+' execution/guards',[TOOLS/'execution_plan.py','--plan',planpath,'--design-lock',out/'lock.json','--design-sha256',locksha,'--fixtures',out/'fixtures.json','--bridge',bridge,'--launch-source','launch','--launch-pointer','/'+platform,'--output',out/'execution'])
    by={(r['state'],r['requirement_id']):r for r in plan['assertions']}
    for cell in denom['cells']:
        original=cell['platforms'][platform];key=(cell['state'],cell['requirement']);compiled=by.get(key)
        row=dict(state=cell['state'],requirement=cell['requirement'],platform=platform,original_disposition=original['disposition'])
        if original['disposition']=='assess':
            assert compiled is not None,key
            value=original['expected'];value=int(value[1:],16) if original['unit']=='argb' else value
            assert compiled['expected']==value and compiled['unit']==original['unit'],key
            assert compiled.get('op','eq')==original['operator'],key
            row.update(compiled_assertion_id=compiled['id'],source_pointer=original['pointer'],unit=original['unit'],expected_unchanged=True)
        else:
            assert compiled is None,key;row.update(reason=original['reason'],representation='Whole-cell N/A within intended-platform contract' if key[1] in keep else 'Explicit N/A retained in complete shared denominator; rule absent only from the platform-inapplicable projection')
        projection.append(row)
    assert len(by)==sum(c['platforms'][platform]['disposition']=='assess' for c in denom['cells'])
    execution=load(out/'execution/execution.json')
    changes=[dict(state=v['state_id'],original_coverage=next(s['coverage'] for s in plan['states'] if s['id']==v['state_id']),execution_coverage=v['coverage'],reason='Frozen execution planner requires a full sweep for an already approved native absence assertion; no new design expectation') for v in execution['required_coverage'] if v['coverage']!=next(s['coverage'] for s in plan['states'] if s['id']==v['state_id'])]
    write(out/'projection-map.json',dict(version=2,intended_platform=platform,forbidden_platform='android' if platform=='ios' else 'ios',schema_only_opposite_slot=True,excluded_platform_inapplicable_rule_ids=excluded,taxonomy_mapping={r['id']:dict(original_primitive_property=r.get('property'),frozen_aspect=aspect(r)) for r in rules if r['kind']=='manual'},execution_coverage_required_by_existing_absence=changes,complete_original_platform_cell_count=len(projection),cells=projection))
    paths=dict(design_lock=platform+'/lock.json',plan=platform+'/generated/plan.json',policy=platform+'/policy.json',routes=platform+'/routes.json',environment=platform+'/environment.json',fixtures=platform+'/fixtures.json',bridge=platform+'/'+bridge.name)
    hashes={k:sha((root/v).read_bytes()) if k=='bridge' else digest(load(root/v)) for k,v in paths.items()}
    entry=dict(platform=platform,design_sha256=locksha,policy_sha256=digest(policy),routes_sha256=digest(routes),environment_sha256=digest(load(out/'environment.json')),paths=paths,hashes=hashes,launch_ref=dict(source='launch',pointer='/'+platform),opposite_slot='Parser-only. No other platform runtime approval or measurement claim.')
    write(out/'seal.json',dict(version=2,**entry,master_denominator_sha256=digest(denom),projection_map_sha256=digest(load(out/'projection-map.json'))))
    return entry

def main():
    assert_original();families=[]
    for task in ('T1','T2','T3','T4','T5'):
        for family in ('public','private'):
            root,ref,master,denom=prepare_master(task,family);profiles={p:project(root,ref,master,denom,p) for p in ('ios','android')}
            approval=dict(version=2,independent_owner='Independent design/oracle author /root/v13_business_design',original_global_seal_sha256=ORIGINAL_SEAL,master_denominator_sha256=digest(denom),profiles=profiles,rule='Every native run must bind the actual config through admit_profile.py using an externally pinned canonical approval digest. A projected lock is approved only for its listed platform; no cross-platform native assertion/claim is authorized.')
            write(root/'PROFILE-APPROVAL.json',approval)
            for platform,p in profiles.items():
                config={k:str((root/v).resolve()) for k,v in p['paths'].items()};config.update({k:p[k] for k in ('design_sha256','policy_sha256','routes_sha256','environment_sha256','launch_ref')});write(root/platform/'admission-config.json',config)
                run(task+'/'+family+'/'+platform+' intended-profile admission',[root/'admit_profile.py','--root',root,'--approval',root/'PROFILE-APPROVAL.json','--approval-sha256',digest(approval),'--platform',platform,'--config',root/platform/'admission-config.json'])
            families.append(dict(task=task,family=family,master_cells=denom['total_cells'],profiles={p:dict(lock=v['design_sha256'],plan=v['hashes']['plan']) for p,v in profiles.items()},approval_sha256=digest(approval)))
    assert_original()
    write(ROOT/'PURE-COMPILATION.json',dict(version=2,status='passed',scope='20 intended-platform projections across all10 families; frozen pure seal/compile/review catalog/route audit/execution+guards/admission. No SDK/native or production source.',steps=len(steps),families=families,original_file_seal_sha256=ORIGINAL_SEAL,original_270_bytes_unchanged=True))
    print(json.dumps(dict(status='pure generators passed',profiles=20,families=10,steps=len(steps),root=str(ROOT))))

if __name__=='__main__':main()
