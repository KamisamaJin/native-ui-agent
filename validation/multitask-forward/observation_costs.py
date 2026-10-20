#!/usr/bin/env python3
"""Measured capture timing breakdowns; no invented platform timing fields."""
import argparse,collections,json
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
def build():
 ex.gate.verify(R/'gates','reveal',R);records=[]
 for category in ['own-corpora','common-corpora','paired-corpora']:
  for path in sorted((R/category).rglob('corpus.json')):
   c=ex.read(path)
   for platform,runs in c.get('platformRuns',{}).items():
    for run in runs:
     raw=path.parent/platform/run['case'];mp=raw/'manifest.json';op=raw/'observation.json';manifest=ex.read(mp)if mp.is_file()else{};obs=ex.read(op)if op.is_file()else{};refs={s['screenshot']for s in obs.get('snapshots',[])if s.get('screenshot')};pngs=[]
     for rel in sorted(refs):
      p=(raw/rel).resolve();assert p.is_relative_to(raw.resolve())and p.is_file();pngs.append({'path':rel,'bytes':p.stat().st_size,'sha256':ex.sha(p)})
     records.append({'corpus':str(path.relative_to(R)),'platform':platform,'phase':c['phase'],'tool':c['tool'],'case':run['case'],'exitCode':run['exitCode'],'wrapperWallSeconds':run['wallSeconds'],'nativeManifestTimings':manifest.get('timings'),'buildCacheHit':manifest.get('build_cache',{}).get('hit'),'frames':len(obs.get('snapshots',[])),'referencedPNGFiles':len(pngs),'distinctPNGHashes':len({p['sha256']for p in pngs}),'referencedPNGBytes':sum(p['bytes']for p in pngs)})
 by={}
 for platform in ['ios','android']:
  rr=[r for r in records if r['platform']==platform];timings=collections.Counter()
  for row in rr:
   for k,v in(row['nativeManifestTimings']or{}).items():timings[k]+=v
  by[platform]={'commands':len(rr),'nonzeroExits':sum(r['exitCode']!=0 for r in rr),'wrapperWallSumSeconds':sum(r['wrapperWallSeconds']for r in rr),'manifestTimingSumsSeconds':dict(timings),'buildCacheHits':sum(r['buildCacheHit']is True for r in rr),'buildCacheRecordedCommands':sum(r['buildCacheHit']is not None for r in rr),'frames':sum(r['frames']for r in rr),'referencedPNGFiles':sum(r['referencedPNGFiles']for r in rr),'referencedPNGBytes':sum(r['referencedPNGBytes']for r in rr)}
 return{'byPlatform':by,'records':records,'scope':'Actual wrapper walls and native manifest timing fields only. Missing Android stage timings stay unavailable. PNG counts are retained reference/storage counts, not a count of screenshot encoding calls or a claimed runtime saving. IOS build reuse, PNG reuse and scheduling already existed/shared across arms; these figures do not establish v7 treatment gains. Command sums overlap across platforms/slots and are not experiment elapsed time.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();v=build();out=R/'observation-costs.json'
 if a.write:assert not out.exists();ex.save(out,v)
 else:assert ex.read(out)==v
 print(json.dumps({'status':'PASS','byPlatform':v['byPlatform']}))
if __name__=='__main__':main()
