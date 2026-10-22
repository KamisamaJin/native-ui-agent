#!/usr/bin/env python3
"""Immutable source capsules and cohort-authorized native acquisitions."""
import argparse,concurrent.futures,hashlib,json,os,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]
sys.path.insert(0,str(REPO/'native-ui-agent/scripts'))
import cohort_gate as gate
JAVA='/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home'
SDK='/Users/rex/Library/Android/sdk';DEV='/Applications/Xcode.app/Contents/Developer'
ROOTS=['alerttoast/Sources','reply/Reply/app/src/main']
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def fingerprint(w):return {str(p.relative_to(w)):sha(p)for rel in ROOTS for p in sorted((w/rel).rglob('*'))if p.is_file()}
def capsule(w,out):
    assert not out.exists();out.mkdir(parents=True);files=fingerprint(w)
    for rel in files:
        dst=out/'source'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(w/rel,dst)
    licenses={}
    for repo in ['reply','alerttoast']:
        for name in ['LICENSE','LICENSE.md','LICENSE.txt','NOTICE']:
            p=w/repo/name
            if p.is_file():
                dst=out/'licenses'/(repo+'-'+name);dst.parent.mkdir(exist_ok=True);shutil.copy2(p,dst);licenses[str(dst.relative_to(out))]=sha(dst)
    save(out/'seal.json',{'sealedAtUTC':utc(),'sealedAtUnix':time.time(),'files':files,'upstreamLicenses':licenses})
def restore(capsule,w):
    assert w.resolve().is_relative_to((R/'cache').resolve())
    seal=read(capsule/'seal.json')
    for rel,h in seal['files'].items():assert sha(capsule/'source'/rel)==h
    for rel in ROOTS:
        if(w/rel).exists():shutil.rmtree(w/rel)
    for rel in seal['files']:
        dst=w/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(capsule/'source'/rel,dst)
    assert fingerprint(w)==seal['files']
def archive(source,destination):
    assert not destination.exists()
    subprocess.run([sys.executable,'-B',str(REPO/'validation/dispatch-forward/helpers/portable.py'),str(source),str(destination)],check=True)
def stage_binds(stage,path):
    relative=str(path.resolve().relative_to(R));wanted=sha(path)
    seen=set()
    def walk(key):
        if key in seen:return False
        seen.add(key);proof=read(R/'gates'/(key+'.json')) # authorize already verified this prerequisite graph
        if any(files.get(relative)==wanted for files in proof['members'].values()):return True
        return any(walk(parent)for parent in proof['prerequisites'])
    assert walk(stage),'Launch artifact is outside sealed prerequisite graph: '+relative
