#!/usr/bin/env python3
import argparse,datetime,hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill');O=R/'validation/multitask-forward/independent-generic';C=R/'validation/multitask-forward/cache/independent-neutral';H=C/'host';S=R/'validation/multitask-forward/development/v7-neutral-candidate/scripts'
a=argparse.ArgumentParser();a.add_argument('platform',choices=['ios','android']);args=a.parse_args();p=args.platform
(C/'.gitignore').write_text('*\n!.gitignore\n')
seal=json.loads((O/'source-seal.json').read_text())
for name,digest in seal['files'].items():
 assert hashlib.sha256((O/name).read_bytes()).hexdigest()==digest
src=O/'source'/('ReadingPanel.swift' if p=='ios' else 'ReadingPanel.kt');actual=H/('alerttoast/Sources/AlertToast/ReadingPanel.swift' if p=='ios' else 'reply/Reply/app/src/main/java/org/neutral/ReadingPanel.kt')
assert src.read_bytes()==actual.read_bytes()
for config in ['normal','dark-large']:
 out=C/('raw-'+p+'-'+config)
 cmd=['python3','-B',str(S/(p+'_observe.py')),'run','--bridge',str(O/'source'/('Bridge.swift' if p=='ios' else 'ObserverBridge.kt')),'--fixtures',str(O/'fixtures'/(config+'-'+p+'.json')),'--actions',str(O/'plans'/config/p/'actions.json'),'--output',str(out)]
 if p=='ios':cmd+=['--package',str(H/'alerttoast'),'--product','AlertToast','--simulator','65215167-05EE-4287-AF67-412007163369','--developer-dir','/Applications/Xcode.app/Contents/Developer','--build-cache',str(C/'ios-build-cache')]
 else:cmd+=['--project',str(H/'reply/Reply'),'--java-home','/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home','--android-sdk','/Users/rex/Library/Android/sdk']
 start=time.time();record={'argv':cmd,'cwd':str(R),'start_unix':start,'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_seal_sha256':hashlib.sha256((O/'source-seal.json').read_bytes()).hexdigest(),'barrier_receipt_sha256':hashlib.sha256((O/'barrier/authorized.json').read_bytes()).hexdigest()}
 log=O/'logs'/(p+'-'+config+'.log');log.parent.mkdir(exist_ok=True);rp=log.with_suffix('.command.json');rp.write_text(json.dumps(record,indent=2)+'\n')
 print('START '+p+' '+config,flush=True)
 try:
  with log.open('w') as f:result=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=660)
  record['exit_code']=result.returncode
 except Exception as e:record['exit_code']=None;record['error']=str(e)
 record['end_unix']=time.time();record['wall_seconds']=time.time()-start;record['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();rp.write_text(json.dumps(record,indent=2)+'\n');print('END '+p+' '+config+' '+str(record['exit_code']),flush=True)
