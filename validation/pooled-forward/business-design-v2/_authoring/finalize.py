#!/usr/bin/env python3
"""Finalize/seal V2 after pure compatibility checks, without touching V1 or native SDKs."""
from revise import *

def main():
    assert_original();equivalence=[];negative=[];coverage_promotions=[]
    for task in ('T1','T2','T3','T4','T5'):
      for family in ('public','private'):
        root=ROOT/task/family;old=OLD/task/family
        # Complete master remains an honest independent source, though its asymmetric
        # applicability intentionally needs the projected frozen-format namespaces.
        master=load(root/'master-contract.json')
        for s in master['sources']:s['sha256']=sha((root/s['path']).read_bytes())
        write(root/'master-contract.json',master)
        orig=load(old/'reference.json');new=load(root/'reference.json');expected=rename_strings(orig);expected['states']=statekeys(expected['states'])
        for p,k in (('ios','titleWeight'),('android','titleWeight'),('android','bodyWeight')):expected['tokens'][p][k]['unit']='scalar'
        assert expected==new
        od=rename_strings(load(old/'denominator.json'))
        for c in od['cells']:
            if c['requirement']=='heading-native-weight':c['platforms']['android']['unit']='scalar'
        assert od==load(root/'denominator.json')
        for name in ('outcomes.json','target-observations.json','routes.json','actions.ios.json','actions.android.json','launch.json'):assert rename_strings(load(old/name))==load(root/name),name
        unchanged=('API.md','PIXEL-SCOPE.md','fixture.schema.json','ObserverBridge.swift','ObserverBridge.kt','fixtures.ios.json','fixtures.android.json','bindings.ios.json','bindings.android.json','environment.ios.json','environment.android.json','reference-initial.svg','reference-ready.svg')
        for name in unchanged:assert (old/name).read_bytes()==(root/name).read_bytes(),name
        approval=load(root/'PROFILE-APPROVAL.json')
        for platform in ('ios','android'):
            p=root/platform;opposite='android' if platform=='ios' else 'ios'
            argv=[sys.executable,'-B',str(root/'admit_profile.py'),'--root',str(root),'--approval',str(root/'PROFILE-APPROVAL.json'),'--approval-sha256',digest(approval),'--platform',opposite,'--config',str(p/'admission-config.json')]
            r=subprocess.run(argv,cwd=REPO,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
            assert r.returncode!=0 and 'Wrong approved' in r.stderr
            negative.append(dict(task=task,family=family,config_platform=platform,requested_platform=opposite,expected_rejection=True,actual_exit_code=r.returncode,reason=r.stderr.strip().splitlines()[-1],argv=argv,native_executed=False))
            projection=load(p/'projection-map.json');coverage_promotions.extend(dict(task=task,family=family,platform=platform,**v) for v in projection['execution_coverage_required_by_existing_absence'])
            generated=load(p/'generated/plan.json');execution=load(p/'execution/execution.json');outcomes=load(root/'outcomes.json');actions=master['scenarios'][next(iter(master['scenarios']))]['actions']
            previous=None
            for state in outcomes['states']:
                if 'stimulus_action' in state:
                    action=actions[state['stimulus_action']]
                    if action['type']=='tap':
                        target=action['target'];assert previous is not None
                        assert previous['primary_enabled'] if target=='primary' else previous['controls'][target]['enabled']
                        for condition in action['preconditions']:
                            if condition['property']=='selected':assert previous['controls'][target]['selected']==condition['expected']
                    for rule in generated['assertions']:
                        if rule['state']==state['id'] and rule['kind']=='event':assert rule['action_index']==state['stimulus_action'] and rule['expected']==state['exact_callback_interval']
                previous=state['exact_business_state']
            assert all(a['type'] in ('sweep','tap','checkpoint','apply_next_fixture') for a in execution['actions'])
            assert all(a.get('depends_on')==([i-1] if i else []) for i,a in enumerate(execution['actions']))
        equivalence.append(dict(task=task,family=family,complete_cells=od['total_cells'],original_business_state_values_unchanged=True,fixture_and_bridge_and_svg_bytes_unchanged=True,exact_questions_unchanged=True,coverage_and_guards_unchanged=True,changes_only=['initial→start state identity','number→scalar dimensionless font-weight unit spelling','platform projection plus restricted expression slots','frozen coarse visual taxonomy metadata']))
    write(ROOT/'EQUIVALENCE.json',dict(version=2,status='passed',all_master_cells=sum(v['complete_cells'] for v in equivalence),families=equivalence,warning='Frozen execution planner promotes target-scoped states containing an already approved native absence to full_content. This is acquisition required by that existing assertion, not added design coverage or a changed outcome.',existing_absence_coverage_promotions=coverage_promotions))
    write(ROOT/'NEGATIVE-ADMISSION.json',dict(version=2,status='all20 cross-platform profile attempts rejected as intended',attempts=negative,scope='Pure external intended-platform admission only; no native invocation or fake native observation.'))
    rejection_sha='65e3aa38510fab4e54395a63f4bc6ce5f69720a8af7dcc888b96857e8098ddf8'
    write(ROOT/'REVISION-LEDGER.json',dict(version=2,original_directory=str(OLD),original_file_seal_sha256=ORIGINAL_SEAL,original_files_preserved_unchanged=270,rejection_record='validation/pooled-forward/business-design-review/REJECTION-SEAL.json',rejection_file_sha256=rejection_sha,reviewer='/root/v13_design_admission',phase='All five revised public/private designs fixed before any production implementation or SDK rendering',revisions=[
        dict(id='R1',finding='Frozen validator supports whole-cell N/A only and validates both platform expressions.',change='Create separate intended-platform contracts/locks/rule universes, retain full shared denominator with original explicit N/A, and map every cell through projection-map.json. Unused opposite expression slots are schema-only; PROFILE-APPROVAL and external admit_profile reject cross-platform use.',scope_limit='No new frozen-tool applicability support or iOS computed-style capability; no mandatory iOS U padding.'),
        dict(id='R2',finding='Font weight unit number unsupported; native font_weight requires scalar.',change='Rename only dimensionless unit metadata to scalar for unchanged600/400 values; preserve all source provenance and Android expected weight600.'),
        dict(id='R3',finding='Explicit action state ID initial is reserved.',change='Rename explicit state identity initial to start consistently in route, state/source pointers, outcomes, denominator and observation targets. Host fixture transport key initial remains byte-identical.'),
        dict(id='R4',finding='Atomic policy visual aspect enum is closed.',change='Keep every primitive property/question/Boolean separate; map wrap→wrapping, overlap→overlap, horizontal fit and rounded boundary→clipping, marks→content_presence, typography/ink/spacing/insets→broad hierarchy. This is taxonomy metadata only, not new measurement capability.')],normative_changes=dict(business_rules=False,fixture_data=False,expected_business_values=False,questions=False,callback_payloads=False,tolerances=False,sampling=False,coverage=False,production_api=False),pure_verification=dict(intended_profiles=20,successful_frozen_cli_steps=120,cross_platform_rejections=20,sdk_commands=0),approval_status='Author-proposed revision sealed for independent preimplementation review, not yet external acceptance'))
    write(ROOT/'INDEPENDENCE.md','''# Independent V2 representation revision

The same independent author revised only frozen-format compatibility in a new directory. The original business-design270-file seal remains byte-for-byte unchanged and is retained externally as6e82784fde88cb617d1e68ee5cac6dab8514eeddd526eb77a95c34f3040dbd60. Current independent rejection and exact blocker groups are cited in REVISION-LEDGER.json; no implementing source, SDK, screenshot, performance result, prior study or candidate-specific answer was used.

Business rules, public/hidden caller data, actual expected UI/business values, exact primitive visual questions, production APIs, bridges, sampling rectangles/support/tolerance, guarded stimuli and selected coverage are unchanged. State identity initial becomes start to satisfy the frozen reserved-ID rule; dimensionless font-weight unit spelling becomes scalar. EQUIVALENCE.json checks all13,358 cells and exact source/fixture/bridge/reference bytes where unchanged.

The frozen compiler cannot express platform-local N/A. It remains unmodified. Each family retains its complete master denominator and explicit N/A reasons. Intended-platform namespaces contain only their actual rule universe, with an approval mapping and external runtime admission guard that pin platform, lock, plan, policy, routes, environment, fixtures and bridge. The frozen schema's mandatory unused opposite slots are parser-only; they authorize no opposite-platform run and establish no unsupported iOS native measurement. All20 wrong-platform profile attempts are rejected by that guard.

All20 intended-platform profiles passed the real frozen pure seal, compile, atomic catalog, route audit, execution/guard generation and profile admission commands (120 successful CLI calls). No native run was requested. The existing execution planner's full-sweep requirement for an already approved native absence is recorded explicitly; it does not add a business requirement or silently carry a previous pass.

Visual taxonomy is coarse. Every original primitive property and exact question remains single-aspect and separate. hierarchy is a broad frozen category for visual organization; clipping covers visible rounded boundaries. This grants no new computed layout/font/color capability.

This is an author seal awaiting independent admission, not external approval or native acceptance. Only T*/public/ may be sent to initial implementation/repair workers. Every private family, _authoring script and hidden projection remains embargoed until ALL10 final source/selfclaim seals are verified. No hidden requirement or tolerance has been added. All five revised public and private designs are fixed together before any initial source.
''')
    imported=ROOT/'_pure-checks/imported-modules.json'
    code="import sys,json;sys.path.insert(0,"+repr(str(TOOLS))+");import design_contract,review_contract,requirement_routes,execution_plan,acceptance;print(json.dumps(sorted(set(m.__file__ for m in list(sys.modules.values()) if getattr(m,'__file__',None) and m.__file__.startswith("+repr(str(TOOLS))+")))))"
    modules=subprocess.run([sys.executable,'-B','-c',code],capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},check=True)
    paths=json.loads(modules.stdout);write(imported,dict(version=2,scope='Pure-generator imports only; no SDK/runtime function invoked',files=[dict(path=p,sha256=sha(Path(p).read_bytes())) for p in paths]))
    write(ROOT/'READSET.json',dict(version=2,original_readset=str(OLD/'READSET.json'),original_readset_sha256=sha((OLD/'READSET.json').read_bytes()),additional_reads='Current own sealed designs and current independent reviewer blocker messages; frozen pure generator/schema modules only under candidate-v13.9/scripts',generator_modules=load(imported)['files'],forbidden='No production implementation/test, SDK, renderer, native observation, historical study or performance result read or executed.'))
    write(ROOT/'INDEX.md','''# Five revised paired native component designs

This directory supersedes the original author draft only for frozen-tool representation. The original270 files and seal remain unchanged. REVISION-LEDGER.json cites the independent rejection; EQUIVALENCE.json verifies unchanged business rules, inputs, expected values, questions, sampling and coverage across all13,358 master cells.

Each T1..T5 has separate public/private families. Public families contain the exact shared brief/API/schema/fixtures/bridges/SVGs/outcomes/denominator and two intended-platform namespaces, ios/ and android/. Use each namespace's lock/generated plan/policy/routes/environment with its platform only. PROFILE-APPROVAL.json and admit_profile.py enforce the exact mapping before any native run. A schema-only opposite expression slot never constitutes runtime approval or measurement evidence.

PURE-COMPILATION.json and _pure-checks contain120 real successful frozen pure CLI calls for all20 intended-platform profiles. NEGATIVE-ADMISSION.json records20 expected wrong-platform rejections. No SDK/native acquisition or implementation was performed. Atomic catalogs, route audits and execution/guard manifests are included in each platform namespace. Independent preimplementation review remains required before code.

Implementation workers receive ONLY T*/public/. Private inputs/expectations, private namespaces and _authoring remain embargoed until ALL10 final source/selfclaim seals. SEAL.sha256 pins all revised files including time/readset/revision/proof records; its own exact digest is retained externally by the coordinator.
''')
    assert_original()
    write(ROOT/'TIME.json',dict(version=2,sealed_utc=datetime.now(timezone.utc).isoformat(),phase='All five public/private representation revisions fixed before any initial production source',original270files_unchanged=True,sdk_or_render_commands=0,production_implementation_files_read=0))
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='SEAL.sha256' and '__pycache__' not in p.parts)
    text=''.join(sha(p.read_bytes())+'  '+str(p.relative_to(ROOT))+'\n' for p in files);write(ROOT/'SEAL.sha256',text)
    for line in text.splitlines():
        d,p=line.split('  ',1);assert sha((ROOT/p).read_bytes())==d
    print(json.dumps(dict(root=str(ROOT),seal_sha256=sha(text.encode()),sealed_files=len(files),original_preserved=True,pure_profiles=20,pure_positive_commands=120,wrong_platform_rejections=20,complete_master_cells=13358)))

if __name__=='__main__':main()
