#!/usr/bin/env python3
"""Recreate one sealed submission with equal native hosts in a NEW workspace."""
import argparse,json,shutil,subprocess,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PINS={'reply':('https://github.com/android/compose-samples.git','53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79'),'alerttoast':('https://github.com/elai950/AlertToast.git','76a1c1793cd3443001c20c6033beb84453b25d9f')}
def run(args,cwd=None):subprocess.run([str(a)for a in args],cwd=cwd,check=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--submission',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--android-sdk',type=Path,required=True);p.add_argument('--ios-device',required=True);p.add_argument('--developer-dir',default='/Applications/Xcode.app/Contents/Developer');a=p.parse_args()
 w=a.workspace.resolve();w.mkdir(parents=True,exist_ok=False);submission=a.submission.resolve();java=a.java_home.resolve()
 for name,(url,pin)in PINS.items():
  target=w/name;run(['git','clone',url,target]);run(['git','checkout','--detach',pin],target)
  patch=ROOT.parent/'blind-comparison/harness'/('android-host.patch'if name=='reply'else'ios-host.patch');run(['git','apply',patch],target)
  src=submission/name
  if not src.is_dir():raise SystemExit('Submission must contain reply/ and alerttoast/ production files')
  for file in src.rglob('*'):
   if file.is_file():dest=target/file.relative_to(src);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest)
 project=w/'reply/Reply';(project/'local.properties').write_text('sdk.dir='+str(a.android_sdk.resolve())+'\n')
 desktop=project/'.native-ui';desktop.mkdir();run([java/'bin/jmod','extract','--dir',desktop/'extract',java/'jmods/java.desktop.jmod']);run([java/'bin/jar','cf',desktop/'java-desktop.jar','-C',desktop/'extract/classes','.']);shutil.rmtree(desktop/'extract')
 with(project/'app/build.gradle.kts').open('a')as f:f.write('\ndependencies { testImplementation(files(rootProject.file(".native-ui/java-desktop.jar"))) }\n')
 tests=project/'app/src/test/java/com/example/reply';tests.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'harness/VisitPanelUiTest.kt',tests)
 shutil.copytree(ROOT/'harness',w/'harness',ignore=shutil.ignore_patterns('environment.local.json','__pycache__'))
 (w/'harness/environment.local.json').write_text(json.dumps({'java_home':str(java),'android_sdk':str(a.android_sdk.resolve()),'developer_dir':a.developer_dir,'ios_device':a.ios_device},indent=2)+'\n')
 print(json.dumps({'workspace':str(w),'capture':str(w/'harness/capture.py'),'note':'Run capture with fixture actions; inspect native outputs and grade separately. Requires installed compatible SDKs, dependencies and simulator.'}))
if __name__=='__main__':main()
