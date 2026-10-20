#!/usr/bin/env python3
"""Execute each arm's unchanged original assertions against its own real corpus."""
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('unit');p.add_argument('phase',choices=['d0','final']);a=p.parse_args()
 base=R/'submissions'/a.unit;folder='initial-agent-output'if a.phase=='d0'else'final-agent-output'
 tool=read(R/'private/assignment.json')['units'][a.unit]['tool'];out=base/'own-checks'/a.phase;assert not out.exists();out.mkdir(parents=True)
 commands=[]
 for case in sorted(p for p in(R/'design/public/cases').iterdir()if p.is_dir()):
  for platform in ['ios','android']:
   plan=base/folder/'plans'/case.name/platform/'plan.json';capture=R/'own-corpora'/a.unit/a.phase/platform/case.name;dest=out/case.name/platform;dest.mkdir(parents=True)
   index=base/('effective-own-'+a.phase+'.json')
   if index.is_file():capture=R/read(index)['captures'][platform+'/'+case.name]
   cmd=[sys.executable,'-B',str(R/tool/'scripts/native_checks.py'),'--plan',str(plan),'--observation',str(capture/'observation.json'),'--platform',platform,'--output',str(dest/'report.json')]
   if tool=='candidate-v6':cmd+=['--design-lock',str(R/'design/public/design-lock.json'),'--design-sha256',read(R/'design/private/DESIGN-SEAL.json')['public_design_lock_canonical_sha256']]
   started=time.time();result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(dest/'command.log').write_text(result.stdout)
   record={'case':case.name,'platform':platform,'argv':cmd,'exitCode':result.returncode,'startedAtUnix':started,'finishedAtUnix':time.time(),'planSHA256':sha(plan),'observationSHA256':sha(capture/'observation.json'),'scope':'Original typed checks; manual visual judgments are separate.'};(dest/'command.json').write_text(json.dumps(record,indent=2)+'\n');commands.append(record)
   print(json.dumps({'unit':a.unit,'phase':a.phase,'case':case.name,'platform':platform,'exitCode':result.returncode,'reportExists':(dest/'report.json').exists()}),flush=True)
 (out/'commands.json').write_text(json.dumps({'commands':commands,'sealedAtUnix':time.time()},indent=2)+'\n')
if __name__=='__main__':main()
