"""Issue source-shape-only approvals from the explicitly permitted initial readset.

No SDK, build, rendering, native data, private packets, old cases, or source edits.
All writes are exclusive and confined to this reviewer-owned directory.
"""
import ast
import copy
import datetime
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

R = Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward')
OUT = Path(__file__).resolve().parent
DESIGN = R / 'business-design-cohort2-v2'
DESIGN_REVIEW = R / 'business-design-cohort2-review/revision-v2'
ARM_NAMES = ['candidate-v13.9', 'baseline-v12.6-common-6']
HOST_FILES = ['assets/ios-observer/ObserverApp.swift', 'assets/ios-observer/ObserverTests.swift']
FROZEN_FILES = HOST_FILES + ['assets/ios-observer/geometry-encoding.json',
    'assets/ios-observer/CONTRACT.md', 'scripts/coverage_domain.py', 'scripts/scroll_coverage.py']
readset = {}
issued = {}

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

def read(path, purpose):
    path = Path(path).resolve()
    raw = path.read_bytes()
    item = {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'purpose': purpose}
    if path in readset:
        assert readset[path]['sha256'] == item['sha256'], 'Input changed while reviewing'
    else:
        readset[path] = item
    return raw

def load(path, purpose):
    return json.loads(read(path, purpose))

def save(name, value):
    path = OUT / name
    assert path.parent == OUT
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()
    with path.open('xb') as handle:
        handle.write(raw)
    issued[name] = {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(),
                    'canonical_sha256': digest(value), 'bytes': len(raw)}
    return {'path': str(path), 'sha256': digest(value)}

def description(symbol, first, last, kind):
    return {'symbol': symbol, 'start_line': first, 'end_line': last, 'kind': kind}

