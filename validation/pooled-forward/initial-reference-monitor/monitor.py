#!/usr/bin/env python3
"""Supplemental common initial-reference ownership/union sampling only.

Keeps the original spec/envelope/SUT unchanged. No SDK forwarding or deletion.
Run as its own process; the frozen envelope's halt gate remains the cancellation
path. Caller must admit all public seals and preserve canonical initial bytes.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import time
import traceback


ROOT = Path(__file__).resolve().parent.parent


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_bytes())
def save(p,value):
    with Path(p).open('x') as f: json.dump(value,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())


def absolute(value):
    if not isinstance(value,str) or not value.startswith('/') or '\x00' in value or str(PurePosixPath(value))!=value or any(v in {'.','..'} or v.casefold()=='.git' for v in value.split('/')):
        raise ValueError('Canonical absolute path required')
    return Path(value)


def dependencies():
    pins=load(Path(__file__).with_name('FROZEN-DEPENDENCIES.json'))
    for rel,want in pins['files'].items():
        if Path(rel).is_absolute() or '..' in Path(rel).parts or sha(ROOT/rel)!=want: raise ValueError('Frozen monitor dependency differs: '+rel)
    sys.path.insert(0,str(ROOT))
    spec=importlib.util.spec_from_file_location('_frozen_initial_reference_envelope',ROOT/'native_envelope.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    if Path(module.rm.__file__).resolve()!=ROOT/'baseline-v12.6/scripts/resource_manager.py' or Path(module.measure.__file__).resolve()!=ROOT/'measure.py':
        raise ValueError('Run supplemental monitor in a fresh process with exact frozen modules')
    return module,pins


def extend(original,declaration):
    if set(declaration)!={'version','kind','owned_root','resource_journals'} or type(declaration['version']) is not int or declaration['version']!=1 or declaration['kind']!='common-initial-reference-meter-extension':
        raise ValueError('Exact initial-reference resource declaration required')
    root=absolute(declaration['owned_root']); extras=declaration['resource_journals']
    if not isinstance(extras,list) or not extras or len(extras)!=len(set(extras)): raise ValueError('Unique explicit initial-reference journals required')
    existing=[j for group in original['groups'].values() for j in group.get('resource_journals',[])]
    if len(existing)!=len(set(existing)): raise ValueError('Original configured journal must be counted once')
    for raw in extras:
        p=absolute(raw)
        if not p.is_relative_to(root) or p==root or p.name!='journal.json' or raw in existing: raise ValueError('New journal must be distinct under the declared initial-reference root')
    if 'whole_study' not in original['groups']: raise ValueError('Frozen whole_study group required')
    result=copy.deepcopy(original)
    result['groups']['whole_study']['resource_journals']=list(result['groups']['whole_study'].get('resource_journals',[]))+extras
    return result


def journals(spec):
    return [Path(j) for group in spec['groups'].values() for j in group.get('resource_journals',[])]


def slots(spec,validator):
    validator(spec)  # frozen exact token/name/root-inode checks, including intents
    return sum(len(load(p).get('devices',[])) for p in journals(spec) if p.is_file())


def idle(original,extended,validator):
    old=slots(original,validator); all_slots=slots(extended,validator)
    if old or all_slots: raise ValueError('Initial reference may start only after every original and supplemental device slot is positively closed')
    return {'original_slots':old,'supplemental_slots':all_slots-old,'whole_study_slots':all_slots,'all_clear':True}


def signal_halt(record,error,last=None):
    value={'at_unix':time.time(),'source':'initial-reference-supplement','error':error,'last_sample':last,'scope':'Common safety/measurement only; original envelope halt gate, no guessed process or device cleanup'}
    save(record/('HALT-'+str(time.time_ns())+'.json'),value)
    target=ROOT/'operators/RESOURCE-HALT.json'
    try: save(target,value)
    except FileExistsError: pass


def preflight(record):
    module,_pins=dependencies(); request=load(record/'REQUEST.json'); ready=load(record/'READY.json')
    if (record/'CLOSED.json').exists() or (ROOT/'operators/RESOURCE-HALT.json').exists(): raise ValueError('Monitor is closed or the original study is halted')
    for p,expected in request['input_files'].items():
        if sha(p)!=expected: raise ValueError('Monitor input changed after READY: '+p)
    if sha(__file__)!=request['monitor_sha256']: raise ValueError('Monitor source changed')
    actual=module.rm.Resources.process_identity(ready['pid'])
    if not module.rm.Resources.same_process(ready['process_identity'],actual,request['token'],ready['pid']): raise ValueError('Monitor process birth/group/token is not live; use process-visible preflight')
    original=load(request['original_spec']); extended=load(record/'EXTENDED-SPEC.json')
    if extended!=extend(original,load(request['declaration'])): raise ValueError('Supplemental spec is not the exact original plus declared journals')
    result=idle(original,extended,module.owned_device_paths)
    return {**result,'ready_at_unix':ready['at_unix'],'cutover_first_sample_started_at_unix':ready['first_union_sample']['started_at_unix'],'cutover_ready_at_unix':ready['at_unix'],'sdk_executed':False}


def run(args):
    module,pins=dependencies(); record=absolute(str(args.record)); declaration=absolute(str(args.declaration))
    spec_path=ROOT/'operators/whole-study-meter-spec-v2.json'
    if not re.fullmatch('[0-9a-f]{32}',args.token) or not 0<args.max_seconds<=43200: raise ValueError('Opaque owner token and bounded monitor lifetime required')
    if record.exists(): raise ValueError('Fresh supplemental monitor record required')
    record.mkdir(parents=True)
    original=load(spec_path); extended=extend(original,load(declaration)); before=idle(original,extended,module.owned_device_paths)
    if (ROOT/'operators/RESOURCE-HALT.json').exists(): raise ValueError('Original whole-study halt already exists')
    save(record/'EXTENDED-SPEC.json',extended)
    request={'version':1,'started_at_unix':time.time(),'token':args.token,'original_spec':str(spec_path),'declaration':str(declaration),'monitor_sha256':sha(__file__),'max_seconds':args.max_seconds,'input_files':{str(spec_path):sha(spec_path),str(declaration):sha(declaration),str(record/'EXTENDED-SPEC.json'):sha(record/'EXTENDED-SPEC.json'),str(Path(__file__).with_name('FROZEN-DEPENDENCIES.json')):sha(Path(__file__).with_name('FROZEN-DEPENDENCIES.json'))},'frozen_dependencies':pins,'initial_idle':before,'scope':'Supplemental common initial-reference safety/union sampling; no treatment or own-public-delivery credit, no original spec/envelope/SUT edits'}
    save(record/'REQUEST.json',request)
    if os.getpgrp()!=os.getpid(): os.setsid()
    identity=module.rm.Resources.process_identity(os.getpid())
    if not identity or identity['pgid']!=os.getpid() or args.token not in identity['command']: raise ValueError('Positive monitor session/birth/token identity unavailable')
    class CheckedMeter(module.measure.Meter):
        def _sample(self):
            module.owned_device_paths(self.spec)
            return super()._sample()
    started=time.monotonic(); error=None
    try:
        with CheckedMeter(extended,record/'union.jsonl') as meter:
            save(record/'READY.json',{'version':1,'pid':os.getpid(),'process_identity':identity,'at_unix':time.time(),'first_union_sample':meter.samples[0],'original_spec_sha256':sha(spec_path),'extended_spec_sha256':sha(record/'EXTENDED-SPEC.json'),'scope':'Full first extended union sample completed before any supplemental reference SDK admission'})
            while not (record/'STOP').exists():
                if meter.error or any(s['budget_exceeded'] for s in meter.samples[-1:]):
                    error=meter.error or {'type':'BudgetExceeded','message':'Frozen whole-study byte/free-space budget exceeded'}; signal_halt(record,error,meter.samples[-1] if meter.samples else None);break
                if time.monotonic()-started>=args.max_seconds:
                    error={'type':'MonitorLifetimeExceeded','message':'Bounded supplemental monitoring expired'};signal_halt(record,error,meter.samples[-1]);break
                time.sleep(.5)
        closure=idle(original,extended,module.owned_device_paths)
    except BaseException as exc:
        error={'type':type(exc).__name__,'message':str(exc)};save(record/'FAILURE.json',{'error':error,'traceback':traceback.format_exc(),'at_unix':time.time()});signal_halt(record,error);closure=None
    save(record/'CLOSED.json',{'finished_at_unix':time.time(),'status':'closed' if error is None else 'failed','error':error,'positive_idle':closure,'scope':'Supplemental resources must be closed before returning measurement coverage to the unchanged original meter; no cleanup was performed by this observer'})
    return 1 if error else 0


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--record',type=Path,required=True);p.add_argument('--declaration',type=Path);p.add_argument('--token');p.add_argument('--max-seconds',type=float,default=14400);p.add_argument('--preflight',action='store_true');a=p.parse_args()
    if a.preflight: print(json.dumps(preflight(a.record)));return 0
    if not a.declaration or not a.token: p.error('--declaration and --token are required for monitoring')
    try: return run(a)
    except BaseException as exc:
        if a.record.is_dir() and not (a.record/'CLOSED.json').exists():
            save(a.record/('ADMISSION-FAILED-'+str(time.time_ns())+'.json'),{'at_unix':time.time(),'error':{'type':type(exc).__name__,'message':str(exc)},'traceback':traceback.format_exc(),'scope':'No SDK forwarded. Failure before READY does not grant an initial-reference window.'})
        raise


if __name__=='__main__': raise SystemExit(main())
