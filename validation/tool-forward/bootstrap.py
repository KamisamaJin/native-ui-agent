#!/usr/bin/env python3
"""Fresh pinned upstream hosts; no old business implementations are copied."""
import argparse,subprocess,shutil,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
PINS={'reply':('https://github.com/android/compose-samples.git','53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79'),'alerttoast':('https://github.com/elai950/AlertToast.git','76a1c1793cd3443001c20c6033beb84453b25d9f')}
def run(args,cwd=None):subprocess.run([str(x)for x in args],cwd=cwd,check=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--android-sdk',type=Path,required=True);p.add_argument('--local-upstreams',type=Path);p.add_argument('--submission',type=Path);a=p.parse_args();w=a.workspace.resolve();w.mkdir(parents=True,exist_ok=False);java=a.java_home.resolve();record={'pinnedUpstreams':{},'localObjectReuse':bool(a.local_upstreams)}
 for name,(url,pin)in PINS.items():
  repo=w/name;source=(a.local_upstreams/name).resolve()if a.local_upstreams else url;run(['git','clone',source,repo]);run(['git','checkout','--detach',pin],repo);run(['git','remote','set-url','origin',url],repo);record['pinnedUpstreams'][name]=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip();assert record['pinnedUpstreams'][name]==pin
  run(['git','apply',R.parent/'blind-comparison/harness'/('android-host.patch'if name=='reply'else'ios-host.patch')],repo)
  if a.submission:
   for file in(a.submission/name).rglob('*'):
    if file.is_file():dest=repo/file.relative_to(a.submission/name);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest)
 project=w/'reply/Reply';(project/'local.properties').write_text('sdk.dir='+str(a.android_sdk.resolve())+'\n');desktop=project/'.native-ui';desktop.mkdir();run([java/'bin/jmod','extract','--dir',desktop/'extract',java/'jmods/java.desktop.jmod']);run([java/'bin/jar','cf',desktop/'java-desktop.jar','-C',desktop/'extract/classes','.']);shutil.rmtree(desktop/'extract')
 with(project/'app/build.gradle.kts').open('a')as f:f.write('\ndependencies { testImplementation(files(rootProject.file(".native-ui/java-desktop.jar"))) }\n')
 record['javaDesktopModuleSha256']=hashlib.sha256((java/'jmods/java.desktop.jmod').read_bytes()).hexdigest();(w/'bootstrap.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'workspace':str(w),'source':'pinned clean upstreams plus test dependencies only'}))
if __name__=='__main__':main()