CASES = [
    {'task': 'T1', 'family': 'catering-package', 'component': 'CateringPackagePlanner',
     'input': 'CateringPackageInput', 'swift_root': 62, 'kotlin_root': 58,
     'swift_closure': [description('CateringPackageInput',3,44,'immutable public input and initializer'),
        description('CateringPackagePlanner',47,250,'public View; body and all four action handlers'),
        description('sectionCaption / secondaryText / choiceButton / recordButton',134,213,'finite native view helpers'),
        description('selectPackage / selectService / toggleConfirmation / recordOrder',215,249,'synchronous local handlers'),
        description('CateringPackageChoice / CateringServiceChoice',252,293,'two-case local enums and predicates'),
        description('CateringPackageState',295,347,'local state and pure reconciliation/text predicates'),
        description('CateringPackageButtonStyle',349,354,'identity native label style'),
        description('CateringPackageColors',356,367,'local constants')],
     'kotlin_closure': [description('CateringPackageInput',35,48,'immutable public input'),
        description('CateringPackagePlanner',51,168,'public composable and all inline handlers'),
        description('CateringCaption / CateringSecondaryText / CateringChoiceButton',170,246,'finite native view helpers'),
        description('CateringPackageChoice / CateringServiceChoice',248,269,'two-case local enums and predicates'),
        description('CateringPackageState',271,310,'local state and pure reconciliation/text predicates'),
        description('CateringPackageColors / CateringTitleStyle / CateringBodyStyle / CateringSectionStyle',312,346,'local constants')],
     'swift_callback_line':246, 'kotlin_callback_line':142},
    {'task': 'T2', 'family': 'training-pathway', 'component': 'TrainingPathwayEnrollment',
     'input': 'TrainingPathwayInput', 'swift_root':180, 'kotlin_root':156,
     'swift_closure': [description('TrainingPathwayInput',4,42,'immutable public input and initializer'),
        description('TrainingPathway / TrainingParticipationMode',44,86,'two-case local enums and predicates'),
        description('TrainingEnrollmentState',88,143,'local state and pure reconciliation/text predicates'),
        description('TrainingEnrollmentPalette',145,154,'local constants'),
        description('TrainingEnrollmentButtonStyle',157,162,'identity native label style'),
        description('TrainingPathwayEnrollment',166,340,'public View with complete body/helper/handler closure'),
        description('header / text / caption / choice / primary',222,307,'finite native view helpers'),
        description('choose(pathway) / choose(mode) / toggleConfirmation / record',309,339,'synchronous local handlers')],
     'kotlin_closure': [description('TrainingPathwayInput',36,48,'immutable public input'),
        description('TrainingPathway / TrainingParticipationMode',50,75,'two-case local enums and predicates'),
        description('TrainingEnrollmentState',77,117,'local state and pure reconciliation/text predicates'),
        description('TrainingEnrollmentPalette / TrainingBodyStyle / TrainingSectionStyle',119,144,'local constants'),
        description('TrainingPathwayEnrollment',148,238,'public composable and all inline handlers'),
        description('TrainingBody / TrainingCaption / TrainingChoice / TrainingPrimary',240,339,'finite native view helpers')],
     'swift_callback_line':336, 'kotlin_callback_line':233},
    {'task':'T3', 'family':'subscription-capacity', 'component':'SubscriptionCapacityChange',
     'input':'SubscriptionCapacityInput', 'swift_root':149, 'kotlin_root':146,
     'swift_closure': [description('SubscriptionCapacityInput',3,38,'immutable public input and initializer'),
        description('SubscriptionCapacityPlan / SubscriptionCapacityTerm',40,60,'two-case local enums'),
        description('SubscriptionCapacityInput.permits overloads',62,79,'pure local predicates'),
        description('SubscriptionCapacityState',81,113,'local state and pure reconciliation predicates'),
        description('SubscriptionCapacityColors / SubscriptionCapacityButtonStyle',115,130,'local constants and identity label style'),
        description('SubscriptionCapacityChange',133,329,'public View with complete body/helper/handler closure'),
        description('current / label / caption / planButton / termButton / choiceButton / primaryButton / status',144,295,'pure state projection and finite native view helpers'),
        description('choose(plan) / choose(term) / toggleConfirmation / record',297,328,'synchronous local handlers')],
     'kotlin_closure': [description('SubscriptionCapacityInput',38,49,'immutable public input'),
        description('CapacityPlan / CapacityTerm',51,59,'two-case local enums'),
        description('SubscriptionCapacityInput.permits overloads',61,70,'pure local predicates'),
        description('CapacitySelection / fresh',72,96,'local state and pure reconciliation predicates'),
        description('CapacityColors / CapacityBodyStyle / CapacitySectionStyle',98,122,'local constants'),
        description('SubscriptionCapacityChange / choosePlan / chooseTerm',124,236,'public composable and all local or inline handlers'),
        description('CapacityLabel / CapacityChoice / capacityStatus',238,310,'finite native view helpers and pure local text predicate')],
     'swift_callback_line':325, 'kotlin_callback_line':213}
]

SCOPE = ('Independent finite eager main-vertical source-shape, actual public bridge call/import, '
         'production placement and shared host SOURCE conformance only. No business correctness, '
         'expected-outcome, design-style, native dispatch, build, runtime, pixel, coverage or behavior P verdict.')
now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
rubric = read(DESIGN_REVIEW/'SOURCE-REVIEW-RUBRIC.md','Permitted final public finite-source review rubric').decode()
seal = load(DESIGN_REVIEW/'APPROVAL-SEAL.json','Permitted final public design-admission identity only')
entry = load(DESIGN_REVIEW/'PUBLIC-READY-ENTRY-MAP.json','Permitted final public task and exact authored bindings')
assert hashlib.sha256(rubric.encode()).hexdigest() == seal['artifacts']['SOURCE-REVIEW-RUBRIC.md']
assert hashlib.sha256(read(DESIGN_REVIEW/'PUBLIC-READY-ENTRY-MAP.json','Permitted final public task bindings')).hexdigest() == seal['artifacts']['PUBLIC-READY-ENTRY-MAP.json']

frozen = {}
for rel in FROZEN_FILES:
    raws = [read(R/arm/rel,'Named frozen common host/contract or exact coverage-admission/registration source') for arm in ARM_NAMES]
    assert raws[0] == raws[1], f'Frozen host support files differ: {rel}'
    frozen[rel] = {'sha256': hashlib.sha256(raws[0]).hexdigest(), 'bytes':len(raws[0]), 'both_frozen_arms_byte_identical':True}