def collect(a):
    # Required complete cohort and live workspace are verified before creating
    # any SDK project/process. Every command gets a fresh launch ticket as well.
    ticket=gate.authorize(R/'gates',a.required_stage,R)
    expected_stage={'own-D0':'d0-sources','own-FINAL':'final-sources','common-D0':'d0-sources','common-FINAL':'hidden-inputs','paired-D0':'own-final'}[a.phase]
    assert a.required_stage==expected_stage,'Phase requires its exact cohort barrier'
    stage_binds(a.required_stage,a.capsule/'seal.json')
    w=a.workspace.resolve();original=fingerprint(w);source=read(a.capsule/'seal.json')
    assert original==source['files'],'Live source differs from sealed capsule'
    out=a.output.resolve();assert not out.exists();out.mkdir(parents=True);started=time.time()
    shutil.copy2(Path(__file__),out/'operator-source.py')
    save(out/'started.json',{'startedAtUTC':utc(),'startedAtUnix':started,'source':original,'tool':a.tool,'phase':a.phase,'authorization':ticket,'sourceSealSHA256':sha(a.capsule/'seal.json'),'operatorSHA256':sha(out/'operator-source.py')})
    def platform_run(platform):
        dest=out/platform;dest.mkdir();rows=[]
        bridge=a.bridges/('Bridge.swift'if platform=='ios'else'ObserverBridge.kt')
        for case in sorted(p for p in a.inputs.iterdir()if p.is_dir()and(p/'fixtures.json').is_file()and(not a.only_case or p.name in a.only_case)):
            assert not case.name.startswith('H')or a.phase=='common-FINAL','Hidden acquisition forbidden before public endpoints'
            actions=case/('actions.'+platform+'.json')
            if not actions.is_file():actions=case/'actions.json'
            if a.own_plans:actions=a.own_plans/case.name/platform/'actions.json'
            for path in [case/'fixtures.json',actions,bridge]:stage_binds(a.required_stage,path)
            assert fingerprint(w)==original,'Source changed before SDK launch'
            receipt=gate.authorize(R/'gates',a.required_stage,R)
            cmd=[sys.executable,'-B',str(R/a.tool/'scripts'/f'{platform}_observe.py'),'run','--bridge',str(bridge.resolve()),'--fixtures',str((case/'fixtures.json').resolve()),'--actions',str(actions.resolve()),'--output',str((dest/case.name).resolve())]
            if platform=='ios':cmd+=['--package',str((w/'alerttoast').resolve()),'--simulator',a.simulator,'--developer-dir',DEV,'--build-cache',str((w/'ios-build-cache').resolve())]
            else:cmd+=['--project',str((w/'reply/Reply').resolve()),'--java-home',JAVA,'--android-sdk',SDK]
            row={'case':case.name,'platform':platform,'argv':cmd,'startedAtUTC':utc(),'startedAtUnix':time.time(),'inputHashes':{'fixtures.json':sha(case/'fixtures.json'),'actions.json':sha(actions),'bridge':sha(bridge)},'authorization':receipt,'sourceSealSHA256':sha(a.capsule/'seal.json')}
            save(dest/(case.name+'-command.json'),row)
            with(dest/(case.name+'-wrapper.log')).open('w')as stream:code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,DEVELOPER_DIR=DEV,PYTHONDONTWRITEBYTECODE='1')).returncode
            row.update(exitCode=code,finishedAtUTC=utc(),finishedAtUnix=time.time());row['wallSeconds']=row['finishedAtUnix']-row['startedAtUnix'];save(dest/(case.name+'-command.json'),row);rows.append(row)
            assert fingerprint(w)==original,'Source changed during SDK collection'
            print(json.dumps({'platform':platform,'case':case.name,'exitCode':code,'wallSeconds':row['wallSeconds']}),flush=True)
        save(dest/'corpus.json',{'phase':a.phase,'platform':platform,'source':original,'tool':a.tool,'runs':rows,'finishedAtUTC':utc(),'finishedAtUnix':time.time()});return platform,rows
    with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:results=dict(pool.map(platform_run,a.only_platform or ['ios','android']))
    save(out/'corpus.json',{'phase':a.phase,'source':original,'tool':a.tool,'startedAtUnix':started,'finishedAtUnix':time.time(),'platformRuns':results,'slots':{'ios':1,'android':1},'requiredStage':a.required_stage})
    if a.archive:
        archive(out,a.archive);save(a.archive/'corpus-seal.json',{'sealedAtUTC':utc(),'sealedAtUnix':time.time(),'producerFinishedAtUnix':read(out/'corpus.json')['finishedAtUnix'],'source':original,'portableManifestSHA256':sha(a.archive/'portable-sha256.json')})
def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('capsule');s.add_argument('workspace',type=Path);s.add_argument('output',type=Path)
    s=sub.add_parser('restore');s.add_argument('capsule',type=Path);s.add_argument('workspace',type=Path)
    s=sub.add_parser('collect');s.add_argument('--workspace',type=Path,required=True);s.add_argument('--capsule',type=Path,required=True);s.add_argument('--required-stage',required=True);s.add_argument('--tool',choices=['baseline-v7','candidate-v8'],required=True);s.add_argument('--inputs',type=Path,required=True);s.add_argument('--bridges',type=Path,required=True);s.add_argument('--simulator',required=True);s.add_argument('--output',type=Path,required=True);s.add_argument('--archive',type=Path);s.add_argument('--phase',choices=['own-D0','own-FINAL','common-D0','common-FINAL','paired-D0'],required=True);s.add_argument('--own-plans',type=Path);s.add_argument('--only-platform',action='append',choices=['ios','android']);s.add_argument('--only-case',action='append')
    a=p.parse_args()
    if a.command=='capsule':capsule(a.workspace.resolve(),a.output.resolve())
    elif a.command=='restore':restore(a.capsule.resolve(),a.workspace.resolve())
    else:collect(a)
if __name__=='__main__':main()
