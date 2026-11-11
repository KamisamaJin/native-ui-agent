"""Isolated unchanged-backend evaluator. JSON stdin/stdout; never SDK or writes."""
import base64
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys


sys.dont_write_bytecode=True


def need(value,message):
    if not value:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main(job):
    backend=Path(job['backend_root']).resolve();runtime=Path(job['runtime_root']).resolve()
    roots=[backend,runtime]
    for row in job['code_files']:
        p=Path(row['physical_path']);need(p.is_absolute() and not p.is_symlink() and any(p.is_relative_to(r) for r in roots),'Code file escapes pinned inventory')
        raw=p.read_bytes();need(sha(raw)==row['sha256'] and len(raw)==row['bytes'],'Pinned backend/runtime bytes changed in child')
    sys.path[:0]=[str(backend),str(runtime)]
    # Imports run in a fresh -I -S process, with no user site/PYTHONPATH/CWD.
    import design_contract as design
    import native_checks
    import review_contract
    import PIL.Image
    need(10<=int(PIL.__version__.split('.')[0])<13,'Pinned Pillow runtime violates frozen backend requirements')
    for name in ['design_contract','native_checks','review_contract','native_pixels','observation_contract']:
        module=sys.modules[name];need(Path(module.__file__).resolve().parent==backend,'A/B or external backend import contamination')
    loaded={k:Path(v.__file__).resolve() for k,v in sys.modules.items() if getattr(v,'__file__',None)}
    for name,p in loaded.items():
        if name=='PIL' or name.startswith('PIL.'):
            need(p.is_relative_to(runtime),'Unpinned Pillow import')
    def decode(name):
        row=job['inputs'][name];raw=base64.b64decode(row['raw_base64'],validate=True)
        need(sha(raw)==row['sha256'],'Original input bytes changed in IPC')
        return design.strict_json(raw.decode())
    lock,policy=decode('lock'),decode('policy');lock_sha=design.digest(lock);policy_sha=design.digest(policy)
    need(lock_sha==job['lock_canonical_sha256'] and policy_sha==job['policy_canonical_sha256'],'Trusted canonical contract/policy pin differs')
    if job['mode']=='prepare_synthetic_fixture':
        need(job.get('synthetic_only') is True,'Fixture preparation is synthetic-only')
        plan,_=design.compile_contract(lock,lock_sha,'neutral','android',decode('bindings'),decode('actions'))
        return {'plan':plan,'catalog':review_contract.catalog(plan,lock,lock_sha,policy,policy_sha,'android')}
    plan,observation,submission=decode('plan'),decode('observation'),decode('submission')
    native_root=Path(job['native_root']).resolve();capture_root=Path(job['capture_root']).resolve()
    need(native_root.parent==capture_root and native_root.name=='native','Verified native/capture directory layout differs')
    # Known frozen domain verification resolves embedded original production
    # paths. Such packets are rejected by the parent before reaching this child.
    need(not any((native_root/n).exists() for n in ['coverage-domain-input.json','coverage-domain-binding.json'])
         and not (capture_root/'coverage-domain-prepared.json').exists(),'Unsupported original production-domain replay')
    def audit(event,args):
        if event in {'subprocess.Popen','os.system','os.exec','os.posix_spawn','socket.__new__','os.remove','os.rename','os.mkdir','os.rmdir','os.chmod','os.chown','os.link','os.symlink'}:
            raise RuntimeError('Pure replay prohibited effect: '+event)
        if event=='open':
            file,mode,flags=args
            if isinstance(file,int):return
            if any(x in str(mode) for x in ['w','a','x','+']) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
                raise RuntimeError('Pure replay prohibited a write')
            p=Path(file).absolute()
            allowed=[capture_root,backend,runtime,Path(sys.base_prefix).resolve()]
            need(any(p==r or p.is_relative_to(r) for r in allowed),'Replay attempted a file outside restored evidence/code/runtime')
    sys.addaudithook(audit)
    catalog=review_contract.catalog(plan,lock,lock_sha,policy,policy_sha,job['platform'])
    manual=review_contract.bind(plan,lock,lock_sha,policy,policy_sha,observation,job['inputs']['observation']['sha256'],
                                native_root,submission,job['platform'])
    report=native_checks.evaluate(plan,observation,job['platform'],manual,native_root,job['inputs']['observation']['sha256'],
                                  lock,lock_sha,policy,policy_sha)
    need(all(Path(v.__file__).resolve().parent==backend for name,v in sys.modules.items()
             if name in {'design_contract','native_checks','review_contract','native_pixels','observation_contract','action_guard','scroll_coverage','coverage_domain','native_geometry'}),
         'Backend import escaped the selected isolated inventory')
    return {'catalog':catalog,'manual':manual,'report':report,'backend_imports_isolated':True}


if __name__=='__main__':
    try:
        result=main(json.loads(sys.stdin.read()));print(json.dumps({'status':'replayed','result':result},ensure_ascii=False,allow_nan=False))
    except Exception as exc:
        print(json.dumps({'status':'failed','error':{'type':type(exc).__name__,'message':str(exc)}},ensure_ascii=False,allow_nan=False))
        raise SystemExit(1)
