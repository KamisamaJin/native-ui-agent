#!/usr/bin/env python3
"""Index every unsuccessful native acquisition; original bytes stay in place."""
import argparse,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def build():
 rows=[]
 for group in ['own-corpora','common-corpora','paired-corpora']:
  for p in sorted((R/group).rglob('corpus.json')):
   data=read(p)
   if 'platformRuns'not in data:continue
   for platform,runs in data['platformRuns'].items():
    for run in runs:
     if run['exitCode']==0:continue
     capture=p.parent/platform/run['case'];summary=capture/'native-summary.json'
     rows.append({'corpus':str(p.relative_to(R)),'phase':data['phase'],'tool':data['tool'],'platform':platform,'case':run['case'],'exitCode':run['exitCode'],'wallSeconds':run['wallSeconds'],'inputHashes':run['inputHashes'],'source':data['source'],'observation':str((capture/'observation.json').relative_to(R)),'observationSHA256':hashlib.sha256((capture/'observation.json').read_bytes()).hexdigest(),'nativeSummary':read(summary)if summary.exists()else None,'commandRecord':str((p.parent/platform/(run['case']+'-command.json')).relative_to(R)),'rawCaptureDirectory':str(capture.relative_to(R))})
 return {'unsuccessfulNativeAcquisitions':rows,'scope':'All nonzero native collection exits in own/common/paired corpora, with originals retained. Assertion reports with exit1 are separate check outcomes, not native acquisition failures. Generic pre-freeze engineering failures and common evaluator/host amendments are documented separately.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();out=R/'failure-index.json';data=build()
 if a.write:out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
 else:assert read(out)==data
 print(json.dumps({'status':'PASS','retainedNativeFailures':len(data['unsuccessfulNativeAcquisitions'])}))
if __name__=='__main__':main()
