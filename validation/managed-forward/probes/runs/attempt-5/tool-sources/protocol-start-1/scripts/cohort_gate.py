#!/usr/bin/env python3
"""Fail-closed cohort barriers for staged multi-candidate validation.

This binds immutable artifacts and complete membership before a stage launches.
It is a procedural guard, not a secure sandbox against direct SDK execution.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import time


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def name(value):
    if not isinstance(value,str)or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',value):
        raise ValueError('Safe explicit stage/member name required')
    return value


def config(root):
    path=Path(root)/'config.json';value=load(path)
    if value.get('version')!=1 or not value.get('stages'):raise ValueError('Version1 stage graph required')
    stages=value['stages']
    for key,spec in stages.items():
        name(key);members=spec.get('members');required=spec.get('requires',[])
        if not isinstance(members,list)or not members or len(members)!=len(set(members)):raise ValueError('Exact nonempty unique cohort membership required')
        for member in members:name(member)
        if not isinstance(required,list)or len(required)!=len(set(required))or any(p not in stages for p in required):raise ValueError('Known unique prerequisites required')
    def visit(key,stack):
        if key in stack:raise ValueError('Cyclic stage graph')
        for parent in stages[key].get('requires',[]):visit(parent,stack+[key])
    for key in stages:visit(key,[])
    return value,digest(path)


def artifact(root,relative):
    if not isinstance(relative,str)or not relative or Path(relative).is_absolute():raise ValueError('Artifact path must be relative to artifact_root')
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve())or not path.is_file():raise ValueError('Artifact missing or escapes root: '+relative)
    return path


def verify(registry,stage,artifact_root=None):
    registry=Path(registry);spec,config_sha=config(registry);name(stage)
    if stage not in spec['stages']:raise ValueError('Unknown stage')
    root=Path(artifact_root or spec['artifact_root']).resolve();path=registry/(stage+'.json')
    if not path.is_file():raise ValueError('Required complete cohort seal missing: '+stage)
    seal=load(path);definition=spec['stages'][stage]
    if seal.get('config_sha256')!=config_sha or seal.get('stage')!=stage:raise ValueError('Stage/config binding changed')
    if set(seal.get('members',{}))!=set(definition['members']):raise ValueError('Incomplete cohort seal')
    parents=definition.get('requires',[])
    if set(seal.get('prerequisites',{}))!=set(parents):raise ValueError('Prerequisite set changed')
    for parent in parents:
        previous=verify(registry,parent,root)
        if seal['prerequisites'][parent]!=digest(registry/(parent+'.json'))or previous['sealedAtUnix']>seal['sealedAtUnix']:raise ValueError('Upstream seal changed or stage order invalid')
    if type(seal.get('sealedAtUnix'))not in(int,float)or seal['sealedAtUnix']>time.time()+1:raise ValueError('Invalid seal time')
    for files in seal['members'].values():
        if not isinstance(files,dict)or not files:raise ValueError('Empty member proof')
        for relative,wanted in files.items():
            if digest(artifact(root,relative))!=wanted:raise ValueError('Sealed artifact changed: '+relative)
    return seal


def seal(registry,stage,members,artifact_root=None):
    registry=Path(registry);spec,config_sha=config(registry);name(stage)
    if stage not in spec['stages']:raise ValueError('Unknown stage')
    definition=spec['stages'][stage];root=Path(artifact_root or spec['artifact_root']).resolve()
    if not isinstance(members,dict)or set(members)!=set(definition['members']):raise ValueError('Every configured cohort member must seal together')
    prerequisites={}
    for previous in definition.get('requires',[]):
        verify(registry,previous,root);prerequisites[previous]=digest(registry/(previous+'.json'))
    manifests={}
    for member,files in members.items():
        if not isinstance(files,list)or not files or len(files)!=len(set(files)):raise ValueError('Nonempty unique member files required')
        manifests[member]={relative:digest(artifact(root,relative))for relative in files}
    result={'version':1,'stage':stage,'config_sha256':config_sha,'sealedAtUnix':time.time(),'prerequisites':prerequisites,'members':manifests}
    path=registry/(stage+'.json');payload=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
    with os.fdopen(fd,'wb')as stream:stream.write(payload);stream.flush();os.fsync(stream.fileno())
    verify(registry,stage,root)
    return result


def authorize(registry,stage,artifact_root=None):
    registry=Path(registry);proof=verify(registry,stage,artifact_root)
    return {'requiredStage':stage,'cohortMembers':sorted(proof['members']),
            'stageSealSHA256':digest(registry/(stage+'.json')),'configSHA256':proof['config_sha256'],
            'authorizedAtUnix':time.time(),'scope':'Complete cohort artifact proof before launch; caller must also verify actual workspace source against capsule.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['seal','authorize','verify']);p.add_argument('--registry',type=Path,required=True);p.add_argument('--stage',required=True);p.add_argument('--artifact-root',type=Path);p.add_argument('--members',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    result=seal(a.registry,a.stage,load(a.members),a.artifact_root)if a.command=='seal'else authorize(a.registry,a.stage,a.artifact_root)if a.command=='authorize'else verify(a.registry,a.stage,a.artifact_root)
    if a.output:
        with a.output.open('x')as stream:stream.write(json.dumps(result,indent=2)+'\n')
    else:print(json.dumps(result,indent=2))
if __name__=='__main__':main()
