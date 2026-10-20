#!/usr/bin/env python3
"""Reveal assignment only after all four anonymous dual stage seals exist."""
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'private/ASSIGNMENT-RELEASE.json';assert not out.exists();seals={}
 for stage in ['D0','FINAL','selfreview','paired-D0']:
  p=R/'evaluation'/stage/'SEAL.json';s=read(p)
  for rel,h in s['files'].items():assert sha(p.parent/rel)==h
  seals[stage]={'sealSHA256':sha(p),'sealedAtUTC':s['sealedAtUTC'],'sealedAtUnix':s['sealedAtUnix']}
 assignment=read(R/'private/assignment.json');out.write_text(json.dumps({'releasedAtUTC':datetime.now(timezone.utc).isoformat(),'releasedAtUnix':time.time(),'gradeAliases':assignment['gradeAliases'],'units':assignment['units'],'stageSeals':seals,'scope':'Procedural anonymous batches, minimal-context independent evaluator, shared filesystem and recognizable code/plan formats. No secure isolation or human gold standard claimed.'},indent=2)+'\n');print('assignment revealed after four dual seals')
if __name__=='__main__':main()