encoding = json.loads(read(R/ARM_NAMES[0]/'assets/ios-observer/geometry-encoding.json','Exact independently fixed geometry encoding'))
encoding_sha = digest(encoding)
assert encoding_sha == 'aa335ed5809a23b048a20a7d0c0f86d51bad2d936b2c21d1ae736d8ff8995a84'

shape = {
    'version':1,
    'shape_id':'finite-eager-main-vertical-component-entry-v1',
    'entry':'One real exported finite component returned by the fixed thin bridge; arbitrary task-specific business branches remain local and finite.',
    'component_scope':{
        'root':'One eager main vertical stack or column; finite section stacks and row labels are in that same content flow.',
        'finite_inputs':'Only the individually hashed immutable public fixture packet is admitted; arbitrary inputs and universal arithmetic safety are unassessed.',
        'state':'Finite local selection/confirmation/receipt state and deterministic synchronous parameter reconciliation are permitted.',
        'business_outcome':'Unassessed; wrong business predicates or text do not by themselves violate source shape.',
        'prohibited':['component-owned scrolling','lazy or virtualized content','off-axis scroll or independently occluded content surfaces','popup, sheet, menu, dialog or foreground overlay','external live/time/random/network business inputs','suspending, asynchronous or IO-driven business paths','fixture-index lookup or forced view identity reset'],
        'framework_reconciliation':'Deterministic onChange, guarded parameter reconciliation, or SideEffect without suspension/IO is local framework reconciliation, not external async.'
    },
    'ios':{
        'requested_offered_width_pt':390,
        'viewport_height_pt':600,
        'theme':'light','direction':'ltr','dynamic_type':'large',
        'scroll_root_identifier':'__observer.scroll',
        'scroll_axes':'vertical',
        'scroll_indicators':'deterministically_hidden',
        'horizontal_padding_pt':16,'top_padding_pt':24,
        'bridge_entry':'ObserverBridge.make(fixture:onEvent:)',
        'bridge_placement':'Direct first child of eager host VStack inside the only vertical ScrollView.',
        'terminal_identifier':'__observer.bottom',
        'terminal_placement':'Immediate final child after the component; no later content inside the scroll content stack.',
        'controls_and_metadata':'Fixture update, receipt and runtime controls are outside the component scroll region.',
        'native_terminal_guard':'For a full sweep, the source queries exactly one current native terminal staticText, records frame and XCUIElement.isHittable with the capture binding; later independent registration requires actual inside-viewport terminal geometry and content end.',
        'host_metadata_only':'UUID, process information and uptime are observer epoch/event instrumentation, not inputs to production business state.',
        'runtime_obligation':'Actual viewport/environment/scale, source compile identity, stable input/event epochs, exact original raster overlap and top/terminal boundaries remain required separately.'
    },
    'claim_limit':SCOPE
}
shape_sha = digest(shape)
shape_ref = save('common-host-shape.json', shape)
provider = {
    'version':1,'status':'conforming','common_host_shape_sha256':shape_sha,
    'files':{rel:frozen[rel]['sha256'] for rel in HOST_FILES},
    'approved_by':'shape-reviewer','approved_at_utc':now,
    'review_kind':'independent_common_host_SOURCE_conformance',
    'frozen_arms':ARM_NAMES,
    'both_frozen_arms_exact_shared_host_bytes':True,
    'reviewed_source':{
        'ObserverApp.swift':['58: hidden-indicator vertical ScrollView','59-65: eager bridge then immediate final terminal','66-79: fixed host padding and width/600 viewport geometry','81-94: controls outside viewport and environment injection'],
        'ObserverTests.swift':['145-210: bounded sweeps request boundary capture','258-273: unique native terminal query and actual isHittable export','331-340: exact native geometry encoding declaration and snapshot/epoch bindings','501-715: actual native actions, same-process checks and finite observation loop'],
        'scroll_coverage.py':['native_rows requires exact supported encoding and actual epoch bindings','native_rows requires true top, unique actual terminal ancestry/geometry, executed current native hittability guard and terminal content extent','certify retains independent original raster/native registration obligation']
    },
    'scope':SCOPE,
    'native_execution_performed':False,'runtime_conformance_claimed':False,'behavior_pass_claimed':False,
    'copied_provider_conformance_or_qualification_metadata':False
}
provider_ref = save('common-host-source-conformance.json',provider)

