"""Mechanical original-byte source-contract supplement packaging; no grading.

The same fixed per-case selection serves all source versions. No judge output,
version map, current business component, SUT, SDK or new source approval is used.
Anonymous content consists only of original raw files and a relative file list.
"""
import datetime
import hashlib
import json
from pathlib import Path

R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward')
D=R/'business-design-cohort2-v2'
OUT=Path(__file__).resolve().parent
PUBLIC_ROOT_FILES={'API.md','BRIEF.md','DESIGN.md','INPUT-DOMAIN.md','REQUIREMENT-MAP.json',
    'fixture.schema.json','flow.json','outcomes.json','reference-blank.svg','reference-long.svg','reference-ready.svg','tokens.json'}
PRIVATE_ROOT_FILES={'PRIVATE-INPUTS.md','flow.json','outcomes.json'}
PLATFORM_FILES={'actions.json','bindings.json','catalog.json','contract.json','denominator.json',
    'environment.json','fixtures.json','launch.json','lock.json','policy.json','reference.json','routes.json'}
PLATFORM_METADATA={'profile.json','responsibility-capability.json','route-audit.json'}
EXPECTED_SETUP='9dc3f574c26aad205644e6356baa1f5d6e6c78ffd30e424cc22b20d6e7a7bb21'
EXPECTED_PREPARATION='f211b669e7be47121346afd1c0baadb4375210de4e45e7939b3b3f51676b1fab'
EXPECTED_INVENTORY='4f6d6e60331bcc58d17b30443b5f48fc1156636d82322ce7f678660e2e47d818'
EXPECTED_REVIEW_READSET='81f114aafcbbb3dabf7e8b133046839ab5168ca6e09fd26e8c4bf7e93724d325'
cache={}
readset={}
issues=[]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode())
def read(path,purpose):
    path=Path(path).resolve();key=str(path)
    if key not in cache:
        raw=path.read_bytes();cache[key]=raw
        readset[key]={'path':key,'sha256':sha(raw),'bytes':len(raw),'purposes':[purpose]}
    elif purpose not in readset[key]['purposes']:readset[key]['purposes'].append(purpose)
    return cache[key]
