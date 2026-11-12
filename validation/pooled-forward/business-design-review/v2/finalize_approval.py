from pathlib import Path
import json,hashlib,copy,importlib.util,sys
BASE=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward');ROOT=BASE/'business-design-v2';OLD=BASE/'business-design';OUT=BASE/'business-design-review/v2';TOOL=BASE/'candidate-v13.9/scripts'
def load(p):return json.loads(p.read_text())
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(canon(v)).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
expectedseal='3c45e454ee7f433ed64668f47e603372f97d121b88f4d1726ffc52ce6a53b103'
assert sha(ROOT/'SEAL.sha256')==expectedseal
for root in [ROOT,OLD]:
 for l in (root/'SEAL.sha256').read_text().splitlines():
  h,n=l.split('  ',1);assert sha(root/n)==h
assert sha(BASE/'business-design-review/REJECTION-SEAL.json')=='65e3aa38510fab4e54395a63f4bc6ce5f69720a8af7dcc888b96857e8098ddf8'
runs=load(OUT/'pure-run-log.json');comparisons=load(OUT/'rebuild-comparison.json');audit=load(OUT/'equivalence-schema-projection-audit.json')
assert all(r['success']for r in runs)and len(runs)==140
assert all(r['canonical_equal']for r in comparisons)and len(comparisons)==160
assert audit['status']=='PASS'and audit['compiled_assessed_assertions']==11788
# Representative mutations exercise the tiny common admission implementation without changing author files.
scripts=[ROOT/f'T{t}/{phase}/admit_profile.py'for t in range(1,6)for phase in ['public','private']]
assert len({sha(p)for p in scripts})==1
spec=importlib.util.spec_from_file_location('design_admission_public',scripts[0]);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
f=ROOT/'T1/public';a=load(f/'PROFILE-APPROVAL.json');config=load(f/'ios/admission-config.json');negative=[]
for name,field,value in [('wrong_lock_digest','design_sha256','0'*64),('wrong_policy_digest','policy_sha256','0'*64),('wrong_routes_digest','routes_sha256','0'*64),('wrong_environment_digest','environment_sha256','0'*64),('cross_platform_plan_path','plan',str(f/'android/generated/plan.json')),('cross_platform_bridge_path','bridge',str(f/'android/ObserverBridge.kt')),('wrong_launch_ref','launch_ref',{'source':'launch','pointer':'/android'})]:
 c=copy.deepcopy(config);c[field]=value;dump(OUT/(name+'.rejected-config.json'),c)
 try:module.verify(f,a,digest(a),'ios',c)
 except ValueError as e:negative.append({'case':name,'rejected':True,'reason':str(e)})
 else:negative.append({'case':name,'rejected':False})
try:module.verify(f,a,'0'*64,'ios',config)
except ValueError as e:negative.append({'case':'wrong_external_approval_digest','rejected':True,'reason':str(e)})
else:negative.append({'case':'wrong_external_approval_digest','rejected':False})
assert all(r['rejected']for r in negative);dump(OUT/'admission-mutation-rejections.json',negative)
entries={}
for t in range(1,6):
 for phase in ['public','private']:
  family=ROOT/f'T{t}'/phase;approval=load(family/'PROFILE-APPROVAL.json')
  for platform in ['ios','android']:
   key=f'T{t}/{phase}/{platform}';src=family/platform;rebuild=OUT/key;profile=approval['profiles'][platform];plan=load(src/'generated/plan.json');execution=load(src/'execution/execution.json');projection=load(src/'projection-map.json')
   originals={}
   for name in ['contract.json','reference.json','lock.json','policy.json','routes.json','environment.json','fixtures.json','bindings.json','actions.json','generated/plan.json','generated/actions.json','catalog.json','route-audit.json','execution/execution.json','execution/actions.json','execution/fixtures.json','projection-map.json','admission-config.json','ObserverBridge.swift'if platform=='ios'else'ObserverBridge.kt']:
    p=src/name;originals[name]={'path':str(p),'file_sha256':sha(p),**({'canonical_sha256':digest(load(p))}if p.suffix=='.json'else{})}
   entries[key]={'task':f'T{t}','family':phase,'platform':platform,'scenario':plan['design_contract']['scenario'],'design_sha256':profile['design_sha256'],'policy_sha256':profile['policy_sha256'],'routes_sha256':profile['routes_sha256'],'environment_sha256':profile['environment_sha256'],'plan_sha256':digest(plan),'execution_sha256':execution['execution_sha256'],'master_denominator':{'path':str(family/'denominator.json'),'file_sha256':sha(family/'denominator.json'),'canonical_sha256':digest(load(family/'denominator.json'))},'source_inputs':originals,'independent_rebuild':{'directory':str(rebuild),'all_eight_artifacts_canonical_equal':True},'profile_admission':{'script':str(family/'admit_profile.py'),'script_file_sha256':sha(family/'admit_profile.py'),'root':str(family),'approval':str(family/'PROFILE-APPROVAL.json'),'approval_file_sha256':sha(family/'PROFILE-APPROVAL.json'),'approval_sha256':digest(approval),'config':str(src/'admission-config.json'),'intended_platform':platform},'schema_only_opposite_slots':'Not approved for runtime use; exact profile admission is mandatory.','source_domain_status':'PENDING_ACTUAL_BUILDER_SOURCE_AND_COMPILE'}
