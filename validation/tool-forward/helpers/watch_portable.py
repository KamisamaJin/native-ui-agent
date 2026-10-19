#!/usr/bin/env python3
"""Publish only finished native capture folders, preserving failed attempts too."""
import argparse,json,subprocess,time
from pathlib import Path
H=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);p.add_argument('--cases',type=int,required=True);a=p.parse_args();a.destination.mkdir(parents=True,exist_ok=True);started=time.time()
while True:
 counts={};published=[]
 for platform in ['android','ios']:
  count=0
  for source in sorted((a.source/platform).glob('C*')):
   if not source.is_dir()or not(source/'capture.json').is_file():continue
   dest=a.destination/platform/source.name
   if not(dest/'portable-sha256.json').is_file():
    if dest.exists():raise RuntimeError('Incomplete portable destination; retain it and choose a new attempt: '+str(dest))
    subprocess.run(['python3',str(H/'portable_trial.py'),str(source),str(dest)],check=True)
   count+=1;published.append({'platform':platform,'case':source.name,'observation_available':(dest/'observation.json').is_file()})
  counts[platform]=count
 complete=all(n==a.cases for n in counts.values())
 state={'started_at':started,'updated_at':time.time(),'expected_cases_per_platform':a.cases,'counts':counts,'complete':complete,'published':published,'scope':'Completed native attempts, not passing business cases. Unavailable/failed captures retained.'}
 (a.destination/'capture-inventory.json').write_text(json.dumps(state,indent=2)+'\n')
 if complete:break
 if time.time()-started>24*3600:raise TimeoutError('Native collection not complete after24h; original captures retained')
 time.sleep(20)