def load(path,purpose):return json.loads(read(path,purpose))
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    raw=value if isinstance(value,bytes)else(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    with path.open('xb')as f:f.write(raw)
    return sha(raw)
def ref(path):
    path=Path(path).resolve();raw=read(path,'Original pin/provenance metadata')
    return {'path':str(path),'sha256':sha(raw),'bytes':len(raw)}

author_path=R/'operators/cohort2/INITIAL-AUTHOR-ADMISSION.json'
preparation_path=R/'operators/cohort2/business-stock-preparation.json'
setup_path=R/'cache/hosts/setup.json'
approval_path=R/'business-design-cohort2-review/revision-v2/APPROVAL-SEAL.json'
review_readset_path=R/'business-design-cohort2-review/revision-v2/READSET.json'
inventory_path=D/'SEAL.sha256'
author=load(author_path,'Original pre-implementation case/source83 and design-admission provenance')
preparation=load(preparation_path,'Original pre-business stock83 copy/hash records')
setup=load(setup_path,'Original common stock Git/setup/host-patch pins')
approval=load(approval_path,'Original sealed design/readset artifact pins only')
review_readset=load(review_readset_path,'Original reviewer per-file raw identity pins only; no grades')
inventory_raw=read(inventory_path,'Original 2108-file unchanged design inventory')
assert sha(read(setup_path,'Original setup pin'))==EXPECTED_SETUP
assert sha(read(preparation_path,'Original pre-business preparation pin'))==EXPECTED_PREPARATION
assert sha(inventory_raw)==EXPECTED_INVENTORY
assert sha(read(review_readset_path,'Original reviewer raw readset pin'))==EXPECTED_REVIEW_READSET
assert approval['artifacts']['READSET.json']==EXPECTED_REVIEW_READSET
assert author['approval']['sha256']==sha(read(approval_path,'Original author-to-design approval link'))
assert author['design']['sha256']==EXPECTED_INVENTORY
inventory={}
for line in inventory_raw.decode().splitlines():
    expected,relative=line.split('  ',1)
    assert len(expected)==64 and relative not in inventory
    inventory[relative]=expected
assert len(inventory)==2108
review_pins={v['path']:v['sha256']for v in review_readset['all_input_bytes_identity_read']}
assert len(review_pins)==len(review_readset['all_input_bytes_identity_read'])
assert review_readset['inventory_file_count']==len(inventory)==2108
assert all(review_pins.get(str(D/relative))==expected for relative,expected in inventory.items())
assert review_readset['cohort_seal_sha256']==EXPECTED_INVENTORY

cases=author['cases']
assert len(cases)==5
stock_records={Path(v['workspace']).parts[-2]:v for v in preparation['records']}
stock_common=None
provenance_refs={
    'initial_author_admission':ref(author_path),'pre_business_stock_preparation':ref(preparation_path),
    'original_stock_setup':ref(setup_path),'original_design_approval_seal':ref(approval_path),
    'original_design_inventory':ref(inventory_path),'original_reviewer_readset':ref(review_readset_path)}
placement_specs=[('alerttoast/Package.swift','stock/ios/Package.swift'),
    ('reply/Reply/app/build.gradle.kts','stock/android/app/build.gradle.kts')]

# Fixed identity constraints cover experimental provenance, not normative OS,
# package/toolchain dependency versions, API signatures or business input fields.
identity_tokens=[b'/Users/',b'/private/tmp/',b'/var/folders/',b'candidate-v13',b'baseline-v12',
    b'v13.9',b'v12.6',b'business-tools-v4',b'run-cohort2',b'COHORT2-EXECUTION',
    b'SELF-SEAL',b'"self_claim"',b'"worker_tokens"',b'"resource_usage"',
    b'"api_version"',b'"arm"',b'"tool_api"',b'coverage_domain_ref']
plans=[]
for number,case in enumerate(cases,1):
    task=case['id'];family=case['design_task'];component=case['component']
    assert case['source_files_before_initial']==83 and case['initial_UI_implementation_exists']is False
    workspace=Path(case['initial_workspace'])
    stock_copy_path=workspace/'STOCK-COPY.json'
    stock_copy=load(stock_copy_path,'Original pre-business stock83 source-copy ledger')
    assert stock_copy==stock_records[task]
    assert stock_copy['stock_setup_sha256']==EXPECTED_SETUP
    assert stock_copy['source']==str(R/'cache/hosts')
    assert stock_copy['finished_at_unix']<author['at_unix']
    stock_files=stock_copy['stock_production_files']
    assert len(stock_files)==83
    if stock_common is None:stock_common=stock_files
    else:assert stock_files==stock_common
    public_pins={}
    public_pin_refs={}
    for arm in ['A','B']:
        p=R/f'cache/business/run-cohort2/arms/{task}/{arm}/public-inputs.json'
        public_pins[arm]=load(p,'Original sealed public-input file-byte pins; only task docs and stock placement entries consumed')
        public_pin_refs[arm]=ref(p)
    files=[]
    excluded=[]
    responsibility_records=[]
    def add(original,relative,kind,pins):
        raw=read(original,'Mechanical original-byte packaging: '+kind)
        expected_hashes=[]
        for pin in pins:
            expected_hashes.append(pin['sha256'])
            assert sha(raw)==pin['sha256'],str(original)
        for token in identity_tokens:
            if token.lower()in raw.lower():
                issues.append({'case':task,'original':str(original),'anonymous_relative':relative,
                    'kind':'original_identity_token_requires_operator_resolution','token':token.decode()})
        files.append({'original_path':str(Path(original).resolve()),'anonymous_relative':relative,
            'sha256':sha(raw),'bytes':len(raw),'kind':kind,'original_pins':pins})
    def design_add(path,relative,kind,visibility):
        key=str(path.relative_to(D));absolute=str(path.resolve())
        assert key in inventory and absolute in review_pins
        pins=[{'authority':'original_design_inventory','sha256':inventory[key]},
              {'authority':'original_independent_readset','sha256':review_pins[absolute]}]
        if visibility=='public':
            for arm in ['A','B']:
                assert absolute in public_pins[arm]
                pins.append({'authority':'original_public_inputs_'+arm,'sha256':public_pins[arm][absolute]})
        add(path,relative,kind,pins)
    for visibility,root_set in [('public',PUBLIC_ROOT_FILES),('private',PRIVATE_ROOT_FILES)]:
        base=D/visibility/'tasks'/family
        direct={p.name for p in base.iterdir()if p.is_file()}
        assert direct==root_set,(task,visibility,'Unexpected task-root file selection')
        for name in sorted(root_set):
            design_add(base/name,f'contracts/{visibility}/{name}','original_task_root_document',visibility)
        for platform,ext in [('ios','swift'),('android','kt')]:
            platform_base=base/platform
            selected=PLATFORM_FILES|{'ObserverBridge.'+ext}
            direct={p.name for p in platform_base.iterdir()if p.is_file()}
            assert direct==selected|PLATFORM_METADATA,(task,visibility,platform,'Unexpected platform direct inventory')
            for name in sorted(selected):
                design_add(platform_base/name,f'contracts/{visibility}/{platform}/{name}',
                    'original_platform_direct_source_contract',visibility)
            excluded.extend({'path':str(platform_base/name),'reason':'Uniform profile/preflight metadata exclusion'}for name in sorted(PLATFORM_METADATA))
            reference=load(platform_base/'reference.json','Mechanical original source-duty artifact/reference completeness only')
            duties=[v for v in reference['responsibilities']if v.get('method')=='source']
            assert {v['subject']for v in duties}=={'production_api','thin_bridge','production_placement'}
            responsibility_records.append({'visibility':visibility,'platform':platform,
                'original_reference_path':str(platform_base/'reference.json'),
                'source_responsibility_ids':[v['id']for v in duties],
                'source_subjects':[v['subject']for v in duties],
                'API_artifact':'contracts/public/API.md',
                'bridge_artifact':f'contracts/{visibility}/{platform}/ObserverBridge.{ext}',
                'stock_production_count':83,
                'placement_artifact':'stock/ios/Package.swift'if platform=='ios'else'stock/android/app/build.gradle.kts'})
    assert len(files)==67
    for namespace,expected in sorted(stock_files.items()):
        root_index,relative=namespace.split('/',1)
        root_index=int(root_index)
        assert root_index in [0,1]
        assert '/business/'not in namespace and component not in namespace
        original_root=(R/'cache/hosts/alerttoast/Sources')if root_index==0 else(R/'cache/hosts/reply/Reply/app/src/main')
        original=original_root/relative
        copied=Path(stock_copy['production_source_roots'][root_index])/relative
        assert sha(read(copied,'Original pre-business stock-copy body equality'))==expected
        assert read(copied,'Original stock equality')==read(original,'Original shared stock baseline raw source/resource')
        target=('stock/ios/Sources/'if root_index==0 else'stock/android/app/src/main/')+relative
        add(original,target,'pre_business_stock_production',[
            {'authority':'original_STOCK_COPY','sha256':expected},
            {'authority':'original_stock_preparation_record','sha256':stock_records[task]['stock_production_files'][namespace]}])
    for source_rel,target in placement_specs:
        original=R/'cache/hosts'/source_rel
        copy_path=workspace/source_rel
        assert read(original,'Original shared production placement')==read(copy_path,'Original initial stock production placement equality')
        pins=[]
        for arm in ['A','B']:
            recorded=str(R/f'cache/business/{task}/{arm}/workspace'/source_rel)
            assert recorded in public_pins[arm]
            pins.append({'authority':'original_public_inputs_'+arm,'sha256':public_pins[arm][recorded]})
        add(original,target,'original_stock_production_placement',pins)
    assert len(files)==152 and len({v['anonymous_relative']for v in files})==152
    plans.append({'task':task,'family':family,'case_id':f'case-{number:02d}','files':files,
        'public_input_pin_ledgers':public_pin_refs,'original_stock_copy':ref(stock_copy_path),
        'source_responsibility_artifact_inventory':responsibility_records,'excluded_metadata':excluded})

# One fixed-selection completeness/identity pass above, before writing any
# anonymous content. Identity-bearing original bytes are never rewritten.
if issues:
    save(OUT/'IDENTITY-ISSUES.json',{'version':1,'kind':'mechanical-packaging-identity-issues','issues':issues,
        'anonymous_content_written':False,'scope':'Original bytes preserved; no semantic or quality verdict.'})
    raise SystemExit('Original identity issue; no anonymous content emitted')

results=[]
for plan in plans:
    case_root=OUT/plan['case_id'];anonymous=case_root/'anonymous';operator=case_root/'operator'
    case_root.mkdir(exist_ok=False)
    for item in plan['files']:
        save(anonymous/item['anonymous_relative'],cache[item['original_path']])
    relative_files=sorted(v['anonymous_relative']for v in plan['files'])
    save(anonymous/'FILES.txt',('\n'.join(relative_files)+'\n').encode())
    ledger={
        'version':1,'kind':'mechanical-original-source-contract-supplement-ledger',
        'scope':'Mechanical raw artifact packaging only; no source-shape/product/behavior/quality approval.',
        'case_id':plan['case_id'],'task':plan['task'],'design_task':plan['family'],
        'shared_for_all_three_source_versions':True,
        'selection_rule':{'public_task_root_files':sorted(PUBLIC_ROOT_FILES),
            'private_task_root_files':sorted(PRIVATE_ROOT_FILES),
            'normative_platform_direct_files':sorted(PLATFORM_FILES),
            'bridge_extension_by_platform':{'ios':'swift','android':'kt'},
            'uniform_excluded_platform_metadata':sorted(PLATFORM_METADATA),
            'excluded_nested_material':['pure-subjects placeholders','generated/execution duplicates','preflight/tool metadata','drafts']},
        'original_pin_provenance':provenance_refs,
        'original_stock_copy':plan['original_stock_copy'],
        'public_input_pin_ledgers':plan['public_input_pin_ledgers'],
        'raw_files':plan['files'],'excluded_metadata':plan['excluded_metadata'],
        'original_source_responsibility_artifact_inventory':plan['source_responsibility_artifact_inventory'],
        'mechanical_counts':{'public_task_root':12,'private_task_root':3,'platform_direct':52,
            'pre_business_stock_production':83,'production_placement':2,'raw_files':152,'neutral_file_lists':1},
        'identity_scan':{'experimental_identity_tokens':[v.decode()for v in identity_tokens],'matches':[]},
        'unavailable_original_artifacts':[],'new_component_used_as_stock_baseline':False,
        'judge_outputs_or_version_maps_read':False,'source_SUT_SDK_or_oracle_edits':False,
        'grader_content':'Only anonymous/ raw byte copies and FILES.txt; operator/ and this case seal are outside anonymous content.'}
    save(operator/'ORIGINAL-PIN-LEDGER.json',ledger)
    members={str(p.relative_to(case_root)):sha(p.read_bytes())for p in sorted(case_root.rglob('*'))if p.is_file()}
    seal={'version':1,'kind':'raw-source-contract-supplement-seal','files':members}
    seal_sha=save(case_root/'SEAL.json',seal)
    assert len(members)==154
    results.append({'task':plan['task'],'case_id':plan['case_id'],'anonymous_directory':str(anonymous),
        'operator_ledger':str(operator/'ORIGINAL-PIN-LEDGER.json'),'case_seal':str(case_root/'SEAL.json'),
        'case_seal_file_sha256':seal_sha,'raw_files':152,'sealed_members':154})

index={'version':1,'kind':'operator-only-mechanical-source-contract-supplement-index',
    'scope':'Mechanical original-byte packaging only; no grading and no new source-domain admission.',
    'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
    'original_pin_provenance':provenance_refs,'cases':results,
    'fixed_uniform_selection_applied_once':True,'all_stock_records_name_same_83_production_files':True,
    'source_API_placement_artifact_inventory_checked_once':True,
    'unavailable_original_artifacts':[],'identity_issues':[],
    'source_or_criteria_edits':0,'SDK_or_SUT_forwards':0,'judge_outputs_or_X_Y_map_read':False,
    'anonymous_delivery_rule':'Provide each case anonymous/ only, identically for its three versions; do not expose operator/ ledgers or this operator index.'}
save(OUT/'OPERATOR-INDEX.json',index)
save(OUT/'OPERATOR-READSET.json',{'version':1,'kind':'mechanical-packaging-readset','scope':index['scope'],
    'files':sorted(readset.values(),key=lambda v:v['path']),
    'bodies_read':['Original task-root/platform direct source contracts selected by fixed rule','Original stock83 and placement bodies'],
    'metadata_read':['Original public-input pin ledgers','Original source83/preparation/setup/admission pins','Original design inventory and reviewer per-file identity readset'],
    'excluded':['judge output','X/Y mapping','individual current business component','costs/selfclaims','SUT/SDK execution']})
outer_members={str(p.relative_to(OUT)):sha(p.read_bytes())for p in sorted(OUT.rglob('*'))if p.is_file()and p.name!='OPERATOR-SEAL.json'}
outer={'version':1,'kind':'operator-mechanical-supplement-packaging-seal','files':outer_members}
outer_sha=save(OUT/'OPERATOR-SEAL.json',outer)
for relative,expected in outer_members.items():assert sha((OUT/relative).read_bytes())==expected
print(json.dumps({'operator_index':str(OUT/'OPERATOR-INDEX.json'),'operator_index_canonical_sha256':digest(index),
    'operator_seal':str(OUT/'OPERATOR-SEAL.json'),'operator_seal_file_sha256':outer_sha,
    'cases':results,'unavailable_original_artifacts':[],'identity_issues':[]},indent=2))