dump(OUT/'GENERATED-READY-ENTRIES.json',{'version':1,'design_file_seal_sha256':expectedseal,'entries':entries})
rs=load(OUT/'READSET.json');seen={e['path']for e in rs}
for p in [TOOL/'design_contract.py',TOOL/'native_checks.py',TOOL/'review_contract.py',TOOL/'requirement_routes.py',TOOL/'execution_plan.py',TOOL/'action_guard.py',TOOL/'observation_contract.py']:
 if str(p)not in seen:rs.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'operation':'frozen-pure-generator-read'})
dump(OUT/'READSET.json',rs)
record={'version':2,'status':'APPROVED_DESIGN_FORMAT','owner':'Independent design/format reviewer /root/v13_design_admission','all_five_tasks_approved':True,'first_initial_UI_source_generation_authorized':True,'design_file_seal':{'path':str(ROOT/'SEAL.sha256'),'sha256':expectedseal,'listed_files':821,'all_hashes_verified_before_and_after':True},'original_rejection':{'path':str(BASE/'business-design-review/REJECTION-SEAL.json'),'file_sha256':'65e3aa38510fab4e54395a63f4bc6ce5f69720a8af7dcc888b96857e8098ddf8','original_design_seal_sha256':'6e82784fde88cb617d1e68ee5cac6dab8514eeddd526eb77a95c34f3040dbd60','original270_bytes_unchanged':True},'approved_tasks':[f'T{t}'for t in range(1,6)],'approved_profiles':list(entries),'generated_ready_entries':{'path':str(OUT/'GENERATED-READY-ENTRIES.json'),'file_sha256':sha(OUT/'GENERATED-READY-ENTRIES.json'),'count':20},'independent_validation':{'positive_pure_cli_runs':120,'expected_wrong_platform_rejections':20,'additional_common_guard_mutation_rejections':len(negative),'rebuilt_artifacts_matching':160,'standard_fixture_schema_payloads':60,'validator':'jsonschema4.23.0 Draft202012Validator from private pure-only dependency path','full_master_denominator_cells':13358,'compiled_assessed_assertions':11788,'explicit_NA_cells':1570,'normative_equivalence':'Verified directly against preserved originals after only initial→start state-ID rename and number→scalar dimensionless unit metadata; all fixtures/bridges/API/schema/SVG/environment/bindings/pixel policy bytes unchanged.','business_oracle':'Every public/private state sequence was independently inspected against identical published business rules in original review; exact outcomes and typed reference business state remain unchanged in v2.','source_partition':'Exact source documents/raw UTF8 and source file hashes checked in every projected lock; no tested hidden-only fixture strings in any public subtree, including embedded locks.','atomic_scope':'Every original assessed cell maps to exactly one generated assertion with unchanged expected value/unit/operator/source pointer. Exact primitive Boolean questions and pixel sampling unchanged; coarse frozen aspect labels add no measurement capability.','actions':'Counts17–25, maxindex24. Guarded original taps/replacements and earlier stimulus indices retained; callback predicates require actual successful native dispatch and exact method.','absence_scope':'Existing native absence assertions require actual full-content acquisition. T4 target checkpoints are promoted by frozen planner; absence targets are not required presences. Collector paths support these full sweeps and preserve unavailable target facts without quiet callback or pass credit.','ios_style':'No generic computed SwiftUI font/padding/layout-box or physical touch-area claim. Android native typography remains assessed; iOS source-bound qualitative propositions remain distinct.'},'runtime_admission_requirement':{'mandatory':True,'rule':'Before every SDK/default-service native action, invoke the pinned public admission helper on the same exact active config consumed by the runner; derive platform from its bound plan and require actual native runner platform to match. Retain exact config bytes/hash, script+approval identities and admitted receipt. Opposite schema-only expressions never grant runtime approval.','shared_helper_integration':'Coordinator implementing same-config admission hook identically for all study arms; this review grants no frozen-tool applicability capability or treatment credit.'},'source_domain':{'status':'PENDING_ACTUAL_SOURCE','rubric_path':str(BASE/'business-design-review/SOURCE-DOMAIN-RUBRIC.json'),'rubric_file_sha256':sha(BASE/'business-design-review/SOURCE-DOMAIN-RUBRIC.json'),'approval':None,'required_later':'Independent production-source/API/placement and exact thin-bridge review, finite eager vertical-flow domain, exact shared provider/host+actual native compile log/compiled bytes. Public and hidden each need matching design-lock/plan domain records later.'},'scope':'Design/format admission for additive finite reusable-component authoring only. No implementation correctness, native execution, screenshot quality, source approval or runtime coverage is certified. Required U/N/A rows and missing native evidence may never be waived.','private_embargo':'Implementation workers receive only T*/public/. This approval/review folder and private namespace entries remain coordinator/reviewer-only until required all10finalproduction-source/selfclaim seals.','readset':{'path':str(OUT/'READSET.json'),'file_sha256':sha(OUT/'READSET.json')},'audit_outputs':{'pure_runs':'pure-run-log.json','rebuilds':'rebuild-comparison.json','equivalence_schema_projection':'equivalence-schema-projection-audit.json','guard_rejections':'admission-mutation-rejections.json'},'failed_new_runs':0}
dump(OUT/'APPROVAL-SEAL.json',record)
text='''# Independent v2 design/format approval

**Approved all five tasks and20 intended-platform public/private profiles for initial source generation.**

Pinned author file seal: `3c45e454ee7f433ed64668f47e603372f97d121b88f4d1726ffc52ce6a53b103`. All821 listed files match. The original rejected design and rejection record remain unchanged.

Independent regeneration passed120 pure CLI calls,20 expected wrong-platform rejections and8 additional admission mutations. All160 rebuilt artifacts match the sealed originals. Standard jsonschema4.23.0 validation passed60fixture payloads. Every13,358 master denominator cell remains explicit:11,788 generated assessed assertions and1,570 N/A cells. Direct comparison confirms unchanged business rules/outcomes/fixture and bridge bytes/API/schema/SVGs, numeric values, qualitative propositions, sampling, tolerances and selected state coverage.

The four original format blockers are resolved through separate intended-platform rule universes and locked admission, supported scalar units, a nonreserved start checkpoint, and truthful coarse visual taxonomy while retaining separate primitive questions. Every mandatory Android native style atom remains; iOS unsupported computed typography/padding is not fabricated.

GENERATED-READY-ENTRIES.json pins every original input, lock, plan, catalog, policy, routes, environment, bridge and execution artifact, with both canonical-object and exact file hashes where relevant. The public admission helper must consume the same active config as the native runner before SDK actions. Its schema-only opposite expression slots authorize no runtime facts.

Actual production-source review, finite eager vertical-flow domain approval, exact provider/host and real native compilation remain pending until builder output exists. This design approval certifies no runtime pass or native coverage. Public/private locks need their own matching source domains later. Existing absence checks still require real full sweeps; incomplete evidence remains U. No SDK/native renderer or production implementation was used in this review.

This folder and its private profile entries are embargoed from implementation workers. Workers receive only the applicable public design subtree.
'''
(OUT/'REVIEW.md').write_text(text)
print(json.dumps({'approval_path':str(OUT/'APPROVAL-SEAL.json'),'approval_file_sha256':sha(OUT/'APPROVAL-SEAL.json'),'ready_entries_path':str(OUT/'GENERATED-READY-ENTRIES.json'),'ready_entries_file_sha256':sha(OUT/'GENERATED-READY-ENTRIES.json'),'approved_tasks':5,'approved_profiles':len(entries),'source_domain':'PENDING_ACTUAL_SOURCE'},indent=2))
