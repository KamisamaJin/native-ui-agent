"""Append independently reviewed T4/T5 initial artifacts; leave T1-T3 immutable.

The reviewer-owned initial issuer is reused solely for identical metadata binding
and prepare-only checks, after manual complete inspection of newly sealed sources.
This imports no repository helper and performs no SDK/native/build work.
"""
import ast
import copy
import datetime
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward')
OUT=Path(__file__).resolve().parent
FIRST=R/'business-source-review-cohort2/initial-public'
DESIGN=R/'business-design-cohort2-v2'
DESIGN_REVIEW=R/'business-design-cohort2-review/revision-v2'
ARM_NAMES=['candidate-v13.9','baseline-v12.6-common-6']
readset={}
issued={}

# Reuse only this reviewer's own pure JSON/readset/exclusive-write helpers and
# the binding loop. Do not import or execute the original issuer as a module.
original=(FIRST/'issue_initial_approvals.py').read_text()
tree=ast.parse(original)
helpers=[node for node in tree.body if isinstance(node,ast.FunctionDef)
         and node.name in {'digest','read','load','save','description'}]
exec(compile(ast.Module(body=helpers,type_ignores=[]),str(FIRST/'issue_initial_approvals.py'),'exec'),globals())
read(FIRST/'issue_initial_approvals.py','Reviewer-owned metadata issuer reuse; not product or oracle code')
SCOPE=('Independent finite eager main-vertical source-shape, actual public bridge call/import, '
       'production placement and shared host SOURCE conformance only. No business correctness, '
       'expected-outcome, design-style, native dispatch, build, runtime, pixel, coverage or behavior P verdict.')
now=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
entry=load(DESIGN_REVIEW/'PUBLIC-READY-ENTRY-MAP.json','Original permitted public design/API/bridge identity')
design_seal=load(DESIGN_REVIEW/'APPROVAL-SEAL.json','Original permitted public design seal identity only')
read(DESIGN_REVIEW/'SOURCE-REVIEW-RUBRIC.md','Original permitted finite source-shape rubric')
assert readset[(DESIGN_REVIEW/'PUBLIC-READY-ENTRY-MAP.json').resolve()]['sha256']==design_seal['artifacts']['PUBLIC-READY-ENTRY-MAP.json']
shape=load(FIRST/'common-host-shape.json','Reuse this reviewer\'s unchanged generic finite component host shape')
shape_sha=digest(shape)
provider=load(FIRST/'common-host-source-conformance.json','Reuse this reviewer\'s immutable common host SOURCE record only')
provider_ref={'path':str(FIRST/'common-host-source-conformance.json'),'sha256':digest(provider)}
assert provider_ref['sha256']=='941bdf2676229a642cfe3f2b02ee131fa68f8be042d43fea66d9cf18db35fc8a'
assert shape_sha=='c7fbe68e0282ea56605c3c2708fc67e15607537c8fe673ff777da6e1705bee18'
assert provider['common_host_shape_sha256']==shape_sha
encoding=load(R/ARM_NAMES[0]/'assets/ios-observer/geometry-encoding.json','Exact unchanged supported geometry asset')
encoding_sha=digest(encoding)
assert encoding_sha=='aa335ed5809a23b048a20a7d0c0f86d51bad2d936b2c21d1ae736d8ff8995a84'
for rel,expected in provider['files'].items():
    for frozen_arm in ARM_NAMES:
        assert hashlib.sha256(read(R/frozen_arm/rel,'Confirm unchanged shared host source bytes already fully reviewed')).hexdigest()==expected

