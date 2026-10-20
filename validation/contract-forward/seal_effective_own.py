#!/usr/bin/env python3
"""Record explicit missing-capture retry overlays; never replace original corpora."""
import argparse,hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['d0','final']);a=p.parse_args();assignment=read(R/'private/assignment.json')
 records=[]
 for unit in assignment['units']:
  original=R/'own-corpora'/unit/a.phase;seal=read(original/'corpus-seal.json');source=read(R/'submissions'/unit/a.phase/'seal.json');assert source['files']==seal['source']
  retry=R/'own-retries'/unit/a.phase
  if retry.exists():assert read(retry/'corpus-seal.json')['source']==source['files']
  captures={};substitutions=[]
  for platform in ['ios','android']:
   for case in ['P1','P2']:
    base=original/platform/case;chosen=base
    if not(base/'observation.json').is_file()and(retry/platform/case/'observation.json').is_file():
     chosen=retry/platform/case;substitutions.append({'platform':platform,'case':case,'originalCapture':str(base.relative_to(R)),'originalCommand':str((original/platform/(case+'-command.json')).relative_to(R)),'retryCapture':str(chosen.relative_to(R)),'reason':'Original pre-native input-policy rejection; exact source/approved stimulus preserved, common-width adapter retry. No original image or verdict overwritten.'})
    assert(chosen/'observation.json').is_file(),str(chosen)
    captures[platform+'/'+case]=str(chosen.relative_to(R))
  records.append((unit,{'phase':a.phase,'sealedAtUTC':datetime.now(timezone.utc).isoformat(),'sealedAtUnix':time.time(),'captures':captures,'missingOriginalRetries':substitutions,'originalCorpusSealSHA256':sha(original/'corpus-seal.json'),'retryCorpusSealSHA256':sha(retry/'corpus-seal.json')if retry.exists()else None,'sourceSealSHA256':sha(R/'submissions'/unit/a.phase/'seal.json')}))
 for unit,data in records:
  out=R/'submissions'/unit/('effective-own-'+a.phase+'.json');assert not out.exists();out.write_text(json.dumps(data,indent=2)+'\n')
 print(json.dumps({'phase':a.phase,'units':len(records),'retryCaptures':sum(len(v['missingOriginalRetries'])for _,v in records)}))
if __name__=='__main__':main()
