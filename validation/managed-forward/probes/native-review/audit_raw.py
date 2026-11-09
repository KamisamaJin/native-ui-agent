#!/usr/bin/env python3
"""Read-only verification of the explicitly supplied native packages."""
import hashlib
import json
from pathlib import Path
import sys
import traceback
import xml.etree.ElementTree as ET
from PIL import Image

ROOT=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill')
BASE=ROOT/'validation/managed-forward'
OUT=BASE/'probes/native-review'
CANDIDATE=BASE/'candidate-v12.1'
sys.path.insert(0,str(CANDIDATE/'scripts'))
import design_contract as d
import action_guard as ag
import native_checks as nc
import acceptance as ac
import execution_plan as xp

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def dump(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n')
def ref(p,note=None):return {'path':str(p.resolve()),'sha256':sha(p),**({'note':note} if note else {})}

readset={}
def remember(p):
    if p.is_file():readset[str(p.resolve())]={'path':str(p.resolve()),'sha256':sha(p),'bytes':p.stat().st_size}

packs=['android-candidate-positive','android-candidate-negative','android-source-feedback','responsibility-negative','zero-sdk-tests','cancel-sdk']
freeze=load(BASE/'CANDIDATE-FREEZE-2.json')
assert sha(BASE/'CANDIDATE-FREEZE-2.json')=='2ee699a9be4a254cdd9f7c035f793f1979b4e779dbfa634d16a69e7db2999e89'
integrity={'portable_packages':[],'prepared_seals':[],'source_reviews':[],'candidate_file_mismatches':[]}
for rel,expected in freeze['files'].items():
    if sha(CANDIDATE/rel)!=expected:integrity['candidate_file_mismatches'].append(rel)
assert not integrity['candidate_file_mismatches']
for pack in packs:
    root=BASE/'evidence/probes'/pack
    for p in root.rglob('*'):
        if p.is_file():remember(p)
    declared=load(root/'portable-sha256.json');checks=[]
    for rel,expected in declared.items():
        p=root/rel;checks.append({'path':str(p),'expected':expected,'actual':sha(p) if p.is_file() else None,'matches':p.is_file() and sha(p)==expected})
    runtime=root/'capture/tool-runtime';runtime_checks=[]
    if runtime.is_dir():
        for p in runtime.rglob('*'):
            if p.is_file():
                rel=str(p.relative_to(runtime));runtime_checks.append({'relative':rel,'matches_candidate':sha(p)==freeze['files'].get(rel),'sha256':sha(p)})
    integrity['portable_packages'].append({'pack':pack,'portable_index':ref(root/'portable-sha256.json'),'all_listed_match':all(c['matches'] for c in checks),'checks':checks,'runtime_matches_candidate':all(c['matches_candidate'] for c in runtime_checks),'runtime_checks':runtime_checks})
for variant in ['prepared','prepared-positive']:
    root=BASE/'probes/native'/variant;seal=load(root/'pre-sdk-seal.json');checks=[]
    for rel,expected in seal['files'].items():
        p=root/rel;remember(p);checks.append({'path':str(p),'matches':sha(p)==expected,'sha256':sha(p)})
    remember(root/'pre-sdk-seal.json')
    integrity['prepared_seals'].append({'variant':variant,'sealed_at_unix':seal['sealed_at_unix'],'all_match':all(c['matches'] for c in checks),'checks':checks})
for p in (BASE/'evidence/probes/production').rglob('*'):
    if p.is_file():remember(p)
for name in ['ObserverBridge.kt','source-actuals.android.json','source-binding.android.json','source-binding-positive.android.json','responsibility-negative.json','zero-sdk-tests/result.json','cancel-sdk/result.json']:
    remember(BASE/'probes/native'/name)
for name in ['source-binding.android.json','source-binding-positive.android.json']:
    binding=load(BASE/'probes/native'/name);p=Path(binding['path']);remember(p)
    integrity['source_reviews'].append({'binding':ref(BASE/'probes/native'/name),'receipt':ref(p),'matches_binding':sha(p)==binding['sha256'],'contents':load(p)})

replays=[];wire=[];image_groups={};image_audit=[]
for pack,prepared in [('android-candidate-positive','prepared-positive'),('android-candidate-negative','prepared')]:
    root=BASE/'evidence/probes'/pack;native=root/'capture/native';fixed=BASE/'probes/native'/prepared/'android'
    config=load(fixed/'config.json');plan=load(fixed/'plan.json');lock=load(fixed/'lock.json');observation=load(native/'observation.json');execution=load(root/'capture/execution.json')
    junit=ET.parse(native/'junit.xml').getroot()
    original_manifest=load(native/'manifest.json');original=load(root/'capture/automatic.json')
    approved_fixtures=load(fixed.parent/'fixtures.json');bridge_sha=sha(native/'sources/ObserverBridge.kt')
    entry={'pack':pack,'junit':{'attributes':junit.attrib,'testcases':[n.attrib for n in junit.findall('testcase')]},'checks':{}}
    entry['checks']['prepared_plan_matches_capture']=sha(fixed/'plan.json')==sha(root/'capture/parent-plan.json')
    entry['checks']['lock_canonical_digest']=d.digest(lock)==config['design_sha256']
    entry['checks']['launch_bridge_matches']=bridge_sha==lock['sources']['reference']['document']['launch']['bridge_sha256']
    try:
        d.verify_generated(plan,lock,config['design_sha256'],'android')
        xp.verify_execution(execution,plan,lock,config['design_sha256'],approved_fixtures,bridge_sha)
        guards=ag.verify_observation(execution['actions'],observation,'android')
        evaluated=nc.evaluate(plan,observation,'android',root=native,observation_sha256=sha(native/'observation.json'),design_lock=lock,design_sha256=config['design_sha256'])
        environment=ac.environment(observation,load(fixed/'environment.json'),'android')
        entry.update(guard_replay=guards,recomputed=evaluated,environment=environment)
        entry['checks']['assertion_statuses_match_original']={r['id']:r['status'] for r in evaluated['assertions']}=={r['id']:r['status'] for r in original['assertions']}
        entry['checks']['all_images_match_manifest']=all((native/rel).is_file() and sha(native/rel)==digest for rel,digest in original_manifest['image_hashes'].items())
        entry['checks']['source_before_after_equal']=load(root/'capture/source-before.json')==load(root/'capture/source-after.json')
        cycle=load(root/'cycle.json');entry['checks']['cycle_pins_actual_resources']=cycle.get('resources_sha256')==sha(root/'resources.json')
    except Exception as error:entry['replay_error']={'type':type(error).__name__,'error':str(error),'traceback':traceback.format_exc()}
    replays.append(entry)
    steps=[]
    for i,s in enumerate(observation['steps']):
        before=s.get('dispatch',{}).get('binding_before',s.get('guard',{}).get('binding',{}));after=s.get('binding_after',{})
        index=s.get('immediate_after',s.get('snapshot'));snapshot=observation['snapshots'][index] if type(index)is int and 0<=index<len(observation['snapshots']) else None
        targets=[]
        if snapshot:
            for n in snapshot.get('nodes',[]):
                if n.get('identifier','').startswith('counter.'):
                    targets.append({k:n.get(k) for k in ['identifier','node_id','parent_id','label','enabled','clickable','role']})
        steps.append({'index':i,'state':s.get('state_id'),'type':s.get('action',{}).get('type'),'target':s.get('action',{}).get('target'),
            'outcome':s.get('outcome'),'dispatch':s.get('dispatch'),'guard':s.get('guard'),'binding_after':after,'callback_delta':s.get('callback_delta'),
            'same_instance':bool(before.get('instance')) and before.get('instance')==after.get('instance'),'immediate_snapshot_index':index,'native_target_facts':targets})
    wire.append({'pack':pack,'configuration':observation.get('configuration'),'events':observation.get('events'),'steps':steps,
        'snapshot_bindings':[{'index':i,'state':s.get('state_id'),'binding':s.get('binding'),'capture_consistent':s.get('capture_consistent'),'screenshot':s.get('screenshot'),
            'screenshot_pixels':s.get('screenshot_pixels'),'native_viewport_px':s.get('native_viewport_px'),'logical_viewport_dp':s.get('logical_viewport_dp')} for i,s in enumerate(observation['snapshots'])]})
for pack in ['android-candidate-positive','android-candidate-negative','cancel-sdk']:
    for p in sorted((BASE/'evidence/probes'/pack).rglob('*.png')):
        digest=sha(p);image_groups.setdefault(digest,[]).append(str(p))
        result={'file':ref(p)}
        try:
            with Image.open(p) as image:result.update(size=list(image.size),mode=image.mode);image.verify()
            with Image.open(p) as image:image.load()
            result['fully_decodable']=True
        except Exception as error:result.update(fully_decodable=False,error_type=type(error).__name__,error=str(error))
        image_audit.append(result)
dump('integrity.json',integrity);dump('recomputed-checks.json',replays);dump('native-wire.json',wire);dump('image-audit.json',{'files':image_audit,'unique_groups':image_groups,
    'visually_reviewed_valid_groups':['4237b1945ac0cc9111927dd9db5cba4208b8b4fa962caf258157e08b13c0111e','b1862c8b1594e860f69799820adb87b06049d07b88947792cd0ee0cda4d2ab85','9a1c9bffd53586f4cf28dbf5f130008ac05734fc9add5b65ecbeb6b77cc38b9e'],
    'visual_observation':'Tally 0, then 1, then 8 are visible; Count and Left/Right remain visible. Disabled appearance is a visual observation only; enabled state comes from semantic facts. Cancel PNG could not be displayed and is independently decode-tested here.'})
dump('readset.json',{'files':list(readset.values()),'scope':'Only the explicitly supplied native packages, independent prepared/prepared-positive contracts, source observations/bindings, production snapshots and frozen v12.1 validators. No business validation task was read.'})
print(json.dumps({'portable_integrity':[(p['pack'],p['all_listed_match'],p['runtime_matches_candidate']) for p in integrity['portable_packages']],
    'replays':[{'pack':r['pack'],'checks':r['checks'],'counts':r.get('recomputed',{}).get('counts'),'environment':r.get('environment',{}).get('status'),'error':r.get('replay_error')} for r in replays],
    'invalid_images':[r for r in image_audit if not r['fully_decodable']],'readset_files':len(readset)},ensure_ascii=False))