CASES=[
    {'task':'T4','family':'visitor-preclearance','component':'VisitorAccessPreclearance',
     'input':'VisitorAccessInput','swift_root':188,'kotlin_root':164,
     'swift_closure':[
         description('VisitorAccessInput',3,47,'immutable public input including two Bool fields'),
         description('VisitorAccessArea / VisitorAccessCredential',49,93,'two-case local enums and pure predicates'),
         description('VisitorAccessSelection',95,152,'local state and pure reconciliation/text predicates'),
         description('VisitorAccessColors / VisitorAccessButtonStyle',154,171,'local constants and identity label style'),
         description('VisitorAccessPreclearance',174,353,'public View with all reachable custom helpers and handlers'),
         description('contentText / sectionText / choiceButton / primaryButton',235,319,'finite native view helpers'),
         description('choose(area) / choose(credential) / toggleConfirmation / record',321,352,'synchronous local action handlers')],
     'kotlin_closure':[
         description('VisitorAccessInput',40,54,'immutable public input including two Boolean fields'),
         description('VisitorAccessArea / VisitorAccessCredential',56,81,'two-case local enums and pure predicates'),
         description('VisitorAccessSelection',83,120,'local state and pure reconciliation/text predicates'),
         description('VisitorAccessColors / VisitorBodyStyle / VisitorSectionStyle / VisitorTitleStyle',122,155,'local constants'),
         description('VisitorAccessPreclearance',157,254,'public composable and all inline synchronous handlers'),
         description('VisitorContentText / VisitorChoiceButton',256,321,'finite native view helpers')],
     'swift_callback_line':349,'kotlin_callback_line':229},
    {'task':'T5','family':'candidate-disposition','component':'CandidateDispositionReview',
     'input':'CandidateDispositionInput','swift_root':178,'kotlin_root':153,
     'swift_closure':[
         description('CandidateDispositionInput',3,44,'immutable public input including Bool field'),
         description('CandidateDispositionRoot / CandidateDispositionDetail',46,95,'two-root/four-detail local enums and pure predicates'),
         description('CandidateDispositionState',97,151,'local state and pure reconciliation/text predicates'),
         description('CandidateDispositionColors',153,162,'local constants'),
         description('CandidateDispositionReview',165,331,'public View with all reachable custom helpers and handlers'),
         description('rootSection / detailSection / contentText / choiceButton / primaryButton',213,294,'finite native view helpers'),
         description('choose(root) / choose(detail) / toggleConfirmation / record',296,330,'synchronous local action handlers')],
     'kotlin_closure':[
         description('CandidateDispositionInput',35,48,'immutable public input including Boolean field'),
         description('CandidateDispositionRoot / CandidateDispositionDetail',50,75,'two-root/four-detail local enums and pure predicates'),
         description('CandidateDispositionState',77,118,'local state and pure reconciliation/text predicates'),
         description('CandidateDispositionColors / candidateDispositionBodyStyle / candidateDispositionSectionStyle / candidateDispositionTitleStyle',120,144,'local constants'),
         description('CandidateDispositionReview',146,237,'public composable and all inline synchronous handlers'),
         description('CandidateDispositionText / CandidateDispositionChoice',239,307,'finite native view helpers')],
     'swift_callback_line':327,'kotlin_callback_line':213}
]
for case,seal_sha in zip(CASES,[
    'cc236f262f99616189a24b7444a6d48890c2949c948d43bc7c58bcc963e990b1',
    '6c97eda613d2462f9f8ce4a7e6724170517e6718e0457072d26edb6aa18dadc4']):
    seal_path=R/f"cache/business/initial/{case['task']}/source-seal/SEAL.json"
    assert hashlib.sha256(read(seal_path,'Newly controller-authorized exact initial source seal')).hexdigest()==seal_sha

reports=[]
configs=[]
binding_loop=next(node for node in tree.body if isinstance(node,ast.For)
                  and isinstance(node.target,ast.Name) and node.target.id=='c')
loop_source=ast.unparse(binding_loop)
# Public portfolioScore's maximum100 narrows the shared signed Int32 bound.
# This is reviewer metadata validation only; no source or oracle is changed.
loop_source=loop_source.replace("assert value.get('maximum') == 2147483647",
                                "assert value.get('maximum') <= 2147483647")
loop_source=loop_source.replace('only_fixed_two_case_choice_iterations_and_finite_input_text_operations',
                                'only_fixed_finite_enum_choice_iterations_and_finite_input_text_operations')
loop_source=loop_source.replace("if task == 'T3':", "if task == 'T4':")
loop_source=loop_source.replace("'line': 293", "'line': 313")
exec(compile(loop_source,str(__file__),'exec'),globals())

# Reuse the exact unchanged prepare-function-only check from our initial issuer.
start=next(i for i,node in enumerate(tree.body) if isinstance(node,ast.Assign)
           and any(isinstance(t,ast.Name) and t.id=='checks' for t in node.targets))
