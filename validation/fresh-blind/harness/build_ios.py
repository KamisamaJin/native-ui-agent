#!/usr/bin/env python3
"""Build-only common bridge integration check. No test execution or screenshot review."""
import argparse,importlib.util,os,subprocess,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--simulator',required=True);a=p.parse_args()
module=importlib.util.spec_from_file_location('observer',HERE/'observer/scripts/ios_observe.py');observer=importlib.util.module_from_spec(module);module.loader.exec_module(observer)
a.output.mkdir(parents=True,exist_ok=False);project=observer.generate_project(a.output/'project',HERE/'VisitBridge.swift',a.package.resolve())
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer')
result=subprocess.run(['xcodebuild','build-for-testing','-project',str(project),'-scheme','Observer','-configuration','Debug','-sdk','iphonesimulator','-destination','platform=iOS Simulator,id='+a.simulator,'-derivedDataPath',str(a.output/'DerivedData'),'CODE_SIGNING_ALLOWED=NO','ARCHS=arm64','ONLY_ACTIVE_ARCH=YES'],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(a.output/'build.log').write_text(result.stdout);print(json.dumps({'exit_code':result.returncode,'log':str(a.output/'build.log')}));raise SystemExit(result.returncode)