reports = []
configs = []
for c in CASES:
    task, family, component = c['task'],c['family'],c['component']
    base = DESIGN/'public/tasks'/family
    public = {}
    for platform,ext in [('ios','swift'),('android','kt')]:
        declared = entry['profiles'][f'public-{family}-{platform}']
        packet = {}
        for key, rel in declared['paths'].items():
            path = DESIGN/rel
            raw = read(path,'Exact admitted public packet binding; plan scope only, no expected-outcome grading')
            file_sha = hashlib.sha256(raw).hexdigest()
            canonical = digest(json.loads(raw)) if path.suffix == '.json' else file_sha
            assert canonical == declared['hashes'][key], (task,platform,key,'authored binding changed')
            packet[key] = {'path':str(path),'file_sha256':file_sha,'canonical_sha256':canonical,'bytes':len(raw)}
        public[platform] = packet
    api = read(base/'API.md','Public API signatures, scalar transport and fixed bridge contract').decode()
    schema = load(base/'fixture.schema.json','Public immutable field types and signed Int32 transport domain')
    profile = load(base/'ios/profile.json','Original public profile identity; pure placeholder roots are not approved')
    for field,value in schema['properties'].items():
        if value['type']=='integer':
            assert value.get('minimum',-2147483648) >= -2147483648
            assert value.get('maximum') == 2147483647
    source_seal_path=R/f'cache/business/initial/{task}/source-seal/SEAL.json'
    source_seal=load(source_seal_path,'Exact permitted initial source-seal manifest; referenced compile result not opened')
    assert source_seal['task']==task
    swift_rel=f'Sources/AlertToast/{component}.swift'
    kotlin_rel=f'app/src/main/java/com/example/reply/ui/components/business/{component}.kt'
    subjects={}
    for platform,project_rel,component_rel,seal_key in [
        ('ios','alerttoast',swift_rel,f'0/AlertToast/{component}.swift'),
        ('android','reply/Reply',kotlin_rel,f'1/java/com/example/reply/ui/components/business/{component}.kt')]:
        files=[]
        for arm in ['A','B']:
            project=R/f'cache/business/{task}/{arm}/workspace'/project_rel
            p=project/component_rel
            raw=read(p,'Actual sealed initial production closure; A fully inspected, B compared byte-for-byte')
            assert source_seal['source_files'][seal_key] == {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
            assert source_seal['arms'][arm]['source_files'][seal_key] == source_seal['source_files'][seal_key]
            files.append({'arm':arm,'project':str(project),'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
            if platform=='ios':
                package_raw=read(project/'Package.swift','Actual existing AlertToast product/target and iOS 14 source placement')
                assert '.iOS(.v14)' in package_raw.decode()
                assert 'name: "AlertToast"' in package_raw.decode()
                assert 'targets: ["AlertToast"]' in package_raw.decode()
        assert readset[Path(files[0]['path'])]['sha256']==readset[Path(files[1]['path'])]['sha256']
        subjects[platform]={'files':files,'component_install_path':component_rel,'A_B_byte_identical':True,'initial_seal_matches':True}
    plan=load(base/'ios/generated/plan.json','Exact selected states and full-content state scope only')
    fixtures=load(base/'ios/fixtures.json','Exact approved immutable public packet; no expected-outcome inspection')
    env=load(base/'ios/environment.json','Exact required public host environment')
    assert env=={'width':390,'height':600,'direction':'ltr','theme':'light','dynamic_type':'large'}
    ios_source=subjects['ios']['files'][0]
    domain={
        'version':1,'approved_by':'shape-reviewer','approved_at_utc':now,
        'scope':SCOPE,
        'binds':{
            'design_lock_sha256':public['ios']['design_lock']['canonical_sha256'],
            'plan_canonical_sha256':public['ios']['plan']['canonical_sha256'],
            'policy_canonical_sha256':public['ios']['policy']['canonical_sha256'],
            'routes_canonical_sha256':public['ios']['routes']['canonical_sha256'],
            'environment_ios_canonical_sha256':public['ios']['environment']['canonical_sha256'],
            'required_native_assertions':len(plan['assertions']),
            'selected_state_ids':[s['id'] for s in plan['states']],
            'full_content_state_ids':[s['id'] for s in plan['states'] if s.get('coverage')=='full_content']
        },
        'actual_subject_binding':{'component_subject':'production_api','bridge_subject':'thin_bridge'},
        'common_host_shape':shape,'common_host_shape_sha256':shape_sha,
        'geometry_encoding':encoding,'geometry_encoding_sha256':encoding_sha,
        'platforms':{'ios':{
            'component_install_path':swift_rel,'module':'AlertToast','product':'AlertToast',
            'component_symbol':component,'input_symbol':c['input'],
            'exact_bridge':{'path':public['ios']['bridge']['path'],'sha256':public['ios']['bridge']['file_sha256']},
            'approved_component_revisions':{'initial':{'sha256':ios_source['sha256'],'bytes':ios_source['bytes']}}
        }},
        'approved_inputs':{f'public-{family}-ios':{
            'platform':'ios','fixture_canonical_sha256':public['ios']['fixtures']['canonical_sha256'],
            'fixture_file_sha256':public['ios']['fixtures']['file_sha256'],
            'launch_bridge_sha256':public['ios']['bridge']['file_sha256']
        }}
    }
    domain_ref=save(f'{task}-public-ios-coverage-domain.json',domain)
    policy_value=copy.deepcopy(domain)
    policy_value.pop('approved_at_utc');policy_value.pop('approved_by')
    policy_value['platforms']['ios'].pop('approved_component_revisions')
    report={
        'version':1,'task':task,'public_family':family,'reviewer_registry_id':'shape-reviewer',
        'decision':'admit_exact_initial_source_shape_only','scope':SCOPE,
        'public_packet':public,'coverage_domain_ref':domain_ref,'coverage_policy_sha256':digest(policy_value),
        'common_host_source_conformance_ref':provider_ref,
        'initial_source_seal':{'path':str(source_seal_path),'file_sha256':readset[source_seal_path.resolve()]['sha256']},
        'production_sources':subjects,
        'public_api_shape':{'immutable_input_fields_and_entry_callback_signatures':'matching_public_API',
            'callback_transport':'same (String) -> Void / (String) -> Unit passed by the fixed bridge',
            'integer_transport':'Shared public schema signed Int32 domain; Swift Int and Kotlin Int declarations match; universal arithmetic safety unassessed'},
        'source_findings':{
            'eager_main_vertical_root':{'ios':{'line':c['swift_root'],'kind':'VStack'},'android':{'line':c['kotlin_root'],'kind':'Column'}},
            'all_custom_reachable_source_in_enumerated_production_file':True,
            'only_fixed_two_case_choice_iterations_and_finite_input_text_operations':True,
            'host_owns_scroll_and_terminal':True,
            'no_lazy_internal_scroll_external_live_async_or_occluding_business_surface_found':True,
            'reconciliation':'Deterministic local parameter reconciliation only; admitted without judging its business result.',
            'event_call_shape':{'ios_line':c['swift_callback_line'],'android_line':c['kotlin_callback_line'],'kind':'direct synchronous onEvent call before local recorded-state assignment; event correctness and actual native delivery unassessed'},
            'native_text_growth_styles_and_controls':'Native text and Button source paths are finite; source modifiers are not claimed as measured fonts, colors, sizes, hit areas or behavior passes.'
        },
        'closure':{'ios':c['swift_closure'],'android':c['kotlin_closure']},
        'thin_bridge':{
            'ios':'Exact supplied make(fixture:[String:Any],onEvent:@escaping(String)->Void)->AnyView imports AlertToast, constructs immutable input and directly returns the exported component with the same callback.',
            'android':'Exact supplied org.nativeobserver.ObserverBridge.Content(JsonObject,(String)->Unit) imports the actual production package, uses schema primitive/list accessors and ContrastAwareReplyTheme(darkTheme=false,dynamicColor=false), and directly calls the production component with the same callback.',
            'no_custom_UI_state_decision_effect_or_identity_reset':True
        },
        'production_placement':{
            'ios':'Actual additive Sources/AlertToast file is in the default source directory of existing AlertToast target exported by the AlertToast library; Package.swift retains iOS 14 minimum.',
            'android':'Actual additive file is under app/src/main/java/com/example/reply/ui/components/business and declares/imports that production package.',
            'compile_actions':'Unassessed: original native compiler proof is required later by coverage_domain.complete.',
            'actual_acquisition_config_and_intended_platform_guard':'Collector must bind these same subjects and original intended-platform packet and run the mandatory intended-platform guard before acquisition; no acquisition config was asserted here.'
        },
        'source_duty_scope':{'production_api':'API and closed source SHAPE only','thin_bridge':'exact fixed source ABI/import/call shape only','production_placement':'source/module placement only'},
        'business_correctness':'unassessed','expected_outcomes':'unassessed','style_correctness':'unassessed',
        'native_or_runtime_evidence':'unassessed','behavior_pass_claimed':False,
        'android_coverage_domain_ref_issued':False,
        'future_revision_rule':'Only this single initial SHA and byte count are approved. Future changes require a controller request plus independent V4/V2-ADMISSION response and operator provenance; append exact revisions with unchanged policy only. No wildcard or future SHA approval.'
    }
    if task=='T3':
        report['closure']['android_stock_resource_reference']={'line':293,'symbol':'R.drawable.ic_check','scope':'Framework painterResource reference to a stock local decorative resource; no additional custom source/business branch. Artwork and pixels unassessed; resource contents not opened.'}
    report_ref=save(f'{task}-initial-source-shape-review.json',report)
    reports.append({'task':task,'coverage_domain_ref':domain_ref,'coverage_policy_sha256':digest(policy_value),'source_review_ref':report_ref})
    for arm in ['A','B']:
        actual=next(v for v in subjects['ios']['files'] if v['arm']==arm)
        config=copy.deepcopy(profile)
        config['purpose']='actual_initial_source_shape_binding_only_not_native_execution'
        config['source_roots']=[str(Path(actual['project'])/'Sources')]
        config['evidence_subjects']={
            'production_api':[actual['path']],
            'thin_bridge':[public['ios']['bridge']['path']],
            'production_placement':[str(Path(actual['project'])/'Package.swift')]
        }
        config['native_options']={'package':actual['project'],'product':'AlertToast'}
        config['coverage_domain_ref']=domain_ref
        config['coverage_provider_ref']=provider_ref
        config['source_review_store']=str(OUT/f'{task}-{arm}-uncreated-source-review-store')
        config['review_store']=str(OUT/f'{task}-{arm}-uncreated-visual-review-store')
        config_ref=save(f'{task}-{arm}-ios-source-binding.json',config)
        configs.append({'task':task,'arm':arm,'config':config,'config_ref':config_ref,'plan':plan})

# Exercise only the exact prepare/pinned/policy/sha function bodies from the
# permitted source. Do not import design_contract.py or any non-permitted file.
# The local JSON adapter is the canonical hash/load operation independently
# checked above against original design, fixture, plan and encoding pins.
checks=[]
for frozen_arm in ARM_NAMES:
    script_path=R/frozen_arm/'scripts/coverage_domain.py'
    script=read(script_path,'Exact unchanged coverage_domain.prepare compatibility check; no SDK or other imports').decode()
    parsed=ast.parse(script)
    keep=[node for node in parsed.body if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in {'DomainReviewRequired','sha','pinned','policy','prepare'}]
    pure=ast.Module(body=keep,type_ignores=[])
    namespace={'__file__':str(script_path),'Path':Path,'hashlib':hashlib,'copy':copy,
        'SUPPORTED_ENCODING_SHA256':encoding_sha,
        'd':SimpleNamespace(load=lambda p:json.loads(Path(p).read_bytes()),digest=digest)}
    exec(compile(pure,str(script_path),'exec'),namespace)
    for item in configs:
        lock=json.loads(Path(item['config']['design_lock']).read_bytes())
        value=namespace['prepare'](item['config'],item['plan'],lock)
        assert value['revision']=='initial' and value['platform']=='ios'
        checks.append({'task':item['task'],'source_arm':item['arm'],'frozen_tool_arm':frozen_arm,
            'status':'prepare_accepted_exact_source_shape_binding',
            'approval_sha256':value['approval_sha256'],'policy_sha256':value['policy_sha256'],
            'provider_sha256':value['provider_sha256'],'component_sha256':value['component']['sha256']})
save('PREPARE-COMPATIBILITY.json',{
    'version':1,'scope':'Exact unchanged prepare function bodies plus local canonical JSON adapter only; no complete(), CLI profile guard, SDK, native execution or runtime evidence.',
    'status':'accepted_12_exact_combinations','checks':checks,
    'dependency_boundary':'No import of design_contract.py or any file outside the explicitly permitted readset.'})
save('READSET.json',{
    'version':1,'reviewer_registry_id':'shape-reviewer','scope':SCOPE,
    'canonical_json':'UTF-8 JSON, sort_keys=True, separators=(comma,colon), ensure_ascii=False; independently matched public pins and fixed encoding.',
    'files':sorted(readset.values(),key=lambda v:v['path']),
    'discovery_only':'Path-only rg --files discovery in the three permitted public task families, T1-T3 sealed roots and actual workspaces resolved exact allowed files; no other source contents were opened.',
    'incidental_metadata':'Permitted SEAL.json manifests carry compile-result reference/hash metadata; the referenced result files were not opened or used as outcome evidence.',
    'not_read':['private packets','drafts','old cases or old production source','qualification or provider-conformance metadata','native screenshots/results','performance results','other source-reviewer judgments','T4/T5 source seals or production files'],
    'not_executed':['SDK/native/render/build','Git writes','source repairs','business-output oracle','intended-platform admission script outside allowed readset']})
save('INDEX.json',{
    'version':1,'reviewer_registry_id':'shape-reviewer','issued_at_utc':now,
    'scope':SCOPE,'decision':'admit_exact_T1_T2_T3_initial_public_source_shapes_only',
    'common_host_shape_ref':shape_ref,'common_host_source_conformance_ref':provider_ref,
    'geometry_encoding_canonical_sha256':encoding_sha,'approvals':reports,
    'source_binding_configs':[{'task':v['task'],'arm':v['arm'],'ref':v['config_ref']}for v in configs],
    'native_assertion_denominator_each':298,'native_runtime_or_behavior_passes_supplied':0,
    'artifact_pins':dict(issued),
    'operator_provenance':{'registry_id':'shape-reviewer','authority':'Controller-scoped independent initial source-shape reviewer','method':'Manual exact source/bridge/host review; independent byte/hash checks; exact prepare-only compatibility check','SDK_or_native_execution':False},
    'future_requests':'Await controller notification for T4/T5 or exact V4/V2-ADMISSION source revisions; no future or hidden approval issued.'})
save('APPROVAL-SEAL.json',{
    'version':1,'reviewer_registry_id':'shape-reviewer','scope':SCOPE,
    'decision':'admit_exact_T1_T2_T3_initial_public_source_shapes_only',
    'index_ref':{'path':str(OUT/'INDEX.json'),'sha256':issued['INDEX.json']['canonical_sha256']},
    'readset_ref':{'path':str(OUT/'READSET.json'),'sha256':issued['READSET.json']['canonical_sha256']},
    'artifacts':dict(issued),'no_native_or_behavior_P_supplied':True})
print(json.dumps({'output':str(OUT),'common_host_shape_sha256':shape_sha,
    'provider_ref':provider_ref,'approvals':reports,
    'readset_canonical_sha256':issued['READSET.json']['canonical_sha256'],
    'seal_canonical_sha256':issued['APPROVAL-SEAL.json']['canonical_sha256'],
    'prepare_checks':len(checks)},indent=2))
