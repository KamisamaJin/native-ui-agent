#!/usr/bin/env python3
"""Archive complete acquired corpora, retaining failures and original evidence."""
import argparse,hashlib,json,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);p.add_argument('--seal',type=Path,required=True);a=p.parse_args();src=a.source.resolve();dst=a.destination.resolve();assert not a.seal.exists();start=time.time();datasets={}
 for platform in ['ios','android']:
  corpus=json.loads((src/platform/'corpus.json').read_text());assert corpus['platform']==platform
  subprocess.run([sys.executable,str(R/'helpers/portable.py'),str(src/platform),str(dst/platform)],check=True)
  datasets[platform]={'source':str(src/platform),'archive':str(dst/platform),'producerFinishedAtUTC':corpus['finishedAtUTC'],'producerFinishedAtUnix':corpus['finishedAtUnix'],'runs':corpus['runs'],'sourceHashes':corpus['source'],'portableManifestSHA256':sha(dst/platform/'portable-sha256.json')}
 seal={'sealedAtUTC':datetime.now(timezone.utc).isoformat(),'sealedAtUnix':time.time(),'archiveWallSeconds':time.time()-start,'datasets':datasets};a.seal.parent.mkdir(parents=True,exist_ok=True);a.seal.write_text(json.dumps(seal,indent=2)+'\n');print(json.dumps({'seal':str(a.seal),'producerEndUnix':max(d['producerFinishedAtUnix'] for d in datasets.values())}))
if __name__=='__main__':main()
