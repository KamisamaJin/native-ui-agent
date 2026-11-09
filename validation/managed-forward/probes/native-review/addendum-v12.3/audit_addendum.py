#!/usr/bin/env python3
"""Independent offline audit; no SDK launch and no original evidence writes."""
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from PIL import Image

ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
BASE=ROOT/'validation/managed-forward'
OUT=BASE/'probes/native-review/addendum-v12.3'
CANDIDATE=BASE/'candidate-v12.3'
sys.path.insert(0,str(CANDIDATE/'scripts'))
import design_contract as d
import native_checks as nc
import action_guard as ag
import execution_plan as xp
import acceptance as ac

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def dump(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n')
def ref(p,note=None):return {'path':str(p.resolve()),'sha256':sha(p),**({'note':note} if note else {})}

freeze={version:load(BASE/name) for version,name in [('v12.2','CANDIDATE-FREEZE-3.json'),('v12.3','CANDIDATE-FREEZE-4.json')]}
assert sha(BASE/'CANDIDATE-FREEZE-4.json')=='13e3b62a8693a87db0e2e127af89053da90ad01d2c228ee1fdcca2fd2fa44ac7'
assert all(Path(m.__file__).resolve().is_relative_to(CANDIDATE) for m in [d,nc,ag,xp,ac])
packs=[('v12.2','positive',BASE/'evidence/qualification-v12.2/android-positive'),
       ('v12.2','cancel',BASE/'evidence/cancel-sdk-v2-qualification'),
       ('v12.3','positive',BASE/'evidence/qualification-v12.3/android-positive'),
       ('v12.3','cancel',BASE/'evidence/qualification-v12.3/android-cancel')]
integrity=[];images=[];sources={};positives=[];cancels=[]
def remember(p):
    if p.is_file():sources[str(p.resolve())]=dict(ref(p),bytes=p.stat().st_size)

for version,kind,root in packs:
    for p in root.rglob('*'):
        if p.is_file():remember(p)
    portable=load(root/'portable-sha256.json');checks=[{'path':str(root/name),'expected':expected,'actual':sha(root/name),'matches':sha(root/name)==expected} for name,expected in portable.items()]
    runtime=root/'capture/tool-runtime';toolchecks=[]
    for p in runtime.rglob('*'):
        if p.is_file():
            rel=str(p.relative_to(runtime));toolchecks.append({'relative':rel,'sha256':sha(p),'matches_declared_candidate':sha(p)==freeze[version]['files'].get(rel)})
    integrity.append({'version':version,'kind':kind,'root':str(root),'portable_index':ref(root/'portable-sha256.json'),'all_portable_match':all(x['matches'] for x in checks),'checks':checks,
        'all_runtime_match_declared_candidate':all(x['matches_declared_candidate'] for x in toolchecks),'toolchecks':toolchecks})
    for p in sorted(root.rglob('*.png')):
        item={'version':version,'kind':kind,'file':ref(p)}
        try:
            with Image.open(p) as image:item['size']=list(image.size);image.verify()
            with Image.open(p) as image:image.load()
            item['fully_decodable']=True
        except Exception as error:item.update(fully_decodable=False,error_type=type(error).__name__,error=str(error))
        images.append(item)
    if kind=='positive':
        native=root/'capture/native';fixed=BASE/'probes/native/prepared-positive/android';config=load(fixed/'config.json');plan=load(fixed/'plan.json');lock=load(fixed/'lock.json');observation=load(native/'observation.json');execution=load(root/'capture/execution.json')
        for p in [fixed/'config.json',fixed/'plan.json',fixed/'lock.json',fixed/'reference.json',fixed/'environment.json',fixed.parent/'fixtures.json']:remember(p)
        xp.verify_execution(execution,plan,lock,config['design_sha256'],load(fixed.parent/'fixtures.json'),sha(native/'sources/ObserverBridge.kt'))
        guards=ag.verify_observation(execution['actions'],observation,'android')
        evaluated=nc.evaluate(plan,observation,'android',root=native,observation_sha256=sha(native/'observation.json'),design_lock=lock,design_sha256=config['design_sha256'])
        env=ac.environment(observation,load(fixed/'environment.json'),'android');junit=ET.parse(native/'junit.xml').getroot();cycle=load(root/'cycle.json');resources=load(root/'resources.json')
        original=load(root/'capture/automatic.json')
        positives.append({'version':version,'root':str(root),'junit':junit.attrib,'testcases':[x.attrib for x in junit.findall('testcase')],
            'recomputed':evaluated,'guards':guards,'environment':env,
            'checks':{'plan_bytes_match':sha(fixed/'plan.json')==sha(root/'capture/parent-plan.json'),
                'assertion_statuses_match_original':{x['id']:x['status'] for x in evaluated['assertions']}=={x['id']:x['status'] for x in original['assertions']},
                'source_before_after_equal':load(root/'capture/source-before.json')==load(root/'capture/source-after.json'),
                'cycle_pins_final_resources':cycle.get('resources_sha256')==sha(root/'resources.json'),
                'final_receipt_clean':resources.get('final')is True and not resources.get('cleanup_errors') and not resources.get('remaining_directories') and not resources.get('remaining_devices'),
                'cycle_status_accepted':cycle.get('status')=='accepted'},
            'evidence':[ref(native/'junit.xml'),ref(native/'observation.json'),ref(root/'capture/automatic.json'),ref(root/'resources.json'),ref(root/'cycle.json')]})
    else:
        record=BASE/('probes/native/cancel-sdk-v2/result.json' if version=='v12.2' else 'probes/native/cancel-sdk-v3/result.json');remember(record);r=load(record)
        p=root/'capture/native'/Path(r['first_frame']['path']).name;first=next(x for x in images if x['file']['path']==str(p.resolve()))
        lease=r['sdk_process_receipt_before_cancel'];before=r['group_before'];after=r['group_after_samples'];leader=next(x for x in before if x['pid']==lease['pid'])
        error=load(root/'service-error.json');resources=load(root/'resources.json');manifest=load(root/'capture/native/manifest.json')
        checks={'frame_fully_decodable':first['fully_decodable'],'first_frame_hash_matches':sha(p)==r['first_frame']['sha256'],
            'same_exact_group_before':bool(before) and all(x['pgid']==lease['pgid'] and not x['state'].startswith('Z') for x in before),
            'leader_birth_group_match':leader['started']==lease['identity']['started'] and leader['pgid']==lease['identity']['pgid']==lease['pid'],
            'leader_command_hash_match':hashlib.sha256(lease['identity']['command'].encode()).hexdigest()==leader['command_sha256'],
            'token_in_registered_command':lease['token'] in lease['identity']['command'],
            'sampled_group_empty_within_ten_seconds':after[-1]['members']==[] and 0<=after[-1]['at_unix']-r['signal_at_unix']<=10,
            'source_before_after_equal':r['source_hashes_before']==r['source_hashes_after'],
            'resource_receipt_matches_record':resources==r['resources'],
            'clean_owned_receipt':not resources['cleanup_errors'] and not resources['remaining_directories'] and not resources['remaining_devices'],
            'signal15_primary_error':resources['primary_error']['type']=='InterruptedError' and '15' in resources['primary_error']['message'],
            'not_accepted_and_no_cycle':error['status']=='not_accepted' and not(root/'cycle.json').exists() and r['cycle_published']is False,
            'reserved_folder_reported_absent':r['reserved_test_folder_exists']is False,
            'nonzero_exit':r['exit_code']!=0}
        log_details=None
        if version=='v12.3':
            prefix=BASE/'probes/native/cancel-sdk-v3/pre-cancel-sdk-prefix.log';controller=BASE/'probes/native/cancel-sdk-v3/controller.log';remember(prefix);remember(controller);remember(BASE/'qualify_cancel.py')
            content=(root/'capture/native/test.log').read_bytes();rawprefix=prefix.read_bytes();log_details={'prefix':ref(prefix),'retained_log':ref(root/'capture/native/test.log'),'prefix_bytes':len(rawprefix),'retained_bytes':len(content)}
            checks.update(nonempty_prefix_before_cancel=len(rawprefix)>0,log_before_hash_matches=sha(prefix)==r['log_before_cancel']['sha256'],
                log_after_hash_matches=hashlib.sha256(content).hexdigest()==r['log_after_cancel']['sha256'],exact_original_prefix_retained=content.startswith(rawprefix))
        cancels.append({'version':version,'root':str(root),'record':ref(record),'checks':checks,'all_scope_checks_pass':all(checks.values()),
            'group_before':before,'group_after_samples':after,'signal_to_empty_seconds':after[-1]['at_unix']-r['signal_at_unix'],'log':log_details,
            'evidence':[ref(record),ref(p),ref(root/'resources.json'),ref(root/'resource-events.jsonl'),ref(root/'service-error.json'),ref(root/'capture/native/manifest.json')],
            'scope':'Recorded owned process group only; no escaped-daemon, OS device, physical touch, SIGINT or iOS credit.'})

seals=[]
for root in [BASE/'evidence/cancel-sdk-v2-qualification',BASE/'evidence/qualification-v12.3']:
    p=root/'SEAL.json';remember(p);seal=load(p);checks=[]
    for rel,data in seal['files'].items():
        expected=data['sha256'] if isinstance(data,dict) else data;checks.append({'path':str(root/rel),'matches':sha(root/rel)==expected})
    seals.append({'seal':ref(p),'all_match':all(x['matches'] for x in checks),'checks':checks})
dump('readset.json',{'files':list(sources.values()),'scope':'Only the two explicitly supplied versioned positive/cancel qualification packages, associated native cancellation records/controller/logs, and the already approved neutral prepared-positive contract.'})
dump('raw-integrity.json',{'packages':integrity,'seals':seals})
dump('positive-recomputations.json',positives);dump('cancel-recomputations.json',cancels);dump('image-audit.json',images)
decisions=[]
for p in positives:
    ok=p['recomputed']['counts']=={'passed':6,'failed':0,'unassessed':0} and p['environment']['status']=='P' and all(p['checks'].values())
    decisions.append({'version':p['version'],'claim':'Neutral Android Paparazzi counter positive route and final managed receipt','status':'qualified_android_provider_scope' if ok else 'not_qualified','evidence':p['evidence'],'scope':'Semantic OnClick/caller replacement in the attached ComposeView, not OS touch or business PR quality.'})
for c in cancels:
    decisions.append({'version':c['version'],'id':'N05/SDK-SIGTERM','status':'closed_recorded_android_owned_group_scope' if c['all_scope_checks_pass'] else 'not_qualified','evidence':c['evidence'],
        'additional_log_evidence':c['log'],'signal_to_empty_seconds':c['signal_to_empty_seconds'],'scope':c['scope'],
        'prior_review_preserved':'Old v1 cancellation PNG remains truncated and its partial judgment is not rewritten. This separate qualification uses new complete frames and exact before/after group records.'})
dump('decisions.json',{'version':1,'decisions':decisions,'latest_scope':'candidate-v12.3 Android provider qualification is distinct from attempt-5 synthetic/generic replay and does not close iOS or escaped-daemon gaps.',
    'original_sdk_review':ref(BASE/'probes/native-review/REPORT.md'),'original_sdk_decisions':ref(BASE/'probes/native-review/decisions.json')})
print(json.dumps({'packages_integrity':[{'version':x['version'],'kind':x['kind'],'all_match':x['all_portable_match'],'runtime_matches':x['all_runtime_match_declared_candidate']} for x in integrity],
    'positive_counts':[(x['version'],x['recomputed']['counts'],x['environment']['status']) for x in positives],
    'cancellations':[(x['version'],x['all_scope_checks_pass'],x['signal_to_empty_seconds']) for x in cancels],
    'invalid_interrupted_images':[x for x in images if not x['fully_decodable']]},ensure_ascii=False))
