#!/usr/bin/env python3
"""Public thin host routing; does not implement a component or grade its output."""
import argparse,json,subprocess,time,hashlib,shutil
from pathlib import Path
H=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--platform',choices=['android','ios'],required=True);p.add_argument('--project',type=Path,required=True);p.add_argument('--fixture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--simulator');p.add_argument('--capability',type=Path,default=H.parent/'capability');a=p.parse_args()
 cap=a.capability.resolve();spec=json.loads(a.fixture.read_text());env=spec['environment'];out=a.output.resolve();transport=out.parent/(out.name+'-inputs');transport.mkdir(parents=True,exist_ok=False)
 config={'initial':{'model':spec['model']},'updates':[{'model':x}for x in spec.get('updates',[])],'width':env['offeredWidth'],'theme':env['appearance'],'direction':env['layoutDirection'],'fontScale':env['fontScale'],'viewportHeight':600,'state_capture':spec.get('state_capture',True),'max_scrolls':80,'required_identifiers':[],'observation_targets':spec.get('observation_targets',[]),'canvas_color':'#101718'if env['appearance']=='dark'else'#FAF8F5'}
 categories={'large':'large','extraExtraExtraLarge':'xxxLarge','accessibilityExtraExtraExtraLarge':'accessibility5'}
 config['dynamic_type']=categories[env['appleContentSizeCategory']]
 actions=spec.get('actions',[]);candidate=(cap/'scripts/native_checks.py').is_file()
 if not candidate:
  # Preserve the previous collector's supported commands/policy. A sweep is only
  # a checkpoint here; do not smuggle the candidate's sweep algorithm into it.
  actions=[dict(x,type='capture')if x.get('type')=='sweep'else x for x in actions]
 (transport/'fixtures.json').write_text(json.dumps(config,indent=2,ensure_ascii=False)+'\n');(transport/'actions.json').write_text(json.dumps(actions,indent=2,ensure_ascii=False)+'\n')
 common=['--fixtures',str(transport/'fixtures.json'),'--actions',str(transport/'actions.json'),'--output',str(out)]
 if a.platform=='ios':
  if not a.simulator:raise ValueError('--simulator required')
  argv=['python3',str(cap/'scripts/ios_observe.py'),'run','--bridge',str(H/'ReturnBridge.swift'),'--package',str(a.project.resolve()),'--product','AlertToast','--simulator',a.simulator,'--developer-dir','/Applications/Xcode.app/Contents/Developer']+common
 else:
  script=cap/'scripts/android_observe.py'if candidate else H/'android_run.py'
  argv=['python3',str(script),'run','--project',str(a.project.resolve()),'--bridge',str(H/'ObserverBridge.kt'),'--java-home','/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home','--android-sdk','/Users/rex/Library/Android/sdk']+common
  if not candidate:argv+=['--template',str(H/'baseline-android/NativeObserverTest.kt')]
 t=time.monotonic();r=subprocess.run(argv,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 out.mkdir(parents=True,exist_ok=True);(out/'operator.log').write_text(r.stdout)
 record={'status':'captured_not_graded'if(out/'observation.json').is_file()else'unavailable','platform':a.platform,'source_fixture_sha256':sha(a.fixture),'command':argv,'exit_code':r.returncode,'seconds':round(time.monotonic()-t,3),'action_protocol':spec.get('protocol',[]),'actual_actions':actions,'harness_sha256':{str(x.relative_to(H)):sha(x)for x in [Path(__file__),H/'ReturnBridge.swift',H/'ObserverBridge.kt']},'native_method_limit':'iOS tap requests and accessibilityActivate requests both execute actual XCUI tap; no AX performAction proof. Android uses native semantic OnClick, not OS physical touch.'}
 (out/'capture.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:record[k]for k in ['status','exit_code','seconds']}));return 0 if record['status']=='captured_not_graded'else 1
if __name__=='__main__':raise SystemExit(main())
