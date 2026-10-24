#!/usr/bin/env python3
"""Compile a real local library/bridge at its declared minimum; never launch it."""
import argparse,hashlib,importlib.util,json,os,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
import study as s
R=s.R
p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--deployment-target',default='14.0');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert a.deployment_target.replace('.','').isdigit();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);w=a.workspace.resolve();before=s.fingerprint(w)
path=R/'candidate-v9/scripts/ios_observe.py';spec=importlib.util.spec_from_file_location('minimum_compile_host',path);observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
project=observer.generate_project(out/'project',a.bridge.resolve(),(w/'alerttoast').resolve())
app=out/'project/ObserverApp.swift';app.write_text('import SwiftUI\n@main struct MinimumCompileApp: App { var body: some Scene { WindowGroup { Text("Compile only") } } }\n')
pbx=project/'project.pbxproj';text=pbx.read_text();text=text.replace('IPHONEOS_DEPLOYMENT_TARGET = 17.0','IPHONEOS_DEPLOYMENT_TARGET = '+a.deployment_target);pbx.write_text(text)
scheme=project/'xcshareddata/xcschemes/Observer.xcscheme';tree=ET.parse(scheme)
for container in tree.getroot().iter('BuildActionEntries'):
 for entry in list(container):
  ref=entry.find('BuildableReference')
  if ref is not None and ref.get('BlueprintName')=='ObserverTests':container.remove(entry)
tree.write(scheme,encoding='unicode')
argv=['xcodebuild','build','-project',str(project),'scheme-placeholder']
argv=['xcodebuild','build','-project',str(project),'-scheme','Observer','-configuration','Debug','-sdk','iphonesimulator','-destination','generic/platform=iOS Simulator','-derivedDataPath',str(out/'DerivedData'),'CODE_SIGNING_ALLOWED=NO','ARCHS=arm64','ONLY_ACTIVE_ARCH=YES','IPHONEOS_DEPLOYMENT_TARGET='+a.deployment_target]
started=time.time();process=subprocess.run(argv,env=dict(os.environ,DEVELOPER_DIR=s.DEV),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(out/'build.log').write_text(process.stdout)
after=s.fingerprint(w);proof='-target arm64-apple-ios'+a.deployment_target+'-simulator';record={'kind':'minimum_deployment_compile_only_no_launch','startedAtUnix':started,'finishedAtUnix':time.time(),'argv':argv,'exitCode':process.returncode,'source':before,'source_unchanged':before==after,'bridge_sha256':s.sha(a.bridge),'deployment_target':a.deployment_target,'compiler_target_observed':proof in process.stdout,'scope':'Actual build, no app launch/render/screenshot or older-OS runtime claim.'}
s.save(out/'record.json',record);print(json.dumps({k:record[k]for k in ['exitCode','source_unchanged','deployment_target','compiler_target_observed']}));print(process.stdout[-2500:]);raise SystemExit(0 if process.returncode==0 and before==after and record['compiler_target_observed']else 1)
