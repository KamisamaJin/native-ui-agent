#!/usr/bin/env python3
"""Equal common build preflight for both builders; no rendering or app launch."""
import argparse,hashlib,importlib.util,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--bridge',type=Path);p.add_argument('--platform',choices=['ios','android'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists();a.output.mkdir(parents=True)
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer',JAVA_HOME='/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home',ANDROID_HOME='/Users/rex/Library/Android/sdk')
if a.platform=='ios':
 assert a.bridge and a.bridge.is_file()
 path=R/'candidate-v5/scripts/ios_observe.py';spec=importlib.util.spec_from_file_location('common_ios_compiler',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 project=module.generate_project(a.output/'project',a.bridge.resolve(),(a.workspace/'alerttoast').resolve())
 cmd=['xcodebuild','build-for-testing','-project',str(project.resolve()),'-scheme','Observer','-configuration','Debug','-sdk','iphonesimulator','-destination','generic/platform=iOS Simulator','-derivedDataPath',str((a.output/'DerivedData').resolve()),'CODE_SIGNING_ALLOWED=NO','ARCHS=arm64','ONLY_ACTIVE_ARCH=YES'];cwd=None
else:cmd=['./gradlew',':app:compileDebugKotlin','--console=plain','--max-workers=2'];cwd=a.workspace/'reply/Reply'
t=time.time();process=subprocess.run(cmd,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(a.output/'build.log').write_text(process.stdout)
record={'kind':'common_compile_only_no_render','argv':cmd,'cwd':str(cwd)if cwd else None,'startedAtUnix':t,'finishedAtUnix':time.time(),'exitCode':process.returncode,'bridgeSHA256':hashlib.sha256(a.bridge.read_bytes()).hexdigest()if a.bridge else None}
(a.output/'record.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));print(process.stdout[-3500:]);raise SystemExit(process.returncode)
