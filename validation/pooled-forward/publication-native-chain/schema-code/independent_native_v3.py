#!/usr/bin/env python3
"""Registered post-barrier facts, never repair/retry/grade or alter expectations."""
import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import traceback

HELPER_SHA='1a52cc62be5cee0bad34fefe8b54a7479761ca5ea5e8981937a8a1ad11ae6b05'
DOMAIN_SHA='fd82356e7b76a8b3099351d6de4d19259eeb241dd99e06b1c4efad3668ba7c8c'
V1_SHA='3c305880a818ab87c21c0c1043064b02af5991633efc7d3ab8d31405c4990a5d'
ZERO_INDEX_SHA='c38a94abf1b1d362989af64aaedefc6337f8fe630d23a4883ed1062d2fac5dea'
ZERO_REVIEW_SHA='5bf91da2480980262447e3c6b0701fcb121e5e4032ed501a98687ddd4411acb4'
V2_SHA='7c8cf014299ea94db1646d22bd09be69040aaf183a10e50a7fd824126dbb02d2'


def need(value,message):
    if not value: raise ValueError(message)


def safe(raw):
    p=Path(raw)
    need(p.is_absolute() and str(p)==os.path.normpath(str(p)) and '..' not in p.parts,'Canonical absolute path required')
    for item in [p,*p.parents]: need(not item.is_symlink(),'Symlink in operation path: '+str(item))
    return p


