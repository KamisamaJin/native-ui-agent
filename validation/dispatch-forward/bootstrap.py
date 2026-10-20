#!/usr/bin/env python3
"""Reuse pinned, common dependency setup; never copy prior untracked business UI."""
import argparse, hashlib, json, shutil, subprocess, time
from pathlib import Path
R=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--java-home',required=True);p.add_argument('--android-sdk',required=True);p.add_argument('--local-upstreams',type=Path);a=p.parse_args()
 cmd=['python3',str(R.parent/'tool-forward/bootstrap.py'),'--workspace',str(a.workspace.resolve()),'--java-home',a.java_home,'--android-sdk',a.android_sdk]
 if a.local_upstreams:cmd+=['--local-upstreams',str(a.local_upstreams.resolve())]
 start=time.time();subprocess.run(cmd,check=True)
 shutil.copy2(R/'common-host/Package.swift',a.workspace/'alerttoast/Package.swift')
 for platform,rel in [('ios','alerttoast/Package.swift'),('android','reply/Reply/app/build.gradle.kts')]:
  path=a.workspace/rel
  print(json.dumps({'platform':platform,'commonHost':rel,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'setupWallSeconds':time.time()-start}))
if __name__=='__main__':main()
