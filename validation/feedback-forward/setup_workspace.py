#!/usr/bin/env python3
"""Clean pinned dependencies; no copied untracked business component code."""
import argparse,subprocess
from pathlib import Path
import study as s
p=argparse.ArgumentParser();p.add_argument('name');a=p.parse_args();assert a.name.replace('-','').isalnum()
w=s.R/'cache'/a.name
subprocess.run(['python3',str(s.REPO/'validation/dispatch-forward/bootstrap.py'),'--workspace',str(w),'--java-home',s.JAVA,'--android-sdk',s.SDK,'--local-upstreams',str(s.R/'cache/neutral-host')],check=True)
files={}
for name in ['alerttoast','reply']:
 folder=w/name
 for rel in subprocess.check_output(['git','ls-files','-z'],cwd=folder).decode().split('\0'):
  path=folder/rel
  if rel and path.is_file()and not any(path.is_relative_to(w/root)for root in s.ROOTS):files[str(path.relative_to(w))]=s.sha(path)
# Build compatibility config differs intentionally from the upstream tracked blob.
for rel in ['alerttoast/Package.swift','reply/Reply/app/build.gradle.kts','reply/Reply/local.properties']:files[rel]=s.sha(w/rel)
s.save(w/'HOST-SEAL.json',{'files':files,'scope':'Pinned tracked nonproduction host/test inputs; production source is separately sealed at every launch.'})
print(w)