def sha(p):
    h=hashlib.sha256()
    with safe(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def load(p): return json.loads(safe(p).read_bytes())
def save(p,value):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    p.chmod(0o444)
def ref(p):p=safe(p);return {'path':str(p),'sha256':sha(p)}
def check_blob_ref(value):
    need(set(value)=={'path','sha256'} and sha(value['path'])==value['sha256'],'Pinned file changed: '+str(value.get('path')))
    return safe(value['path'])
def check_ref(value):
    check_blob_ref(value)
    return load(value['path'])
def module(p,name):
    spec=importlib.util.spec_from_file_location(name,safe(p));result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
def intersects(a,b):return a==b or a.is_relative_to(b) or b.is_relative_to(a)


def validate_barrier(members,cohort,authorization,events,expected):
    need(set(members)==set(expected) and cohort['members']==members,'Complete expected ten-member cohort required')
    co=[e for e in events if e['kind']=='cohort_sealed'];au=[e for e in events if e['kind']=='hidden_authorized'];va=[e for e in events if e['kind']=='hidden_contexts_validated']
    need(len(co)==len(au)==len(va)==1 and co[0]==cohort and au[0]==authorization['authorization'],'Original unique cohort/authorization events required')
    self_events=[e for e in events if e['kind']=='self_sealed']
    need(len(self_events)==len(expected) and {(e['task'],e['arm']) for e in self_events}=={tuple(v.split('/')) for v in expected},'Self-seal membership differs')
    for e in self_events:
        locks=[v for v in events if v['kind']=='source_locked' and (v.get('task'),v.get('arm'))==(e['task'],e['arm'])]
        need(len(locks)==1 and locks[0]['sequence']<e['sequence']<cohort['sequence'] and e['source_sha256']==locks[0]['source_sha256']==members[e['task']+'/'+e['arm']]['source_sha256'],'Final source/self/cohort order or digest differs')
    need(cohort['sequence']<au[0]['sequence']<va[0]['sequence'] and va[0]['authorization_sequence']==au[0]['sequence'],'Hidden authorization/validation occurred before barrier')


def barrier(root,helper,cleanup=False):
    run=root/'cache/business/run-cohort2'
    # These exact frozen methods are read-only. Do not call expire/status/serve.
    with safe(run/'state.lock').open('rb') as state:
        fcntl.flock(state,fcntl.LOCK_SH)
        study=helper.Study(run);events=study.events()
        cohort=load(run/'COHORT-SEAL.json');authorization=load(run/'HIDDEN-AUTHORIZATION.json')
        members=cohort['members'] if cleanup else study.cohort()
        if cleanup:
            # A changed/missing live production file must not prohibit safe
            # positive-owned recovery. Keep historical metadata pins intact.
            for item in members.values():
                seal=check_ref({'path':item['path'],'sha256':item['sha256']})
                need(seal['source_sha256']==item['source_sha256'],'Cleanup historical member digest differs')
                need(sha(seal['claim_path'])==seal['claim_sha256'],'Cleanup historical self-claim changed')
            for tool in study.manifest['tools'].values():helper.frozen_files(tool)
        expected=[t['id']+'/'+a for t in study.manifest['tasks'] for a in t['arms']]
        validate_barrier(members,cohort,authorization,events,expected)
        need(authorization['authorization']['cohort_sha256']==sha(run/'COHORT-SEAL.json'),'Cohort authorization hash differs')
        registered={e['request_id'] for e in events if e['kind']=='request_enqueued'};terminal={e['request_id'] for e in events if e['kind']=='request_finished'}
        need(registered==terminal,'Public FIFO is not terminal')
        for t in study.manifest['tasks']:
            for alias in t['arms']:
                proof=study.d0_proof(t['id'],alias);need(proof is not None,'Original first D0 proof absent')
                first,prepared,result,_finished=proof
                anchors=[e for e in events if e['kind']=='repair_started' and (e.get('task'),e.get('arm'))==(t['id'],alias)]
                fields={'deadline_clock':result['finished_at_clock']+1200,'deadline_at_unix':result['finished_at_unix']+1200,'repair_budget_seconds':1200,'d0_request_id':first['request_id'],'d0_finished_at_clock':result['finished_at_clock'],'d0_finished_at_unix':result['finished_at_unix'],'d0_result':{'path':prepared['result_path'],'sha256':prepared['result_sha256']},'d0_source_sha256':first['source']['content_sha256'],'d0_readset_sha256':helper.digest(first['readset'])}
                need(len(anchors)==1 and all(anchors[0].get(k)==v for k,v in fields.items()),'First D0 source window changed')
        return run,study.manifest,authorization


def initial_entry(root,task,profile,manifest,seal_path,seal_sha):
    expected=root/'cache/business/initial-reference/PREPARATION-SEAL.json'
    need(seal_path is not None and seal_sha and safe(seal_path)==expected and sha(seal_path)==seal_sha,'Exact external initial-preparation pin required')
    seal=load(seal_path)
    need(set(seal)=={'version','kind','tasks'} and seal['version']==1 and seal['kind']=='canonical-initial-reference-preparation','Initial preparation schema differs')
    need(set(seal['tasks'])=={t['id'] for t in manifest['tasks']},'Initial preparation task set differs')
    for t in manifest['tasks']:need(set(seal['tasks'][t['id']])==set(t['arms']['A']['public_configs']),'Initial profile set differs')
    entry=seal['tasks'][task][profile]
    need(set(entry)=={'config','source_manifest','resource_root','source_roots'},'Exact initial profile entry required')
    need(entry['config']['path']==str(root/f'cache/business/initial-reference/{task}/profiles/{profile}.json'),'Initial config path differs')
    need(entry['resource_root']==str(root/f'cache/business/initial-reference/{task}/resources/{profile}'),'Initial resource must use its distinct registered root')
    check_ref(entry['config']);check_ref(entry['source_manifest'])
    base=root/f'cache/business/initial-reference/{task}'
    need(safe(entry['source_manifest']['path']).is_relative_to(base),'Initial source manifest is outside canonical tree namespace')
    protected=[root/'cache/business/run-cohort2',root/'cache/business/independent-evaluation',safe(entry['resource_root'])]
    protected += [safe(p) for t in manifest['tasks'] for a in t['arms'].values() for p in [*a['source_roots'],*a['resource_roots']]]
    for raw in entry['source_roots']:
        p=safe(raw);need(p.is_relative_to(base) and not any(intersects(p,v) for v in protected),'Initial source overlaps final/evidence/resource namespace')
    return entry,ref(seal_path)


def profile_admission(run,task,alias,arm,config_path,helper,output):
    public=load(run/f'arms/{task}/{alias}/public-inputs.json')
    config=load(config_path);platform=helper.domain.platform(config);hook=arm['profile_admissions'][platform]
    files=[hook['script'],hook['approval'],*hook.get('dependencies',[])]
    for p in files:need(p in public and sha(p)==public[p],'Original profile-admission code/input changed: '+p)
    approval=load(hook['approval']);need(helper.digest(approval)==hook['approval_sha256'],'Profile approval canonical pin differs')
    guard=module(hook['script'],'independent_actual_profile')
    verdict=guard.verify(Path(hook['root']),approval,hook['approval_sha256'],platform,config)
    need(verdict.get('status')=='admitted_profile' and verdict.get('platform')==platform,'Actual runtime profile not admitted')
    inputs={key:{**ref(config[key]),'canonical_sha256':helper.digest(load(config[key]))} for key in ['design_lock','plan','policy','routes','environment','fixtures']}
    inputs['bridge']=ref(config['bridge'])
    for key in ['coverage_domain_ref','coverage_provider_ref']:
        if key in config:
            item=config[key];need(helper.digest(load(item['path']))==item['sha256'],'Changed '+key);inputs[key]={**ref(item['path']),'canonical_sha256':item['sha256']}
    for p in files:need(sha(p)==public[p],'Profile-admission input changed during admission')
    value={'version':1,'config':{**ref(config_path),'canonical_sha256':helper.digest(config)},'script':ref(hook['script']),'approval':{**ref(hook['approval']),'canonical_sha256':hook['approval_sha256']},'dependency_files':{p:public[p] for p in files},'platform':platform,'inputs':inputs,'verdict':verdict}
    save(output,value);return value


def scope_path(evidence,task,arm,profile):return evidence/'native-claims'/task/arm/(profile+'.json')
def reserve_native(evidence,task,arm,profile,record,config,capsule):
    p=scope_path(evidence,task,arm,profile)
    save(p,{'version':1,'task':task,'arm':arm,'profile':profile,'action':'native','record':str(record),'config':config,'source_capsule':capsule,'reserved_at_unix':time.time(),'scope':'One admitted native attempt; failure/interruption never authorizes a replacement sample'})
    return ref(p)


def continuation_scope(task,arm,profile): return task+'/'+arm+'/'+profile
def continuation_claim_path(evidence,task,arm,profile): return evidence/'native-continuation-claims'/task/arm/(profile+'.json')


def entry_resume(root,row,record,permit_path,permit_sha,registered_claim=None):
    expected=root/'operators/cohort2/coordination/UNCLAIMED-ENTRY-v3-ADMISSION.json'
    need(permit_path is not None and permit_sha and safe(permit_path)==expected and sha(permit_path)==permit_sha,'Exact reviewed preclaim-entry permit required')
    permit=load(permit_path)
    need(permit.get('kind')=='explicit-unclaimed-pre-forward-entry-admission' and permit.get('operator_review_completed') is True,'Preclaim-entry admission is not reviewed')
    need(permit['base_authority']==load(root/'cache/business/independent-evaluation/NATIVE-CONTINUATION-AUTHORITY.json'),'Original d434 authority registry must remain unchanged')
    key=continuation_scope(*[load(row['original']['original_outcome']['path'])[k] for k in ['task','arm','profile']])
    need(key=='T1/B/android','Only the exact proven preclaim Android entry is eligible')
    entry=permit['entry_resume'];need(entry['scope']==key and entry['licensed_record']==row['record'] and entry['resumed_record']==str(record),'Preclaim entry/record scope differs')
    need(record==root/'cache/business/independent-evaluation/entry-resumptions/T1/B/android/native','Exact distinct preclaim-resume namespace required')
    failed=safe(row['record']);need(set(p.name for p in failed.iterdir())=={'ENTRY.json','outcome.json','failure.json'},'Any extra execution evidence forbids entry resume')
    for name,pin in entry['failed_record_files'].items():
        need(pin['path']==str(failed/name),'Foreign failed-entry file');check_blob_ref(pin)
    need(set(entry['failed_record_files'])=={'ENTRY.json','outcome.json','failure.json'},'Exact preclaim file inventory required')
    outcome=check_ref(entry['failed_record_files']['outcome.json'])
    need(outcome.get('error')=={'type':'ValueError','message':'Original fresh independent context is no longer empty before first native UI'} and outcome.get('source_unchanged') is True,'Not the exact source-unchanged preclaim admission failure')
    need(outcome['config']==row['original']['original_config'] and outcome['source_capsule']==row['original']['original_source_capsule'],'Preclaim source/config differs')
    need(not any(outcome.get(k) for k in ['native_claim','native_continuation_claim','envelope_record','service_output','capture','cycle']),'Existing or ambiguous UI evidence forbids entry resume')
    evidence=root/'cache/business/independent-evaluation';claim_path=continuation_claim_path(evidence,*key.split('/'))
    if registered_claim is None:need(not claim_path.exists(),'Preclaim already has a native continuation claim')
    else:
        claim=load(claim_path)
        need(ref(claim_path)==registered_claim and claim['record']==str(record),'Registered resumed entry claim differs')
        need(claim.get('entry_resume_permit')==ref(permit_path) and claim.get('failed_preclaim_entry')==entry['failed_record_files']['outcome.json'] and claim.get('licensed_original_record')==row['record'],'Registered entry-resume permit/failure chain differs')
    return ref(permit_path),entry['failed_record_files']['outcome.json']


def fresh_platform_context(root,evidence,task,arm,profile,config,capsule,helper):
    for key in ['review_store','source_review_store']:
        p=safe(config[key]);need(not p.exists() or not any(p.iterdir()),'Current platform review context is not fresh')
    raw=config.get('workflow',{}).get('root')
    if not raw:return {'current_platform_fresh':True,'workflow':'not_configured'}
    workflow=safe(raw)
    if not workflow.exists() or not any(workflow.iterdir()):return {'current_platform_fresh':True,'workflow':'fresh_empty'}
    need(arm=='B','Only the declared stateful own-arm workflow may share platform namespaces')
    sibling='android' if profile=='ios' else 'ios'
    allowed={'owner.json',sibling+'.lock',sibling+'.json',sibling+'-backup.json'}
    need(set(p.name for p in workflow.iterdir())==allowed,'Only registered sibling-platform workflow members are allowed before first current-platform UI')
    sibling_files={p.name:ref(p) for p in workflow.iterdir()}
    owner=helper.digest([str(Path(p).resolve()) for p in config['source_roots']])
    expected_owner={'format':'native-ui-workflow-v1','owner':owner,'root_identity':{'device':workflow.stat().st_dev,'inode':workflow.stat().st_ino}}
    need(load(workflow/'owner.json')==expected_owner,'Shared workflow owner/root identity differs')
    claim_path=continuation_claim_path(evidence,task,arm,sibling);claim=load(claim_path);native_path=safe(claim['record'])/'outcome.json';native=load(native_path)
    native_reference(evidence,task,arm,sibling,native['config'],capsule,native_path,sha(native_path))
    sibling_config=check_ref(native['config'])
    need(sibling_config.get('workflow',{}).get('root')==str(workflow) and sibling_config['source_roots']==config['source_roots'],'Sibling platform does not own this same declared workflow/source')
    need(helper.domain.platform(sibling_config)==sibling,'Registered sibling actual platform differs')
    inventory=check_ref(native['inventory']);service=safe(native['service_output'])
    for name in ['workflow-state.json','workflow-context.json']:
        p=service/name;need(inventory[str(p)]['sha256']==sha(p) and inventory[str(p)]['bytes']==p.stat().st_size,'Original sibling workflow output changed')
    snapshot=load(service/'workflow-state.json');context=load(service/'workflow-context.json');context_sha=helper.digest(context)
    need(snapshot.get('owner')==owner and snapshot.get('platform')==sibling and snapshot.get('cycles')==[{'cycle':native['cycle'],'context_sha256':context_sha}],'Sibling checkpoint is not its one registered first native cycle')
    need(snapshot.get('capture')=={'cycle':native['cycle'],'context_sha256':context_sha,'capture':native['capture'],'context':ref(service/'workflow-context.json')},'Sibling checkpoint capture/context binding differs')
    expected=copy.deepcopy(snapshot);expected['generation']+=2
    need(load(workflow/(sibling+'.json'))==expected and load(workflow/(sibling+'-backup.json'))==expected,'Shared checkpoint differs from frozen publish/checkpoint result')
    lock=safe(workflow/(sibling+'.lock'));need(lock.stat().st_size==0,'Sibling lock has unexpected payload')
    with lock.open('rb') as stream:fcntl.flock(stream,fcntl.LOCK_SH|fcntl.LOCK_NB)
    return {'current_platform_fresh':True,'workflow':'registered_same_arm_sibling_only','owner':ref(workflow/'owner.json'),'sibling_native':ref(native_path),'sibling_files':sibling_files}


def continuation_authority(root,path,pinned):
    expected=root/'operators/cohort2/coordination/UNFORWARDED-CONTINUATION-AUTHORIZATION.json'
    need(path is not None and pinned and safe(path)==expected and sha(path)==pinned,'External exact continuation-authority pin required')
    value=load(path)
    need(value.get('version')==1 and value.get('kind')=='explicit-single-unforwarded-native-continuation-authority','Continuation authority kind differs')
    need(value.get('approval_delivery',{}).get('operator_review_completed') is True,'Explicit reviewed continuation admission required')
    need(value['original_runner']=={'path':str(Path(__file__).with_name('independent_native.py')),'sha256':V1_SHA},'Original runner pin differs')
    need(sha(value['original_runner']['path'])==V1_SHA,'Original runner bytes changed')
    need(value['zero_forwarding_index']['sha256']==ZERO_INDEX_SHA and value['independent_review']['sha256']==ZERO_REVIEW_SHA,'Original zero-forwarding pins differ')
    index=check_ref(value['zero_forwarding_index']);review=check_ref(value['independent_review'])
    need(review['status']=='verified' and not review['errors'] and review['index']==value['zero_forwarding_index'],'Independent zero-forwarding review absent')
    expected_scopes={continuation_scope('T'+str(i),a,p) for i in range(1,6) for a in ['A','B'] for p in ['ios','android']}
    expected_scopes|={continuation_scope('T'+str(i),'I',p) for i in range(2,6) for p in ['ios','android']}
    rows={continuation_scope(v['task'],v['arm'],v['profile']):v for v in index['failures']}
    reviewed={continuation_scope(v['task'],v['arm'],v['profile']):v for v in review['checked']}
    need(len(rows)==len(reviewed)==28 and set(rows)==set(reviewed)==set(value['scopes'])==expected_scopes,'Exact proven unforwarded scopes required; acquired I1 excluded')
    for key,row in value['scopes'].items():
        need(row['original']==rows[key] and reviewed[key]['original_outcome']==row['original']['original_outcome'],'Continuation source proof differs')
        task,arm,profile=key.split('/')
        need(row['record']==str(root/f'cache/business/independent-evaluation/continuations/{task}/{arm}/{profile}/native'),'Only the declared fresh continuation namespace is admitted')
    check_ref(value['cohort']);check_ref(value['hidden_authorization']);check_ref(value['initial_preparation'])
    return value,ref(path)


def verify_unforwarded(row,config,capsule):
    original=row['original']
    old_claim=check_ref(original['original_claim']);old=check_ref(original['original_outcome'])
    need(original['original_config']==config==old_claim['config']==old['config'],'Continuation config changed')
    need(original['original_source_capsule']==capsule==old_claim['source_capsule']==old['source_capsule'],'Continuation capsule changed')
    record=safe(old_claim['record'])
    sidecars=row['original_sidecars']
    names={'command':'command.json','sdk_observation':'sdk-observation.json','exception_log':'envelope/exception.log',
           'envelope_result':'envelope/result.json','recovery_log':'envelope/recovery.log',
           'recovery_resources':'envelope/error-recovery/resources.json','recovery_journal':'envelope/error-recovery/resource-journal.json',
           'recovery_events':'envelope/error-recovery/resource-events.jsonl'}
    need(set(sidecars)==set(names),'Exact original sidecar inventory required')
    for key,relative in names.items():
        need(sidecars[key]['path']==str(record/relative),'Foreign original sidecar path')
        check_blob_ref(sidecars[key])
    need(sidecars['envelope_result']==original['envelope_result'] and sidecars['recovery_resources']==original['positive_recovery_resources'],'Original sidecar aliases differ')
    need(original['original_outcome']['path']==str(record/'outcome.json') and old['action']=='native','Original claimed operation differs')
    need(old.get('source_unchanged') is True and not old.get('capture') and not old.get('cycle') and old.get('new_ui_acquisition') is not True,'Existing or ambiguous UI facts forbid continuation')
    env=check_ref(original['envelope_result']);request=check_ref(original['envelope_request'])
    need(env.get('exit_code') is None and env.get('error')=={'type':'ValueError','message':'Resource ownership differs from this project'} and env.get('source_unchanged') is True,'Only original exact pre-forward ownership failure may continue')
    command=check_ref(sidecars['command'])
    expected_argv=[env['argv'][0],'-B',str(Path(old['tool_root'])/'scripts/ui_loop.py'),'native','--config',config['path'],'--output',str(record/'service'),'--final']
    need(env['argv']==request['argv']==command['argv']==expected_argv and command['config']==config,'Original never-forwarded inner command changed')
    recovery=env.get('recovery',{})
    need(recovery.get('exit_code')==0 and recovery.get('argv')==[env['argv'][0],'-B',str(Path(old['tool_root'])/'scripts/resource_manager.py'),'--config',config['path'],'--output',str(record/'envelope/error-recovery'),'cleanup'],'Original recovery result/command differs')
    need(not (record/'envelope/command.log').exists() and not (record/'service').exists(),'Any original inner command/service evidence forbids continuation')
    resources=check_ref(original['positive_recovery_resources'])
    need(resources.get('final') is True and all(resources.get(k)==[] for k in ['cleanup_errors','remaining_directories','remaining_devices']),'Original resources did not positively close')
    sdk=check_ref(sidecars['sdk_observation'])
    need(not any(v.get('kind')=='process_started' for v in sdk['observed_command_records']),'Original process evidence is not zero-forwarding')
    return old_claim,old


def reserve_continuation(root,evidence,task,arm,profile,record,config,capsule,source_before,authority_path,authority_sha,entry_permit=None,entry_permit_sha=None):
    authority,pin=continuation_authority(root,authority_path,authority_sha)
    key=continuation_scope(task,arm,profile)
    need(key in authority['scopes'],'Already acquired or unregistered scope cannot continue')
    row=authority['scopes'][key]
    entry_pin=entry_failure=None
    if str(record)!=row['record']:entry_pin,entry_failure=entry_resume(root,row,record,entry_permit,entry_permit_sha)
    old_claim,old=verify_unforwarded(row,config,capsule)
    need(source_before==old['source_before'],'Source differs from original never-forwarded operation')
    need(ref(scope_path(evidence,task,arm,profile))==row['original']['original_claim'],'Original unique claim changed')
    need(all(old.get(k)==v for k,v in [('task',task),('arm',arm),('profile',profile)]),'Original zero-forwarding scope differs')
    registry=evidence/'NATIVE-CONTINUATION-AUTHORITY.json'
    if registry.exists():need(load(registry)==pin,'Continuation authority changed after first registration')
    else:save(registry,pin)
    p=continuation_claim_path(evidence,task,arm,profile)
    value={'version':1,'task':task,'arm':arm,'profile':profile,'action':'native','record':str(record),
            'config':config,'source_capsule':capsule,'original_claim':row['original']['original_claim'],
            'original_outcome':row['original']['original_outcome'],'authority':pin,'reserved_at_unix':time.time(),
            'scope':'Single explicit continuation before first inner native UI; original failed claim/outcome/cost retained. Never a replacement sample.'}
    if entry_pin:value.update(entry_resume_permit=entry_pin,failed_preclaim_entry=entry_failure,licensed_original_record=row['record'])
    save(p,value)
    return ref(p),row['original'],pin


def native_reference(evidence,task,arm,profile,config,capsule,outcome_path,outcome_sha):
    continued=continuation_claim_path(evidence,task,arm,profile)
    if continued.exists():
        claim=load(continued);root=evidence.parents[2]
        authority,pin=continuation_authority(root,Path(claim['authority']['path']),claim['authority']['sha256'])
        need(load(evidence/'NATIVE-CONTINUATION-AUTHORITY.json')==pin,'Registered continuation authority differs')
        row=authority['scopes'][continuation_scope(task,arm,profile)]
        need(all(claim.get(k)==v for k,v in {'task':task,'arm':arm,'profile':profile,'action':'native','config':config,'source_capsule':capsule,'original_claim':row['original']['original_claim'],'original_outcome':row['original']['original_outcome'],'authority':pin}.items()),'Registered continuation claim scope/source/authority differs')
        if claim['record']!=row['record']:
            pin=claim.get('entry_resume_permit');need(pin,'Alternate native record has no explicit entry permit')
            entry_resume(root,row,safe(claim['record']),Path(pin['path']),pin['sha256'],registered_claim=ref(continued))
        else:need(not claim.get('entry_resume_permit'),'Unexpected entry permit on ordinary licensed record')
        verify_unforwarded(row,config,capsule)
        p=safe(outcome_path);need(p==safe(claim['record'])/'outcome.json' and sha(p)==outcome_sha,'Exact original continuation outcome required')
        value=load(p)
        need(all(value.get(k)==v for k,v in {'task':task,'arm':arm,'profile':profile,'action':'native','config':config,'source_capsule':capsule}.items()),'Continuation belongs to another scope/config/source')
        need(value.get('native_continuation_claim')==ref(continued) and value.get('original_zero_forwarding_outcome')==row['original']['original_outcome'],'Native continuation chain changed')
        need(value.get('source_unchanged') is True and value.get('new_ui_acquisition') is True and not value.get('capture_reused'),'Continuation has no fresh original facts')
        for key in ['capture','cycle']:
            item=value.get(key);need(item and safe(item['path']).is_relative_to(safe(claim['record'])) and sha(item['path'])==item['sha256'],'Original continuation packet changed')
        return value,ref(p)
    claim=load(scope_path(evidence,task,arm,profile));p=safe(outcome_path)
    need(p==safe(claim['record'])/'outcome.json' and sha(p)==outcome_sha,'Original registered native outcome required')
    value=load(p)
    need(all(value.get(k)==v for k,v in {'task':task,'arm':arm,'profile':profile,'action':'native','config':config,'source_capsule':capsule}.items()),'Native reference belongs to another scope/config/source')
    need(claim['config']==config and claim['source_capsule']==capsule and value.get('source_unchanged') is True,'Native owner/source changed')
    need(value.get('new_ui_acquisition') is True and not value.get('capture_reused') and value.get('capture') and value.get('cycle'),'Registered operation has no fresh original capture')
    for key in ['capture','cycle']:
        item=value[key];need(safe(item['path']).is_relative_to(safe(claim['record'])) and sha(item['path'])==item['sha256'],'Original native reference changed')
    return value,ref(p)


def preserve(service,inventory_path):
    """Record links as links and never chmod their targets; always retain errors."""
    inventory={};errors=[]
    if service is None or not (service.exists() or service.is_symlink()):return None,errors
    paths=[service]
    if not service.is_symlink():
        for base,dirs,files in os.walk(service,followlinks=False):
            paths += [Path(base)/name for name in [*dirs,*files]]
    for p in paths:
        try:
            s=p.lstat()
            if stat.S_ISLNK(s.st_mode):inventory[str(p)]={'kind':'symlink','target':os.readlink(p)}
            elif stat.S_ISREG(s.st_mode):inventory[str(p)]={'sha256':sha(p),'bytes':s.st_size}
            elif not stat.S_ISDIR(s.st_mode):inventory[str(p)]={'kind':'unsupported','mode':s.st_mode};errors.append({'path':str(p),'error':'Unsupported original entry'})
        except BaseException as exc:errors.append({'path':str(p),'error':str(exc)})
    try:save(inventory_path,inventory)
    except BaseException as exc:errors.append({'path':str(inventory_path),'error':str(exc)})
    for p in reversed(paths):
        try:
            s=p.lstat()
            if stat.S_ISLNK(s.st_mode):continue
            if stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode):
                fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|(os.O_DIRECTORY if stat.S_ISDIR(s.st_mode) else 0))
                try:os.fchmod(fd,stat.S_IMODE(os.fstat(fd).st_mode)&~0o222)
                finally:os.close(fd)
        except BaseException as exc:errors.append({'path':str(p),'error':str(exc)})
    if any(v.get('kind')=='symlink' for v in inventory.values()):errors.append({'error':'Unexpected original symlinks retained without following/protecting targets'})
    return ref(inventory_path) if inventory_path.is_file() else None,errors


