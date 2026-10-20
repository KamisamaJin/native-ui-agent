#!/usr/bin/env python3
"""Seal same-source paired acquisition plan after primary development endpoints."""
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 a=read(R/'private/assignment.json');ends={u:read(R/'own-corpora'/u/'final/corpus-seal.json')['sealedAtUnix']for u in a['units']};out=R/'private/paired-acquisition-scheduling.json';assert not out.exists()
 rows=[]
 for alias,u in a['gradeAliases'].items():rows.append({'anonymousID':alias,'sourceSeal':str((R/'submissions'/u/'d0/seal.json').relative_to(R)),'sourceSealSHA256':sha(R/'submissions'/u/'d0/seal.json'),'reuseV6Corpus':str((R/'common-corpora'/alias/'d0').relative_to(R)),'reuseV6ManifestSHA256':sha(R/'common-corpora'/alias/'d0/portable-sha256.json'),'newV5Corpus':f'paired-corpora/{alias}/v5'})
 out.write_text(json.dumps({'recordedAtUTC':datetime.now(timezone.utc).isoformat(),'recordedAtUnix':time.time(),'primaryEndpoints':ends,'corpora':rows,'scope':'V5 separate actual public D0 acquisition after primary endpoints. V6 side exact common-D0 raw/native-base reuse, manual=None. Native classes only; input/API/visual judgment excluded. Identical offered-width amendment in both versions. Common FINAL and paired V5 use same audit checkouts sequentially; no source races.'},indent=2)+'\n');print('paired acquisition schedule sealed')
if __name__=='__main__':main()
