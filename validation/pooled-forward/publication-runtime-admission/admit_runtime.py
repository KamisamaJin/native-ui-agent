"""Qualify only the current host for fixed generic pure evaluator replay.

No SDK, Git, network, actual study data, historical JSON rewriting or data
adoption. Existing runtime inventories and original freezes remain untouched.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import sys
import time
import traceback


HERE=Path(__file__).resolve().parent
SOURCE_SHA='22b61e8c21dd7f1725dab8ddab3a524587e195e81bbafa763bc0fcd44efca5df'
GOLDEN_SHA='60fc5c6ebb2fd8697636a6b0c3ff7e9d4e01b9c675f07d4de8b1d999bd50b9a9'
PILLOW_VERSION='11.3.0'


def need(value,message):
    if not value:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def ref(path):
    path=Path(path);raw=path.read_bytes();return {'path':str(path),'sha256':sha(raw),'bytes':len(raw)}


def save(path,value):
    raw=(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n').encode();copy_raw(path,raw);return ref(path)


def copy_raw(path,raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    path.chmod(0o444)


def verify_sources():
    raw=(HERE/'SOURCE-INVENTORY.json').read_bytes();need(sha(raw)==SOURCE_SHA,'Fixed source inventory changed')
    value=json.loads(raw)
    for name,expected in value['files'].items():need(sha((HERE/name).read_bytes())==expected,'Pinned source/golden bytes changed: '+name)
    need(value['golden_manifest_sha256']==GOLDEN_SHA,'Fixed generic evidence identity differs')
    return value


def check_target(target,system=None,version=None):
    system=platform.system() if system is None else system;version=sys.version_info[:2] if version is None else version
    need(target in {'current','linux-py311'},'Explicit current or linux-py311 target required')
    if target=='linux-py311':need(system=='Linux' and tuple(version)==(3,11),'CI target requires actual Linux Python3.11; no Darwin substitution or skip')


def check_pillow(package_version,metadata_version):
    need(package_version==metadata_version==PILLOW_VERSION,'Current-host admission requires installed Pillow11.3.0 package and matching wheel metadata')


def member(value):
    p=PurePosixPath(str(value));need(not p.is_absolute() and str(p)==str(value) and all(v not in {'.','..'} for v in p.parts),'Unsafe installed-wheel member')
    return p


def wheel_kind(value):
    p=member(value);top=p.parts[0]
    if top=='PIL':return 'package'
    if re.fullmatch('[A-Za-z0-9_.-]+[.]libs',top):return 'support'
    if top.lower()=='pillow-11.3.0.dist-info':return 'metadata'
    return None


def stage_runtime(owned):
    import PIL
    dist=importlib.metadata.distribution('Pillow');check_pillow(PIL.__version__,dist.version)
    need(dist.files,'Installed Pillow wheel RECORD is required')
    package=Path(PIL.__file__).resolve().parent;declared={};metadata={};support={};runtime=owned/'vendor/runtime'
    for original in dist.files:
        try:kind=wheel_kind(original)
        except ValueError:
            # Wheel executables outside site-packages are not runtime imports.
            continue
        if kind is None:continue
        rel=member(original)
        if '__pycache__' in rel.parts or str(rel).endswith('.pyc'):continue
        path=Path(dist.locate_file(original));need(path.is_file() and not path.is_symlink(),'Installed wheel member missing or aliased: '+str(original))
        if kind=='package':need(path.resolve().is_relative_to(package),'PIL import does not match installed wheel RECORD')
        raw=path.read_bytes();dest=(owned/'wheel-metadata'/str(rel)) if kind=='metadata' else runtime/str(rel)
        copy_raw(dest,raw);row=ref(dest)
        if kind=='package':declared[str(rel)]=row
        elif kind=='support':support[str(rel)]=row
        else:metadata[str(rel)]=row
    actual={str(p.relative_to(package)) for p in package.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    need(actual=={str(PurePosixPath(k).relative_to('PIL')) for k in declared},'Unrecorded or missing PIL package files; no implicit imports')
    need(any(k.endswith('/WHEEL') for k in metadata) and any(k.endswith('/RECORD') for k in metadata),'Complete installed wheel metadata is required')
    licenses={k:v for k,v in metadata.items() if any(w in k.lower() for w in ['license','copying','notice'])}
    need(licenses and all(row['bytes']>0 for row in licenses.values()),'Full locally installed wheel license texts required')
    return {'root':str(runtime),'files':declared,'support_files':support,'distribution_metadata_files':metadata,'license_files':licenses,
            'interpreter':{'path':sys.executable,'sha256':sha(Path(sys.executable).read_bytes())},'version':sys.version,
            'pillow_version':PIL.__version__,'platform':platform.platform(),'system':platform.system(),'machine':platform.machine(),
            'abi_scope':'New current-host inventory only. Historical Darwin runtime remains distinct; no cross-OS binary substitution.'}


def stage_sources(owned,source):
    # Only a runtime-support inventory extension differs from historical replay;
    # the worker, both backends, generic assets and all23 controls are unchanged.
    copies={'replay_current_host.py':'replay.py','vendor/runner/worker.py':'runner/worker.py',
            'vendor/fixture_utils.py':'fixture_utils.py','vendor/test_replay.py':'test_replay.py',
            'vendor/vendor/resolver.py':'vendor/resolver.py','golden_runner.py':'golden_runner.py'}
    for src,dest in copies.items():copy_raw(owned/dest,(HERE/src).read_bytes())
    for p in sorted((HERE/'vendor/vendor/frozen').rglob('*')):
        if p.is_file():copy_raw(owned/'vendor/frozen'/p.relative_to(HERE/'vendor/vendor/frozen'),p.read_bytes())
    for p in sorted((HERE/'golden').rglob('*')):
        if p.is_file():copy_raw(owned/'golden'/p.relative_to(HERE/'golden'),p.read_bytes())
    copy_raw(owned/'licenses/historical-pillow-11.3.0-LICENSE',(HERE/'vendor/historical-pillow-11.3.0-LICENSE').read_bytes())
    backends={}
    for label,name in [('A','BASELINE-COMMON-FREEZE-6.json'),('B','CANDIDATE-FREEZE-10.json')]:
        root=owned/'vendor/frozen'/label;freeze=json.loads((root/name).read_bytes());files={}
        for p in sorted((root/'scripts').glob('*.py')):
            relative='scripts/'+p.name;row=ref(p);need(row['sha256']==freeze['files'][relative],'Frozen backend source changed');files[relative]=row
        backends[label]={'freeze':ref(root/name),'root':str(root),'files':files,
                         'source_freeze_sha256':source['files']['vendor/vendor/frozen/'+label+'/'+name]}
    return backends


def command(argv,log,timeout=150):
    process=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,check=False,
                           env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    copy_raw(log,process.stdout)
    need(process.returncode==0,'Required qualification failed; retained log: '+str(log))
    lines=[line for line in process.stdout.decode().splitlines() if line.strip()]
    record=json.loads(lines[-1]);path=Path(record['path']);need(ref(path)['sha256']==record['sha256'],'Qualification result pin changed')
    return record,json.loads(path.read_bytes())


def run_admission(output,target):
    output=Path(output).absolute();need(output.is_relative_to(HERE/'HOST') and not output.exists(),'Fresh owned output under publication-runtime-admission/HOST required')
    for p in output.parents:need(not p.is_symlink(),'Symlink in owned output namespace')
    output.mkdir(parents=True,exist_ok=False);started=time.time()
    status={'version':1,'kind':'current-host-generic-replay-runtime-admission','requested_target':target,'started_at_unix':started,
            'host':{'system':platform.system(),'python_version':sys.version,'executable':sys.executable,'machine':platform.machine()},
            'actual_study_data_used':False,'SDK_Git_network_or_delegation_used':False,'historical_inventory_rewritten':False,
            'source_domain_replay':'unsupported','source_responsibility_replay':'unsupported','current_source_delivery_verified':False}
    try:
        source_raw={n:(HERE/n).read_bytes() for n in ['admit_runtime.py','golden_runner.py','test_admission.py','replay_current_host.py']}
        status['source_code_pins']={}
        for name,raw in source_raw.items():
            copy_raw(output/'source-snapshots'/name,raw);status['source_code_pins'][name]=ref(output/'source-snapshots'/name)
        source=verify_sources();check_target(target);owned=output/'owned';owned.mkdir()
        backends=stage_sources(owned,source);runtime=stage_runtime(owned)
        inventory={'version':1,'kind':'externally-pinned-isolated-evaluator-code-inventory','backends':backends,'runtime':runtime,
                   'source_inventory_sha256':SOURCE_SHA,'fixed_generic_fixture_sha256':GOLDEN_SHA,
                   'scope':'NEW current-host runtime byte pins for fixed generic replay only. Not historical ABI, arbitrary-data or actual-study admission.'}
        inventory_ref=save(owned/'CODE-INVENTORY.json',inventory)
        mechanism,mechanism_value=command([sys.executable,'-B',str(HERE/'test_admission.py'),'--output',str(output/'mechanism')],output/'MECHANISM.log')
        golden,golden_value=command([sys.executable,'-B',str(owned/'golden_runner.py'),'--golden',str(owned/'golden'),'--output',str(owned/'HOST/golden')],output/'GOLDEN.log')
        controls,controls_value=command([sys.executable,'-B',str(owned/'test_replay.py')],output/'REPLAY-CONTROLS.log')
        need(mechanism_value['passed'] and golden_value['status']=='verified' and controls_value['passed']
             and controls_value['tests']==23 and controls_value['failures']==controls_value['errors']==0,'Required controls were skipped, changed or failed')
        need(all((HERE/n).read_bytes()==raw for n,raw in source_raw.items()),'Runtime qualification sources changed during execution')
        status.update(status='qualified_generic_current_host',code_inventory=inventory_ref,mechanism_controls=mechanism,
                      fixed_golden_result=golden,replay_controls=controls,replay_control_count=23,
                      fixed_generic_backends=['A','B'],license_files=runtime['license_files'],
                      historical_license=ref(owned/'licenses/historical-pillow-11.3.0-LICENSE'),
                      linux_python311_executed=platform.system()=='Linux' and sys.version_info[:2]==(3,11),
                      scope='Qualification only for the frozen generic fixture and unchanged23 replay/corruption/U controls on this recorded host. No actual-data or unsupported-domain admission.')
    except Exception as exc:
        status.update(status='failed',error={'type':type(exc).__name__,'message':str(exc)},traceback=traceback.format_exc(),
                      linux_python311_executed=False)
    status['finished_at_unix']=time.time()
    result=save(output/'RESULT.json',status);return result,status


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--target',choices=['current','linux-py311'],required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();result,value=run_admission(args.output,args.target)
    print(json.dumps({'path':result['path'],'sha256':result['sha256'],'status':value['status'],'host':value['host'],'linux_python311_executed':value['linux_python311_executed']}))
    return 0 if value['status']=='qualified_generic_current_host' else 1


if __name__=='__main__':raise SystemExit(main())