def monitor_gate(root,record,require_live):
    need(record is not None,'Initial-reference monitor record required');record=safe(record)
    if require_live or not (record/'CLOSED.json').exists():
        cmd=[sys.executable,'-B',str(root/'initial-reference-monitor/monitor.py'),'--record',str(record),'--preflight']
        return cmd,None
    closed=load(record/'CLOSED.json')
    need(closed.get('status')=='closed' and closed.get('positive_idle',{}).get('all_clear') is True,'Supplemental monitor did not positively close')
    # No new native facts after closure; check declared reference roots still idle.
    for raw in load(record/'EXTENDED-SPEC.json')['groups']['whole_study']['resource_journals']:
        p=safe(raw)
        if p.is_file():need(not load(p).get('devices'),'Owned slot reappeared after supplemental closure')
    return None,ref(record/'CLOSED.json')


def envelope_record(record):
    return record/('envelope-'+hashlib.sha256(str(safe(record)).encode()).hexdigest())


def forwarding_command(envelope,tool_root,config_path,record,service,action,argv):
    if action=='cleanup-native-resources':
        inner=[sys.executable,'-B',str(Path(tool_root)/'scripts/resource_manager.py'),'--config',str(config_path),'--output',str(service),'cleanup']
    else:
        inner=[sys.executable,'-B',envelope['path'],'--config',str(config_path),'--skill',tool_root,'--record',str(envelope_record(record)),'--timeout','1200','--',*argv]
    return [sys.executable,'-B',envelope['meter_path'],'--spec',envelope['meter_spec_path'],'--output',str(record/'meter.jsonl'),'--',*inner]


