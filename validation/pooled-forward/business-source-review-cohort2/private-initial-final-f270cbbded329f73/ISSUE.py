"""Fresh independent private source-shape admission after verified public closure.

Reviewer-owned output only. No native SDK/build, source/oracle edit, result,
cost, self-claim or other-grader access. Exact input pins fail closed.
"""
import ast
import copy
import datetime
import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward')
OUT=Path(__file__).resolve().parent
REQUEST=R/'cache/business/independent-domain-requests/private-initial-final/request.json'
REQUEST_SHA='f270cbbded329f73405f8ed6f3c9bfcf98b6d48ed215652be8389a665e0dbb99'
SCOPE=('Independent finite eager main-vertical source-shape, actual thin bridge call/import, '
       'production placement and shared host SOURCE conformance only. No business correctness, '
       'expected-outcome, design-style, native dispatch, build, runtime, pixel, coverage or behavior P verdict.')
readset={}
sequence=0
barrier_checked=False

def sha(raw): return hashlib.sha256(raw).hexdigest()
def digest(value):
    return sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode())
def read(path,purpose):
    global sequence
    p=Path(path).resolve()
    if '/business-design-cohort2-v2/private/' in str(p):
        assert barrier_checked,'Private input access before closure verification'
    raw=p.read_bytes();sequence+=1
    if str(p) in readset:
        assert readset[str(p)]['sha256']==sha(raw),'Input changed during review'
        if purpose not in readset[str(p)]['purposes']:readset[str(p)]['purposes'].append(purpose)
    else:
        readset[str(p)]={'path':str(p),'sha256':sha(raw),'bytes':len(raw),'first_read_sequence':sequence,'purposes':[purpose]}
    return raw
def load(path,purpose): return json.loads(read(path,purpose))
def readref(ref,purpose,canonical=False):
    raw=read(ref['path'],purpose)
    assert (digest(json.loads(raw))if canonical else sha(raw))==ref['sha256'],ref['path']
    if 'bytes'in ref:assert len(raw)==ref['bytes']
    return raw
