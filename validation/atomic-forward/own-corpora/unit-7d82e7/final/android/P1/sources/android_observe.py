#!/usr/bin/env python3
"""Observe a caller Compose bridge in an existing Paparazzi/JVM test project."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,time,xml.etree.ElementTree as ET,importlib.util
from pathlib import Path
TEMPLATE=Path(__file__).resolve().parents[1]/'assets/android-observer/NativeObserverTest.kt'
CONTRACT=Path(__file__).with_name('observation_contract.py')
_spec=importlib.util.spec_from_file_location('native_observation_contract',CONTRACT);_contract=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_contract)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['run']);p.add_argument('--project',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--actions',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--java-home',type=Path,required=True);p.add_argument('--android-sdk',type=Path,required=True);p.add_argument('--gradle-task',default=':app:testDebugUnitTest');p.add_argument('--test-source',default='app/src/test/java');p.add_argument('--template',type=Path,default=TEMPLATE);a=p.parse_args()
 project=a.project.resolve();output=a.output.resolve();bridge=a.bridge.resolve();config=json.loads(a.fixtures.read_text());actions=json.loads(a.actions.read_text())if a.actions else []
 if not isinstance(config.get('initial'),dict)or not isinstance(config.get('updates',[]),list):raise ValueError('initial object and updates array required')
 _contract.validate_actions(actions)
 if output.exists():raise ValueError('Fresh output required')
 target=(project/a.test_source/'org/nativeobserver').resolve()
 if not target.is_relative_to(project)or target.exists():raise ValueError('Reserved org/nativeobserver test folder must be fresh and inside project')
 output.mkdir(parents=True);(output/'sources').mkdir();config['actions']=actions;(output/'fixtures.json').write_text(json.dumps(config,indent=2)+'\n')
 shutil.copy2(a.template,output/'sources/NativeObserverTest.kt');shutil.copy2(bridge,output/'sources/ObserverBridge.kt')
 shutil.copy2(CONTRACT,output/'sources/observation_contract.py');shutil.copy2(Path(__file__),output/'sources/android_observe.py')
 sources=[x for x in(project/'app/src/main').rglob('*')if x.is_file()];manifest={'schema_version':1,'status':'error','started_at':time.time(),'native_test_count':0,'source_hashes':{str(x):sha(x)for x in sources+[bridge,a.template,Path(__file__).resolve(),CONTRACT]},'input_hashes':{'fixtures':sha(a.fixtures),**({'actions':sha(a.actions)}if a.actions else{})}}
 created=False
 try:
  target.mkdir(parents=True);created=True;shutil.copy2(a.template,target/'NativeObserverTest.kt');shutil.copy2(bridge,target/'ObserverBridge.kt')
  env=dict(os.environ,JAVA_HOME=str(a.java_home.resolve()),ANDROID_HOME=str(a.android_sdk.resolve()),NATIVE_UI_OUTPUT=str(output),BENCH_FIXTURE=str(output/'fixtures.json'))
  argv=['./gradlew',a.gradle_task,'--tests','org.nativeobserver.NativeObserverTest.capture','--console=plain','--max-workers=2'];manifest['command']=argv
  result=subprocess.run(argv,cwd=project,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(output/'test.log').write_text(result.stdout);manifest['exit_code']=result.returncode
  junit=project/'app/build/test-results'/a.gradle_task.split(':')[-1]/'TEST-org.nativeobserver.NativeObserverTest.xml'
  if junit.is_file():
   shutil.copy2(junit,output/'junit.xml');counts=ET.parse(junit).getroot().attrib;manifest['native_test_count']=int(counts.get('tests',0));manifest['native_counts']=counts
  observation=output/'observation.json'
  if observation.is_file():
   manifest['observation_sha256']=sha(observation);manifest['image_hashes']={str(x.relative_to(output)):sha(x)for x in output.glob('*.png')};manifest['status']='captured_not_graded'if result.returncode==0 and manifest['native_test_count']==1 else'failed'
 except Exception as e:manifest['error']=str(e)
 finally:
  # Only this invocation's newly created reserved files are removed.
  if created:
   for name in ['NativeObserverTest.kt','ObserverBridge.kt']:
    q=target/name
    if q.is_file():q.unlink()
   if target.is_dir()and not any(target.iterdir()):target.rmdir()
  manifest['finished_at']=time.time();(output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'status':manifest['status'],'native_test_count':manifest['native_test_count'],'output':str(output),'error':manifest.get('error')}));return 0 if manifest['status']=='captured_not_graded'else 1
if __name__=='__main__':raise SystemExit(main())