def main():
    entry_clock=time.monotonic();entry_unix=time.time();entry_shared_clock=time.clock_gettime(time.CLOCK_MONOTONIC)
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['root','config','record']:p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--task',choices=['T'+str(i) for i in range(1,6)],required=True);p.add_argument('--arm',choices=['A','B','I'],required=True);p.add_argument('--profile',choices=['ios','android'],required=True)
    p.add_argument('--action',choices=['native','bind-source-review','bind-native-review','finish-native-review','cleanup-native-resources'],required=True)
    for key in ['submission','capture','cycle','initial-monitor','initial-seal','native-outcome','continuation-authority','entry-permit']:p.add_argument('--'+key,type=Path)
    p.add_argument('--initial-seal-sha256');p.add_argument('--native-outcome-sha256');p.add_argument('--continuation-authority-sha256');p.add_argument('--entry-permit-sha256');a=p.parse_args()
    root=safe(a.root);record=safe(a.record);evidence=root/'cache/business/independent-evaluation'
    need(record.is_relative_to(evidence) and record!=evidence,'Fresh independent-evaluation record required')
    record.mkdir(parents=True,exist_ok=False)
    outcome={'version':4,'kind':'independent-original-fact-operation','operator_revision':'strict-own-platform-shared-workflow-preclaim-entry-v3','task':a.task,'arm':a.arm,'profile':a.profile,'action':a.action,'started_at_unix':entry_unix,'started_at_monotonic':entry_clock,'started_at_clock_gettime_monotonic':entry_shared_clock,'scope':'Full entry/barrier/admission/queue/SDK/review/cleanup wall; original failed work retained, no repair/expected override/UI resampling. Process exit is not delivery acceptance.'}
    save(record/'ENTRY.json',{**outcome,'argv':sys.argv,'runner':ref(Path(__file__).resolve())})
    code=None;service=None;source_before=None;config=None;helper=None
    try:
        with (evidence/'serialized-forwarding.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            helper_path=root/'business-tools-v4/blind_study.py'
            need(sha(Path(__file__).with_name('independent_native.py'))==V1_SHA,'Original v1 operator runner changed')
            need(sha(Path(__file__).with_name('independent_native_v2.py'))==V2_SHA,'Original v2 operator runner changed')
            need(sha(helper_path)==HELPER_SHA and sha(helper_path.with_name('source_domain.py'))==DOMAIN_SHA,'Frozen controller/domain changed')
            helper=module(helper_path,'independent_frozen_helpers');run,manifest,authorization=barrier(root,helper,a.action=='cleanup-native-resources')
            task=next(t for t in manifest['tasks'] if t['id']==a.task);alias='A' if a.arm=='I' else a.arm;arm=task['arms'][alias];tool=manifest['tools'][arm['tool']]
            config_path=safe(a.config);initial=None
            if a.arm=='I':
                initial,preparation=initial_entry(root,a.task,a.profile,manifest,a.initial_seal,a.initial_seal_sha256)
                authority=evidence/'INITIAL-PREPARATION-AUTHORITY.json'
                if authority.exists():need(load(authority)==preparation,'Initial preparation pin changed after first operation')
                else:save(authority,preparation)
                expected=initial['config'];outcome['initial_preparation']=preparation
                original_ref=load(run/'INITIAL-COHORT.json')[a.task]['A'];original=check_ref(original_ref)
                outcome['original_initial_capsule']=original_ref
                canonical=check_ref(initial['source_manifest'])
                need(canonical['files']==original['files'] and canonical['content_sha256']==original['content_sha256'],'Canonical initial bytes differ from original initial')
                capsule=initial['source_manifest'];wanted=canonical
            else:
                expected={k:authorization['hidden_configs'][a.task][a.arm][a.profile][k] for k in ['path','sha256']}
                locked=next(e for e in helper.Study(run).events() if e['kind']=='source_locked' and (e.get('task'),e.get('arm'))==(a.task,a.arm))
                capsule={'path':locked['source_manifest'],'sha256':locked['source_manifest_sha256']};wanted=check_ref(capsule)
            need(str(config_path)==expected['path'] and sha(config_path)==expected['sha256'],'Exact authorized config pin required')
            config=load(config_path)
            need(config['source_roots']==(initial['source_roots'] if initial else arm['source_roots']),'Source roots differ from registered scope')
            need(config['resources'].get('max_simulators',1)==1,'One owned device per reference/final required')
            need(config['resources']['root']==initial['resource_root'] if initial else config['resources']['root'] in arm['resource_roots'],'Foreign resource root')
            if a.action!='cleanup-native-resources':need(helper.domain.platform(config)==a.profile,'Actual profile platform differs')
            try:source_before=helper.source(config['source_roots'])
            except BaseException:
                if a.action!='cleanup-native-resources':raise
            if a.action!='cleanup-native-resources':
                need(source_before==wanted,'Actual locked/canonical source identity differs')
                if a.arm=='I':
                    for raw in config['source_roots']:
                        rr=safe(raw)
                        need(all(not (v.stat().st_mode&0o222) for v in [rr,*rr.rglob('*')]),'Canonical initial production roots must remain readonly')
            outcome.update(config=ref(config_path),source_capsule=capsule,source_before=source_before,tool_root=tool['skill_root'])
            if a.action=='native':
                context_proof=fresh_platform_context(root,evidence,a.task,a.arm,a.profile,config,capsule,helper)
                save(record/'fresh-platform-context.json',context_proof)
                outcome['fresh_platform_context']=ref(record/'fresh-platform-context.json')
                continued,original,pin=reserve_continuation(root,evidence,a.task,a.arm,a.profile,record,ref(config_path),capsule,source_before,a.continuation_authority,a.continuation_authority_sha256,a.entry_permit,a.entry_permit_sha256)
                outcome.update(native_claim=original['original_claim'],native_continuation_claim=continued,original_zero_forwarding_outcome=original['original_outcome'],continuation_authority=pin)
            if a.action in {'bind-native-review','finish-native-review'}:
                need(a.native_outcome is not None and a.native_outcome_sha256,'Original registered native operation pin required')
                native,pinned=native_reference(evidence,a.task,a.arm,a.profile,ref(config_path),capsule,a.native_outcome,a.native_outcome_sha256)
                outcome['native_operation']=pinned
                item=native['capture' if a.action=='bind-native-review' else 'cycle'];supplied=a.capture if a.action=='bind-native-review' else a.cycle
                need(supplied is not None and ref(supplied)==item,'Binding/finish may reference only its registered own native packet')
            if a.arm=='I' and a.action!='cleanup-native-resources':
                cmd,closed=monitor_gate(root,a.initial_monitor,a.action=='native')
                if cmd:
                    with (record/'initial-monitor-preflight.log').open('x') as stream:check=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT)
                    save(record/'initial-monitor-preflight.json',{'argv':cmd,'exit_code':check.returncode});need(check.returncode==0,'Supplemental monitor rejected')
                else:outcome['initial_monitor_positive_closed']=closed
            admission=None
            if a.action!='cleanup-native-resources':admission=profile_admission(run,a.task,alias,arm,config_path,helper,record/'profile-admission.json')
            service=record/'service';argv=[sys.executable,'-B',str(Path(tool['skill_root'])/'scripts/ui_loop.py'),a.action,'--config',str(config_path)]
            if a.action=='native':argv+=['--output',str(service),'--final']
            elif a.action=='bind-source-review':
                need(a.submission is not None,'Source actuals required');safe(a.submission);service.mkdir();argv+=['--submission',str(a.submission),'--output',str(service/'source-review-ref.json')]
            elif a.action=='bind-native-review':
                need(a.submission is not None,'Image actuals required');safe(a.submission);service=safe(config['review_store'])/record.name
                argv+=['--capture-result',str(a.capture),'--capture-sha256',sha(a.capture),'--submission',str(a.submission),'--submission-sha256',sha(a.submission),'--output',str(service)]
            elif a.action=='finish-native-review':argv+=['--cycle',str(a.cycle),'--cycle-sha256',sha(a.cycle),'--output',str(service)]
            else:
                # Explicit positive-owned recovery is allowed even after halt,
                # occupied slot, source drift or monitor failure. No UI launch.
                argv=[sys.executable,'-B',str(Path(tool['skill_root'])/'scripts/resource_manager.py'),'--config',str(config_path),'--output',str(service),'cleanup']
            envelope=manifest['envelope']
            for pk,hk in [('path','sha256'),('meter_path','meter_sha256'),('meter_spec_path','meter_spec_sha256')]:need(sha(envelope[pk])==envelope[hk],'Frozen supervision changed')
            command=forwarding_command(envelope,tool['skill_root'],config_path,record,service,a.action,argv)
            if a.action!='cleanup-native-resources':outcome['envelope_record']=str(envelope_record(record))
            save(record/'command.json',{'argv':argv,'service_output':str(service),'config':ref(config_path),'submission':ref(a.submission) if a.submission else None,'capture':ref(a.capture) if a.capture else None,'cycle':ref(a.cycle) if a.cycle else None})
            save(record/'supervised-command.json',{'argv':command,'cleanup_bypasses_new_sdk_admission_only':a.action=='cleanup-native-resources'})
            journal=safe(config['resources']['root'])/'events.jsonl';offset=journal.stat().st_size if journal.exists() else 0
            with (record/'supervisor.log').open('x') as stream:code=subprocess.run(command,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=stream,stderr=subprocess.STDOUT).returncode
            outcome.update(exit_code=code,service_output=str(service))
            raw=journal.read_bytes() if journal.exists() else b''
            save(record/'sdk-observation.json',{'journal_prefixes':[{'path':str(journal),'start_byte':offset,'end_byte':len(raw),'prefix_sha256':hashlib.sha256(raw).hexdigest()}],'observed_command_records':[item for line in raw[offset:].splitlines() if (item:=json.loads(line)).get('kind') in {'simctl_command','process_started'}],'scope':'Partial owned-resource command observations only; internal descendants/identity queries may be unobserved'})
            for key,name in [('cycle','cycle.json'),('completion','completion.json'),('review','review-result.json'),('resources','resources.json')]:
                if (service/name).is_file():outcome[key]=ref(service/name)
            if 'cycle' in outcome:
                cycle=load(outcome['cycle']['path']);outcome.update(service_status=cycle.get('status'),new_ui_acquisition=cycle.get('native_executed'),capture_reused=cycle.get('capture_reused'))
                if cycle.get('capture_result'):
                    capture=safe(cycle['capture_result']);need((a.action!='native' or capture.is_relative_to(record)) and sha(capture)==cycle['capture_sha256'],'Native packet origin/hash differs');outcome['capture']=ref(capture)
            if 'completion' in outcome:outcome['service_status']=load(outcome['completion']['path']).get('status')
            if a.action=='native':need(outcome.get('new_ui_acquisition') is True and not outcome.get('capture_reused'),'A fresh original native packet was required')
            if admission:
                need(sha(config_path)==admission['config']['sha256'] and all(sha(v['path'])==v['sha256'] for v in admission['inputs'].values()) and all(sha(p)==s for p,s in admission['dependency_files'].items()),'Admitted config/code/input changed during operation')
            helper.frozen_files(tool)
    except BaseException as exc:
        outcome['error']={'type':type(exc).__name__,'message':str(exc)};save(record/'failure.json',{'error':outcome['error'],'traceback':traceback.format_exc()})
    finally:
        try:
            inventory,errors=preserve(service,record/'original-inventory.json')
            if inventory:outcome['inventory']=inventory
            if errors:outcome['preservation_errors']=errors
        except BaseException as exc:outcome['preservation_errors']=[{'type':type(exc).__name__,'message':str(exc)}]
        after=None
        if helper is not None and config is not None:
            try:after=helper.source(config['source_roots'])
            except BaseException as exc:outcome['source_after_error']={'type':type(exc).__name__,'message':str(exc)}
        outcome.update(finished_at_unix=time.time(),finished_at_monotonic=time.monotonic(),wall_seconds=time.monotonic()-entry_clock,source_after=after,source_unchanged=source_before is not None and after==source_before)
        outcome['finished_at_clock_gettime_monotonic']=time.clock_gettime(time.CLOCK_MONOTONIC)
        outcome['accepted']=code==0 and not outcome.get('error') and not outcome.get('preservation_errors') and outcome.get('service_status')=='accepted' and outcome['source_unchanged']
        save(record/'outcome.json',outcome)
    print(json.dumps({'outcome':str(record/'outcome.json'),'sha256':sha(record/'outcome.json'),'exit_code':code,'accepted':outcome['accepted'],'error':outcome.get('error')}))
    return 0 if code==0 and not outcome.get('error') and not outcome.get('preservation_errors') and (outcome['source_unchanged'] or a.action=='cleanup-native-resources') else 1


if __name__=='__main__':raise SystemExit(main())
