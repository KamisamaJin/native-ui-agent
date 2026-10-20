#!/usr/bin/env python3
"""Record exact argument arrays, wall time and output for one authorized command."""
import argparse,json,os,subprocess,time
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--cwd',type=Path);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
 cmd=a.command[1:]if a.command[:1]==['--']else a.command
 if not cmd or a.record.exists():raise ValueError('Command and fresh record required')
 a.record.parent.mkdir(parents=True,exist_ok=True)
 started=time.time();r=subprocess.run(cmd,cwd=a.cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 ended=time.time();log=a.record.with_suffix('.log');log.write_text(r.stdout)
 out={'argv':cmd,'cwd':str((a.cwd or Path.cwd()).resolve()),'started_at':started,'finished_at':ended,
      'wall_seconds':ended-started,'exit_code':r.returncode,'log':log.name}
 a.record.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));print(r.stdout[-2500:])
 return r.returncode
if __name__=='__main__':raise SystemExit(main())