check_nodes=[]
for node in tree.body[start:]:
    if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='save':
        break
    check_nodes.append(node)
exec(compile(ast.Module(body=check_nodes,type_ignores=[]),str(__file__),'exec'),globals())
assert len(checks)==8
save('PREPARE-COMPATIBILITY.json',{
    'version':1,'status':'accepted_8_exact_combinations','checks':checks,
    'scope':'Exact unchanged prepare function bodies plus local canonical JSON adapter only; no complete(), CLI admission guard, SDK, build or runtime evidence.',
    'dependency_boundary':'No import of repository design_contract.py or other source outside the permitted readset.'})
save('READSET.json',{
    'version':1,'reviewer_registry_id':'shape-reviewer','scope':SCOPE,
    'controller_authorization':'T4 source-seal and exact actual source newly authorized first, then T5 source-seal and exact actual source authorized after controller sealed notice; source reads began after those messages.',
    'common_host_prior_review':{'readset':str(FIRST/'READSET.json'),'readset_canonical_sha256':'3e017fb8515fd43e2f7b8bf12af5f086e78487c812c28c5b26c72fdc59ed0e36','seal':str(FIRST/'APPROVAL-SEAL.json'),'seal_canonical_sha256':'b632098aa951927158c4964c717fa9e9c644c541c77860d89cbb9d0983279c48'},
    'files':sorted(readset.values(),key=lambda v:v['path']),
    'incidental_metadata':'Permitted source-seal manifests contain compile-result reference/hash metadata; referenced results were not opened or used as native outcome evidence.',
    'not_read':['private packets','drafts','old cases or production sources','qualification/native/performance results','other source-reviewer judgments'],
    'not_executed':['SDK/native/render/build','Git writes','source repairs','business-output oracle','intended-platform admission script outside allowed readset'],
    'public_design_mutations':0,'capture_adoption_policy_fields_added':0})
save('INDEX.json',{
    'version':1,'reviewer_registry_id':'shape-reviewer','issued_at_utc':now,
    'scope':SCOPE,'decision':'admit_exact_T4_T5_initial_public_source_shapes_only',
    'common_host_shape_ref':{'path':str(FIRST/'common-host-shape.json'),'sha256':shape_sha},
    'common_host_source_conformance_ref':provider_ref,
    'geometry_encoding_canonical_sha256':encoding_sha,'approvals':reports,
    'source_binding_configs':[{'task':v['task'],'arm':v['arm'],'ref':v['config_ref']} for v in configs],
    'native_assertion_denominators':{v['task']:len(v['plan']['assertions'])for v in configs},
    'native_runtime_or_behavior_passes_supplied':0,'original_T1_T2_T3_artifacts_modified':False,
    'public_design_mutations':0,'capture_adoption_policy_fields_added':0,
    'artifact_pins':dict(issued),
    'operator_provenance':{'registry_id':'shape-reviewer','authority':'Controller-scoped independent finite initial source-shape reviewer','method':'Complete manual source/bridge inspection; exact A/B seal/hash equality and prepare-only checks; same immutable common host record','SDK_or_native_execution':False},
    'future_requests':'Await controller requests for exact V4/V2-ADMISSION revisions; no hidden, wildcard or future-source approval.'})
save('APPROVAL-SEAL.json',{
    'version':1,'reviewer_registry_id':'shape-reviewer','decision':'admit_exact_T4_T5_initial_public_source_shapes_only','scope':SCOPE,
    'index_ref':{'path':str(OUT/'INDEX.json'),'sha256':issued['INDEX.json']['canonical_sha256']},
    'readset_ref':{'path':str(OUT/'READSET.json'),'sha256':issued['READSET.json']['canonical_sha256']},
    'artifacts':dict(issued),'no_native_or_behavior_P_supplied':True,
    'original_T1_T2_T3_artifacts_modified':False})
print(json.dumps({'output':str(OUT),'provider_ref':provider_ref,'approvals':reports,
    'readset_canonical_sha256':issued['READSET.json']['canonical_sha256'],
    'seal_canonical_sha256':issued['APPROVAL-SEAL.json']['canonical_sha256'],
    'prepare_checks':len(checks)},indent=2))
