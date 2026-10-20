#!/usr/bin/env python3
"""Deliver actual V5 captures and byte-exact original V6 native-base grades."""
import hashlib,json,shutil,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert(R/'evaluation/selfreview/SEAL.json').is_file(),'Dual original-selfreview matching must seal first'
 out=R/'evaluation-inputs/paired-D0';assert not out.exists();out.mkdir(parents=True);corpora=[]
 for alias in ['source-a','source-b']:
  raw=R/'paired-corpora'/alias/'v5';assert(raw/'corpus-seal.json').is_file()
  for rel,h in read(raw/'portable-sha256.json').items():assert sha(raw/rel)==h
  shutil.copytree(R/'evaluation/D0'/alias/'native-base',out/alias/'v6/native-base')
  shutil.copytree(R/'evaluation-inputs/D0'/alias/'source-capsule',out/alias/'source-capsule')
  corpora.append({'anonymousID':alias,'newV5Captures':str(raw.relative_to(R)),'reuseV6Captures':f'common-corpora/{alias}/d0','reusedV6NativeGrades':str((out/alias/'v6/native-base').relative_to(R)),'v5ManifestSHA256':sha(raw/'portable-sha256.json'),'v6ManifestSHA256':sha(R/'common-corpora'/alias/'d0/portable-sha256.json')})
 (out/'batch.json').write_text(json.dumps({'stage':'paired-D0','corpora':corpora,'cases':['P1','P2'],'scope':'Same D0 sources and common public inputs. V5 new actual captures; V6 native-base/raw exact reuse. Grade V5 with unchanged frozen v6 oracle and manual=None/source_root=None/api_review=None. Compare native classes only; visual/API/input cannot count as collector gains.'},indent=2)+'\n')
 files={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()};(out/'DELIVERY-SEAL.json').write_text(json.dumps({'sealedAtUTC':datetime.now(timezone.utc).isoformat(),'sealedAtUnix':time.time(),'files':files},indent=2)+'\n');print('paired-D0 delivery sealed')
if __name__=='__main__':main()
