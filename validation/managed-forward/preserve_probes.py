#!/usr/bin/env python3
"""Preserve closed neutral receipts before disposable host/build cleanup."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,time
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'evidence/probes';out.mkdir(parents=True,exist_ok=False)
 copies={
  'android-prototype-1':'neutral-android-attempt-1',
  'android-prototype-2':'neutral-android-attempt-2',
  'android-prototype-3':'neutral-android-attempt-3',
  'android-source-feedback':'neutral-android-after-source',
  'android-candidate-negative':'neutral-android-candidate-2',
  'android-candidate-positive':'neutral-android-positive',
  'responsibility-negative':'responsibility-negative-cycle',
  'zero-sdk-tests':'zero-sdk-tests',
  'cancel-sdk':'cancel-sdk'}
 for name,cache in copies.items():
  src=R/'cache'/cache
  if not src.is_dir():raise ValueError('Original probe missing: '+cache)
  subprocess.run([sys.executable,'-B',str(REPO/'validation/dispatch-forward/helpers/portable.py'),str(src),str(out/name)],check=True)
 reviews=R/'cache/neutral-source-reviews'
 shutil.copytree(reviews,out/'source-reviews')
 # Actual neutral source files are retained separately from pinned stock hosts.
 production={
  'alerttoast/Sources/AlertToast/NeutralCounter.swift':R/'cache/neutral/alerttoast/Sources/AlertToast/NeutralCounter.swift',
  'reply/Reply/app/src/main/java/com/example/reply/ui/components/NeutralCounter.kt':R/'cache/neutral/reply/Reply/app/src/main/java/com/example/reply/ui/components/NeutralCounter.kt'}
 for rel,src in production.items():
  target=out/'production'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
 for name in ['alerttoast','reply']:
  src=R/'cache/stock'/name
  for license in ['LICENSE','LICENSE.md','LICENSE.txt','NOTICE']:
   p=src/license
   if p.is_file():target=out/'licenses'/(name+'-'+license);target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
 (out/'upstreams.json').write_bytes((R/'cache/stock/bootstrap.json').read_bytes())
 inventory={str(p.relative_to(out)):{'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(out.rglob('*'))if p.is_file()}
 (out/'SEAL.json').write_text(json.dumps({'sealed_at_unix':time.time(),'files':inventory,
  'scope':'Original neutral probe data only. No business PR designed/authored/rendered. SDK build caches and stock checkouts are disposable; raw failed runs remain.'},indent=2)+'\n')
 print(json.dumps({'files':len(inventory),'logical_bytes':sum(v['bytes']for v in inventory.values())}))
if __name__=='__main__':main()
