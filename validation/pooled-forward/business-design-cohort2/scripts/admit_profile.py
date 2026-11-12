#!/usr/bin/env python3
"""Require the actual platform's exact sealed design projection before any SDK use.

This integration guard adds no observation items and changes no frozen tool.
"""
import argparse, copy, hashlib, json, sys
from pathlib import Path

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def digest(x):return hashlib.sha256(canonical(x)).hexdigest()
def load(p):return json.loads(Path(p).read_text())

def verify(root, approval, approval_sha, actual_platform, profile_id, config, *, runtime=False):
    root=Path(root).resolve()
    if digest(approval)!=approval_sha:raise ValueError('Approval mapping changed from independently pinned canonical identity')
    if actual_platform not in {'ios','android'}:raise ValueError('Actual native platform is required')
    if profile_id not in approval['profiles']:raise ValueError('Unapproved profile')
    p=approval['profiles'][profile_id]
    if p['intended_platform']!=actual_platform or config.get('platform')!=actual_platform:raise ValueError('Actual platform must match the intended-platform lock; opposite expression slots are schema-only')
    if p['opposite_slot']!='schema_only_forbidden_runtime':raise ValueError('Missing opposite-slot prohibition')
    for field in ['design_sha256','policy_sha256','routes_sha256','environment_sha256']:
        if config.get(field)!=p[field]:raise ValueError('Wrong pinned '+field)
    for field in ['design_lock','plan','policy','routes','environment','fixtures','bridge']:
        actual=Path(config[field]).resolve();expected=(root/p['paths'][field]).resolve()
        if actual!=expected:raise ValueError('Wrong exact '+field+' path')
        observed=hashlib.sha256(actual.read_bytes()).hexdigest() if field=='bridge' else digest(load(actual))
        if observed!=p['hashes'][field]:raise ValueError('Changed exact '+field+' identity')
    plan=load(config['plan']);lock=load(config['design_lock'])
    if plan['design_contract']['platform']!=actual_platform or plan['design_contract']['scenario']!=p['scenario'] or plan['design_contract']['lock_sha256']!=p['design_sha256']:raise ValueError('Plan has another platform/scenario/lock')
    if lock['sources']['reference']['document']['platform_scope']['intended_platform']!=actual_platform:raise ValueError('Opposite lock projection is not executable')
    for field in ['launch_ref','responsibility_ref']:
        if config.get(field)!=p[field]:raise ValueError('Wrong '+field)
    launch=lock['sources']['launch']['document'][actual_platform]
    if launch!={'platform':actual_platform,'scenario':p['scenario'],'fixtures_sha256':p['hashes']['fixtures'],'bridge_sha256':p['hashes']['bridge']}:raise ValueError('Sealed launch does not bind this fixture/bridge/platform/scenario')
    if runtime:
        if config.get('purpose')=='pure_preimplementation_capability_only':raise ValueError('Pure placeholders cannot launch native work; bind actual source subjects first')
        paths=config['source_roots']+[v for paths in config['evidence_subjects'].values() for v in paths]
        if any('pure-subjects' in Path(v).parts for v in paths):raise ValueError('Capability placeholder cannot serve as actual production/integration evidence')
        if not config.get('native_options'):raise ValueError('Actual native host options required')
    return {'status':'admitted_profile','profile_id':profile_id,'actual_platform':actual_platform,'design_sha256':p['design_sha256'],'plan_sha256':p['hashes']['plan'],'pure_only':not runtime,'source_approved':False,'native_executed':False,'scope':'Exact intended-platform mapping/launch identity only; source and behavior remain unassessed.'}

def main():
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--approval',type=Path,required=True);a.add_argument('--approval-sha256',required=True);a.add_argument('--platform',choices=['ios','android'],required=True);a.add_argument('--profile-id',required=True);a.add_argument('--config',type=Path,required=True);a.add_argument('--runtime',action='store_true');v=a.parse_args()
    print(json.dumps(verify(v.root,load(v.approval),v.approval_sha256,v.platform,v.profile_id,load(v.config),runtime=v.runtime)))
if __name__=='__main__':main()
