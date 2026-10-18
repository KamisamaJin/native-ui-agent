#!/usr/bin/env python3
"""Prepare a fresh native replay of an archived blind-comparison submission.

Replays its source and native fixtures; does not regenerate an AI submission or
recreate procedural blinding/model randomness.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parent
PROJECTS={
    "android":("https://github.com/android/compose-samples.git","53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79","reply"),
    "ios":("https://github.com/elai950/AlertToast.git","76a1c1793cd3443001c20c6033beb84453b25d9f","alerttoast"),
}


def run(*argv,cwd=None):
    subprocess.run(list(map(str,argv)),cwd=cwd,check=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace",type=Path,required=True)
    p.add_argument("--arm",choices=["with-skill","without-skill"],required=True)
    p.add_argument("--phase",choices=["d0","final"],required=True)
    p.add_argument("--android-sdk",required=True);p.add_argument("--java-home",required=True)
    p.add_argument("--ios-device",required=True)
    p.add_argument("--developer-dir",default="/Applications/Xcode.app/Contents/Developer")
    p.add_argument("--local-reply-repository",type=Path)
    p.add_argument("--local-alerttoast-repository",type=Path)
    a=p.parse_args();w=a.workspace.resolve();w.mkdir(parents=True,exist_ok=False)
    receipt={"arm":a.arm,"phase":a.phase,"projects":{}}
    for platform,(url,revision,name) in PROJECTS.items():
        checkout=w/name;local=a.local_reply_repository if platform=="android" else a.local_alerttoast_repository
        if local:
            run("git","clone","--shared","--no-checkout",local.resolve(),checkout)
            run("git","remote","set-url","origin",url,cwd=checkout)
            run("git","checkout","--detach",revision,cwd=checkout)
        else:
            run("git","init",checkout);run("git","remote","add","origin",url,cwd=checkout)
            run("git","fetch","--depth","1","origin",revision,cwd=checkout)
            run("git","checkout","--detach","FETCH_HEAD",cwd=checkout)
        patch=ROOT/"harness"/(platform+"-host.patch")
        run("git","apply","--check",patch,cwd=checkout);run("git","apply",patch,cwd=checkout)
        if platform=="android":
            source=checkout/"Reply/app/src/main/java/com/example/reply/ui/components/ReplyTransferPanel.kt"
            test=checkout/"Reply/app/src/test/java/com/example/reply/BlindPanelUiTest.kt"
        else:
            source=checkout/"Sources/AlertToast/TransferToastPanel.swift"
            test=checkout/"Tests/AlertToastTests/BlindPanelUiTests.swift"
            shutil.copy2(ROOT.parent/"native-ui-pilot/adapters/AlertToast.Package.resolved",checkout/"Package.resolved")
        source.parent.mkdir(parents=True,exist_ok=True);test.parent.mkdir(parents=True,exist_ok=True)
        archived=ROOT/"implementations"/a.arm/a.phase/source.name
        shutil.copy2(archived,source);shutil.copy2(ROOT/"harness"/test.name,test)
        receipt["projects"][platform]={"revision":revision,"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"host_patch_sha256":hashlib.sha256(patch.read_bytes()).hexdigest()}
    shutil.copy2(ROOT/"harness/capture.py",w/"capture.py")
    (w/"environment.json").write_text(json.dumps(dict(java_home=a.java_home,android_sdk=a.android_sdk,
        developer_dir=a.developer_dir,ios_device=a.ios_device),indent=2)+"\n")
    (w/"prepare-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("Ready:",w)


if __name__=="__main__":main()
