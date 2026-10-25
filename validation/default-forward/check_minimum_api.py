#!/usr/bin/env python3
"""Emit the real module and typecheck its original caller at a minimum OS API.
No Xcode package/archive/link or older-OS rendering/runtime claim is made.
"""
import argparse,os,subprocess,time
from pathlib import Path
import study as s
R=s.R

def run(workspace,bridge,output,deployment='14.0'):
 w=Path(workspace).resolve();bridge=Path(bridge).resolve();out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False);before=s.fingerprint(w)
 root=w/'alerttoast/Sources';sources=sorted(p for p in root.rglob('*.swift')if not any(v.startswith('.')for v in p.relative_to(root).parts))
 if not sources:raise ValueError('Real production Swift sources required')
 env=dict(os.environ,DEVELOPER_DIR=s.DEV);sdk=subprocess.check_output(['xcrun','--sdk','iphonesimulator','--show-sdk-path'],env=env,text=True).strip();target='arm64-apple-ios'+deployment+'-simulator';module=out/'module';module.mkdir()
 commands=[['xcrun','swiftc','-emit-module','-emit-module-path',str(module/'AlertToast.swiftmodule'),'-parse-as-library','-swift-version','5','-module-name','AlertToast','-target',target,'-sdk',sdk]+list(map(str,sources)),['xcrun','swiftc','-typecheck','-parse-as-library','-swift-version','5','-module-name','MinimumClient','-target',target,'-sdk',sdk,'-I',str(module),str(bridge)]]
 began=time.time();rows=[]
 for index,argv in enumerate(commands):
  started=time.time();process=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(out/('step-'+str(index)+'.log')).write_text(process.stdout);rows.append({'argv':argv,'startedAtUnix':started,'finishedAtUnix':time.time(),'exitCode':process.returncode})
  if process.returncode:break
 after=s.fingerprint(w);record={'kind':'minimum_source_api_module_and_client_check','startedAtUnix':began,'finishedAtUnix':time.time(),'deployment_target':deployment,'compiler_target':target,'source':before,'source_after':after,'source_unchanged':before==after,'source_files':{str(p.relative_to(w)):s.sha(p)for p in sources},'bridge_sha256':s.sha(bridge),'operator_sha256':s.sha(Path(__file__)),'commands':rows,'status':'source_api_typechecked'if len(rows)==2 and all(v['exitCode']==0 for v in rows)and before==after else'failed_or_unverified','scope':'Source/module/caller API availability only. No package archive/link, app launch, iOS14 runtime or rendered-style pass.'}
 s.save(out/'record.json',record);return record

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--deployment-target',default='14.0');a=p.parse_args()
 if not a.deployment_target.replace('.','').isdigit():p.error('Explicit numeric deployment target required')
 result=run(a.workspace,a.bridge,a.output,a.deployment_target);print(result['status']);raise SystemExit(0 if result['status']=='source_api_typechecked'else 1)
