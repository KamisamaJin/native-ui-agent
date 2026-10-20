#!/usr/bin/env python3
"""Replay generic decoder controls without changing sealed historical statistics."""
import json,subprocess,sys
from contract import R,read,sha
def main():
 commitment=read(R/'evaluation-execution-commitment.json')
 for rel,h in commitment['files'].items():assert sha(R/rel)==h
 root=R/'design/private/evaluation/d0';report=root/'cache-controls-report.json';old=report.read_bytes()
 try:
  result=subprocess.run([sys.executable,'-B',str(root/'cache_controls.py')],capture_output=True,text=True)
  assert result.returncode==0,result.stdout+'\n'+result.stderr
  actual=read(report);historical=json.loads(old)
  assert actual['all_passed']and len(actual['controls'])==6
  for d in [actual,historical]:
   d['metadata'].pop('decoder_seconds');d['metadata'].pop('decoder_source')
  assert actual==historical,'Generic decoder equivalence/bounds results changed'
 finally:report.write_bytes(old)
 print('PASS: 6 generic decoder equivalence/stale-byte/bound controls; sealed report preserved')
if __name__=='__main__':main()
