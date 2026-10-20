#!/usr/bin/env python3
"""Formal reveal only after every complete anonymous scoring batch seals."""
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'private/ASSIGNMENT-RELEASE.json';assert not out.exists();stages={}
 for stage in ['D0','FINAL','selfreview','paired-D0']:
  folder=R/'evaluation'/stage;p=folder/'SEAL.json';seal=read(p)
  for item in seal['files']:assert sha(folder/item['path'])==item['sha256']
  stages[stage]={'sealSHA256':sha(p),'aggregateSHA256':seal['aggregateSHA256'],'sealedAtUTC':seal['sealedAtUTC']}
 mapping=read(R/'private/grade-assignment.json')['mapping'];units=read(R/'private/assignment.json')['units']
 result={'releasedAtUTC':datetime.now(timezone.utc).isoformat(),'releasedAtUnix':time.time(),'stageSeals':stages,'gradeAliases':mapping,'treatments':{x['id']:x['tool']for x in units},'scope':'Formal assignment release after all four complete scoring-batch seals. Shared filesystem and recognizable original formats limit procedural blindness; primary D0/FINAL scores were sealed before original self-review and producer-labeled pair delivery.'}
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