def save(name,value):
    raw=value if isinstance(value,bytes)else(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    p=OUT/name
    assert p.parent==OUT
    with p.open('xb')as f:f.write(raw)
    return {'path':str(p),'sha256':digest(value)if not isinstance(value,bytes)else sha(raw)}
def policy(value):
    value=copy.deepcopy(value)
    for key in ['approved_at_utc','approved_by']:value.pop(key,None)
    for platform in value['platforms'].values():platform.pop('approved_component_revisions',None)
    return value

request_raw=read(REQUEST,'Exact independent admission request and pointer metadata')
assert sha(request_raw)==REQUEST_SHA
request=json.loads(request_raw)
assert request['reviewer_id']=='shape-reviewer'and request['operator_id']=='study-controller'
cohort=json.loads(readref(request['cohort'],'Cohort closure metadata only'))
authorization=json.loads(readref(request['operator_first_private_admission'],'Operator first-private access authorization metadata'))
assert cohort['kind']=='cohort_sealed'and len(cohort['members'])==10
assert authorization['kind']=='operator-first-private-preparation-admission'
assert authorization['private_body_opened_before_this_record']is False
assert authorization['cohort']==request['cohort']
assert cohort['members']==authorization['members']
assert cohort['at_unix']<=authorization['at_unix']<=request['at_unix']
assert set(cohort['members'])=={f'T{i}/{arm}'for i in range(1,6)for arm in ['A','B']}
for ref in authorization['members'].values():
    readref(ref,'SELF-SEAL file-byte verification only; no parsing of costs, claims or outcomes')
for key in ['cohort_event','public_context_checkpoint']:
    readref(authorization[key],'Closure event/handoff pointer file-byte verification only')
for item in request['items']:
    for arm in ['A','B']:
        assert authorization['members'][item['task']+'/'+arm]['source_sha256']==item['actual_sources']['final-'+arm]['controller_content_sha256']
barrier_checked=True
barrier={
    'version':1,'status':'verified_before_private_body_access','request_file_sha256':REQUEST_SHA,
    'cohort':request['cohort'],'operator_first_private_admission':request['operator_first_private_admission'],
    'cohort_sequence':cohort['sequence'],'cohort_at_unix':cohort['at_unix'],
    'operator_admission_at_unix':authorization['at_unix'],'request_at_unix':request['at_unix'],
    'all_ten_self_seal_byte_hashes_matched':True,'cohort_operator_members_equal':True,
    'self_claims_costs_or_native_outcomes_parsed':False,
    'before_private_read_sequence':sequence,
    'reviewer_trace':'The reviewer first checked request/pointer bytes and closure metadata in tool calls before the first private profile/bridge/plan/environment read; this issuer repeats those checks before any private input body access.',
    'scope':'Closure and access authorization only; no grading, SDK or execution authorization supplied.'}
save('BARRIER-VERIFICATION.json',barrier)
mapping=json.loads(readref(request['approved_design_mapping'],'Original admitted design-profile/hash mapping metadata only'))
assert len(request['items'])==5

templates=[]
for item in request['items']:
    # Only shape/geometry fields are consumed from a prior public template.
    raw=readref(item['public_shape_template'],'Prior template: common_host_shape and geometry_encoding only',canonical=True)
    value=json.loads(raw)
    templates.append({key:value[key]for key in ['common_host_shape','common_host_shape_sha256','geometry_encoding','geometry_encoding_sha256']})
assert all(t==templates[0]for t in templates)
template=templates[0]
shape=template['common_host_shape'];shape_sha=template['common_host_shape_sha256']
encoding=template['geometry_encoding'];encoding_sha=template['geometry_encoding_sha256']
assert digest(shape)==shape_sha=='c7fbe68e0282ea56605c3c2708fc67e15607537c8fe673ff777da6e1705bee18'
assert digest(encoding)==encoding_sha=='aa335ed5809a23b048a20a7d0c0f86d51bad2d936b2c21d1ae736d8ff8995a84'

host_files=['assets/ios-observer/ObserverApp.swift','assets/ios-observer/ObserverTests.swift']
host={}
frozen_scripts={}
for rel in host_files+['assets/ios-observer/geometry-encoding.json','scripts/coverage_domain.py','scripts/scroll_coverage.py']:
    by_arm={name:read(Path(root)/rel,'Current frozen common host/encoding/admission source; SOURCE review only')for name,root in request['frozen_tool_roots'].items()}
    assert len(set(by_arm.values()))==1,'Frozen arm source mismatch'
    raw=next(iter(by_arm.values()))
    if rel in host_files:
        host[rel]=sha(raw)
        save('host-'+Path(rel).name,raw)
    if rel.endswith('geometry-encoding.json'):
        assert digest(json.loads(raw))==encoding_sha and json.loads(raw)==encoding
        save('geometry-encoding.json',raw)
    if rel.endswith('coverage_domain.py'):
        assert "SUPPORTED_ENCODING_SHA256='"+encoding_sha+"'"in raw.decode()
        frozen_scripts['coverage_domain.py']=raw.decode()

now=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
provider={
    'version':1,'status':'conforming','common_host_shape_sha256':shape_sha,'files':host,
    'approved_by':'shape-reviewer','approved_at_utc':now,
    'review_kind':'fresh_independent_private_initial_final_common_host_SOURCE_conformance',
    'request_file_sha256':REQUEST_SHA,'frozen_roots':request['frozen_tool_roots'],
    'both_current_frozen_arms_byte_identical':True,
    'original_observation':('I re-read the current ObserverApp.swift and ObserverTests.swift source. The app calls ObserverBridge.make directly as the first child of one eager VStack in its single vertical ScrollView, showsIndicators:false. The component is followed immediately by the final __observer.bottom staticText, with no later scroll content. Host padding is horizontal16/top24 and the ScrollView frame uses requested width and height600; fixed private metadata requests width390, light/ltr/large. Fixture/receipt/runtime controls are outside this region. The actual test-source full sweep calls capture(boundaryRequired:true); a reached terminal is resolved by unique native staticText query and exports the current frame and executed XCUIElement.isHittable with the input/event binding. Original raster/native registration separately rejects missing top, terminal ancestry/geometry, current hittability guard or content-end extent. This is source conformance, not an observation that any private run achieved those runtime facts.'),
    'source_locations':{
        'ObserverApp.swift':['58-65: vertical hidden-indicator scroll, direct bridge and final sentinel','66-80: host padding/frame/geometry and scroll identity','81-94: out-of-region controls and environment injection'],
        'ObserverTests.swift':['145-210: finite sweeps request boundary capture and retain epoch/extent metadata','258-273: unique actual terminal frame/isHittable query','331-341: original geometry encoding, epoch and boundary exports','501-715: original bounded native actions, receipts and same-process checks']},
    'prior_provider_record_copied':False,'native_execution_performed':False,'runtime_conformance_claimed':False,
    'scope':SCOPE}
provider_ref=save('common-host-source-conformance.json',provider)

OBSERVATIONS={
 'T1':{'root_lines':{'all':62},'callback_lines':{'all':246},'closure':['CateringPackageInput 3-44','CateringPackagePlanner and all view/action helpers 47-250','CateringPackageChoice/CateringServiceChoice 252-293','CateringPackageState and all local predicates/text 295-347','CateringPackageButtonStyle 349-354','CateringPackageColors 356-367'],
       'observation':'The complete catering source uses fixed two-case package/service loops, eager vertical sections and finite native text/Button helpers. onChange and all four handlers use local reconciled values; recordOrder calls the supplied callback synchronously before local recorded-state assignment. The identity ButtonStyle adds no custom content branch.'},
 'T2':{'root_lines':{'all':180},'callback_lines':{'all':336},'closure':['TrainingPathwayInput 4-42','TrainingPathway/TrainingParticipationMode 44-86','TrainingEnrollmentState 88-143','TrainingEnrollmentPalette 145-154','TrainingEnrollmentButtonStyle 157-162','TrainingPathwayEnrollment with header/text/caption/choice/primary and all four handlers 166-340'],
       'observation':'The training file closes all helpers and handlers in one source. Two fixed allCases collections are eagerly emitted under the main VStack. The header Group, labels, background decoration and selected checkmarks remain in the same flow. Input reconciliation is local; record directly invokes onEvent before local state assignment.'},
 'T3':{'root_lines':{'all':149},'callback_lines':{'all':325},'closure':['SubscriptionCapacityInput 3-38','SubscriptionCapacityPlan/SubscriptionCapacityTerm 40-60','Input.permits overloads 62-79','SubscriptionCapacityState 81-113','SubscriptionCapacityColors/ButtonStyle 115-130','SubscriptionCapacityChange with current/label/caption/planButton/termButton/choiceButton/primaryButton/status and four handlers 133-329'],
       'observation':'The capacity view explicitly emits two plan and two term Buttons inside eager vertical sections. The entire current-state, permits, label, choice, primary and handler closure is local. Background-only ZStack shapes decorate native labels and introduce no separate content surface. No business outcome or visual property is certified by these source modifiers.'},
 'T4':{'root_lines':{'all':188},'callback_lines':{'all':349},'closure':['VisitorAccessInput 3-47','VisitorAccessArea/VisitorAccessCredential 49-93','VisitorAccessSelection 95-152','VisitorAccessColors/ButtonStyle 154-171','VisitorAccessPreclearance with contentText/sectionText/choiceButton/primaryButton and all four handlers 174-353'],
       'observation':'The visitor source has immutable Bool fields, finite two-case area/credential choices and a single eager main VStack. Every custom text/Button helper, pure reconciliation predicate and synchronous action is present in the same file. The direct callback precedes the local recorded assignment. Framework onChange is deterministic parameter reconciliation without suspension or IO.'},
 'T5':{'root_lines':{'initial':178,'final':184},'callback_lines':{'initial':327,'final':333},'closure':['Both revisions: CandidateDispositionInput 3-44; root/detail enums 46-95; CandidateDispositionState 97-151; colors 153-162','Initial: CandidateDispositionReview including all section/text/button helpers and four handlers 165-331; stock PlainButtonStyle','Final: label-only CandidateDispositionButtonStyle 164-168; CandidateDispositionReview including all helpers and four handlers 171-337'],
       'observation':'Both distinct candidate revisions were inspected directly. They eagerly emit the same bounded two-root/four-detail choice collections under the main VStack. The initial revision uses stock PlainButtonStyle; the final revision defines a ButtonStyle whose entire makeBody returns configuration.label. Neither implementation creates a new content surface, external input, asynchronous business path or identity reset. All state/action helpers are in-file and the callback is synchronous. This records only their admissible shapes, not visual or business quality.'}
}

task_index={}
task_reviews=[]
prepare_inputs=[]
unique_count=0
for item in request['items']:
    task=item['task'];family=item['design_task'];component=item['component']
    declared=mapping['profiles']['private-'+family+'-ios']
    assert declared==item['approved_profile_metadata']
    profile=json.loads(readref(item['private_profile'],'Exact unchanged original private iOS profile metadata'))
    assert profile['platform']=='ios'and declared['intended_platform']=='ios'and declared['family']=='private'
    packet={}
    for key,rel in declared['paths'].items():
        path=R/'business-design-cohort2-v2'/rel
        purpose='Exact private bridge source/import/call closure'if key=='bridge'else'Unchanged private packet canonical/file binding; plan state/assertion scope only, no oracle grading'
        raw=read(path,purpose)
        canonical=digest(json.loads(raw))if path.suffix=='.json'else sha(raw)
        assert canonical==declared['hashes'][key],(task,key)
        field='design_lock'if key=='design_lock'else key
        assert Path(profile[field]).resolve()==path.resolve(),(task,key)
        packet[key]={'path':str(path),'file_sha256':sha(raw),'canonical_sha256':canonical,'bytes':len(raw)}
        if key=='bridge':
            text=raw.decode()
            assert 'import AlertToast'in text and 'static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView'in text
            assert f'AnyView({component}(input: input, onEvent: onEvent))'in text
            save(task+'-private-bridge.swift',raw)
    plan=load(profile['plan'],'Private plan selected states/full-content IDs and assertion count only')
    env=load(profile['environment'],'Private required fixed host environment')
    assert env=={'width':390,'height':600,'direction':'ltr','theme':'light','dynamic_type':'large'}
    assert plan['design_contract']['platform']=='ios'
    assert declared['design_sha256']==profile['design_sha256']==packet['design_lock']['canonical_sha256']
    assert declared['environment_sha256']==profile['environment_sha256']==packet['environment']['canonical_sha256']
    revisions={}
    installations=[]
    sources_by_hash={}
    for label,source in item['actual_sources'].items():
        capsule=readref(source['exact_capsule'],'Exact requested initial/final source capsule; complete custom closure manually inspected')
        installed=readref(source['installed_component'],'Actual installed initial/final production bytes and capsule equality')
        assert capsule==installed
        manifest=json.loads(readref(source['source_manifest'],'Exact initial/final sealed source manifest namespace metadata only'))
        assert manifest['content_sha256']==source['controller_content_sha256']
        assert manifest['files']['0/AlertToast/'+component+'.swift']=={'sha256':sha(capsule),'bytes':len(capsule)}
        package=readref(source['production_placement'],'Actual existing AlertToast package/export/target and iOS14 placement')
        package_text=package.decode()
        assert '.iOS(.v14)'in package_text and 'name: "AlertToast"'in package_text and 'targets: ["AlertToast"]'in package_text
        actual_path=Path(source['installed_component']['path'])
        project=Path(source['production_placement']['path']).parent
        assert actual_path==(project/'Sources/AlertToast'/f'{component}.swift')
        assert capsule.decode().splitlines()[0]=='import SwiftUI'
        assert 'public struct '+component+': View'in capsule.decode()
        key='actual_'+sha(capsule)
        revisions[key]={'sha256':sha(capsule),'bytes':len(capsule)}
        if sha(capsule)not in sources_by_hash:
            unique_count+=1
            capsule_name=task+'-source-'+sha(capsule)+'.swift'
            save(capsule_name,capsule)
            declarations=[{'line':n,'declaration':line.strip()}for n,line in enumerate(capsule.decode().splitlines(),1)
                if re.match(r'^\s*(?:(?:public|private|static)\s+)*(?:struct|enum|extension|func|init)\b',line)]
            sources_by_hash[sha(capsule)]={'sha256':sha(capsule),'bytes':len(capsule),'line_count':len(capsule.decode().splitlines()),'sealed_capsule':str(OUT/capsule_name),'declarations':declarations,'source_labels':[]}
        sources_by_hash[sha(capsule)]['source_labels'].append(label)
        installations.append({'label':label,'component':source['installed_component'],'capsule':source['exact_capsule'],'source_manifest':source['source_manifest'],'controller_content_sha256':source['controller_content_sha256'],'production_placement':source['production_placement'],'approved_revision':key})
        config=copy.deepcopy(profile)
        config['source_roots']=[str(project/'Sources')]
        config['native_options']={'package':str(project),'product':'AlertToast'}
        config['evidence_subjects']={'production_api':[str(actual_path)],'thin_bridge':[profile['bridge']],'production_placement':[str(project/'Package.swift')]}
        prepare_inputs.append({'task':task,'label':label,'config':config,'plan':plan})
    assert len(revisions)==len(sources_by_hash)
    domain={
        'version':1,'approved_by':'shape-reviewer','approved_at_utc':now,'scope':SCOPE,
        'binds':{
            'design_lock_sha256':packet['design_lock']['canonical_sha256'],
            'plan_canonical_sha256':packet['plan']['canonical_sha256'],
            'policy_canonical_sha256':packet['policy']['canonical_sha256'],
            'routes_canonical_sha256':packet['routes']['canonical_sha256'],
            'environment_ios_canonical_sha256':packet['environment']['canonical_sha256'],
            'required_native_assertions':len(plan['assertions']),
            'selected_state_ids':[s['id']for s in plan['states']],
            'full_content_state_ids':[s['id']for s in plan['states']if s.get('coverage')=='full_content']},
        'actual_subject_binding':{'component_subject':'production_api','bridge_subject':'thin_bridge'},
        'common_host_shape':copy.deepcopy(shape),'common_host_shape_sha256':shape_sha,
        'geometry_encoding':copy.deepcopy(encoding),'geometry_encoding_sha256':encoding_sha,
        'platforms':{'ios':{'component_install_path':'Sources/AlertToast/'+component+'.swift',
            'module':'AlertToast','product':'AlertToast','component_symbol':component,
            'exact_bridge':{'path':profile['bridge'],'sha256':packet['bridge']['file_sha256']},
            'approved_component_revisions':revisions}},
        'approved_inputs':{'private-'+family+'-ios':{
            'platform':'ios','fixture_canonical_sha256':packet['fixtures']['canonical_sha256'],
            'fixture_file_sha256':packet['fixtures']['file_sha256'],
            'launch_bridge_sha256':packet['bridge']['file_sha256']}}}
    domain_ref=save(task+'-private-ios-coverage-domain.json',domain)
    task_index[task]={'coverage_domain_ref':domain_ref,'coverage_policy_sha256':digest(policy(domain)),
        'profile_path':item['private_profile']['path'],'approved_revision_count':len(revisions),
        'native_assertions_bound':len(plan['assertions']),'unique_actual_sources':list(sources_by_hash.values())}
    task_reviews.append({'task':task,'design_task':family,'decision':'admit_exact_actual_initial_final_source_shapes_only',
        'private_packet':packet,'installations':installations,'unique_source_observations':list(sources_by_hash.values()),
        **OBSERVATIONS[task],
        'private_bridge_observation':'The exact private bridge imports SwiftUI and AlertToast, synchronously decodes immutable fixture primitives/arrays, directly returns the real exported production View and passes the same onEvent callback. It contains no view identity reset, state, business branch, test-only UI or asynchronous path.',
        'production_placement_observation':'Each listed initial/final source is byte-equal to its exact capsule and named in its sealed source manifest. The actual Package.swift exports the existing AlertToast library/target with iOS14 minimum and default Sources/AlertToast inclusion; no replacement UI or package is admitted.',
        'common_negative_shape_finding':'No source-owned scroll/lazy/virtualized surface, off-axis flow surface, popup/menu/dialog/sheet/foreground overlay, external live/time/random/network input, IO/suspending business work, hidden fixture lookup or forced identity reset was found in any reviewed custom closure. Finite local conditions and deterministic onChange reconciliation remain permitted.',
        'claim_limit':'Source/API/call/import/placement shape only. Business predicates/text/events, fonts/colors/sizes, native compile/dispatch, runtime epochs, original pixels and terminal coverage remain unassessed.'})
assert unique_count==6

# Exact unchanged prepare bodies are exercised with a local canonical JSON
# adapter only, avoiding imports outside the explicitly reviewed source scope.
checks=[]
for arm,root in request['frozen_tool_roots'].items():
    path=Path(root)/'scripts/coverage_domain.py'
    text=read(path,'Exact prepare-only field/source compatibility; no native execution').decode()
    parsed=ast.parse(text)
    keep=[n for n in parsed.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in {'DomainReviewRequired','sha','pinned','policy','prepare'}]
    ns={'__file__':str(path),'Path':Path,'hashlib':hashlib,'copy':copy,'SUPPORTED_ENCODING_SHA256':encoding_sha,
        'd':SimpleNamespace(load=lambda p:json.loads(Path(p).read_bytes()),digest=digest)}
    exec(compile(ast.Module(body=keep,type_ignores=[]),str(path),'exec'),ns)
    for item in prepare_inputs:
        config=item['config']
        config['coverage_domain_ref']=task_index[item['task']]['coverage_domain_ref']
        config['coverage_provider_ref']=provider_ref
        result=ns['prepare'](config,item['plan'],json.loads(Path(config['design_lock']).read_bytes()))
        checks.append({'task':item['task'],'source_label':item['label'],'frozen_tool_arm':arm,
            'status':'prepare_accepted_exact_shape_binding','approval_sha256':result['approval_sha256'],
            'policy_sha256':result['policy_sha256'],'provider_sha256':result['provider_sha256'],
            'component_sha256':result['component']['sha256'],'revision':result['revision']})
assert len(checks)==30
save('PREPARE-COMPATIBILITY.json',{'version':1,'status':'accepted_30_exact_combinations','checks':checks,
    'scope':'Five private tasks x initial/final-A/final-B x both frozen tools, unchanged prepare bodies and local canonical JSON adapter only; no complete(), intended-platform CLI admission, SDK, native capture or runtime proof.'})
save('SOURCE-OBSERVATIONS.json',{'version':1,'kind':'independent-private-initial-final-source-shape-review',
    'reviewer_id':'shape-reviewer','request_file_sha256':REQUEST_SHA,'scope':SCOPE,
    'decision':'admit_exact_six_unique_actual_ios_source_revisions_only','sources_inspected':6,
    'actual_installation_bindings':15,'tasks':task_reviews,'native_runtime_or_behavior_passes_supplied':0,
    'public_profile_or_config_versions_edited':False,'private_or_public_source_or_oracle_edited':False,
    'adoption_window_or_permission_added':False,'source_deadline_extended':False})

# Recheck all read inputs for byte stability without parsing any sealed claims.
for item in list(readset.values()):
    assert sha(Path(item['path']).read_bytes())==item['sha256'],'Reviewed input changed'
save('READSET.json',{'version':1,'reviewer_id':'shape-reviewer','request_file_sha256':REQUEST_SHA,
    'scope':SCOPE,'files':sorted(readset.values(),key=lambda v:v['first_read_sequence']),
    'prior_template_consumption':'Only common_host_shape/geometry_encoding and their pins were consumed; old source revisions and provider observations were not inherited.',
    'private_data_use':'Private profile/lock/plan/policy/routes/environment/fixtures were used solely for unchanged canonical/file pins, platform and selected/full-content state/assertion counts; private bridge source was inspected for actual ABI/import/call shape.',
    'excluded':['SDK/native/render/build','cost or self-claim inspection','other grader results','product/style/expected-output grading','source/oracle/criteria edits','capture-adoption window'],
    'actual_first_private_access_barrier':'Verified in reviewer tool chronology before first private input body read; repeated and fail-closed in this issuer.'})
index={'version':1,'kind':'independent-private-source-shape-admission-index','reviewer_id':'shape-reviewer',
    'issued_at_utc':now,'request':{'path':str(REQUEST),'sha256':REQUEST_SHA},'scope':SCOPE,
    'decision':'admit_exact_initial_final_ios_sources_for_unchanged_private_profiles',
    'tasks':task_index,'coverage_provider_ref':provider_ref,
    'common_host_shape_sha256':shape_sha,'geometry_encoding_sha256':encoding_sha,
    'unique_actual_source_revisions':6,'actual_installation_bindings':15,
    'duplicate_approved_revision_aliases':0,'native_runtime_or_behavior_passes_supplied':0,
    'source_or_oracle_edits':0,'capture_adoption_permissions_added':0,
    'controller_obligations':'Separate delivery provenance, original intended-platform guard, frozen helper authorize-hidden before helper private-config open/acquisition, and actual SDK/epoch/raster/top/terminal proofs remain required. This record grants no repair/source deadline extension or public admission after closure.'}
save('INDEX.json',index)
members={p.name:sha(p.read_bytes())for p in sorted(OUT.iterdir())if p.is_file()and p.name!='SEAL.json'}
seal={'version':1,'kind':'independent-private-source-shape-admission-seal','reviewer_id':'shape-reviewer',
    'request_file_sha256':REQUEST_SHA,'scope':'source_shape_only','files':members}
sealraw=(json.dumps(seal,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
save('SEAL.json',sealraw)
assert set(p.name for p in OUT.iterdir())==set(members)|{'SEAL.json'}
for name,expected in members.items():assert sha((OUT/name).read_bytes())==expected
print(json.dumps({'decision':index['decision'],'seal_path':str(OUT/'SEAL.json'),'seal_file_sha256':sha(sealraw),
    'seal_canonical_sha256':digest(seal),'index_path':str(OUT/'INDEX.json'),'index_canonical_sha256':digest(index),
    'coverage_provider_ref':provider_ref,'task_coverage_domain_refs':{k:v['coverage_domain_ref']for k,v in task_index.items()},
    'sealed_member_count':len(members),'unique_source_revisions':6,'prepare_combinations':len(checks)},indent=2))
