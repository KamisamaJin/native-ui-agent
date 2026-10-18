#!/usr/bin/env python3
"""Common native observation capability. Does not implement or grade the component."""
import argparse,hashlib,json,os,shutil,subprocess,time,xml.etree.ElementTree as ET
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
SETTINGS=json.loads((HERE/'environment.local.json').read_text()) if (HERE/'environment.local.json').exists() else {}
JAVA=SETTINGS.get('java_home','/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--platform',choices=['android','ios'],required=True);p.add_argument('--project',type=Path,required=True);p.add_argument('--fixture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--simulator');a=p.parse_args()
 project=a.project.resolve();fixture=a.fixture.resolve();output=a.output.resolve();started=time.monotonic()
 if output.exists():raise SystemExit('Fresh output required')
 spec=json.loads(fixture.read_text());environment=spec['environment'];commands=[]
 env=dict(os.environ,JAVA_HOME=JAVA,ANDROID_HOME=SETTINGS.get('android_sdk','/Users/rex/Library/Android/sdk'),DEVELOPER_DIR=SETTINGS.get('developer_dir','/Applications/Xcode.app/Contents/Developer'),NATIVE_UI_OUTPUT=str(output),BENCH_FIXTURE=str(fixture))
 def run(argv,cwd=REPO):
  t=time.monotonic();r=subprocess.run(argv,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);commands.append({'argv':argv,'seconds':round(time.monotonic()-t,3),'exit_code':r.returncode});return r
 if a.platform=='android':
  output.mkdir(parents=True)
  r=run(['./gradlew',':app:testDebugUnitTest','--tests','com.example.reply.VisitPanelUiTest.capture','--console=plain'],project);(output/'test.log').write_text(r.stdout)
  junit=project/'app/build/test-results/testDebugUnitTest/TEST-com.example.reply.VisitPanelUiTest.xml'
  if junit.exists():shutil.copy2(junit,output/'junit.xml')
  count=ET.parse(junit).getroot().attrib if junit.exists() else {}
  if r.returncode or count.get('tests')!='1' or count.get('failures')!='0' or count.get('errors')!='0':raise SystemExit('Native test failed or wrong count; see '+str(output))
 else:
  if not a.simulator:raise SystemExit('--simulator required for iOS')
  # Transport/checkpoint names are host metadata, never production model fields.
  updates=[];actions=[]
  protocol=spec.get('actions',[])
  for index,step in enumerate(protocol):
   typ=step['type'];checkpoint=step.get('checkpoint',f'step_{index}')
   if typ=='capture' and checkpoint=='initial':continue  # observer already captures top
   if typ=='scroll_until' and index+1<len(protocol) and protocol[index+1].get('type')=='tap' and protocol[index+1].get('identifier')==step['identifier']:continue  # tap reveal executes the same native scroll
   if typ=='update':updates.append({'model':step['model']});native={'type':'apply_next_fixture'}
   elif typ=='tap':native={'type':'tap','identifier':step['identifier'],'reveal':True,'allow_disabled':True,'max_steps':40}
   elif typ=='scroll_until':native={'type':'scroll','direction':'auto','until_identifier':step['identifier'],'max_steps':40}
   elif typ=='scroll':native={'type':'scroll','direction':step.get('direction','down')}
   elif typ=='capture':native={'type':'capture'}
   else:raise SystemExit('Unsupported action '+typ)
   native['name']=checkpoint
   actions.append(native)
  config={'initial':{'model':spec['model']},'updates':updates,'width':environment['width'],'theme':environment['theme'],'dynamic_type':environment.get('dynamicType','accessibility3' if environment['fontScale']>=2 else 'accessibility2' if environment['fontScale']>=1.7 else 'xxxLarge' if environment['fontScale']>=1.25 else 'large'),'direction':environment['direction'],'required_identifiers':[],'max_scrolls':45,'canvas_color':'#0D1420' if environment['theme']=='dark' else '#EDF1F6'}
  # Use temporary input siblings; output freshness belongs to the observer.
  transport=output.parent/(output.name+'-inputs');transport.mkdir(parents=True,exist_ok=False)
  (transport/'fixtures.json').write_text(json.dumps(config));(transport/'actions.json').write_text(json.dumps(actions))
  r=run(['python3',str(HERE/'observer/scripts/ios_observe.py'),'run','--bridge',str(HERE/'VisitBridge.swift'),'--package',str(project),'--fixtures',str(transport/'fixtures.json'),'--actions',str(transport/'actions.json'),'--simulator',a.simulator,'--output',str(output)])
  # A denied/failed product action must remain visible evidence, not erase all native outputs.
  (output/'operator.log').write_text(r.stdout)
  if not (output/'observation.json').exists():raise SystemExit('Native observation unavailable; see '+str(output))
 observation=json.loads((output/'observation.json').read_text())
 initial=observation.get('snapshots',[{}])[0].get('screenshot')
 if initial and (output/initial).exists():shutil.copy2(output/initial,output/'actual.png')
 sources=sorted((project/('app/src/main/java/com/example/reply/ui/components' if a.platform=='android' else 'Sources/AlertToast')).glob('*Visit*'))
 manifest={'platform':a.platform,'status':'captured_not_graded','fixture_sha256':sha(fixture),'sources':{str(x.relative_to(project)):sha(x)for x in sources if x.is_file()},'harness':{str(x.relative_to(HERE)):sha(x)for x in [Path(__file__),HERE/'VisitPanelUiTest.kt',HERE/'VisitBridge.swift']},'seconds':round(time.monotonic()-started,3),'commands':commands,'checkpoint_aliases':{'initial':'top'} if a.platform=='ios' else {},'protocol':spec.get('actions',[])}
 (output/'capture.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'output':str(output),'status':'captured_not_graded','seconds':manifest['seconds']}))
if __name__=='__main__':main()
